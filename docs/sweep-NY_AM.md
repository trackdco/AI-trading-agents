# NY_AM SESSION SWEEP — winner/loser separation, all variables

Scope: **NY_AM only** (09:30–10:30 NY, cash open). Per
`docs/DECLARATIONS-agent-sweep.md`: fit-only, no holdout, report-only,
nothing adopted. All five declared tests run via the shared
`scripts/sweep_lib.py` (`test_split`, `quintiles`, `cells`,
`predictors`) — no statistics reimplemented. Sessions and mechanisms
are never pooled; direction splits (long/short) are reported as
separate cells, as the library does natively.

Cells (9): `NY_AM/M1` (n=486, 226 days), `M1/long` (253, 117d),
`M1/short` (233, 129d), `M2` (263, 116d), `M2/long` (127, 60d),
`M2/short` (136, 58d), `M3` (248, 128d), `M3/long` (126, 68d),
`M3/short` (122, 67d).

**Methodology note (predictor-list correction):** `predictors(B)`
initially returned 99 columns, one of which — `out_pts` — is
`out × risk`, computed in `load_wide()` itself. It is outcome-derived,
not a predictor, and was omitted from `sweep_lib.OUTCOME_COLS` by
oversight. Splitting on `out_pts` against `out` is close to
self-prediction and "survived" all five tests tautologically in every
cell it was tested in (not a market finding). This was caught during
this sweep and independently confirmed by the coordinator; `out_pts`
has since been added to `OUTCOME_COLS` in `scripts/sweep_lib.py`, and
`predictors(B)` now correctly returns 98 columns. Every count and
table below already excludes `out_pts` throughout.

## SCOPE AND COUNTS

- Tests run (median/boolean split, 9 cells × 98 predictors): **882**
- Clear the day-clustered CI (test 1 only): **58**
- Survive all five declared tests: **42**
- Clear but fail one of tests 2–5 ("clears, does not survive"): **16**

**False-positive budget (mandatory framing):** 882 tests × 0.05 =
**44.1 expected spurious CI-clears** under a pure null, at test 1
alone. Observed CI-clears: 58 — about **1.3× the test-1 budget**,
a mild excess, not dramatic on its own.

The number that needs explaining is not 58, it's **42 full survivors**.
Under a true null, the compound filter (CI clears AND both day-halves
agree in sign at ≥1/3 magnitude AND points-control agrees in sign AND
not mechanically coupled) should knock out the large majority of the
~44 test-1 false positives — sign agreement across an independent
day-split-half is roughly a coin flip, points-control agreement is
close to another coin flip, so a noise-only sweep should land in the
**single digits** of full survivors (this is exactly what BR-91 and
BR-94 found in prior passes: 9/110 and 9/160). NY_AM instead produced
42. That is real excess over the null — **but see "PATTERNS ACROSS
CELLS" below: 42 raw survivors collapse to roughly 26 by
within-cell correlation clustering (|r|>0.5), and to a much smaller
handful of underlying constructs once cross-cell replication of the
same signal is accounted for.** NY_AM is not "42 independent
discoveries." It is a session with real, repeated structure around a
few themes, expressed redundantly across correlated columns.

Additional **SEARCHED** mini-sweeps (reported separately, not folded
into the 882/44.1 budget above):
- `tmin` at 4 non-median cuts (10/15/20/30 min) × 9 cells = 36 tests,
  budget 1.8 spurious clears. Observed: 1 (see TIME-OF-SESSION).
- Alternative thresholds (tercile, quartile) on the 9 non-boolean
  variables judged most promising, ×2 schemes = 18 tests (2 of these
  are degenerate — see below). Observed: 13 survive, 3 fail, 2
  degenerate. See per-variable detail below.

## SURVIVORS

All 42 pass CI (test 1), both-halves-agree-in-sign-and-magnitude
(test 2), points-control (test 3), non-mechanical |ρ(var,risk)|<0.4
(test 4), and the power floor (test 5). None of these are threshold
searches (median or boolean split) unless explicitly marked SEARCHED.
"Shape" is the `quintiles()` pattern of the variable's own mean across
realized-R quintiles (Q1=worst outcomes … Q5=best).

### NY_AM/M1 (n=486, 226 days)

| var | dev | 95% CI | halves (a/b) | d_pts | ρ(risk) | shape |
|---|---|---|---|---|---|---|
| `aff_val` | -0.55 | [-0.90, -0.14] | -0.47 / -0.62 | -13.8 | -0.04 | step: flat Q1–3, drops Q4–5 (not monotone) |
| `aff_vwap_m1` | -0.55 | [-0.88, -0.14] | -0.77 / -0.40 | -13.3 | -0.00 | same step shape (r=0.75 with aff_val — same signal) |
| `inventory_pts` | 0.51 | [0.23, 0.79] | 0.49 / 0.52 | 12.0 | -0.16 | **U-shaped**, not monotone — high in Q1 (losers) and Q5 (winners), low mid |
| `ma15_vs_ma60_w` | 0.33 | [0.001, 0.65] | 0.21 / 0.48 | 10.0 | -0.26 | J-shaped, not monotone |

### NY_AM/M1/long (n=253, 117 days)

| var | dev | 95% CI | halves | d_pts | ρ(risk) | shape |
|---|---|---|---|---|---|---|
| `atr30_over_w` | 0.48 | [0.10, 0.87] | 0.58 / 0.40 | 11.7 | -0.06 | flat — weak shape support |
| `ma60_slope30_w` | 0.44 | [0.02, 0.87] (barely clears) | 0.30 / 0.61 | 16.5 | 0.01 | flat near zero — weak shape support |
| `n_struct_ahead` | -0.40 | [-0.82, -0.0005] (barely clears) | -0.36 / -0.44 | -6.5 | -0.05 | mostly monotone decreasing |

### NY_AM/M1/short (n=233, 129 days) — the largest survivor cluster

| var | dev | 95% CI | halves | d_pts | ρ(risk) | shape |
|---|---|---|---|---|---|---|
| `aff_val` | -0.64 | [-1.05, -0.19] | -0.39 / -0.87 | -16.2 | 0.01 | step shape, replicates M1 pooled |
| `aff_vwap_m1` | -0.66 | [-1.07, -0.21] | -0.71 / -0.67 | -16.7 | 0.08 | step shape, replicates M1 pooled |
| `conf_tightness_w` | 0.62 | [0.20, 1.02] | 0.47 / 0.85 | 13.5 | 0.08 | roughly monotone increasing |
| `inventory_pts` | 0.71 | [0.30, 1.17] | 0.31 / 1.03 (a is at the 1/3 floor) | 17.7 | -0.11 | **U-shaped**, replicates M1 pooled |
| `ma15_vs_ma60_w` | 0.57 | [0.07, 1.09] | 0.54 / 0.67 | 15.2 | -0.14 | J-shaped, not monotone |
| `px_vs_poc_w` | 0.45 | [0.03, 0.87] | 0.62 / 0.30 | 13.0 | -0.10 | U-shaped |
| `px_vs_vwap_w` | 0.49 | [0.09, 0.91] | 0.43 / 0.56 | 13.7 | -0.17 | J/U-shaped |
| `seq_sess` | -0.54 | [-0.93, -0.13] | -0.40 / -0.63 | -14.8 | 0.01 | flat, drop at Q4 — not clean monotone |
| `trend_align` | -0.58 | [-0.99, -0.17] | -0.71 / -0.51 | -18.6 | 0.17 | inverted-U — peaks mid-quintile, odd shape |

Six of these nine (`aff_val`, `aff_vwap_m1`, `inventory_pts`,
`ma15_vs_ma60_w`, `px_vs_vwap_w`, `trend_align`) are mutually
correlated at |r|>0.5 within this cell — one construct expressed six
ways, not six findings.

### NY_AM/M2 (n=263, 116 days)

| var | dev | 95% CI | halves | d_pts | ρ(risk) | shape |
|---|---|---|---|---|---|---|
| `support_minus_resist` | 0.28 | [0.03, 0.55] (barely clears) | 0.18 / 0.36 | 11.3 | 0.00 | bucket at bottom (Q1 low, Q2–5 flat) |
| `thru_delta_conf` | -0.51 | [-1.23, -0.07] | -0.79 / -0.31 | -10.3 | 0.09 | roughly declining at the top quintiles |

### NY_AM/M2/long (n=127, 60 days) — thinnest cell, weakest evidence

| var | dev | 95% CI | halves | d_pts | ρ(risk) | shape |
|---|---|---|---|---|---|---|
| `dep_imbalance` | 0.40 | [0.01, 0.86] (barely clears) | 0.37 / 0.44 | 9.2 | -0.03 | flat/noisy, n=98 — no shape support |
| `eff_result` | 0.67 | [0.10, 1.44] | 0.66 / 0.68 | 19.4 | -0.18 | single spike at Q4, n=90 — outlier-driven, no monotone support |
| `support_minus_resist` | 0.40 | [0.01, 0.86] | 0.37 / 0.44 | 9.2 | 0.00 | identical to `dep_imbalance` (r=0.95 — same variable) |
| `volx` | -0.50 | [-1.09, -0.07] (barely clears) | -0.82 / -0.23 (b at the 1/3 floor) | -14.1 | 0.22 | declines only in upper half, partial shape |

### NY_AM/M2/short (n=136, 58 days)

| var | dev | 95% CI | halves | d_pts | ρ(risk) | shape |
|---|---|---|---|---|---|---|
| `nearest_ahead_r` | -0.29 | [-0.56, -0.007] (barely clears) | -0.34 / -0.24 | -9.4 | -0.26 | U-shaped |
| `thru_delta_conf` | -0.40 | [-0.71, -0.14] | -0.29 / -0.46 | -12.7 | 0.13 | roughly declining, noisy |

### NY_AM/M3 (n=248, 128 days) — richest, most coherent cluster; BR-91 cell

| var | dev | 95% CI | halves | d_pts | ρ(risk) | shape | searched robustness |
|---|---|---|---|---|---|---|---|
| `bar_range_w` | 0.31 | [0.05, 0.57] | 0.30 / 0.31 | 9.4 | 0.32 | roughly monotone increasing | — |
| `disp_abs_w` (BR-91) | -0.36 | [-0.61, -0.09] | -0.28 / -0.44 | -10.8 | -0.13 | mostly monotone decreasing/plateau | tercile & quartile both survive |
| `ma15_ahead_r` | 0.43 | [0.15, 0.69] | 0.37 / 0.52 | 13.2 | 0.34 (close to LAW2 cutoff) | strong monotone increasing then plateau | tercile survives; **quartile fails LAW2** (ρ→0.43) |
| `n_aff` (BR-91) | -0.35 | [-0.62, -0.12] | -0.51 / -0.17 (b at the 1/3 floor) | -7.0 | -0.08 | weak/flat — little shape support despite passing | tercile/quartile identical to median (coarse integer var) |
| `nearest_behind_r` | -0.28 | [-0.54, -0.04] (barely clears) | -0.39 / -0.14 (b at the 1/3 floor) | -9.3 | -0.32 (close to cutoff) | strong monotone decreasing then plateau | tercile survives; **quartile fails LAW2** (ρ→0.40) |
| `on_range_w` | 0.41 | [0.15, 0.65] | 0.32 / 0.52 | 13.2 | 0.13 | mostly monotone increasing | tercile survives; **quartile fails CI (spans zero)** |
| `slope_with_trade` | -0.46 | [-0.72, -0.21] | -0.25 / -0.73 (a at the 1/3 floor) | -9.2 | -0.09 | monotone decreasing (small magnitude, consistent) | tercile & quartile both survive |

### NY_AM/M3/long (n=126, 68 days)

| var | dev | 95% CI | halves | d_pts | ρ(risk) | shape |
|---|---|---|---|---|---|---|
| `ma15_ahead_r` | 0.56 | [0.12, 0.94] | 0.28 / 0.93 (a at the 1/3 floor) | 10.5 | 0.35 | strong monotone increasing |
| `ma15_slope30_w` / `slope_with_trade` | -0.70 | [-1.14, -0.35] | -0.66 / -0.74 | -13.7 | -0.15 | monotone decreasing (identical vars here, r=1.0) |
| `n_aff` (BR-91) | -0.53 | [-0.92, -0.20] | -0.73 / -0.31 | -9.0 | 0.03 | roughly monotone decreasing |
| `nearest_behind_r` | -0.41 | [-0.83, -0.04] (barely clears) | -0.52 / -0.25 | -12.8 | -0.30 | big Q1→Q2 drop then flat — bucket, not smooth |

### NY_AM/M3/short (n=122, 67 days)

| var | dev | 95% CI | halves | d_pts | ρ(risk) | shape |
|---|---|---|---|---|---|---|
| `day_range_w` | 0.34 | [0.03, 0.67] (barely clears) | 0.34 / 0.32 | 14.4 | 0.03 | flat/noisy — weak shape |
| `disp_abs_w` (BR-91) | -0.42 | [-0.73, -0.11] | -0.51 / -0.32 | -19.0 | -0.05 | noisy/flat — weak shape despite passing |
| `disp_w` | 0.44 | [0.12, 0.75] | 0.47 / 0.40 | 18.9 | 0.20 | mixed sign, noisy |
| `on_range_w` | 0.51 | [0.21, 0.82] | 0.62 / 0.35 | 23.8 | 0.09 | noisy dip-then-rise |
| `overlap` | -0.38 | [-0.67, -0.09] | -0.31 / -0.49 | -10.6 | -0.08 | roughly declining with noise |
| `prev15_ret_dir` | 0.36 | [0.06, 0.64] | 0.24 / 0.50 | 13.0 | 0.28 | monotone increasing in lower half, flattens |

## SEARCHED THRESHOLDS (tercile / quartile, top-vs-bottom, middle dropped)

Run on the 9 non-boolean variables judged most promising by effect
size, replication, and shape. **Labeled SEARCHED per the declaration**
— a threshold chosen or tried after seeing the outcome is a fit
artifact even when it clears every test. `aff_val`, `aff_vwap_m1`,
`trend_align` are boolean and have no alternative threshold to search.

| cell | var | tercile | quartile |
|---|---|---|---|
| M1 | `inventory_pts` | survives (dev 0.49, [0.15,0.86]) | survives (dev 0.52, [0.14,0.94]) |
| M3 | `ma15_ahead_r` | survives (dev 0.42, [0.06,0.72]) | **fails — LAW2 mechanical** (ρ=0.43) |
| M3 | `nearest_behind_r` | survives (dev -0.42, [-0.75,-0.11]) | **fails — LAW2 mechanical** (ρ=-0.40) |
| M3 | `slope_with_trade` | survives (dev -0.53, [-0.77,-0.28]) | survives (dev -0.53, [-0.81,-0.23]) |
| M3 | `n_aff` | survives (identical to median — degenerate, coarse var) | same (degenerate) |
| M3 | `disp_abs_w` | survives (dev -0.47, [-0.80,-0.10]) | survives (dev -0.47, [-0.83,-0.04]) |
| M3 | `on_range_w` | survives (dev 0.44, [0.06,0.77]) | **fails — CI spans zero** ([-0.16,0.75]) |
| M3/long | `n_aff` | survives (identical to median — degenerate) | same (degenerate) |
| M3/short | `disp_abs_w` | survives (dev -0.47, [-0.84,-0.11]) | survives (dev -0.57, [-0.94,-0.19]) |

Reading this: `disp_abs_w`, `slope_with_trade`, and `inventory_pts` are
robust across every threshold tried. `ma15_ahead_r`, `nearest_behind_r`
and `on_range_w` are **not** — at the more extreme quartile cut, the
first two cross into mechanical territory (their correlation with
`risk` rises with the tail extremity, which is itself informative:
these variables are somewhat entangled with position sizing at the
extremes even though the median split passes test 4 cleanly), and
`on_range_w`'s CI opens up and spans zero. `n_aff` is too coarse
(mostly 0/1/2/3) for tercile/quartile to be a meaningfully different
split from the median — treat its "robustness" here as not
informative, not as three independent confirmations.

## CLEARS THAT DID NOT SURVIVE

16 splits cleared the CI (test 1) and then failed a later test.

| cell | var | dev | 95% CI | killed by |
|---|---|---|---|---|
| M1/long | `entry` | 0.41 | [0.04, 0.76] | LAW2 mechanical (declared) |
| M1/long | `stop` | 0.39 | [0.01, 0.73] | LAW2 mechanical (declared) |
| M1/long | `ma15` | 0.41 | [0.03, 0.76] | LAW2 mechanical (declared) |
| M1/short | `rangex` | 0.41 | [0.02, 0.78] | LAW2 mechanical (declared) |
| M1/short | `bar_closeloc_dir` | 0.45 | [0.04, 0.88] | a half is <1/3 the effect |
| M1/short | `nearest_ahead_w` | 0.38 | [0.02, 0.76] | a half is <1/3 the effect |
| M1/short | `prev_out_day` | -0.49 | [-0.85, -0.13] | a half is <1/3 the effect |
| M2 | `entry` | 0.32 | [0.04, 0.65] | LAW2 mechanical (declared) |
| M2 | `stop` | 0.33 | [0.04, 0.65] | LAW2 mechanical (declared) |
| M2 | `ma15` | 0.32 | [0.04, 0.67] | LAW2 mechanical (declared) |
| M2/long | `n_tie` | -0.63 | [-1.24, -0.01] | half too thin (n<5 in an arm within a day-half) |
| M3 | `w15` | -0.32 | [-0.59, -0.07] | LAW2 mechanical (declared) |
| M3 | `w15_pts` | -0.32 | [-0.59, -0.07] | LAW2 mechanical (declared) |
| M3 | `risk_over_w` | 0.28 | [0.01, 0.53] | LAW2 mechanical (declared) |
| M3/long | `disp_w` | -0.49 | [-0.85, -0.06] | a half is <1/3 the effect |
| M3/short | `px_vs_on_hi_w` | -0.39 | [-0.68, -0.11] | a half is <1/3 the effect |

10 of 16 die on the declared-mechanical list (`entry`, `stop`, `ma15`,
`rangex`, `w15`, `w15_pts`, `risk_over_w` — all in `MECHANICAL` by
declaration, unsurprising and expected: entry/stop/ma15 are price
levels, they trivially separate winners from losers and say nothing
about the market). 5 die on split-half magnitude — a real-looking
full-cell effect that one day-half barely reproduces, the textbook
false-positive signature. 1 dies on thin data within a half.

## TIME-OF-SESSION STRUCTURE

`tmin` (minutes since 09:30) at the **median split** clears in
**zero** of 9 NY_AM cells — dev ranges from -0.21 to +0.20, every CI
spans zero. There is no simple "early vs late in the hour" separator
at the median.

Per the brief's specific instruction, non-median cuts were tried —
`tmin < 10`, `< 15`, `< 20`, `< 30` — in all 9 cells (36 SEARCHED
tests, budget 1.8 spurious clears). One test cleared and survived:
**`NY_AM/M3/short`, `tmin < 15`**: dev 0.42, 95% CI [0.09, 0.72],
both halves positive (0.47 / 0.37), d_pts +18.0, ρ(risk)=-0.22, n=122
(35 in the first-15-minutes arm, days=24 vs 51). This technically
passes all five tests.

It is reported here but **not treated as a real time-of-open effect**,
for three reasons stated honestly: (1) it is the *only* survivor out
of 36 searched cuts — 1/36 is inside the noise budget (1.8 expected)
for this specific mini-sweep, so it is not evidence of a broad pattern;
(2) it does **not** replicate at the adjacent cuts in the same cell —
`tmin<10` (dev 0.34, CI [-0.03, 0.73]) and `tmin<20` (dev 0.24, CI
[-0.12, 0.56]) both fail, meaning the finding is fragile to exactly
where the line is drawn, the hallmark of a threshold picked by the
data rather than a real regime boundary; (3) it appears in a single
cell (M3/short) with no counterpart in M3/long, M3 pooled, or any M1/M2
cell. **Conclusion: `tmin` shows no reliable time-of-session structure
in NY_AM at any cut tried, including the specific first-15-minutes
question the brief raised.** The cash-open minute itself is not doing
detectable work here, at least not as a standalone linear/threshold
separator of `out`. (It remains possible tmin interacts with other
variables — that is out of scope for this univariate sweep and is not
claimed.)

## THE BR-91 RE-TEST

BR-91 reported `n_aff` (count of affirming structures) and
`disp_abs_w` (absolute w-normalized displacement) **negatively**
related to outcome in NY_AM M3. Re-run under the full five-test rule:

| var | M3 pooled | M3/long | M3/short |
|---|---|---|---|
| `n_aff` | **SURVIVES**: dev -0.35, CI [-0.62,-0.12], halves -0.51/-0.17, d_pts -7.0, ρ=-0.08 | **SURVIVES**: dev -0.53, CI [-0.92,-0.20], halves -0.73/-0.31, d_pts -9.0, ρ=0.03 | does not clear CI: dev -0.20, CI [-0.53, 0.09] — same sign, not significant |
| `disp_abs_w` | **SURVIVES**: dev -0.36, CI [-0.61,-0.09], halves -0.28/-0.44, d_pts -10.8, ρ=-0.13 | does not clear CI: dev -0.42, CI [-0.79, 0.02] — same sign, borderline | **SURVIVES**: dev -0.42, CI [-0.73,-0.11], halves -0.51/-0.32, d_pts -19.0, ρ=-0.05 |

**Both hold.** `n_aff` and `disp_abs_w` both survive all five tests
in the pooled `NY_AM/M3` cell, exactly as BR-91 reported. Each also
survives independently in one of the two direction splits (`n_aff` in
`M3/long`, `disp_abs_w` in `M3/short`) and is directionally consistent
(same sign, just short of significance) in the other direction split.
Neither reverses sign anywhere in NY_AM/M3. `disp_abs_w` is also
robust to tercile and quartile re-thresholding (searched, both hold).
`n_aff` is a coarse integer variable (mostly 0–3) so tercile/quartile
collapse to the same split as the median — not an independent
confirmation, but not a contradiction either. Both are low-ρ, cleanly
non-mechanical (|ρ(risk)| ≤ 0.13 everywhere they're tested), and their
quintile shapes are weak-to-moderate (mostly flat/declining, not
sharply monotone) — the statistical result is solid; the shape
evidence is supportive but not dramatic. This is the strongest,
most-replicated finding in the NY_AM sweep, and it is a **negative**
finding for both: more affirming structures and more absolute
displacement at decision time associate with a **worse** outcome for
M3 fights in the cash-open hour, consistent with BR-91.

## PATTERNS ACROSS CELLS

- **M3 (cash-open, third-mechanism fights) is where the real
  structure lives.** 7/98, 5/98, and 6/98 predictors survive in
  M3 pooled/long/short respectively — the highest survival rate of
  any mechanism in NY_AM, and it clusters into a coherent, plausible
  story: `bar_range_w`, `disp_abs_w`, `ma15_ahead_r`, `nearest_behind_r`
  and `on_range_w` co-vary (|r| 0.4–0.6 within the cell) — one
  "displacement/structure-position" construct expressed five ways
  (bigger recent range + being farther from nearby structure +
  favorable MA15 position associate with a better outcome). `n_aff`
  and `slope_with_trade` are weakly correlated with that cluster
  (|r|<0.45) and with each other — genuinely separate signals, not
  restatements. Net: M3's 7 pooled survivors are closer to **3
  independent findings** (the displacement/position cluster, `n_aff`,
  `slope_with_trade`) than 7.
- **M1/short carries the single largest cluster of correlated
  survivors** (6 of its 9 survivors correlate at |r|>0.5): `aff_val`,
  `aff_vwap_m1`, `inventory_pts`, `ma15_vs_ma60_w`, `px_vs_vwap_w`,
  `trend_align` are one construct — roughly "trend/inventory alignment
  at decision time" — not six. `aff_val`/`aff_vwap_m1` replicate
  (same sign, same step-shaped quintile pattern) in both `M1` pooled
  and `M1/short`, which is a real cross-cell replication (M1 pooled is
  M1/short ∪ M1/long, so this is expected structure, not independent
  confirmation, but the sign and shape stability across the split is
  reassuring).
- **`inventory_pts` is the most statistically robust single survivor**
  (survives median split in both M1 and M1/short, survives tercile and
  quartile SEARCHED re-thresholds, stable |ρ(risk)|<0.2, both-halves
  agreement comfortably above the 1/3 floor) — but its quintile shape
  is **U-shaped in every cell it appears in**, not monotone. The
  "high inventory → better outcome" framing implied by an
  above-median split is not the right description; it is "extreme
  inventory in either direction associates with better outcome than
  near-zero inventory," which is a materially different (and less
  actionable) claim than a simple linear separator.
- **M2 is the weakest cell family** — only 2, 4, and 2 survivors in
  M2/pooled/long/short respectively, several barely clearing CI (lower
  bound within 0.03 of zero), one cell (`M2/long`) thin enough (n=90
  for `eff_result`) that the finding is fragile on its face, and no
  variable replicates across all three M2 splits. Different variables
  survive in each of the three M2 cells — this looks much closer to
  the noise pattern BR-91/BR-94 describe than M1 or M3 do.
- **Two "duplicate variable" pairs were caught by direction-filtering**:
  `ma15_slope30_w` and `slope_with_trade` are literally the same
  column in `M3/long` (r=1.0, because `slope_with_trade` is
  `ma15_slope30_w` signed by direction, and direction is fixed once
  you filter to `/long`); `dep_imbalance` and `support_minus_resist`
  are r=0.95 in `M2/long`. Treat each pair as one finding.
- **The mechanically-flagged clears (`entry`, `stop`, `ma15`, `rangex`,
  `w15`, `w15_pts`, `risk_over_w`) appear in exactly the cells you'd
  expect** — wherever a raw price level or a `risk`-denominated ratio
  gets tested, it clears trivially and gets correctly killed by test 4.
  This is the sweep behaving as designed, not a finding.

## WHAT NY_AM SAYS

NY_AM is not a null session the way the declaration's prior predicted
most sessions would be. **42 splits survive all five tests**, well
above what the false-positive budget and the BR-91/BR-94 precedent
would suggest for a session with no real structure — but that number
overstates the discovery count: correlation clustering collapses it to
roughly 26 within-cell, and the two mechanism families that actually
carry the weight (M3, and to a lesser extent M1/short) reduce further,
to on the order of **3–5 genuinely distinct constructs per mechanism**,
each showing up under several correlated column names.

The two headline results:

1. **BR-91 replicates cleanly.** `n_aff` and `disp_abs_w` are
   negatively related to outcome in `NY_AM/M3`, survive the full
   five-test rule in the pooled cell and in one direction split each,
   are directionally consistent (not contradicted) in the other
   direction split, and `disp_abs_w` holds under searched
   tercile/quartile re-thresholds. This is now confirmed under a
   stricter rule than the one BR-91 originally used.
2. **M3 in the cash-open hour has a coherent "displacement/structure
   position" signal** (bigger `bar_range_w`, more `disp_abs_w`-opposite
   spacing, better `ma15_ahead_r`/`nearest_behind_r` positioning →
   better outcome) that is the most internally consistent finding in
   this sweep, though several of its member variables (`ma15_ahead_r`,
   `nearest_behind_r`) sit close enough to the LAW2 mechanical boundary
   (ρ 0.32–0.35 at median, crossing 0.4 at more extreme thresholds)
   that they should be treated as borderline, not clean.

`tmin` — the variable the brief flagged as most plausible for this
specific session — **shows no reliable effect at the median, at any of
four non-median cuts tried in a 36-test searched sweep, and specifically
not at the first-15-minutes-vs-rest cut the brief asked about**: the
one nominal "survivor" found there is a single isolated result out of
36 searched tests, inside the expected noise budget, non-replicating at
adjacent cuts, and appears in only one of nine cells. The cash-open
minute itself is not a standalone separator of outcome in this data.
M2 remains the weakest of the three mechanisms in NY_AM and looks the
most like the null the declaration's prior expects. Standing:
fit-only, no holdout, report-only, nothing adopted.
