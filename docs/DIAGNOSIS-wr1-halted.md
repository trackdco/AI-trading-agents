# wr1 — HALTED 2026-08-19 for diagnosis

His instruction: *"stop this shit now and push to git, we need to diagnose before we run."*
Run stopped mid-flight. Nothing below is a verdict on the batch; the run is 22/76
candidates deep and NY_AM is almost entirely unrun.

## Where it stopped

| window | settled | of |
|---|---|---|
| LONDON | 13 | 21 |
| NY_PRE | 7 | 20 |
| NY_AM | 2 | 35 |
| **total** | **22** | **76** |

Book: 124 rows across five day-files, of which **21 are superseded or void**. That
ratio is the diagnosis, and it is covered below.

## The seven closed trades

| trade | wr1 | w49 | note |
|---|---|---|---|
| Mon L1 | +1.5538 | +1.7661 | unmanaged full-target hold was **-1.0000** |
| Tue L2 | **+1.9283** | +1.8208 | **wr1 wins** - the only two-target plan in the week |
| Wed L1 | +0.8421 | +1.5684 | |
| Wed L2 | **-0.5946** | *(w49 passed)* | **new losing shape** |
| Thu A3 | +0.3707 | +0.4706 | |
| Fri L1 | +0.3500 | +0.7841 | |
| Fri L3 | -0.3788 | -1.0000 | T68 flip saved 0.62R |
| **total** | **+4.0715** | **+5.4100** | **-1.34R** |

Sample is biased against wr1: six of seven are single-target plans, which is the
shape the 50/50 split punishes. The one two-target trade beats w49.

## What is actually wrong - one failure family, five instances

Every error found in this run is the same shape: **a hand-written state file
describing a state that had already moved.** None was a tape leak. All five were
caught downstream by something reading a number back, never by a check written in
advance.

1. **Wrong tape-day anchor.** A capture worklist keyed on session-day 2026-06-25
   instead of its tape day 2026-06-26; three frames pulled from a different session.
   Consequence: none - they fed a scheduler change that was reverted. Quarantined.
   Caught by the capture agent converting the cursor back to wall-clock.

2. **Stale position state - four separate times.** Wed L2-L10, Fri L2-L4, Thu A4/A5,
   Wed L3. Each time a downstream candidate was adjudicated against a book state that
   a fill, a partial or an exit had already changed. This is the single largest source
   of the 21 superseded rows.

3. **w49 escalation history carried into wr1.** Two briefings asserted an escalation
   that never happened in this run and named a thesis version wr1 does not have.
   **It entered the reasoning** - Wed L3's verdict cited *"v2 re-fire already
   accommodates this"*. Fixed at the root: escalation state is now DERIVED from the
   run's own book (`mkesc.py`), so it cannot disagree with what happened.

4. **Manage calls issued after a position had closed.** Mon L1's 04:24 trail was hit
   on the bar it was set; two further calls were issued against a position that no
   longer existed. Caught by the 04:36 manager REFUSING to act and reporting that a
   short cannot have its stop below price. It did not invent a resolution to make the
   briefing coherent - exactly the contract behaviour wanted.

5. **Ordering hazard.** A manage call and a candidate can fall one minute apart. Wed
   L3's briefing was built before Wed L2's 03:26 exit verdict landed, so it was told a
   position was open that had just closed.

### Root cause

The orchestrator has **no single source of truth for "book state as of minute M"**.
Position state, escalation state and cap state are each hand-authored per briefing
batch and re-authored ad hoc whenever something upstream changes. Escalation state was
fixed this way mid-run and stopped producing errors immediately. **Position state has
not been, and it is where four of the five instances came from.**

**The fix, before any further run:** derive position state from the book at a given
minute, the way `mkesc.py` now derives escalation state - replay the day's live fill /
manage / exit rows up to minute M and emit the state. A generated file cannot disagree
with what happened; a hand-written one can, and did, four times.

## Contract-level questions for his ruling (none acted on)

- **Second target mandatory.** 20/26 w49 fills and 11/18 j49 fills were single-target;
  tv-trigger 0.4.11 never asks for a second target (the strings "second target" and
  "runner" do not appear in it). Under 50/50 the destination-less runner is half the
  size instead of a quarter. Tue L2 is the counter-example and it beat w49.
- **T55 trail clearance.** Three trails placed legally under T55 were then collected:
  Mon L1 (hit on the bar it was set, 9.25pt clearance vs a 14pt wick), Wed L1 (5pt
  ABOVE a short's entry, so the runner could only bank a loss), Thu A3 (27.78pt above
  entry, same). The floor is 0.5x the AVERAGE 2m range and these were not average bars.
- **T68 flattens on the TAKE, not the fill.** Fri L4 flattened L3 and then never
  filled its own limit. Contract as written; worth confirming it is intended.
- **Chart-not-read.** One trigger adjudicated from the briefing's numeric blocks alone.
  Re-run with the chart produced a DIFFERENT grade (C vs B), stop and rejected level.
  Reading the chart changes the trade - so briefing-only adjudication is not equivalent.
- **Wed L2 is a new losing shape** (a trade w49 passed). Whether that is the batch or
  the rebuild churn is genuinely ambiguous: it was adjudicated three times as state was
  corrected, and the version that took it graded it C and called its own rejection
  "single-candle wick, no anchor confluence, low merit".

## Deliberately NOT fixed (post-run tickets, per his 2026-08-19 ruling)

Lone-15m-MA second legs in the scanner; 3m chart vs 2m briefing text; frame anchoring
lag; and the `htf.management_minutes` gap where a runner with no remaining target gets
no structural manage calls. The scheduler fix for the last one was written, measured
and REVERTED so wr1 keeps w49's management structure exactly.

## Positive signal worth keeping

`r_full_target` shows management earning its keep independently of the split: Mon L1
+1.55 vs -1.00 unmanaged, Wed L2 -0.59 vs -1.00, Fri L3 -0.38 vs -1.00. Both T68 flips
improved on where the position was heading.

## The one source change standing

`scripts/replay_tools/runmanage.py` - the manage briefing was quoting the RETIRED
conviction-keyed partial schedule (A 50 / B 75 / C 100) as "the contract text" while
tv-manage 0.3.3 mandates uniform 50/50. Four calls read it; none is affected (both TP1
calls returned 50%, the correct answer either way) and every affected row names its own
exposure. Fixed rather than deferred because it fed agents a contract not in force.
