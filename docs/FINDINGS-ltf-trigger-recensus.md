# FINDINGS — LTF TRIGGER RE-CENSUS (the conjunction)

Run 2026-08-07 against `DECLARATIONS-ltf-trigger-recensus.md`, which was
written and committed (`d47cfc4e`, amended `f675e39f`) before a single row
existed. Fit span 2025-06-01..2026-07-14, 291 session days, 81,457 triggers
with outcomes. **Holdout look #1 remains HALTED and unspent.**

> ## CORRECTION, same day, before anything was acted on
>
> The first version of this document concluded "**the LTF trigger family is
> closed**" from the raw-substrate result below. **That conclusion was
> wrong and is withdrawn.** The objection that produced the correction:
> *the raw book is unselected substrate — a population containing trades
> nobody would take — so a raw-vs-raw comparison does not settle which
> trigger timeframe supports the better selected book.*
>
> That objection is correct, and the test is in **§ MATCHED SELECTIVITY**
> below. At matched trades/day, **3m and 5m beat the 15m control by
> +0.12 to +0.20R** and clear both eras; the raw ordering reverses
> everywhere except 1m. The mechanism is specific and is the most useful thing in this
> pass: **a tighter stop does not enlarge MFE (prediction 3 stays refuted)
> — it makes room-to-run measurable.**
>
> What survives unchanged: every gate, every raw number, the refutation of
> predictions 3 and 5, the stop-rule defect, and the D1a verdict on (B).
> What is withdrawn: the closure of the LTF family and the cancellation of
> the cross-TF union.

## THE HEADLINE (raw substrate, unselected — see the correction above)

**On raw substrate the 15-minute candle is the best of the five timeframes
measured, and the ordering is monotone.** This is a fact about the
unselected population and it is NOT the same claim as "the 15m trigger
supports the best book."

Pooled (A)-only executable first-of-fight book, shipped exit, one
convention throughout (both arms entering at the next 1m open), X=0.5W15:

| trigger TF | book EV | fights/day | median stop | cost_R p50 |
|---|---|---|---|---|
| **1m** | **−0.071R** | 26.03 | 8.25pt (0.092W) | 0.061 |
| **2m** | +0.028R | 24.60 | 11.75pt (0.130W) | 0.043 |
| **3m** | +0.057R | 23.34 | 14.25pt (0.155W) | 0.035 |
| **5m** | +0.096R | 21.97 | 18.50pt (0.204W) | 0.027 |
| **15m (control)** | **+0.176R** | 18.62 | 30.75pt (0.345W) | 0.016 |

Monotone in TF at **every** clustering width (X = 0.25 / 0.5 / 1.0 / 2.0W),
so this is not an artefact of the fight convention. The 1m book is
**negative**.

**Nothing in this pass cleared a declared bar.** Zero of 168 (A)-only cells
met the E1.4 both-era test. Zero of 30 (session × TF × arm) cells met the
D1a bar for condition (B).

## GATES AND CONTROLS (all passed before any row was read)

- **D8 pre-flight.** No cell exceeded 50 triggers/day (max 6.01). Trigger
  counts scale strongly **sub-linearly**: 1m produces 3.50× the 15m trigger
  rate against 15× the candles (2m 2.57×, 3m 2.12×, 5m 1.67×). Zero
  super-linear cells. No pathology.
- **Calibration control, trigger stage.** The (A)-only path at TF=15
  reproduced the existing level census **exactly**: 8,107 vs 8,107 triggers,
  zero rows either way, matched on (day, t, locus, arm, side).
- **Calibration control, outcome stage.** The vectorised outcome walk was
  checked row-by-row against the 15m census on 353 matched reject rows:
  `entry`, `stop`, `risk`, `mfe_r`, `out_ship`, `out_trail`, `out_hold`,
  `t_entry`, `t_exit` all identical to 1e-9.
- **Entry-price gate, all four TFs: PASS.** T1 flatten (0 bad of 1,074
  probes, and the entry moved on 916 of them, so it is genuinely read from
  post-decision data), T2 next-open 0 failures either arm, and T3B — a new
  probe replacing the level census's fill-bar test — shifted every
  post-decision bar +50pt and confirmed condition (B) never flips.

## THE PREDICTION, SCORED

The declaration named five consequences before the run.

| # | prediction | verdict |
|---|---|---|
| 1 | fights/day UP | **confirmed, but far smaller than it looks.** Raw triggers rise 3.50× from 15m to 1m; *fights* rise only 1.40× (18.62 → 26.03/day). The structural clustering absorbs most of the extra triggers — they are the same fight seen more often. |
| 2 | stop width DOWN 2–3× | **confirmed, 3.7×** (30.75 → 8.25pt median, 0.345W → 0.092W). |
| 3 | MFE-in-R shifted substantially UP | **REFUTED.** LONDON median MFE 1.11R (15m) → 0.75R (1m). P(MFE≥3R) is flat at 27.4% → 27.1%. Only the far tail stretched (p90 8.50 → 12.99). |
| 4 | the partial relocated away from 3R | **essentially invariant.** T=5 was already best in LONDON at 15m and stays T=5 at every TF; NY_AM moves T=3 → T=5. Every LTF EV at every T is lower than the 15m EV at the same T. |
| 5 | flow markedly STRONGER at 1m | **REFUTED as stated** — see below. |

**Prediction 3 is the important refutation.** The premise was: same
excursion, smaller denominator, therefore a bigger R-multiple. What
actually happens is that the excursion is denominated in W, not in your
stop (BR-4, the scale law). Cutting the stop 3.7× did not multiply MFE-in-R
by 3.7 — it left the body of the distribution alone and moved the losers.
P(≥3R) — the quantity the 75%-at-3R leg actually depends on — did not move
at all.

## WHY THE RAW LTF BOOK LOSES: the stop RULE, not the timeframe

Two mechanisms, both measured. Note the scope: this explains the **raw**
ordering above. Mechanism 2 in particular is separable, which is part of
why the ordering does not survive selection.

**1. Costs, exactly as D6 warned.** cost_R median 0.061 at 1m vs 0.016 at
15m. Under the declared stress assumptions:

| TF | EV @0.5pt | EV @1.0pt | EV @1.5pt |
|---|---|---|---|
| 1m | −0.071 | −0.180 | −0.289 |
| 5m | +0.096 | +0.044 | −0.007 |
| 15m | +0.176 | +0.147 | +0.118 |

Only the 15m book survives an adverse-fill assumption. **This was the
declared "if costs eat the tighter-stop advantage, THAT IS THE FINDING"
outcome, and it is the finding — but it is not the whole of it.** Costs
explain roughly a third of the 1m→15m gap; the rest is mechanism 2.

**2. The stop rule degenerates.** "Stop = the trigger candle's extreme ± 1
tick" is a sound risk unit when the candle is 30pt tall. At 1m the candle's
own range is sometimes a single point, and then *risk stops being a risk
unit*: the stop sits inside the noise and `cost_R = 0.5/risk` explodes.

| TF | risk p05 | share <2pt | EV \| risk<2pt | EV \| risk≥2pt | book EV |
|---|---|---|---|---|---|
| 1m | 1.50pt | 7.6% | **−0.667** | −0.022 | −0.071 |
| 5m | 3.00pt | 2.0% | −0.598 | +0.110 | +0.096 |
| 15m | 5.50pt | 0.7% | −0.599 | +0.182 | +0.176 |

Within-TF risk quintiles say the same thing: at 1m the smallest-stop
quintile returns −0.358R. **This is a defect in the stop rule at short
timeframes, not a fact about short timeframes**, and it is separable — a
risk floor recovers the 1m book from −0.071 to −0.022, which is still worse
than every other TF.

**Consequence for `closeloc`.** For a long, stop = the candle's low, so
`risk ≈ closeloc × range`. A candle that closed near its own stop has a
near-zero risk denominator. `closeloc` is the strongest single feature in
the flow table (Spearman +0.35 at every TF) and that correlation is
**partly mechanical**. Any future use of `closeloc` — including the D1
bar-only proxy for S1 — must be re-measured on a risk-floored population.

## D1a — CONDITION (B) DOES NOT CLEAR ITS BAR

Declared bar: marginal lift ≥ +0.05R with the day-boot CI on the **lift**
clear of zero in **both** eras, per (session, TF). Result: **0 of 30 cells
pass. Per D1a the verdict recorded is "(B) adds nothing" and the shipped
trigger stays (A)-only.**

That verdict stands, and the following does not amend it — but the two arms
failed in visibly different ways and the difference is on the record:

- **Reject arm:** (B) is a savage filter (q = 0.88–0.98; it removes
  93–98% of 1m reject triggers). Point estimates are **positive in 14 of 15
  cells**, median ≈ +0.18R, and the dual currency **agrees** (kept win rate
  29–45% vs failed 24–32%) — this is not the BR-20 hit-rate/EV inversion.
  It fails on **power**, not on sign: n_keep is 30–170 rows per cell and
  only two cells clear in a single era.
- **Break arm:** point estimates straddle zero (7 negative of 15), median
  ≈ 0. Here (B) genuinely adds nothing.

The reject-arm sign consistency is **not** a sign test with n=15: the
cells share populations across TFs (the same move fires at 1m, then 2m,
then 3m) and across sessions within a day, so the effective independent n
is far smaller. It is a directional signal worth a fresh blind declaration
on the 15m reject book — where n_keep would be ~7× larger — and nothing more.

**Structural check on the conjunction wiring.** At TF=15 the locus
`bbma15` *is* that TF's own BB MA, so (B) must be trivially true for every
break (100.0% observed) and trivially false for every reject (0.0%
observed). Both identities hold exactly. At TF=1 the same locus gives 21.9%
/ 5.7% — so (B) is a genuinely independent condition at LTF, which is what
makes the test meaningful. A side-effect worth stating: **the incumbent
15m reject book is precisely the population (B) rejects.**

## PREDICTION 5 — FLOW AT THE EVENT MINUTE

The claim that motivated the entire re-census: at 15m the delta window
pools fifteen minutes of mixed flow around a one-minute event, so the flow
family was never tested, only attenuated. It has now been tested.

Per-feature Spearman vs `out_ship`, same feature, same population grammar,
only the window changes:

| feature | 1m | 2m | 3m | 5m | |
|---|---|---|---|---|---|
| flowconf | +0.196 | +0.199 | +0.201 | **+0.237** | weaker at 1m |
| volx | +0.197 | +0.221 | +0.240 | **+0.261** | weaker at 1m |
| eff_result | n/a | +0.157 | +0.132 | +0.113 | — |
| thru_delta_conf | **+0.196** | +0.194 | +0.175 | +0.122 | stronger at 1m |
| d5/d15/d30_conf, cvd_slope30, delta_z, bp5opp | ≈0 | ≈0 | ≈0 | ≈0 | flat (control) |

**The prediction is refuted as stated.** The bar-window flow features are
*weaker* at 1m, not stronger. The pre-bar features are flat across TF,
exactly as they must be — they never used the bar window — which is the
internal control confirming the comparison is fair.

The one feature that strengthens, `thru_delta_conf`, is **the same number
arriving twice**: at TF=1 the decision bar is one minute, so
`thru_delta_conf` and `flowconf` are 100.0% identical. Its rise to the
1m level of `flowconf` is arithmetic, not evidence. (CONCORD therefore
double-counts one signal at 1m; left uncorrected so the count stays
identical to BR-19's.)

**This closes a question open since the beginning: the flow family is
genuinely weak, not mis-measured.** Aligning delta to the exact event
minute does not rescue it. That is a result, recorded as one.

One thing did move, and it is honest to say so: **CONCORD ranks the LTF
population better than it ranked the 15m one** (reject-arm Spearman +0.19
to +0.24 in every session and TF, vs BR-19's +0.129 at 15m). It still has
no gate value — 96 cut cells were searched and **0 cleared the +0.05R bar
in both eras**; the largest lift anywhere was +0.321R (LONDON reject 1m,
CC≥8) and it fails H1. With 96 cells the Bonferroni α is 0.00052. This is
a fit-side ranking of candidates, not a result.

## D4 — THE VALLEY, AND WHY THE PROCEDURE NEEDED A GUARD

Re-run per (TF × session). At LTF the excursion distribution collapses
towards zero (LONDON 1m: p50 0.10W, p75 0.19W) because consecutive triggers
are minutes apart. The valley detector then fires **out in the decaying
tail** — "a valley at 0.95W" sitting at the 99.2nd percentile of a
distribution whose p75 is 0.19W is a count artefact, not structure.

A percentile guard was added: a candidate beyond p95 is rejected as tail
noise. After it, **no TF ∈ {1,2,3,5} cell produces a both-era valley, so
the declared X=0.5W fallback stands everywhere.** One control-column cell
(TF=15, NY_PRE, 0.95W at the 80th percentile) does replicate across eras —
1 of 15, uncorrected, on the control rather than a candidate. Not adopted;
noted as a possible follow-up for the 15m book under its own declaration.

## D3 — TF SIGN AGREEMENT

Break arm: sign-agreement in LONDON and NY_AM. Reject arm: none, in any
session — the 1m reject EV is negative in all three sessions while the 5m
and 15m are positive. Since no cell clears the E1.4 bar, no pooled verdict
is available either way; this is recorded, not used.

## MATCHED SELECTIVITY — the test the raw comparison could not settle

**The question.** The raw book is every trigger at every locus, both arms,
all sessions. Nobody trades that. If short timeframes produce a larger and
more heterogeneous population, selection has more to work with there — so
the raw ordering could reverse once both sides are selected. The raw
comparison cannot answer this, and the first draft of this document
wrongly treated it as if it had.

**The design.** Hold **trades/day constant** across timeframes and compare
EV. The *same three filters* are applied identically at every TF — a 2pt
risk floor, room-to-run (`next_lvl_R ≥ 3R` or open space), then top
flow-concordance until the per-day rate hits the target. Selectivity is
**swept, not tuned**. Only the TF changes.

| target/day | 1m | 2m | 3m | 5m | **15m** |
|---|---|---|---|---|---|
| 1.0 | +0.317 | +0.366 | **+0.453** | +0.400 | +0.256 |
| 2.0 | +0.264 | +0.334 | **+0.446** | +0.427 | +0.306 |
| 3.0 | +0.232 | +0.350 | **+0.406** | +0.386 | +0.328 |
| 4.0 | +0.211 | +0.300 | **+0.363** | +0.348 | +0.282 |
| 6.0 | +0.120 | +0.247 | *max 5.36* | *max 5.07* | *max 4.70* |

**The raw ordering reverses.** At every rung from 1 to 4 trades/day, 3m and
5m beat the 15m control, by +0.12 to +0.20R. At ~2/day the day-boot CIs
clear zero in **both eras** at 2m, 3m, 5m and 15m — and **not** at 1m.
Split-half on the frozen seeded day-split: all five positive on both
halves, 5m the most stable (+0.435 / +0.418).

**The advantage lives exactly where the trader operates.** As selectivity
loosens the books converge and 15m *improves* (+0.256 → +0.328) while the
LTF books decay. The raw comparison was measuring the ~20-trades-a-day
regime, which is not a regime anyone trades.

### WHY — and this is the useful part

The reversal is carried **entirely by room-to-run**. Drop that one filter
and the raw ordering returns:

| filter stack @2/day | 1m | 3m | 5m | 15m |
|---|---|---|---|---|
| risk + room + concordance | +0.264 | **+0.446** | +0.427 | +0.306 |
| room + concordance (no risk floor) | +0.256 | **+0.421** | +0.418 | +0.304 |
| risk + concordance (**no room**) | +0.050 | +0.168 | +0.165 | **+0.234** |
| concordance only | +0.043 | +0.169 | +0.165 | **+0.234** |

The mechanism is arithmetic and it explains prediction 3's refutation
rather than contradicting it. **At 15m the median next level sits only
0.40R away**, because the stop is so wide that everything is nearby *in R
terms* — so there is almost nothing for a room filter to select. At 3–5m
the same distances are 0.83R and 0.67R with a much longer right tail, and
the filter has real range to work in.

> **The tighter stop's payoff is not a bigger MFE. It is that room-to-run
> becomes a measurable, selectable quantity.** Prediction 3 said the
> excursion table would shift up; it did not, and it still has not. What
> shifts is the *selectability* of the population.

### WHAT THIS IS NOT

It is **fit-side and post-hoc**. The filter stack was assembled after
seeing the raw result; room-to-run was declared a reported column and
explicitly *not* a filter this pass, and concordance failed its own gate
bar. Two of the three filters are therefore being used in ways their own
declarations forbade for this pass. The split-half passes, but it was run
on an object chosen by looking, so it is a stability check, not a
confirmation.

**Nothing here ships.** What it does is reopen a family this document had
wrongly closed, and hand the next declaration a specific, mechanism-backed
hypothesis instead of a vague one.

## D7 — THE ONE LIVE LEAD (declared as a column, NOT acted on)

`next_lvl_R` — distance to the nearest other locus ahead of entry, in R —
splits the book hard, at every timeframe including the control:

| TF | EV, room ≥3R or open space | EV, room <3R |
|---|---|---|
| 1m | −0.050 | −0.081 |
| 3m | +0.207 | +0.006 |
| 5m | **+0.272** | +0.039 |
| 15m | **+0.287** | +0.138 |

With a 2pt risk floor (removing the degenerate-stop rows), as a gate with
the paired day-boot CI **on the lift**: TF=2 +0.185 [+0.011,+0.297] /
[+0.081,+0.359], TF=3 +0.212, TF=5 +0.214, all three clearing **both**
eras; TF=1 and TF=15 clear H2 only.

**It is not a confound in the flattering direction.** Small stops inflate
`next_lvl_R` (it is a ratio with risk in the denominator) *and* predict bad
outcomes — so the room-rich group is enriched in the population we just
showed to be the worst, and beats the book anyway.

**This is not a result.** D7 declared target-admissibility a reported
column and explicitly *not a filter this pass*; it was found by looking,
after the fact, across a table that also contains 168 other cells. It is
recorded here as the candidate that has earned the next blind declaration —
and it is Law 5 restated in the data: select on room-to-run, not on
likelihood of arrival.

## WHAT THIS PASS COSTS THE PROGRAMME, AND WHAT IT BUYS

**Costs:** the **1-minute** trigger is closed — it loses raw, it is worst
at every matched-selectivity rung, and it is the only TF that fails the
both-era check under selection. Condition (B), the trader's own momentum
requirement, adds nothing at any timeframe. *(The first draft closed the
whole LTF family here; that was withdrawn — see the correction at the top.)*

**Buys:**
1. **A mechanism, not just a ranking.** Room-to-run is worth roughly three
   times more at 3–5m than at 15m, and the reason is measurable and
   arithmetic: the 15m stop is so wide that the next level is a median
   0.40R away, leaving a room filter nothing to discriminate on. This is
   the most useful thing in the pass.
2. The flow question is closed. Weak, not mis-measured. That had been open
   since the beginning.
3. Everything BR-19..BR-26 was measured on is **re-validated as the right
   population** rather than being invalidated. The invalidation list in the
   declaration is withdrawn.
4. A stop-rule defect is now visible that was invisible at 15m, and it
   contaminates `closeloc` at every timeframe.
5. The trigger timeframe is now a **measured** dimension rather than an
   inherited convention — which is what the E1 declaration was actually
   weak on. It just did not resolve the way either side expected: 15m wins
   raw, 3–5m win selected.

## WHAT IS EXPLICITLY NOT DONE

- The **cross-TF union with a declared dedup rule** — D3 called it the
  necessary next pass. *The first draft cancelled it on the grounds that no
  LTF book was competitive. That cancellation is withdrawn:* 3m and 5m are
  competitive under selection, so the union is live again and still needs a
  declared dedup rule before it can be built.
- The **depth family at the LTF decision bar**. The staleness argument
  survives and now has a book to select inside. Still parked this pass —
  it needs its own declaration — but no longer parked "with cause".
- **Holdout look #1 stays HALTED**, and the reason has changed. It is no
  longer "the trigger set is closed": the trigger set is *reopened at 3–5m*.
  Spending the look now would burn it on a question the next declaration is
  about to reframe.

## THE NEXT DECLARATION, IN ONE LINE

Blind, before any of it is measured: **at 3m and 5m, does a room-to-run
gate clear +0.05R marginal lift with both-era CIs, per session, at matched
trades/day against the 15m control?** Everything in the matched-selectivity
section is the hypothesis, not the answer.
