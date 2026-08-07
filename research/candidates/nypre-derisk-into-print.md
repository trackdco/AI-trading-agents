---
date: 2026-08-05
status: thesis-pending
tags: [ny-pre, news, order-flow]
sources: ["articles/2026-08-05-nypre-inventory-academic.md#A2", "articles/yt-2026-08-05-nypre-video-sweep.md#U6", "candidates/nypre-prerelease-premium.md"]
---

# nypre-derisk-into-print — get paid for the flattening, not for the number

## Thesis (for Angus)

We already measured this one by accident, and we killed the wrong half of it.

`nypre-prerelease-premium` claimed traders get paid a risk premium for *holding*
into an 08:30 release. Our census said no — and not weakly. On event days the
04:00→08:25 drift came in at **−12.5 pts (2025, n=27)** and **−32.0 pts (2026,
n=12, median −45.8)**, against −3.3 / +5.4 on non-event days. Negative in both
eras, and much more negative than the non-event baseline. The tombstone says it
plainly: *"if anything the sample shows pre-release DE-RISKING (drift down into
prints)"* — and flags the inverse as a new claim needing its own prereg.

This is that prereg. And since we wrote it, two independent sources have landed
on the same side.

The NY Fed's volume study finds a distinct activity U-shape **between 03:00 and
08:30 that they attribute directly to scheduled US macro announcements** — the
pre-print window is not quiet, it is busy. And the traders themselves say what
they're doing in it. From the video sweep, TTrades on the economic calendar:
*"I will just avoid prior to 8:30 on Tuesday... with PPI since that is under a
medium impact I'm just going to avoid prior to 8:30."* That is the standard
discipline, taught everywhere.

Put those together and the mechanism is embarrassingly simple: **the whole market
is being told to be flat before the number.** Flattening is not neutral. If the
book is net long overnight — which it usually is, since that's the direction
carry and inventory both push — then "everyone flattens" means "everyone sells,"
on a deadline, into a thin book, regardless of price.

**Who's on the other side:** every participant holding overnight risk who has
decided, hours in advance, that they will not carry it through a binary event.
They are not trading a view. They are meeting a deadline. Deadline-driven flow is
the most reliably exploitable kind there is, because it is indifferent to price
and it cannot be postponed.

**Why this is cheap to test.** It is a sign flip on a census we have already run,
on data we already hold, with a calendar we already committed. It costs
approximately one arm. Given the program sits at 34 arms and every additional arm
deflates the entire book's DSR, a candidate that reuses an existing measurement is
worth disproportionately more than one that needs a fresh search.

**The honest risk, stated up front.** Sample size, and it is the binding one.
n=27 and n=12 event days per era is thin — that is the number of qualifying days,
not trades, and A1 wants ≥60. Two ways this dies legitimately: not enough event
days to clear sample sufficiency, or the drift is real but too small per unit of
risk once we pay the pre-market spread (the euro-handoff failure mode — right
about the pattern, wrong about the economics). I'd rather we agree now that
"directionally confirmed but n-starved" is a **PARK**, not a kill, so it stays
available if we later extend the span or widen the release tier.

Secondary risk: overlap with `nypre-closing-imbalance-unwind`. Both predict a
negative pre-open drift. They condition on completely different things (a
scheduled release vs yesterday's closing imbalance) but they will agree on some
days. **Their day-level R correlation has to be measured before both ship**, not
after — two sleeves that fire together are one sleeve.

## Skeleton

Classify tomorrow from the committed release calendar by tier (high / medium /
none). On a qualifying release day, bias **short** across the pre-print window,
entering from a level rather than at a clock tick, flat **before** 08:30 — the
position is in the flattening, never in the print. Non-event days are the control
arm, not a trade.

The 08:30 reaction itself is out of scope and stays out: `nypre-0830-event-tree`
already established that post-impulse continuation into the open does not exist in
2025–26, and that kill stands.

## Flags

- **Data: fully in hand.** Release calendar committed (`config/news_calendar.csv`,
  `data/reference/news_archive.csv`), bars and CVD cover both eras and the holdout.
- Reuses the `nypre-prerelease-premium` census — declare explicitly that this is a
  fresh claim on the same measurement, so the family arm count is honest.
- Tier gate (M1 from the prior sweep) is the natural first conditioning axis and
  is already specified; do not invent a second one in the same trial.
- **Must be flat before 08:30.** No arm holds through a print. That is a
  declaration, not a preference.
- Canon redundancy: needs checking — the canon's pre leg trades this window and
  release-tier splitting of its P&L was already flagged as an owed free
  deliverable.

## Trial ledger — NYP-DIP-01

_Awaiting Angus greenlight. No trials run._
