# Conviction × run distance — the exit-agnostic test

*Generated 2026-08-08 from `output/htf_ma_census/race_wide.parquet` (via
`scripts/conviction_lib.py`) joined to `output/htf_ma_census/race_runs.parquet`
(untruncated walk-outs: stop or session end only, no structural target).
Read-only — no parquet touched, nothing committed, nothing adopted.
Code: `/tmp/claude-0/.../scratchpad/run_analysis.py`, `run_ci_calib.py`,
`run_divergence.py` (session-scratch, not committed).*

**Bottom line up front: no.** Across all nine (session × mechanism) cells,
conviction does not produce a rising `P(reach 3R)` or a rising run-distance
distribution with the stacked-agreement count. Where the top-vs-bottom
contrast is negative and largest (NY_AM M2: HIGH arm reaches 3R **less**
often than LOW, -18.9 points; NY_PRE M2 spearman -0.166), it still sits
**inside** the run-block permutation null (p=0.035 and p=0.015
respectively — the closest things to a signal in the whole sweep, and both
run the WRONG way, high conviction predicting a *shorter* run, not a
longer one). The aggregate contrast across all 9 cells (-5.16 points) is
also inside its null (p=0.075). This is the same "no edge, occasionally
backwards" verdict `conviction-flow.md` reached under the truncated EV
target — reached again here under an exit-agnostic target that cannot be
blamed for closing early. Divergence at entry is uncorrelated with run
length in every mechanism, in both directions of the reversal/continuation
hypothesis. The one structural fact that is real and matters for
everything else: **median time-to-peak is 3 minutes**, so most of a run's
whole life is over before most plausible exits could act on it anyway.

---

## 1. METHOD

- **Join.** `B = add_counts(signals(load()))` merged to `race_runs.parquet`
  on `scid`, inner join → **3,153 fights**, all rows of `race_wide` matched
  (no loss). Whole-book reach rates reproduce the stated baselines exactly:
  reach 1R 51.76%, 2R 34.19%, 3R 25.06%, 5R 15.19%, 8R 9.74%, stopped
  92.42%, median bars held 9, median mins-to-peak 3 — the merge is sound.
- **Conviction measure.** `cc_flow_clean` (10 flow signals, `s_closeloc`/
  `s_rangex` dropped, LAW-2) is primary, for direct comparability with
  `conviction-flow.md`. Three tiers used throughout: **LOW** (count 0-3),
  **MID** (4-6), **HIGH** (7-10) — same cut points as the prior flow
  report's top-vs-bottom thresholds (population median is 5-6). Every
  cell clears ≥15 fights in both LOW and HIGH (min 17, NY_AM M3 LOW).
  `cc_all_clean` (flow+depth, 15 signals) was spot-checked as a robustness
  variant (§7 footnote); it does not change the conclusion.
- **Cells.** 3 sessions × 3 mechanisms = 9, never pooled for the core
  tables. Per-cell n 243-617, days 116-257 — identical population to
  `conviction-flow.md`.
- **Day-clustered CIs.** `dboot_mean` (`scripts/conviction_lib.py`, seed
  20260807, 2,000 draws, clustered on `sess_day`) used directly for
  per-level `P(reach 3R)`. For the HIGH-vs-LOW **difference** in a metric
  (proportion, median, or p90 of `run_mfe_r`), a `day_boot_diff` helper was
  written on top of it: each of 2,000 draws resamples the **same** set of
  days (with replacement) and applies that one draw to both arms before
  differencing — paired on day, not two independent bootstraps — then
  reports the 2.5/97.5 percentiles of the 2,000 differences.
- **Permutation calibration — mandatory, the centrepiece.** `permute` in
  `conviction_lib.py` shuffles `out`/`win`, which is the wrong null here:
  run distance is a completely different set of columns. A parallel
  `permute_runs(M, seed)` was written: within each (session, mech) cell, one
  random row-permutation is drawn and applied **identically** to the full
  run-outcome block — `run_mfe_r`, `run_mae_r`, `stopped`, `bars_held`,
  `mins_to_peak`, `eod_r`, `reach_1r..reach_8r`, `exc_5m_r..exc_60m_r` — so
  a shuffled row's `reach_3r` still exactly matches its (also shuffled)
  `run_mfe_r`: internal consistency of each run is preserved, only which
  *fight* it lands on is randomised. Conviction counts, signals, and
  divergence columns stay on the original row — the null answers exactly
  "does conviction predict which run a fight draws", nothing else.
  `calibrate_runs(fn, M, n_perm, permute_runs)` mirrors `calibrate`'s
  signature. Per the brief, `n_perm=10` was run first (the mandatory,
  coarse 11-point grid); every headline was then re-run at `n_perm=200` for
  resolution, matching `conviction-flow.md`'s practice — conclusions are
  drawn from the 200-permutation numbers.
- **Divergence null.** A second, independent shuffle, `permute_div`, moves
  only the divergence block (`div_5m/15m/30m`, `dvg_15m/30m`) as a unit
  within each (session, mech) cell, leaving run outcomes and conviction on
  the original row. `dvg_5m` is **entirely NaN** (0/3,153 populated) and is
  dropped from every divergence test; `div_5m` (boolean) is used in its
  place for the 5-minute window.

### Cell sizes and unconditional baseline (no conditioning on conviction)

| session | mech | n | days | P(1R) | P(2R) | P(3R) | P(5R) | P(8R) | med `run_mfe_r` | p90 `run_mfe_r` | med peak(min) | med bars |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| LONDON | M1 | 617 | 257 | 54.3% | 34.8% | 26.3% | 16.9% | 13.5% | 1.16 | 11.27 | 3 | 10 |
| LONDON | M2 | 280 | 137 | 52.5% | 35.4% | 26.1% | 14.6% | 8.9% | 1.08 | 6.91 | 2 | 8 |
| LONDON | M3 | 334 | 168 | 51.5% | 35.6% | 27.8% | 17.1% | 9.3% | 1.02 | 7.22 | 2 | 7 |
| NY_AM | M1 | 486 | 226 | 56.0% | 36.8% | 25.7% | 15.0% | 8.0% | 1.26 | 7.40 | 3 | 10 |
| NY_AM | M2 | 263 | 116 | 48.7% | 35.4% | 24.3% | 14.4% | 6.5% | 0.93 | 6.35 | 3 | 10 |
| NY_AM | M3 | 248 | 128 | 45.2% | 26.6% | 17.7% | 10.1% | 4.4% | 0.83 | 4.98 | 2 | 7 |
| NY_PRE | M1 | 438 | 233 | 53.2% | 35.4% | 24.9% | 15.8% | 11.4% | 1.14 | 9.48 | 3 | 9 |
| NY_PRE | M2 | 243 | 143 | 46.5% | 30.9% | 23.5% | 11.1% | 7.8% | 0.90 | 5.39 | 2 | 8 |
| NY_PRE | M3 | 244 | 137 | 49.2% | 31.6% | 25.8% | 18.4% | 13.1% | 0.93 | 10.02 | 3 | 8 |

---

## 2. P(REACH R) BY CONVICTION — per cell, never pooled

### 2a. Core metric, full-resolution: `P(reach 3R)` by every `cc_flow_clean` level (0-10)

No cell rises monotonically from level 0 to level 10. LONDON M1 wobbles
18-32% with no trend; LONDON M2 *falls* from 29-45% at levels 0-3 to
16-31% at 7-9; NY_AM M2 falls from 33-50% (levels 1-3) to 0-32% (7-10);
NY_AM M3 and NY_PRE M2 show the same shape. Every level-to-level CI at
n≥15 overlaps its neighbors.

| level | LON-M1 | LON-M2 | LON-M3 | NYAM-M1 | NYAM-M2 | NYAM-M3 | NYPRE-M1 | NYPRE-M2 | NYPRE-M3 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 16.7 (n6) | 33.3 (n3) | 0.0 (n1) | 0.0 (n1) | — | — | 100 (n1) | — | — |
| 1 | 33.3 (n9) | 40.0 (n5) | 16.7 (n6) | 0.0 (n4) | 33.3 (n3) | 50.0 (n2) | 16.7 (n6) | 100 (n1) | 40.0 (n5) |
| 2 | 25.9 (n27) | 45.5 (n11) | 30.8 (n13) | 33.3 (n9) | 50.0 (n4) | 20.0 (n5) | 20.0 (n10) | 12.5 (n8) | 27.3 (n11) |
| 3 | 25.4 (n67) | 29.0 (n31) | 42.4 (n33) | 35.0 (n20) | 41.7 (n24) | 0.0 (n10) | 24.5 (n53) | 30.4 (n23) | 21.1 (n19) |
| 4 | 23.1 (n104) | 8.6 (n35) | 24.6 (n61) | 28.9 (n76) | 21.1 (n38) | 18.8 (n32) | 22.9 (n83) | 33.3 (n39) | 30.0 (n40) |
| 5 | 26.8 (n153) | 36.2 (n47) | 27.7 (n65) | 20.0 (n90) | 20.6 (n63) | 20.0 (n60) | 24.4 (n90) | 20.5 (n44) | 18.9 (n37) |
| 6 | 27.7 (n112) | 31.7 (n60) | 26.2 (n65) | 26.5 (n98) | 22.6 (n53) | 16.3 (n43) | 24.1 (n83) | 23.1 (n52) | 30.2 (n53) |
| 7 | 32.1 (n84) | 16.3 (n49) | 24.0 (n50) | 31.2 (n77) | 32.4 (n37) | 20.4 (n49) | 25.0 (n56) | 21.4 (n28) | 23.4 (n47) |
| 8 | 18.2 (n33) | 20.7 (n29) | 29.0 (n31) | 23.2 (n56) | 17.6 (n17) | 13.3 (n30) | 22.2 (n36) | 23.8 (n21) | 14.3 (n21) |
| 9 | 25.0 (n20) | 30.0 (n10) | 25.0 (n8) | 26.3 (n38) | 17.6 (n17) | 20.0 (n10) | 38.9 (n18) | 14.3 (n21) | 50.0 (n10) |
| 10 | 0.0 (n2) | — | 100 (n1) | 11.8 (n17) | 0.0 (n7) | 14.3 (n7) | 100 (n2) | 0.0 (n6) | 0.0 (n1) |

(`—` = level not present in that cell; day-clustered 95% CIs at n≥15 given
in the scratch output all overlap adjacent levels — omitted here for
width, available in `run_analysis.py` output.)

### 2b. Tercile view, all five R thresholds

| cell | tier | n | P(1R) | P(2R) | P(3R) | P(5R) | P(8R) |
|---|---|---:|---:|---:|---:|---:|---:|
| LONDON M1 | LOW/MID/HIGH | 109/369/139 | 53.2/55.6/51.8 | 31.2/35.8/35.3 | 25.7/26.0/27.3 | 17.4/16.3/18.0 | 11.9/13.3/15.1 |
| LONDON M2 | LOW/MID/HIGH | 50/142/88 | 62.0/51.4/48.9 | 40.0/34.5/34.1 | 34.0/27.5/**19.3** | 20.0/15.5/10.2 | 8.0/10.6/6.8 |
| LONDON M3 | LOW/MID/HIGH | 53/191/90 | 62.3/46.1/56.7 | 45.3/33.5/34.4 | 35.8/26.2/26.7 | 22.6/16.8/14.4 | 15.1/8.4/7.8 |
| NY_AM M1 | LOW/MID/HIGH | 34/264/188 | 61.8/52.3/60.1 | 41.2/34.5/39.4 | 29.4/25.0/26.1 | 26.5/13.6/14.9 | 11.8/6.8/9.0 |
| NY_AM M2 | LOW/MID/HIGH | 31/154/78 | **71.0**/44.8/47.4 | **58.1**/31.2/34.6 | **41.9**/21.4/23.1 | **32.3**/13.0/10.3 | 16.1/5.8/3.8 |
| NY_AM M3 | LOW/MID/HIGH | 17/135/96 | 58.8/40.0/50.0 | 23.5/23.7/31.2 | 11.8/18.5/17.7 | 5.9/12.6/7.3 | 0.0/4.4/5.2 |
| NY_PRE M1 | LOW/MID/HIGH | 70/256/112 | 52.9/56.6/45.5 | 34.3/35.5/35.7 | 24.3/23.8/27.7 | 18.6/13.3/19.6 | 15.7/9.0/14.3 |
| NY_PRE M2 | LOW/MID/HIGH | 32/135/76 | **68.8**/45.2/39.5 | **53.1**/28.1/26.3 | 28.1/25.2/18.4 | 12.5/11.9/9.2 | 6.2/8.9/6.6 |
| NY_PRE M3 | LOW/MID/HIGH | 35/130/79 | 45.7/50.8/48.1 | 31.4/33.1/29.1 | 25.7/26.9/24.1 | 14.3/21.5/15.2 | 11.4/15.4/10.1 |

Bold = the cases where LOW clearly beats HIGH (NY_AM M2, NY_PRE M2 —
both M2/continuation cells, both by a wide, day-clustered margin at every
R). No cell shows a clean LOW<MID<HIGH staircase at P(3R).

---

## 3. RUN DISTRIBUTION BY CONVICTION (median / p75 / p90 of `run_mfe_r`, plus time)

| cell | tier | n | med R | p75 R | p90 R | med peak (min) | med bars |
|---|---|---:|---:|---:|---:|---:|---:|
| LONDON M1 | LOW/MID/HIGH | 109/369/139 | 1.13/1.16/1.19 | 3.00/3.21/3.44 | 9.1/11.8/16.1 | 2/4/4 | 5/11/11 |
| LONDON M2 | LOW/MID/HIGH | 50/142/88 | **1.51**/1.04/0.93 | 4.49/3.42/2.25 | 7.4/8.4/5.0 | 3/2/1 | 7.5/9.5/7.5 |
| LONDON M3 | LOW/MID/HIGH | 53/191/90 | **1.63**/0.86/1.24 | 4.11/3.13/3.25 | 12.3/6.9/6.9 | 2/3/2 | 11/8/5 |
| NY_AM M1 | LOW/MID/HIGH | 34/264/188 | 1.67/1.13/1.39 | 4.65/2.99/3.07 | 8.0/6.8/7.3 | 3.5/3/4 | 9.5/9/11 |
| NY_AM M2 | LOW/MID/HIGH | 31/154/78 | **2.66**/0.80/0.92 | **6.23**/2.66/2.68 | **9.2**/6.1/4.9 | **11**/2/3.5 | 20/8/18.5 |
| NY_AM M3 | LOW/MID/HIGH | 17/135/96 | 1.13/0.78/0.97 | 1.92/1.86/2.38 | 3.3/5.4/3.9 | 1/2/3 | 6/6/9.5 |
| NY_PRE M1 | LOW/MID/HIGH | 70/256/112 | 1.03/1.28/0.92 | 2.89/2.76/3.51 | 12.4/6.8/13.2 | 2/3.5/2.5 | 5.5/10/8 |
| NY_PRE M2 | LOW/MID/HIGH | 32/135/76 | **2.09**/0.88/0.70 | 3.12/2.91/2.03 | 5.3/5.5/4.9 | 4.5/2/1.5 | 9.5/9/6 |
| NY_PRE M3 | LOW/MID/HIGH | 35/130/79 | 0.74/1.01/0.87 | 3.12/3.54/2.53 | 7.7/10.2/8.1 | 1/3/3 | 4/8/9 |

Bold: LOW arm's median run is the *largest* of the three tiers in 4 of 9
cells (both LONDON M2/M3, both M2-family cells) — the opposite of what
conviction sizing needs. Only LONDON M1 and (weakly) NY_AM M1 show a
LOW<MID≤HIGH ordering on the median, and neither survives calibration
(§5).

---

## 4. TOP-VS-BOTTOM CONTRASTS (HIGH 7-10 vs LOW 0-3), day-clustered 95% CI on the difference

| session | mech | n(lo/hi) | ΔP(3R) pts | 95% CI | Δ median R | 95% CI | Δ p90 R | 95% CI |
|---|---|---|---:|---|---:|---|---:|---|
| LONDON | M1 | 109/139 | +1.65 | [-9.5, +13.0] | +0.06 | [-0.50, +0.55] | +6.94 | [-4.2, +14.5] |
| LONDON | M2 | 50/88 | -14.68 | [-29.6, -0.7] | -0.58 | [-1.84, +0.24] | -2.46 | [-8.8, +3.6] |
| LONDON | M3 | 53/90 | -9.18 | [-26.1, +7.9] | -0.39 | [-1.82, +0.51] | -5.41 | [-14.6, +14.8] |
| NY_AM | M1 | 34/188 | -3.35 | [-20.2, +13.9] | -0.28 | [-1.28, +0.63] | -0.69 | [-6.9, +3.8] |
| NY_AM | M2 | 31/78 | -18.86 | [-41.3, +1.9] | -1.75 | [-4.33, -0.09] | -4.23 | [-11.6, -0.2] |
| NY_AM | M3 | 17/96 | +5.94 | [-12.4, +21.8] | -0.15 | [-1.08, +0.67] | +0.56 | [-1.7, +3.9] |
| NY_PRE | M1 | 70/112 | +3.39 | [-10.2, +16.5] | -0.11 | [-0.96, +0.49] | +0.83 | [-10.5, +10.0] |
| NY_PRE | M2 | 32/76 | -9.70 | [-28.4, +8.2] | -1.38 | [-2.04, -0.37] | -0.42 | [-6.9, +7.0] |
| NY_PRE | M3 | 35/79 | -1.66 | [-21.2, +16.7] | +0.13 | [-0.66, +0.76] | +0.45 | [-10.8, +16.2] |

6 of 9 cells: HIGH's P(3R) contrast is *negative*. 7 of 9: HIGH's median
run is *smaller*. Two cells (LONDON M2, NY_AM M2 — both on the median-R
gap; NY_PRE M2 on median-R too) clear zero on the raw day-clustered CI.
That looks like signal — but see §5: it does not survive the permutation
null designed for exactly this comparison, with one narrow exception.

---

## 5. PERMUTATION CALIBRATION — real vs null, every headline (the centrepiece)

Null = `permute_runs`: the run-outcome block shuffled as one unit within
each (session, mech) cell (see §1). `n_perm=10` run first (mandatory,
coarse grid), `n_perm=200` for resolution; conclusions from n=200.

### 5a. `n_perm=10` (mandatory grid, coarse)

| cell | real ΔP(3R) | null10 mean | null10 range | real spearman(cc, mfe) | null10 mean | null10 range |
|---|---:|---:|---|---:|---:|---|
| LONDON M1 | +1.65 | -3.14 | [-13.0, +8.4] | +0.010 | +0.002 | [-0.050, +0.059] |
| LONDON M2 | -14.68 | -2.94 | [-12.1, +6.1] | -0.092 | +0.001 | [-0.076, +0.079] |
| LONDON M3 | -9.18 | -3.06 | [-12.1, +9.4] | -0.000 | +0.001 | [-0.050, +0.078] |
| NY_AM M1 | -3.35 | -3.13 | [-10.9, +7.6] | +0.004 | -0.014 | [-0.089, +0.034] |
| NY_AM M2 | -18.86 | -0.80 | [-15.0, +12.5] | -0.063 | +0.013 | [-0.069, +0.124] |
| NY_AM M3 | +5.94 | +2.48 | [-12.5, +17.4] | +0.011 | -0.035 | [-0.072, +0.003] |
| NY_PRE M1 | +3.39 | +2.75 | [-7.2, +14.7] | -0.010 | +0.020 | [-0.040, +0.085] |
| NY_PRE M2 | -9.70 | -0.46 | [-13.2, +8.7] | -0.166 | -0.027 | [-0.099, +0.029] |
| NY_PRE M3 | -1.66 | -2.99 | [-20.0, +15.7] | +0.018 | -0.019 | [-0.110, +0.051] |

Every real value in this table already falls inside its own null10 range.

### 5b. `n_perm=200` (resolution confirm — decisions made here)

| cell | real ΔP(3R) | null200 95% | p (two-sided) | real spearman | null200 95% | p |
|---|---:|---|---:|---:|---|---:|
| LONDON M1 | +1.65 | [-10.9, +9.9] | 0.760 | +0.010 | [-0.080, +0.084] | 0.800 |
| LONDON M2 | -14.68 | [-15.3, +16.4] | 0.090 | -0.092 | [-0.104, +0.099] | 0.095 |
| LONDON M3 | -9.18 | [-14.0, +13.7] | 0.220 | -0.000 | [-0.096, +0.102] | 1.000 |
| NY_AM M1 | -3.35 | [-15.9, +13.2] | 0.730 | +0.004 | [-0.093, +0.083] | 0.960 |
| NY_AM M2 | **-18.86** | [-18.8, +16.6] | **0.035** | -0.063 | [-0.104, +0.125] | 0.290 |
| NY_AM M3 | +5.94 | [-18.8, +19.8] | 0.565 | +0.011 | [-0.133, +0.151] | 0.880 |
| NY_PRE M1 | +3.39 | [-14.1, +12.5] | 0.660 | -0.010 | [-0.091, +0.097] | 0.850 |
| NY_PRE M2 | -9.70 | [-14.7, +17.3] | 0.250 | **-0.166** | [-0.102, +0.130] | **0.015** |
| NY_PRE M3 | -1.66 | [-18.2, +17.7] | 0.900 | +0.018 | [-0.118, +0.125] | 0.750 |

Two cells clear the 200-permutation null: NY_AM M2's ΔP(3R) (p=0.035) and
NY_PRE M2's spearman (p=0.015) — with 18 tests run at α=0.05 here, ~1 false
positive is the expectation under pure noise, so two borderline hits, both
in the M2/continuation family and both pointing the **same, wrong**
direction (more conviction → shorter run), read as a soft, directionally-
consistent hint at most — not as two independent confirmations. Neither
would survive a Bonferroni-style correction for 18 comparisons (needed
p<0.0028). Both cells' companion metric (spearman for NY_AM M2, ΔP(3R) for
NY_PRE M2) sits comfortably inside its null.

### 5c. Aggregate headline (all 9 cells pooled into one statistic)

Mean HIGH-LOW contrast in P(reach 3R) across the 9 cells:
**real = -5.16 points**; null10 mean -1.26 (range [-5.41, +2.34]); null200
mean +0.22, 95% [-5.43, +5.58], **p = 0.075**. Inside the null.
`cc_all_clean` (flow+depth, robustness check, not separately calibrated):
same-direction mean contrast **-2.38 points** — consistent sign, smaller
magnitude, same conclusion.

**Verdict for §5: no calibrated, positive conviction→run effect anywhere.
The only things that even approach the null's edge run backwards, are
directionally concentrated in a single mechanism (M2), and do not survive
multiple-comparison correction.**

---

## 6. DIVERGENCE AND RUN LENGTH (per mechanism, sign stated, not assumed)

`dvg_5m` is **100% missing** (0/3,153) — dropped; `div_5m` (boolean) used
for the 5-minute window instead. `dvg_15m`/`dvg_30m` are signed, oriented
so positive favours the trade. Null = `permute_div` (divergence block
shuffled within each session×mech cell, run outcome untouched), n_perm=200.

Hypothesis stated in the brief: divergence should help REVERSAL (M1) and
hurt CONTINUATION (M2/M3). Result contradicts neither direction because
there is no effect to have a sign of:

| mech | n | spearman(dvg_15m, mfe) | null95 | p | spearman(dvg_30m, mfe) | null95 | p | div_5m: mean mfe(yes)-mean(no) | null95 | p |
|---|---:|---:|---|---:|---:|---|---:|---:|---|---:|
| M1 (reversal — expect +) | 1,541 | +0.022 | [-0.049,+0.050] | 0.355 | -0.001 | [-0.054,+0.051] | 0.980 | +0.56 | [-0.82,+1.21] | 0.31 |
| M2 (continuation — expect -) | 786 | +0.018 | [-0.071,+0.059] | 0.630 | +0.034 | [-0.078,+0.074] | 0.390 | +0.49 | [-0.93,+0.92] | 0.28 |
| M3 (continuation — expect -) | 826 | +0.004 | [-0.065,+0.065] | 0.935 | -0.002 | [-0.070,+0.068] | 0.965 | +0.10 | [-1.17,+1.26] | 0.87 |

All nine mechanism-level tests are inside their null (p 0.28-0.98). Signs
are all weakly *positive* for M2/M3 — opposite the "divergence hurts
continuation" hypothesis, but the magnitudes (spearman 0.003-0.034) are
indistinguishable from zero, so this is not a reversed effect, it is no
effect. Per-cell (session×mechanism, 9×3 tests, not tabulated for space,
see `run_divergence.py` output) shows the same picture with one marginal
exception, NY_PRE M1 `div_5m` (p=0.035) — a single hit among 27 divergence
tests, expected by chance alone. **Divergence at entry does not predict
run length in any mechanism on this population.**

---

## 7. TIME STRUCTURE — `mins_to_peak`

Whole book: median **3 minutes**, p75 = 16, p90 = 95, mean = 39 (heavy
right tail — a handful of very slow grinders pull the mean far past the
median). By mechanism: M1 median 3 min, M2 and M3 median 2 min. Cumulative:
43% of runs peak within 1 minute, 54% within 3, 60% within 5, 74% within
15, 81% within 30. For the median trade, `exc_5m_r` already equals
`run_mfe_r` (ratio 1.00) — the entire favourable excursion the trade will
ever see typically arrives inside the first five minutes; the mean ratio
(0.75) is lower only because the right-tail slow-grinders drag it down.
`mins_to_peak` is essentially flat across conviction tiers (median 2/3/3
for LOW/MID/HIGH, p90 90/90/106) — conviction does not buy more time
either.

**What this implies:** any exit slower than a few minutes to react is
racing a peak that, for the median trade, has often already passed.
Every EV number scored against a target that resolves at a median 9 bars
(this book's structural exits) is not "closing early" relative to the raw
move so much as arriving close to when the move itself typically already
finished — the more consequential mismatch flagged in the brief is real
(p90 mfe reaches 7.66R against a 0.5R median close), but it is a mismatch
about the **tail**, not the **typical** trade, and it does not change the
conviction verdict either way: conviction fails to predict run length
whether run length is measured at 3 minutes or at the full walk-out.

---

## 8. DOES CONVICTION PREDICT RUN? — plain answer

**No, not on this population, under any of the tests run.** Per session ×
mechanism (never pooled): none of the 9 cells shows a P(reach 3R) or
run-distance ordering that rises with `cc_flow_clean` and survives the
run-block permutation null. The two nominally sub-0.05 hits (NY_AM M2's
ΔP(3R), NY_PRE M2's spearman) are both in the M2 family, both run
backwards (high conviction → shorter run, not longer), and neither
survives correction for the 18 tests performed — treat both as noise the
calibration correctly let through at its stated ~5% rate (consistent with
BR-97's finding that this machinery passes ~5% of pure noise), not as
discoveries. The aggregate 9-cell contrast (-5.16 points) is inside its
null (p=0.075). Divergence at entry — tested per mechanism with the
hypothesized reversal/continuation sign stated in advance — shows no
effect in either direction, in any mechanism. This is a clean, exit-agnostic
null: it cannot be attributed to the truncated-target problem that
motivated this test, because `race_runs.parquet` walks with no structural
target at all. Run distance is not predictable from this conviction
construct. `mins_to_peak`'s 3-minute median additionally constrains how
much even a correctly-timed exit could ever have captured, on top of that.
