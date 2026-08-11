# The pre-merge gates

Three procedures that run before any analysis touches a newly built population. Each one exists because it has caught a defect that would otherwise have been invisible until the strategy lost money live — or worse, would have produced a false null on a holdout that can only be spent once.

## Gate 1 — Row existence under perturbation

**What it catches:** a population conditioned on a future event.

**The failure mode.** Suppose the table records a level break only when a retest followed. Breaks that ran away without retesting never get a row. The resulting comparison — "break-and-retest outperforms immediate rejection" — compares a population conditioned on a future retest against an unconditioned one. In live trading the missing rows are no-fills, and if price ran away without you, that is a missed winner. The measured advantage is an artifact of which rows exist.

**The procedure.** Perturb everything strictly after the decision bar — replace subsequent bars with the previous close, or randomise them — and rebuild. Assert that the **set of row keys is identical**. If rows appear or vanish, row existence depends on the future.

**The fix.** Create the row at the trigger, unconditionally. Make the later event an outcome *column* (a boolean flag plus its own timing and outcome fields), never a precondition for the row existing. Then the fair comparison becomes available: the conditional probability of the later event as a fill rate, plus the outcomes of the cases where it never happened as opportunity cost.

**Related trap.** An analysis parameter that silently determines row existence is a mild cousin of the same defect. Capping an attempt counter at four means the fifth-and-beyond stratum never exists, so any null measured on "persistence" was measured on a truncated range. Check every cap.

## Gate 2 — Entry price perturbation

**What it catches:** an unachievable fill price.

**The failure mode.** A feature-perturbation gate tests *features*. If the entry price is the decision bar's own close, perturbing later bars does not change it either — so the gate passes identically whether the entry is achievable or not. It structurally cannot verify the fill. Nothing else in a normal build does either.

**Three cases, only one clean:**

1. **A limit filled mid-bar with features read at bar end.** Fatal. This is the classic strategy-killer: the features knew how the bar resolved and the fill did not have to wait for it.
2. **Entry at the decision bar's close.** Not a feature lookahead, but optimistic — it fills at a print you only knew was final after it printed, and it is biased by the close-to-next-open gap.
3. **Entry at the open of the bar strictly after the decision bar.** Clean.

**The procedure.** Flatten every bar strictly after the decision bar to the previous close, then assert the entry price *moves* to that flat value. If it does not move, the price is being read off the decision bar. Add a hard row-level assertion: entry price equals the open of the bar strictly after the decision bar, on every row, and no entry price equals any decision-bar price.

**A subtle version worth checking explicitly.** Any level computed from a developing indicator embeds the current bar. A twenty-period moving average that includes the current bar shifts by exactly one-twentieth of the current bar's close change — so a limit placed at that average embeds the fill bar's own close. The signature is an offset of precisely delta-close divided by the period.

**Consequence to state out loud.** Verifying case 3 makes the *market-entry* version honest. If the trader actually uses limits, the validated model is not the traded model, and that gap has to be decided deliberately rather than inherited by default: trade market and accept the average fill, or trade limits and accept a fill model that carries a queue assumption. Both are defensible; silently validating one and trading the other is not.

## Gate 3 — Convention check against a deliberate overlap

**What it catches:** silently inverted or mis-scaled fields in a newly merged data source.

**The failure mode.** Signed order-flow fields have no universal convention. One extraction computes delta as ask-minus-bid; another as bid-minus-ask. Merging a new span using the opposite convention produces a dataset where one era's signs are flipped relative to another's. If the flipped era is a small part of the fit set, fit results look mostly fine — while the holdout, if it came from the flipped extraction, is entirely inverted. Any finding that passes fit then fails the holdout with the *opposite sign*, and the conclusion reads as "this does not generalise." That is a false null on the one test you only get to run once, and it is indistinguishable from a real failure.

**The procedure.** Require an overlap period present in both the old and new extraction. Recompute the field both ways on the overlap and assert agreement to a stated precision. The gate only works if an overlap exists, so preserve one deliberately whenever a source is extended.

**Standing practice.** Every new data source gets a convention check against an overlap before merge — not after, and not as a spot check on a few rows.

**Watch the era of the overlap.** Validating a convention against a fit-era overlap does not validate a sealed span that came from a different extraction. That needs its own check — which is a data-*format* check, verifiable without unsealing any analysis.

## After the gates: the deduplication question

Not a gate, but it belongs here because it is a population property rather than a finding.

When the same move triggers on several timeframes within minutes, those are not independent observations — they are one setup seen at different resolutions, and the trader was only ever going to take one. Left unhandled, the row count is inflated and every confidence interval is too narrow.

**Measure before choosing a rule.** Take all trigger pairs in the same session and direction and plot the joint distribution of time gap and price gap. Multi-timeframe duplicates should appear as a spike at tiny time gaps with near-zero price difference; genuine repeat setups as a separate mode. If there is a valley between the modes, that is the threshold — measured, not assumed. If there is no valley, record that as a miss and fall back to a threshold declared from the strategy's own grammar rather than an arbitrary round number.

**Prefer a structural criterion to a clock window.** Triggers separated by an intervening excursion away from the level are separate events; triggers with no excursion between them are one event seen at different resolutions. This handles closely spaced genuine re-entries correctly while still collapsing simultaneous multi-timeframe firings — and it avoids the failure of a clock window, which mis-measures separation for the same reason a point threshold mis-measures distance.

**Keep the count as a column.** The number of timeframes that fired is itself a candidate variable, and often one the trader already uses implicitly as confirmation. Collapse to one row and retain the count.

**Sensitivity is mandatory once a collapse convention is load-bearing.** Different conventions carry opposite cluster-size gradients, and equal-weighting against size-weighting can swing the mean expectancy substantially — enough to dwarf the effect being hunted. Report the book across a range of threshold values. If the result holds across the range it is real; if it holds only at the chosen value, it is an artifact of a bookkeeping decision, and every downstream selection result is confounded with it.

**Independence is a separate job from deduplication.** Dedup identifies the same setup. Independence is for confidence intervals, and the right unit there is the day. Use a day-level block bootstrap rather than literally collapsing to one row per cluster — collapsing is conservative but discards within-day variation, and the bootstrap gives honest intervals while keeping it.
