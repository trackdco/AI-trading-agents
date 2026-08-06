---
date: 2026-08-05
status: thesis-pending
tags: [ny-pre, depth-walls, order-flow, structural-events]
sources: ["articles/yt-2026-08-05-nypre-video-sweep.md#U1", "articles/yt-2026-08-05-nypre-video-sweep.md#U3", "articles/yt-2026-08-05-nypre-video-sweep.md#C2", "articles/2026-08-05-nypre-inventory-academic.md#A6", "articles/2026-08-05-orderflow-scalpers-fabio-carmine.md#U1", "articles/2026-08-05-orderflow-scalpers-fabio-carmine.md#U2", "articles/2026-08-05-orderflow-scalpers-fabio-carmine.md#U3", "articles/2026-08-05-orderflow-scalpers-fabio-carmine.md#U6"]
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

### UPDATE 2026-08-05 — a ranked practitioner names this exact setup, unprompted

Angus supplied five order-flow scalping sessions (677,503 chars transcribed,
`articles/2026-08-05-orderflow-scalpers-fabio-carmine.md`). Asked what the best
trade of a four-hour live NQ/ES session was, Fabio Valentini — three-time ranked
in the Robbins World Cup scalping division — answered [xUyqIjCfZzg @ 45:09]:

> *"The best setup that I saw, which I hesitated to execute on, was **when the
> pre-market lows broke. We had the zero prints that formed and the massive
> absorption at the low**."* — *"That's an **A+ perfect setup**"* — *"and
> **really low risk**."*

That is this candidate's trigger with the discriminator filled in. I wrote above
that the open adjudicates the break; he says what the adjudication *looks like on
the tape* before the open confirms it:

- **Absorption at the level** — aggressive orders arriving and price refusing to
  move, because passive size is filling them. He states the inverse as a
  stand-down rule [DyS79Eb92Ug @ 44:35]: *"not when we are getting absorbed,
  because when we are getting absorbed we are betting on the losing side."*
  That is the cleanest trapped-counterparty test in any source we hold.
- **Zero prints** — price levels where one side traded literally zero
  [xUyqIjCfZzg @ 6:48]: *"zero volume on one side of the market... no trades hit
  the offer... they're usually very strong magnetic forces."* Computable from our
  footprint parquets, and it supplies a *target*, which is the leg our sleeves
  keep dying on (`euro-handoff`: 78% WR, +0.02R, because the natural target was
  too far).

**Ranking change: this moves from third to first among the three theses.** Not
because the story got better — because it went from under-specified to the
best-specified of the three, and because the missing piece was exactly the one I
flagged. The two inventory theses remain stronger on *independence*; this one is
now stronger on *specification and frequency*.

**Cost caveat, from the same source, and it is the real kill test** [xUyqIjCfZzg
@ 45:40]: *"The only fear I have on this setup is being slipped... in the NASDAQ,
that's very possible... there's more slippage in the NASDAQ, especially with
larger size."* He estimates ES book thickness at 40–50 contracts and does not
know NQ's. **We do** — MBP-10 for this window. Measure book thickness at trigger
time rather than assuming a slippage constant, and treat the 2× arm as the
adjudicating test, not a formality.

**The honest risk, unchanged and still primary.** Redundancy. It shares a window
and a direction-generating idea with the parked `nypre-open-sweep-fade` (which
fades a sweep *at* 09:30) and touches the `depth-walls` family the canon already
uses. `pairwise_overlap` against the canon's actual pre fills runs at census
time — flag 1 in the sweep merge — and if it comes back high this candidate
should be dropped rather than refined.

**One thing this evidence is not.** These traders work the 09:30 open and the
afternoon; the same source has Fabio avoiding the pre-market open outright
(*"you see the battle but you don't know who will win it"*). So this is
corroboration of the **mechanism**, not evidence that 08:00–09:30 is tradeable.
The census still has to establish that from our own data.

Second risk: it may need to hold through 09:30 to resolve, which is new execution
semantics against the canon's rule-K flatten and needs your ruling before any arm
that does so is run. A variant that resolves entirely before 09:30 is weaker but
avoids the question — worth declaring both and letting the census say.

## Skeleton

During 08:00–09:25, detect a break of a watched level (pre-market extreme,
overnight extreme, prior-day extreme) and classify it on three measurables:

1. **Backing** — resting size at the level before the break, size *pulled* versus
   *consumed*, and signed volume through it. "Unbacked" = broke into a vacuum on
   thin executed flow.
2. **Absorption at the extreme** — aggressive volume arriving at the break
   extreme with price failing to extend. This is the discriminator; without it
   we are back to the bare price trigger that killed `quiet-hours-reversion`.
3. **Zero prints beyond the break** — footprint levels with zero volume on one
   side, marked as targets rather than entries.

Unbacked breaks showing absorption are faded back inside, targeting the zero
prints / pre-market mid. Backed breaks are stood down from entirely (joining them
is a separate declared arm, not this trial). Stop beyond the absorption extreme —
that is where the "really low risk" property comes from, and if the geometry does
not come out tight the candidate has failed the `euro-handoff` test regardless of
hit rate.

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
