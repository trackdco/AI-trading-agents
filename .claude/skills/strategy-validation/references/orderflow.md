# Order flow: what each family can measure, and what it cannot

Order flow is the most over-claimed area in retail strategy material and one of the least validated in the literature. Almost every specific claim about delta, absorption and depth is practitioner lore with no published effect size. That does not make it wrong — it makes it a set of testable hypotheses, and if you hold the data you are in a position most people are not. Treat it accordingly: hypotheses until your own pre-declared test returns a number.

## The two distinct data objects

These are constantly conflated and they answer different questions.

**Trade prints (the footprint / time-and-sales).** Every execution with its price, size, and which side was the aggressor. Supports: volume at price, delta, cumulative delta, imbalance stacking, absorption measured as aggression that fails to move price.

**Book state (market-by-price, typically ten levels).** The resting limit orders at each price at a point in time. Supports: depth, walls, book imbalance, thinness ahead of price.

**Establish which one you actually have before designing anything.** A depth feed carries no aggressor information, so it cannot produce delta. A trade feed carries no resting liquidity, so it cannot produce walls. Verify by inspecting the raw files rather than trusting a description — a file described as order flow may be book-state only, and any spec built on the assumption it contains aggression will fail at implementation.

## Resolution limits that determine which questions are answerable

**Depth is censored at whatever level count the feed provides.** A ten-level feed cannot see a wall beyond ten levels. This biases both wall detection and absorption estimates, and the bias is not random — it is worst exactly when the book is thin and levels are wide, which is often the regime of interest.

**Snapshot frequency sets a floor on what is observable.** One snapshot per minute cannot resolve a sub-minute event. Anything shorter-lived than the snapshot interval — a fleeting wall, a spoof, an absorption episode inside a single bar — is simply not in the data. Do not design a feature that requires resolution the feed does not have; compute what the feed can support and say what was given up.

**Coverage is three-dimensional: period, session, and data type.** Coverage often differs across all three, and a single-dimension answer will mislead. Footprint and depth may have different spans. A session may have depth for one part of the day and not another. Build a coverage manifest as period-by-session-by-type before committing to a research order, because it determines which family can be confirmed at what effect size — and whether a given strategy has any holdout at all.

## The families, and what each is a hypothesis about

**Cumulative delta and delta divergence.** The claim: a break with delta expanding in the break direction continues; a break where price makes a new extreme while delta does not is unconfirmed and reverses. Mechanistically coherent — it is a statement about whether aggression is driving the move or the move is drifting on thin liquidity. No published effect size. Testable as a cut on the decision bar's signed delta agreeing with trade direction, which is about the cheapest flow hypothesis available.

**Absorption.** The claim: heavy aggression into a level that fails to move price indicates a large resting participant, and price reverses. Requires both objects — aggression from prints, resting size from the book — so it is only measurable where both feeds overlap. Verify feasibility before specifying it.

**Resting walls and thinness ahead of price.** The claim: a thick opposing wall caps the tail; a thin book ahead means room to run. This is the one flow family that speaks directly to *room to run* rather than arrival, which makes it unusually valuable given that arrival predictors are abundant and tail predictors are scarce. Censoring at the feed's level count is the main threat to measuring it honestly.

**Imbalance stacking in the footprint.** The claim: consecutive price levels showing lopsided aggression indicate initiative. Highly collinear with delta and with displacement-quality measures on the same bar — do not count it as an independent confluence alongside those.

**Volume at price / profile structure.** Low-volume nodes as accelerants and high-volume nodes as barriers is the most mechanistically defensible profile claim: price crosses thin, un-traded prices quickly because there is no resting inventory to slow it. Derivable at coarse resolution from bar volume, at fine resolution from prints.

## Sequencing rules

**Compute confirmability first.** Flow coverage is usually the narrowest, so the flow holdout is the weakest. Work out the minimum effect size that venue can confirm before running anything, and aim the search at effects of that magnitude or larger. A property present in most losers and few winners is confirmable on a short span; a ten-point win-rate shift generally is not.

**Pre-commit the unconfirmable outcome.** Declare in advance that a finding which passes fit but sits below the holdout's resolution is recorded as interesting-but-unconfirmable, is not fought over, and does not spend the look. Without that declaration in writing, the temptation to spend the look on a marginal result is very hard to resist.

**Hunt for a bar-only proxy for anything that survives.** If a pure-OHLC variable captures most of a flow variable's effect, the idea becomes testable on the much wider bar-only holdout. Close location within the bar's range is a natural proxy for aggressive-side dominance — a bar closing near its extreme had pressure in that direction. This is usually the cleanest route to a confirmable version of a flow finding, and it is worth checking before assuming flow data is required at all.

**Start a live recorder immediately, whatever else is happening.** Forward flow data is the only uncontaminated venue that grows, and every day without recording is a day of it lost permanently. For any finding that cannot be confirmed on the historical flow span, forward validation is the fallback — and it only exists if the recorder was started.

**Flow goes last in build order but is not permanently capped.** If holdout coverage includes flow months, flow findings can eventually be load-bearing rather than forever a modifier. Sequencing it last is about confirmability economics, not about flow being second-class.

## Reporting flow findings

State the data object required (prints, book, or both), the resolution assumed, the coverage the test ran on, and the effect in R and points. Separate the measured effect from the mechanistic story offered for it — the story is what makes it worth testing, not evidence that it works.
