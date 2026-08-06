---
date: 2026-08-05
status: thesis-pending
tags: [ny-pre, overnight-structure, order-flow]
sources: ["articles/2026-08-05-nypre-inventory-academic.md#A1", "articles/2026-08-05-nypre-inventory-academic.md#A2", "articles/2026-08-05-nypre-inventory-academic.md#A3", "articles/2026-08-05-nypre-inventory-academic.md#A5"]
---

# nypre-closing-imbalance-unwind — yesterday's close tells you today's pre-open

## Thesis (for Angus)

When the last hour of the day session is heavily one-sided — say everyone is
dumping into the close — somebody has to take the other side. That somebody is
the market makers, and they don't do it as a favour: they take it at a discount,
and now they're sitting on a position they never wanted, overnight, in a book too
thin to get out of. Their whole job is to get flat. They get flat when liquidity
comes back.

For twenty years they got flat at the European open, and that trade paid 3.7% a
year. **Since 2021 it pays zero — the NY Fed re-ran it this July with five extra
years and confirmed it's gone on NQ specifically.** So the obvious version of
this idea is dead and we should not touch it.

But here's the part worth our time. The Fed's own charts mark a *second* window
where that same inventory shows up: **08:30–10:00 ET, which they call the
"opening reversal."** And they separately document that in the thirty minutes
before the 9:30 bell, returns are *"initially large and negative."* Dalton, coming
at this from auction theory with no knowledge of the paper, says the same thing in
different words: one-sided overnight inventory gets corrected in the day session
as a liquidation break or a short-covering rally.

Two independent traditions, one conclusion: **the position gets unwound where the
liquidity is.** The European leg went flat. The liquidity didn't disappear — it
moved to our window.

So the trade is: measure how one-sided yesterday's close was, and let that set
the bias for this morning's pre-market.

**Who's on the other side:** a market maker with unwanted inventory and a risk
limit. Not a crowd, not a "retail base rate" — a participant who is *obliged* to
transact regardless of what he thinks price is worth. That's the thing our last
five kills were missing. `on-polarity` and `euro-handoff` both died with the same
tombstone: *a public statistic with no trapped counterparty is not a trade.* This
one has the counterparty, and the paper names him.

**Why it should not be correlated with what we already run.** Every candidate in
the book conditions on something inside the current session — the overnight range,
the gap, the Euro handoff. This one conditions on **yesterday afternoon**. Given
that our two shelved sleeves are both stuck below the DSR screen and the combined
book grades at PSR(0) 0.943 needing 291 days against our 268, an *independent*
sleeve is worth more to us right now than a strong correlated one.

**The honest risk, stated up front.** The reason the 2am trade died is that the
conditioning variable itself compressed — the spread of closing imbalances halved
(SD 6.5% → 2.9%) because algos slice their closing flow finer now. That
compression applies to our window too. So this may fail not because the mechanism
is wrong but because **there aren't enough one-sided closes left to trade.** That
is a sample-size kill and I want it declared before the census, not discovered
after. If we get fewer than ~40 qualifying days per era, the answer is "unproven,
insufficient dispersion," not "no edge."

## Skeleton

Prior day, 15:15–16:15 ET: compute **RSV** = net buyer-initiated share of volume,
bounded [−1, +1] (the paper's exact definition; we have it from the CVD footprint
parquets). Rank into bins against a trailing window.

Today, pre-market: extreme negative RSV yesterday (LPs absorbed selling → LPs are
long → they sell into liquidity) biases **short** into 09:00–09:30; extreme
positive RSV biases **long**, but weakly — the paper's asymmetry says sell-side
closes give robust reversals and buy-side closes give modest ones, so the two
sides are *not* symmetric arms and must not be pooled.

Entry from a level rather than at a clock tick — the geometry has to be tight or
the euro-handoff lesson repeats. Resolve by 09:30 (canon rule K flattens); the
09:30–10:00 leg is a separate declared arm requiring the semantics ruling.

## Flags

- **Data: fully in hand.** RSV needs prior-day 15:15–16:15 signed volume — CVD
  footprints cover Q3/Q4 2025, Jan–Jul 2026, and the six 2023/24 holdout months.
  No purchase, no new plumbing.
- **Asymmetry is a prediction, not a parameter.** If the census finds a symmetric
  effect, we have measured something other than the inventory channel and should
  say so.
- **VIX is explicitly ruled out** as a conditioner by the paper's double sort —
  do not add it as a "regime filter" without a fresh reason.
- Canon redundancy: expected LOW (prior-day conditioning, no shared input family),
  but `pairwise_overlap` against the canon's actual pre fills runs at census time
  per program flag 1, not at the end.
- Arm discipline: **one census, one geometry, then stop.** Program is already at
  34 arms and every new arm deflates the whole book's DSR. The tail-day count from
  the census decides whether a second arm is even legal.

## Trial ledger — NYP-CIU-01

_Awaiting Angus greenlight. No trials run._
