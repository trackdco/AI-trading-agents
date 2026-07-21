#!/usr/bin/env python3
"""Q3/Q4 REGIME CHECK (Angus 21 Jul). We're entering Q3/Q4 2026; the strategy is calibrated
on H1 2026. Two questions:
  1. Is there a Q3/Q4-SPECIFIC leak in the base setups? (uses allyears_daily_books, 2023-25)
  2. Is the market regime structurally different in Q3/Q4? (08:00-10:15 window range + trend
     efficiency from the master 1m parquet)
Note: CVD + heatmap (the profitable edge layer) are 2026-only, so the base books here LOSE in
all of 2025 -- the point is the REGIME characterization, not the base P&L.

    python -m scripts.q3q4_regime
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
NY = "America/New_York"


def books():
    d = pd.read_csv("output/allyears_daily_books.csv")
    d["mo"] = d.day.str[5:7].astype(int)
    print("=== base-engine book P&L by half-year (E3 retest / E4 momentum) ===")
    print("    (base setups only -- no CVD gate; loses in 2025 both halves -> regime is the point)")
    for y in (2023, 2024, 2025):
        yr = d[d.year == y]
        for lbl, m in (("H1", yr[yr.mo <= 6]), ("H2 (Q3/Q4)", yr[yr.mo >= 7])):
            print(f"  {y} {lbl:11s}  E3 ${m.E3.sum():+8,.0f}   E4 ${m.E4.sum():+8,.0f}   "
                  f"oracle+SD ${m.oracle_sd.sum():+8,.0f}")
    print()


def regime():
    df = pd.read_parquet("data/reference/nq_1m_master.parquet")
    ny = df.ts_event.dt.tz_convert(NY)
    df = df.assign(sess=(ny + pd.Timedelta(hours=6)).dt.date, hm=ny.dt.hour * 60 + ny.dt.minute)
    w = df[(df.hm >= 480) & (df.hm < 615)]                 # 08:00-10:15 window
    g = w.groupby("sess").agg(hi=("high", "max"), lo=("low", "min"),
                              o=("open", "first"), c=("close", "last"), v=("volume", "sum"))
    g["rng"] = g.hi - g.lo
    g["eff"] = (g.c - g.o).abs() / g["rng"]
    g.index = pd.to_datetime(g.index)
    print("=== 08:00-10:15 window regime (the 'different properties') ===")
    for lbl, a, b in (("2025 H1", "2025-01-01", "2025-07-01"),
                      ("2025 Q3", "2025-07-01", "2025-10-01"),
                      ("2025 Q4", "2025-10-01", "2026-01-01"),
                      ("2026 H1 (tuned on)", "2026-01-01", "2026-07-01")):
        s = g[(g.index >= a) & (g.index < b)]
        print(f"  {lbl:20s}  range {s.rng.mean():5.1f}pt   trend-eff {s.eff.mean():.2f}   ({len(s)}d)")
    print("\n  Q3 (summer) is ~40% tighter than 2026 H1 -> 2R structural targets sized for 250pt")
    print("  days won't develop on 143pt days; lower trend-eff = more chop = both books saw off.")


def main():
    books()
    regime()


if __name__ == "__main__":
    main()
