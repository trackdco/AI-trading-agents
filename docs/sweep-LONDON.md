# LONDON Session Sweep — Winner/Loser Separation

Run 2026-08-08. Governed by `docs/DECLARATIONS-agent-sweep.md` (the five-test
survival rule, frozen before any outcome was read). Statistics computed
exclusively with `scripts.sweep_lib` (`load_wide`, `test_split`,
`quintiles`, `cells`, `predictors`) — no reimplemented tests. Scope is
LONDON only; LONDON is never pooled with NY_PRE or NY_AM; M1/M2/M3 are
never pooled with each other. Directions (long/short) are pooled within a
cell only where the library's `cells()` yields a pooled cell, and that
pooling is stated in every table below.

**Data hygiene note (pre-empts the coordinator's defect alert):** the
candidate predictor list returned by `predictors(B)` contains `out_pts`
(`= out × risk`), the points-based outcome control itself, re-expressed in
points. It correlates `0.81` with `out` in this data and "survives" every
cell tautologically (verified, then discarded — see below) because it is
outcome-derived, not an ex-ante predictor. It was excluded from this sweep
from the start, before any test was run, on that basis (98 predictors used,
not the raw 99 `predictors()` returns). `scripts/sweep_lib.py` has since
been patched to add `out_pts` to `OUTCOME_COLS` so this is fixed for future
agents; the exclusion made no difference to any count in this report
because it was never in the sweep to begin with.

---

## SCOPE AND COUNTS

- **Cells swept** (via `cells(B, "LONDON")`): 9 — `LONDON/M1` (n=617),
  `LONDON/M1/long` (271), `LONDON/M1/short` (346), `LONDON/M2` (280),
  `LONDON/M2/long` (149), `LONDON/M2/short` (131), `LONDON/M3` (334),
  `LONDON/M3/long` (189), `LONDON/M3/short` (145).
- **Predictors swept**: 98 (`predictors(B)`'s 99 usable columns, minus
  `out_pts` — see hygiene note above).
- **Tests run**: 98 × 9 = **882**, each running all five declared tests
  via one `test_split` call, default above-median (or boolean) split.

**False-positive budget (mandatory arithmetic):**

> 882 tests × 0.05 = **44.1 expected spurious CI-clears at 95%** (this is
> what test 1 alone would produce under a pure null with independent
> tests).

**Observed:**

| Stage | Count | vs. budget |
|---|---|---|
| T1 CI-clears (test 1 only) | **69** | 1.6× the 44.1 budget — in the same ballpark as this family's history (BR-91: 9/110 = 8.2%; BR-94: 9/160 = 5.6%; here: 69/882 = 7.8%) |
| Full 5-test **survivors** | **52** raw (variable, cell) rows | far above a naive null expectation, but see the independence discount below |

**Why-breakdown for the 830 non-survivors:** CI spans zero 752, power 37,
constant/missing 24, LAW2 mechanical 11, a half `<1/3` the effect 5,
halves disagree in sign 1.

**The independence discount (read before trusting "52").** 882 tests are
not 882 independent shots at 5%. Within this survivor set:

- **2 pairs are exact-duplicate columns** inside a single-direction cell
  (`slope_with_trade ≡ ma15_slope30_w` and `prev3_ret_dir ≡ prev3_ret_w`,
  both in `LONDON/M3/long`, because the direction-adjustment multiplier is
  constant `+1` once direction is fixed — verified `corr = 1.000`,
  identical `dev`/CI to 6 decimals).
- **3 more pairs are near-duplicate (`|corr| ≥ 0.9`) within the same
  cell**: `is_long` / `px_vs_ma15_w` in `LONDON/M1` (`corr = -0.95`),
  `disp_w` / `px_vs_ma15_w` in `LONDON/M2` (`corr = 0.97`),
  `ma15_vs_ma60_w` / `px_vs_ma60_w` in `LONDON/M2/short` (`corr = 0.97`).
- **4 variables survive in both a pooled mechanism cell and that
  mechanism's direction-subset**, which is *nested*, not independent data
  (the subset's fights are a strict subset of the pooled cell's fights):
  `d30_conf`, `cvd_slope30`, `atr30_over_w` (all `M1` + `M1/long`), and
  `bar_range_w` (`M3` + `M3/long`).

Collapsing exact duplicates, `|corr|≥0.9` pairs, and pooled/direction
nesting via connected components: **52 raw survivor rows → 41 distinct
clusters.** That is the honest count of non-redundant findings. It is
still well above what a clean null would produce, and the interpretation
of that gap is addressed in WHAT LONDON SAYS.

Minimum-power gate (≥40/cell, ≥10/arm, ≥3 days/arm) is enforced inside
`test_split`; 37 tests failed it outright and are excluded from all counts
above.

---

## SURVIVORS

Not none — 52 raw rows (41 distinct after collapsing duplicates/nesting)
pass all five declared tests. Per the declaration's own prior ("the honest
expectation is that most or all of this sweep returns nothing... If
something does survive all five tests in a session, it is the first thing
on this family that has"), this is the first LONDON result on this family
to clear the full bar — but the scale of it (41 distinct clusters, not
1–2) plus the fragility uncovered by threshold search below argue against
reading it as a small number of clean edges. Full detail on every survivor
is below; the honest overall read is in WHAT LONDON SAYS.

### Most load-bearing four (with SEARCHED threshold stress-test)

Per the task's step 3, the 5–10 most promising variables were re-tested at
top/bottom **tercile** and top/bottom **quartile** splits via `mask=`
(middle third / middle half dropped). These thresholds were **picked after
seeing which variables cleared the median split — they are SEARCHED, and
a threshold chosen on the same data it is tested on is a fit artifact even
when it survives split-half**, per the declaration. 10 variable/cell pairs
were stress-tested; results:

| Variable / cell | Median (declared) | Tercile [SEARCHED] | Quartile [SEARCHED] | Verdict |
|---|---|---|---|---|
| `atr30_over_w` / `LONDON/M1` | survives, dev +0.617 | survives, dev +0.593 (n=408) | survives, dev +0.431 (n=310) | **robust** to threshold choice |
| `bar_range_w` / `LONDON/M3` | survives, dev +0.480 | survives, dev +0.445 (n=220) | survives, dev +0.664 (n=168) | **robust** to threshold choice |
| `inventory_pts` / `LONDON/M1/short` | survives, dev -0.502 | survives, dev -0.780 (n=230) | survives, dev -0.785 (n=177) | **robust** to threshold choice |
| `n_struct_ahead` / `LONDON/M1` | survives, dev -0.614 | CI spans zero, dev -0.034 | CI spans zero, dev -0.092 | **fragile** — median-split-specific |
| `d30_conf` / `LONDON/M1` | survives, dev -0.408 | untestable (p25=p33=p50=p67=p75=0, variable is near-degenerate/count-like) | untestable | median split is effectively the only cut this variable supports |
| `cvd_slope30` / `LONDON/M1` | survives, dev -0.384 | CI spans zero, dev -0.235 | survives, dev -0.435 | mixed / inconsistent across cuts |
| `disp_w` / `LONDON/M2` | survives, dev -0.383 | survives, dev -0.451 (n=186) | CI spans zero, dev -0.283 (n=140, thin) | weakens at tightest (possibly power-limited) cut |
| `ma15_vs_ma60_w` / `LONDON/M2/short` | survives, dev +0.895 | survives, dev +0.627 (n=64) | CI spans zero, dev +0.492 (n=48, thin) | weakens at tightest (possibly power-limited) cut |
| `inventory_pts` / `LONDON/M1/long` | survives, dev +0.633 | CI spans zero, dev +0.601 | CI spans zero, dev +0.763 | **fragile** — median-split-specific |
| `bar_range_w` / `LONDON/M3/long` | survives, dev +0.522 | flips to **LAW2 mechanical** (`ρ(risk)` crosses 0.4 in the tails), dev +0.790 | flips to **LAW2 mechanical**, dev +0.928 | mechanical coupling revealed by the tails — **discount this one** |

Only 3 of 10 stress-tested variables are threshold-robust:
`atr30_over_w` (`LONDON/M1`), `bar_range_w` (`LONDON/M3`, pooled — its
nested `M3/long` sibling above is *not* robust and turns out to be
partly mechanical), and `inventory_pts` (`LONDON/M1/short` only — the
same variable in `M1/long`, opposite sign, is fragile). This is the
single clearest piece of evidence in this sweep that the five-test rule,
while strict, does not by itself guarantee a threshold-independent
relationship — three of the ten hardest-tested "survivors" turn out to be
artifacts of the specific 50/50 cut.

### Full survivor listing, by cell

`dev` = mean(`out`, arm A above-median) − mean(`out`, arm B); CI is the
day-clustered bootstrap on that difference (seed 20260807, 2000 draws);
`d_pts` is the points-control difference (test 3); `rho` is
`corr(var, risk)` (test 4, must be `<0.4` in magnitude); half A/B are the
frozen split-half differences (test 2, same sign, `≥1/3` magnitude
required); quintiles are `quintiles(g, var)` — mean of the variable within
each realized-`out` quintile (Q1=worst, Q5=best); shape is `monotone`
(|Spearman ρ vs quintile index| ≥0.9), `rough-mono` (≥0.7), or `non-mono`
(<0.7, single-bucket / tail-loaded / noisy). `==X` marks the two exact
duplicates (identical test, kept once, alias noted).

**LONDON/M1** (pooled, n=617)

| Variable | n (a/b) | dev (R) | 95% CI | d_pts | rho | half A | half B | quintiles (Q1..Q5) | shape | searched |
|---|---|---|---|---|---|---|---|---|---|---|
| atr30_over_w | 308/309 | +0.617 | [+0.286, +0.941] | +5.32 | -0.06 | +0.48 | +0.72 | 0.08 0.08 0.08 0.09 0.08 | non-mono | yes |
| cvd_slope30 | 308/309 | -0.384 | [-0.709, -0.057] | -3.55 | -0.01 | -0.54 | -0.23 | -5.17 -4.99 -4.49 -4.86 -5.95 | non-mono | yes |
| d30_conf | 152/465 | -0.408 | [-0.723, -0.074] | -4.03 | -0.01 | -0.49 | -0.33 | 0.25 0.29 0.28 0.22 0.19 | rough-mono | yes |
| eff_result | 200/200 | -0.424 | [-0.799, -0.039] | -3.41 | -0.17 | -0.23 | -0.61 | 74.19 84.01 62.45 52.45 61.20 | rough-mono | no |
| is_long | 271/346 | +0.342 | [+0.001, +0.690] | +1.81 | +0.11 | +0.31 | +0.39 | 0.35 0.37 0.46 0.51 0.51 | monotone | no |
| ma60_slope30_w | 239/239 | -0.349 | [-0.691, -0.020] | -2.76 | -0.13 | -0.29 | -0.41 | 0.05 0.03 0.01 0.04 -0.01 | rough-mono | no |
| n_struct_ahead | 49/568 | -0.614 | [-1.070, -0.003] | -5.85 | -0.09 | -0.73 | -0.52 | 7.47 7.31 7.25 6.73 7.19 | rough-mono | yes |
| px_vs_ma15_w | 308/309 | -0.335 | [-0.663, -0.011] | -1.59 | -0.13 | -0.27 | -0.41 | 0.12 0.10 0.02 -0.03 -0.02 | rough-mono | no |

Note: `is_long` (`corr = -0.95` with `px_vs_ma15_w` in this cell) and
`px_vs_ma15_w` are effectively one signal, not two ("longs win more" and
"price sits below the 15m MA more" are almost the same statement here
because direction is so imbalanced relative to `px_vs_ma15_w`'s sign).
`d30_conf`, `cvd_slope30`, `atr30_over_w` are nested with their
`M1/long` counterparts below (not independent confirmation).

**LONDON/M1/long** (n=271)

| Variable | n (a/b) | dev (R) | 95% CI | d_pts | rho | half A | half B | quintiles (Q1..Q5) | shape | searched |
|---|---|---|---|---|---|---|---|---|---|---|
| aff_val | 69/202 | -0.585 | [-1.119, -0.023] | -4.68 | +0.06 | -0.51 | -0.62 | 0.27 0.26 0.35 0.20 0.19 | rough-mono | no |
| atr30_over_w | 135/136 | +1.078 | [+0.559, +1.651] | +11.14 | -0.15 | +0.92 | +1.19 | 0.08 0.09 0.08 0.10 0.09 | non-mono | no |
| cvd_slope30 | 135/136 | -0.609 | [-1.201, -0.087] | -6.40 | -0.07 | -0.88 | -0.38 | -4.52 -5.36 -4.09 -6.01 -5.62 | non-mono | no |
| d30_conf | 69/202 | -0.522 | [-1.064, -0.009] | -5.04 | -0.02 | -0.92 | -0.25 | 0.29 0.26 0.30 0.21 0.20 | rough-mono | no |
| delta_z | 135/136 | +0.650 | [+0.165, +1.218] | +6.72 | +0.13 | +0.48 | +0.77 | 0.59 0.71 1.25 1.23 1.00 | non-mono | no |
| inventory_pts | 133/138 | +0.633 | [+0.040, +1.198] | +6.24 | +0.09 | +0.22 | +0.95 | 0.09 -14.71 1.72 10.55 12.01 | rough-mono | **yes — fragile, see stress test** |

**LONDON/M1/short** (n=346)

| Variable | n (a/b) | dev (R) | 95% CI | d_pts | rho | half A | half B | quintiles (Q1..Q5) | shape | searched |
|---|---|---|---|---|---|---|---|---|---|---|
| d15_conf | 133/213 | -0.372 | [-0.697, -0.049] | -3.72 | -0.08 | -0.37 | -0.40 | 0.43 0.39 0.45 0.35 0.30 | rough-mono | no |
| delta_z | 173/173 | -0.425 | [-0.751, -0.093] | -2.99 | -0.31 | -0.52 | -0.35 | -0.50 -0.63 -0.84 -1.45 -1.14 | rough-mono | no |
| inventory_pts | 173/173 | -0.502 | [-0.868, -0.155] | -5.97 | -0.02 | -0.35 | -0.59 | 13.38 20.95 16.75 24.34 -3.30 | non-mono | **yes — robust, see stress test** |
| ma15_ahead_r | 173/173 | -0.513 | [-0.862, -0.190] | -3.38 | -0.33 | -0.42 | -0.58 | 10.47 6.90 4.61 2.14 3.05 | rough-mono | no |
| n_ahead_within_2r | 78/268 | +0.422 | [+0.050, +0.840] | +4.01 | +0.37 | +0.26 | +0.57 | 0.51 0.62 0.72 1.46 1.10 | rough-mono | no |
| nearest_behind_r | 173/173 | -0.363 | [-0.730, -0.014] | -1.57 | -0.26 | -0.31 | -0.42 | 3.60 3.11 1.75 1.18 1.34 | rough-mono | no |

Note: `inventory_pts` is +0.633 here in `M1/long` but -0.502 in
`M1/short` — opposite raw sign in the two disjoint direction subsets. The
short-side version is threshold-robust; the long-side version is not
(see stress table). This is a within-cell asymmetry, not a repeating
cross-cell pattern.

**LONDON/M2** (pooled, n=280)

| Variable | n (a/b) | dev (R) | 95% CI | d_pts | rho | half A | half B | quintiles (Q1..Q5) | shape | searched |
|---|---|---|---|---|---|---|---|---|---|---|
| abs_px_vs_ma15_w | 140/140 | -0.344 | [-0.649, -0.041] | -2.52 | +0.16 | -0.47 | -0.25 | 0.32 0.33 0.38 0.36 0.29 | non-mono | no |
| disp_abs_w | 140/140 | -0.340 | [-0.636, -0.026] | -2.55 | -0.11 | -0.36 | -0.31 | 0.27 0.24 0.25 0.24 0.20 | rough-mono | no |
| disp_w | 140/140 | -0.383 | [-0.696, -0.073] | -4.86 | +0.06 | -0.53 | -0.29 | -0.01 0.03 0.08 -0.03 -0.05 | non-mono | yes |
| pos_in_range_dir | 140/140 | -0.366 | [-0.669, -0.049] | -5.90 | +0.13 | -0.36 | -0.39 | 0.70 0.78 0.79 0.76 0.69 | non-mono | no |
| px_vs_ma15_w | 140/140 | -0.377 | [-0.692, -0.078] | -4.91 | +0.04 | -0.58 | -0.24 | -0.01 0.04 0.12 -0.01 -0.06 | non-mono | no |

Note: `disp_w`/`px_vs_ma15_w` are near-duplicate (`corr=0.97`);
`abs_px_vs_ma15_w`/`disp_abs_w` correlate 0.84 — this cell's 5 survivors
are closer to 2–3 distinct signals (a directional distance-from-MA15
measure, and its magnitude/absolute-value cousin).

**LONDON/M2/long** (n=149)

| Variable | n (a/b) | dev (R) | 95% CI | d_pts | rho | half A | half B | quintiles (Q1..Q5) | shape | searched |
|---|---|---|---|---|---|---|---|---|---|---|
| dow | 55/94 | -0.427 | [-0.830, -0.052] | -5.13 | +0.12 | -0.47 | -0.38 | 2.04 2.28 2.32 1.92 1.64 | non-mono | no |
| ma15_vs_ma60_w | 60/61 | +0.481 | [+0.033, +0.907] | +6.61 | -0.27 | +0.77 | +0.33 | 0.66 0.45 0.04 0.72 0.74 | non-mono | no |

`dow` (day-of-week) surviving is calendar noise dressed as a finding —
flagged, not elevated, despite technically passing all five tests; a
day-of-week effect with no economic mechanism and thin cell (n=149,
crosses only 3 possible thresholds) is exactly the kind of thing a broad
sweep is expected to throw up by chance.

**LONDON/M2/short** (n=131)

| Variable | n (a/b) | dev (R) | 95% CI | d_pts | rho | half A | half B | quintiles (Q1..Q5) | shape | searched |
|---|---|---|---|---|---|---|---|---|---|---|
| ma15_vs_ma60_w | 48/48 | +0.895 | [+0.395, +1.385] | +7.93 | -0.10 | +0.88 | +0.88 | 0.17 -0.22 0.14 0.10 0.32 | non-mono | yes |
| prev15_ret_dir | 65/66 | +0.469 | [+0.022, +0.886] | +3.46 | +0.30 | +0.28 | +0.58 | -0.06 0.00 0.07 0.05 0.03 | non-mono | no |
| px_vs_ma60_w | 48/48 | +0.884 | [+0.405, +1.352] | +7.77 | -0.17 | +0.71 | +0.99 | -0.16 -0.51 -0.24 -0.29 0.03 | non-mono | no |
| trend_align | 47/84 | -0.700 | [-1.078, -0.276] | -5.52 | +0.10 | -0.57 | -0.78 | 0.45 0.50 0.45 0.41 0.14 | rough-mono | no |

Note: `ma15_vs_ma60_w`/`px_vs_ma60_w` are near-duplicate (`corr=0.97`);
`trend_align` (a boolean sign-agreement flag between the same two MAs and
direction) correlates -0.74/-0.75 with both. All three are one underlying
"MA15-vs-MA60 trend alignment" signal, expressed three ways — the biggest
raw effect sizes in the whole sweep (dev up to +0.90) live in the
smallest cell here (n=96–131), and the strongest of the three variants
weakens sharply once the tercile/quartile stress test thins the sample.

**LONDON/M3** (pooled, n=334)

| Variable | n (a/b) | dev (R) | 95% CI | d_pts | rho | half A | half B | quintiles (Q1..Q5) | shape | searched |
|---|---|---|---|---|---|---|---|---|---|---|
| bar_range_w | 167/167 | +0.480 | [+0.210, +0.764] | +4.57 | +0.24 | +0.50 | +0.40 | 0.08 0.09 0.10 0.13 0.10 | rough-mono | yes |
| n_aff | 162/172 | -0.384 | [-0.696, -0.083] | -1.97 | -0.19 | -0.41 | -0.47 | 1.64 1.40 1.42 1.52 1.34 | non-mono | no |
| prev3_ret_dir | 167/167 | +0.347 | [+0.054, +0.639] | +0.75 | +0.32 | +0.25 | +0.47 | 0.02 0.08 0.11 0.11 0.08 | non-mono | no |
| slope_with_trade | 167/167 | -0.434 | [-0.749, -0.146] | -3.06 | -0.00 | -0.54 | -0.36 | 0.04 0.04 0.04 0.04 0.04 | flat@2dp | no |

**LONDON/M3/long** (n=189)

| Variable | n (a/b) | dev (R) | 95% CI | d_pts | rho | half A | half B | quintiles (Q1..Q5) | shape | searched |
|---|---|---|---|---|---|---|---|---|---|---|
| aff_poc | 96/93 | +0.456 | [+0.013, +0.904] | +2.62 | -0.11 | +0.18 | +0.51 | 0.52 0.25 0.50 0.50 0.59 | non-mono | no |
| aff_vah | 52/137 | -0.604 | [-0.971, -0.216] | -5.12 | -0.10 | -0.30 | -0.87 | 0.30 0.41 0.19 0.19 0.12 | rough-mono | no |
| aff_vwap_p1 | 33/156 | -0.525 | [-0.975, -0.016] | -4.20 | +0.05 | -0.57 | -0.20 | 0.24 0.31 0.19 0.16 0.09 | rough-mono | no |
| bar_range_w | 94/95 | +0.522 | [+0.182, +0.885] | +6.11 | +0.30 | +0.42 | +0.55 | 0.06 0.09 0.10 0.11 0.11 | monotone | **yes — reveals LAW2 in tails, discount** |
| disp_abs_w | 94/95 | -0.440 | [-0.804, -0.095] | -3.08 | -0.13 | -0.35 | -0.47 | 0.29 0.26 0.23 0.23 0.24 | non-mono | no |
| disp_w | 94/95 | -0.382 | [-0.754, -0.032] | -2.10 | -0.15 | -0.22 | -0.53 | 0.27 0.22 0.22 0.15 0.21 | rough-mono | no |
| ma15_slope30_w (≡slope_with_trade) | 94/95 | -0.500 | [-0.923, -0.074] | -3.55 | -0.09 | -0.17 | -0.77 | 0.04 0.05 0.04 0.04 0.04 | non-mono | no |
| poc_dist_w | 94/95 | -0.483 | [-0.938, -0.038] | -2.78 | +0.05 | -0.18 | -0.58 | 0.21 0.34 0.22 0.20 0.22 | non-mono | no |
| prev15_ret_dir | 94/95 | +0.477 | [+0.079, +0.882] | +5.31 | +0.20 | +0.56 | +0.43 | 0.00 -0.02 0.00 0.01 0.05 | rough-mono | no |
| prev3_ret_w (≡prev3_ret_dir) | 94/95 | +0.436 | [+0.049, +0.851] | +1.15 | +0.36 | +0.30 | +0.63 | 0.02 0.09 0.11 0.10 0.11 | rough-mono | no |
| px_vs_on_hi_w | 94/95 | -0.484 | [-0.866, -0.128] | -4.21 | -0.10 | -0.33 | -0.62 | -0.31 -0.40 -0.40 -0.65 -0.47 | rough-mono | no |
| px_vs_poc_w | 94/95 | -0.512 | [-0.957, -0.104] | -3.79 | +0.00 | -0.18 | -0.68 | 0.38 0.62 0.44 0.30 0.32 | non-mono | no |

Note: this cell has 12 raw survivor rows that collapse to roughly
6 distinct signal clusters — `{disp_w, ma15_slope30_w, slope_with_trade,
px_vs_on_hi_w, px_vs_poc_w, disp_abs_w}` (all pairwise correlated
0.5–0.78, a single "trend/distance-from-structure" cluster),
`{poc_dist_w, aff_poc}`, `{bar_range_w, prev3_ret_w, prev3_ret_dir}`,
plus `prev15_ret_dir`, `aff_vwap_p1`, `aff_vah` standing alone.

**LONDON/M3/short** (n=145)

| Variable | n (a/b) | dev (R) | 95% CI | d_pts | rho | half A | half B | quintiles (Q1..Q5) | shape | searched |
|---|---|---|---|---|---|---|---|---|---|---|
| aff_vah | 19/126 | +0.463 | [+0.026, +0.877] | +3.66 | -0.00 | +0.40 | +0.50 | 0.00 0.04 0.27 0.27 0.15 | non-mono | no |
| bar_closeloc_dir | 72/73 | +0.443 | [+0.042, +0.847] | +5.91 | +0.17 | +0.27 | +0.58 | 0.72 0.73 0.76 0.76 0.78 | monotone | no |
| ma15_vs_ma60_w | 57/57 | +0.547 | [+0.022, +1.079] | +4.08 | -0.28 | +0.37 | +0.68 | 0.37 0.07 -0.19 0.29 0.13 | non-mono | no |

Note: `aff_vah` is **-0.604** in `M3/long` above but **+0.463** here in
`M3/short` — sign flips between the disjoint direction subsets of the
same mechanism, same as `inventory_pts` in M1. Not a repeating pattern;
a direction-dependent one.

---

## CLEARS THAT DID NOT SURVIVE

17 rows cleared the CI test (test 1) but died on a later test. All but
one died on the mechanical guard (test 4) or split-half (test 2):

| Cell | Variable | dev (R) | 95% CI | Killed by |
|---|---|---|---|---|
| LONDON/M1 | rangex | +0.325 | [+0.023, +0.601] | LAW2 mechanical |
| LONDON/M1 | risk_over_w | +0.370 | [+0.055, +0.652] | LAW2 mechanical |
| LONDON/M1/long | support_wall_size | -0.682 | [-1.315, -0.063] | LAW2 mechanical |
| LONDON/M1/long | tf_won | -0.530 | [-1.032, -0.005] | LAW2 mechanical |
| LONDON/M1/short | rangex | +0.650 | [+0.318, +0.968] | LAW2 mechanical |
| LONDON/M1/short | risk_over_atr30 | +0.451 | [+0.131, +0.758] | LAW2 mechanical |
| LONDON/M1/short | risk_over_w | +0.376 | [+0.023, +0.732] | LAW2 mechanical |
| LONDON/M2 | cvd_slope30 | -0.301 | [-0.580, -0.048] | halves disagree in sign |
| LONDON/M2/long | entry | -0.829 | [-1.217, -0.452] | LAW2 mechanical |
| LONDON/M2/long | ma15 | -0.742 | [-1.165, -0.348] | LAW2 mechanical |
| LONDON/M2/long | stop | -0.829 | [-1.217, -0.452] | LAW2 mechanical |
| LONDON/M3 | tf_won | +0.561 | [+0.054, +1.090] | LAW2 mechanical |
| LONDON/M3 | rv30_over_rv120 | +0.286 | [+0.001, +0.581] | half `<1/3` the effect |
| LONDON/M3 | vol30_over_vol240 | +0.352 | [+0.051, +0.683] | half `<1/3` the effect |
| LONDON/M3/long | atr30_over_w | +0.489 | [+0.031, +0.895] | half `<1/3` the effect |
| LONDON/M3/long | day_range_w | +0.502 | [+0.086, +0.976] | half `<1/3` the effect |
| LONDON/M3/long | on_range_w | +0.454 | [+0.035, +0.933] | half `<1/3` the effect |

Worth noting: `cvd_slope30` clears in `LONDON/M2` (dev -0.301) with signs
that flip between the two halves, yet the *same* variable survives
cleanly in `LONDON/M1` and `LONDON/M1/long` (both negative, both halves
agree). Same predictor, opposite verdict, different mechanism — exactly
the session/mechanism discipline the declaration requires, and exactly
why mechanisms must never be pooled.

---

## PATTERNS ACROSS CELLS

Beyond individual survival, every predictor's above-median `dev` sign was
compared across the three **pooled** mechanism cells (`LONDON/M1`,
`LONDON/M2`, `LONDON/M3` — not the direction splits) regardless of
whether any single cell cleared. **38 of 98 predictors (39%) share the
same sign in all three mechanisms** — versus ~24.5 expected if signs were
independent coin flips (`98 × 0.25`). That excess is modest and not
itself a test any of these variables passed; most of the 38 are also
mutually correlated with each other (they cluster around a handful of
underlying themes: trend/slope alignment, distance from MA15/POC/VWAP,
recent momentum, relative volatility), so it is not 38 independent
corroborations either. The table below keeps only the tightest and most
economically legible ones (full spread ≤ 0.15 R across the three
mechanisms, or individually survives at least once):

| Variable | M1 dev | M2 dev | M3 dev | Survives (pooled cell) |
|---|---|---|---|---|
| **ma15_slope30_w** | -0.225 | -0.242 | -0.233 | M3 (as `slope_with_trade`) |
| bar_body_frac | -0.084 | -0.100 | -0.080 | — |
| nearest_ahead_r | -0.123 | -0.140 | -0.065 | — |
| px_vs_on_hi_w | -0.226 | -0.271 | -0.189 | — |
| cvd_slope30 | -0.384 | -0.301 | -0.286 | M1 (M2 clears but fails half-sign) |
| px_vs_vwap_w | -0.170 | -0.260 | -0.143 | — |
| pos_in_day_range | -0.170 | -0.252 | -0.131 | — |
| aff_vah | -0.113 | -0.201 | -0.237 | — (M3/long and M3/short survive with **opposite** signs to each other) |
| disp_w | -0.259 | -0.383 | -0.244 | M2, M3/long |
| px_vs_poc_w | -0.326 | -0.257 | -0.174 | M3/long |
| trend_align | -0.131 | -0.273 | -0.310 | M2/short |
| px_vs_ma15_w | -0.335 | -0.377 | -0.140 | M1, M2 |
| prev3_ret_dir | +0.237 | +0.045 | +0.347 | M3 |
| prev15_ret_dir | +0.258 | +0.106 | +0.275 | M2/short, M3/long |
| bar_range_w | +0.232 | +0.006 | +0.480 | M3, M3/long |
| atr30_over_w | +0.617 | +0.116 | +0.252 | M1, M1/long |

**`ma15_slope30_w` is the single most consistent directional pattern in
the whole LONDON sweep.** Its magnitude is nearly identical across all
three independently-mechanism-defined cells (-0.225, -0.242, -0.233 —
tighter than any other economically meaningful variable), it fully
survives all five tests in `M3/long` (where it is identical to
`slope_with_trade`), and its sign says the same thing everywhere: MA15
sloping against the trade's direction associates with a worse outcome, in
M1 (first-passage-to-15m-MA), M2 and M3 (first-passage-to-menu-structure)
alike — three mechanistically different outcome definitions, one
consistent directional read. `cvd_slope30`, `px_vs_ma15_w`, `disp_w`, and
`bar_range_w` show the same kind of repetition, each with at least one
individual survival to back it, but with looser magnitude agreement
across mechanisms than `ma15_slope30_w`.

`aff_vah` and `inventory_pts` are flagged as **direction-dependent, not
repeating** — both survive with opposite raw signs in the long vs. short
subsets of the same mechanism, so "same sign in M1/M2/M3" does not apply
to them (they were excluded from the table above for that reason, though
`aff_vah` did land in the raw 38-list — it's the pooled-M3 average
masking a direction-level sign split, listed here to flag the
distinction).

---

## WHAT LONDON SAYS

LONDON does not return the clean null the declaration's prior expected
(zero survivors), but it also does not return a small number of
convincing, independent, adoptable edges. What it returns is a **moderate
family of same-direction, mutually-correlated findings** — 52 raw
survivor rows collapsing to 41 distinct clusters, most describing a
handful of underlying themes (trend/MA-slope alignment with trade
direction, distance from MA15/POC/VWAP/day-structure, recent momentum,
relative volatility/bar range) that point the same way inside more than
one LONDON mechanism.

Three findings earn the most confidence, because they are the only ones
of the ten stress-tested that held up under alternate (SEARCHED) tercile
and quartile cuts as well as the median: **`atr30_over_w` in pooled
`LONDON/M1`** (relative volatility, higher associates with better
outcomes, dev +0.62→+0.59→+0.43 across median/tercile/quartile, all
survive), **`bar_range_w` in pooled `LONDON/M3`** (bigger entry-bar range
associates with better outcomes, dev +0.48→+0.45→+0.66, all survive —
though its `M3/long`-only sibling turns out to be mechanically coupled to
risk in the tails and should be discounted), and **`inventory_pts` in
`LONDON/M1/short`** only (dev -0.50→-0.78→-0.79, strengthening at tighter
cuts — the mirror-image `M1/long` version of the same variable is
threshold-fragile and should not be trusted). Separately, **`ma15_slope30_w`**
is the most persuasive *directional* (not per-cell-significance) result:
its effect size is nearly identical across M1, M2, and M3 pooled cells,
independent mechanisms with independent outcome definitions, which is a
harder coincidence to explain away than any single cell's CI.

Against that: seven of the ten stress-tested variables did **not** hold up
cleanly under alternate thresholds — some flip to CI-spans-zero, one
reveals a hidden mechanical coupling with risk in its tails, one is too
discrete to even test. That a majority of the hardest-scrutinized
"survivors" wobble under a threshold the five-test rule itself doesn't
require, is the most important thing this sweep says about LONDON: **the
five-test rule catches noise but not median-split-specific artifacts**,
and a meaningful fraction of what nominally survives here would not
survive a second, differently-chosen cut on the same data. The 69 T1
clears versus a 44.1 false-positive budget, and the unusually high
clear→survive pass-through rate (52 of 69, 75%), are both larger than a
clean-null read would predict but consistent with this family's own
history of clearing "at or near" its false-positive budget (BR-91, BR-94)
— LONDON looks like more of the same story, not a departure from it.

Per the declaration's standing: **fit-only, no holdout, report-only,
nothing adopted.** None of the above — including the three
threshold-robust variables and `ma15_slope30_w`'s cross-mechanism
consistency — should be treated as a validated edge. They are candidates
for a genuinely out-of-sample test, not for trading.
