# SWEEP — day/regime/sequence/cross-session context (2026-08-08)

Scope: day classification, calendar, volatility/trend regime, sequence/streak,
and day-location variables, tested per session (LONDON / NY_PRE / NY_AM),
never pooled, mechanisms never pooled with each other. All five declared
tests from `docs/DECLARATIONS-agent-sweep.md` via `scripts.sweep_lib.test_split`
— no statistics reimplemented. Fit-only, no holdout, report-only, nothing
adopted, per the governing declaration's standing.

**Housekeeping note (coordinator defect alert):** `out_pts` (outcome
re-scaled to points) was briefly missing from `sweep_lib.OUTCOME_COLS` and
could have entered a variable list as a tautological predictor. Checked:
`out_pts` never appears anywhere in this agent's variable list, sweep
script, or results (`grep`/`base_var==` count = 0). It is used only, and
correctly, as the points-control **target column** inside `test_split`'s
built-in test 3 — exactly its intended role. No correction needed here.

---

## 1. SCOPE AND COUNTS

**Variable set** (as assigned): 2 day-classification numerics
(`inventory_pts`, `overlap`) + 8 volatility/activity-regime numerics + 6
trend/structure numerics + 7 sequence/streak numerics (4 of which — the
"streak" R-valued columns — also got an explicit sign split, prior-winner
vs prior-loser-or-flat, on top of the default median split) + 7
day-location numerics = **30 numeric variables**, each run as an
above/below-median split in every qualifying cell, plus 4 extra sign
splits. Categorical variables `daytype`, `value_position`, `open_vs_value`,
`dow`, `month` were run **level-vs-rest** in every cell, per instruction.

**Level counts, dataset-wide** (many fail the per-cell power floor by
construction — expected and correct):
- `daytype`: imbalanced 1792, balanced 1347, unknown 14
- `value_position`: inside 1347, above 825, below 493, overlap_up 290,
  overlap_dn 184, missing 14
- `open_vs_value`: in_value 2163, above_value 607, below_value 369,
  missing 14
- `dow`: Mon 601, Tue 613, Wed 680, Thu 665, Fri 594 (Mon–Fri only)
- `month`: Jan 192, Feb 206, Mar 233, Apr 226, May 222, **Jun 535**, **Jul
  330**, Aug 232, Sep 288, Oct 226, Nov 222, Dec 241. **Caveat:** the
  sample spans 2025-06-02 → 2026-07-15 (13.5 months), so Jun and Jul each
  pool two different calendar years (2025 and 2026) under one label —
  roughly double the days of every other month. Any June/July "finding"
  may be two unrelated years' coincidence, not a seasonal effect; flagged
  below.

**Cells:** 27 (LONDON/NY_PRE/NY_AM × M1/M2/M3 × {both, long, short}, per
`cells()`).

**Tests run:** 1,635 total `test_split` invocations (801 numeric-median,
99 numeric-sign, 735 categorical level-vs-rest, including levels that
never reach the CI stage because they fail the power floor immediately).
**1,358** of those reached the CI stage (test 1 computed) — the honest
denominator for a false-positive rate, since a test that never computes a
CI cannot spuriously clear one.

**Clears (test 1 only):** 84
**Survivors (all five declared tests):** 66

### False-positive budget — mandatory arithmetic

- On eligible tests (tests that actually reached the CI stage):
  **1,358 × 0.05 = 67.9** expected spurious clears at 95%. **Observed: 84**
  → **1.24×** budget.
- On all attempted tests (the convention the top-level declaration itself
  uses for its headline number): **1,635 × 0.05 = 81.8**. **Observed: 84**
  → **1.03×** budget, i.e. statistically indistinguishable from pure noise.
- Either denominator lands this sweep in the same place every prior pass
  on this family has landed: **at or near the false-positive budget**
  (BR-91: 9/110 ≈1.6×; BR-94: 9/160 ≈1.1×). That is the headline
  scope-level result before any individual row is inspected: **this
  variable family, in aggregate, is statistically indistinguishable from
  noise.**

**Why 66 "survivors" does not mean 66 findings.** The declared five-test
filter is not a multiple-comparisons correction, and it is not designed to
catch two specific problems that are rampant in this variable set:
(a) **near-duplicate columns** — e.g. `ma15_slope30_w` and
`slope_with_trade` are literally identical inside any direction-only cell
(`slope_with_trade` = the raw slope signed by trade direction, so a
long-only or short-only subset makes them the same split); `dist_day_low_w`
and `room_ahead_day_w` are identical for short trades; `px_vs_on_lo_w`
correlates 0.96 with `dist_day_low_w`; `ma15_vs_ma60_w` correlates 0.89
with `px_vs_ma60_w`. Testing both counts one signal twice or three times.
(b) **cell nesting** — every `SESSION/MECH` cell's `long` and `short`
subsets share the same trades and the same frozen `half` assignment as the
parent cell, so a variable that clears in the parent very often
mechanically clears in a subset too. After collapsing exact/near-duplicate
variables and nested cells, the 66 rows reduce to roughly **20–25
independent cell×signal claims** — see §2 for the clustering.

---

## 2. SURVIVORS (mechanical — passed all five declared tests)

Full list below: `dev` = mean(arm A) − mean(arm B) in R, arm A is the
above-median / level-true side; `halves` = split-half A / B (both must
share sign and be ≥⅓ the full effect, per T2); `pts Δ` = points-control
(T3); `ρ_risk` = mechanical-coupling check (T4, must be <0.4 abs to
survive); `days(a/b)` = **distinct sess_day count per arm** (required
sanity check, not part of the formal five tests) — **THIN flags any
survivor whose smaller arm rests on fewer than 15 distinct days.**

8 of 66 are THIN by that flag — including the exact scenario the task
called out in advance (`LONDON/M2/short month=12`, 8 days in the minority
arm). Thin survivors are not treated as findings regardless of passing the
mechanical filter.

### SURVIVORS TABLE

| session | cell | variable | n (a/b) | dev(R) | 95% CI | halves(a/b) | pts Δ | ρ_risk | days(a/b) | flag |
|---|---|---|---|---|---|---|---|---|---|---|
| LONDON | LONDON/M1 | atr30_over_w | 308/309 | +0.617 | [+0.29, +0.94] | +0.48 / +0.72 | +5.32 | -0.06 | 150/163 |  |
| LONDON | LONDON/M1 | ma60_slope30_w | 239/239 | -0.349 | [-0.69, -0.02] | -0.29 / -0.41 | -2.76 | -0.13 | 130/133 |  |
| LONDON | LONDON/M1/long | atr30_over_w | 135/136 | +1.078 | [+0.56, +1.65] | +0.92 / +1.19 | +11.14 | -0.15 | 70/67 |  |
| LONDON | LONDON/M1/long | inventory_pts | 133/138 | +0.633 | [+0.04, +1.20] | +0.22 / +0.95 | +6.24 | +0.09 | 60/61 |  |
| LONDON | LONDON/M1/long | month=7 | 41/230 | -0.796 | [-1.36, -0.21] | -1.00 / -0.67 | -9.65 | -0.07 | 19/102 |  |
| LONDON | LONDON/M1/short | inventory_pts | 173/173 | -0.502 | [-0.87, -0.15] | -0.35 / -0.59 | -5.97 | -0.02 | 76/84 |  |
| LONDON | LONDON/M2 | month=12 | 28/252 | -0.535 | [-1.10, -0.04] | -0.94 / -0.25 | -0.66 | -0.22 | 10/127 | THIN |
| LONDON | LONDON/M2 | pos_in_range_dir | 140/140 | -0.366 | [-0.67, -0.05] | -0.36 / -0.39 | -5.90 | +0.13 | 67/87 |  |
| LONDON | LONDON/M2/long | dow=Fri | 21/128 | -0.551 | [-0.93, -0.05] | -0.76 / -0.44 | -4.64 | +0.02 | 13/69 | THIN |
| LONDON | LONDON/M2/long | dow=Tue | 28/121 | +0.601 | [+0.02, +1.36] | +0.74 / +0.50 | +5.59 | +0.01 | 16/66 |  |
| LONDON | LONDON/M2/long | ma15_vs_ma60_w | 60/61 | +0.481 | [+0.03, +0.91] | +0.77 / +0.33 | +6.61 | -0.27 | 32/40 |  |
| LONDON | LONDON/M2/short | ma15_vs_ma60_w | 48/48 | +0.895 | [+0.40, +1.39] | +0.88 / +0.88 | +7.93 | -0.10 | 27/30 |  |
| LONDON | LONDON/M2/short | month=12 | 23/108 | -0.601 | [-1.12, -0.13] | -1.06 / -0.39 | -3.39 | -0.30 | 8/57 | THIN |
| LONDON | LONDON/M2/short | px_vs_ma60_w | 48/48 | +0.884 | [+0.41, +1.35] | +0.71 / +0.99 | +7.77 | -0.17 | 29/30 |  |
| LONDON | LONDON/M2/short | trend_align | 47/84 | -0.700 | [-1.08, -0.28] | -0.57 / -0.78 | -5.52 | +0.10 | 29/39 |  |
| LONDON | LONDON/M3 | dow=Thu | 71/263 | -0.395 | [-0.68, -0.11] | -0.15 / -0.61 | -3.72 | -0.05 | 35/133 |  |
| LONDON | LONDON/M3 | month=6 | 56/278 | -0.605 | [-0.93, -0.23] | -0.74 / -0.41 | -5.61 | +0.04 | 27/141 |  |
| LONDON | LONDON/M3 | month=7 | 34/300 | +0.910 | [+0.15, +1.91] | +1.13 / +0.71 | +4.73 | +0.03 | 22/146 |  |
| LONDON | LONDON/M3 | slope_with_trade | 167/167 | -0.434 | [-0.75, -0.15] | -0.54 / -0.36 | -3.06 | -0.00 | 93/116 |  |
| LONDON | LONDON/M3/long | ma15_slope30_w | 94/95 | -0.500 | [-0.92, -0.07] | -0.17 / -0.77 | -3.55 | -0.09 | 51/72 |  |
| LONDON | LONDON/M3/long | month=6 | 38/151 | -0.667 | [-1.10, -0.09] | -0.78 / -0.67 | -6.23 | +0.03 | 19/89 |  |
| LONDON | LONDON/M3/long | px_vs_on_hi_w | 94/95 | -0.484 | [-0.87, -0.13] | -0.33 / -0.62 | -4.21 | -0.10 | 45/76 |  |
| LONDON | LONDON/M3/long | slope_with_trade | 94/95 | -0.500 | [-0.92, -0.07] | -0.17 / -0.77 | -3.55 | -0.09 | 51/72 |  |
| LONDON | LONDON/M3/short | ma15_vs_ma60_w | 57/57 | +0.547 | [+0.02, +1.08] | +0.37 / +0.68 | +4.08 | -0.28 | 41/35 |  |
| LONDON | LONDON/M3/short | open_vs_value=above_value | 23/122 | -0.554 | [-0.97, -0.14] | -0.56 / -0.55 | -5.44 | -0.13 | 19/72 |  |
| NY_AM | NY_AM/M1 | inventory_pts | 235/246 | +0.506 | [+0.23, +0.79] | +0.49 / +0.52 | +11.98 | -0.16 | 115/110 |  |
| NY_AM | NY_AM/M1 | ma15_vs_ma60_w | 197/197 | +0.328 | [+0.00, +0.65] | +0.21 / +0.48 | +10.02 | -0.26 | 92/92 |  |
| NY_AM | NY_AM/M1 | month=11 | 35/451 | -0.543 | [-0.93, -0.03] | -0.50 / -0.59 | -16.99 | +0.04 | 15/211 |  |
| NY_AM | NY_AM/M1 | open_vs_value=above_value | 93/393 | +0.615 | [+0.20, +1.09] | +0.67 / +0.57 | +7.90 | -0.12 | 45/181 |  |
| NY_AM | NY_AM/M1/long | atr30_over_w | 126/127 | +0.479 | [+0.10, +0.87] | +0.58 / +0.40 | +11.67 | -0.06 | 69/74 |  |
| NY_AM | NY_AM/M1/long | ma60_slope30_w | 106/106 | +0.444 | [+0.02, +0.87] | +0.30 / +0.61 | +16.50 | +0.01 | 55/65 |  |
| NY_AM | NY_AM/M1/long | month=11 | 21/232 | -0.757 | [-1.11, -0.31] | -0.92 / -0.56 | -24.05 | +0.09 | 9/108 | THIN |
| NY_AM | NY_AM/M1/short | day_out_so_far (sign>0) | 63/170 | +0.500 | [+0.02, +1.05] | +0.37 / +0.60 | +10.46 | -0.03 | 51/89 |  |
| NY_AM | NY_AM/M1/short | inventory_pts | 114/114 | +0.709 | [+0.30, +1.17] | +0.31 / +1.03 | +17.68 | -0.11 | 70/58 |  |
| NY_AM | NY_AM/M1/short | ma15_vs_ma60_w | 91/91 | +0.569 | [+0.07, +1.09] | +0.54 / +0.67 | +15.20 | -0.14 | 50/45 |  |
| NY_AM | NY_AM/M1/short | open_vs_value=above_value | 48/185 | +0.808 | [+0.15, +1.58] | +0.42 / +1.20 | +12.13 | -0.20 | 30/99 |  |
| NY_AM | NY_AM/M1/short | seq_sess | 105/128 | -0.541 | [-0.93, -0.13] | -0.40 / -0.63 | -14.76 | +0.01 | 64/108 |  |
| NY_AM | NY_AM/M1/short | trend_align | 67/166 | -0.583 | [-0.99, -0.17] | -0.71 / -0.51 | -18.59 | +0.17 | 33/99 |  |
| NY_AM | NY_AM/M2 | dow=Fri | 43/220 | -0.327 | [-0.62, -0.07] | -0.30 / -0.35 | -14.69 | +0.15 | 21/95 |  |
| NY_AM | NY_AM/M2/short | dow=Fri | 20/116 | -0.350 | [-0.73, -0.11] | -0.44 / -0.35 | -24.77 | +0.18 | 9/49 | THIN |
| NY_AM | NY_AM/M3 | on_range_w | 124/124 | +0.408 | [+0.15, +0.65] | +0.32 / +0.52 | +13.23 | +0.13 | 72/63 |  |
| NY_AM | NY_AM/M3 | slope_with_trade | 124/124 | -0.456 | [-0.72, -0.21] | -0.25 / -0.73 | -9.18 | -0.09 | 65/74 |  |
| NY_AM | NY_AM/M3/long | ma15_slope30_w | 63/63 | -0.704 | [-1.14, -0.35] | -0.66 / -0.74 | -13.65 | -0.15 | 32/41 |  |
| NY_AM | NY_AM/M3/long | slope_with_trade | 63/63 | -0.704 | [-1.14, -0.35] | -0.66 / -0.74 | -13.65 | -0.15 | 32/41 |  |
| NY_AM | NY_AM/M3/short | day_range_w | 61/61 | +0.338 | [+0.03, +0.67] | +0.34 / +0.32 | +14.44 | +0.03 | 40/30 |  |
| NY_AM | NY_AM/M3/short | on_range_w | 61/61 | +0.508 | [+0.21, +0.82] | +0.62 / +0.35 | +23.80 | +0.09 | 37/34 |  |
| NY_AM | NY_AM/M3/short | overlap | 58/64 | -0.378 | [-0.67, -0.09] | -0.31 / -0.49 | -10.59 | -0.08 | 34/33 |  |
| NY_PRE | NY_PRE/M1 | month=11 | 29/409 | -0.626 | [-1.05, -0.18] | -0.60 / -0.43 | -11.59 | +0.05 | 14/219 | THIN |
| NY_PRE | NY_PRE/M1 | month=4 | 27/411 | +1.351 | [+0.12, +2.80] | +0.64 / +2.49 | +16.77 | +0.05 | 19/214 |  |
| NY_PRE | NY_PRE/M1/short | dist_day_low_w | 122/123 | -0.672 | [-1.30, -0.08] | -0.44 / -0.95 | -7.76 | +0.04 | 68/77 |  |
| NY_PRE | NY_PRE/M1/short | dow=Mon | 55/190 | -0.753 | [-1.23, -0.26] | -0.68 / -0.80 | -9.73 | +0.07 | 31/107 |  |
| NY_PRE | NY_PRE/M1/short | px_vs_on_lo_w | 122/123 | -0.600 | [-1.24, -0.03] | -0.46 / -0.76 | -7.49 | +0.02 | 69/75 |  |
| NY_PRE | NY_PRE/M1/short | room_ahead_day_w | 122/123 | -0.672 | [-1.30, -0.08] | -0.44 / -0.95 | -7.76 | +0.04 | 68/77 |  |
| NY_PRE | NY_PRE/M2 | dist_day_high_w | 121/122 | +0.770 | [+0.30, +1.30] | +0.75 / +0.74 | +8.20 | -0.03 | 85/72 |  |
| NY_PRE | NY_PRE/M2 | dow=Fri | 56/187 | -0.465 | [-0.90, -0.07] | -0.70 / -0.30 | -1.28 | +0.13 | 32/111 |  |
| NY_PRE | NY_PRE/M2 | london_out_today | 116/127 | +0.548 | [+0.06, +1.08] | +0.63 / +0.49 | +5.33 | -0.09 | 66/77 |  |
| NY_PRE | NY_PRE/M2 | london_out_today (sign>0) | 116/127 | +0.548 | [+0.06, +1.08] | +0.63 / +0.49 | +5.33 | -0.11 | 66/77 |  |
| NY_PRE | NY_PRE/M2 | month=8 | 21/222 | -0.502 | [-0.97, -0.05] | -0.60 / -0.41 | -4.46 | -0.12 | 12/131 | THIN |
| NY_PRE | NY_PRE/M2 | value_position=below | 33/210 | -0.534 | [-0.97, -0.15] | -0.63 / -0.46 | -9.12 | -0.02 | 23/120 |  |
| NY_PRE | NY_PRE/M2/long | atr30_over_w | 72/72 | +0.519 | [+0.13, +0.89] | +0.58 / +0.39 | +6.79 | +0.16 | 47/49 |  |
| NY_PRE | NY_PRE/M2/long | on_range_w | 72/72 | +0.492 | [+0.11, +0.89] | +0.54 / +0.39 | +4.53 | -0.06 | 44/47 |  |
| NY_PRE | NY_PRE/M3 | dist_day_low_w | 122/122 | -0.413 | [-0.81, -0.01] | -0.75 / -0.15 | -3.94 | -0.15 | 73/73 |  |
| NY_PRE | NY_PRE/M3 | dow=Mon | 49/195 | -0.458 | [-0.84, -0.08] | -0.39 / -0.52 | -4.91 | -0.09 | 31/106 |  |
| NY_PRE | NY_PRE/M3 | month=4 | 24/220 | -0.593 | [-0.99, -0.20] | -0.68 / -0.46 | -4.75 | -0.09 | 12/125 | THIN |
| NY_PRE | NY_PRE/M3 | trend_align | 108/136 | +0.434 | [+0.01, +0.88] | +0.23 / +0.59 | +4.79 | +0.02 | 71/82 |  |
| NY_PRE | NY_PRE/M3/short | inventory_pts | 52/57 | -0.630 | [-1.22, -0.02] | -0.94 / -0.34 | -5.41 | -0.01 | 37/35 |  |

### Clustering the 66 rows into independent claims

- **Volatility/ATR regime (`atr30_over_w`), M1, positive** — LONDON/M1,
  LONDON/M1/long, NY_AM/M1/long, NY_PRE/M2/long formally survive; **every
  one of the 9 M1 cells across all three sessions has the same positive
  sign** (only 3 individually clear at n≈130–310; the rest are directionally
  consistent but CI-wide). This is the strongest, most cross-session-
  replicated pattern in the sweep. Still fit-only.
- **Momentum "with the trade" (`slope_with_trade` / `ma15_slope30_w`,
  identical inside direction-only cells), M3, negative** —
  LONDON/M3, LONDON/M3/long, NY_AM/M3, NY_AM/M3/long survive (4 rows = 2
  independent cells × parent+subset duplication); 8 of 9 M3 cells
  sign-agree negative (only NY_PRE/M3/short flips, and it's not
  significant). Pattern is **absent in NY_PRE**.
- **MA-alignment (`ma15_vs_ma60_w` / `px_vs_ma60_w`, r=0.89), mixed
  mechanism, mostly positive** — 5 survivor rows across M1 (NY_AM) and M2
  (LONDON, both directions), but LONDON/M1 direction cells for the *same*
  variable run negative (not significant) — session/mechanism dependent,
  not a clean single axis.
- **Calendar `dow=Fri`, M2, negative** — LONDON/M2/long, NY_PRE/M2,
  NY_AM/M2, NY_AM/M2/short (nested in NY_AM/M2) all negative — 3
  independent cells, one per session, same sign, same mechanism. The most
  credible calendar candidate.
- **Calendar `dow=Mon`, NY_PRE, negative** — NY_PRE/M1/short and
  NY_PRE/M3 both negative, same session, same day. (LONDON/M3/long
  `dow=Mon` ran the opposite sign and did **not** survive — halves
  disagreed.)
- **`inventory_pts`** — 5 survivor rows but **sign-inconsistent**:
  positive in LONDON/M1/long, NY_AM/M1, NY_AM/M1/short; negative in
  LONDON/M1/short, NY_PRE/M3/short. No stable direction across cells —
  treated as noise despite passing the mechanical filter in 5/27 cells.
- **Day-location cluster** (`dist_day_low_w` ≡ `room_ahead_day_w` for
  shorts, `px_vs_on_lo_w` r=0.96 with the same) — NY_PRE/M1/short is
  **one** finding counted three times by variable duplication;
  NY_PRE/M2 `dist_day_high_w`, NY_PRE/M3 `dist_day_low_w`, LONDON/M2
  `pos_in_range_dir` are single, non-replicated, cell-specific hits.
- **Calendar `month` — 12 survivor rows, no consistent month, mostly
  session/mechanism-specific**, and 5 of the 12 are THIN. `month=6`/`7`
  additionally carry the two-calendar-year confound noted in §1.
  `month=4` in NY_PRE runs **opposite signs** in M1 (+1.35, good) vs M3
  (−0.59, bad) — same session, same calendar month, opposite direction —
  consistent with noise, not a seasonal effect.
- Remaining isolated, non-replicated single-cell hits (`on_range_w`,
  `day_range_w`, `overlap`, `seq_sess`, `trend_align` in NY_AM/M1/short
  and NY_PRE/M3, `open_vs_value=above_value` sign-flips between LONDON
  (negative) and NY_AM (positive, ×2 nested)) are not corroborated
  anywhere else in the sweep.

**Bottom line on survivors:** after collapsing duplicate variables, nested
cells, thin-day arms, and sign-inconsistent variables, this sweep produces
**zero variables that meet a validated-finding bar** (which would require
independent, non-nested, non-duplicate replication with adequate day
counts in every arm — none of these fully clear that bar). The two
patterns worth carrying forward as **candidates for a future,
purpose-declared test** — not adopted, not validated — are the M1
volatility-regime lift and the M3 momentum-overrun penalty (§6), because
they are the only ones that replicate sign across multiple independent,
non-nested cells and multiple sessions with non-thin day counts.

---

## 3. CLEARS THAT DID NOT SURVIVE (18 of 84)

| session | cell | variable | dev(R) | killed by |
|---|---|---|---|---|
| LONDON | LONDON/M3 | rv30_over_rv120 | +0.286 | a half is <1/3 the effect |
| LONDON | LONDON/M3 | vol30_over_vol240 | +0.352 | a half is <1/3 the effect |
| LONDON | LONDON/M3 | month=10 | -0.584 | a half is <1/3 the effect |
| LONDON | LONDON/M3 | month=3 | +0.393 | halves disagree in sign |
| LONDON | LONDON/M3/long | atr30_over_w | +0.489 | a half is <1/3 the effect |
| LONDON | LONDON/M3/long | day_range_w | +0.502 | a half is <1/3 the effect |
| LONDON | LONDON/M3/long | on_range_w | +0.454 | a half is <1/3 the effect |
| LONDON | LONDON/M3/long | dow=Mon | +0.886 | halves disagree in sign |
| NY_AM | NY_AM/M1/short | prev_out_day | -0.489 | a half is <1/3 the effect |
| NY_AM | NY_AM/M1/short | prev_out_day (sign>0) | -0.400 | halves disagree in sign |
| NY_AM | NY_AM/M1/short | month=7 | +1.116 | half too thin |
| NY_AM | NY_AM/M3 | w15_pts | -0.321 | **LAW2 mechanical (declared)** |
| NY_AM | NY_AM/M3/short | px_vs_on_hi_w | -0.386 | a half is <1/3 the effect |
| NY_PRE | NY_PRE/M1/long | month=7 | +0.781 | half too thin |
| NY_PRE | NY_PRE/M1/short | pos_in_day_range | -0.811 | a half is <1/3 the effect |
| NY_PRE | NY_PRE/M1/short | pos_in_range_dir | +0.834 | a half is <1/3 the effect |
| NY_PRE | NY_PRE/M2/long | px_vs_on_hi_w | -0.508 | a half is <1/3 the effect |
| NY_PRE | NY_PRE/M3/short | w15_pts | +0.652 | **LAW2 mechanical (declared)** |

`w15_pts` clears CI in 2 cells and is correctly killed both times by the
pre-declared LAW2 mechanical rule (it's in `MECHANICAL` by declaration) —
exactly the outcome the declaration predicted for it. The dominant killer
overall is **T2 (half-agreement / magnitude)**, 13 of 18 — the split-half
check is doing most of the real work of separating signal from noise in
this sweep.

---

## 4. STREAK / TILT — question 3a, answered directly

Tested: `prev_out_sess`, `prev_out_day`, `day_out_so_far` — median split
**and** an explicit sign split (prior R > 0 vs ≤ 0), across all 27 cells.
**162 tests total.**

- `prev_out_sess` (same-session previous trade's R): **0 of 54 tests
  cleared test 1, anywhere, in any session or mechanism.** Complete null.
- `prev_out_day` (previous trade's R, any session, same day): 2 clears,
  both in NY_AM/M1/short, both killed by T2 (one by magnitude, the sign
  version by the halves disagreeing outright).
- `day_out_so_far` (cumulative R so far, same day, causal): 1 survivor —
  NY_AM/M1/short, sign split, **+0.50R** (prior-day-positive → better next
  trade), CI [+0.02, +1.05], both halves positive, 51/89 days.

**Answer: no.** Out of 162 tests, expected false clears at 5% ≈ 8; only
4 cleared test 1 and only 1 survived all five. That single survivor sits
in one direction-split cell, is not corroborated by `prev_out_sess` or
`prev_out_day` in the same cell (both null there), and is not corroborated
in any other cell. **There is no day-level autocorrelation / "hot hand" in
this grammar's mechanical fills** — a trade's outcome does not depend on
how the previous trade (same session or earlier that day) or the day's
running total went in. Given these are mechanical fills with no human in
the loop, this is the expected result and it is clean: the market shows no
detectable streak persistence in this construction.

---

## 5. CROSS-SESSION CARRY — question 3b, answered directly

Tested: `london_out_today` (defined only for NY_PRE and NY_AM rows —
confirmed: 0/1231 LONDON rows, 925/925 possible NY_PRE, 997/997 possible
NY_AM have it populated where applicable). Median + sign split, 18 NY
cells → **36 tests.**

- **NY_PRE/M2: survives.** dev = **+0.548R**, CI [+0.06, +1.08], both
  halves positive (+0.63/+0.49), points-control agrees (+5.33), ρ_risk =
  −0.09 (not mechanical), 66/77 days per arm (not thin). Median-split and
  sign-split (prior-London-positive vs not) give the identical result.
- **Every other NY cell — 8 in NY_PRE (excluding M2), 9 in NY_AM — shows
  no effect** (CI spans zero in all of them). In particular **NY_AM never
  clears**, in any mechanism or direction: whatever carry exists from
  London does not reach as far as the NY_AM session.

**Answer: one candidate, unconfirmed.** 36 tests, expected false clears at
5% ≈ 1.8; observed 2 (both the same cell, tested two ways) — right at the
naive single-family budget. It is not disqualified by the day-count check
(66/77 days, comfortably not thin) and it is directionally sensible (a
positive London session → positive NY_PRE follow-through, decaying away by
NY_AM, consistent with a shared day-quality/trend-day effect rather than
anything mechanism-specific to M2). But it is **one isolated cell out of
18**, with no corroboration from M1 or M3 in the same session, and no
NY_AM echo. Treated as a single-cell candidate worth a purpose-declared
follow-up, not a cross-session finding — the honest read is "mostly no,
with one unconfirmed exception in NY_PRE/M2."

---

## 6. REGIME — is there a volatility or trend regime where this grammar works better?

**Plainly: weakly yes, mechanism-specific, not session-uniform, not
validated.**

Two patterns replicate sign across multiple **independent** (non-nested,
non-duplicate-variable) cells and multiple sessions:

1. **M1 does better in a relatively higher-ATR regime.** `atr30_over_w`
   (30-bar ATR relative to the 15m-BB width W) is **positive in all 9 M1
   cells** (every session × every direction split), 3 of which
   individually clear+survive (LONDON/M1 +0.62R, LONDON/M1/long +1.08R,
   NY_AM/M1/long +0.48R; NY_PRE/M1 direction cells run positive too but
   don't clear). Quintile check is weak support at best — `atr30_over_w`
   by realized-R quintile in LONDON/M1 is nearly flat (Q1:0.08 … Q5:0.08),
   so the CI-based finding isn't backed by a strongly monotonic quintile
   structure; treat this as a real but modest lift, not a strong regime
   gate.
2. **M3 does worse when momentum is already running with the trade at
   entry.** `slope_with_trade`/`ma15_slope30_w` is **negative in 8 of 9
   M3 cells**, 4 of which clear+survive, spanning LONDON and NY_AM (not
   NY_PRE). Quintile check here is mildly monotonic and in the expected
   direction (NY_AM/M3: Q1:0.06 → Q5:0.04, worse-outcome trades have
   systematically higher with-trade slope). Reads as an "overrun" effect
   — the menu-structure mechanism (M3) does worse when price has already
   spent its momentum by the time the fight starts.

Both are **M1-only** and **M3-only** respectively — this is squarely a
mechanism-dependent regime effect, not a session-wide or grammar-wide one,
and **both patterns go quiet in NY_PRE** specifically. `rv30_over_rv120`
and `vol30_over_vol240` (the more standard realized-vol ratios) cleared
test 1 once each (LONDON/M3) but both failed T2 (half magnitude) — the
ATR-relative-to-W framing carries the regime signal here better than raw
realized-vol ratios do, for whatever that's worth. Neither pattern has
been validated out-of-sample; both are fit-only candidates for a future
declared test, not adopted.

---

## 7. WHAT DAY CONTEXT SAYS

- **`daytype` (balanced/imbalanced/unknown) is a clean, total null**: 60
  tests across all cells and levels, **zero clears**. Whether TPO
  classifies the day as balanced or trend/imbalanced carries no detectable
  signal for any session or mechanism in this grammar.
- **`value_position` and `open_vs_value`** are nearly as clean: 1/135 and
  3/81 survivors respectively, each isolated to a single cell with no
  cross-session echo (`value_position=below` only in NY_PRE/M2;
  `open_vs_value=above_value` flips sign between LONDON, negative, and
  NY_AM, positive — inconsistent, treated as noise).
- **`n_bars_since_open`, `seq_day`, `vwap_sd_over_w15`, `w60_over_w15`**:
  zero clears anywhere (0/27 each) — how far into the session/day a fight
  occurs, and vwap-band width relative to W, carry no detectable signal.
- **Calendar (`dow`, `month`) is the noisiest category** — 25 total
  survivors between the two, more than a third of the sweep's raw
  survivor count, but riddled with thin-day arms (5 of the month
  survivors, 2 of the dow survivors are THIN), sign flips within the same
  session (`month=4` in NY_PRE: +1.35R for M1, −0.59R for M3), and a
  built-in two-calendar-year confound for June/July. The one calendar
  pattern that survives scrutiny across independent cells is **Friday
  being bad for M2, in all three sessions** (LONDON/M2/long, NY_PRE/M2,
  NY_AM/M2, days 13/32/21 respectively — not thin) and, more weakly,
  **Monday being bad for NY_PRE specifically** (M1/short and M3 agree).
  Neither should be treated as more than a candidate: calendar effects on
  a 290-day sample with 5–12 levels are exactly the kind of split this
  family's false-positive budget predicts will throw up a few
  reproducible-looking hits by chance, and Friday/Monday partition the
  week into only 5 buckets tested 27 times each — multiplicity is severe
  and uncorrected.
- **Day-location variables** (`pos_in_day_range`, `dist_day_high/low_w`,
  `room_ahead_day_w`, `px_vs_on_hi/lo_w`) mostly cleared 0–1 times each,
  concentrated in one NY_PRE/M1/short cell (three near-duplicate columns
  restating the same single hit) — not a broad day-location effect.

**Net assessment:** day-level and cross-session context in this grammar is
overwhelmingly null, in line with the family's prior (BR-86/90/91/94). The
sweep clears at essentially its false-positive budget in aggregate
(1.03–1.24×). The only things worth carrying into a future, independently
declared test are: (1) the M1 ATR-regime lift, (2) the M3 momentum-overrun
penalty, and (3) the M2 Friday effect — all three replicate sign across
multiple independent, non-thin cells, none are validated, and per the
governing declaration's standing, **nothing here is adopted.**
