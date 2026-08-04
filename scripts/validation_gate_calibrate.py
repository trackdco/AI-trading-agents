#!/usr/bin/env python3
"""Calibrate the validation gate (DSR + PBO) against a case with a known honest answer.

The known case: the London stage-2 sweep — 29,161 combinations (all singles and pairs of
the atoms derived from the L3 features) over the risk>=9.5 fit population — which produced
a CLEAN NULL under the pre-registered bar (docs/LONDON-AUDIT-STAGE2-combinations.md), and
the stage-3 selection-null which measured what that search breadth manufactures: IS median
+1.378 mean R, OOS median +0.260 — 81% evaporates (docs/LONDON-AUDIT-STAGE3-selection-null.md).
The wall arm, chosen from FOUR pre-existing checks, showed ~zero shrinkage at its own
breadth and an honest forward expectation of ~+0.483 mean R.

The three questions this run answers, verbatim from the brief:
  1. Does DSR agree that the 29k sweep's best combo is not real?
  2. Does PBO on that candidate population come out high, as it should?
  3. Where do DSR/PBO and the shrinkage model disagree, and which is more trustworthy?

METHOD NOTES.
- Population, atoms and combination order are IMPORTED from scripts.london_overnight_audit
  — the calibration runs on the audit's own definitions, not a reimplementation.
- Each combination becomes a BOOK: its selected trades' R summed per day, zero on days it
  does not trade, over every day the population spans. Day-level, zero-filled series are
  the same shape Angus's correlation battery consumes, and day-level (never trade-level)
  splitting is the stage-3 leak rule. The gate's metric is the per-day Sharpe of that
  series; stage-3 selected on mean R per trade — both selections are reported.
- The DSR null is estimated from the CROSS-SECTIONAL VARIANCE of the trial Sharpes (the
  variance-of-Sharpes form). 29,161 singles-and-pairs are massively correlated/nested;
  charging a nominal count would over-deflate. This is the exact failure mode our
  shrinkage model has (it charges nominal breadth), so the wall arm is also scored at its
  OWN four-check breadth vs wrongly charged at 29k breadth, to show the difference.
- Selection floors mirror the audit: stage-3's n>=25 pooled for the headline eligible set;
  the full unfloored set is reported as sensitivity. PBO runs at the paper-standard S=16.

Output: docs/VALIDATION-GATE-CALIBRATION.md + docs/validation_gate_calibration.json.
Requires output/l3_features_london_fit.parquet (rebuild: L0->L3 chain, --span fit).
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.london_overnight_audit import atoms, population
from src.validation import deflated_sharpe_ratio, pbo_cscv, sharpe_ratio

DOCS = ROOT / "docs"
N_BLOCKS = 16          # CSCV paper standard: C(16,8) = 12,870 splits
MIN_N_POOLED = 25      # stage-3's selection floor — the space the shrinkage model searched
CHECKS = ["W", "FAR", "ROOM", "ASIA"]  # the wall arm's actual selection space (stage 3)


def day_matrix(P: pd.DataFrame, masks: np.ndarray) -> tuple[np.ndarray, list[str]]:
    """(n_days x n_combos) day-summed R series per combo, zero-filled on no-trade days."""
    days = sorted(P.day.unique())
    day_ix = {d: i for i, d in enumerate(days)}
    rows = np.array([day_ix[d] for d in P.day])
    R = P.R.to_numpy(float)
    D = np.zeros((len(days), len(P)))
    D[rows, np.arange(len(P))] = R
    out = np.empty((len(days), masks.shape[1]))
    for lo in range(0, masks.shape[1], 4000):  # chunk the bool->float cast
        out[:, lo : lo + 4000] = D @ masks[:, lo : lo + 4000].astype(float)
    return out, days


def col_sharpes(X: np.ndarray) -> np.ndarray:
    """Per-column per-day Sharpe; NaN where the column has no variance."""
    mean = X.mean(axis=0)
    sd = X.std(axis=0, ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        sr = np.where(sd > 0, mean / sd, np.nan)
    return sr


def main() -> None:
    src = ROOT / "output/l3_features_london_fit.parquet"
    if not src.exists():
        raise SystemExit(
            f"{src} missing — rebuild the London fit chain first "
            "(build_l0/l1/l2/l3_*_london --span fit)"
        )

    P = population()
    A = atoms(P)
    names = [n for n, _ in A]
    M = np.column_stack([m for _, m in A])  # (rows, n_atoms) bool

    # every single and every pair, in the audit's own combination order
    pair_ix = list(itertools.combinations(range(len(names)), 2))
    B = np.empty((len(P), len(names) + len(pair_ix)), dtype=bool)
    B[:, : len(names)] = M
    for k, (i, j) in enumerate(pair_ix):
        B[:, len(names) + k] = M[:, i] & M[:, j]
    combo_names = names + [f"{names[i]} AND {names[j]}" for i, j in pair_ix]
    n_per = B.sum(axis=0)

    X, days = day_matrix(P, B)
    sr_all = col_sharpes(X)
    meanR_per_trade = np.where(n_per > 0, (P.R.to_numpy(float) @ B) / np.maximum(n_per, 1), -np.inf)

    eligible = n_per >= MIN_N_POOLED
    elig_ix = np.flatnonzero(eligible)
    sr_elig = sr_all[eligible]
    assert np.isfinite(sr_elig).all(), "an eligible combo produced a flat day series"

    # the two selection rules: the gate's (best Sharpe) and stage-3's (best mean R/trade)
    w_sr = int(elig_ix[np.argmax(sr_elig)])
    w_mr = int(elig_ix[np.argmax(meanR_per_trade[eligible])])

    dsr_sr = deflated_sharpe_ratio(X[:, w_sr], trial_sharpes=sr_elig)
    dsr_mr = deflated_sharpe_ratio(X[:, w_mr], trial_sharpes=sr_elig)
    # sensitivity: the null estimated from EVERY combo that has a live day series
    finite_all = np.isfinite(sr_all)
    dsr_sr_allnull = deflated_sharpe_ratio(X[:, w_sr], trial_sharpes=sr_all[finite_all])

    pbo_elig = pbo_cscv(X[:, eligible], n_blocks=N_BLOCKS, batch_size=128)
    pbo_all = pbo_cscv(X[:, finite_all], n_blocks=N_BLOCKS, batch_size=64)

    # the wall arm at its own breadth vs wrongly charged for a search it never ran
    wall = ((P.W == 1) | (P.FAR == 1)).to_numpy(bool)
    check_masks = np.column_stack([(P[c] == 1).to_numpy(bool) for c in CHECKS])
    Xw, _ = day_matrix(P, np.column_stack([wall, check_masks]))
    wall_series = Xw[:, 0]
    check_sharpes = col_sharpes(Xw[:, 1:])
    dsr_wall_own = deflated_sharpe_ratio(wall_series, trial_sharpes=check_sharpes)
    dsr_wall_29k = deflated_sharpe_ratio(wall_series, trial_sharpes=sr_elig)
    wall_meanR = float(P.R.to_numpy(float)[wall].mean())

    s3 = json.loads((DOCS / "london_audit_stage3.json").read_text()) \
        if (DOCS / "london_audit_stage3.json").exists() else {}

    res = {
        "population": {"n": len(P), "days": len(days),
                       "day_span": [days[0], days[-1]], "atoms": len(names),
                       "combinations": int(B.shape[1])},
        "eligible": {"floor_n": MIN_N_POOLED, "count": int(eligible.sum())},
        "winner_by_sharpe": {
            "cell": combo_names[w_sr], "n": int(n_per[w_sr]),
            "mean_R_per_trade": float(meanR_per_trade[w_sr]),
            "day_sharpe": float(sr_all[w_sr]),
            "psr_zero": dsr_sr.psr_zero, "sr0": dsr_sr.sr0, "dsr": dsr_sr.dsr,
            "dsr_all_combo_null": dsr_sr_allnull.dsr,
            "significant": dsr_sr.significant},
        "winner_by_meanR": {
            "cell": combo_names[w_mr], "n": int(n_per[w_mr]),
            "mean_R_per_trade": float(meanR_per_trade[w_mr]),
            "day_sharpe": float(sr_all[w_mr]),
            "psr_zero": dsr_mr.psr_zero, "sr0": dsr_mr.sr0, "dsr": dsr_mr.dsr,
            "significant": dsr_mr.significant},
        "pbo": {
            "eligible": {"pbo": pbo_elig.pbo, "n_trials": pbo_elig.n_trials,
                         "splits": pbo_elig.n_combinations, "slope": pbo_elig.slope,
                         "prob_oos_loss": pbo_elig.prob_oos_loss,
                         "days_used": pbo_elig.n_obs_used,
                         "days_dropped": pbo_elig.n_obs_dropped},
            "all_combos": {"pbo": pbo_all.pbo, "n_trials": pbo_all.n_trials,
                           "slope": pbo_all.slope,
                           "prob_oos_loss": pbo_all.prob_oos_loss}},
        "wall_arm": {
            "mean_R_per_trade": wall_meanR,
            "day_sharpe": float(sharpe_ratio(wall_series)),
            "n": int(wall.sum()),
            "dsr_at_own_breadth": {"n_trials": 4, "sr0": dsr_wall_own.sr0,
                                   "psr_zero": dsr_wall_own.psr_zero,
                                   "dsr": dsr_wall_own.dsr,
                                   "significant": dsr_wall_own.significant},
            "dsr_charged_at_29k": {"n_trials": dsr_wall_29k.n_trials,
                                   "sr0": dsr_wall_29k.sr0, "dsr": dsr_wall_29k.dsr}},
        "stage3_shrinkage_model": s3,
    }
    (DOCS / "validation_gate_calibration.json").write_text(json.dumps(res, indent=2))

    q1 = not dsr_sr.significant and not dsr_mr.significant
    q2 = pbo_elig.pbo >= 0.5
    agree_wall = dsr_wall_own.significant
    verdict_q1 = (
        "AGREES — the best combo is not distinguishable from best-of-search noise"
        if q1
        else "DISAGREES — DSR marks the sweep winner significant; "
        "investigate before trusting either tool"
    )
    verdict_q2 = (
        "AGREES — PBO says this selection procedure picks noise"
        if q2
        else "PBO comes out below 0.5 — the procedure retains some OOS ranking skill; "
        "see the reading below"
    )
    verdict_wall = (
        "Both frameworks land on the same side for the wall arm: real at its own breadth."
        if agree_wall
        else "NOTE: DSR does NOT confirm the wall arm at its own breadth — that is a "
        "finding, not a formatting problem; see the reading."
    )

    L = [
        "# Validation gate calibration — DSR + PBO vs the London 29k sweep\n",
        (
            "\n**Fit only. Sealed 2023/24 never loaded** (population comes through the "
            "audit's `fit_only()` guard).\n"
        ),
        (
            "\nThe gate (`src/validation`) is calibrated against the one case where the "
            "honest answer is already known by other means: the stage-2 combination sweep "
            "(clean null under the pre-registered bar) and the stage-3 selection-null "
            "(exhaustive search manufactures +1.378 IS median mean R and keeps +0.260 OOS; "
            "the wall arm shows ~zero shrinkage at its own 4-check breadth).\n"
        ),
        (
            f"\nPopulation: n={len(P)} trades over {len(days)} days "
            f"({days[0]} -> {days[-1]}), {len(names)} atoms, {B.shape[1]:,} combinations "
            f"(all singles and pairs, the audit's own generator). Each combination is "
            f"scored as a BOOK: day-summed R, zero-filled on no-trade days, per-day "
            f"Sharpe. Eligibility floor for selection: n >= {MIN_N_POOLED} pooled "
            f"(stage-3's floor); {int(eligible.sum()):,} combinations qualify.\n"
        ),
        "\n## Q1 — does DSR agree the sweep's best combo is not real?\n",
        (
            f"\n| selection rule | cell | n | mean R | day SR | PSR (undeflated) | SR0 "
            f"(noise best-of-search) | **DSR** |\n|---|---|---|---|---|---|---|---|\n"
            f"| best day-Sharpe | `{combo_names[w_sr]}` | {n_per[w_sr]} | "
            f"{meanR_per_trade[w_sr]:+.3f} | {sr_all[w_sr]:.3f} | {dsr_sr.psr_zero:.4f} | "
            f"{dsr_sr.sr0:.3f} | **{dsr_sr.dsr:.4f}** |\n"
            f"| best mean R (stage-3's rule) | `{combo_names[w_mr]}` | {n_per[w_mr]} | "
            f"{meanR_per_trade[w_mr]:+.3f} | {sr_all[w_mr]:.3f} | {dsr_mr.psr_zero:.4f} | "
            f"{dsr_mr.sr0:.3f} | **{dsr_mr.dsr:.4f}** |\n"
        ),
        (
            f"\nThe undeflated PSR is the trap the sweep sets: the winner LOOKS "
            f"significant before the search is priced. The DSR null, estimated from the "
            f"cross-sectional variance of the {int(eligible.sum()):,} eligible trial "
            f"Sharpes (SD {np.std(sr_elig, ddof=1):.3f}), expects a best-of-search Sharpe "
            f"of {dsr_sr.sr0:.3f} from pure noise. Sensitivity: with the null estimated "
            f"from all {int(finite_all.sum()):,} live combinations instead, the best "
            f"combo's DSR is {dsr_sr_allnull.dsr:.4f}.\n"
        ),
        f"\n**Verdict Q1: {verdict_q1}** (significance screen: DSR >= 0.95).\n",
        "\n## Q2 — is PBO high on this candidate population, as it should be?\n",
        (
            f"\n| population | trials | splits (S={N_BLOCKS}) | **PBO** | degradation "
            f"slope | P[OOS loss] |\n|---|---|---|---|---|---|\n"
            f"| eligible (n>={MIN_N_POOLED}) | {pbo_elig.n_trials:,} | "
            f"{pbo_elig.n_combinations:,} | **{pbo_elig.pbo:.3f}** | "
            f"{pbo_elig.slope:+.3f} | {pbo_elig.prob_oos_loss:.3f} |\n"
            f"| all live combos | {pbo_all.n_trials:,} | {pbo_all.n_combinations:,} | "
            f"**{pbo_all.pbo:.3f}** | {pbo_all.slope:+.3f} | "
            f"{pbo_all.prob_oos_loss:.3f} |\n"
        ),
        (
            f"\nPBO reads: in what fraction of the {pbo_elig.n_combinations:,} "
            f"symmetric IS/OOS splits does the in-sample winner land at or below the "
            f"median out-of-sample? Coin-flip (~0.5+) means the selection procedure is "
            f"picking noise.\n"
        ),
        f"\n**Verdict Q2: {verdict_q2}** (PBO = {pbo_elig.pbo:.3f}).\n",
        "\n## Q3 — where the tools and the shrinkage model disagree\n",
        (
            "\nThe shrinkage model charges NOMINAL breadth. DSR's variance-of-Sharpes "
            "null charges EFFECTIVE breadth. The wall arm is the discriminating case — "
            "it was chosen from 4 pre-existing checks, not 29k combinations:\n"
        ),
        (
            f"\n| wall arm scored... | n_trials | SR0 | DSR | verdict |\n"
            f"|---|---|---|---|---|\n"
            f"| at its own breadth (4 checks) | 4 | {dsr_wall_own.sr0:.3f} | "
            f"**{dsr_wall_own.dsr:.4f}** | "
            f"{'survives' if dsr_wall_own.significant else 'not significant'} |\n"
            f"| wrongly charged at 29k breadth | {dsr_wall_29k.n_trials:,} | "
            f"{dsr_wall_29k.sr0:.3f} | {dsr_wall_29k.dsr:.4f} | what nominal charging "
            f"does |\n"
        ),
        (
            f"\nWall arm facts: n={int(wall.sum())}, mean R {wall_meanR:+.3f}/trade, day "
            f"Sharpe {sharpe_ratio(wall_series):.3f}, undeflated PSR "
            f"{dsr_wall_own.psr_zero:.4f}. Stage-3's matching numbers: 4-check shrinkage "
            f"{s3.get('median_shrinkage_4check', float('nan')):+.3f} R, honest forward "
            f"{s3.get('honest_forward', float('nan')):+.3f} R.\n"
        ),
        f"\n{verdict_wall}\n",
    ]
    (DOCS / "VALIDATION-GATE-CALIBRATION.md").write_text("".join(L))
    print(f"wrote {DOCS / 'VALIDATION-GATE-CALIBRATION.md'}")
    print(json.dumps(res, indent=2)[:2000])


if __name__ == "__main__":
    main()
