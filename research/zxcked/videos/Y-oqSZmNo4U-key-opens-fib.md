---
videoId: Y-oqSZmNo4U
title: "How to find tick precision entries everyday"
date: 2025-10-17
duration: 24m48s
source_channel: "Powell trades (OWN)"
views: 257454
trader: Powell
prefix: zxck-
GAP_ENTRY: YES — 5m/15m gaps used as the PD array at the key open
NY_SESSION: YES — the 10:00 ET open is the entire subject
---

# Key opens + fib — THE most complete strategy statement in the whole corpus

## Why this is the centrepiece
His stated #2 concept (*"rejection blocks being number one, key opens being number two"*
`[Y-oqSZmNo4U @ 15:54]`), specified end to end: what the level is, why it works, how to draw
the fib, stop sizing, and session timing.

## THE MECHANISM — stated, and it is falsifiable
> *"the way that I use the 10 a.m. key open specifically is I use it on the 4 hour first and
> foremost. The 10:00 a.m. is the 4-hour candle open. Now, if you look at all these candles on
> the 4-hour time frame… They all have wicks on the top and on the bottom. Like 97% of them do
> at least. So, knowing this, we can expect our 10:00 a.m. open to go in one direction and then
> for it to manipulate in the other direction."* `[@ 00:49–01:40]`

**The claim: ~97% of 4-hour candles have both an upper and a lower wick, so the 10:00 open will
be traded through in both directions.** That is directly measurable on our data and costs one
trial.

Same for midnight: *"95% of the time we will manipulate either below or above midnight open and
then we will start the actual move."* `[@ 14:17]` `[trader-claimed, unverified]`

## THE TRADE — `[stated]`
1. Mark the **10:00 ET opening price** (the 4-hour candle open) `[@ 02:25]`
2. Wait for the **manipulation leg** through it `[@ 02:51]`
3. Require the open to coincide with a **PD array** (order block / FVG) `[@ 03:15]`
4. Draw the **fib high→low on the unbalanced leg**, and require the key open to land on a fib
   level — 0.79 for a premium short, 0.5/0.62 for a discount long `[@ 04:49, 11:11]`
5. **Limit at the key open** `[@ 05:12]`
6. **Stop 10–15 points** (27 if playing safe) `[@ 06:20, 07:52]`
7. Target the first internal low/high — *"a 6.6 RR, which is typically what I would go for. I go
   for everything from 1 to 4 to 1 to 6"* `[@ 06:46]`

## THE FIB-ANCHORING RULE — genuinely technical, and nobody else states it
> *"These little legs are constantly getting rebalanced, which means that from high to low, the
> unbalanced range continuously changes… this leg has already rebalanced to 50%. 50% is like —
> okay, that's a new leg now, I can't use that fib in the same area anymore… So where I would
> have to actually draw the fib would be this high, because this high we have not rebalanced
> anywhere."* `[@ 09:30–10:43]`

**Anchor the fib to the most recent high whose leg has NOT been 50%-rebalanced.** That is a
complete, implementable rule and it removes the biggest discretionary element in his fib work.

## THE MIDNIGHT-OPEN-AS-TARGET RULE — `[stated]`
> *"If we see this where we have no or barely any manipulation below midnight open and we rally
> like this, you can actually use midnight open as a target… 90 to 95% of the time if this up
> move was the real move we would have a bigger down move below midnight open."* `[@ 14:41–15:31]`

Same logic applied to 10:00: *"we close aggressively above 10 a.m., but we have no manipulation
below it, which means I'm not going to long. Longs are out of the question. Now I can find a
short setup up here and then target 10 a.m. open."* `[@ 19:52]`

## SESSION ROUTINE — `[stated]`
> *"I like to just go on the chart at 10 a.m. If there's news at 8:30, I'll trade a data high/low
> setup at 8:30 if it appears. If not, I'll look at 10 a.m."* `[@ 18:12]`
> *"I might take like three trades per week and they are just high quality trades… high RR,
> decent win rate, low trade frequency."* `[@ 17:05, 23:19]`

## Timestamped index
| time | moment |
|---|---|
| 00:49 | **10:00 ET = the 4-hour candle open** |
| 01:15 | **the ~97% both-wicks claim — the mechanism** |
| 02:25 | mark the opening price off the 4-hour candle |
| 03:15 | good vs bad order block: same criteria as a rejection block |
| 04:49 | **fib drawn high→low; key open landing on 0.79 is ideal** |
| 05:34 | **limit at the key open** |
| 06:20 | **10–15 point stop**; 27 for the conservative version |
| 06:46 | 6.6 RR; his band is 1:4–1:6 |
| 07:29 | volatility warning — peak NY AM can make 10–15pt stops wrong |
| 09:30 | **THE FIB-ANCHORING RULE — skip legs already 50%-rebalanced** |
| 11:11 | key open landing in fib discount |
| 13:08 | stop above the 5-minute FVG (25pt) also covers fib 0.62 |
| 14:17 | **midnight open: 95% manipulate first** |
| 14:41 | **no manipulation below ⇒ midnight open becomes the TARGET** |
| 15:54 | rejection blocks #1, key opens #2 |
| 18:12 | **routine: 08:30 only on news, otherwise 10:00** |
| 19:03 | worked example of the no-manipulation case |
| 22:31 | a day he took NO trade because the entry never came |

## Candidate strategies introduced
| id | name | one line | gap-entry? |
|---|---|---|---|
| `zxck-10am-keyopen` | **10:00 ET key-open limit** | Limit at the 10:00 open after the manipulation leg, requiring a PD array and a fib level to coincide; 10–15pt stop, 1:4–1:6 | **YES** |
| `zxck-4h-both-wicks` | **The both-wicks base rate** | ~97% of 4-hour candles wick both sides of their open — a pure measurement, no trade | no |
| `zxck-open-as-target` | **Un-manipulated open as a target** | If price never traded through the open before moving, the open becomes the draw | no |

## Grounding notes
- **`zxck-4h-both-wicks` is free to test** — it is a base-rate measurement with a pre-stated
  number (97%), so it costs no selection budget and either supports or kills the mechanism
  behind `zxck-10am-keyopen`. **Do this first.**
- **The 10:00 ET open sits inside ash10hazard's AM1 window (09:45–10:15).** Two independent
  traders, same instrument, same half hour, incompatible entries: ash enters an FVG after a
  sweep+MSS with a ~25pt stop; Powell limits the open with a 10–15pt stop.
