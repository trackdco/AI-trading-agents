# NY_PRE Sweep — Winner/Loser Separation

Session scope: **NY_PRE only** (08:00–09:29 NY). Sessions never pooled with
LONDON/NY_AM. Mechanisms M1/M2/M3 never pooled with each other. Directions
pooled within a mechanism only where stated. Tests run with the shared
`scripts/sweep_lib.py` module (`test_split`, `quintiles`, `cells`,
`predictors`) exactly as declared in `docs/DECLARATIONS-agent-sweep.md`; no
statistics reimplemented. Standing: fit-only, no holdout, report-only,
**nothing adopted**.

## SCOPE AND COUNTS

- Cells (session × mechanism [× direction], ≥40 fights): **9** —
  `NY_PRE/M1`, `M1/long`, `M1/short`, `M2`, `M2/long`, `M2/short`, `M3`,
  `M3/long`, `M3/short`.
- Predictors: `predictors(B)` returns **99** base columns. Three
  NY_PRE-relevant categoricals the task flagged (`daytype`,
  `value_position`, `open_vs_value`) are strings and are not in that
  numeric/boolean set, so they were exploded into **11 one-hot boolean
  columns** (`daytype_balanced/imbalanced/unknown`,
  `valpos_below/inside/above/overlap_dn/overlap_up`,
  `ovv_above_value/in_value/below_value`) and added to the frame before
  calling `predictors(B)` again — this is "deriving further columns from
  those present," which the declaration permits. That yields 110 columns.
  **One column, `out_pts`, was then dropped**: it is `out × risk`, added by
  `load_wide()` itself as the T3 points-control target, not an independent
  predictor — testing it against `out` is tautological (median-split on
  `out_pts` reproduces `out`'s sign almost exactly) and it "survived" in
  literally all 9 cells with the largest effect size in the sweep before
  being caught and removed. Final predictor count: **109**.
- **Total tests run: 9 cells × 109 predictors = 981**, one above-median (or
  boolean) split per predictor per cell, all five declared tests per
  split.
- **False-positive budget: 981 × 0.05 ≈ 49 spurious clears expected at
  95%, by construction, before any of the other four tests are applied.**
- **Observed: 57 splits clear the day-clustered CI (test 1) alone; 37
  splits survive all five tests.** 37 < 49 — the full-survivor count sits
  *under* the naive FP budget, which is the expected outcome under the
  prior that most of this sweep is noise. (57 > 49 at the CI-only stage is
  not a contradiction: many of the 109 columns are re-encodings of a
  handful of underlying quantities — see below — so CI-clears are not 109
  independent draws per cell.)
- 9 clears were killed by the Law-2 mechanical filter (`risk`, `w15`,
  `w15_pts`, `entry`, `stop`, `ma15`, `volx`, `risk_over_w`,
  `risk_over_atr30` — either declared-mechanical or ρ(var, risk) > 0.4),
  11 by split-half disagreement or thinness.
- **Collinearity check on the 37 survivors**: within each cell, survivor
  variables were clustered by |correlation| ≥ 0.6. The 37 raw survivors
  collapse to **23 independent clusters** — e.g. in `NY_PRE/M2`,
  `disp_w`, `px_vs_ma15_w`, `px_vs_poc_w`, `dist_day_high_w` and `is_long`
  all cluster together (|r| 0.57–0.89): they are largely the same signal
  (position/direction), not five independent discoveries. This matters
  for reading the "37" honestly — it is not 37 independent bets against a
  49-bet budget, it is closer to 23.

## SURVIVORS

37 raw survivors / 23 independent clusters. None were pre-registered
thresholds beyond the declared above-median (or boolean) split; alternate
thresholds tried on the most promising ones are reported separately below
and labeled **SEARCHED**. All effect sizes are `out` (R) differences
unless noted; `d_pts` is the points-control difference (same sign
required to clear).

Grouped by cell, one row per surviving variable. "Half a / Half b" are the
frozen split-half effects (both must share sign with the full effect and
be ≥1/3 its magnitude to survive). ρ = correlation with `risk` (all <0.4,
required). Quintile shape from `quintiles(g, var)`.

### NY_PRE/M1 (pooled, n=438)
| var | dev | 95% CI | d_pts | ρ | half a / b | shape |
|---|---|---|---|---|---|---|
| `aff_val` | −0.61 | [−1.04, −0.08] | −13.3 | 0.11 | −0.71 / −0.59 | non-monotone (n_a=40, thin arm) |
| `ma15_slope5_w` | +0.41 | [0.04, 0.81] | +5.0 | −0.09 | +0.40 / +0.45 | near-monotone but on a near-zero scale (Q values 0.01→0.00→0.01) |

### NY_PRE/M1/long (n=193)
| var | dev | 95% CI | d_pts | ρ | half a / b | shape |
|---|---|---|---|---|---|---|
| `aff_val` | −0.93 | [−1.29, −0.48] | −17.0 | 0.10 | −0.95 / −1.02 | non-monotone (n_a=28, thin) |
| `eff_result` | +0.56 | [0.03, 1.10] | +7.2 | −0.17 | +0.24 / +0.79 | near-monotone (U-shaped tail); weakest half is only 43% of full effect |

### NY_PRE/M1/short (n=245)
| var | dev | 95% CI | d_pts | ρ | half a / b | shape |
|---|---|---|---|---|---|---|
| `dist_day_low_w` | −0.67 | [−1.30, −0.08] | −7.8 | 0.04 | −0.44 / −0.95 | non-monotone |
| `room_ahead_day_w` | −0.67 | [−1.30, −0.08] | −7.8 | 0.04 | −0.44 / −0.95 | **numerically identical to `dist_day_low_w`** — same column in this direction subset (r=1.00) |
| `px_vs_on_lo_w` | −0.60 | [−1.24, −0.03] | −7.5 | 0.02 | −0.46 / −0.76 | non-monotone; r=0.98 with the pair above — same cluster |
| `bar_body_frac` | +0.57 | [0.005, 1.16] | +4.7 | 0.16 | +0.73 / +0.49 | non-monotone, CI nearly touches zero |
| `aff_vwap_p1` | −0.67 | [−1.22, −0.11] | −8.1 | −0.07 | −0.55 / −0.85 | non-monotone (n_a=62) |

**Note**: in NY_PRE (before the 09:30 RTH open), "distance to the day's
low so far" and "distance to the overnight low" are nearly the same
quantity (r=0.98) — this is the overnight-context signal the task asked
about, but it clears in only one of nine cells (M1/short) and is
non-monotone across quintiles.

### NY_PRE/M2 (pooled, n=243)
| var | dev | 95% CI | d_pts | ρ | half a / b | shape |
|---|---|---|---|---|---|---|
| `disp_w` | −0.51 | [−0.99, −0.03] | −6.8 | −0.12 | −0.49 / −0.46 | non-monotone |
| `dist_day_high_w` | +0.77 | [0.30, 1.30] | +8.2 | −0.03 | +0.75 / +0.74 | non-monotone |
| `px_vs_poc_w` | −0.51 | [−0.97, −0.05] | −6.4 | 0.07 | −0.35 / −0.54 | non-monotone |
| `px_vs_ma15_w` | −0.61 | [−1.09, −0.15] | −6.9 | 0.14 | −0.79 / −0.44 | non-monotone |
| `is_long` | −0.69 | [−1.25, −0.17] | −8.8 | 0.01 | −0.72 / −0.64 | non-monotone — **this is the direction variable itself** |
| `aff_vwap_m1` | −0.54 | [−0.96, −0.15] | −10.0 | −0.04 | −0.75 / −0.42 | near-monotone (n_a=23, thin) |
| `london_out_today` | +0.55 | [0.06, 1.08] | +5.3 | −0.09 | +0.63 / +0.49 | non-monotone, one quintile (Q3) breaks sign |
| `valpos_below` (derived) | −0.53 | [−0.97, −0.15] | −9.1 | −0.02 | −0.63 / −0.46 | near-monotone (n_a=33, thin) |

**Collinearity**: `disp_w`, `px_vs_ma15_w`, `px_vs_poc_w`, `dist_day_high_w`
and `is_long` cluster together (|r| 0.57–0.89 pairwise, driven mostly by
`is_long`). This is **one finding wearing five names**: in the pooled M2
cell, direction (long vs. short) and its price-displacement correlates
recover the already-known M2 direction split (near_out EV −0.387 long vs
+0.302 short, BR-86/90) — it is not new information.

### NY_PRE/M2/long (n=144) — see THE M2-LONG PROBLEM below
| var | dev | 95% CI | d_pts | ρ | half a / b | shape |
|---|---|---|---|---|---|---|
| `atr30_over_w` | +0.52 | [0.13, 0.89] | +6.8 | 0.16 | +0.58 / +0.39 | **monotone** (Q1 0.07 → Q5 0.10) |
| `eff_result` | −0.55 | [−1.11, −0.04] | −8.3 | −0.11 | −0.70 / −0.44 | near-monotone (U-shaped) |
| `on_range_w` | +0.49 | [0.11, 0.89] | +4.5 | −0.06 | +0.54 / +0.39 | non-monotone |
| `struct_spread_w` | +0.49 | [0.12, 0.88] | +2.7 | 0.04 | +0.53 / +0.45 | non-monotone |
| `n_ahead_within_2r` | +0.52 | [0.15, 0.86] | +7.3 | 0.17 | +0.29 / +0.68 | near-monotone (n_a=24, thin) |

### NY_PRE/M2/short (n=99)
| var | dev | 95% CI | d_pts | ρ | half a / b | shape |
|---|---|---|---|---|---|---|
| `aff_vwap_m1` | −1.23 | [−1.94, −0.58] | −21.3 | −0.003 | −1.20 / −1.19 | non-monotone (n_a=14, very thin) |

### NY_PRE/M3 (pooled, n=244)
| var | dev | 95% CI | d_pts | ρ | half a / b | shape |
|---|---|---|---|---|---|---|
| `disp_abs_w` | −0.55 | [−0.92, −0.16] | −5.4 | −0.08 | −0.21 / −0.81 | near-monotone; halves differ 3.8× in magnitude (both still ≥1/3) |
| `dist_day_low_w` | −0.41 | [−0.81, −0.01] | −3.9 | −0.15 | −0.75 / −0.15 | non-monotone, CI nearly touches zero |
| `epi_max_w` | −0.54 | [−0.93, −0.13] | −6.1 | 0.16 | −0.56 / −0.55 | non-monotone |
| `epi_max_w_r` | −0.54 | [−0.93, −0.13] | −6.1 | 0.16 | −0.56 / −0.55 | identical to `epi_max_w` (r=1.00) |
| `ma15_ahead_r` | +0.39 | [0.03, 0.75] | +5.2 | 0.27 | +0.20 / +0.53 | near-monotone |
| `trend_align` | +0.43 | [0.01, 0.88] | +4.8 | 0.02 | +0.23 / +0.59 | non-monotone, CI nearly touches zero |

`epi_max_w`/`disp_abs_w`/`ma15_ahead_r` cluster together (|r| 0.44–0.67):
one displacement/episode-depth signal, not three.

### NY_PRE/M3/long (n=135)
| var | dev | 95% CI | d_pts | ρ | half a / b | shape |
|---|---|---|---|---|---|---|
| `disp_abs_w` | −0.90 | [−1.39, −0.39] | −12.8 | −0.15 | −0.56 / −1.13 | **monotone** (Q1 0.29 → Q5 0.19) |
| `disp_w` | −0.94 | [−1.42, −0.43] | −13.1 | −0.17 | −0.65 / −1.13 | non-monotone; r=0.86 with `disp_abs_w` |
| `epi_max_w` | −0.72 | [−1.20, −0.22] | −9.3 | 0.01 | −0.84 / −0.61 | near-monotone |
| `epi_max_w_r` | −0.72 | [−1.20, −0.22] | −9.3 | 0.01 | −0.84 / −0.61 | identical to `epi_max_w` |
| `ma15_ahead_r` | +0.70 | [0.23, 1.15] | +8.0 | 0.27 | +0.92 / +0.49 | near-monotone |
| `nearest_behind_r` | −0.70 | [−1.23, −0.19] | −5.4 | −0.30 | −0.96 / −0.53 | non-monotone (monotone decreasing until Q5 upticks) |

### NY_PRE/M3/short (n=109)
| var | dev | 95% CI | d_pts | ρ | half a / b | shape |
|---|---|---|---|---|---|---|
| `cvd_slope30` | −0.64 | [−1.19, −0.10] | −6.2 | −0.15 | −0.99 / −0.37 | non-monotone (Q3, Q5 flip sign) |
| `inventory_pts` | −0.63 | [−1.22, −0.02] | −5.4 | −0.01 | −0.94 / −0.34 | non-monotone (Q3 dips hardest, not an edge quintile) |

### Reading across the 37: quintile shape is weak evidence overall
Of 37 survivors, only **2** show a clean monotone quintile progression
(`atr30_over_w` in M2/long, `disp_abs_w` in M3/long); another ~15 are
"near-monotone" (one sign flip, usually at an interior quintile — the
signature of a single-bucket artifact rather than a dose-response); the
rest (~20) are non-monotone, several with the effect concentrated in one
quintile while the other four are flat or noisy. This is the single most
important qualifier on the survivor list: **passing all five declared
tests does not imply a clean dose-response relationship**, and most of
these do not have one.

### SEARCHED: alternate thresholds on the 10 most promising splits
Per the declaration, a threshold chosen by search is a fit artifact even
when it survives split-half, and is labeled as such. Ten variable/cell
pairs were re-tested with `mask=` at top/bottom tercile and top/bottom
quartile (median result shown for reference):

| cell / var | median split | tercile (33/67) | quartile (25/75) | verdict |
|---|---|---|---|---|
| M2/long `atr30_over_w` | dev +0.52, survives | dev +0.66, survives | dev +0.79, survives | **robust, strengthens** — SEARCHED |
| M2/long `on_range_w` | dev +0.49, survives | dev +0.41, CI spans 0 | dev +0.54, CI spans 0 | **fragile** — median-only artifact — SEARCHED |
| M2/long `struct_spread_w` | dev +0.49, survives | dev +0.25, CI spans 0 | dev +0.23, CI spans 0 | **fragile** — SEARCHED |
| M2/long `eff_result` | dev −0.55, survives | dev −0.56, survives | dev −0.59, survives | **robust** — SEARCHED |
| M3/long `disp_abs_w` | dev −0.90, survives | dev −1.23, survives | dev −1.43, survives | **robust, strengthens** — SEARCHED |
| M3 `ma15_ahead_r` | dev +0.39, survives | dev +0.17, CI spans 0 | dev +0.30, CI spans 0 | **fragile** — SEARCHED |
| M3/long `ma15_ahead_r` | dev +0.70, survives | dev +0.72, survives | dev +0.66, CI spans 0 | **borderline fragile** — SEARCHED |
| M1/short `dist_day_low_w` | dev −0.67, survives | dev −0.67, survives | dev −0.47, CI spans 0 | **borderline fragile** — SEARCHED |
| M1/short `px_vs_on_lo_w` | dev −0.60, survives | dev −0.53, CI spans 0 | dev −0.88, survives | **inconsistent across thresholds** — SEARCHED |
| M3/short `inventory_pts` | dev −0.63, survives | dev −0.79, CI spans 0 | dev −0.37, CI spans 0 | **fragile** — SEARCHED |

**7 of 10 fail to reproduce under at least one alternate threshold.** Only
`atr30_over_w` (M2/long), `eff_result` (M2/long), and `disp_abs_w`
(M3/long) hold up — and even those are fit-only, same-data-searched, and
not adopted. This threshold-fragility, on top of the weak quintile shapes
above, is the strongest reason to treat the 37/23-cluster survivor count
as mostly noise rather than mostly signal.

## CLEARS THAT DID NOT SURVIVE (20 splits)

| cell | var | dev | 95% CI | killing test |
|---|---|---|---|---|
| M1/long | `aff_vah` | +1.49 | [0.29, 2.88] | half too thin |
| M1/long | `valpos_overlap_dn` | −0.85 | [−1.27, −0.19] | half too thin |
| M1/long | `volx` | +0.58 | [0.06, 1.08] | LAW2 mechanical (ρ=0.50) |
| M1/short | `entry` | +0.61 | [0.00, 1.27] | LAW2 mechanical |
| M1/short | `ma15` | +0.64 | [0.04, 1.31] | LAW2 mechanical |
| M1/short | `stop` | +0.63 | [0.02, 1.31] | LAW2 mechanical |
| M1/short | `pos_in_day_range` | −0.81 | [−1.47, −0.21] | half <1/3 the effect |
| M1/short | `pos_in_range_dir` | +0.83 | [0.22, 1.48] | half <1/3 the effect |
| M2/long | `bar_range_w` | +0.46 | [0.06, 0.87] | half <1/3 the effect |
| M2/long | `px_vs_on_hi_w` | −0.51 | [−0.90, −0.14] | half <1/3 the effect |
| M2/long | `risk_over_w` | +0.52 | [0.12, 0.93] | LAW2 mechanical (ρ=0.76) |
| M2/short | `n_tie` | +2.39 | [0.01, 4.98] | halves disagree in sign |
| M2/short | `valpos_below` | −1.23 | [−1.89, −0.63] | half too thin |
| M3 | `disp_w` | −0.41 | [−0.80, −0.003] | half <1/3 the effect |
| M3 | `risk` | +0.53 | [0.13, 0.96] | LAW2 mechanical (declared, ρ=1.00) |
| M3/long | `risk_over_atr30` | +0.59 | [0.06, 1.09] | LAW2 mechanical (ρ=0.85) |
| M3/short | `aff_val` | −0.66 | [−1.18, −0.08] | half too thin |
| M3/short | `n_tie` | −0.86 | [−1.34, −0.27] | half too thin |
| M3/short | `w15` | +0.65 | [0.05, 1.24] | LAW2 mechanical (declared) |
| M3/short | `w15_pts` | +0.65 | [0.05, 1.24] | LAW2 mechanical (declared) |

## THE M2-LONG PROBLEM

`NY_PRE/M2/long` (n=144) has EV(`near_out`) = **−0.387R**, EV(`far_out`) =
**−0.722R** — confirmed against BR-86/90 (matches exactly). This is the
worst cell in the family. Five variables survive all five tests in this
cell: `atr30_over_w`, `eff_result`, `on_range_w`, `struct_spread_w`,
`n_ahead_within_2r` (4 independent clusters after collapsing
`on_range_w`/`struct_spread_w`, which correlate 0.73).

**Does any of them rescue the cell? No — the "good" arm is still a
loser, and for the two most NY_PRE-relevant variables the apparent rescue
inverts on the deeper outcome:**

| var | "good" arm `near_out` | "bad" arm `near_out` | "good" arm `far_out` | "bad" arm `far_out` |
|---|---|---|---|---|
| `atr30_over_w` (high vol) | −0.136 | −0.655 | **−0.834** | −0.571 |
| `on_range_w` (wide overnight range) | −0.160 | −0.653 | **−0.833** | −0.539 |
| `struct_spread_w` (wide) | −0.146 | −0.637 | **−0.792** | −0.553 |
| `eff_result` (low) | −0.094 | −0.648 | −0.835 | −0.741 |
| `n_ahead_within_2r` (≥1 struct within 2R, n=24) | **+0.039** | −0.486 | **−0.017** | −0.949 |

For the three volatility/range-cluster variables — including `on_range_w`,
the overnight-range variable the task specifically asked about — the
subset that looks "better" on the near-structure outcome is *worse* on
the far-structure outcome (near_out improves by ~0.5R while far_out
worsens by ~0.26–0.28R). The most parsimonious read is that wider
overnight range/volatility puts a nearer structure in the way, giving an
earlier (less bad) exit on the near metric, while the underlying adverse
excursion is if anything larger — not a real quality difference in the
trade, an accounting artifact of where structures happen to sit that
day. This is exactly the "population nets zero, timing lever was
accounting" pattern the declaration already found once (BR-96) recurring
here.

The one exception, `n_ahead_within_2r`, is directionally consistent on
*both* near (+0.039 vs −0.486) and far (−0.017 vs −0.949) — the closest
thing to a real "less bad" subset found anywhere in NY_PRE/M2/long. But
its "good" arm is **24 trades**, its quintile shape is only
near-monotone, it was not tried at alternate thresholds, and its own
effect on `near_out` alone is still a loss (+0.039, i.e. roughly
breakeven at best, not profitable). It does not rescue the cell; it
identifies a small, underpowered corner that is merely not-catastrophic
rather than good.

**Honest answer: nothing in this sweep rescues M2-long.** Every surviving
split's better arm remains net-negative EV in R, and the two variables
most on-theme for NY_PRE (`on_range_w`, and by extension the
volatility-regime family) actively point the wrong way once the deeper
(`far_out`) outcome is checked. The family's worst cell stays the
family's worst cell.

## PATTERNS ACROSS CELLS

Cross-mechanism sign repetition (same variable clearing in ≥2 *different*
mechanisms, not just a pooled cell and its own long/short subset):

- **`aff_val` (affirms the VAL structure at trigger): negative in M1
  (pooled), M1/long, and M3/short.** Three cells, two different
  mechanisms (M1 and M3), same sign. This is the closest thing to a
  cross-mechanism pattern in the sweep — but all three arms are thin
  (n_a = 40, 28, and the M3/short instance clears but doesn't survive),
  and the quintile shape is non-monotone in both survivors.
- **`disp_w` (signed displacement at trigger): negative in M2 (pooled),
  M3 (pooled), and M3/long.** Two mechanisms (M2, M3), consistent sign.
  Partly the same underlying displacement signal picked up by
  `disp_abs_w`/`epi_max_w` inside M3.
- **`eff_result` flips sign across mechanisms**: positive in M1/long
  (higher eff_result → better) but negative in M2/long (higher
  eff_result → worse). Not a stable pattern — same variable name, opposite
  relationship to outcome in different mechanisms.
- **`n_tie` flips sign**: positive-clearing in M2/short, negative-clearing
  in M3/short (neither survives).
- Within a single mechanism, subset consistency (e.g. `valpos_below` and
  `aff_vwap_m1` clearing in both `M2` and `M2/short`) is expected by
  construction (`M2/short ⊂ M2`) and is not independent evidence.

No variable clears with consistent sign across all three mechanisms.
Two variables (`aff_val`, `disp_w`) clear with consistent sign across two
of three mechanisms, both on thin/partial evidence. This is weak, and is
reported as weak.

## WHAT NY_PRE SAYS

- 981 tests run, 981 × 0.05 ≈ **49 expected false positives**. Observed
  **37 full survivors (23 independent clusters after collapsing
  same-cell |r|≥0.6 groups)** — under the naive budget even before
  collapsing.
- Of those 37/23, only 2 have a clean monotone quintile shape; roughly
  half are near-monotone with the effect concentrated in one interior
  quintile (the single-bucket-artifact signature); the rest are flat or
  noisy across quintiles despite passing the CI/half/points/rho tests.
- Of the 10 most promising splits pressure-tested at alternate
  (tercile/quartile) thresholds, **7 failed to reproduce** at at least one
  alternate cut. Only `atr30_over_w` (M2/long), `eff_result` (M2/long)
  and `disp_abs_w` (M3/long) held up under all three thresholds tried —
  and per the declaration these remain SEARCHED, fit-only, not adopted.
- The NY_PRE-specific variables the task flagged were mostly null:
  `daytype` (0/9 cells clear, any level), `open_vs_value` (0/9),
  `overlap` (0/9), `rv30_over_rv120` (0/9), `vol30_over_vol240` (0/9),
  `bar_vol_over_30` (0/9). `on_range_w`, `px_vs_on_hi_w`,
  `px_vs_on_lo_w`, `value_position`(`below`), and `inventory_pts` each
  clear in exactly **one** of nine cells — no NY_PRE-wide overnight-context
  signal, only isolated single-cell splits, and for the one case that
  bears directly on the family's worst cell (`on_range_w` in M2/long) the
  apparent improvement inverts on the deeper (`far_out`) outcome.
- **The M2-long problem is not solved.** Every surviving split's better
  arm is still net-negative in R; the overnight-range/volatility variables
  most relevant to NY_PRE point the wrong way once checked against the
  far outcome. The one variable with a consistent-direction hint on both
  near and far (`n_ahead_within_2r`) has a 24-trade "good" arm and is
  merely less-bad, not good.
- Net read: **NY_PRE adds one methodological finding (`out_pts` must be
  excluded as a tautological predictor, not just a T3 control column) and
  no adopted separator.** The handful of clusters that survive all five
  tests are thin, mostly non-monotone, and mostly fail alternate
  thresholds — consistent with the declared prior that most or all of
  this sweep returns nothing. Nothing here is adopted; nothing here
  rescues the family's worst cell.
