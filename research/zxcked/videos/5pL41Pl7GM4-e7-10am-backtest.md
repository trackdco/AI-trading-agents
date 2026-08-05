---
videoId: 5pL41Pl7GM4
title: "Powell - 10am key opening (E7 course)"
date: 2026-04-20
duration: 30m14s
source_channel: "Archive Vault (re-host of the E7 course)"
views: 22672
trader: Powell
prefix: zxck-
GAP_ENTRY: YES — 5m/15m gaps and 1m inverse FVGs at the open
NY_SESSION: YES — the 10:00 ET open is the whole video
---

# E7 10:00 key open — a multi-day backtest walkthrough, with the good/bad wick criterion

## What it covers
Roughly ten trading days walked in replay, each judged on whether the 10:00 open produced a
tradeable setup. **The closest thing in the corpus to a systematic review.**

## THE GOOD-VS-BAD MANIPULATION CRITERION — `[stated]`, and it is quantitative-ish
> *"this is a good example of what we would call a good wick versus a bad wick… do we have
> sufficient manipulation? On the 4-hour, barely anything. This is a two-point wick. Do we see
> that as sufficient? No. Does it count as good manipulation? No."* `[5pL41Pl7GM4 @ 01:36–01:58]`

Later, a 10-point wick: *"Is this better as a manipulation leg? Yes, it is, 10 points. Is it very
good? No."* `[@ 02:46]`

**So: 2 points is insufficient, 10 points is marginal.** The threshold sits above 10. He never
names an exact number, and I am not inventing one.

## THE ORDER-BLOCK-AT-THE-OPEN VARIANT — `[stated]`
> *"10:00 a.m. opens, and then we close this candle forming an order block here. We close below
> the opening price, which means we can use the opening price of this as an actual order
> block."* `[@ 19:57]`

## THE ENTRY-QUALITY TRADE-OFF — stated as an explicit choice, three times
> *"do I use the 5-minute structure and get a better entry, or do I just use the 1-minute
> structure and get a more guaranteed entry? And there's no right or wrong."* `[@ 23:17]`
> *"with the better entries, you're going to get a smaller stop loss and be less susceptible to
> getting stopped at break-even. But you're also going to be more susceptible to getting edged or
> not getting in the trade at all."* `[@ 24:03]`
> *"for me, when we have these scenarios, I usually just take the closest entry, and I take the
> bigger risk."* `[@ 24:25]`

**His own preference: take the closer entry with the bigger stop.**

## THE TIMING FRAMEWORK — restated
> *"10:00 a.m. is just a framework that we want to work within. It gives us structure to go off
> of in terms of time and candle opens… If there's 8:30 news, I'll look at the chart at 8:30. If
> not, I will have the peace of mind usually until 10:00 a.m."* `[@ 27:53]`

And entering **before** 10:00 is permitted with conviction: *"you would have entered before 10:00
a.m. Which, can you do that? Yes, if you have really strong conviction."* `[@ 27:29]`

## Break-even policy
> *"I prefer to go break even because with these Apex accounts I have some pretty aggressive
> trailing drawdown, which is not very kind on your accounts."* `[@ 24:46]`
**His break-even rule is prop-firm-driven, exactly as his trailing is.**

## Timestamped index
| time | moment |
|---|---|
| 00:24 | hybrid of key opens and rejection blocks |
| 01:36 | **good vs bad manipulation wick — 2 points is not sufficient** |
| 02:23 | *"this is Monday, probably would not have traded this anyway"* |
| 02:46 | 10-point wick is better but *"not very good"* |
| 19:57 | **the 10:00 candle itself as an order block** |
| 20:18 | fib anchored at the 10:00 candle |
| 21:22 | 1-minute rejection block as the trigger, 8-point stop |
| 22:55 | 5.6 RR aiming at a 1-minute gap |
| 23:17 | **the 5m-vs-1m entry-quality trade-off** |
| 24:25 | **his preference: closest entry, bigger risk** |
| 24:46 | break-even because of Apex trailing drawdown |
| 25:30 | *"pretty much all of these days, if you just soup the 10:00 key open into a rejection block or one other PD array, you would have gotten a juicy take profit"* `[trader-claimed, unverified]` |
| 27:29 | entering before 10:00 is allowed with conviction |
| 27:53 | **the routine: 08:30 only on news, otherwise 10:00** |

## Candidate strategies
Refines `zxck-10am-keyopen` with the **manipulation-size criterion** and the
**open-candle-as-order-block** variant.

## Grounding notes
- **Skips Mondays and holiday weeks by preference** `[@ 02:23, 29:06]` — a day filter he applies
  but never states as a rule. Recorded as an observation, not a rule.
- The claim at `[@ 25:30]` that nearly every day worked is exactly the sort of retrospective
  walkthrough that a backtest exists to check.
