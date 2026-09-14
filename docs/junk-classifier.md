# JUNK-TAIL MULTIVARIATE CLASSIFIER — FINDINGS

2026-08-08. First genuine multivariate attempt at identifying the junk
tail (`run_mfe_r < 0.5`, 1,000/3,153 fights = 31.7%, costing −1,098R
of the book's −392R) at decision time. Prior work (BR-97) tested
~11,500 univariate splits and 2-way interactions and found nothing
beyond a calibrated permutation null. This pass trains real multivariate
models — logistic regression (L1/L2) and gradient boosting — on all 112
decision-time features simultaneously, on the theory that a combination
of individually-weak features could separate the tail even when no
single split does.

**VERDICT UP FRONT: NO. The junk tail is not identifiable at entry from
this feature set, by any of the five models tested.** Real out-of-fold
AUC (0.49–0.52) does not clear the permutation null (mean ≈0.50) at any
feature-set × model combination — the largest deviation is z = +1.20
(20 permutations), well short of significance. The skip table confirms
this operationally: acting on the classifier's ranking does no better
than skipping a random slice of the book. Full detail below.

---

## 1. METHOD

**Data.** `output/htf_ma_census/race_wide.parquet` (3,153 fights) joined
on `scid` to `race_runs.parquet` (target: `is_junk = run_mfe_r < 0.5`,
and `reach_3r` for the money table) and `race_realexit.parquet`
(`real_out`, the book's realised R under the trader's actual exit rule,
for the money table). All three joins are 1:1 and complete — no fights
dropped.

**Target.** `is_junk = 1{run_mfe_r < 0.5}`. Base rate 31.7% (1,000/3,153),
confirmed to reproduce the brief's numbers exactly: book EV −392.06R
(−0.1243R/trade), non-junk EV +0.328R/trade, P(reach 3R) 25.1%
unselected / 36.7% with junk perfectly removed.

**Features — 112 decision-time columns**, built causally (every value
is computed from information at or before the decision bar; verified
against `scripts/race_wide_features.py`'s own causality discipline):
104 numeric/boolean + 8 categorical (`session`, `mech`, `tf_won`, `dow`,
`month`, `value_position`, `open_vs_value`, `daytype`).

**Exclusions (forbidden / outcome-derived):** `out`, `hit`, `mfe_r`,
`near_*`, `far_*`, `m1_hit/out/dist_r`, raw prices (`entry`, `stop`,
`ma15`), `w15_pts` (exact duplicate of `w15`), and `half` (an unrelated
frozen train/test split flag from a different study). `direction`/`dir`
were dropped in favor of `is_long` (same information).

**Flow/depth orientation fix.** Per the 2026-08-08 defect note in
`scripts/conviction_lib.py`, `delta_z` and `dep_imbalance` are raw-signed
in `race_wide` (not oriented by trade direction). Both were replaced
with `delta_z_oriented = delta_z × direction` and
`dep_imbalance_oriented = dep_imbalance × direction`. The library's
stacked-confirmation counts (`cc_flow`, `cc_flow_clean`, `cc_depth`,
`cc_all`, `cc_all_clean`, and their coverage-adjusted `_frac` versions)
were added as engineered multivariate-style features — the "how many
signals agree" construct is exactly the kind of combination a univariate
sweep cannot see.

**Risk-family flag (BR-43).** 14 features are mechanically coupled to
the R-denominator (`risk`) that both `run_mfe_r` (the target) and
`real_out`/`reach_3r` (the money-table outcomes) are scaled by:
`risk`, `risk_over_w`, `risk_over_atr30`, `w15`, `closeloc`, `rangex`,
`nearest_ahead_r`, `nearest_behind_r`, `ma15_ahead_r`,
`n_ahead_within_2r`, and `cc_flow`/`cc_flow_frac`/`cc_all`/`cc_all_frac`
(these last four inherit the coupling because they include the
Law-2-flagged `closeloc`/`rangex` signals). Two feature sets were run
throughout: **full** (112 features) and **clean** (98, risk-family
excluded). A model leaning on the full set could be measuring arithmetic
(large `risk` → mechanically small `run_mfe_r`), not the market.

**Cross-validation.** `GroupKFold(n_splits=5)` on `sess_day` (290 unique
days) — no session-day appears in both train and test for any fold.

**Models.** `sklearn` 1.9.0 (installed at the start of this task; not
present before). Logistic regression L1 (`liblinear`, C=0.5) and L2
(`lbfgs`, C=1.0), both with median imputation + missingness indicators +
standardisation + one-hot categoricals in a `ColumnTransformer` pipeline.
`HistGradientBoostingClassifier` (max_iter=150, max_depth=4,
learning_rate=0.06, min_samples_leaf=30, l2_regularization=1.0), using
native categorical splits and native NaN handling — no imputation
needed. Hyperparameters were sanity-checked against three alternative
configurations (deeper/shallower, more/fewer iterations); real OOF AUC
stayed in a tight 0.51–0.51 band regardless, so the result is not a
tuning artifact.

**Permutation calibration.** `is_junk` shuffled within each
(`session`, `mech`) cell (12 cells), full day-grouped 5-fold pipeline
refit on the shuffled label, OOF AUC recorded — same discipline as
`conviction_lib.permute`/BR-97. **Run count: 5 permutations for the four
logistic-regression combinations, extended to 20 for the two
gradient-boosting combinations** (HGB showed the only non-trivial
deviation at 5 draws, so the null was firmed up before reporting; the
first 5 of the 20 used one seed block, the other 15 a second, both
reported combined). This is below the "10+" ceiling requested for the
LR runs and disclosed as such — cutting cost was requested explicitly
after an earlier background attempt stalled; the LR nulls are already
tight (sd ≈0.017–0.020) and their z-scores are all |z|<0.5, so more
draws would not change the reading.

**Money table.** Out-of-fold predicted probabilities only. Fights
ranked by predicted junk probability; top 10/20/30% "skipped"; remaining
book's `real_out` (sum, mean) and `reach_3r` rate reported, against a
random-skip null of the same size (2,000 draws pooled, 1,000 per
session/mechanism slice), with the random null's 2.5/97.5 percentile
band as the significance bar.

---

## 2. HEADLINE: OUT-OF-FOLD AUC vs PERMUTATION NULL

| feature set | model | real OOF AUC | fold range | null mean ± sd (n perm) | null range | **z** |
|---|---|---|---|---|---|---|
| full  | LR-L2 | 0.4960 | 0.470–0.525 | 0.4977 ± 0.0195 (5)  | 0.461–0.515 | **−0.09** |
| full  | LR-L1 | 0.4911 | 0.471–0.513 | 0.4994 ± 0.0182 (5)  | 0.465–0.516 | **−0.45** |
| full  | HGB   | 0.5109 | 0.480–0.548 | 0.4984 ± 0.0161 (20) | 0.468–0.532 | **+0.77** |
| clean | LR-L2 | 0.5008 | 0.475–0.526 | 0.4955 ± 0.0194 (5)  | 0.459–0.516 | **+0.27** |
| clean | LR-L1 | 0.4945 | 0.474–0.512 | 0.4985 ± 0.0171 (5)  | 0.466–0.514 | **−0.23** |
| clean | HGB   | 0.5222 | 0.488–0.560 | 0.5013 ± 0.0174 (20) | 0.468–0.530 | **+1.20** |

**No model, in any feature set, clears the permutation null.** The best
result — HGB on the risk-family-free feature set, AUC 0.522 — sits 1.2
standard deviations above a null centred at 0.501; conventionally
z ≥ ~2 is the bar for "worth a second look," and this pass doesn't reach
half that. Removing the mechanically risk-coupled features (`clean` set)
did not hurt performance — if anything it helped slightly (0.511→0.522
for HGB) — which argues against even the modest full-set signal being
arithmetic, but the honest reading is that neither number is
distinguishable from noise. This is the same shape of result as BR-97
(real 130 survivors vs null 112.0±17.1, z=+1.05): **a fully multivariate
model, given every decision-time variable simultaneously, lands in the
same place univariate splits did.**

**Precision/recall** (base rate 31.7%): at the default 0.5 probability
threshold the models flag almost nothing (HGB-clean: 124/3,153 fights,
precision 36.3%, recall 4.5%) — too conservative to be useful. At a
threshold matched to the money table's top-30%-flagged operating point,
precision is 32–34% against a 31.7% base rate — a **1–2 point lift**,
consistent with the AUC finding that there is at most a sliver of signal
and it is not reliably distinguishable from chance.

---

## 3. THE SKIP TABLE (the money table)

Best pooled model by real AUC: **clean · HGB** (still not permutation-significant — reported because it is the strongest candidate, not because it is validated).

| cut | n | book EV (real_out, sum) | EV/trade | P(reach 3R) |
|---|---|---|---|---|
| full book (0% skipped) | 3,153 | −392.06R | −0.1243R | 25.06% |
| **skip top 10% (model)** | 2,838 | −326.10R | −0.1149R | 25.16% |
| skip random 10% (null, mean of 2,000; 95% CI) | 2,838 | −352.27R [−415.6, −292.0] | −0.1241R [−0.146, −0.103] | 25.06% [24.5, 25.6] |
| **skip top 20% (model)** | 2,522 | −260.62R | −0.1033R | 25.54% |
| skip random 20% (null; 95% CI) | 2,522 | −313.40R [−394.8, −233.4] | −0.1243R [−0.157, −0.093] | 25.05% [24.3, 25.8] |
| **skip top 30% (model)** | 2,207 | −220.15R | **−0.0998R** | **25.65%** |
| skip random 30% (null; 95% CI) | 2,207 | −273.59R [−363.1, −180.4] | −0.1240R [−0.165, −0.082] | 25.06% [24.1, 26.1] |

**The model's best row (skip top 30%) lands inside the random-skip
null's own 95% interval on every metric** — EV/trade −0.0998R sits
comfortably inside [−0.165, −0.082], and P(3R) 25.65% sits inside
[24.1%, 26.1%]. Skipping the model's top-30%-riskiest fights is not
distinguishable from skipping a random 30%.

For comparison, `full` · HGB (real AUC 0.511, the un-cleaned set) at
skip-10% is actually **worse than random** (model EV −0.1283R vs random
mean −0.1241R) — the ranking is not even monotonically helpful. Across
all five models tested (LR-L1/L2 × full/clean, HGB × full/clean), no
skip fraction on any model beats its own random-skip 95% CI. Full tables
for every model × fraction are saved at
`/tmp/claude-0/.../scratchpad/junk_classifier/money_table_*.csv`.

**Against the benchmark that matters**: the trader's exit needs
P(3R) ≥ 28.3% to break even. Unselected the book runs 25.1%; perfect
junk removal would reach 36.7% (+11.6 points). The best this classifier
achieves, at its most aggressive and statistically unsupported cut, is
25.65% (+0.6 points) — **about 5% of the available gap, and not
significantly different from the 25.06% a random skip already gets by
arithmetic alone** (dropping any 30% of a losing book improves its
per-trade average somewhat by construction; the question is whether the
model's 30% is a *better* 30% than random, and it is not, measurably).

---

## 4. WHAT LOSERS SHARE (feature importance) — read this section skeptically

Because no model clears the permutation null, nothing below is a
validated finding — it describes what the strongest model fit to, not
a confirmed driver. Reported per the task's requirement, with the
risk-family flagged.

**HGB, permutation importance (AUC drop), averaged across the 5 OOF
folds' own held-out data, 3 repeats/fold:**

| feature set | top features (AUC-drop, all ≤0.009 — tiny) | risk-family present? |
|---|---|---|
| full | `volx` (.0061), `prev_out_sess` (.0041), `prev_out_day` (.0040), `seq_day` (.0032), `bar_body_frac` (.0031), **`w15`** (.0030, flagged), `bar_closeloc_dir`, `disp_abs_w`, `ma15_vs_ma60_w`, `poc_dist_w` | `w15` at #6 |
| clean | `volx` (.0086), `ma15_vs_ma60_w` (.0057), `prev_out_sess` (.0049), `month` (.0048), `disp_abs_w` (.0037), `seq_day` (.0037), `cc_all_clean_frac` (.0034), `rv30_over_rv120` (.0031) | none (by construction) |

**Direction check** (junk-mean vs non-junk-mean, full population):
`ma15_vs_ma60_w` 0.130 vs 0.213 (junk trades enter with the 15m MA
closer to the 60m MA — weaker trend alignment); `px_vs_ma60_w` 0.148 vs
0.231 (same story, price side); `prev_out_sess` −0.076 vs −0.203 (junk
follows a *less bad* prior same-session result, i.e. no streak
punishment); `support_minus_resist` −0.78 vs +0.17 on the 80%-coverage
depth subsample (junk trades see less order-book support in their
direction) — but depth features were already refuted at chance-level by
BR-94 on this same population, so this is a repeat of a known dead end,
not new evidence. `volx`, `disp_abs_w`, `bar_body_frac`,
`cc_all_clean_frac` all show differences under 0.01 in absolute terms —
noise-level.

**LR (L1/L2) coefficients, averaged across fold-fitted models
(standardised, so magnitude ~ importance):** dominated by
**missingness indicators** (`missingindicator_ma60_slope30_w`,
`missingindicator_struct_spread_w`, `missingindicator_day_out_so_far`)
and single calendar dummies (`month_2`, `dow_0`) — i.e. the logistic
models' largest coefficients describe *when data was available* and
*which specific month*, not a market mechanism. This is exactly the
calendar/regime pattern BR-97 already found unvalidated (regime sweep:
84 clears vs 68–82 budget, zero validated). `cc_depth` /`cc_depth_frac`
(stacked depth confirmation) also rank high in both LR variants but
depth is BR-94-refuted. **No feature is large, directionally coherent,
non-mechanical, and consistent across both model families** — the
closest is `ma15_vs_ma60_w` / `px_vs_ma60_w` (trend-alignment proxies),
which appear in HGB's top 10 and LR's top 20, both pointing the same
direction (weaker trend alignment → more junk), but this is the kind of
single-variable, weak, plausible-sounding signal BR-97's five-agent
sweep already tested directly and found inside the null.

Bottom line: **removing the risk-family features cost nothing** (AUC
went up, not down, full→clean for HGB), so the modest full-set
importance of `w15` is not load-bearing. But neither feature set
produces a coherent, validated story — every top feature is small in
absolute effect and the model carrying them fails the permutation test.

---

## 5. PER SESSION / PER MECHANISM (never pooled for conclusions)

Skip-30% cut, `clean · HGB` model, OOF probabilities sliced by session/mechanism (model vs random-skip mean [95% CI]):

| slice | n | junk % | EV/trade, model | EV/trade, random [CI] | P(3R), model | P(3R), random [CI] |
|---|---|---|---|---|---|---|
| LONDON | 1,231 | 31.8% | −0.0851R | −0.1412R [−0.209, −0.076] | 27.84% | 26.65% [24.9, 28.3] |
| NY_AM  | 997   | 30.8% | −0.0695R | −0.0626R [−0.132, +0.011] | 23.07% | 23.41% [21.9, 24.9] |
| NY_PRE | 925   | 32.5% | −0.1455R | −0.1641R [−0.247, −0.084] | 25.50% | 24.79% [23.0, 26.6] |
| M1 | 1,541 | 30.4% | −0.0535R | −0.0823R [−0.142, −0.023] | 26.41% | 25.71% [24.3, 27.2] |
| M2 | 786   | 34.2% | −0.1362R | −0.1817R [−0.266, −0.109] | 25.64% | 24.66% [22.5, 26.5] |
| M3 | 826   | 31.8% | −0.1034R | −0.1512R [−0.238, −0.070] | 25.09% | 24.18% [22.3, 25.9] |

Every slice's model-skip point estimate sits inside its own random-skip
95% CI (NY_AM is the one slice where the model is nominally *worse* than
random on EV, still inside the CI). LONDON shows the largest apparent
gap (P(3R) 27.84% vs random 26.65%, EV −0.085R vs −0.141R) — closer to
the 28.3% breakeven line than any other slice, but still inside its own
null band and built from n=862 after a 30% skip, so this is not read as
a session-specific finding. No session or mechanism clears its
permutation-null-equivalent bar; the trader's standing rule (never pool
across sessions for conclusions) changes nothing here — the pooled null
result and the per-slice null results agree.

---

## 6. VERDICT

**NO — the junk tail is not identifiable at entry from the 112
decision-time variables in `race_wide.parquet`, using genuine
multivariate models (L1/L2-regularised logistic regression and gradient
boosting), day-grouped cross-validation, and permutation calibration.**

- Real out-of-fold AUC across all six feature-set × model combinations:
  0.491–0.522. Permutation-null AUC (label shuffled within
  session × mechanism, full pipeline refit): centred at 0.498–0.501 in
  every case. Maximum deviation: **z = +1.20** (clean-feature HGB, 20
  permutations) — not significant.
- The skip table confirms this operationally: ranking fights by
  predicted junk-probability and skipping the riskiest 10/20/30% does
  no better, on book EV or P(reach 3R), than skipping a random slice of
  the same size, in the pooled book and in every session and every
  mechanism individually.
- The best operating point found (skip top 30%, clean HGB) reaches
  P(3R) = 25.65%, a small step from the unselected 25.1% and nowhere
  near the 28.3% breakeven the trader's exit needs, let alone the 36.7%
  ceiling perfect junk removal would deliver — and even that small step
  is statistically indistinguishable from what a random 30% cut already
  achieves.
- This extends BR-97 (univariate + 2-way interactions, calibrated null,
  nothing survives) to the fully multivariate case: giving the model
  every decision-time variable at once — price state, structure
  geometry, continuous confluence, flow and depth (direction-corrected
  per the 2026-08-08 fix), volatility/trend regime, day type, calendar,
  sequence, cross-session carry, and the mechanically-flagged
  risk/`w15`/`closeloc`/`rangex` family — does not find a combination
  that separates the junk tail from the rest of the book beyond what
  shuffled labels already produce.
- What remains, per `FINDINGS-agent-sweep`'s closing note, is unchanged:
  whatever distinguishes a junk fight from a real one is not encoded in
  any bar-derived decision-time column measured here.

**Standing: fit-only, no holdout, report-only, nothing adopted, nulls
published.**

---

*Code and intermediate artifacts (feature builder, modeling harness,
permutation nulls, money tables, importance CSVs) are in
`/tmp/claude-0/-home-user-AI-trading-agents/a87daf6c-a595-5ece-94e9-4ca26a3ca172/scratchpad/junk_classifier/`
— not committed, per instructions. No existing parquet was modified.*
