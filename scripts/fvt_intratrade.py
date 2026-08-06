#!/usr/bin/env python3
"""Intra-trade path analysis: what do losers do that winners don't, and can we exit earlier?

ANGUS 2026-08-06: *"What properties do losers share on entry, but also within the trade intra
trade… If we can cut losers much earlier and hold the win rate, our profit factor etc looks a
lot better simply because an average loss could be -0.3-0.5 r rather than a full -1r. At a 50%
win rate where an average win is 1.5r and a loss is 0.5, THAT is an edge worth keeping."*

The arithmetic is the whole motivation:
    50% win rate, +1.5R wins, -0.5R losses  ->  E = 0.5(1.5) - 0.5(0.5) = **+0.5R**, PF 3.0
against what the calibrated book currently does:
    47.1% win, +0.788R wins, -0.658R losses ->  E = **+0.023R**, PF 1.07

So the loss side is where the leverage is, and it is worth ~20x the entry-selection work that
has failed all session.

WHY A TIME-STOP AND NOT A TIGHTER STOP. A tighter stop was already tested and is strictly
worse (0.5x stop -> -1.58 pt/trade) because it clips winners that dip before working: winners'
median MAE is 0.46x the stop, and 20.7% of them come within 90% of it. A tighter stop cannot
tell "dipped then worked" from "failed". A TIME rule can: it fires on *stagnation*, not on a
spike, so it targets a property winners do not share.

CAUSALITY. Every exit decision uses only the path up to that minute. The excursion arrays are
running maxima computed forward from entry, so a rule evaluated at minute N sees nothing after N.

    python -m scripts.fvt_intratrade
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.fvt_model as F  # noqa: E402

FRIC = 0.5
RR = 1.5
ATR_TF = 30
MARKS = (3, 5, 10, 15, 20, 30, 45)


def paths(b: pd.DataFrame) -> list[dict]:
    """Every calibrated-book entry with its minute-by-minute excursion path."""
    b = b.copy()
    b["atr"] = F.atr_series(b, ATR_TF)
    rng = (b.high - b.low).to_numpy()
    upw = (b.high - np.maximum(b.open, b.close)).to_numpy()
    dnw = (np.minimum(b.open, b.close) - b.low).to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        du = (b.close > b.open).to_numpy() & (np.where(rng > 0, dnw / rng, 1.0) <= F.WICK_MAX)
        dd = (b.close < b.open).to_numpy() & (np.where(rng > 0, upw / rng, 1.0) <= F.WICK_MAX)
    b["du"], b["dd"] = du, dd

    out = []
    for day, g in b.groupby("day"):
        g = g.reset_index(drop=True)
        hi, lo, cl = g.high.to_numpy(float), g.low.to_numpy(float), g.close.to_numpy(float)
        hm, atr = g.hm.to_numpy(), g.atr.to_numpy(float)
        gu, gd = g.du.to_numpy(), g.dd.to_numpy()
        sh = np.full(len(g), np.nan); sl = np.full(len(g), np.nan)
        lh = ll = np.nan
        for i in range(len(g)):
            if i >= 2:
                if hi[i - 1] > hi[i - 2] and hi[i - 1] > hi[i]:
                    lh = hi[i - 1]
                if lo[i - 1] < lo[i - 2] and lo[i - 1] < lo[i]:
                    ll = lo[i - 1]
            sh[i], sl[i] = lh, ll
        for wn, wlo, whi in F.WINDOW_SETS["all"]:
            seg = np.flatnonzero(hm >= wlo)
            if not len(seg):
                continue
            fv = float(g.open.iloc[seg[0]])
            start = wlo + (F.SKIP_FIRST_MIN if wn == "AM" else 0)
            taken = False
            for i in np.flatnonzero((hm >= start) & (hm < wlo + 15)):
                if taken or not np.isfinite(atr[i]):
                    continue
                above = cl[i] > fv
                d_ = 0
                if above and np.isfinite(sh[i]) and cl[i] > sh[i] and gu[i]:
                    d_ = 1
                elif (not above) and np.isfinite(sl[i]) and cl[i] < sl[i] and gd[i]:
                    d_ = -1
                if d_ == 0:
                    continue
                taken = True
                fwd = np.flatnonzero((hm > hm[i]) & (hm < whi))
                if not len(fwd):
                    continue
                e = cl[i]
                sd = next(s for a, s in F.TIERS if atr[i] > a)
                adv = np.maximum.accumulate((e - lo[fwd]) if d_ == 1 else (hi[fwd] - e))
                fav = np.maximum.accumulate((hi[fwd] - e) if d_ == 1 else (e - lo[fwd]))
                # mark-to-market on closes, for the time rule
                mtm = (cl[fwd] - e) * d_
                out.append({"day": day, "yr": day[:4], "win": wn, "dir": d_, "entry": e,
                            "stop": sd, "adv": adv, "fav": fav, "mtm": mtm})
    return out


def resolve(p, time_min=None, need_R=0.0):
    """Outcome in R. Optional time rule: at `time_min`, if mark-to-market < need_R, exit flat
    at that bar's close. Uses only information available at that minute."""
    sd, tgt = p["stop"], p["stop"] * RR
    adv, fav, mtm = p["adv"], p["fav"], p["mtm"]
    ts = int(np.argmax(adv >= sd)) if (adv >= sd).any() else 10**9
    tt = int(np.argmax(fav >= tgt)) if (fav >= tgt).any() else 10**9
    if time_min is not None:
        k = time_min - 1
        if k < len(mtm) and min(ts, tt) > k:            # still open at the mark
            if mtm[k] < need_R * sd:
                return (mtm[k] - FRIC) / sd
    if ts == 10**9 and tt == 10**9:
        return (mtm[-1] - FRIC) / sd
    return ((-sd if ts <= tt else tgt) - FRIC) / sd


def main() -> int:
    b = F.load()
    P = paths(b)
    print(f"{len(P):,} entries with full paths", flush=True)
    base = np.array([resolve(p) for p in P])
    win = base > 0
    print(f"base: win {win.mean():.1%}  avgR {base.mean():+.3f}  "
          f"avgWin {base[win].mean():+.3f}  avgLoss {base[~win].mean():+.3f}  "
          f"PF {base[win].sum()/abs(base[~win].sum()):.2f}")

    L = ["# Intra-trade: what losers do that winners don't", "",
         "Motivation (ANGUS): *at a 50% win rate with +1.5R wins and −0.5R losses, "
         "E = **+0.5R**, PF 3.0.* The calibrated book is +0.023R at PF 1.07, so the loss side "
         "is where the leverage is.", "",
         f"**{len(P):,} entries.** Base: win {win.mean():.1%}, avg R {base.mean():+.3f}, "
         f"avg win {base[win].mean():+.3f}, avg loss {base[~win].mean():+.3f}, "
         f"PF {base[win].sum()/abs(base[~win].sum()):.2f}", "",
         "## Where do the two populations separate?", "",
         "Mark-to-market in R at each minute after entry, split by eventual outcome.", "",
         "| minute | winners MTM | losers MTM | **gap** | winners still ≤0 | losers still >0 |",
         "|---:|---:|---:|---:|---:|---:|"]
    for m in MARKS:
        wv, lv, wneg, lpos = [], [], [], []
        for p, isw in zip(P, win):
            k = m - 1
            if k >= len(p["mtm"]):
                continue
            v = p["mtm"][k] / p["stop"]
            (wv if isw else lv).append(v)
            if isw:
                wneg.append(v <= 0)
            else:
                lpos.append(v > 0)
        if len(wv) < 100:
            continue
        L.append(f"| {m} | {np.mean(wv):+.3f} | {np.mean(lv):+.3f} | "
                 f"**{np.mean(wv)-np.mean(lv):+.3f}** | {np.mean(wneg):.0%} | {np.mean(lpos):.0%} |")

    L += ["", "## Time-stop sweep — exit flat if not ≥ X R by minute N", "",
          "| minute | need ≥ R | n | win% | avg R | avg win | **avg loss** | **PF** | vs base |",
          "|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    best = None
    for m in MARKS:
        for need in (0.0, 0.1, 0.25, 0.5):
            r = np.array([resolve(p, m, need) for p in P])
            w = r > 0
            if w.sum() < 100 or (~w).sum() < 100:
                continue
            pf = r[w].sum() / abs(r[~w].sum())
            L.append(f"| {m} | {need:+.2f} | {len(r):,} | {w.mean():.1%} | **{r.mean():+.3f}** | "
                     f"{r[w].mean():+.3f} | **{r[~w].mean():+.3f}** | **{pf:.2f}** | "
                     f"{r.mean()-base.mean():+.3f} |")
            if best is None or r.mean() > best[0]:
                best = (r.mean(), m, need, w.mean(), r[w].mean(), r[~w].mean(), pf, r)

    if best:
        _, m, need, wr, aw, al, pf, r = best
        yrs = np.array([p["yr"] for p in P])
        ys = [r[yrs == y].mean() for y in ("2023", "2024", "2025", "2026")]
        L += ["", f"**Best: exit if not ≥ {need:+.2f}R by minute {m}.**", "",
              f"win {wr:.1%} · avg R **{r.mean():+.3f}** · avg win {aw:+.3f} · "
              f"avg loss **{al:+.3f}** · **PF {pf:.2f}**", "",
              "| year | 2023 | 2024 | 2025 | 2026 |", "|---|---:|---:|---:|---:|",
              "| avg R | " + " | ".join(f"{v:+.3f}" for v in ys) + " |", "",
              ("**Positive in all four years.**" if all(v > 0 for v in ys) else
               "**NOT positive in all four years — treat as a lead, not a result.**"), ""]

    text = "\n".join(L)
    print(text)
    (ROOT / "output/fvt_intratrade.md").write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
