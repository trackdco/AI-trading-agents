# CONCORD / CONVICTION-SIZING — FLOW SIGNALS ONLY, RE-TESTED WITH THE ORIENTATION FIX

**Question.** BR-94 settled that individual flow/depth signals are chance-level
selectors, tested one at a time. This is a different, genuinely untested
question: *when several flow signals agree at once at the moment the trigger
candle closes and the market order is sent, does win rate and EV climb with
the number of agreements?* This is the CONCORD/conviction-sizing construct,
and per `scripts/conviction_lib.py`'s header, the `delta_z` orientation defect
that contaminated the three prior refutations (BR-19, BR-26, BR-62) is fixed
here — the question is legitimately reopened.

**Bottom line up front: no, with one flagged exception that runs backwards.**
Across all nine (session x mechanism) cells, EV climbs monotonically with
stacked flow agreement in zero cells. Win% alone looks monotone in a couple
of cells, but its matching EV trend is flat or negative there — the dual-
currency inversion this programme keeps finding (BR-20). One session/mech
pair, **LONDON M2 and M3**, shows a *calibrated, non-null* relationship
between flow-conviction and outcome — but it runs the WRONG way: **more
stacked agreement predicts WORSE trades**, not better. Nowhere does more
agreement predict better trades at a level that survives permutation
calibration. Flow-conviction stacking does not work on this population.

Scope: **flow signals only** (10-12 of the 18 `s_*` columns in
`conviction_lib.py`; depth is a separate agent's scope). Sessions and
mechanisms reported separately throughout, never pooled, per standing
instruction. Read-only on `output/htf_ma_census/race_wide.parquet`; nothing
committed, nothing adopted.

Code: `/tmp/claude-0/.../scratchpad/run_conviction.py`,
`run_hires_calib.py`, `run_hires_full.py`, `build_report.py` (session-scratch,
not committed).

---

## 1. METHOD

- **Library**: all statistics come from `scripts/conviction_lib.py`
  (`load`, `signals`, `add_counts`, `monotone_table`, `spearman_trend`,
  `dboot_mean`, `permute`, `calibrate`) — nothing reimplemented except a
  small day-clustered bootstrap on the **difference** between two arms
  (`dboot_diff`, built directly on top of `dboot_mean`'s exact resampling
  scheme: same seed 20260807, same 2,000 draws, same `sess_day` clustering,
  applied with a shared per-draw day-resample index so the two arms are
  compared on the *same* bootstrapped day set each draw, i.e. paired).
- **Counts used**: `cc_flow_clean` (10 signals, `s_closeloc`/`s_rangex`
  dropped per BR-43/Law-2) is **primary**; `cc_flow` (12 signals, includes
  both) is **secondary**, used only to check whether including the two
  risk-coupled signals changes the conclusion (§6).
- **Coverage**: flow signals are essentially fully available — 9 of 12 are
  100% available; `s_eff` (eff_result) is available on 67.7% of fights (its
  threshold is the population median, so its NaNs simply drop from both
  numerator and denominator). Because of this near-universal coverage,
  `cc_flow_n` is 11-12 (of 12) for effectively every row and `cc_flow_clean_n`
  is 9-10 (of 10) — the `_frac` variants exist for cross-coverage
  comparability (depth signals run 40-100% coverage) but add nothing here:
  raw counts and `_frac` counts rank fights identically in this family, so
  raw counts are used throughout and `_frac` is not separately reported.
- **Cells**: 3 sessions (LONDON, NY_PRE, NY_AM) x 3 mechanisms (M1/M2/M3) =
  9 cells, 3,153 fights, 290 distinct session-days, 2025-06-02 to
  2026-07-15. Per-cell n ranges 243-617, days 116-257 (table below).
- **Monotonicity**: `spearman_trend(tab, "ev")` and `spearman_trend(tab,
  "win_pct")` on `monotone_table`'s per-level rows, thin levels (`n<15`)
  excluded from the rank correlation per the library's own rule.
- **Permutation calibration (mandatory, the centrepiece)**: every headline
  statistic — the two spearman trends and the top-vs-bottom EV/win% gaps —
  was run through `calibrate(fn, B, n_perm=10)` exactly as specified
  (`permute` reshuffles `out`/`win` within each session x mech cell,
  preserving every signal, count, and cell size). Because `n_perm=10` gives
  only an 11-point p-value grid (coarsest resolvable p = 1/11 = 0.091), every
  statistic that looked borderline or clearly-outside the 10-permutation
  null range was **re-run at `n_perm=200`** for resolution (same `calibrate`
  function, same `permute` null, just more draws) before being called
  anything. Both the mandatory n=10 call and the n=200 confirmation are
  reported; conclusions are drawn from the n=200 numbers, never from n=10
  alone, because 10 permutations cannot resolve p below ~0.09.
- **Top-vs-bottom thresholds**: chosen once off the pooled marginal
  distribution of each count (not per-cell, so "high"/"low" mean the same
  thing everywhere) and applied to every cell: `cc_flow_clean` HIGH >= 7,
  LOW <= 3 (of max 10, population median 5); `cc_flow` HIGH >= 8, LOW <= 4
  (of max 12, population median 7). Every cell clears >=15 fights on both
  arms with this choice (min 17, LOW arm, NY_AM M3).

### Cell sizes and baseline (unconditional) EV/win%

| session | mech | n | days | win% | EV |
|---|---|---:|---:|---:|---:|
| LONDON | M1 | 617 | 257 | 28.4 | -0.077 |
| LONDON | M2 | 280 | 137 | 37.5 | -0.139 |
| LONDON | M3 | 334 | 168 | 43.1 | -0.070 |
| NY_PRE | M1 | 438 | 233 | 29.9 | -0.036 |
| NY_PRE | M2 | 243 | 143 | 34.2 | -0.096 |
| NY_PRE | M3 | 244 | 137 | 35.7 | -0.089 |
| NY_AM | M1 | 486 | 226 | 41.6 | +0.005 |
| NY_AM | M2 | 263 | 116 | 60.8 | -0.033 |
| NY_AM | M3 | 248 | 128 | 52.0 | -0.181 |

Every cell's unconditional EV is at or below zero (consistent with BR-86/90 —
the population nets zero before any selection layer). The question here is
purely whether stacked flow agreement moves a cell *away* from that baseline
in either direction, and whether that move survives permutation.

---

## 2. PER-SESSION CONVICTION TABLES (primary: `cc_flow_clean`, never pooled)

Win% and EV reported side by side (Law 3, dual currency). `lo`/`hi` is the
day-clustered 95% CI on EV at that level (`dboot_mean`, 2,000 draws); `--`
means the level has `n<15` and is marked thin (excluded from the
monotonicity test too). Full 0-10-level tables, all nine cells:

### LONDON x M1 (n=617, 257 days)

| level | n | days | win% | EV | 95% CI (EV) |
|---:|---:|---:|---:|---:|:---:|
| 0 | 6 | 6 | 0.0 | -1.072 | -- |
| 1 | 9 | 9 | 33.3 | +0.797 | -- |
| 2 | 27 | 23 | 33.3 | +0.145 | [-0.52, +0.96] |
| 3 | 67 | 56 | 20.9 | -0.370 | [-0.72, +0.02] |
| 4 | 104 | 88 | 31.7 | -0.093 | [-0.43, +0.27] |
| 5 | 153 | 116 | 28.8 | -0.062 | [-0.33, +0.23] |
| 6 | 112 | 88 | 28.6 | +0.054 | [-0.36, +0.53] |
| 7 | 84 | 73 | 31.0 | +0.120 | [-0.36, +0.65] |
| 8 | 33 | 28 | 30.3 | -0.278 | [-0.67, +0.23] |
| 9 | 20 | 18 | 20.0 | -0.654 | [-0.98, -0.24] |
| 10 | 2 | 2 | 0.0 | -1.065 | -- |

No shape: EV bounces around zero with no rise into the high levels; the one
CI that clears zero (level 9) clears NEGATIVE.

### LONDON x M2 (n=280, 137 days)

| level | n | days | win% | EV | 95% CI (EV) |
|---:|---:|---:|---:|---:|:---:|
| 0 | 3 | 3 | 33.3 | +0.251 | -- |
| 1 | 5 | 5 | 60.0 | +0.208 | -- |
| 2 | 11 | 11 | 45.5 | +0.300 | -- |
| 3 | 31 | 30 | 58.1 | +0.342 | [-0.21, +0.94] |
| 4 | 35 | 30 | 17.1 | -0.700 | [-0.93, -0.46] |
| 5 | 47 | 37 | 36.2 | -0.218 | [-0.54, +0.10] |
| 6 | 60 | 48 | 43.3 | +0.035 | [-0.33, +0.51] |
| 7 | 49 | 39 | 26.5 | -0.459 | [-0.79, -0.10] |
| 8 | 29 | 27 | 44.8 | +0.073 | [-0.42, +0.59] |
| 9 | 10 | 10 | 30.0 | -0.467 | -- |

The low end (levels 0-3) is the best-performing part of this cell, not the
high end — the opposite of CONCORD.

### LONDON x M3 (n=334, 168 days)

| level | n | days | win% | EV | 95% CI (EV) |
|---:|---:|---:|---:|---:|:---:|
| 0 | 1 | 1 | 100.0 | +0.171 | -- |
| 1 | 6 | 6 | 16.7 | -0.735 | -- |
| 2 | 13 | 13 | 46.2 | +0.797 | -- |
| 3 | 33 | 29 | 54.5 | +0.019 | [-0.36, +0.42] |
| 4 | 61 | 51 | 50.8 | +0.048 | [-0.31, +0.44] |
| 5 | 65 | 57 | 43.1 | -0.040 | [-0.36, +0.28] |
| 6 | 65 | 55 | 43.1 | -0.071 | [-0.34, +0.24] |
| 7 | 50 | 43 | 30.0 | -0.334 | [-0.70, +0.12] |
| 8 | 31 | 27 | 35.5 | -0.369 | [-0.69, -0.07] |
| 9 | 8 | 8 | 50.0 | -0.284 | -- |
| 10 | 1 | 1 | 100.0 | +1.871 | -- |

A clean, near-monotone DECLINE from level 3 through level 8 in both win% and
EV — see §4, this is the one cell where the trend calibrates as real.

### NY_PRE x M1 (n=438, 233 days)

| level | n | days | win% | EV | 95% CI (EV) |
|---:|---:|---:|---:|---:|:---:|
| 0 | 1 | 1 | 100.0 | +4.605 | -- |
| 1 | 6 | 6 | 16.7 | +1.286 | -- |
| 2 | 10 | 10 | 10.0 | -0.672 | -- |
| 3 | 53 | 46 | 22.6 | +0.068 | [-0.64, +1.06] |
| 4 | 83 | 71 | 28.9 | -0.190 | [-0.50, +0.15] |
| 5 | 90 | 76 | 31.1 | -0.013 | [-0.36, +0.39] |
| 6 | 83 | 72 | 31.3 | -0.084 | [-0.44, +0.31] |
| 7 | 56 | 50 | 33.9 | -0.108 | [-0.49, +0.36] |
| 8 | 36 | 35 | 27.8 | -0.074 | [-0.60, +0.54] |
| 9 | 18 | 18 | 38.9 | -0.061 | [-0.64, +0.60] |
| 10 | 2 | 2 | 100.0 | +4.367 | -- |

Win% drifts up (22.6% -> 38.9% across non-thin levels) but EV stays flat to
slightly negative the whole way — a textbook dual-currency split (§4).

### NY_PRE x M2 (n=243, 143 days)

| level | n | days | win% | EV | 95% CI (EV) |
|---:|---:|---:|---:|---:|:---:|
| 1 | 1 | 1 | 0.0 | -1.154 | -- |
| 2 | 8 | 7 | 37.5 | -0.322 | -- |
| 3 | 23 | 22 | 39.1 | -0.095 | [-0.62, +0.48] |
| 4 | 39 | 32 | 46.2 | +0.658 | [-0.29, +2.02] |
| 5 | 44 | 35 | 36.4 | -0.038 | [-0.47, +0.47] |
| 6 | 52 | 45 | 32.7 | -0.241 | [-0.67, +0.35] |
| 7 | 28 | 25 | 28.6 | -0.445 | [-0.74, -0.08] |
| 8 | 21 | 20 | 38.1 | -0.006 | [-0.62, +0.68] |
| 9 | 21 | 20 | 14.3 | -0.657 | [-0.97, -0.29] |
| 10 | 6 | 5 | 16.7 | -0.783 | -- |

Best level is 4 (of 10); levels 7 and 9 clear NEGATIVE. High end is worse
than the middle.

### NY_PRE x M3 (n=244, 137 days)

| level | n | days | win% | EV | 95% CI (EV) |
|---:|---:|---:|---:|---:|:---:|
| 1 | 5 | 5 | 20.0 | -0.476 | -- |
| 2 | 11 | 10 | 27.3 | -0.257 | -- |
| 3 | 19 | 19 | 36.8 | -0.128 | [-0.70, +0.53] |
| 4 | 40 | 34 | 45.0 | +0.102 | [-0.41, +0.70] |
| 5 | 37 | 33 | 27.0 | -0.273 | [-0.77, +0.37] |
| 6 | 53 | 45 | 37.7 | -0.046 | [-0.44, +0.41] |
| 7 | 47 | 41 | 36.2 | -0.100 | [-0.46, +0.33] |
| 8 | 21 | 17 | 23.8 | -0.410 | [-0.90, +0.25] |
| 9 | 10 | 10 | 60.0 | +0.790 | -- |
| 10 | 1 | 1 | 0.0 | -1.017 | -- |

No shape; every non-thin CI spans zero.

### NY_AM x M1 (n=486, 226 days)

| level | n | days | win% | EV | 95% CI (EV) |
|---:|---:|---:|---:|---:|:---:|
| 0 | 1 | 1 | 0.0 | -1.016 | -- |
| 1 | 4 | 4 | 0.0 | -1.053 | -- |
| 2 | 9 | 9 | 55.6 | +0.761 | -- |
| 3 | 20 | 19 | 35.0 | -0.033 | [-0.72, +0.78] |
| 4 | 76 | 62 | 40.8 | +0.241 | [-0.15, +0.65] |
| 5 | 90 | 74 | 32.2 | -0.279 | [-0.53, +0.00] |
| 6 | 98 | 76 | 40.8 | -0.126 | [-0.39, +0.18] |
| 7 | 77 | 68 | 46.8 | +0.279 | [-0.08, +0.69] |
| 8 | 56 | 51 | 46.4 | -0.096 | [-0.39, +0.22] |
| 9 | 38 | 36 | 52.6 | +0.177 | [-0.25, +0.62] |
| 10 | 17 | 17 | 47.1 | -0.125 | [-0.60, +0.40] |

Win% rises fairly steadily (35.0% at level 3 to 52.6% at level 9); EV is
essentially flat/noisy the whole way (-0.28 to +0.28, all CIs span zero) —
another dual-currency split (§4).

### NY_AM x M2 (n=263, 116 days)

| level | n | days | win% | EV | 95% CI (EV) |
|---:|---:|---:|---:|---:|:---:|
| 1 | 3 | 3 | 33.3 | -0.038 | -- |
| 2 | 4 | 4 | 50.0 | -0.388 | -- |
| 3 | 24 | 17 | 79.2 | +0.253 | [-0.14, +0.62] |
| 4 | 38 | 31 | 60.5 | -0.152 | [-0.40, +0.10] |
| 5 | 63 | 43 | 41.3 | -0.085 | [-0.51, +0.57] |
| 6 | 53 | 42 | 62.3 | -0.049 | [-0.26, +0.15] |
| 7 | 37 | 28 | 73.0 | +0.016 | [-0.25, +0.25] |
| 8 | 17 | 17 | 64.7 | +0.013 | [-0.40, +0.45] |
| 9 | 17 | 14 | 70.6 | -0.080 | [-0.36, +0.12] |
| 10 | 7 | 7 | 85.7 | +0.110 | -- |

High baseline win% in this cell (this is the 60.8%-win M2 continuation
mechanism), no level separates on EV; every non-thin CI spans zero.

### NY_AM x M3 (n=248, 128 days)

| level | n | days | win% | EV | 95% CI (EV) |
|---:|---:|---:|---:|---:|:---:|
| 1 | 2 | 2 | 0.0 | -1.039 | -- |
| 2 | 5 | 4 | 40.0 | -0.183 | -- |
| 3 | 10 | 9 | 40.0 | -0.492 | -- |
| 4 | 32 | 30 | 53.1 | -0.081 | [-0.53, +0.57] |
| 5 | 60 | 46 | 55.0 | -0.163 | [-0.38, +0.05] |
| 6 | 43 | 31 | 37.2 | -0.382 | [-0.68, -0.09] |
| 7 | 49 | 37 | 63.3 | +0.045 | [-0.18, +0.28] |
| 8 | 30 | 23 | 50.0 | -0.286 | [-0.58, +0.02] |
| 9 | 10 | 10 | 70.0 | -0.023 | -- |
| 10 | 7 | 6 | 57.1 | -0.184 | -- |

No shape; level 6 clears NEGATIVE, no level clears positive. This is the
cell whose top-vs-bottom contrast looks best (§5) but does not hold up
against calibration.

---

## 3. MONOTONICITY (Spearman, level vs metric)

| cell | EV trend (clean) | win% trend (clean) | EV trend (full, `cc_flow`) | win% trend (full) | primary/secondary agree? |
|---|---:|---:|---:|---:|:---:|
| LONDON M1 | -0.405 | -0.452 | -0.283 | +0.183 | NO (win sign flips) |
| LONDON M2 | -0.029 | -0.029 | +0.036 | +0.143 | NO (both flip, magnitudes ~0) |
| LONDON M3 | **-0.943** | **-0.928** | -0.548 | -0.190 | yes (same sign, weaker) |
| NY_PRE M1 | -0.143 | +0.643 | -0.393 | +0.786 | yes |
| NY_PRE M2 | -0.500 | -0.750 | -0.762 | -0.524 | yes |
| NY_PRE M3 | -0.371 | -0.600 | +0.107 | +0.036 | NO (both flip) |
| NY_AM M1 | -0.048 | **+0.881** | +0.381 | +0.881 | NO (EV flips) |
| NY_AM M2 | +0.000 | +0.107 | -0.143 | +0.071 | NO (EV flips) |
| NY_AM M3 | -0.200 | -0.100 | -0.257 | +0.543 | NO (win flips) |

**Not one cell shows a positive EV trend that is both non-trivial in
magnitude and stable between the primary and secondary count.** Five of nine
cells flip sign on at least one metric when `s_closeloc`/`s_rangex` are added
back in (§6) — the trend is not robust to that choice in most cells, which
is itself informative. Two patterns stand out and are calibrated in §4:

- **LONDON M3**: strong negative EV *and* win% trend (-0.94/-0.93), same
  sign both counts — a real shape, running backwards from CONCORD.
- **NY_PRE M1 and NY_AM M1**: win% trend positive (+0.64, +0.88) while EV
  trend is flat-to-negative (-0.14, -0.05) — dual-currency inversions
  (BR-20's pattern): more agreement, better hit rate, no better money.

---

## 4. PERMUTATION CALIBRATION — the centrepiece

Every trend statistic above was calibrated against `calibrate(fn, B,
n_perm=10)` exactly as specified. Because 10 permutations only resolve a
p-value to the nearest 1/11 (~0.09), anything that looked outside or near
the edge of the 10-permutation null was re-run at `n_perm=200` for real
resolution before being called anything. **Both are reported; conclusions
use the n=200 numbers.**

### 4a. Mandatory n_perm=10 calibration (spearman EV/win trend, `cc_flow_clean`)

| cell | metric | real | null mean | null range (10 perms) | inside null? | emp. p |
|---|---|---:|---:|---:|:---:|---:|
| LONDON M1 | EV trend | -0.405 | -0.255 | [-0.90, +0.21] | yes | 0.455 |
| LONDON M1 | win% trend | -0.452 | -0.049 | [-0.81, +0.33] | yes | 0.182 |
| LONDON M2 | EV trend | -0.029 | -0.177 | [-0.94, +0.89] | yes | 1.000 |
| LONDON M2 | win% trend | -0.029 | -0.091 | [-0.89, +0.83] | yes | 1.000 |
| **LONDON M3** | **EV trend** | **-0.943** | +0.069 | [-0.71, +0.66] | **NO** | 0.091 |
| **LONDON M3** | **win% trend** | **-0.928** | +0.291 | [-0.31, +0.77] | **NO** | 0.091 |
| NY_PRE M1 | EV trend | -0.143 | +0.150 | [-0.75, +0.71] | yes | 0.636 |
| NY_PRE M1 | win% trend | +0.643 | +0.101 | [-0.75, +0.79] | yes | 0.364 |
| NY_PRE M2 | EV trend | -0.500 | -0.064 | [-0.89, +0.68] | yes | 0.545 |
| NY_PRE M2 | win% trend | -0.750 | -0.054 | [-0.61, +0.86] | NO | 0.182 |
| NY_PRE M3 | EV trend | -0.371 | -0.274 | [-0.89, +0.60] | yes | 0.636 |
| NY_PRE M3 | win% trend | -0.600 | -0.177 | [-0.71, +0.37] | yes | 0.182 |
| NY_AM M1 | EV trend | -0.048 | -0.119 | [-0.69, +0.67] | yes | 1.000 |
| **NY_AM M1** | **win% trend** | **+0.881** | -0.086 | [-0.69, +0.57] | **NO** | 0.091 |
| NY_AM M2 | EV trend | +0.000 | -0.086 | [-0.89, +0.82] | yes | 1.000 |
| NY_AM M2 | win% trend | +0.107 | +0.087 | [-0.81, +0.93] | yes | 0.818 |
| NY_AM M3 | EV trend | -0.200 | -0.240 | [-0.80, +0.90] | yes | 0.727 |
| NY_AM M3 | win% trend | -0.100 | -0.095 | [-0.70, +0.60] | yes | 0.909 |

Three rows fall outside the 10-permutation null range: LONDON M3 (both EV
and win% trend) and NY_AM M1 (win% trend only, its EV trend sits dead
center of the null). Everything else — 15 of 18 trend statistics — sits
comfortably inside a null built from pure noise. **This is exactly BR-97's
finding reproducing on a fresh construction: most of what looks like a
pattern in a raw table is noise, and the calibration is what tells you
which.**

### 4b. n_perm=200 resolution — every trend and top-vs-bottom statistic, all 9 cells

Run on the exact same `calibrate`/`permute` machinery, just more draws, so
p is resolvable to 1/201 instead of 1/11. **This is the complete set — 18
trend statistics + 18 top-vs-bottom statistics = 36 headline numbers**, not
a cherry-picked subset.

**Spearman trend (level vs metric), `cc_flow_clean`:**

| cell | EV trend | emp. p | win% trend | emp. p |
|---|---:|---:|---:|---:|
| LONDON M1 | -0.405 | 0.443 | -0.452 | 0.368 |
| LONDON M2 | -0.029 | 1.000 | -0.029 | 1.000 |
| **LONDON M3** | **-0.943** | **0.025** | **-0.928** | **0.025** |
| NY_PRE M1 | -0.143 | 0.786 | +0.643 | 0.174 |
| NY_PRE M2 | -0.500 | 0.313 | -0.750 | 0.070 |
| NY_PRE M3 | -0.371 | 0.517 | -0.600 | 0.289 |
| NY_AM M1 | -0.048 | 0.950 | **+0.881** | **0.020** |
| NY_AM M2 | +0.000 | 1.000 | +0.107 | 0.836 |
| NY_AM M3 | -0.200 | 0.791 | -0.100 | 0.950 |

**Top-vs-bottom gap (HIGH>=7 minus LOW<=3, `cc_flow_clean`):**

| cell | EV gap | emp. p | win% gap | emp. p |
|---|---:|---:|---:|---:|
| LONDON M1 | +0.081 | 0.756 | +4.9pp | 0.393 |
| **LONDON M2** | **-0.581** | **0.020** | **-21.0pp** | **0.010** |
| LONDON M3 | -0.448 | 0.095 | -14.6pp | 0.119 |
| NY_PRE M1 | -0.141 | 0.677 | +12.5pp | 0.090 |
| NY_PRE M2 | -0.230 | 0.602 | -11.2pp | 0.309 |
| NY_PRE M3 | +0.148 | 0.592 | +4.0pp | 0.667 |
| NY_AM M1 | +0.082 | 0.781 | +12.6pp | 0.174 |
| NY_AM M2 | -0.138 | 0.512 | +0.8pp | 0.970 |
| NY_AM M3 | +0.382 | 0.104 | +24.1pp | 0.045 |

**Reading it, statistic by statistic before conclusions:** of 36 headline
numbers, 6 fall under p=0.05 — roughly 3x the ~1.8 expected by chance at
alpha=0.05 across 36 tests, but not by a margin that lets every one of them
stand alone; each has to pass its *own* dual-currency and robustness check
before it counts as anything (Law 3):

- **LONDON M3 trend** (EV p=0.025, win% p=0.025): dual-currency-consistent
  (same sign, both currencies) but caveated — `spearman_trend` ranks only
  6 non-thin levels here, so the achievable rho values are coarse (±0.943
  is close to the most extreme 6-point rho possible), and its own
  top-vs-bottom check on the SAME cell does **not** independently clear
  (p=0.095 EV, p=0.119 win%). Suggestive, not confirmed.
- **LONDON M2 top-vs-bottom** (EV p=0.020, win% p=0.010): dual-currency-
  consistent, no small-sample caveat (88/50 fights), and its own trend
  statistic points the same negative direction (though the trend itself
  doesn't clear, p=1.00 — flat through the middle, negative only at the
  extremes, which is exactly what a threshold contrast is built to catch
  and a monotone rank test is not). **This is the single strongest
  calibrated result in the report.**
- **NY_AM M1 win% trend** (p=0.020): calibrated-real on its own, but its
  EV-trend partner sits at p=0.950 — dead center of the null. Fails dual
  currency. Not a finding; textbook BR-20 inversion (win rate moves,
  money does not).
- **NY_AM M3 top-vs-bottom win% gap** (p=0.045): calibrated-real on its
  own, but its EV-gap partner is p=0.104 — inside the null. Fails dual
  currency for the same reason as NY_AM M1 above. The day-clustered CI on
  this EV gap happened to clear zero (§5), which is exactly the case that
  makes permutation calibration mandatory rather than optional: the CI
  rule alone would have called this a finding, and it is not one.
- **NY_PRE M2 win% trend** (p=0.070) and **NY_PRE M1 top-vs-bottom win%
  gap** (p=0.090) are the closest near-misses among the rest; both fail
  their EV partner (p=0.313 and p=0.677) and neither clears 0.05 on its
  own metric either.

**Net: after requiring both calibration AND dual-currency agreement, only
two (session, mechanism) cells survive — LONDON M2 and, more weakly,
LONDON M3 — and both say more stacked flow agreement predicts a WORSE
trade, not a better one.**

---

## 5. TOP-VS-BOTTOM CONTRASTS (`cc_flow_clean` HIGH>=7 vs LOW<=3, all cells)

Day-clustered 95% CI on the arm DIFFERENCE (`dboot_diff`, paired day
resampling, seed 20260807, 2,000 draws — see §1).

| cell | n hi/lo | days hi/lo | win% hi | win% lo | EV hi | EV lo | EV gap | CI (gap) | win gap (pp) | CI (win gap) |
|---|---|---|---:|---:|---:|---:|---:|:---:|---:|:---:|
| LONDON M1 | 139/109 | 105/82 | 28.8 | 23.9 | -0.103 | -0.184 | +0.081 | [-0.42, +0.59] | +4.9 | [-6.5, +16.0] |
| **LONDON M2** | 88/50 | 62/46 | 33.0 | 54.0 | -0.267 | +0.314 | **-0.581** | **[-1.05, -0.12]** | **-21.0** | **[-38.2, -4.4]** |
| LONDON M3 | 90/53 | 64/44 | 34.4 | 49.1 | -0.313 | +0.136 | -0.448 | [-1.02, +0.05] | -14.6 | [-32.2, +1.7] |
| NY_PRE M1 | 112/70 | 99/58 | 33.9 | 21.4 | -0.010 | +0.132 | -0.141 | [-1.02, +0.61] | +12.5 | [-1.3, +26.1] |
| NY_PRE M2 | 76/32 | 60/30 | 26.3 | 37.5 | -0.410 | -0.181 | -0.230 | [-0.76, +0.31] | -11.2 | [-32.5, +10.0] |
| NY_PRE M3 | 79/35 | 64/31 | 35.4 | 31.4 | -0.070 | -0.218 | +0.148 | [-0.56, +0.76] | +4.0 | [-16.3, +22.8] |
| NY_AM M1 | 188/34 | 132/31 | 47.9 | 35.3 | +0.110 | +0.028 | +0.082 | [-0.55, +0.72] | +12.6 | [-5.5, +31.8] |
| NY_AM M2 | 78/31 | 47/21 | 71.8 | 71.0 | +0.004 | +0.142 | -0.138 | [-0.53, +0.30] | +0.8 | [-18.3, +23.4] |
| NY_AM M3 | 96/17 | 64/13 | 59.4 | 35.3 | -0.084 | -0.465 | +0.382 | [+0.06, +0.76] | +24.1 | [+1.5, +45.8] |

Only two cells clear zero on the day-clustered CI at all: **LONDON M2**
(negative, both currencies, and calibrated-real per §4b) and **NY_AM M3**
(positive, both currencies, but its permutation calibration in §4b puts the
EV gap inside the null — p=0.10 — so the CI-clears-zero read is not backed
by the calibration and should not be reported as a finding). Every other
cell's top-vs-bottom CI spans zero on both currencies. **This is the direct
demonstration of why permutation calibration is mandatory**: the naive rule
"day-clustered CI excludes zero" would have flagged NY_AM M3 as a positive
CONCORD result; the calibrated null shows that exact magnitude of gap
appears in 1 of 10 (and ~1 of 10 at n=200, 21/201) pure-noise permutations
of the same cell — not rare enough to believe.

Secondary check with `cc_flow` (HIGH>=8, LOW<=4, includes closeloc/rangex):
directionally consistent with the primary result for LONDON M2 and M3
(still negative) but the magnitudes shrink, consistent with §6's point that
`s_closeloc` mostly adds noise to the count.

---

## 6. EFFECT OF `s_closeloc` / `s_rangex` (why `cc_flow_clean` is primary)

- `s_closeloc` agrees with the trade 95.2% of fights — confirmed on this
  population (task's stated 95.2% reproduces exactly). It is very nearly a
  constant, so folding it into a count adds almost the same +1 to almost
  every row: it does not discriminate between fights, it just shifts the
  whole distribution, while being risk-coupled per BR-43 (closeloc is part
  of the risk = closeloc x range identity) — exactly why Law-2 flags it.
- `s_rangex` agrees exactly 50.0% of the time by construction (its threshold
  IS the population median), so on its own it is uninformative by
  definition; it can still interact with other signals, which is why it's
  worth checking, not assuming away.
- **Measured effect of including both**: `cc_flow` and `cc_flow_clean` are
  correlated at rho=0.963 (close but not identical). Comparing the primary
  (clean) and secondary (full) trend columns in §3, **5 of 9 cells flip the
  sign of at least one Spearman trend** when closeloc/rangex are added back
  — LONDON M1 (win%), LONDON M2 (both, though both are ~0), NY_PRE M3
  (both), NY_AM M1 (EV), NY_AM M2 (EV), NY_AM M3 (win%). The top-vs-bottom
  contrast is more stable (same sign, shrunk magnitude, for the two cells
  that mattered — LONDON M2/M3). **Conclusion: including `s_closeloc`
  materially changes which cells look like they have a monotone trend, in
  the direction of manufacturing apparent structure that the clean count
  does not show — this is the mechanism BR-43 predicted, and it is why
  `cc_flow_clean` is reported as primary throughout.**

---

## 7. WHAT STACKED FLOW SAYS

**No cell shows a monotone, calibrated, dual-currency-consistent POSITIVE
relationship between stacked flow agreement and trade quality.** Specifically:

1. **Nothing confirms CONCORD.** Zero of nine cells show EV climbing with
   conviction level in a way that survives permutation calibration. The two
   cells with the largest apparent win% trend (NY_PRE M1 +0.64, NY_AM M1
   +0.88) both fail on EV — the same dual-currency-inversion pattern this
   programme has now found repeatedly (BR-20, and now here): higher
   conviction buys a higher hit rate and pays for it in size, netting
   nothing. Per Law 3, these are refutations, not findings.

2. **One session actively refutes it.** LONDON is the only session where a
   flow-conviction relationship survives calibration at all, and it runs
   BACKWARDS: LONDON M2's top-vs-bottom gap (p=0.02 EV, p=0.01 win% at
   n=200 permutations) shows HIGH stacked agreement performing worse than
   LOW agreement, in both currencies, in agreement with LONDON M3's
   monotone decline (p=0.025, with the caveat that its own top-vs-bottom
   check does not independently confirm at p=0.10-0.12). LONDON M1 shows
   the same negative direction non-significantly. The honest reading is not
   "CONCORD works in reverse in LONDON" (M3's result doesn't survive its
   own robustness check) but "there is no session where stacking flow
   signals helps, and LONDON is where it comes closest to calibrated
   evidence of actively hurting."

3. **The permutation null is doing real work.** Of 36 headline numbers (18
   trend + 18 top-vs-bottom statistics), 6 clear p<0.05 at n=200 — about
   3x the ~1.8 expected by chance, but requiring each to also pass its
   dual-currency partner (Law 3) drops that to **2 independent
   cell-level findings, both negative, both in LONDON** (M2's
   top-vs-bottom gap and M3's monotone trend); the other two "significant"
   numbers (NY_AM M1 win-trend, NY_AM M3 win-gap) each fail because their
   EV partner sits inside the null. This mirrors BR-97 exactly: a
   plausible-looking raw table throws up a handful of "interesting" cells
   at roughly the rate pure noise would, and calibration plus dual currency
   is what separates the real ones from the rest.

4. **`cc_flow_clean` vs `cc_flow` disagree often enough to matter.** 5 of 9
   cells flip the sign of at least one trend when the near-constant,
   risk-coupled `s_closeloc` is folded back in — reproducing BR-43's
   mechanism live. `cc_flow_clean` is the right primary metric for exactly
   the reason the library's docstring gives.

**Verdict for the trader: do not size or gate on stacked flow-signal count.**
The construct does not predict better trades in any of the three sessions
or three mechanisms tested. Where a calibrated relationship exists at all
(LONDON M2, and more weakly M3), it says the opposite of what a
conviction-sizing rule would want to hear. This is a publishable null,
consistent with BR-19/26/62/94/97, on a construction that had a real reason
to reopen the question (the orientation fix) and still found nothing to
confirm.
