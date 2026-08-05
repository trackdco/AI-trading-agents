---
videoId: xae9AiV5Ps4
title: "Powell Trades Engineered Liquidity (Private Course)"
date: 2026-01-07
duration: 12m30s
source_channel: "YohanNQ (re-host)"
views: 1454
trader: Powell
prefix: zxck-
GAP_ENTRY: no
NY_SESSION: YES — 10:00 ET open discussed; a Powell-testimony day skipped
---

# Engineered liquidity FAQ — the DISTANCE RULE. The most quantitative video in the corpus.

## Why this one matters disproportionately
Every other video says *"you need engineered liquidity beyond the CE"* without saying **how
far**. This one answers it, in points.

## THE DISTANCE RULE — `[stated]`, and it is a number
> *"A lot of you are asking how many points, how close can it be. My rule of thumb is if it's
> like two points or less away from the CE, I'll just not take it, because at that point I count
> the CE as already mitigated."* `[xae9AiV5Ps4 @ 02:16]`

> *"can it be too far away? Generally, not really… if the liquidity is inside of the rejection
> block — from here to here — that's usually the sweet spot for me. Because that shows we've
> already rejected this rejection block, we're willing to reject price at this level, come down,
> sweep price, go into the actual level."* `[@ 02:40–03:03]`

**Implementable band: liquidity must sit MORE than 2 points from the CE, and ideally WITHIN the
rejection block's own range.** This turns the corpus's most-repeated gate from a vibe into a rule.

## STOP SIZING — the rule that resolves the 2pt-vs-20pt confusion
> *"when you guys ask how big should my stop loss be, I always say it depends on volatility,
> depends on the points of the range… in this case that 5-minute wick is 20 points big. I can't
> do anything about that except adjust my risk."* `[@ 06:51–07:13]`

**Stop size is determined by the PD array's own size, not by a fixed point value.** Position size
absorbs the difference. That reconciles the 2-point stops of 2025 with the 20-point stops here.

## THE ALTERNATIVE STOP — fib-based
> *"something that is also a possibility if you're trading big wicks is to put it below the OTE
> of the wick. By OTE, the most premium or discounted part of the fib is going to be 0.79.
> Anything beyond that, I think it's overextended and we're most likely not going to hold that
> level."* `[@ 08:03]`

**Stop at fib 0.79 OF THE WICK ITSELF** — a scale-free stop rule.

## Trigger-timeframe selection
> *"1-hour level, 5-minute entry trigger makes sense. You can do 1-minute, you can do three…
> if you went for the 1-minute entry trigger down here at this rejection block, you would have
> got edged, which happens a lot when you got these tiny PD arrays."* `[@ 05:18–05:39]`

**Match the trigger timeframe to the level's timeframe.** Stated as a principle.

## Session note
> *"it was a no-news Monday and the next day had Powell, so AM session that next day was out of
> the question."* `[@ 01:31]` — FOMC/Powell testimony days are skipped.

## Timestamped index
| time | moment |
|---|---|
| 01:31 | skips the session before a Powell/FOMC event |
| 01:54 | *"This is engineered liquidity. Doesn't really get much simpler than this."* |
| 02:16 | **THE 2-POINT MINIMUM DISTANCE RULE** |
| 02:40 | **the sweet spot — liquidity inside the rejection block's range** |
| 03:46 | why a 10-point stop was wrong on an hourly-level entry |
| 04:29 | used a 5-minute entry trigger instead of the raw level |
| 05:18 | **match trigger timeframe to level timeframe** |
| 06:26 | 20-point stop accepted because the 5m wick is 20 points; TP 200 = 1:10 |
| 06:51 | **stop size follows the PD array's size and volatility** |
| 08:03 | **alternative: stop below fib 0.79 of the wick** |
| 09:16 | admits the recent 10:00 opens have been unreadable — manipulation both sides |
| 10:01 | a level rejecting three times builds the liquidity that then breaks it |

## Candidate strategies
No new card. **This is the parameterisation layer** — the numbers that let every other zxcked
card be implemented rather than approximated.

## Grounding notes
- **Highest-value non-strategy video in the set.** Without `[@ 02:16]` we would have had to
  invent a distance threshold ourselves, and any result would then have been ours, not his.
- Note the register and delivery match the Powell own-channel videos exactly, despite the
  uploader being a third party.
