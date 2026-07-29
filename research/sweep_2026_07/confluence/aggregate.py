#!/usr/bin/env python3
"""CONFLUENCE STUDY — the SINGLE NON-AGENT AGGREGATOR.

Merges the append-only shard artefacts in raw/ (one writer per file, disjoint by construction),
computes the noise-floor percentile, applies the registered gate, and decides whether conviction
sizing part 2 is permitted to run at all.

THE GATE, registered before any result was seen: if the real composite's out-of-sample metric is
not beyond the 99th percentile of the 2,000 block-shuffled runs, THE ANSWER IS NULL and is
reported as null. No exceptions, no reinterpretation.
"""
import glob
import hashlib
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pipeline import (BLIND, MIN_TRAIN, PENALTIES, POOL, headline, load,  # noqa: E402
                      walk_forward)

RAW = f"{HERE}/raw"
R = {}

def read(mode):
    recs, dup = {}, 0
    for p in sorted(glob.glob(f"{RAW}/{mode}_*.jsonl")):
        for line in open(p):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d["k"] in recs:
                dup += 1
            recs[d["k"]] = d
    return recs, dup

J = load()
W = walk_forward(J, POOL, seed=0)
real = headline(J, W)
FAL = json.load(open(f"{HERE}/falsifiers.json"))

perm, dup_p = read("perm")
rand, dup_r = read("random")
pv = np.array([v["metric"] for v in perm.values() if v["metric"] == v["metric"]])
rv = np.array([v["metric"] for v in rand.values() if v["metric"] == v["metric"]])
print(f"shards merged: {len(perm)} permutations ({dup_p} duplicate keys), "
      f"{len(rand)} random-weight draws ({dup_r} duplicates)")
print(f"shard files: {[os.path.basename(p) for p in sorted(glob.glob(f'{RAW}/*.jsonl'))]}")

print("\n" + "=" * 96)
print("NOISE FLOOR — identical pipeline on day-block-shuffled outcomes")
print("=" * 96)
pct = float((pv < real).mean() * 100) if len(pv) else np.nan
p_emp = float(((pv >= real).sum() + 1) / (len(pv) + 1)) if len(pv) else np.nan
q99 = float(np.percentile(pv, 99)) if len(pv) else np.nan
print(f"  real composite metric      : rho {real:+.4f}  ({len(W)} OOS predictions)")
print(f"  shuffled runs completed    : {len(pv)} of 2000")
print(f"  shuffled distribution      : min {pv.min():+.4f}  p50 {np.median(pv):+.4f}  "
      f"p95 {np.percentile(pv,95):+.4f}  p99 {q99:+.4f}  max {pv.max():+.4f}")
print(f"  REAL SITS AT THE {pct:.2f}th PERCENTILE   (empirical p = {p_emp:.4f})")
passes = bool(np.isfinite(pct) and real > q99)
print(f"  registered gate (> 99th percentile): {'PASS' if passes else 'FAIL -> NULL'}")
R["noise_floor"] = dict(real=real, n_perm=len(pv), percentile=pct, p_empirical=p_emp,
                        p99=q99, p95=float(np.percentile(pv, 95)) if len(pv) else None,
                        median=float(np.median(pv)) if len(pv) else None,
                        minv=float(pv.min()) if len(pv) else None,
                        maxv=float(pv.max()) if len(pv) else None,
                        passes=passes, dup_keys=dup_p)

print("\nFALSIFIER (c) random-weights composite, same pool, same pipeline")
if len(rv):
    rpct = float((rv < real).mean() * 100)
    print(f"  {len(rv)} draws: p50 {np.median(rv):+.4f}  p95 {np.percentile(rv,95):+.4f}  "
          f"max {rv.max():+.4f}  -> real sits at the {rpct:.1f}th percentile")
    R["random_weights"] = dict(n=len(rv), median=float(np.median(rv)),
                               p95=float(np.percentile(rv, 95)), maxv=float(rv.max()),
                               percentile=rpct,
                               fires=bool(np.percentile(rv, 95) >= real))
    print(f"  -> {'FIRES: random weights match the fitted composite' if np.percentile(rv,95) >= real else 'fitted weights exceed the random-weight 95th percentile'}")

# ---------------------------------------------------------------- configurations examined
n_cfg = 1 + 1 + len(POOL)          # composite + blind twin + one per single-feature baseline
R["configurations"] = dict(
    model_specs_examined=n_cfg,
    detail=(f"1 ridge composite + 1 direction-blind composite + {len(POOL)} single-feature "
            f"baselines = {n_cfg} model specifications. The penalty grid "
            f"({len(PENALTIES)} values) is selected INSIDE each fold by {3}-fold CV on training "
            f"trades only and is part of the fitting, not a study-level search. "
            f"{len(rv)} random-weight draws and {len(pv)} block-shuffled runs are nulls, not "
            f"configurations. No model family other than ridge was examined; none was added "
            f"after registration."),
    pool_size=len(POOL), min_train=MIN_TRAIN, penalties=list(PENALTIES))
print(f"\nCONFIGURATIONS EXAMINED: {n_cfg} model specifications "
      f"(1 composite + 1 blind + {len(POOL)} singles). Penalty grid is inside-fold, not a "
      f"study-level search. Nulls: {len(pv)} shuffles + {len(rv)} random-weight draws.")

# ---------------------------------------------------------------- verdict + gate on part 2
fal_a = FAL["blind"]["fires"]
fal_b = not FAL["best_single"]["composite_beats"]
fal_c = R.get("random_weights", {}).get("fires", False)
print("\n" + "=" * 96)
print("VERDICT")
print("=" * 96)
print(f"  noise floor        : {'PASS' if passes else 'FAIL'} "
      f"(real at {pct:.2f}th pct, gate is >99th)")
print(f"  falsifier (a) blind: {'FIRES' if fal_a else 'does not fire'} "
      f"(signed {real:+.4f} vs blind {FAL['blind']['rho']:+.4f})")
print(f"  falsifier (b) best single: {'FIRES' if fal_b else 'does not fire'} "
      f"(best single {FAL['best_single']['feature']} {FAL['best_single']['rho']:+.4f})")
print(f"  falsifier (c) random weights: {'FIRES' if fal_c else 'does not fire'}")
verdict = "NULL" if (not passes or fal_b) else "SIGNAL"
print(f"\n  OVERALL: {verdict}")
R["verdict"] = dict(overall=verdict, noise_floor_passes=passes, fal_a=fal_a, fal_b=fal_b,
                    fal_c=fal_c)

print("\nCONVICTION SIZING PART 2 (score-proportional vs flat under funded rules)")
if verdict == "SIGNAL":
    print("  gate open — would run.")
    R["conviction_part2"] = dict(run=True)
else:
    print("  NOT RUN. It was registered as conditional on the composite clearing its noise")
    print("  floor. The composite did not clear it, so sizing by composite score would be")
    print("  sizing by noise. Running it anyway would be the search widening itself.")
    R["conviction_part2"] = dict(run=False,
                                 reason="gated on the composite clearing its noise floor; it did not")

# ---------------------------------------------------------------- provenance
def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

R["provenance"] = dict(
    commit=subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                          text=True, cwd="/home/user/AI-trading-agents").stdout.strip(),
    pipeline_sha=sha(f"{HERE}/pipeline.py"), shard_sha=sha(f"{HERE}/run_shard.py"),
    pool=POOL, blind=BLIND,
    baseline="PARTIALLY REMEDIATED (C only) + news filter; W and dep_* STILL LEAKY",
    n_trades=int(len(J)), n_days=int(J.day.nunique()),
    shard_files=[os.path.basename(p) for p in sorted(glob.glob(f"{RAW}/*.jsonl"))])
R["falsifiers"] = FAL
json.dump(R, open(f"{HERE}/results.json", "w"), indent=1, default=float)
print(f"\nwrote {HERE}/results.json")
