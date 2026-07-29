#!/usr/bin/env python3
"""GOLDEN STAND-DOWN SEPARATOR (Angus 21 Jul). On 55% of golden days both books lose; the
whole golden-oracle edge is standing down on those. Which observable, causal-at-09:40 day
feature separates the both-lose days from the >=1-green days? Ranked on TRAIN (Feb-Apr),
validated on TEST (May-Jul) so a 55-day fit can't fool us. Pattern recognition, then the
$ impact of a simple interpretable stand-down rule.

    python -m scripts.golden_standdown
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

TRAIN = {"2026-02", "2026-03", "2026-04"}
NUM = ["range_pctl_20", "trap_rate_10", "imbal_share_20", "imbal_share_10", "gap_open_pts",
       "streak_imbal", "inventory_pts", "on_nr_rank", "gap_vs_value", "rng", "cvd"]
CAT = ["day_type", "value_position", "open_vs_value", "pdc_loc", "oc_label", "odir",
       "red_folder_today", "named_high_today", "swept", "confirmed", "diverge"]


def auc(x, y):
    """rank-AUC of feature x separating y in {0,1}; 0.5 = no separation."""
    d = pd.DataFrame({"x": x, "y": y}).dropna()
    if d.y.nunique() < 2 or len(d) < 6:
        return np.nan
    r = d.x.rank()
    n1 = (d.y == 1).sum(); n0 = (d.y == 0).sum()
    return (r[d.y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def main():
    M = pd.read_csv("output/golden_read.csv")
    vec = pd.read_csv("output/regime_vector.csv").rename(columns={"day": "date"})
    M = M.merge(vec, on="date", how="left", suffixes=("", "_v"))
    M["mo"] = M.date.str[:7]
    M["standdown"] = (M.action == "STAND_DOWN").astype(int)   # 1 = both books lose
    tr, te = M[M.mo.isin(TRAIN)], M[~M.mo.isin(TRAIN)]
    print(f"{len(M)} golden days   train {len(tr)} (SD {tr.standdown.mean()*100:.0f}%)   "
          f"test {len(te)} (SD {te.standdown.mean()*100:.0f}%)\n")

    print("=== NUMERIC features: AUC for 'both books lose' (0.5=noise), train vs test ===")
    rows = []
    for f in NUM:
        if f not in M:
            continue
        a_tr, a_te = auc(tr[f], tr.standdown), auc(te[f], te.standdown)
        rows.append((f, a_tr, a_te))
    for f, a_tr, a_te in sorted(rows, key=lambda r: -abs((r[1] or .5) - .5)):
        flag = "  <- holds" if (a_tr and a_te and (a_tr - .5) * (a_te - .5) > 0
                                and abs(a_te - .5) > 0.12) else ""
        print(f"  {f:16s} train AUC {a_tr:.2f}   test AUC {a_te:.2f}{flag}")

    print("\n=== CATEGORICAL features: stand-down rate by value (train), n ===")
    for f in CAT:
        if f not in M:
            continue
        g = tr.groupby(f).standdown.agg(["mean", "size"])
        if len(g) < 2:
            continue
        spread = g["mean"].max() - g["mean"].min()
        if spread < 0.25:
            continue
        print(f"  {f}:  (train spread {spread*100:.0f}pp)")
        for v, r in g.iterrows():
            print(f"      {str(v):14s} SD {r['mean']*100:3.0f}%  (n={int(r['size'])})")

    # ---- simple interpretable rule from the strongest separators; $ impact train vs test ----
    print("\n=== $ impact of a stand-down rule (always-E4 golden book as the base) ===")
    best = max(rows, key=lambda r: abs((r[1] or .5) - .5))
    f = best[0]
    thr = tr[f].median()
    hi_sd = tr[tr[f] >= thr].standdown.mean() > tr[tr[f] < thr].standdown.mean()
    def stand(s):
        return (s[f] >= thr) if hi_sd else (s[f] < thr)
    print(f"  rule: STAND DOWN when {f} {'>=' if hi_sd else '<'} {thr:.2f}  (train median)")
    for name, s in (("TRAIN", tr), ("TEST", te)):
        base = s.E4.sum()
        kept = s[~stand(s)].E4.sum()          # trade E4 only when rule says GO
        acc = ((stand(s).astype(int)) == s.standdown).mean() * 100
        print(f"  {name}: always-E4 ${base:+7,.0f}  ->  with stand-down ${kept:+7,.0f}   "
              f"(rule matches correct SD {acc:.0f}%)")


if __name__ == "__main__":
    main()
