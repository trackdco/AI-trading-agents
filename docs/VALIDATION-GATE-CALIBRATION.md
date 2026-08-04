# Validation gate calibration — DSR + PBO vs the London 29k sweep

**Fit only. Sealed 2023/24 never loaded** (population comes through the audit's `fit_only()` guard).

The gate (`src/validation`) is calibrated against the one case where the honest answer is already known by other means: the stage-2 combination sweep (clean null under the pre-registered bar) and the stage-3 selection-null (exhaustive search manufactures +1.378 IS median mean R and keeps +0.260 OOS; the wall arm shows ~zero shrinkage at its own 4-check breadth).

Population: n=884 trades over 195 days (2025-06-02 -> 2026-07-13), 241 atoms, 29,161 combinations (all singles and pairs, the audit's own generator). Each combination is scored as a BOOK: day-summed R, zero-filled on no-trade days, per-day Sharpe. Eligibility floor for selection: n >= 25 pooled (stage-3's floor); 28,570 combinations qualify.

## Q1 — does DSR agree the sweep's best combo is not real?

| selection rule | cell | n | mean R | day SR | PSR (undeflated) | SR0 (noise best-of-search) | **DSR** |
|---|---|---|---|---|---|---|---|
| best day-Sharpe | `dep_resist>23 AND FAR==1` | 119 | +0.754 | 0.306 | 1.0000 | 0.283 | **0.6725** |
| best mean R (stage-3's rule) | `lvl_churn_30>6 AND FAR==1` | 33 | +1.224 | 0.179 | 1.0000 | 0.283 | **0.0042** |

The undeflated PSR is the trap the sweep sets: the winner LOOKS significant before the search is priced. The DSR null, estimated from the cross-sectional variance of the 28,570 eligible trial Sharpes (SD 0.069), expects a best-of-search Sharpe of 0.283 from pure noise. Sensitivity: with the null estimated from all 28,902 live combinations instead, the best combo's DSR is 0.6678.

**Verdict Q1: AGREES — the best combo is not distinguishable from best-of-search noise** (significance screen: DSR >= 0.95).

## Q2 — is PBO high on this candidate population, as it should be?

| population | trials | splits (S=16) | **PBO** | degradation slope | P[OOS loss] |
|---|---|---|---|---|---|
| eligible (n>=25) | 28,570 | 12,870 | **0.175** | -0.070 | 0.134 |
| all live combos | 28,902 | 12,870 | **0.175** | -0.070 | 0.134 |

PBO reads: in what fraction of the 12,870 symmetric IS/OOS splits does the in-sample winner land at or below the median out-of-sample? Coin-flip (~0.5+) means the selection procedure is picking noise.

**Verdict Q2: PBO comes out below 0.5 — the procedure retains some OOS ranking skill; see the reading below** (PBO = 0.175).

## Q3 — where the tools and the shrinkage model disagree

The shrinkage model charges NOMINAL breadth. DSR's variance-of-Sharpes null charges EFFECTIVE breadth. The wall arm is the discriminating case — it was chosen from 4 pre-existing checks, not 29k combinations:

| wall arm scored... | n_trials | SR0 | DSR | verdict |
|---|---|---|---|---|
| at its own breadth (4 checks) | 4 | 0.165 | **0.9747** | survives |
| wrongly charged at 29k breadth | 28,570 | 0.283 | 0.4105 | what nominal charging does |

Wall arm facts: n=213, mean R +0.483/trade, day Sharpe 0.271, undeflated PSR 1.0000. Stage-3's matching numbers: 4-check shrinkage -0.014 R, honest forward +0.483 R.

Both frameworks land on the same side for the wall arm: real at its own breadth.

## Reading (Brake session, 2026-08-04 — authored, not script-generated)

**Q1 is a clean AGREE.** Both selection rules' winners look overwhelming before
deflation (PSR 1.0000) and die after it (DSR 0.67 and 0.004 vs the 0.95 screen). The
stage-3 mean-R winner is the starkest case: +1.224 mean R per trade over 33 trades, and
DSR prices it at a 0.4% probability of being real once the search is charged. This is the
trap working exactly as designed.

**Q2's number needs care, and it is NOT a malfunction.** PBO = 0.175, not the >0.5 a
pure-noise population would give (the implementation provably returns ~0.5 on synthetic
noise: seeded 29,161-trial noise run gives PBO 0.499). The population is NOT pure noise —
the wall signal lives inside it, and hundreds of wall-flavoured combinations carry
diluted versions of it. CSCV asks only whether the IS winner beats the OOS *median* of
the same trial set; a wall-adjacent winner usually does. This is consistent with stage-3,
which found the same thing in magnitude terms: the exhaustive OOS median was +0.260 —
positive, just 81% smaller than in-sample. Rank persistence survives; magnitude mostly
does not (degradation slope 0.07: IS level carries ~no information about OOS level).
So PBO here answers "is there ANY signal in the population the selection can find?"
(yes — the wall), while DSR answers "is the SPECIFIC winner's edge real at its size?"
(no). Read together, they reproduce the audit's twin conclusions exactly: no elite cell,
one real signal.

**Q3 — the disagreement with the shrinkage model is confined to where we already knew it
was wrong.** The discriminating case is the wall arm. Charged at its own 4-check breadth,
DSR = 0.9747 — survives, matching stage-3's ~zero 4-check shrinkage. Charged nominally at
the full sweep breadth it would score 0.41 — the over-penalty our shrinkage model applies
to narrow searches by charging nominal grid size. The variance-of-Sharpes null fixes
precisely that failure mode and agrees with the shrinkage model everywhere else. Where
they disagree, the DSR form is the more trustworthy: it observes how correlated the
trials actually were instead of assuming independence.

**Caveats, stated plainly.** (1) The wall arm's 4-check DSR inherits stage-3's caveat
verbatim: the four checks were fitted on 2025 by the original canon, so "own breadth" is
a lower bound on the true search that produced them; the sealed holdout remains the only
test that owes nothing to this data. (2) The gate metric is the per-day Sharpe of
zero-filled day books; stage-3 selected on mean R per trade — both winners are reported
above and both die, so the conclusion does not hinge on the metric. (3) These are
screening statistics. Promotion still runs through funded-rules Monte Carlo and maxDD.

**Gate thresholds this calibration supports:** DSR >= 0.95 at the candidate's true
search breadth (trial Sharpes recorded at sweep time, never reconstructed after), and
PBO read as a population diagnostic alongside it, with the noise anchor at ~0.5. A
candidate must pass DSR; a PBO near 0.5 on its discovery population is a red flag that
the selection procedure itself found nothing.

**Population provenance.** `output/l3_features_london_fit.parquet` was regenerated this
session via the committed L0->L3 chain (the original was never committed — the burn rule
bit again); the rebuild reproduces the audit's population exactly (wall arm mean R
+0.48318075117370884 matches docs/london_audit_stage3.json to the last digit; n=884,
195 days, 241 atoms, 29,161 combinations). The artifact is now committed.
