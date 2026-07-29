# CONFLUENCE STUDY — RESEARCH MEMO

To: Brake · 2026-07-29 · commit `87481e2`, pipeline sha `b249fe2e582b81a6`
Baseline: **PARTIALLY REMEDIATED (C only) + news filter. The W check and the entire `dep_*`
family remain LEAKY in the selection path.** Sample: **182 trades / 145 days**, one regime
transition. Every number below is conditional on that book.


## 1. WHAT WAS TESTED

Whether *confluence* — several order-flow reads agreeing — predicts realised R better than any
single read, conditional on a trade being taken:

- **Frozen 13-feature pool**: `cvd_5/15/30, cvd_norm_15, abs_cvd_15, delta_div_15, absorp_rel,
  vol_15_rel, vol_30_rel, gap_abs, ec_delta, ec_fp_imb, ec_aggr_flip`. The `ec_*` entrants passed
  shift and exchangeability gating; `ec_delta_hi_lo` **failed** (KS 0.264, p 0.0080), excluded
  not remedied.
- **One model family**: rank-normalised composite, weights by ridge against realised R. Penalty
  picked **inside each fold** by 3-fold CV on training trades only. No trees or interactions.
- **Walk-forward**: expanding window, daily; for day D, fit on every trade strictly before D.
  Predictions begin at 40 training trades → **142 out-of-sample predictions**.
- **Noise floor**: 2,000 day-block shuffles through the identical pipeline. Registered gate: the
  real metric must exceed the **99th percentile**, else null.
- **Three registered falsifiers**: (a) direction-blind twin of 5 unsigned magnitudes; (b) best
  single-feature baseline; (c) 500 random-weight draws.

## 2. WHAT THE NUMBERS SAY

**Real composite: Spearman rho = +0.0645** (142 predictions).

Shuffled distribution (n = 2,000): median **−0.0702**, p95 **+0.0829**, p99 **+0.1453**,
min −0.3407, max +0.2376. The real value sits at the **92.70th percentile**, empirical
**p = 0.0735**. It does not clear p95, let alone the registered p99 gate. **FAIL.**

- **(a) direction-blind — does not fire.** Blind **+0.0585** vs signed **+0.0645**: a margin of
  0.0060, far inside a null whose p95 is 0.0829. Read as "not fired", not as directional content.
- **(b) best single — FIRES.** `cvd_15` alone scores **+0.0658**, *above* the 13-feature
  composite. Confluence adds nothing. Singles range 0.0092 (`ec_delta`) to 0.0658 (`cvd_15`).
- **(c) random weights — FIRES.** 500 draws: median +0.0046, **p95 +0.1374**, max +0.2728; the
  fitted composite sits at the **74.6th percentile** of randomly weighted composites.

**VERDICT: NULL.** 15 model specifications were examined (1 composite + 1 blind twin + 13
singles); the 6-value penalty grid is inside-fold fitting, not a study-level search; shuffles and
random draws are nulls, not configurations.

## 3. WHAT IS NOW RULED OUT

Permanently, on this book and this sample:

1. **Order-flow confluence as an entry-conviction signal is dead here.** It failed three ways at
   once: below its noise floor, beaten by its best component, inside the random-weight
   distribution. A composite that cannot beat random weights has no weight structure to find.
2. **No rescue by model family.** Ridge was the only registered family; adding trees, boosting or
   interactions after seeing this result would be the search widening itself.
3. **`ec_delta_hi_lo` stays out.** Exchangeability failure is a data-regime fact, not tuning.
4. **Conviction sizing part 2 (score-proportional vs flat under funded rules) was GATED OFF and
   did not run.** Pre-registered as conditional on the composite clearing its noise floor; it did
   not, so sizing by composite score would be sizing by noise. Recorded as not-run, not negative.

## 4. WHAT REMAINS OPEN

**The conviction-state diagnostic is the live thread, and is not evidence yet.** Same frame,
day-clustered bootstrap intervals:

| state | rho | 95% CI | p | rho (OOS half) | n for 80% power |
|---|---|---|---|---|---|
| `struct` | +0.168 | [+0.022, +0.308] | 0.025 | +0.163 | 275 (n=176) |
| `day_pos` | +0.168 | [+0.019, +0.302] | 0.025 | +0.144 | 277 |
| `score` | +0.158 | [+0.025, +0.288] | 0.020 | +0.143 | 311 |
| `nth` | +0.158 | [+0.010, +0.295] | 0.039 | +0.128 | 311 |
| `cold` | −0.179 | [−0.318, −0.035] | 0.015 | −0.131 | 243 |
| `governor` | +0.057 | [−0.085, +0.203] | 0.451 | −0.006 | 2,406 |

Five of six carry associations **larger than any order-flow feature** (best OF single 0.066) and
hold sign out of sample. **None survives Bonferroni over 6 (α = 0.0083): survivors = NONE.**
Required n is 243–311 against an actual 182; `nth`/`day_pos` have 2 and 1 thin cells; the
variables are collinear by construction. Open, underpowered, unproven.

Also open: the gap lane (Amendment 5; |gap| carried rho +0.153 in Part 1), the expiry-week cell
(n=11), and Part 2's 60.2% tradeable resume rate.

## 5. RECOMMENDATIONS FOR THE NEXT ROUND

**Nothing here auto-applies. No feature, weight, threshold or config was or will be changed by
this memo. Every item needs your explicit sign-off before any code moves.**

1. **Remediate W and `dep_*` before any further selection-path study.** Every result this round
   rests on a leaky selection path. *Falsified if* a fully remediated book reproduces the Part-3
   news delta and the conviction rhos within existing CIs.
2. **Give conviction-state one lane and ONE pre-registered test, not six.** Bonferroni over six
   collinear variables is what killed it; one pre-declared index spends the alpha once.
   *Falsified if* that index fails the same >99th-percentile block-shuffle gate out of sample.
3. **Run no conviction test until n ≥ ~280 trades.** The artefact's own power figures say 243–311.
   *Falsified if* a sample that size still returns CIs spanning zero — the lane then closes.
4. **Prioritise the gap lane (G1/G2/G3) over further order-flow work.** Only registered hypothesis
   with an effect larger than the OF pool. *Falsified if* the non-monotone tercile pattern fails
   its own noise floor — flag the mid-cell overfitting trap in advance.
