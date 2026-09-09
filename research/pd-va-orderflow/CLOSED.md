# CLOSED — "daily bias / value-area levels / order-flow execution" (2026-09-09)

**Decision, Angus, 2026-09-09: closed.** The video's method, written as rules and tested where the
repository's data allows, produced nothing to build on.

| claim | test | result |
|---|---|---|
| Bias from the 09:30 open vs the prior cash value area is 70–80% accurate | `bias_accuracy.py`, 1,809 sessions 2018-08 → 2026-09 | **49.1%** on directional days; the plain gap rule 50.1%; bearish calls wrong 55% of the time |
| Order-flow confirmation at the level (absorption → aggression + imbalance → inversion) produces high-probability entries | `PREREGISTRATION-4.md`, `orderflow_test.py`, 13 months of aggressor-tagged footprint, 8 readings + unfiltered baseline | **NOT DEMONSTRATED**: 7 of 8 readings negative, PF 0.92–1.04; win rate up from ~20% to ~30%, expectancy unchanged; the level with no order flow is zero too |
| Gamma levels add "insane accuracy" | — | untestable, no historical data |

One lead, not a rule: fades on days that open inside the prior value area (the only positive cells,
n=91; inside-open days close inside value 30% vs a 21% base rate). Would need data none of this
has touched.

Files: `EXTRACTED-RULES.md` (the method as rules, gaps marked, §11 bias test),
`PREREGISTRATION-4.md`, `RESULTS-4.md`, `bias_accuracy.py`, `orderflow_test.py`,
`BIAS-ACCURACY.txt`. Footprint files and the raw tape are not committed (regenerable from the
newer branches).
