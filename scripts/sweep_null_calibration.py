#!/usr/bin/env python3
"""NULL CALIBRATION for the agent sweep — how many "survivors" does the
declared five-test rule produce on data with NO signal at all?

WHY: the declared split-half test (docs/DECLARATIONS-agent-sweep.md,
test 2) is NOT independent of test 1 — the two halves compose the
full-sample effect, so conditional on the full CI clearing, the halves
usually agree. The rule is therefore softer than its five-part
structure suggests, and the only way to know what a survivor count
MEANS is to run the identical machinery on a known null.

METHOD: within each (session, mechanism) cell, randomly permute the
`out` column across rows. This destroys every predictor-outcome
relationship while preserving cell sizes, the marginal outcome
distribution, and every predictor's own distribution and correlations.
Re-derive out_pts from the permuted outcome. Run the SAME sweep with
the SAME shared module. Repeat over several seeds.

CONSERVATISM NOTE: the permutation also destroys within-day outcome
correlation, which narrows the day-clustered bootstrap and so tends to
INFLATE the null's clear/survivor counts. A real count that merely
matches the null is therefore certainly noise; a real count must exceed
this inflated null to mean anything.

    python -m scripts.sweep_null_calibration [--seeds 5]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.sweep_lib import (cells, load_wide, predictors,          # noqa: E402
                               test_split)

SESSIONS = ["LONDON", "NY_PRE", "NY_AM"]


def run_sweep(B, preds):
    """Returns (n_tests, n_clears, n_survivors, survivor_labels)."""
    nt = nc = ns = 0
    surv = []
    for sess in SESSIONS:
        for label, g in cells(B, sess):
            for v in preds:
                if v not in g.columns:
                    continue
                r = test_split(g, v)
                nt += 1
                if r.get("clears"):
                    nc += 1
                if r.get("survives"):
                    ns += 1
                    surv.append(f"{label}:{v}")
    return nt, nc, ns, surv


def main() -> None:
    nseeds = 5
    if "--seeds" in sys.argv:
        nseeds = int(sys.argv[sys.argv.index("--seeds") + 1])
    B = load_wide()
    preds = predictors(B)
    print(f"predictors: {len(preds)}  (out_pts excluded: "
          f"{'out_pts' not in preds})")

    print("\n=== REAL DATA ===", flush=True)
    nt, nc, ns, surv = run_sweep(B, preds)
    print(f"tests {nt}  CI-clears {nc} ({nc/nt*100:.1f}%)  "
          f"SURVIVORS {ns} ({ns/nt*100:.1f}%)")
    real = (nt, nc, ns)
    real_surv = set(surv)

    print("\n=== NULL (outcome permuted within each session x mech "
          "cell) ===", flush=True)
    rows = []
    all_null_surv = []
    for s in range(nseeds):
        rng = np.random.default_rng(90000 + s)
        Bn = B.copy()
        for sess in SESSIONS:
            for mech in ("M1", "M2", "M3"):
                m = (Bn.session == sess) & (Bn.mech == mech)
                idx = Bn.index[m].to_numpy()
                if len(idx) < 2:
                    continue
                perm = rng.permutation(idx)
                Bn.loc[idx, "out"] = Bn.loc[perm, "out"].to_numpy()
        Bn["out_pts"] = Bn["out"] * Bn["risk"]
        nt2, nc2, ns2, sv = run_sweep(Bn, preds)
        all_null_surv.append(set(sv))
        rows.append((nt2, nc2, ns2))
        print(f"  seed {s}: tests {nt2}  clears {nc2} "
              f"({nc2/nt2*100:.1f}%)  survivors {ns2} "
              f"({ns2/nt2*100:.1f}%)", flush=True)

    cl = np.array([r[1] for r in rows], dtype=float)
    sv_ = np.array([r[2] for r in rows], dtype=float)
    print("\n" + "=" * 78)
    print("VERDICT")
    print("=" * 78)
    print(f"  REAL: {real[1]} clears, {real[2]} survivors "
          f"out of {real[0]} tests")
    print(f"  NULL: clears {cl.mean():.1f} +/- {cl.std():.1f} "
          f"(range {cl.min():.0f}-{cl.max():.0f})")
    print(f"        survivors {sv_.mean():.1f} +/- {sv_.std():.1f} "
          f"(range {sv_.min():.0f}-{sv_.max():.0f})")
    excess_c = real[1] - cl.mean()
    excess_s = real[2] - sv_.mean()
    print(f"  EXCESS over null: clears {excess_c:+.1f}, "
          f"survivors {excess_s:+.1f}")
    if sv_.std() > 0:
        print(f"  survivors z vs null: {excess_s / sv_.std():+.2f}")
    # how often does a REAL survivor label also appear as a NULL
    # survivor in some seed? (label-level reproducibility of noise)
    ever = set().union(*all_null_surv) if all_null_surv else set()
    both = real_surv & ever
    print(f"  real survivor labels also appearing as NULL survivors in "
          f">=1 seed: {len(both)} of {len(real_surv)}")
    print("\n  Reading: the null is INFLATED by construction (the "
          "permutation destroys within-day")
    print("  outcome correlation, narrowing the day-clustered "
          "bootstrap). A real count at or below")
    print("  the null is noise. Only a clear excess means anything.")


if __name__ == "__main__":
    main()
