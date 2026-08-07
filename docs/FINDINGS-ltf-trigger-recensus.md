# FINDINGS — LTF TRIGGER RE-CENSUS (the conjunction)

Run 2026-08-07 against `DECLARATIONS-ltf-trigger-recensus.md`, which was
written and committed (`d47cfc4e`, amended `f675e39f`) before a single row
existed. Fit span 2025-06-01..2026-07-14, 291 session days, 81,457 triggers
with outcomes. **Holdout look #1 remains HALTED and unspent.**

## THE HEADLINE

**The 15-minute trigger candle is not a legacy convention that was never
tested. It is the best of the five timeframes measured, and the ordering is
monotone.**

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

## WHY THE LTF BOOK LOSES: the stop RULE, not the timeframe

Two mechanisms, both measured:

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

**Costs:** the LTF trigger family is closed. The conjunction — the
trader's own stated grammar — does not beat the incumbent at any of the
four timeframes it was tested at, and the shortest one loses money.

**Buys:**
1. The 15m trigger is now **defended by measurement** rather than by
   comparability with an incumbent. That was the actual weakness in the E1
   declaration and it is now repaired.
2. The flow question is closed. Weak, not mis-measured.
3. Everything BR-19..BR-26 was measured on is **re-validated as the right
   population** rather than being invalidated. The invalidation list in the
   declaration is withdrawn.
4. A stop-rule defect is now visible that was invisible at 15m, and it
   contaminates `closeloc` at every timeframe.
5. One live, well-powered, mechanism-consistent lead (D7 room-to-run).

## WHAT IS EXPLICITLY NOT DONE

- The **cross-TF union with a declared dedup rule** — D3 called it the
  necessary next pass. Given that every LTF book is worse than the 15m
  control, a union of them is not worth building; the necessity was
  conditional on an LTF book being competitive, and none is. Recorded as
  **cancelled with cause**, not as skipped.
- The **depth family at the LTF decision bar**. The declaration argued
  15m snapshots were up to 15 minutes stale. That argument survives, but
  with every LTF book losing to the 15m control there is no book for a
  depth gate to select inside. Parked with cause.
- **Holdout look #1 stays HALTED.** The locus set is closed; the trigger
  set is now closed too. What is not settled is D7, and spending the look
  before that is declared would waste it.
