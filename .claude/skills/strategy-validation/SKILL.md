---
name: strategy-validation
description: A staged pipeline for turning a discretionary trading setup into a mechanically-specified, statistically-validated automated strategy — covering specification lock, population build, lookahead and row-existence gates, base rates, fill modelling for limit entries, session splits, pre-declared cut studies, order-flow layering, loser autopsy, and holdout confirmation. Use this whenever the user is validating, backtesting, auditing, or automating a trading strategy; researching a trader's model from transcripts, charts or courses; adding order flow (CVD, delta, footprint, depth/heatmap) to an existing setup; investigating why a backtest looks too good; deciding whether a finding is real or overfit; or building a spec for a trading bot. Trigger it even when the user only asks a narrow piece of this — "test my entry", "does this edge hold", "what times does this work", "can you tell winners from losers" — because the staged order and the gates are what prevent the usual failure modes.
---

# Strategy Validation

A pipeline for converting a discretionary setup into an armed mechanical strategy without fooling yourself.

The default failure mode is not a bad idea — it is a good idea measured wrongly. Almost every dead strategy died of one of five things: lookahead in the entry or the features, a population conditioned on a future event, a denominator that bought hit rate with stop width, pseudo-replication inflating significance, or an objective function that did not match how the account actually pays. The stages below are ordered so each of those is caught before it can contaminate what follows.

## Core principles

**Denominate in something scale-free.** Point and dollar thresholds silently change meaning as volatility drifts. A fixed stop buffer that is sane at one volatility level is noise-triggered at another. Express thresholds as a fraction of a measured width (ATR, band width, wick width) and *report* results in R and points so a human can read them.

**Anything correlated with stop width must be tested in R, never in hit rate.** A variable that narrows the stop buys hit rate through the denominator while destroying expectancy. This kills more candidate variables than any other single check.

**Select on room to run, not likelihood of arrival.** Variables predicting that price will *reach* a nearby level also predict congestion at that level, and congestion caps the tail. Confluence counts, level density and proximity measures are usually arrival predictors. Expect them to show strong hit-rate lift and flat-or-negative R.

**Gates convert lift; weights bleed it.** A filter that removes a trade converts its edge roughly one-for-one into expectancy. A sizing weight loses most of it in the rank transform and bucketing. Prefer cuts to weights — but a cut needs a bar declared before it runs, because a cut is a hypothesis.

**Deduplication is not selection.** Collapsing the same setup seen on four timeframes into one row is a counting fix that moves confidence intervals, not expectancy. It needs no declared bar because it is not a hypothesis. A cut changes expectancy and does need one. Never let a dedup rule get the ceremony of a cut, or a cut skip it.

**Compute the effect-size arithmetic before building anything.** Work out what a variable can be worth through the mechanism you intend to use it in, and compare that to the gap you are trying to close. A correlation of 0.12 pushed through a sizing ladder yields roughly 0.01R; if the gap is 0.05R, the build is pointless before it starts. This applies to confirmability too: know in advance whether the effect you are hunting is large enough to be confirmed on the holdout you actually have.

**Independence is measured in days, not minutes.** Trades in one session share the regime, the level set and the profile. Use a day-level block bootstrap for intervals. A clock window mis-measures separation for the same reason a point threshold mis-measures distance.

## The pipeline

Work through these in order. Each stage has an exit condition; do not carry a failed stage forward by loosening it.

### Stage 0 — Specification lock

Get the setup written down as something a machine could execute with no judgement left over, and confirm it with the trader before touching data.

Extract from whatever sources exist (their own annotated charts are worth more than any transcript, because they show what the trader actually does rather than what they say):

- The **object**: what price structure defines the level? Be exact — "the wick of the prior swing low on the trading timeframe" is a specification; "a key level" is not.
- The **selection rule**: when several candidate objects exist, which one? This is where discretionary setups hide most of their judgement.
- The **context/bias**: what makes the setup permitted at all, and is it derived from structure, an indicator, a session, or a higher timeframe?
- The **trigger**: the precise event, including whether it must occur in a single bar or may accumulate.
- The **entry**: market at next bar open, or a resting limit at a stated price? This choice determines the entire validation approach (see Stage 3).
- The **stop**: anchored to what, with what buffer, expressed in what units?
- The **target**: fixed R, structural level, or nearest opposing feature? And is there a minimum-R condition?
- The **timeframe**: one declared timeframe, or several?

Then read the specification back to the trader and ask what is wrong with it. Two things reliably surface: rules they follow without having stated them, and rules they stated that they do not actually follow.

**Watch for a target or entry rule that is secretly a geometry filter.** If entry sits at a fraction of the object and the stop sits just beyond the object's far edge, stop distance is a function of the object's *width*. If the target is then a fixed price, R is mechanically determined by that width — so a "minimum 1R" condition is really a filter on object width relative to distance-to-target. It may be excluding the widest, most violent examples, which are often the best ones. Name it, make it explicit, and test it as its own hypothesis.

**Exit condition:** the trader confirms the spec, and every rule is executable without a human looking at the chart.

### Stage 1 — Population build

Build one row per event, unconditionally. This is the stage where most fatal defects are introduced, so it gets three gates before merge. See `references/gates.md` for the full procedures.

Requirements:

- **Rows exist unconditionally.** If an event only appears in the table when some later thing happened, the population is conditioned on the future. The classic version: recording a break only when a retest followed, so breaks that ran away are invisible — in live trading those are the no-fills and the missed winners. Fix by creating the row at the trigger and making the later event an outcome *column*, not a precondition.
- **Features computed as of the decision bar, entry on the bar after.** Assert it, do not assume it.
- **A convention check against a deliberate overlap period** for every new data source before merge. Sign conventions (delta as bid-minus-ask versus ask-minus-bid) invert silently and will pass a fit-era sanity check while destroying the holdout.
- **Sealed rows written unread.** Split the span up front, write the holdout to disk without inspecting it, and record the partition in a committed declarations file.
- **An exclusion log.** Any quarantined rows need a written criterion and a demonstration that the criterion is outcome-independent. Calendar-based exclusions are fine; anything correlated with outcomes is a selection effect baked into the population.

**Exit condition:** all three gates pass, the exclusion criterion is in writing, and the holdout partition is committed.

### Stage 2 — Base rates before any conditioning

Measure what the unselected population does. Skipping this is how a strategy gets credited with an edge that is just the base rate of the market.

Produce: the trigger frequency per session, the raw win rate at the declared target, the stop-width distribution, and — most importantly — the **MFE and MAE distributions in R**, at least the median, 75th, 90th and 95th percentiles.

The MFE distribution determines the entire exit design and is routinely skipped. A median MFE near 1R with a 90th percentile above 6R tells you a near target takes the bottom of the distribution, a pure hold gives the tail back, and a partial-plus-runner banks the median while keeping the optionality. You cannot design an exit without this table.

Record every null in a base-rate library so nobody re-proposes it.

**Exit condition:** base rates and the MFE/MAE table exist for the whole population and per session.

### Stage 3 — The raw trigger book, and the fill model

Run the specification exactly as written, with realistic costs, and see what it does before adding anything.

**If the entry is a market order at the next bar's open**, this is straightforward — but verify the entry price with a perturbation aimed at the *price*, not the features. Flatten every bar after the decision bar to the previous close and assert the entry price moves. A feature-perturbation gate cannot catch an entry price read off the decision bar, because it passes identically either way.

**If the entry is a resting limit**, the fill model is the whole ballgame and needs its own treatment:

- Log every **qualified setup at the trigger**, then tag filled versus unfilled. Never log at fill.
- Report the **fill rate** as a first-class statistic.
- Measure the **no-fill opportunity cost**: how far did the unfilled ones travel? If the setups that never retrace are the larger winners, the filled sample is adversely selected and the limit entry is costing more than it saves. This single query can invalidate the entry design.
- Require **trade-through, not touch**. An exact touch is not a fill; orders ahead in the queue may absorb everything at that price. Book a fill only if price trades at least one tick beyond the limit, and stress-test at two ticks with partial fills.
- Run a **market-entry control** on the same population. If the market version is roughly break-even and the limit version is positive, the entire edge is fill price improvement — which means the fill model is load-bearing and must be calibrated against depth data rather than assumed.

Cost every trade. Net costs inside the R numerator; keep hit-rate tables gross by design and say so.

**Exit condition:** the raw book's expectancy is known in R and points, with the fill rate and no-fill opportunity cost reported, and the entry-price perturbation passes.

### Stage 4 — Geometry and exit

Fix the mechanical defects before hunting for edge, because everything measured later is conditional on these choices.

- Replace fixed point buffers with a fraction of a measured width, with a tick floor. Grid a small number of declared values; do not sweep.
- Test the exit shape against the MFE table from Stage 2: fixed targets at several R, structural targets, pure hold with stop, and partial-plus-trail. Choose from the **interior of a plateau**, never the argmax and never a grid edge — a winner at the edge of the grid means the grid was mis-sized.
- If a minimum-R condition exists, test it as an explicit hypothesis rather than leaving it as an invisible geometry filter.

Be aware that exit and selection can fight each other. An exit that banks most of the position early truncates the tail, so a tail-predicting variable will re-price much weaker under it. If both are being optimised, optimise them jointly as a declared factorial, not sequentially.

**Exit condition:** stop and exit are scale-free, chosen from a plateau interior, and re-validated across period folds.

### Stage 5 — Session and time-of-day

This is usually the largest single effect available and it costs nothing but a split.

Split expectancy in R by session and by intraday bucket. Report, do not filter, unless the split was declared in advance — post-hoc session selection is exactly the cherry-picking the discipline exists to prevent.

Two things worth knowing before interpreting the result. Liquidity sets a floor on viability: if median spread exceeds roughly fifteen percent of median R in a session, a low-R strategy cannot survive there regardless of hit rate, so compute spread-over-R per session first. And a clock-anchored grid drifts against the flow it is proxying whenever daylight-saving regimes diverge between regions — anchor session logic to the local time of the market generating the flow, or to the actual event calendar.

**Test any clock-based claim with a boundary placebo.** Where a framework asserts special times, split the boundaries into those coinciding with genuine scheduled flow (cash opens and closes, scheduled data releases, benchmark fixes, auctions, settlement windows) and those with nothing behind them. If the effect lives only at the event boundaries, the framework is a proxy for the calendar and should be replaced by it. If it is uniform across both, the clock is telling you something and is worth holdout spend.

**Exit condition:** per-session expectancy in R and points, spread-over-R per session, and a boundary placebo result for any time-based claim.

### Stage 6 — Cut study on bar-only variables

Now hunt for selection, using cuts rather than weights, on variables that need no special data — so the finding can be confirmed on the widest holdout available.

Discipline that makes this credible:

- Enumerate candidates and **pin every declaration before contact with data** — the variable, the cut direction, the bin structure, the bar.
- Declare cuts off an existing bin structure (bottom bin, bottom quartile). Never sweep the threshold.
- Use a **seeded split-half**: derive on half one, then attempt to kill on half two. A high kill rate on the second half is the best evidence you have that the test was real rather than permissive. Report it.
- Score survivors on period folds and day-level clustering, and check the maximum single-day contribution — a finding carried by one day is a day, not an edge.
- **Score on both axes.** A cut that raises expectancy while halving trade count can reduce the number of qualifying days. Frequency is not free.
- Separate arms that are structurally different bets. A continuation setup and a reversal setup at the same level are different claims about what happens next and will have different validators; pooling them averages a positive and a negative.

**Exit condition:** survivors pass the pre-declared bar on the second half, on period folds, and on clustering — or the family is recorded dead in the base-rate library.

### Stage 7 — Order flow

Order flow goes late for a reason: it usually has the narrowest data coverage, so it has the weakest holdout, and law of effect-size arithmetic says know your confirmability before you start. See `references/orderflow.md` for what each family can and cannot measure, and for the resolution limits that determine which questions are answerable at all.

Before running anything, compute the confirmable effect size on the flow holdout you have. If it is around twenty percentage points and the candidate effects are around ten, pre-commit that a sub-threshold finding is recorded as interesting-but-unconfirmable and validated forward on live recording instead — and start that live recorder immediately, because every day without it is uncontaminated forward data lost permanently.

Aim the flow search at large effects. A property present in most losers and few winners is enormously significant and confirmable on a short holdout; a ten-point win-rate shift is not.

**Look for a bar-only proxy for any flow finding.** If a pure-OHLC variable captures most of a flow variable's effect, the same idea becomes testable on the much wider bar-only holdout. Close location within the bar's range, for instance, is a natural proxy for aggressive-side dominance. This is often the cleanest route to a confirmable version of the first thing that survives.

**Exit condition:** flow findings are either confirmable and confirmed, or explicitly recorded as forward-validation candidates.

### Stage 8 — Loser autopsy

Ask what distinguishes losers from winners. This is where the largest effects usually live, and it is also the stage most vulnerable to a specific error.

The threat is not multiplicity — a property in ninety percent of a thousand losers versus thirty percent of a thousand winners is enormously significant, far beyond any reasonable correction. The threat is **pseudo-replication**. A few trades per day over a few hundred days means a day-level property masquerades as a trade-level one: ninety percent of losers could be ninety percent of twenty bad days. Run the within-day versus between-day variance decomposition before believing anything.

Discipline: the autopsy is exploratory, so it cannot be priced by the multiple-testing corrections that need an enumerable trial count. That means its output is **hypotheses, not findings**. Anything the autopsy surfaces re-enters at Stage 6 as a pre-declared cut with its own bar, on data the autopsy did not touch.

**Exit condition:** autopsy hypotheses are written down and queued as declared cuts, with the pseudo-replication check done.

### Stage 9 — Holdout confirmation

One look, declared in advance.

- Declare the **aggregation rule before opening anything**: pooled with a single interval, or sign-agreement across all period folds, or a stated minimum fraction of folds. A long holdout span contains multiple volatility regimes, and a mixed result invites sub-selecting the favourable stretch — which is precisely what the one-look rule exists to prevent.
- **Split a long holdout into blocks and require both to pass.** This is stricter than one pooled look, so it is not a weakening; it catches internal regime flips automatically, and it converts one bit into two so a marginal first result is not automatically terminal.
- **Partition venues by family.** If flow-covered months sit inside the bar-only span, whichever family looks first contaminates the other. Assign the flow-covered months exclusively to flow and the remainder exclusively to bar-only, so both looks land on data virgin for their own family.
- Record the result whatever it is. A failed holdout is a permanent finding, not an invitation to re-tune.

**Exit condition:** the declared bar is met on the declared venue, or the strategy is recorded dead.

### Stage 10 — Arming

Score on the objective the account actually pays on, not per-trade expectancy. For a funded or prop account with a hard failure condition, the objective is the probability of reaching the payout state before the failure state — which is path-dependent, and ranks strategies differently from expectancy. See `references/prop-objective.md`.

Then: paper-trade forward with live recording, compare live fills against replay to measure the execution gap, and only scale size once the forward record matches the backtest within its stated interval.

## Reporting

Lead with R and points. Derived or normalised units (band widths, sigma, standardised scales) are fine as working units but should never carry a headline on their own — a result stated only in a derived scale is unreadable to the person who has to decide whether to risk money on it.

For every claim, separate what was **measured** from what was **asserted**. When the only source for a claim is an educator or a vendor with no dataset behind it, say so and treat it as unverified rather than laundering it into evidence. Flag claims that cannot be falsified as stated, and either convert them into a level plus a forward-return test or discard them.

Keep a trial ledger: every hypothesis, its declared bar, and its verdict. Nulls are the most reusable output the process produces.
