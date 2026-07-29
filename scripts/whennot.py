#!/usr/bin/env python3
"""WHEN NOT TO TRADE (Angus 21 Jul). The oracle ceiling = knowing which book + when to stand
down. This decomposes the 2025 gap, then tests whether a PRICE-ONLY chop read (no CVD/heatmap,
so it works on 2025) identifies the both-books-lose days across 2023-25 -- the durable
"stand-down" signal we need for Q3/Q4.

    python -m scripts.whennot
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
NY = "America/New_York"


def auc(x, y):
    d = pd.DataFrame({"x": x, "y": y}).dropna()
    if d.y.nunique() < 2 or len(d) < 8:
        return np.nan
    r = d.x.rank(); n1 = (d.y == 1).sum(); n0 = (d.y == 0).sum()
    return (r[d.y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def main():
    d = pd.read_csv("output/allyears_daily_books.csv")
    d["standdown"] = ((d.E3 <= 0) & (d.E4 <= 0)).astype(int)
    d["best"] = d[["E3", "E4"]].max(axis=1)

    print("=== the oracle gap = book-pick + stand-down (2025) ===")
    y = d[d.year == 2025]
    always = max(y.E3.sum(), y.E4.sum())
    best = y.best.sum()                    # perfect book pick, still trades every day
    orc = y.oracle_sd.sum()                # + stand down on both-lose days
    print(f"  best single book (always)     ${always:+8,.0f}")
    print(f"  + perfect book-pick/day       ${best:+8,.0f}   (book selection worth ${best-always:+,.0f})")
    print(f"  + stand down both-lose days   ${orc:+8,.0f}   (stand-down worth ${orc-best:+,.0f})")
    print(f"  stand-down days: {y.standdown.mean()*100:.0f}% of the year\n")

    # PRICE-ONLY chop features, causal 08:00-09:40 (pre-golden), + range vs trailing-20d
    df = pd.read_parquet("data/reference/nq_1m_master.parquet")
    ny = df.ts_event.dt.tz_convert(NY)
    df = df.assign(sess=(ny + pd.Timedelta(hours=6)).dt.date, hm=ny.dt.hour * 60 + ny.dt.minute)
    w = df[(df.hm >= 480) & (df.hm < 580)]                       # 08:00-09:40
    g = w.groupby("sess").agg(hi=("high", "max"), lo=("low", "min"), o=("open", "first"), c=("close", "last"))
    g["rng"] = g.hi - g.lo
    g["eff"] = (g.c - g.o).abs() / g["rng"]
    g["atr20"] = g["rng"].rolling(20, min_periods=10).mean().shift(1)
    g["rng_vs_atr"] = g["rng"] / g["atr20"]                     # <1 = tighter than typical
    g.index = pd.to_datetime(g.index)
    g["day"] = g.index.strftime("%Y-%m-%d")

    M = d.merge(g[["day", "rng", "eff", "rng_vs_atr"]], on="day", how="inner")
    print("=== does a PRICE chop read flag both-lose days? AUC per year (0.5=noise) ===")
    print("    low opening range / low trend-eff = chop -> expect AUC < 0.5 (assoc w/ stand-down)")
    for feat in ("rng", "eff", "rng_vs_atr"):
        aucs = " ".join(f"{yr}:{auc(M[M.year==yr][feat], M[M.year==yr].standdown):.2f}" for yr in (2023, 2024, 2025))
        print(f"  {feat:11s}  {aucs}")

    # P&L: skip the tightest-range days (chop), always-E4 base, per year, walk-forward threshold
    print("\n=== stand-down rule: skip when opening range < trailing-60d median (walk-forward) ===")
    M = M.sort_values("day").reset_index(drop=True)
    M["thr"] = M["rng"].rolling(60, min_periods=20).median().shift(1)
    M["skip"] = M["rng"] < M["thr"]
    for yr in (2023, 2024, 2025):
        s = M[M.year == yr]
        for book in ("E4", "E3"):
            base = s[book].sum(); kept = s[~s.skip][book].sum()
            tag = "  " if book == "E4" else "  "
            print(f"  {yr} {book}: base ${base:+8,.0f}  ->  skip-chop ${kept:+8,.0f}   "
                  f"(Δ ${kept-base:+,.0f}, skipped {int(s.skip.sum())}/{len(s)})")
    print("\n  (base books lose without CVD; question is whether a price chop-skip moves them")
    print("   toward breakeven CONSISTENTLY across years -> a durable when-not-to-trade signal.)")

    print("\n=== E4 momentum is a WIDE-RANGE book (which book wins by range, per year) ===")
    M["wide"] = M["rng"] >= M["thr"]
    for yr in (2023, 2024, 2025):
        s = M[M.year == yr]
        wd, tt = s[s.wide], s[~s.wide]
        print(f"  {yr}:  WIDE E4 ${wd.E4.sum():+8,.0f} / E3 ${wd.E3.sum():+8,.0f}    "
              f"TIGHT E4 ${tt.E4.sum():+8,.0f} / E3 ${tt.E3.sum():+8,.0f}")
    print("  -> E4 profitable on wide days, bleeds on tight days, EVERY year. Trade momentum only")
    print("     when the opening range is wide; stand down (don't flip to E3) on tight days.")


if __name__ == "__main__":
    main()
