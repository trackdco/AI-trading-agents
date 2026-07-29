#!/usr/bin/env python3
"""DIAGNOSE THE SELECTION PROBLEM (Angus 22 Jul). Before the bot takes a trade it must decide:
(1) trade or STAND DOWN, and (2) which book (E3 rotation vs E4 momentum). The oracle proves the
right answer exists; the fresh-eyes agent only hit 34% (near random). This ranks which CAUSAL
pre-open features separate those two decisions, PER YEAR, to find what GENERALIZES.

Uses the fresh-eyes ledger (per-day e3/e4/oracle) + regime_vector (causal pre-open features).
No engine sim. All years 2023-2026.

    python -m scripts.diagnose_selection
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

NUM = ["range_pctl_20", "trap_rate_10", "imbal_share_20", "imbal_share_10", "gap_open_pts",
       "streak_imbal", "inventory_pts", "on_nr_rank", "gap_vs_value"]
CAT = ["day_type", "value_position", "open_vs_value"]
YEARS = [2023, 2024, 2025, 2026]


def auc(x, y):
    d = pd.DataFrame({"x": x, "y": y}).dropna()
    if d.y.nunique() < 2 or len(d) < 12:
        return np.nan
    r = d.x.rank(); n1 = (d.y == 1).sum(); n0 = (d.y == 0).sum()
    return (r[d.y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def main():
    L = pd.read_csv("output/v07/walk_v07/ledger.csv")[["day", "e3", "e4"]]
    V = pd.read_csv("output/regime_vector.csv").rename(columns={"day": "day"})
    M = L.merge(V, on="day", how="left")
    M["yr"] = M.day.str[:4].astype(int)
    M["tradeable"] = (M[["e3", "e4"]].max(axis=1) > 0).astype(int)        # 1 = a book wins today
    M["e4_best"] = np.where(M[["e3", "e4"]].max(axis=1) > 0, (M.e4 > M.e3).astype(int), np.nan)

    print("=== base rates by year ===")
    for y in YEARS:
        s = M[M.yr == y]
        td = s.tradeable.mean() * 100
        e4 = s.e4_best.mean() * 100
        print(f"  {y}: tradeable {td:2.0f}%  (stand-down {100-td:2.0f}%)   of tradeable, E4-best {e4:2.0f}%   n={len(s)}")

    print("\n### DECISION 1 — TRADE vs STAND DOWN: feature AUC per year (0.5=noise) ###")
    print(f"  {'feature':16s} " + "".join(f"{y:>7d}" for y in YEARS) + "   verdict")
    for f in NUM:
        if f not in M: continue
        aucs = [auc(M[M.yr == y][f], M[M.yr == y].tradeable) for y in YEARS]
        sign = [a - 0.5 for a in aucs if not np.isnan(a)]
        holds = len(sign) >= 3 and (all(s > 0.03 for s in sign) or all(s < -0.03 for s in sign))
        print(f"  {f:16s} " + "".join(f"{a:7.2f}" if not np.isnan(a) else '     na' for a in aucs)
              + ("   <- HOLDS" if holds else ""))

    print("\n### DECISION 2 — E4 (momentum) vs E3 (rotation), given we trade: AUC per year ###")
    print(f"  {'feature':16s} " + "".join(f"{y:>7d}" for y in YEARS) + "   verdict")
    for f in NUM:
        if f not in M: continue
        aucs = [auc(M[(M.yr == y) & M.e4_best.notna()][f], M[(M.yr == y) & M.e4_best.notna()].e4_best) for y in YEARS]
        sign = [a - 0.5 for a in aucs if not np.isnan(a)]
        holds = len(sign) >= 3 and (all(s > 0.03 for s in sign) or all(s < -0.03 for s in sign))
        print(f"  {f:16s} " + "".join(f"{a:7.2f}" if not np.isnan(a) else '     na' for a in aucs)
              + ("   <- HOLDS" if holds else ""))

    print("\n### categorical: stand-down rate + E4-best rate by value ===")
    for f in CAT:
        if f not in M: continue
        g = M.groupby(f).agg(n=("tradeable", "size"), sd=("tradeable", lambda x: (1 - x.mean()) * 100),
                             e4=("e4_best", lambda x: x.mean() * 100))
        g = g[g.n >= 30]
        if len(g) >= 2:
            print(f"  {f}:")
            for v, r in g.iterrows():
                print(f"      {str(v):12s} n={int(r.n):3d}  stand-down {r.sd:2.0f}%  E4-best {r.e4:2.0f}%")


if __name__ == "__main__":
    main()
