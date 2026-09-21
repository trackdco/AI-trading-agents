# SWEEP — TWO-WAY INTERACTIONS (conditional / regime-switch structure)

2026-08-08. Fit-only, no holdout, report-only, nothing adopted. Governed by
`docs/DECLARATIONS-agent-sweep.md` (the five declared tests, reproduced by
`scripts.sweep_lib.test_split` — not reimplemented here). Data:
`output/htf_ma_census/race_wide.parquet` (3,153 fights × 126 cols), untouched.

**Scope discipline honored throughout:** LONDON, NY_PRE, NY_AM are never
pooled; M1/M2/M3 are never pooled with each other. "Cell" = one
session × mechanism (9 cells, all ≥ 40 rows: 280–617). Direction is handled
as a *conditioner* (`is_long`), not as a pre-split, so the 9 base cells
above are the only ones used — the `cells()` helper's dir-split cells were
not invoked, to avoid double-counting direction both as a cell split and as
a conditioner.

## COORDINATOR DEFECT NOTE — `out_pts`

The coordinator flagged that `out_pts` (outcome × risk) was left in
`predictors()` and would "survive" tautologically. Checked directly against
both lists used in this sweep: `out_pts` appears in **neither** the 14
conditioners nor the 25 predictors below (grep of the results table
confirms zero occurrences in the `pred` or `conditioner` columns). It was
used only in its correct, intended role — internally, inside
`test_split`, as the points-denominated control for declared test 3. No
counts in this report required correction.

## METHOD

**Conditioners (14).** Picked from the task's suggested list, mechanistic
regime/context switches, each producing two subgroups (A / complementary
B) inside a cell. Binary ones split on the flag; continuous ones split on
the **within-cell** median (so the cut point is cell-specific and is a
searched/data-defined split, not a pre-registered numeric threshold — flagged
here as such, per the declaration's SEARCHED convention):

| conditioner | split | why chosen |
|---|---|---|
| `trend_align` | ==1 / ==0 | HTF trend agreement with trade direction |
| `px_in_va` | ==1 / ==0 | price inside vs outside value area |
| `vwap_side_with_trade` | ==1 / ==0 | price on the favorable side of VWAP |
| `is_long` | ==1 / ==0 | direction, as a conditioner not a pre-split |
| `overlap` | >med / ≤med | day-level range overlap / concurrency regime |
| `rv30_over_rv120` | >med / ≤med | expanding vs contracting realized vol |
| `day_range_w` | >med / ≤med | wide vs narrow day so far |
| `n_struct_ahead` | >med / ≤med | crowded vs open structure ahead |
| `pos_in_range_dir` | >med / ≤med | favorable vs unfavorable position in day range |
| `slope_with_trade` | >med / ≤med | MA slope aligned vs against trade |
| `tmin` | >med / ≤med | late vs early in the session window |
| `daytype` | imbalanced / balanced | day-type regime (14 "unknown" rows dropped) |
| `seq_sess` | ==0 / >0 | first trade of the session vs a repeat |
| `tf_won` | ==2 / ≠2 | which timeframe won the race, as a subgroup only — never tested as a predictor (it is declared MECHANICAL) |

`open_space` from the suggested list was **dropped and replaced with
`overlap`**: `open_space` is 0 for 3,151 of 3,153 rows (2 non-zero), so no
cell could ever produce two usable arms from it — it would have wasted its
entire test budget on power failure.

**Predictors (25).** A focused mechanistic set spanning flow/depth,
structure/confluence, price-location, room-ahead, and bar-behavior
families — deliberately excluding the declared-MECHANICAL columns (`risk`,
`w15`, `w15_pts`, `risk_over_w`, `tf_won`, `closeloc`, `rangex`,
`risk_over_atr30`, `entry`, `stop`, `ma15`), since those auto-fail test 4
and would waste budget, and excluding every conditioner variable (no
predictor is also used as a conditioner, so no test conditions a variable
on itself):

flow/depth: `n_aff`, `cvd_slope30`, `delta_z`, `dep_imbalance`,
`vol30_over_vol240`, `dep_thickness_vs_day`, `thru_delta_conf`,
`flowconf`, `bp5opp` — structure/confluence: `conf_mean_dist_w`,
`conf_tightness_w`, `d5_conf`, `d15_conf`, `d30_conf`, `struct_spread_w`,
`support_minus_resist`, `support_wall_dist`, `support_wall_size` —
price-location: `px_vs_vwap_w`, `px_vs_poc_w`, `vwap_dist_w` — room-ahead:
`room_ahead_day_w`, `nearest_ahead_r` — bar behavior: `bar_body_frac`,
`disp_w`. (`dep_thickness_delta_5m` was in the original draft list but is
constant in this table — 1 unique value — and was swapped for
`vol30_over_vol240` before any test was run.)

**Test count.** 9 cells × 14 conditioners × 2 sides (A, complementary B) ×
25 predictors = **6,300 individual `test_split` calls**, covering **3,150**
distinct (cell, conditioner, predictor) interaction units. Each call runs
all five declared tests via `scripts.sweep_lib.test_split` unmodified; the
outcome column is `out` (R-multiple), with `out_pts` used automatically by
the library for test 3.

## FP BUDGET ARITHMETIC (mandatory)

| stage | count | rate | naive chance expectation |
|---|---:|---:|---:|
| tests run | 6,300 | — | — |
| died on power/degenerate before any CI | 630 | 10.0% | — |
| got a day-clustered CI computed | 5,670 | 90.0% | — |
| **cleared test 1** (CI excludes zero) | **389** | 6.2% | 6,300 × 0.05 = **315** |
| **survived all five tests** (per side) | **326** | 5.2% | same budget, **315** |

389 T1-clears against a 315 budget is a 1.23× excess — small, and fully
explainable by non-independence: the 14 conditioners are not orthogonal
(several are correlated day-regime proxies — `day_range_w`,
`rv30_over_rv120`, `overlap`, `tmin` all move together on volatile days),
and several predictor families are internally correlated (`d5_conf` /
`d15_conf` / `d30_conf`; `disp_w` / `bar_body_frac`; `cvd_slope30` /
`delta_z` / `dep_imbalance` / `flowconf` / `thru_delta_conf`). Correlated
tests inflate the *count* of nominal clears without adding independent
evidence.

More tellingly: **326 full five-test survivors against the same 315
budget is a near-exact match** — this is the identical signature the
declaration itself names as consistent with nothing (BR-91: 9/110, BR-94:
9/160, both "at or near budget"). Per the task's own rule: **observed ≈
expected ⇒ the raw survivor count is not distinguishable from chance.**

That raw 326, however, is not yet a list of *interactions* — most of it is
main-effect bleed-through, diagnosed next.

### Main-effect bleed-through (why raw survivor counts overstate interaction evidence)

Grouping the 326 side-survivors by (cell, predictor): only **124** distinct
(cell, predictor) pairs account for all 326 hits. Of those,

- **72 pairs survive under more than one of the 14 conditioners** (up to
  12 of 14 for `LONDON/M1 × cvd_slope30`) — accounting for **268 of the
  326** side-survivals (82%). A predictor that clears regardless of which
  of 14 largely-unrelated conditioners is used to cut the cell is not
  conditional on any of them — it is a **main effect** of that predictor
  in that cell (other agents' job, explicitly out of this report's scope),
  showing through whichever arbitrary partition happens to preserve
  power. These 268 are excluded from interaction consideration.
- **52 pairs are conditioner-specific** (survive under exactly one of the
  14) — the only instances structurally consistent with "the split
  actually matters."

## SURVIVORS

**None certified.** Applying the declared five tests plus the task's
mandatory complementary-subgroup check (§5) to the conditioner-specific
pool:

1. Start from the 52 conditioner-specific side-survivals.
2. Require the complementary side to genuinely diverge — sign-flipped, or
   attenuated to under half the surviving side's magnitude (a disclosed,
   stricter operationalization of "does not work in the complementary
   subgroup" than bare non-survival, since a complementary side can fail
   the five-test bar by a hair while still pointing the same way at
   similar size — that is a power artifact, not an interaction).
3. **44 of 3,150 units (1.4%) pass both filters.**
4. Cross-checked the 44 for replication (same conditioner × predictor,
   consistent sign, consistent winning side, in an independent cell):
   **exactly one** pair replicates —
   `n_struct_ahead × vwap_dist_w`, NY_PRE, sides B (`n_struct_ahead ≤
   median`) in **both** M1 and M2. Every other one of the 44 is a
   singleton with no echo anywhere else in the grid — the expected
   fingerprint of noise scattered across a large correlated search, not
   of systematic conditional structure. (One other repeated pair,
   `vwap_side_with_trade × disp_w`, appears in NY_AM/M1 and NY_PRE/M1 but
   with **opposite sign** — contradicting rather than corroborating
   itself, and is treated as noise.)

**The one candidate examined in full, and why it is reported but not
certified:**

`NY_PRE / M1`, conditioner `n_struct_ahead` (median split, split point 7),
predictor `vwap_dist_w`:
- Side A (`n_struct_ahead > 7`, n=182): CI [-0.94, 0.59] — spans zero, does not clear.
- Side B (`n_struct_ahead ≤ 7`, n=256, n_a=128/n_b=128, days ok): dev
  **-0.539R**, CI **[-1.02, -0.10]** (clears), points control -5.65 (same
  sign), ρ(var, risk)=0.025 (not mechanical), half A -0.32 / half B -0.80
  (same sign, both ≥ 1/3 of -0.539) → **survives all five**.
- Complementary check: side A does not clear at all (dev -0.11, CI spans
  zero) → conditioning genuinely matters in this cell.

`NY_PRE / M2`, same conditioner (median split, split point 3), same
predictor:
- Side A (`n_struct_ahead > 3`, n=87): CI [-0.74, 1.00] — spans zero.
- Side B (`n_struct_ahead ≤ 3`, n=156, n_a=78/n_b=78, days ok): dev
  **-0.642R**, CI **[-1.30, -0.03]**, points control -8.07 (same sign),
  ρ=0.003, half A -0.62 / half B -0.27 (same sign, both ≥ 1/3) →
  **survives all five**. Side A does not clear (dev +0.06) →
  complementary check passes again.

Read literally against the declared rule plus the task's complementary
check, this is two independently-passing cells with a consistent story
(price farther below VWAP tends to travel farther, and only when the path
ahead isn't already crowded with structure) — the shape a real interaction
should have. **It is not certified as a survivor here** for three stated
reasons: (a) it is one hit out of 44 similarly-qualified one-off
candidates drawn from a 6,300-test search whose raw all-five-tests count
already sits at the chance budget — a single technically-qualifying case
emerging from that pool is not strong evidence on its own; (b) NY_PRE/M1
and NY_PRE/M2 are **not independent samples** — they are the same
calendar days scored through two different mechanisms, so this is
corroboration within one session's data, not external replication; (c)
the same conditioner/side (`n_struct_ahead ≤ med`, NY_PRE/M2) produces a
sign-flipping half-split for a *different* predictor (`disp_w`, see
near-misses below) in the identical subgroup, showing that subgroup is not
uniformly clean. It is flagged prominently as the search's single most
notable pattern and nothing more.

**No survivor is reported for LONDON or NY_AM.** No survivor is reported
for any conditioner other than `n_struct_ahead`, and even that one is
declined.

## KILLED BY POWER

630 of 6,300 tests (10.0%) died before a CI was even attempted: 625 on the
n≥40 / ≥10-per-arm / ≥3-days-per-arm floor, 5 more on a degenerate
(constant) predictor inside the subgroup. Breakdown:

- **217 of the 252 (cell × conditioner × side) subgroups** lost at least
  one of their 25 predictors to power (mostly predictor-specific
  missingness pushing n or day-count under the floor within an
  already-thin subgroup).
- **Only 2 subgroups were dead for every predictor**: `LONDON/M2 ×
  vwap_side_with_trade==0` and `NY_AM/M2 × n_struct_ahead>med`.
- Power deaths concentrate in the smaller M2/M3 cells (LONDON/M2: 106,
  LONDON/M1: 95, LONDON/M3: 83; NY_AM/M1 the least-hit at 25) and in
  conditioners that cut furthest from 50/50 or interact badly with
  predictor NA patterns — `vwap_side_with_trade` alone accounts for 125 of
  the 625 (20%), `n_struct_ahead` for 69.

This is the expected, correct behavior of the power floor on conditioned
subgroups — shrinking the cell twice (once for session×mech, once for the
conditioner) hits exactly the small M2/M3 cells hardest, as it should.

## NEAR-MISSES (clears test 1, fails exactly one more — not survivors)

Three illustrative cases, one per failure mode, out of 63 total
one-test-away misses:

- **NY_PRE/M2, `trend_align==1`, `d30_conf`** (n=126): dev -1.11R, CI
  [-2.08, -0.32] clears; points control agrees; ρ=−0.02 not mechanical;
  but half A -2.00 / half B **-0.36**, and 0.36 is just under 1/3 of 1.11
  (0.37) — genuinely a hair's-breadth miss, driven almost entirely by one
  day-half.
- **NY_PRE/M2, `n_struct_ahead≤med`, `disp_w`** (n=156, the same subgroup
  as the one candidate above): dev -0.65R, CI [-1.19, -0.10] clears; but
  half A -1.24 / half B **+0.05** — halves disagree in sign outright. This
  sits in the exact same conditioned subgroup as the reported candidate
  and is a direct caution against trusting that subgroup too far.
- **NY_PRE/M2, `vwap_side_with_trade==0`, `disp_w`** (n=40 — right at the
  power floor, n_a=n_b=20): dev -1.37R, CI [-3.01, -0.01] clears; but half
  A -0.04 / half B -1.93 — one half carries the entire effect. Classic
  thin-cell lucky-half pattern.

(`delta_z` also repeatedly clears test 1 but is killed by LAW2 —
ρ(delta_z, risk) run 0.57–0.71 in several conditioned subgroups, well
over the 0.4 mechanical threshold, even though `delta_z` itself is not on
the declared MECHANICAL list. Correctly caught by test 4 regardless.)

## WHAT THE INTERACTION SEARCH SAYS

6,300 tests were run across 14 regime conditioners × 25 predictors × 9
session×mechanism cells. The naive false-positive budget is 315 clears;
389 tests cleared test 1 and 326 survived all five — both essentially at
budget, the same signature the declaration itself treats as
indistinguishable from chance. Diagnosing the raw 326 further shows 82% of
it is main-effect bleed-through (a predictor's unconditional relationship
with the outcome showing through whichever of the 14 conditioners
happened to preserve power), not conditional structure. After removing
that and applying the complementary-subgroup requirement the task
mandates, 44 of 3,150 candidate units (1.4%) remain, and of those exactly
one shows any cross-cell corroboration — which is itself two
non-independent draws on the same calendar days, and is explicitly
declined as a survivor for the reasons stated above.

**The interaction search finds no conditional/regime-switch structure
that survives scrutiny in any of LONDON, NY_PRE, or NY_AM.** This is a
null result and, per the declaration's own stated prior, the expected and
publishable outcome. The single near-corroborated pattern
(`n_struct_ahead × vwap_dist_w`, NY_PRE) is documented in full rather than
discarded, but is not put forward as a finding.
