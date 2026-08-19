#!/usr/bin/env python3
"""Is the iFVG trigger distinguishable from a coin flip with the same geometry?

This should have been the first test in the stream, not the seventh. Every result so
far -- the sweep, obviousness, rule 4, the session split, the exit, the near draw set --
measures whether a FILTER improves the trigger. None of them asks whether the trigger
carries any information at all, and the arithmetic now says it may not: gross of cost the
book is -0.017R on 81,038 trades, against a 33.33% break-even win rate at 2R and an
observed 32.80%. That is a coin flip that pays a toll.

The repo's own convention for this is BR-1 on gold: 92.85% [92.26,93.42] against a 71.73%
placebo. A base rate without a matched control is not evidence.

MATCHING. The placebo must share the trigger's GEOMETRY so the comparison isolates its
INFORMATION. Each placebo trade copies its real signal's
  - direction  (long/short),
  - risk in points  -- critical, because risk sets cost-in-R and an unmatched risk
    distribution would reintroduce the Law 2 denominator problem wholesale,
  - minute of day  -- volatility and spread are strongly time-of-day dependent,
and differs only in WHERE it is placed. Everything downstream is identical: entry at the
next open, stop at 1R, target at 2R, 240-bar max hold, same round turn.

What is deliberately NOT matched is the stop's LOCATION at a fair-value-gap edge. That is
the claim under test -- he says the gap edge is a meaningful price -- so matching it would
assume the conclusion.

THREE CONTROLS, because each kills a different explanation:
  random_day  same minute of day, a different session day. Kills the pattern, keeps the
              clock. K=5 draws per signal, averaged, to damp placebo noise.
  shift_1d    the same bar index one session day later. Keeps the local volatility
              regime as well as the clock, so it is the tighter control of the two.
  flip        the SAME bar, same risk, opposite direction. Isolates the directional call
              from timing and geometry entirely: if the trigger cannot tell up from down,
              nothing built on top of it can.

STATISTIC. The comparison is PAIRED and bootstrapped by session day: every real trade is
differenced against its own control before resampling, which is both the correct clustering
and far more powerful than eyeballing two overlapping intervals.

    .venv/bin/python scripts/dodgy_placebo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.dodgy_ifvg_test import COST_PTS, MAX_HOLD
from scripts.dodgy_near_draw import PT, simulate
from src.research.tomtrades import autopsy as AU

SEED = 20260819          # fixed and stated; no seed search
K = 5                    # placebo draws per signal for the random_day control
BARS_PER_DAY = 1380      # 23h of 1m bars, the 18:00-anchored session
WIN = (510, 660)


def realized_risk(sig: pd.DataFrame, bars: pd.DataFrame) -> np.ndarray:
    """Risk the REAL book actually traded: |next open - stop|, not the signal-bar figure.

    simulate() derives risk from (entry, stop) and entry is the next open, so matching on
    sig.risk -- measured from the signal-bar CLOSE -- would leave a small mismatch exactly
    where the whole comparison lives.
    """
    o = bars["open"].to_numpy()
    return np.abs(o[np.minimum(sig.i.to_numpy() + 1, len(o) - 1)] - sig.stop.to_numpy())


def restop(p: pd.DataFrame, bars: pd.DataFrame, risk: np.ndarray) -> pd.DataFrame:
    """Place the control's stop at `risk` points on the LOSING side of its own entry.

    THIS IS THE WHOLE MATCH, and the first version of this script got it wrong: it carried
    the real signal's absolute stop PRICE onto a different bar (or a flipped direction),
    where that price is unrelated to the new entry and frequently sits on the WINNING side.
    simulate() then triggers its stop check on the entry bar itself and books an instant
    +1R, which is why the flip control came back winning 99.98% of the time. A control that
    cannot lose is not a control. See FINDINGS-dodgy-placebo CORRECTION.
    """
    o = bars["open"].to_numpy()
    i0 = np.minimum(p.i.to_numpy() + 1, len(o) - 1)
    d = p.direction.to_numpy()
    p = p.copy()
    p["stop"] = o[i0] - d * risk
    return p


def placebo(sig: pd.DataFrame, bars: pd.DataFrame, mode: str,
            rng: np.random.Generator,
            pool_mask: np.ndarray | None = None) -> list[pd.DataFrame]:
    """Return K matched control books (1 for the deterministic modes).

    ``pool_mask`` restricts where random_day may place a control. For a SUBPOPULATION
    arm it must be the subpopulation's own mask -- drawing controls from the whole tape
    would ask whether the subpopulation is a good place to be, which is a different and
    much easier question than whether the trigger beats a coin flip taken there.
    """
    n = len(bars)
    ts = bars.index
    mod = (ts.hour * 60 + ts.minute).to_numpy()
    sday = (ts - pd.Timedelta(hours=18)).date
    last = n - MAX_HOLD - 2                       # room for entry + full hold
    risk = realized_risk(sig, bars)

    if mode == "flip":
        p = sig.copy()
        p["direction"] = -p["direction"]
        return [restop(p, bars, risk)]

    if mode == "shift_1d":
        p = sig.copy()
        p["i"] = p["i"] + BARS_PER_DAY
        keep = (p.i < last).to_numpy()
        return [restop(p[keep].reset_index(drop=True), bars, risk[keep])]

    # random_day: same minute of day, a different session day
    si = sig.i.to_numpy()
    smin = mod[si]
    sd = sday[si]
    ok = (np.arange(n) < last)
    if pool_mask is not None:
        ok &= pool_mask
    pool = {m: np.flatnonzero((mod == m) & ok) for m in np.unique(smin)}
    thin = [m for m, v in pool.items() if len(v) < 20]
    if thin:
        raise ValueError(f"{len(thin)} minutes have <20 control bars; pool too thin")
    out = []
    for _ in range(K):
        newi = np.empty(len(sig), dtype=np.int64)
        for m in np.unique(smin):
            w = np.flatnonzero(smin == m)
            newi[w] = rng.choice(pool[m], size=len(w), replace=True)
        p = sig.copy()
        p["i"] = newi
        p = restop(p, bars, risk)
        p.attrs["collide"] = (sday[newi] == sd).mean()
        out.append(p)
    return out


def audit(real: pd.DataFrame, ctrl: list[pd.DataFrame], bars: pd.DataFrame,
          label: str) -> None:
    """Hard guards. The first version of this script would have failed all three."""
    o = bars["open"].to_numpy()
    ref = pd.Series(realized_risk(real, bars), index=real.sid.to_numpy())
    for c in ctrl:
        i0 = np.minimum(c.i.to_numpy() + 1, len(o) - 1)
        d = c.direction.to_numpy()
        # Only rows that actually trade: simulate() discards risk < 2.0, and a handful
        # of real signals have a next open sitting exactly ON their stop (risk 0), which
        # would otherwise trip this check on trades that never happen.
        cr_all = realized_risk(c, bars)
        live = cr_all >= 2.0
        wrong_side = ((o[i0] - c.stop.to_numpy()) * d <= 0)[live].mean()
        assert wrong_side == 0, f"{label}: {100 * wrong_side:.2f}% of stops on the winning side"
        cr = pd.Series(realized_risk(c, bars), index=c.sid.to_numpy())
        assert np.allclose(cr.to_numpy(), ref.loc[cr.index].to_numpy(), atol=1e-9), \
            f"{label}: risk not matched"
    print(f"  [audit] {label}: stops all on the losing side, risk matched to 1e-9",
          flush=True)


def paired(real: pd.DataFrame, ctrl: list[pd.DataFrame], bars: pd.DataFrame,
           label: str) -> dict:
    """EV difference real - control, day-clustered bootstrap on the PAIRED difference."""
    r = simulate(bars, real, "fixed2r").set_index("sid")
    books = [simulate(bars, c, "fixed2r").set_index("sid") for c in ctrl]
    cm = pd.concat(books).groupby(level=0)[["out", "usd", "win"]].mean()
    j = r[["out", "usd", "win", "sess_day"]].join(cm, how="inner", rsuffix="_p")
    d = pd.DataFrame({"out": j.out - j.out_p, "sess_day": j.sess_day})
    lo, hi = AU.dboot_mean(d, "out")
    du = pd.DataFrame({"out": j.usd - j.usd_p, "sess_day": j.sess_day})
    ulo, uhi = AU.dboot_mean(du, "out")
    return {"control": label, "n_pairs": len(j),
            "real_ev": j.out.mean(), "ctrl_ev": j.out_p.mean(),
            "diff": d.out.mean(), "lo": lo, "hi": hi,
            "real_win": 100 * j.win.mean(), "ctrl_win": 100 * j.win_p.mean(),
            "real_usd": j.usd.mean(), "ctrl_usd": j.usd_p.mean(),
            "diff_usd": du.out.mean(), "ulo": ulo, "uhi": uhi}


def main() -> None:
    bars = pd.read_parquet(ROOT / "output/_nq_bars.parquet")
    sig = pd.read_parquet(ROOT / "output/_nq_sig.parquet")
    sig["sid"] = np.arange(len(sig))
    ts = pd.DatetimeIndex(sig.ts)
    m = ts.hour * 60 + ts.minute
    pops = {"FULL BOOK": sig,
            "08:30-11:00": sig[(m >= WIN[0]) & (m < WIN[1])].reset_index(drop=True)}

    rows = []
    for pop, s in pops.items():
        t = simulate(bars, s, "fixed2r")
        gross = (t.out + COST_PTS / t.risk).mean()
        print(f"\n{pop}: {len(s):,} signals -> {len(t):,} trades · "
              f"win {100 * t.win.mean():.2f}% · net {t.out.mean():+.4f}R · "
              f"gross {gross:+.4f}R · ${t.usd.mean():+.2f}", flush=True)
        for mode in ("random_day", "shift_1d", "flip"):
            rng = np.random.default_rng(SEED)
            ctrl = placebo(s, bars, mode, rng)
            audit(s, ctrl, bars, mode)
            if mode == "random_day":
                print(f"  same-session-day collisions: "
                      f"{100 * ctrl[0].attrs['collide']:.2f}% (biases TOWARD the null)",
                      flush=True)
            r = paired(s, ctrl, bars, mode)
            r["pop"] = pop
            rows.append(r)
            print(f"  {mode:11s} n={r['n_pairs']:6,d}  real {r['real_ev']:+.4f} vs "
                  f"ctrl {r['ctrl_ev']:+.4f}  diff {r['diff']:+.4f} "
                  f"[{r['lo']:+.4f},{r['hi']:+.4f}]", flush=True)

    d = pd.DataFrame(rows)
    d["ci"] = d.apply(lambda r: f"[{r.lo:+.4f},{r.hi:+.4f}]", axis=1)
    d["usd_ci"] = d.apply(lambda r: f"[{r.ulo:+.2f},{r.uhi:+.2f}]", axis=1)
    d["verdict"] = np.where(d.lo > 0, "REAL > PLACEBO",
                            np.where(d.hi < 0, "REAL < PLACEBO", "indistinguishable"))
    print("\n=== TRIGGER vs MATCHED PLACEBO (paired, day-clustered) ===")
    print(d[["pop", "control", "n_pairs", "real_ev", "ctrl_ev", "diff", "ci", "verdict"]]
          .to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print("\n=== the same thing in dollars, and in win rate ===")
    print(d[["pop", "control", "real_win", "ctrl_win", "real_usd", "ctrl_usd",
             "diff_usd", "usd_ci"]]
          .to_string(index=False, float_format=lambda v: f"{v:.2f}"))
    d.to_csv(ROOT / "output/dodgy_placebo.csv", index=False)
    print(f"\nPT=${PT:.0f}/pt · seed={SEED} · K={K} · wrote output/dodgy_placebo.csv")


if __name__ == "__main__":
    main()
