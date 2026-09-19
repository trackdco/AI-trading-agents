# INDEX — overnight run, 2026-08-07

Four phases, strictly in order. **Report-only. Nothing shipped, nothing
armed, nothing adopted. No holdout contact — look #1 remains HALTED.**

## The three things to read first

1. **PHASE 2's precondition FAILED.** Of 17 entry-usable candidates, one
   passes all four ladder tests and it is Law-2 mechanical. **Zero
   non-mechanical variables** show tier-to-tier differentiation across 3+
   tiers. No sizing ladder was built. → `FINDINGS-phase1-diagnosis.md`
2. **The London combination works, and costs size.** Incumbent + room-gated
   3m: 3.42/day, +0.420R, graduation 98.5% → **100.0%**, live proxy +24% —
   but worst-day R −5.41 → −6.88 and max safe size **$350 → $250**.
   → `FINDINGS-phase0.md`
3. **"Frequency beats EV" is NOT a sim-stage artifact.** It was queued to
   be scoped that way; the live-stage proxy was run to check and **the
   ranking is identical at both stages**, so the narrower scoping would
   have been wrong. → BR-39.

## Documents

| file | what it is |
|---|---|
| `FINDINGS-phase0.md` | overlap (redundancy vs concurrency), the full 12-cell table with CIs, the combination through the full account lab, the frequency-vs-EV scoping |
| `DECLARATIONS-combination-london.md` | specification of record for the combination — **written after the run**, see its §0 |
| `FINDINGS-phase1-diagnosis.md` | the diagnosis and the Phase 2 precondition |
| `BASE-RATES.md` | BR-39 … BR-45 added tonight |

## What each phase did

**PHASE 0.** Overlap split into two measurements as asked. Redundancy (same
locus, same direction, entry within 5 min) came back **6.6% at 3m / 8.1% at
5m** — far under the 50% line — so a simple union with the number stated,
no invented dedup rule. Concurrency reported separately at **22.2% /
25.3%** and carried into the account lab through daily-total R rather than
position counting. Cross-TF union still not built: **41.9%** of the 5m
stream is redundant with the 3m stream, so 3m and 5m are combined with the
incumbent separately and never with each other. Full 12-cell table
published with point estimates and CIs — all twelve lifts positive, ten
missing on interval width rather than sign.

**PHASE 1.** Every column, both bootstraps, magnitude quintiles, variance
decomposition, per-book fresh worst-days, dual currency on every row.
Diagnosed per book, never pooled.

**PHASE 2.** Precondition reported with numbers and failed. Stopped there.

**PHASE 3.** Not reached — Phase 2 gates it and Phase 2 stopped.

## Three process notes, all against my own work

1. **A declaration was written after its run.** The queue said "combination
   declaration and run"; the run went first. The combination numbers are
   therefore fit-side descriptive, not a declared test. Full accounting in
   `DECLARATIONS-combination-london.md` §0.
2. **The Law-2 screen was too narrow as declared** and was widened
   mid-run. It covered mechanical coupling to stop width and the R
   denominator, but not variables that are *not knowable at the decision
   bar*. The in-trade family topped the raw ranking at +1.125R and is
   useless for entry selection. Now flagged POST-ENTRY (BR-41).
3. **The first Phase 1 run was wrong and was discarded.** Columns present on
   only part of a combined book were being reported as book-level findings —
   the combined books were silently reproducing the incumbent's numbers for
   any column the room stream lacked. Fixed with per-column coverage
   flagging; anything under 90% is now marked a sub-population finding.

## Open items for review

- **The 2pt risk floor is too low** (BR-45). `risk_w` still separates
  monotonically with the floor applied. It was set by argument, never
  measured. A declared sweep is the obvious next thing.
- **`volx` as a binary gate** rather than a ladder. It survives
  day-clustering in both trigger timeframes with dual currency agreeing —
  the only variable in the run that replicates across timeframes. That is a
  Law 7 gate question and needs its own declaration.
- **The combination's size regression.** It wins on graduation and live
  dollars while requiring a 30% smaller position. Whether that trade is
  acceptable is a decision, not a measurement.
- **Depth was never built for the LTF population.** Stated throughout, not
  papered over; the depth six are diagnosed on the incumbent only.
- **Holdout look #1** stays halted. Its claim list now holds one live
  candidate (LONDON reject, room ≥3R, 3m and 5m).
