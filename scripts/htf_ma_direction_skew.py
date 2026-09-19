#!/usr/bin/env python3
"""ITEM 1 — DIRECTION-SKEW TEST (fit only, free, changes how a holdout reads).

VAL break is 79% short and VWAP-1 break 69% short, so the significance of
the +0.230R union book rests on the short side. If monthly EV is negatively
correlated with the month's NQ return, part of that EV is a
downside-continuation premium rather than a level effect. That does NOT
disqualify it -- a directional edge is still an edge -- but it changes what
a holdout pass or fail MEANS and how the book should be sized, especially
since the 23-month sealed span is bull-heavy and therefore adversarial.

Reports: monthly book EV vs monthly NQ return (Pearson + Spearman + OLS
slope, day-boot CI on the slope), for VAL, VWAP-1 and the union; long-side
vs short-side cells with EXPLICIT power (n, CI half-width, and the minimum
detectable effect at 80% power).

    python -m scripts.htf_ma_direction_skew [--table <levels parquet>]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.htf_ma_level_report import (PAIRS, assign, book,       # noqa: E402
                                         boot_mean)
from src.htf_ma.levels import NY                                    # noqa: E402

SEED, DRAWS = 20260807, 2000


def monthly_nq(bars: pd.DataFrame) -> pd.Series:
    """Month-over-month NQ return from the session-close series."""
    d = bars.close.resample("D").last().dropna()
    m = d.resample("MS").last().dropna()
    return (m / m.shift(1) - 1.0).dropna()


def slope_ci(x: np.ndarray, y: np.ndarray, seed=SEED, draws=DRAWS):
    """Bootstrap CI on the OLS slope, resampling MONTHS (the unit here)."""
    rng = np.random.default_rng(seed)
    n = len(x)
    out = []
    for _ in range(draws):
        i = rng.integers(0, n, n)
        if np.ptp(x[i]) == 0:
            continue
        out.append(np.polyfit(x[i], y[i], 1)[0])
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def mde(sd: float, n: int) -> float:
    """Minimum detectable effect, two-sided alpha=.05, 80% power."""
    return 2.8 * sd / np.sqrt(n) if n > 0 else np.nan


def main() -> None:
    table = "output/htf_ma_census/levels_fit_v1.parquet"
    if "--table" in sys.argv:
        table = sys.argv[sys.argv.index("--table") + 1]
    F = pd.read_parquet(ROOT / table)
    F["era"] = np.where(F.sess_day < "2026-01-01", "H2-2025", "H1-2026")
    P = pd.read_parquet(PAIRS)
    F5 = F.join(assign(F, P, 0.5))

    val = book(F5[F5.locus == "val"], "break")
    vm1 = book(F5[F5.locus == "vwap_m1"], "break")
    union = pd.concat([val, vm1]).drop_duplicates(["sess_day", "t", "side"])

    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()
    nq = monthly_nq(bars)

    print("== ITEM 1: monthly book EV vs monthly NQ return ==")
    print("  (a negative slope means part of the EV is a downside-"
          "continuation premium)")
    print(f"{'book':10s} {'months':>7s} {'pearson':>8s} {'spearman':>9s} "
          f"{'slope R/1%':>11s} {'slope 95% CI':>22s}")
    for name, b in (("val", val), ("vwap_m1", vm1), ("UNION", union)):
        b = b.copy()
        b["month"] = pd.PeriodIndex(pd.to_datetime(b.sess_day), freq="M")
        mev = b.groupby("month").out_ship.mean()
        mn = b.groupby("month").size()
        mev = mev[mn >= 15]                      # months with enough fights
        idx = [p for p in mev.index
               if pd.Timestamp(p.start_time, tz=NY) in nq.index]
        x = np.array([nq[pd.Timestamp(p.start_time, tz=NY)] for p in idx])
        y = mev.loc[idx].to_numpy()
        if len(x) < 6:
            print(f"{name:10s} {len(x):7d}   UNDERPOWERED")
            continue
        pear = float(np.corrcoef(x, y)[0, 1])
        spear = float(pd.Series(x).rank().corr(pd.Series(y).rank()))
        sl = float(np.polyfit(x, y, 1)[0]) / 100.0   # per 1% move
        lo, hi = slope_ci(x, y)
        print(f"{name:10s} {len(x):7d} {pear:+8.3f} {spear:+9.3f} "
              f"{sl:+11.4f} [{lo/100:+.4f},{hi/100:+.4f}]")

    print("\n== monthly detail (UNION): month | NQ ret | book EV | n ==")
    u = union.copy()
    u["month"] = pd.PeriodIndex(pd.to_datetime(u.sess_day), freq="M")
    g = u.groupby("month").out_ship.agg(["mean", "size"])
    for p, r in g.iterrows():
        ts = pd.Timestamp(p.start_time, tz=NY)
        ret = nq.get(ts, np.nan)
        flag = "  down-month" if ret < 0 else ""
        print(f"  {p}  NQ {ret*100:+6.2f}%   EV {r['mean']:+.3f}  "
              f"n={int(r['size']):4d}{flag}")

    print("\n== down-month vs up-month split (UNION) ==")
    u["nq_ret"] = [nq.get(pd.Timestamp(p.start_time, tz=NY), np.nan)
                   for p in u.month]
    for lab, sub in (("up months", u[u.nq_ret > 0]),
                     ("down months", u[u.nq_ret < 0])):
        if len(sub) < 30:
            print(f"  {lab:12s} n={len(sub)} UNDERPOWERED")
            continue
        lo, hi = boot_mean(sub)
        print(f"  {lab:12s} n={len(sub):5d} EV {sub.out_ship.mean():+.3f} "
              f"[{lo:+.3f},{hi:+.3f}] over "
              f"{sub.month.nunique()} months")

    print("\n== LONG-SIDE POWER, stated explicitly ==")
    print(f"{'book':10s} {'side':>6s} {'n':>6s} {'EV':>8s} "
          f"{'day-boot 95% CI':>22s} {'halfwidth':>10s} {'MDE@80%':>9s}")
    for name, b in (("val", val), ("vwap_m1", vm1), ("UNION", union)):
        for d, lab in ((1, "long"), (-1, "short")):
            s = b[b.direction == d]
            if len(s) < 15:
                print(f"{name:10s} {lab:>6s} {len(s):6d}   UNDERPOWERED")
                continue
            lo, hi = boot_mean(s)
            print(f"{name:10s} {lab:>6s} {len(s):6d} {s.out_ship.mean():+8.3f} "
                  f"[{lo:+.3f},{hi:+.3f}]".ljust(58)
                  + f"{(hi-lo)/2:10.3f} {mde(s.out_ship.std(), len(s)):9.3f}")
    print("\n  MDE = smallest true EV this cell could reliably detect "
          "(two-sided a=.05, 80% power). A long-side MDE far above the")
    print("  observed short-side EV means the long side is not evidence of "
          "absence — it is absence of evidence.")


if __name__ == "__main__":
    main()
