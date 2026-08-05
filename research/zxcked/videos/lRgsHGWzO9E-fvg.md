---
videoId: lRgsHGWzO9E
title: "Powell Trades | FVG | Dumb Money Concepts Whop"
date: 2025-08-09
duration: 9m26s
source_stream: Dumb Money Concepts Whop
trader: zxcked
prefix: zxck-
GAP_ENTRY: YES
NY_SESSION: not stated
---

# FVG — imbalance inside an order block, and the inverse-FVG 50% mark

## What it covers
Two distinct ideas, and the second is the more valuable one.

1. **Validating an order block by the imbalance inside it.** `[stated]` Drop a timeframe and
   check whether the HTF order block contains a LTF imbalance: *"what I like to look at is do
   we have an imbalance inside of this order block… that's what makes it not random because
   you can choose any random order block and it's going to get raped"* `[lRgsHGWzO9E @ 01:13]`.
2. **The 50% mark of an INVERSE fair value gap** — he breaks off mid-video to flag this as a
   standalone model.

## The mechanical claim — this is the testable one
> *"15 minute or five minute inverse fair value gap. Enter on the 50% mark of that inverse
> fair value gap with a five-point stop. Look at how often it does this."* `[@ 07:44]`

> *"You could literally make a model out of this alone and be profitable."* `[@ 08:30]`
> `[trader-claimed, unverified]`

Timeframes named: **5-minute and 15-minute** `[@ 07:44]`. Stop: **5 points** `[@ 07:44]`.
No target rule is given in this video.

## Instrument / session
Not stated in this video. Point magnitudes quoted (50–60pt targets, 250pt selloffs) are
consistent with NQ, and NQ is named explicitly elsewhere in the set `[inferred]`.

## Timestamped index
| time | moment |
|---|---|
| 00:22 | frames it off the CISD video — up-close candle closed below |
| 01:13 | **rule**: scale down inside an order block, look for the imbalance |
| 02:29 | fib on top of the imbalance to locate the tap — 0.705 named as his usual |
| 03:18 | worked example: 1H order block + 15m imbalance, target 50–60 points |
| 04:29 | second example — 5-minute imbalances and 5-minute *inverse* imbalances |
| 06:32 | cross-refs the gap-fill video |
| 07:20 | **the standalone claim** — 50% of inverse FVGs, "mindboggling how often" |
| 07:44 | **full spec**: 5m/15m inverse FVG, enter 50%, 5-point stop |
| 08:06 | live example from that day on a 15-minute inverse |

## Candidate strategies introduced
| id | name | one line | gap-entry? |
|---|---|---|---|
| `zxck-ifvg-50` | **Inverse-FVG 50% mark** | Enter the 50% of a 5m/15m inverse FVG with a 5-point stop | **YES** |
| `zxck-ob-imbalance` | **Order block validated by inner imbalance** | Only take an OB that contains a lower-timeframe imbalance | **YES** (imbalance-based) |

## Grounding notes
- Target/exit for `zxck-ifvg-50` is **never stated** — a gap in the spec, not an omission by me.
- Direction/bias filter is not stated for either idea in this video.
- *"I'm not even sure how I found out… Maybe I watched an ICT video on this"* `[@ 00:00]` — he
  does not claim originality.
