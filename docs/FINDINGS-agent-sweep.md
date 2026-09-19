# FINDINGS — THE AGENT SWEEP: a calibrated null

2026-08-08. Five agents, ~11,500 statistical tests across every
decision-time variable on the corrected (episode-M1) race census,
reported per session and never pooled. Declaration:
`docs/DECLARATIONS-agent-sweep.md`, committed before any agent read an
outcome. Fit-only, no holdout, report-only, nothing adopted.

## THE HEADLINE: THE SURVIVAL RULE PASSES ~5% OF PURE NOISE, AND THE REAL DATA SITS INSIDE THAT RANGE

The single most important number in this pass is not a finding — it is
the calibration of the filter. The identical machinery was run on
**permuted data**: outcomes shuffled within each (session × mechanism)
cell, destroying every predictor–outcome relationship while preserving
cell sizes, outcome distributions, and every predictor's own
distribution.

| | tests | CI-clears | SURVIVORS (all five tests) |
|---|---|---|---|
| **REAL DATA** | 2,646 | 181 (6.8%) | **130 (4.9%)** |
| null, 5 permutations | 2,646 | 162.6 ± 15.9 | **112.0 ± 17.1** (range 86–**135**) |

**The real data's 130 survivors sit squarely inside the null's range —
z = +1.05, and one permutation produced MORE survivors (135) than the
real data did.** The five-test rule passes roughly one test in twenty
whether or not any signal exists.

Worse for the candidate list: **32 of the 130 real survivor labels
(variable × cell) also appear as survivors on shuffled data in at least
one of five permutations.** Nearly a quarter of the "findings" are
combinations that survive when the outcome is random.

Every survivor count reported below must be read against that baseline,
and none of them clears it.

*(The null is conservative by construction: permutation destroys
within-day outcome correlation, narrowing the day-clustered bootstrap
and inflating the null's counts. A real count that merely matches the
null is certainly noise.)*

## FOUR INDEPENDENT AGENTS REACHED THE SAME PLACE BEFORE THE CALIBRATION EXISTED

| sweep | tests | clears | FP budget | verdict reached independently |
|---|---|---|---|---|
| LONDON | 882 | 69 | 44 | 52 survivors → 41 clusters; **7 of 10 strongest failed alternate thresholds** |
| NY_PRE | 981 | 57 | 49 | 37 survivors → 23 clusters; "mostly null" |
| NY_AM | 882 | 58 | 44 | 42 survivors → ~26 clusters → 3–5 constructs |
| interactions | 6,300 | 389 | 315 | 326 survivors ≈ budget; **zero certified** |
| regime/day | 1,635 | 84 | 68–82 | **zero fully validated** |

Every agent, working separately and without sight of the others,
landed on "at or near the false-positive budget." The calibration then
confirmed the budget itself was the whole story.

## THE ONE PIECE OF DIFFERENT EVIDENCE, ALSO KILLED

LONDON's strongest candidate was not a single CI but a **magnitude
match across three mechanistically distinct constructions**:
`ma15_slope30_w` at −0.225 / −0.242 / −0.233 in M1 / M2 / M3. A
survivor count cannot address that kind of evidence, so it was tested
directly — how many variables achieve same-sign, similar-magnitude
agreement across all three mechanisms, real versus permuted?

| session | real | null (5 perms) |
|---|---|---|
| LONDON | 3 | 1.8 ± 1.3 (max **4**) |
| NY_PRE | 3 | 0.8 ± 1.2 (max 3) |
| NY_AM | 1 | 1.4 ± 1.4 (max 3) |

**Real is within one standard deviation of the null in every session,
and a null permutation produced MORE cross-mechanism agreement in
LONDON (4) than the real data did (3).** The cross-mechanism match is
noise too.

*(A mechanistic note that would have complicated this finding even had
it held: BR-17 already documents this book carrying a
−0.0155R-per-1%-NQ slope. A negative MA-slope effect would plausibly be
the intraday expression of that known regime tilt rather than a new
selector.)*

## THREE DEFECTS AND WEAKNESSES FOUND, TWO OF THEM MINE

1. **`out_pts` was left in the predictor list** — the outcome itself
   re-scaled (out × risk), so it "survived" tautologically in every
   cell it touched. **Caught by the NY_PRE agent, not by me**; module
   fixed, remaining agents alerted mid-run, counts restated. My defect.
2. **The declared split-half test is NOT independent of the CI test.**
   The two halves *compose* the full-sample effect, so conditional on
   the full CI clearing, the halves usually agree by arithmetic — which
   is why ~72% of clears passed it. The rule looked like five filters
   and behaved like roughly two. My declaration error, and the direct
   cause of the misleading survivor counts.
3. **Threshold fragility is unfiltered by the rule.** The LONDON agent
   re-tested its 10 strongest candidates at alternative cuts: **only 3
   held every cut**; one passed all five tests at the median then
   failed both alternates outright, and another flipped to mechanically
   risk-coupled in the tails, revealing coupling the median split hid.
4. **82% of "interaction survivors" were main-effect bleed-through** —
   a predictor clearing under many different correlated conditioners
   regardless of which one cut the cell (interactions agent's finding).

## THE CLEAN NEGATIVES WORTH KEEPING

These are real results, not absences of results:

- **Time-of-session does nothing at the cash open.** `tmin` fails at
  the median in all nine NY_AM cells; a 36-test sweep of non-median
  cuts, including first-15-minutes-vs-rest, produced one isolated
  survivor that does not replicate at adjacent cuts.
- **No streak or tilt.** 162 tests on prior-trade outcome variables;
  `prev_out_sess` is a complete null (0 of 54 clears). This grammar's
  mechanical fills carry no day-level autocorrelation.
- **No cross-session carry.** `london_out_today` clears in exactly one
  NY cell (NY_PRE/M2) and 0 of 17 others; 2 of 36 tests clearing is the
  naive budget.
- **Nothing rescues NY_PRE M2-long**, the family's worst cell. Five
  variables "survive" there and *every good arm is still net-negative
  in R* — you can find subsets that lose less, never subsets that win.
  The overnight-volatility cluster that looked most plausible improves
  the near target while worsening the far one, the signature of where a
  structure happens to sit rather than trade quality.
- **BR-91's `n_aff` and `disp_abs_w` "confirmation" in NY_AM M3 is
  withdrawn as evidence.** They survive a rule that passes 5% of pure
  noise; that is not confirmation. The underlying directional
  observation (heavier confluence load associates with worse outcomes)
  still has BR-91's cross-cell repetition behind it, but it has not
  been validated by this sweep and must not be counted as such.

## WHAT THIS PASS ESTABLISHES

**Nothing in 111 decision-time variables — price state, structure
geometry, confluence measured continuously, volatility and trend
regime, day type, calendar, sequence, cross-session carry, order flow,
book depth, or any two-way interaction among them — separates winners
from losers on this population beyond what shuffled outcomes produce.**

That is a strong, calibrated negative, and it is worth more than a list
of 130 fragile candidates would have been. It also closes the loop on
the programme's standing principle: the raw mechanism is fairly priced,
and no *bar-derived, decision-time* variable rescues it.

**What remains untested is what it always was**: the trader takes ~1.3
trades a day out of ~11 valid fights, and whatever governs that choice
is not in any column measured here. Measuring it requires capturing the
decision itself — the forward flow recorder running on this grammar, or
a hand-log of take/pass against the census's own fight list — not
another sweep of the same table.

Standing: fit-only, no holdout, report-only, nothing adopted, nulls
published.
