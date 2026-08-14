#!/usr/bin/env python3
"""Does anything the repo already measured rescue the iFVG trigger?

The bare trigger is -0.026R before cost (docs/FINDINGS-dodgy-ifvg.md). He says that is
expected — *"we don't like just an inversion fair value gap in the middle of nowhere"* —
and that context supplies the edge. He never says which context.

This repo does. So instead of guessing his confluences, every inversion is annotated
with the things that have ALREADY been measured to matter here, and each is tested as a
filter on his trigger:

  locus proximity   BR-11/12. Which of the seven censused levels is the inversion at?
                    On NQ the break arm liked vwap_m1 (+0.248) and val (+0.234); on GC
                    vah was the only survivor. If "context" means anything mechanical,
                    it should show up as an inversion AT a locus beating one in the gap
                    between loci — which is his own claim, tested with a measured list.
  BR-1 state        displaced >=0.5W from the 15m BB MA, i.e. the market is "awaiting
                    rebalance" and the MA is a live draw. 89% on NQ, 92.85% on GC — the
                    strongest base rate in the repo. Does trading an inversion INTO
                    that draw beat trading one away from it?
  room to run       BR-32/35. Distance to the next locus in R. Two of twelve cells
                    cleared both eras on NQ, the largest non-flow gate found there.
  risk_w            BR-29/45. Stop size in W. Monotone on GC and mostly the cost
                    denominator — included so it cannot masquerade as something new.

Everything is dual currency and day-clustered. A filter that lifts win rate and not EV
is a refutation (Law 3, BR-20), and this family has produced exactly that before.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.dodgy_ifvg_test import COST_PTS, load_nq, signals, simulate
from src.htf_ma.levels import bb_ma_asof, profile_at_minutes, vwap_bands
from src.research.tomtrades import autopsy as AU

LOCI = ["bbma15", "poc", "val", "vah", "vwap", "vwap_m1", "vwap_p1"]


def annotate(bars: pd.DataFrame, sig: pd.DataFrame) -> pd.DataFrame:
    idx = bars.index
    ma15, w15 = bb_ma_asof(bars, 15)
    vw = vwap_bands(bars)
    prof = profile_at_minutes(bars, list(idx), bin_width=1.0)

    lv = pd.DataFrame(index=idx)
    lv["bbma15"] = ma15
    for c in ("vwap", "vwap_m1", "vwap_p1"):
        lv[c] = vw[c].reindex(idx)
    for c in ("poc", "val", "vah"):
        lv[c] = prof[c].reindex(idx)

    i = sig.i.to_numpy()
    px = bars.close.to_numpy()[i]
    W = w15.to_numpy()[i]
    L = lv.to_numpy()[i]                       # (n_signals, 7)

    dist = np.abs(L - px[:, None]) / W[:, None]          # distance to each locus, in W
    nearest = np.nanargmin(np.where(np.isnan(dist), np.inf, dist), axis=1)
    out = sig.copy()
    out["near_locus"] = [LOCI[k] for k in nearest]
    nd = np.nanmin(np.where(np.isnan(dist), np.inf, dist), axis=1)
    # early bars have no session profile or VWAP yet, so every locus is NaN and the
    # min comes back inf. Left as inf it silently becomes its own qcut bucket.
    out["near_dist_w"] = np.where(np.isfinite(nd), nd, np.nan)
    out["risk_w"] = sig.risk.to_numpy() / W

    # BR-1 state: is the market displaced >=0.5W from the 15m MA, and is the trade
    # heading BACK toward it? That is the strongest draw the repo has measured.
    gap_w = (px - lv["bbma15"].to_numpy()[i]) / W
    out["disp_w"] = np.abs(gap_w)
    out["toward_ma"] = ((np.sign(gap_w) < 0) == (sig.direction.to_numpy() > 0)).astype(int)
    out["br1_state"] = ((out.disp_w >= 0.5) & (out.toward_ma == 1)).astype(int)

    # room to run: distance to the nearest locus BEYOND the entry, in R
    d = sig.direction.to_numpy()[:, None]
    ahead = np.where((L - px[:, None]) * d > 0, np.abs(L - px[:, None]), np.nan)
    out["room_r"] = np.nanmin(np.where(np.isnan(ahead), np.inf, ahead), axis=1) / sig.risk.to_numpy()
    out.loc[~np.isfinite(out.room_r), "room_r"] = np.nan
    return out


def q4(s: pd.Series):
    """Quartiles on the finite values only; NaN rows fall out rather than forming a bin."""
    return pd.qcut(s.where(np.isfinite(s)), 4, duplicates="drop")


def cells(t: pd.DataFrame, by, label: str) -> list[dict]:
    rows = []
    for lvl, g in t.groupby(by, observed=True):
        if len(g) < 100:
            continue
        lo, hi = AU.dboot_mean(g, "out")
        c = COST_PTS / g.risk
        rows.append({"factor": label, "bucket": str(lvl), "n": len(g),
                     "win_pct": 100 * g.win.mean(), "ev": g["out"].mean(),
                     "lo": lo, "hi": hi, "ev_pre_cost": (g["out"] + c).mean()})
    return rows


def main() -> None:
    bars = load_nq()
    sig = annotate(bars, signals(bars, require_sweep=False))
    tr = simulate(bars, sig, be_at_t1=False)
    # JOIN on the signal index, never by position: simulate drops rows non-contiguously
    # (no next bar, sub-floor risk), so slicing would pair each trade with a different
    # signal's context and every table below would be quietly wrong.
    t = tr.merge(sig[["i", "near_locus", "near_dist_w", "risk_w", "disp_w",
                      "toward_ma", "br1_state", "room_r"]], on="i", how="left",
                 validate="one_to_one")
    print(f"{len(t):,} trades annotated", flush=True)

    rows = [{"factor": "ALL", "bucket": "-", "n": len(t),
             "win_pct": 100 * t.win.mean(), "ev": t["out"].mean(),
             **dict(zip(("lo", "hi"), AU.dboot_mean(t, "out"))),
             "ev_pre_cost": (t["out"] + COST_PTS / t.risk).mean()}]
    rows += cells(t, "near_locus", "nearest locus")
    rows += cells(t, q4(t.near_dist_w), "distance to locus (W)")
    rows += cells(t, "br1_state", "BR-1 draw (displaced + toward MA)")
    rows += cells(t, "toward_ma", "trading toward the 15m MA")
    rows += cells(t, q4(t.room_r.clip(0, 20)), "room to run (R)")
    rows += cells(t, q4(t.risk_w), "risk in W")

    out = pd.DataFrame(rows)
    pd.set_option("display.width", 220)
    print(out.round(3).to_string(index=False), flush=True)
    out.to_csv(ROOT / "output/dodgy_ifvg_context.csv", index=False)


if __name__ == "__main__":
    main()
