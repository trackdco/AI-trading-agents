---
date: 2026-08-05
status: thesis-pending
tags: [ny-pre, depth-walls, order-flow, structural-events]
sources: ["articles/yt-2026-08-05-nypre-video-sweep.md#U1", "articles/yt-2026-08-05-nypre-video-sweep.md#U3", "articles/yt-2026-08-05-nypre-video-sweep.md#C2", "articles/2026-08-05-nypre-inventory-academic.md#A6"]
---

# nypre-thin-break-trap — the open decides whether the pre-market break was real

## Thesis (for Angus)

Breaking a level at 07:00 on 200 contracts and breaking the same level at 10:00
on 4,000 look identical on a chart and mean completely different things. In a
book as thin as the pre-market's, price travels a long way on very little flow —
so a pre-market break tells you almost nothing about conviction. It is cheap to
produce, and sometimes it is produced on purpose.

Meanwhile every retail trader in the market has drawn the pre-market high and the
pre-market low before the bell. That is not a guess — it is the single most
consistent thing in the whole video sweep; every routine video does exactly the
same ritual. So by 09:00 there is a dense stack of breakout orders and stops
sitting on two lines, placed hours earlier by people who are not watching them.

Then 09:30 arrives with the largest liquidity injection of the day and the
overnight order backlog executing at once. **That is the moment the break gets
adjudicated.** If real size wanted to be through that level, the open confirms it
and price accepts. If it didn't, price comes back inside, and now everyone who
bought the break is offside with a stop below — and their exits are the fuel.

NinjaTrader states the mechanism outright: low pre-market volume, NQ breaks
resistance, longs get enticed, the regular session opens with much higher
liquidity, price drops back below, and the trapped buyers' selling adds to the
reversal.

**Who's on the other side:** the pre-market breakout buyer. Specifically, someone
who committed on evidence generated in a book too thin to carry that evidence,
and who finds out he was wrong at a scheduled moment he does not control.

**Why this isn't the one we already killed.** `nypre-quiet-hours-reversion` faded
false breaks back to an *hourly midpoint within the same hour* and came in at
43–53% against a published 76–83.5%. I think the reason is structural rather than
bad luck: **nothing forces price back to an hourly mid.** There is no event, no
deadline, no participant who must act. Here the forcing event is the cash open,
which arrives on schedule whether anyone likes it or not. Same family of
observation, completely different resolution mechanism — and the previous failure
is evidence for this distinction, not against it.

**Why this is where our depth data earns its keep.** The whole thesis is "was the
break backed by real resting size or by a vacuum?" That is a direct MBP-10
question and we hold the book for this exact window. But CME's own liquidity work
is a warning we should take seriously: order-book depth read alone is misleading —
in December 2018 E-mini volume rose ~65% while book depth fell 75%. **Thin is not
the same as illiquid, and a wall is not the same as a defended level.** So the
trigger has to pair resting size with what actually executed, not resting size
alone. That pairing is exactly what our depth-walls + CVD combination is for.

**The honest risk, stated up front.** This is the closest of the three to ground
we have already worked, and redundancy is the defining program risk in this
session. It shares a window and a direction-generating idea with the parked
`nypre-open-sweep-fade` (which fades a sweep *at* 09:30) and touches the
`depth-walls` family the canon already uses. `pairwise_overlap` against the
canon's actual pre fills has to run at census time — flag 1 in the sweep merge —
and if it comes back high this candidate should be dropped rather than refined.
Of the three theses I am putting up, this is the one I would fund third.

Second risk: it may need to hold through 09:30 to resolve, which is new execution
semantics against the canon's rule-K flatten and needs your ruling before any arm
that does so is run. A variant that resolves entirely before 09:30 is weaker but
avoids the question — worth declaring both and letting the census say.

## Skeleton

During 08:00–09:25, detect a break of a watched level (pre-market extreme,
overnight extreme, prior-day extreme) and classify it: resting size at the level
before the break, size pulled versus consumed, and signed volume through it.
"Unbacked" = broke into a vacuum with thin executed flow. At the open, unbacked
breaks that fail back inside are faded toward the pre-market mid / opposing
extreme; backed breaks are stood down from entirely (or joined, as a separate
declared arm — not the same trial).

## Flags

- **Data: fully in hand.** MBP-10 for the NY window covers 2025-06→2026-07 plus
  the 128-day 2023/24 holdout; CVD footprints cover the same span.
- **Redundancy is the primary kill risk**, not edge. Check it first, cheaply.
- Depth alone is not the trigger — resting size must be paired with executed flow
  per A6, or we will systematically misread pulled liquidity as absorbed liquidity.
- Holding through 09:30 needs an Angus semantics ruling; declare a
  resolves-before-09:30 variant alongside so the census is not blocked on it.
- Arm discipline: the classification has one free parameter (what counts as
  "backed"). Declare its plateau check in the prereg — if only one threshold
  works, it is noise.

## Trial ledger — NYP-TBT-01

_Awaiting Angus greenlight. No trials run._
