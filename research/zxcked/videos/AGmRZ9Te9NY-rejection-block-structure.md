---
videoId: AGmRZ9Te9NY
title: "How to structure a Rejection block entry (Trade breakdown)"
date: 2025-07-13
duration: 11m06s
source_channel: "Powell trades (OWN)"
views: 156343
trader: Powell
prefix: zxck-
GAP_ENTRY: YES — bias is an unfilled NWOG; entry at a 1-hour FVG
NY_SESSION: no — a LONDON trade, explicitly an exception
---

# Rejection block structure — a London trade, and premium-vs-discount level selection

## Session — worth flagging
> *"This was a London session rejection block. So, not something that I usually go for, but I
> was busy during New York AM that day."* `[AGmRZ9Te9NY @ 00:23]`

**Confirms New York AM is his default session**, and that the model is session-agnostic enough
to be taken in London when he is not around for NY.

## BIAS — `[stated]`
> *"this new week opening gap down here… is completely unfilled. So I was really confident that
> we were going to go down. Unfilled new week opening gaps are super powerful. In terms of bias
> and confluences I don't really need much more if we have that."* `[@ 01:12–01:35]`

## LEVEL SELECTION — premium vs discount, the rule that picks between two candidate levels
> *"why did I not short off of this one? Because when there are two like this, this one is
> pretty — you're shorting in deep discount, which is not great. This one is more of a premium
> level. That's what I like to base my levels off of… If we tap into this and we get a little
> reaction down, that is usually a manipulation move, and we're going to come up, tap this
> higher premium PDA, and then make the actual move."* `[@ 01:59–02:24]`

**A mechanical tie-break when two FVGs are stacked: take the one in premium (for shorts).**

## THE TIMING RULE — `[stated]`
> *"Technically, it's not a rejection block until this candle closes… that's going to give me
> actual bearish confirmation."* `[@ 02:47]`
He explicitly disputes the ICT definition: *"ICT might teach it with it being the last up-close
candle. I don't really care. I'm teaching you guys how I like to do it."* `[@ 03:11]`

**Recorded because it means his rejection block is NOT the ICT rejection block.** Any
implementation must use his version.

## THE STOP MIGRATION — stated, with a reason
> *"three point stop, not something that I really like to do anymore because I like to play a
> bit more safe. I like to combine my high RR with a high win rate… I used to do like anything
> between two to 10 point stops when I was broke because I couldn't handle losses."* `[@ 05:06–05:52]`

**His stop sizes grew as his account grew.** So the 2-3 point stops in the 2025 zxcked videos
and the 10–15 point stops in the 2026 videos are the same person at different account sizes —
not a contradiction, and the later numbers are the ones to test.

## The trade
Missed the first entry; on the second, price swept the interim high (*"a good manipulation
move"*), he limited at ~4047 with the stop above that high — *"because we already manipulated"*
`[@ 06:38–07:00]` — for a 1:3 `[@ 07:24]`.

## Timestamped index
| time | moment |
|---|---|
| 00:23 | **London session, an exception; NY AM is the default** |
| 01:12 | **bias = unfilled NWOG, and that alone is enough** |
| 01:59 | **premium-vs-discount tie-break between two stacked FVGs** |
| 02:47 | **the rejection block is not valid until the candle closes** |
| 03:11 | explicitly departs from the ICT definition |
| 04:21 | rejects a 5-minute rejection block as *"too premium"* — beyond fib 0.79 |
| 05:06 | **stop-size migration as the account grew** |
| 06:38 | limit after the manipulation sweep; stop above the swept high |
| 07:24 | 1:3 target |
| 08:58 | the four confluences named: NWOG bias, FVG, rejection block, fib |

## Candidate strategies
Refines `zxck-wick-ce` (candle-close timing, premium/discount tie-break) and `zxck-nwog-bias`
(unfilled NWOG alone is sufficient bias).
