# Pre-Registration — Augmentation Layer 01

**Time-of-day deseasonalisation + scheduled-release proximity, as continuous covariates
on the frozen sweep model.**

| | |
|---|---|
| Status | **PRE-REGISTERED — written before any run** |
| Layer ID | `AUG-01` |
| Author | Claude Code, on Pat's instruction |
| Date written | 2026-08-07 |
| Base model | Frozen sweep model (parameters locked; see §1) |
| Trade budget | n = 756 |
| Primary form | Continuous covariate, joint F-test |
| Family-wise α | 0.05 across L = 10 planned layers → **α = 0.005 for this layer** |
| Immutability | This file must be committed and its SHA-256 recorded **before** any build or test code executes. Any edit after that point voids the pre-registration and the layer restarts as a new ID. |

This document is written to be falsifiable. Everything that could be tuned after seeing
results is fixed here with a number and a justification, or explicitly declared exploratory
and barred from promotion.

---

## 1. What is frozen, and the inputs I do not have

**Frozen and untouchable for the duration of this layer:** the sweep model's entry
condition, exit condition, stop placement, target placement, and the resulting 756-trade
list. This layer adds a covariate to the *analysis* of those trades. It does not alter
which trades exist. If any base-model parameter moves, the trade list changes, and this
pre-registration is void.

**Inputs I need from you before the build runs.** I have not been given the sweep model
spec, so these are named placeholders, not assumptions I have quietly filled in:

| Placeholder | What I need | Why it matters |
|---|---|---|
| `TRADE_LIST` | 756 rows: entry ts (tz-aware ET), direction, entry px, initial stop px, exit ts, exit px, exit reason ∈ {target, stop, time, EOD} | Everything keys off this |
| `R_DEF` | Confirm R = \|entry − initial stop\| in points, fixed at entry, never re-based | The whole outcome variable is denominated in it |
| `WINDOW` | The session window the sweep model trades | Determines which 5-min buckets can ever be populated |
| `TRAIN_SPAN` | Calendar span the 756 trades cover | Determines whether the rolling profile has burn-in before trade #1 |
| `N_PRIOR` | How many hypotheses have already been tested against this trade list | Seeds the multiplicity ledger (§4.5). **If this is not zero, α changes.** |

`N_PRIOR` is the one that can invalidate the arithmetic below. If layers were already run
against these 756 trades, they consumed α that this document assumes is unspent.

---

## 2. Evidence base

Grades: **A** peer-reviewed, quantitative, replicated, on this asset class or adjacent
futures · **B** peer-reviewed, quantitative, different market · **C** documented but not
quantitatively established for our case · **D** widely repeated with no quantitative
backing located — *recorded as a finding* · **E** to be measured by us.

| # | Claim | Grade | Source / note |
|---|---|---|---|
| E1 | Intraday volatility follows a robust, strongly non-flat time-of-day periodicity | **A** | Wood, McInish & Ord (1985) *J. Finance*; Harris (1986) *J. Financial Economics*; Andersen & Bollerslev (1997) *J. Empirical Finance*. Established for equities and FX; index futures adjacent |
| E2 | Ignoring intraday periodicity distorts inference on volatility dynamics — the seasonal component dominates and masks the persistence structure | **A** | Andersen & Bollerslev (1997), which is the canonical treatment and the origin of the Flexible Fourier Form deseasonalisation |
| E3 | Scheduled macro releases produce sharp, concentrated volatility responses at the release minute | **A** | Ederington & Lee (1993) *J. Finance*, on interest-rate and FX futures; documents 08:30 ET releases dominating the intraday vol pattern |
| E4 | Most price adjustment to a release completes within the first minute; elevated volatility persists roughly 15 minutes, mildly for hours | **A** | Ederington & Lee (1995) *J. Financial & Quantitative Analysis*. This is what fixes τ = 30 min in §3.4 |
| E5 | Parkinson's range estimator is materially more efficient than close-to-close for the same sample | **A** | Parkinson (1980) *J. Business* |
| E6 | Range estimators are biased **downward** under discrete sampling, and the bias grows as the number of price observations inside the bar falls | **A** | Garman & Klass (1980); Beckers (1983). **This bias is itself time-of-day dependent and directly contaminates a seasonal curve — see §3.2 hazard** |
| E7 | The intraday volatility curve is unstable year-to-year, so a once-fitted static curve drifts | **C** | Time-variation in intraday patterns is documented in general terms, but I could not locate a quantitative study of year-over-year curve instability *for NQ specifically*. The rolling design in §3.2 is therefore justified on precautionary grounds (§3.2), not on this citation. Do not cite E7 as settled |
| E8 | "Do not trade within N minutes of a news release" | **D** | **Finding.** Ubiquitous in retail trading education, with N variously 5, 15, 30 or 60 and no study cited for any value. Our own `strategy-definition-v1.0.md` §7 carries it as hypothesis H4 with N unspecified. This layer is the first quantitative test of it in this project. The absence of backing is the result, and it should be written up as such |
| E9 | Economic-calendar aggregators' "high/medium/low impact" ratings identify the releases that move markets | **D** | **Finding.** No published methodology for any major aggregator's rating. Ratings are editorial and revised. This is why §3.4 sources the calendar from statistical agencies instead |
| E10 | Specific named intraday windows ("kill zones", an 08:00 anchor) carry edge | **D** | **Finding.** Widely repeated in ICT-derived retail material, including the Star Trading corpus reviewed earlier in this project. No peer-reviewed quantitative backing located. Not tested here; noted so it is not mistaken for E1, which is a different and genuinely evidenced claim |
| E11 | Seasonal profile shape and per-bucket observation counts for NQ over our window | **E** | Produced by §3.2 |

Two of the three Grade D entries are load-bearing for this project's existing plans (H4 in
§7 of the strategy doc; the news-day override in §6.3). Neither currently rests on anything
quantitative.

---

## 3. Build specification

### 3.0 Data preparation — non-negotiable, from the Stage 0 audit

1. **Exclude calendar spreads.** Any `symbol` containing `-` (e.g. `NQZ5-NQH6`) is a spread
   instrument and is dropped. Confirmed present in the OHLCV files.
2. **Front-month selection by daily volume.** For each session, the outright with the
   highest total volume is the front month. Roll date = the first session where the
   deferred contract's volume exceeds the front's (verified: 2025-12-15 for NQZ5→NQH6).
3. **Returns never cross a roll.** Prices are **not** back-adjusted; the inter-contract
   spread was measured at ~227–258 points across the Dec-2025 roll. **CORRECTED 2026-08-08:
   the spread is not a constant.** Measured from the `NQxx-NQyy` calendar instrument's own
   quotes across all **eight workbench rolls**, the median ranges **125.05 → 300.40 points**
   (2023-03: 125.05 · 2023-06: 180.75 · 2023-09: 197.90 · 2023-12: 210.80 · 2024-03: 247.65 ·
   2024-06: 264.15 · 2024-09: 236.00 · **2024-12: 300.40**), growing roughly with the rate
   environment. The four 2025+ rolls are holdout-dated and were refused. The first bar of a new
   front month has **no** return; it is dropped, not carried. A single unhandled roll injects a
   fake return of **125 to 300 points** — the size depends on which roll — that would swamp
   every seasonal bucket it lands in. See `research/STATE.md` → ROLL SPREADS, and
   `research/star-trading/tools/roll_spreads.py`.
4. **Bar labelling.** Source bars are **open-labelled** (verified empirically: median
   \|book_mid − bar.close\| = 0.38 pts vs 6.69 pts against bar.open). Bar labelled `13:00`
   covers `13:00:00–13:00:59`. Apply the pipeline's standard +1 min shift to close labels
   once, at load, and assert it once.
5. **Session definition.** Globex 18:00 ET → 16:59 ET, 1380 bars, tz-aware
   `America/New_York`, DST handled by the tz library. Sessions with < 1380 bars (holidays,
   early closes) are flagged and **excluded from the seasonal profile** but retained for
   trade evaluation, with the exclusion count reported.

### 3.1 Notation

- `b` — 5-minute bucket index, 0…275 across the 1380-bar session
- `d` — session date
- `H_{b,d}`, `L_{b,d}` — high and low of bucket `b` on session `d`, from its 5 constituent 1-min bars
- `r_t` — 1-minute log return, within-contract only

### 3.2 Seasonal volatility profile — rolling

**Estimator.** Parkinson variance computed on the **bucket's own** high/low, not as an
average of five per-minute Parkinsons:

```
parkvar(b,d) = ( ln( H_{b,d} / L_{b,d} ) )^2 / (4 ln 2)
```

Bucket-level H/L is chosen over averaging per-minute estimates because zero-range 1-minute
bars are common in thin Globex hours and each one contributes an exact zero, dragging the
bucket mean down. Bucket-level aggregation reduces zero-range incidence by roughly the
bucket width.

**Rolling window.** For session `d`, the seasonal sigma for bucket `b` uses the trailing
**W = 60 completed sessions, strictly before `d`**:

```
sigma_seasonal(b, d) = sqrt( mean over the 60 sessions in [d-60, d-1] of parkvar(b, ·) )
```

Causal by construction — session `d` never contributes to its own normaliser. **60 sessions
gives exactly 60 observations per bucket per estimate**, a relative standard error on the
variance of ≈ 1/√(2·60) ≈ 9.1%.

**Why rolling, given E7 is only Grade C.** Rolling is chosen as a dominance argument, not
on the strength of the citation. If the curve is stable, rolling costs only estimator
variance (9.1% vs 4.1% at W=240) and the conclusion is unchanged. If the curve drifts, a
static curve is biased and rolling is not. Since the downside is bounded and small and the
upside is protection against an unquantified risk, rolling wins without needing E7 to be
true. **W = 60 is fixed here and is not tunable.** W ∈ {120, 240} is run once as a declared
robustness check (§8), reported whatever it shows, and cannot change the primary result.

**Burn-in.** The first 60 sessions of the data have no profile and are unusable. Confirm
`TRAIN_SPAN` starts ≥ 60 sessions after the first available session, or trades in the
burn-in are dropped and the count reported.

**Required outputs (reported before any test is run):**

- Observations per bucket per estimate (expected 60, exactly), and the count of buckets
  falling short due to holiday exclusions
- The mean profile across the full window, all 276 buckets, plotted
- **Fraction of zero-range 1-min bars per bucket**, and **mean volume per bucket** — see hazard
- A stability panel: the profile computed per calendar year, overlaid. **This is our own
  measurement of E7** and converts a Grade C claim into a Grade E fact for our data

**Hazard, stated up front (E6).** Parkinson is biased downward when few price observations
fall inside the bar, and observation density varies enormously across the Globex session —
by an order of magnitude between the overnight lull and the cash open. The measured seasonal
curve therefore conflates *true* volatility seasonality with *sampling-density* seasonality,
and it does so in the same direction: thin hours look even quieter than they are. We have no
tick data to correct this. Mitigation is disclosure, not repair: report per-bucket volume
and zero-range fraction alongside the curve, and treat the overnight buckets' levels as
biased low. If the sweep model does not trade the thin hours, the bias is largely irrelevant
to this layer — confirm from `WINDOW`.

**Floor.** `sigma_seasonal` is floored at 0.25 points (one tick) expressed in log terms, to
prevent division blow-ups. Buckets hitting the floor are counted and reported.

### 3.3 Deseasonalised return series

```
r_norm(t) = r_t / sigma_seasonal( bucket(t), session(t) )
```

**Validation gate before any testing (this is a build check, not a hypothesis test).** If
deseasonalisation worked, the time-of-day signature in dispersion should be largely removed.
Compute RMS(`r_norm`) per bucket across the training window. Report:

- The ratio max/min of bucket RMS, before vs after normalisation
- Kurtosis of `r_norm` pooled, vs `r_t` pooled

Expected: bucket RMS ≈ 1 across buckets after normalisation. **If the post-normalisation
max/min ratio exceeds 1.5, the deseasonalisation has failed and the layer stops here** —
reported as a build failure, not tested and not promoted. This is a pre-committed abort
condition, not a threshold to be relaxed on the day.

### 3.4 Scheduled-release fields

**Calendar source — official statistical agencies, not an aggregator.** Per E9, aggregator
impact ratings have no published methodology and their archives are revised. The calendar is
built from primary release schedules:

| Release time | Releases | Source |
|---|---|---|
| **08:30 ET** | Employment Situation, CPI, PPI, Real Earnings | **BLS** — `bls.gov/schedule/news_release/` |
| 08:30 ET | GDP, Personal Income & Outlays (PCE), Trade Balance | **BEA** — `bea.gov/news/schedule` |
| 08:30 ET | Retail Sales, Durable Goods, Housing Starts | **US Census Bureau** |
| **10:00 ET** | ISM Manufacturing PMI, ISM Services PMI | **Institute for Supply Management** |
| 10:00 ET | JOLTS | **BLS** |
| 10:00 ET | Consumer Sentiment (final/prelim) | **University of Michigan** |
| 10:00 ET | Consumer Confidence | **The Conference Board** |

**Frozen artefact.** The calendar is compiled once to
`config/news_calendar.csv`, columns `date, release_time_et, agency, release_name`, then
**SHA-256 hashed and the hash recorded in this file's amendment log before any test runs.**
No release may be added or removed after that point. Retroactively editing a calendar to
match results is the single easiest way to fabricate this effect.

Coverage must span `TRAIN_SPAN` fully; any date with missing calendar coverage is dropped
from the trade set and the count reported. No date is silently treated as "no release" —
absence of data and absence of a release are different states and must be distinct columns.

**Fields built** (all causal — known at or before entry):

| Field | Definition |
|---|---|
| `has_0830` | bool — session contains a scheduled 08:30 ET release |
| `has_1000` | bool — session contains a scheduled 10:00 ET release |
| `mins_to_next` | minutes from entry to the next scheduled release in-session; `NULL` if none remains |
| `mins_since_last` | minutes from the most recent in-session release to entry; `NULL` if none yet |
| `tau_signed` | signed minutes to the **nearest** release: negative = already released, positive = upcoming |

**A correction to the brief, with reason.** The spec asked for `mins_to_next` as the
continuous field. Used alone it is wrong in a way that would bias the test toward the null:
a trade at 08:31 ET — one minute after a major release, at the volatility peak — has
`mins_to_next` = 89 (to the 10:00 release) and is therefore coded as *far from news*, which
is the opposite of its true state. The primary model therefore uses `|tau_signed|`, which is
small both just before and just after a release. `mins_to_next` is still built and reported
as specified, and the before/after asymmetry is examined descriptively in §7.

**Release proximity covariate:**

```
w_i = exp( -|tau_signed_i| / 30 )        w in (0, 1]
```

**τ = 30 minutes, fixed a priori, not tunable.** Justified by E4: adjustment concentrated in
the first minute, elevated volatility ~15 min, mild elevation for hours. τ = 30 gives
w = 0.61 at 15 min, 0.37 at 30 min, 0.14 at 60 min. Fitting τ would be a hidden multiple
test with an unbounded search space and is prohibited. If no release exists in a session,
`w_i = 0`.

---

## 4. The pre-registered test

### 4.1 Outcome variable

```
y_i = net R multiple after costs   (§5)
```

Denominated in the frozen model's own initial-risk unit (`R_DEF`). **Win rate is not an
outcome variable anywhere in this document.**

### 4.2 Covariates

```
z_i = ln( RMS( r_norm ) over the 30 one-minute bars strictly before entry_i )
w_i = exp( -|tau_signed_i| / 30 )
```

`z_i` is the deseasonalisation output expressed as a state variable: under working
deseasonalisation, RMS(`r_norm`) ≈ 1 in normal conditions, so `z_i` ≈ 0, positive when the
market is unusually volatile *for that time of day*, negative when unusually quiet. This is
the quantity a raw volatility measure cannot express, and it is the entire point of the
layer.

Both are standardised to zero mean, unit variance using **training-window statistics only**,
before entering the model.

### 4.3 Model

```
y_i = β0 + β1·z_i + β2·w_i + ε_i          OLS, HAC (Newey–West) standard errors
```

Lag for the HAC estimator: **10 trades**, fixed. Trades overlap in time and cluster within
sessions, so i.i.d. standard errors would be anti-conservative.

**Primary null:** `H0: β1 = β2 = 0` — a single joint F-test, 2 numerator df.

One test, not two. Testing the coefficients separately would split α again; the joint test
spends it once. Individual coefficients are examined **only if** the joint test passes, and
then descriptively.

**Why an in-sample F-test is legitimate here.** Because this document fixes the functional
form, both covariates, τ, W, the HAC lag and the standardisation before any data is seen.
There is no variable selection and no search. Pre-registration is precisely what makes the
nominal df correct. This validity evaporates if anything in §3 or §4 is altered after a run.

### 4.4 Statistical criterion and power

α = 0.005 (§4.5). With n = 756, df = (2, 753):

```
F_crit(2, 753) at α = 0.005  =  5.336
```

*(Computed by direct evaluation of the regularised incomplete beta; validated against
published tables — F(2,100)@0.05 = 3.0873 vs 3.087, F(1,10)@0.05 = 4.9646 vs 4.965 — and
cross-checked against the closed form for df1 = 2.)*

| True R² | Power at n = 756 | n required for 80% power |
|---|---|---|
| 0.005 | 0.133 | 3,120 |
| 0.010 | 0.370 | 1,555 |
| 0.015 | 0.610 | 1,033 |
| **0.020** | **0.788** | **773** |
| 0.0204 | 0.799 | 757 |
| 0.025 | 0.897 | 616 |
| 0.030 | 0.954 | 512 |
| 0.050 | 0.999 | 303 |

**Minimum detectable effect: R² = 2.04% at 80% power.**

**The honest reading of this table, recorded now so it cannot be spun later.** A trade-level
conditioning variable that explains 2% of net-R variance is a *large* effect for this kind of
problem; 0.5–1% is the more typical magnitude for something genuinely useful. At R² = 1%
this design has **37% power** — it will miss a real effect of that size nearly two times in
three. Detecting 1% would need 1,555 trades, more than double the budget.

Therefore: **a failed test does not license the conclusion that no effect exists.** If the
test fails, the report states the point estimate and its 95% confidence interval, and the
conclusion is "no effect of detectable size was found, and effects below R² ≈ 2% are outside
this design's reach." Declaring the covariate dead on a null result at n = 756 would be a
Type II error dressed as a finding.

### 4.5 Multiplicity ledger

Correction is across the whole project, not this layer.

| | |
|---|---|
| Family-wise α (project) | 0.05 |
| Planned augmentation layers, L | **10** |
| Correction | Bonferroni, fixed |
| **α per layer** | **0.005** |
| Tests inside this layer | 1 (joint F, 2 df) |
| **N_trials consumed by AUG-01** | **1** |
| **Running N_trials after this layer** | **`N_PRIOR` + 1** — must be confirmed |

Rules, binding:

1. **Every** hypothesis tested against this trade list increments `N_trials`, including ones
   abandoned before completion and ones whose results were never written up. An untested
   idea costs nothing; a tested-and-discarded one costs α.
2. If the project exceeds L = 10 layers, α must be **re-derived at the new L and all prior
   conclusions re-evaluated at the tighter threshold.** A layer that passed at 0.005 does not
   stay passed if L rises to 20 (α = 0.0025, F_crit = 6.039).
3. The exploratory items in §7 do **not** increment `N_trials`, because they carry no pass
   mark and cannot be promoted. If any is ever promoted, it gets its own pre-registration and
   its own increment.
4. Bonferroni is conservative. Holm–Bonferroni controls the same family-wise error rate with
   uniformly greater power and may be applied **retrospectively across all L layers once the
   programme completes**. It cannot be applied prospectively to individual layers, since Holm
   needs the full set of p-values. Fixed Bonferroni is used for live decisions because each
   layer needs a verdict when it runs.

The robustness runs in §8 do not increment `N_trials`; they are reported unconditionally and
cannot overturn a primary result in either direction.

---

## 5. Cost model — and its weakest link

Applied to every trade before `y_i` is formed. Never applied selectively.

```
cost_i ($) = 4.50                                 commission, round turn, 1 NQ contract
           + 5.00  if exit_reason == 'stop'       1 tick adverse on a market-triggered stop
           + 0.00  if exit_reason == 'target'     limit fills do not slip favourably
           + 5.00  if exit_reason in ('time','EOD')  market exit
entry slippage = 0.00                             limit entry per strategy doc §5
y_i = ( gross_points_i * $5.00 - cost_i ) / ( R_points_i * $5.00 )
```

**The load-bearing weakness, stated plainly: slippage is assumed, not measured.** The Stage 0
audit established there is no trade-level data — three trade records across 67,419 book rows
— so no execution-quality estimate is possible from what we hold. The 1-tick figure is a
convention, not a measurement.

**Mandatory sensitivity analysis, reported with the primary result whatever it shows:**
re-run the full decision at stop slippage ∈ {0, 1, 2, 3} ticks. **If the pass/fail verdict
changes anywhere in that range, the layer is reported as NOT ROBUST and is not promoted,
regardless of the primary p-value.** A result that depends on an unmeasured convention is not
a result.

A second-order effect worth naming: this layer conditions on volatility state, and slippage
is itself worse in high-volatility states. A fixed per-trade slippage assumption therefore
under-penalises exactly the trades the covariate is most likely to favour. The direction of
this bias is **toward a false positive on β1**. It cannot be corrected without tick data;
it is disclosed, and it is a further reason the {0,1,2,3}-tick band is binding rather than
decorative.

---

## 6. Decision rule

The layer is promoted **only if all four conditions hold.** Any single failure means no
promotion. There is no partial credit and no "promising, run it again" branch.

**C1 — Build validity.** §3.3 post-normalisation bucket RMS max/min ≤ 1.5, and the calendar
hash recorded before the run.

**C2 — Statistical.** Joint F(2, 753) ≥ 5.336, i.e. p ≤ 0.005.

**C3 — Economic, and this is the binding criterion.** Net expectancy after costs must
improve by a pre-specified margin, measured out-of-sample.

The fitted score becomes a **risk-sizing multiplier** — which honours the covariate form,
uses every one of the 756 trades, and never gates a trade out:

```
score_i   = β̂1·z_i + β̂2·w_i          β̂ from training folds only
k_i       = clip( 1 + 0.5 · standardise(score_i), 0.5, 1.5 )
E_base    = mean( y_i )
E_layer   = mean( k_i · y_i ) / mean( k_i )       risk-normalised: same average risk deployed
Δ         = E_layer - E_base
```

λ = 0.5 and the clip band [0.5, 1.5] are **fixed a priori**. Sizing is risk-normalised so the
comparison is expectancy per unit of risk deployed, not a leverage effect masquerading as
skill.

Evaluated by **purged, embargoed, expanding-window walk-forward**: minimum 300-trade initial
training block, then 5 sequential evaluation folds; β̂ and all standardisation statistics
come from data strictly prior to each fold; trades whose 30-bar feature window or 60-session
seasonal window overlaps a fold boundary are purged; a 5-trade embargo follows each training
block.

**Pass requires both:**

```
Δ ≥ +0.05 R per trade          pre-specified minimum, ≈ +37.8R over 756 trades
AND  one-sided t-test on the paired per-trade delta, p ≤ 0.005
```

The +0.05R floor sits above the design's economic detection limit — at a paired-delta SD of
0.30R the minimum detectable Δ is +0.028R, at 0.50R it is +0.047R — so the floor is
reachable rather than decorative, with margin at plausible dispersions.

**Explicitly: a rise in win rate is not evidence and will not be reported as such.** A
filter that raises win rate by removing large winners loses money. If win rate rises while Δ
is negative or insignificant, the layer **fails**, and the write-up must state the win-rate
movement and the failure together, in that order, so the seductive number never appears
without its refutation.

**C4 — Cost robustness.** §5 verdict stable across stop slippage ∈ {0, 1, 2, 3} ticks.

**On failure:** the layer is recorded as tested-and-failed in the ledger, `N_trials` still
increments, and the covariate is not retried in a different functional form without a new
pre-registration and a new increment. Re-specifying until something passes is the failure
mode this whole document exists to prevent.

---

## 7. Secondary — exploratory, fenced, no pass mark

**These are descriptive only. They have no threshold, cannot pass, cannot fail, do not
increment `N_trials`, and must not be promoted without their own pre-registration.** They are
reported because the full-Globex bar coverage makes them computable, not because they are
being tested.

Now computable, per the Stage 0 audit:

| Field | Definition |
|---|---|
| `gap_atr` | (RTH open 09:30 ET − prior session close 16:59 ET) / ATR(14, daily), within-contract only |
| `on_range_pos` | (RTH open − ON low) / (ON high − ON low), overnight range 18:00 ET → 09:29 ET |
| `on_range_atr` | (ON high − ON low) / ATR(14, daily) |

Reported as: decile tables of mean net R with bootstrap confidence intervals, scatter against
`y_i`, and Spearman correlation with `y_i`. **No p-values, no thresholds, no verdict.**

Also exploratory, examining the asymmetry §3.4 set aside: mean net R split by
`tau_signed < 0` (post-release) vs `> 0` (pre-release) within \|tau\| ≤ 30 min. Descriptive
only — and per E4 the pre/post dynamics genuinely differ, so if this looks interesting it is
a candidate for AUG-02 with its own α, not a finding here.

If any of these looks compelling, the correct response is to write the next pre-registration,
not to append it to this one. Appending is how L becomes uncountable and α becomes fiction.

---

## 8. Declared robustness runs

Run and reported unconditionally, whatever they show. They **cannot** overturn the §6
verdict in either direction — they are context for the reader, and they do not increment
`N_trials` because they test no new hypothesis.

1. Seasonal window W ∈ {120, 240} sessions alongside the primary W = 60
2. Local volatility lookback ∈ {15, 60} bars alongside the primary 30
3. HAC lag ∈ {5, 20} alongside the primary 10
4. Per-year subsample coefficient stability (also serves as our own measurement of E7)

If the primary passes but the coefficient sign flips across years, the write-up says so in
the summary line, not in a footnote.

---

## 9. What would invalidate this pre-registration

- Any edit to §3–§6 after the recorded commit hash
- `N_PRIOR` turning out to be non-zero without α being re-derived
- Any change to the frozen sweep model or the 756-trade list
- The news calendar being modified after its hash is recorded
- L rising above 10 without re-derivation and re-evaluation of prior conclusions
- τ, W, λ, the clip band, or the HAC lag being fitted rather than taken as fixed

---

## 10. Amendment log

| Date | Change | Hash after |
|---|---|---|
| 2026-08-07 | Initial pre-registration, written before any build or test code | *(record `git rev-parse HEAD` and the calendar SHA-256 here before the first run)* |
