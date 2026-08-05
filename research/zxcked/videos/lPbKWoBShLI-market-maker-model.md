---
videoId: lPbKWoBShLI
title: "Powell Trades | Market Maker Model | Dumb Money Concepts Whop"
date: 2025-08-09
duration: 7m09s
source_stream: Dumb Money Concepts Whop
trader: zxcked
prefix: zxck-
GAP_ENTRY: partial — the breaker is paired with a 5-minute imbalance
NY_SESSION: YES — midnight open as the daily discount/premium pivot
---

# Market Maker Model — original consolidation, curves, and breaker entries

## What it covers
MMXM as a **bias framework** with **breakers as the entry trigger**.

## IDENTIFICATION — `[stated]`
> *"the original consolidation is going to be one of the biggest things that's going to help
> you identify a market maker model. Almost every market maker model has an original
> consolidation and then a buy-side curve and a sell-side curve."* `[lPbKWoBShLI @ 00:23]`

## THE ENTRY — `[stated]`
> *"breakers are going to be the biggest part of your market maker entries."* `[@ 01:56]`
Breaker defined: *"it's a high and a low and a higher high and then that gets traded through"*
`[@ 01:56]`.
> *"we want a candle closure above this breaker."* `[@ 03:55]` — a **close**, not a wick:
> *"It didn't close above. It just kind of swept it and then had a retracement leg"* `[@ 04:22]`.

## THE PLUS-PLUS CONDITION — `[stated]`
> *"a market maker model is essentially your bias and then breakers is going to be the entry
> trigger. And then obviously imbalances, great bonus. And then you want a swing above or below
> your midnight open for it to be like a plus plus."* `[@ 06:37]`

## Numbers stated
- Preferred timeframe: *"If you're going to use market maker models, I found that five minute
  time frame is the best to use."* `[@ 03:55]`
- *"I like to use the 50% mark of every imbalance just so that my risk is better"* `[@ 05:28]`
- *"my stop loss would be probably five points"* `[@ 05:51]`
- Target: relative equal highs `[@ 06:37]`

## Timestamped index
| time | moment |
|---|---|
| 00:00 | starting confluences: NWOG with liquidity above it |
| 00:23 | **identification** — original consolidation + buy/sell-side curves |
| 01:32 | smart money reversal — sweep into an order block |
| 01:56 | **breaker defined; breakers are the entry** |
| 02:20 | mark midnight open first, every day |
| 02:42 | breaker + midnight open + 5-minute imbalance stack |
| 03:55 | **5-minute is the best timeframe; requires a candle CLOSE through the breaker** |
| 04:22 | counter-example — a sweep without a close is not an entry |
| 05:28 | 50% of every imbalance for better risk |
| 06:37 | **the full stack: MMXM bias → breaker trigger → imbalance bonus → midnight-open swing** |

## Candidate strategies introduced
| id | name | one line | gap-entry? |
|---|---|---|---|
| `zxck-mmxm-breaker` | **MMXM breaker entry** | Identify the curve, wait for a 5-minute close through a breaker, enter at the 50% of the paired imbalance, ~5pt stop | **partial** |

## Grounding notes
- **"Original consolidation" is not mechanically defined** — same gap as AMD. Both models hinge
  on a range that is recognised by eye.
- The breaker + imbalance-50% entry **is** mechanical once the curve is granted, so `zxck-mmxm-
  breaker` could be tested with a hand-supplied or heuristic consolidation definition, clearly
  flagged as ours.
