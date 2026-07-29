# PART 3 PRE-REGISTRATION — the give-back gap
### Written and committed BEFORE any Part-3 statistic was computed. 2026-07-29.

**Origin.** The Part-1 / microstructure descriptive pass reported give-back (reaching +1R and
finishing red) at roughly 20% / 18% / 7% across early / mid / late segments. That was a
descriptive observation on all 182 trades. This part asks whether the difference survives a
noise floor.

**Question (frozen).** Does give-back differ by pre-market segment beyond chance?

**Segments (frozen, no re-bucketing, no edge-moving):**
`early 08:00-08:29` | `mid 08:30-08:59` | `late 09:00-09:29` — the registered half-open bins,
identical to every prior round.

**Two rates, both frozen now:**
* **PRIMARY — conditional give-back:** `P(finished red | reached +1R)`. This is the actual
  give-back rate: of the trades that got into profit, what share handed it back. Denominator is
  trades with `mfe_life >= 1.0` in that segment.
* **SECONDARY — unconditional:** `P(reached +1R AND finished red)` over all trades in the
  segment. This is the figure quoted descriptively and is carried for continuity.

**Primary test statistic (frozen):** the difference in conditional give-back rate between the
`early` and `late` segments — the two extremes named in the original observation.
**Secondary statistic:** max-minus-min of the conditional rate across all three segments.

**Noise floor (frozen):** day-block permutation, **2,000 draws**. Segment membership is a fixed
property of a trade's fill time and is never permuted. The permutation shuffles the OUTCOME
labels in whole-day blocks, preserving within-day clustering while breaking any association
between segment and give-back. p is the share of draws whose statistic is at least as extreme
as the observed one.

**Reported regardless of outcome:** the effect size in percentage points, a day-clustered
bootstrap 95% CI (4,000 draws), the permutation p, and the sample size required for 80% power
at the observed effect. Cells under 10 trades are marked insufficient and are not given numbers.

**Decision rule (frozen):** p < 0.05 against the day-block noise floor AND a CI excluding zero
is required to call it established. Anything else is reported as INCONCLUSIVE, with the sample
that would settle it stated. No threshold, segment edge, or definition may be changed after
seeing the result.
