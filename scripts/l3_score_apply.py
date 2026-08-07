#!/usr/bin/env python3
"""Apply the FROZEN survivor scores to a span's feature matrix -> l3_scored_{span}.parquet.

Formulas are the fit-frozen architecture (chosen on 2025, validated on 2026) and are NEVER
refit here — on the holdout this is the one-shot out-of-fit application:
  gold_score        = 2*D + Tc + AGE + TRIG + T2
  gold_score_notrig = 2*D + Tc + AGE + T2
  pre_score         = 2*W + G + F_
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.l3_check_trial import load  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--span", default="fit", choices=["fit", "holdout"])
a = ap.parse_args()
F = load(a.span)
F["gold_score"] = 2 * F.D.fillna(0) + F.Tc.fillna(0) + F.AGE.fillna(0) + F.TRIG.fillna(0) + F.T2.fillna(0)
F["gold_score_notrig"] = 2 * F.D.fillna(0) + F.Tc.fillna(0) + F.AGE.fillna(0) + F.T2.fillna(0)
F["pre_score"] = 2 * F.W.fillna(0) + F.G.fillna(0) + F.F_.fillna(0)
out = ROOT / f"output/l3_scored_{a.span}.parquet"
F.to_parquet(out, index=False)
print(f"wrote {out} — {len(F)} rows (frozen formulas, no refit)")
