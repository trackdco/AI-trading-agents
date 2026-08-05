---
videoId: W_2x8Mv0-9M
title: "Powell Trades | Wick Theory #4 | Dumb Money Concepts Whop"
date: 2025-07-13
duration: 7m44s
source_stream: Dumb Money Concepts Whop
trader: zxcked
prefix: zxck-
GAP_ENTRY: no (but the primary DISQUALIFIER is imbalance-based)
NY_SESSION: not stated
---

# Wick Theory #4 — the filters. The most important video in the set.

## What it covers
Explicit **do / don't** filters that turn `zxck-wick-ce` from a pattern into a rule set. He
sets out to make the model *"higher probability"* `[W_2x8Mv0-9M @ 00:01]`.

## THE DISQUALIFIERS — both `[stated]`, both mechanical

**DON'T #1 — the wick must not begin an unfilled imbalance.**
> *"number one, it should not be the beginning of an unfilled imbalance… if it's the beginning
> of an unfilled imbalance, then do not take it because it's going to be low probability."*
> `[@ 00:52–02:04]`
Applies on **every** timeframe: *"hourly, 4 hour, daily, 30 minute, 15 minute, 5 minute,
3 minute, 1 minute, whatever"* `[@ 01:42]`.

**DON'T #2 — the wick must not form equal highs/lows with a SWING point.**
> *"if we got like equal highs in the form of two swing highs and we have this wick that fits
> our criteria for the wick model, then don't take it."* `[@ 06:34]`
Qualified: *"equal highs and equal lows should be like swing lows and highs, not just random"*
`[@ 06:08]` — random intraday equal highs do not disqualify.

## THE ENHANCER
**DO — SMT at the wick.**
> *"if there's an SMT at the wick that you're trying to short, that makes it way higher
> probability… otherwise you're kind of in a way trading support and resistance"* `[@ 03:17]`
ES vs NQ is the pair he reaches for `[@ 03:17]`.

## The bias filter
> *"don't trade away from the draw on liquidity… if we just mitigated something on the higher
> time frame and you're trying to take this bearish wick — just don't take it"* `[@ 04:37]`

## Stated trading style
> *"I like to trade with like a high win rate, high risk-to-reward and then a lower trade
> frequency. So I'll just wait for everything to kind of be perfect and then enter."* `[@ 04:59]`

## Timestamped index
| time | moment |
|---|---|
| 00:52 | **DON'T #1** — not the start of an unfilled imbalance |
| 01:16 | worked counter-example: a wick that meets criteria but is disqualified |
| 01:42 | applies on all timeframes |
| 03:17 | **DO** — SMT at the wick; without it *"you're trading support and resistance"* |
| 04:09 | restates the full model: mitigate something, reject, leave liquidity below CE |
| 04:37 | **bias**: never against the draw on liquidity |
| 04:59 | style: high WR, high RR, low frequency |
| 06:34 | **DON'T #2** — swing-point equal highs/lows disqualify |

## Candidate strategies introduced
No new strategy — this is the filter layer for `zxck-wick-ce`, and it is what makes that model
backtestable.

## Grounding notes
- DON'T #1 is **imbalance-defined**, so implementing `zxck-wick-ce` requires FVG detection even
  though the entry is not a gap entry. That shares code with the ash10hazard work.
- *"there's probably something I'm forgetting"* `[@ 07:19]` — he does not claim the list is
  complete.
