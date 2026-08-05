---
videoId: 6opmiyFvJBA
title: "Powell Trades | Rejection Wick | Dumb Money Concepts Whop"
date: 2025-08-09
duration: 10m10s
source_stream: Dumb Money Concepts Whop
trader: zxcked
prefix: zxck-
GAP_ENTRY: no
NY_SESSION: YES — pre-market and market-open examples
---

# Rejection wick / rejection block — the concept behind wick theory

## What it covers
The concept video that `zxck-wick-ce` is built on, and the distinction between entering at the
**start of the wick** and at the **CE**.

## THE DEFINITION — `[stated]`
> *"a rejection block is just the start of a wick… we sweep these highs and then we have this
> huge rejection wick. This is a rejection block."* `[6opmiyFvJBA @ 00:46]`

> *"price comes back up to test the start of the wick. Sometimes it touches CE, sometimes it
> just touches the start of the wick."* `[@ 01:08]`

## THE TWO ENTRY VARIANTS — `[stated]`
> *"you can either use the CE or the 50%, or you can just enter on the beginning of the wick.
> That's kind of up to you. If you want to make sure that you get an entry, then put it at the
> beginning of the wick. If the risk is too much, then put it at the CE."* `[@ 08:13]`

**This is a real, testable fork**: fill rate vs risk size. Start-of-wick fills more often with a
bigger stop; CE fills less often with a smaller stop.

## The precondition
> *"usually you want like a sweep or for it to tap into something."* `[@ 09:29]`
And, cross-referenced: *"what I posted in wick theory is basically just you're only focusing on
the CE of the rejection block and you want some engineered liquidity right below CE"* `[@ 01:30]`.

## Confluence named
The **fib golden pocket**, *"basically just the 0.62 up to the 0.79 area"* `[@ 01:54]` — a PD
array landing in that band raises probability.

## Why he thinks it works — `[inferred by him, not evidence]`
Traders who swept the high close their position when price retraces to their entry; the
rejection block is where that happens `[@ 05:29–06:37]`. *"the best trade is the scariest
trade"* `[@ 07:02]`.

## Timestamped index
| time | moment |
|---|---|
| 00:46 | **definition** — the start of a rejection wick |
| 01:08 | price returns to the wick start, sometimes only the CE |
| 01:30 | wick theory = CE + engineered liquidity below |
| 01:54 | fib golden pocket 0.62–0.79 as confluence |
| 03:09 | **the trade-off** — rejection block entry vs order block entry stop size (20pt) |
| 03:30 | works on every timeframe, 15-second to 4-hour |
| 05:29 | the behavioural story he tells for why it works |
| 08:13 | **the two entry variants, stated as a choice** |
| 09:29 | precondition — a sweep or a tap into something |

## Candidate strategies introduced
| id | name | one line | gap-entry? |
|---|---|---|---|
| `zxck-wick-start` | **Rejection-block start-of-wick entry** | Enter at the wick's origin rather than its 50% — worse risk, higher fill rate | no |

## Grounding notes
- The behavioural explanation at `[@ 05:29]` is **his hypothesis about other traders**, not
  evidence. Tagged `[inferred]` and it is not testable from price data.
