#!/usr/bin/env python3
"""COMBINED selection read (Angus 22 Jul): AMT + CVD + heatmap working hand in hand. No single
feature cracks the daily call (~0.55); this tests whether COMBINING them does. Uses a
directional z-score consensus (each feature oriented by its TRAIN-set sign, then summed) --
no fitted weights, so it resists overfitting -- and validates OUT-OF-FIT across regimes
(train 2026 / test 2025 H2, and reverse). If the ensemble beats the best single feature on
the held-out regime, the multi-tool read is real.

    python -m scripts.combined_selection
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# features that showed any life: AMT/profile + order flow + heatmap
PROF = ["va_width", "poc_migration", "price_vs_poc", "dist_below_poc", "price_in_va"]
FLOW = ["cvd_premkt", "cvd_confirm", "book_balance"]


def auc(x, y):
    d = pd.DataFrame({"x": x, "y": y}).dropna()
    if d.y.nunique() < 2 or len(d) < 12:
        return np.nan
    r = d.x.rank(); n1 = (d.y == 1).sum(); n0 = (d.y == 0).sum()
    return (r[d.y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def composite(tr, te, feats, target):
    """z-score consensus: orient each feature by its sign on TRAIN, sum standardized values
    (train mean/std) on TEST. Returns the composite score on TEST."""
    score = pd.Series(0.0, index=te.index)
    used = 0
    for f in feats:
        a = auc(tr[f], tr[target])
        if np.isnan(a) or abs(a - 0.5) < 0.02:
            continue
        sign = 1.0 if a > 0.5 else -1.0
        mu, sd = tr[f].mean(), tr[f].std()
        if not sd or np.isnan(sd):
            continue
        score = score + sign * (te[f] - mu) / sd
        used += 1
    return score, used


def main():
    A = pd.read_csv("output/intraday_selection.csv")
    B = pd.read_csv("output/dynamic_profile_selection.csv")
    M = A.merge(B.drop(columns=[c for c in ("tradeable", "e4_best") if c in B], errors="ignore"),
                on="day", how="inner", suffixes=("", "_b"))
    M["yr"] = M.day.str[:4].astype(int)
    feats = [f for f in PROF + FLOW if f in M.columns]
    print(f"{len(M)} days, features: {feats}\n")

    for target, label in (("tradeable", "TRADE vs STAND-DOWN"), ("e4_best", "E4 vs E3")):
        print(f"### {label} — out-of-fit combined vs best single ###")
        for train_yr, test_yr in ((2026, 2025), (2025, 2026)):
            tr = M[(M.yr == train_yr) & M[target].notna()]
            te = M[(M.yr == test_yr) & M[target].notna()]
            if len(tr) < 20 or len(te) < 20:
                continue
            base = max(te[target].mean(), 1 - te[target].mean()) * 100     # majority-class %
            best_single = max((abs(auc(te[f], te[target]) - 0.5) for f in feats
                               if not np.isnan(auc(te[f], te[target]))), default=0) + 0.5
            for grp, name in ((PROF, "AMT/profile only"), (FLOW, "order-flow only"), (feats, "ALL combined")):
                gf = [f for f in grp if f in M.columns]
                sc, used = composite(tr, te, gf, target)
                a = auc(sc, te[target])
                print(f"  train {train_yr} -> test {test_yr}: {name:18s} AUC {a:.2f}  ({used} feats)")
            print(f"    [test {test_yr}: base-rate {base:.0f}%, best single-feature AUC {best_single:.2f}, n={len(te)}]\n")


if __name__ == "__main__":
    main()
