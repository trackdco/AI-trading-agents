#!/usr/bin/env python3
"""TIER-1 STACK (Angus 24-Jul): stop floor first, then the verified tier-1 confirmations as a
trade-by-trade validation ladder. W = wall-behind absent (heatmap), F = fill-bar delta confirms,
T = not fighting the 15-min tape, G = geometry aligned (not deep counter-VWAP-side),
C = window-correct CVD (PM->pre, LON->gold). Thresholds 2025-only.

    python -m scripts.tier1_stack
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    T = pd.read_parquet("output/trade_matrix.parquet")
    T["win"] = T.dollars > 0
    long = T.direction == "long"
    T["W"] = np.where(long, T.dep_wall_below_d.isna(), T.dep_wall_above_d.isna()).astype(float)
    T["W"] = T["W"].where(T.dep_thick.notna())
    T["F"] = (T.fill_delta_conf == 1).astype(float)
    d15dir = T.d15 * np.where(long, 1, -1)
    T["Tp"] = (d15dir >= d15dir[T.yr == 2025].quantile(0.25)).astype(float)
    T["G"] = (T.ent_vs_vwap_sd_dir >= T[T.yr == 2025].ent_vs_vwap_sd_dir.quantile(0.25)).astype(float)
    T["C"] = np.where(T.win_ == "pre", (T.conf_PM == 1), (T.conf_LON == 1)).astype(float)

    def line(tag, d):
        if len(d) == 0:
            print(f"  {tag:30s} n=0"); return
        days = d.day.nunique()
        print(f"  {tag:30s} n={len(d):3d}  WR {d.win.mean()*100:4.1f}%  ${d.dollars.mean():+6.0f}/t  "
              f"tot ${d.dollars.sum():+8,.0f}  ({len(d)/max(days,1):.2f} tr/d)")

    S = T[T.risk >= 7].copy()
    S["score"] = S[["W", "F", "Tp", "G", "C"]].sum(axis=1)
    for yr in (2025, 2026):
        d = S[S.yr == yr]
        print(f"=== {yr} (stop-floored risk>=7) ===")
        line("base", d)
        line("W AND F", d[(d.W == 1) & (d.F == 1)])
        line("W OR F", d[(d.W == 1) | (d.F == 1)])
        line("NEITHER W nor F", d[(d.W == 0) & (d.F == 0)])
        for k in (2, 3, 4):
            line(f"score>={k}", d[d.score >= k])
        print()
    S.to_parquet("output/tier1_stack.parquet")


if __name__ == "__main__":
    main()
