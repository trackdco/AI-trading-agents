#!/usr/bin/env python3
"""Second pass over the saved autopsy population — the questions the first pass raised.

Reads ``output/tomtrades_autopsy_trades.parquet`` so nothing is re-detected. Three
things the main run left open:

1. the model statistics at the full permutation count (the first pass capped them at 40
   because each null re-runs a cross-validation, and both p-values landed on that
   floor, which is not the same as being small);
2. how tightly the "significant" features are bound to each other, since a table of
   twenty correlations means nothing if six of them are the same variable;
3. what the obvious fix — only take the trades that pay more than they risk — actually
   returns.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.research.tomtrades import autopsy as AU

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--perm", type=int, default=200)
    a = ap.parse_args()

    B = pd.read_parquet(OUT / "tomtrades_autopsy_trades.parquet")
    print(f"{len(B):,} trades, {B.sess_day.nunique():,} days", flush=True)

    print("\n--- model statistics, full permutation count ---", flush=True)
    mc = AU.calibrate_dict(lambda d: AU.model_stats(d, AU.CLEAN_COLS), B, n_perm=a.perm)
    rows = []
    for k, (real, null, p) in mc.items():
        rows.append({"statistic": k, "real": real, "null_mean": float(np.nanmean(null)),
                     "null_sd": float(np.nanstd(null)), "p": p,
                     "p_floor": 1 / (1 + a.perm)})
    mtab = pd.DataFrame(rows)
    print(mtab.to_string(index=False), flush=True)
    mtab.to_csv(OUT / "tomtrades_autopsy_model.csv", index=False)

    # Quintiles of reward:risk are still wide, so distance-to-target information can
    # survive inside a stratum and masquerade as skill. Narrowing the strata is the
    # check: if the within-stratum AUC decays toward 0.5 as the bins tighten, what
    # looked like separation was the geometry all along.
    print("\n--- within-RR AUC as the strata tighten ---", flush=True)
    rows = []
    for q in (5, 10, 20, 40):
        real, null, p = AU.calibrate(
            lambda d, qq=q: AU.oos_auc_within(d, AU.CLEAN_COLS, q=qq), B,
            n_perm=min(a.perm, 60))
        rows.append({"strata": q, "auc_within": real, "null_mean": float(np.nanmean(null)),
                     "null_sd": float(np.nanstd(null)), "p": p})
    strata = pd.DataFrame(rows)
    print(strata.round(4).to_string(index=False), flush=True)
    strata.to_csv(OUT / "tomtrades_autopsy_strata.csv", index=False)

    print("\n--- how much of the feature table is one variable ---", flush=True)
    fam = ["rr_at_entry", "retrace_frac", "run_minutes", "minute_of_hour",
           "run_displacement", "disp_atr", "sweep_depth", "bars_since_arm", "risk_pts"]
    corr = pd.DataFrame({a_: {b_: AU.spearman(B[a_].to_numpy(dtype=float),
                                              B[b_].to_numpy(dtype=float))
                              for b_ in fam} for a_ in fam})
    print(corr.round(3).to_string(), flush=True)
    corr.round(4).to_csv(OUT / "tomtrades_autopsy_collinearity.csv")

    print("\n--- reward:risk quintiles ---", flush=True)
    rr = AU.bucket_table(B, "rr_at_entry", q=5)
    print(rr.round(4).to_string(index=False), flush=True)

    print("\n--- the obvious fix: only take trades that pay more than they risk ---",
          flush=True)
    rows = []
    for thr in (0.0, 0.4, 0.6, 0.8, 1.0, 1.5):
        s = B[B["rr_at_entry"] >= thr]
        if len(s) < AU.MIN_N:
            rows.append({"min_rr": thr, "n": len(s), "note": "below the floor"})
            continue
        lo, hi = AU.dboot_mean(s, "out")
        rows.append({"min_rr": thr, "n": len(s), "days": s["sess_day"].nunique(),
                     "win_pct": 100 * float(s["win"].mean()),
                     "mean_win_r": float(s[s["out"] > 0]["out"].mean()),
                     "ev": float(s["out"].mean()), "ev_lo": lo, "ev_hi": hi,
                     "total_r": float(s["out"].sum())})
    fix = pd.DataFrame(rows)
    print(fix.round(4).to_string(index=False), flush=True)
    fix.to_csv(OUT / "tomtrades_autopsy_rrfilter.csv", index=False)

    print("\n--- sweep depth, the one survivor that is not a distance proxy ---",
          flush=True)
    print(AU.bucket_table(B, "sweep_depth", q=5).round(4).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
