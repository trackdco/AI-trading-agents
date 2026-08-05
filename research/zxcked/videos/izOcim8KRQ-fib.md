---
videoId: -izOcim8KRQ
title: "Powell Trades | FIB | Dumb Money Concepts Whop"
date: 2025-08-09
duration: 6m27s
source_stream: Dumb Money Concepts Whop
trader: zxcked
prefix: zxck-
GAP_ENTRY: no
NY_SESSION: partial — PPI / 08:30 key open example
note: "filename drops the leading hyphen of the videoId for CLI safety; transcript file keeps it"
---

# FIB — the retracement levels and where he puts the stop

## THE SETTINGS — `[stated]`
> *"what's going to be most sensitive is the 0.5 and the 0.705. 0.62 is also going to give a
> lot of entries and if you don't want to use that with a bigger stop, then you can, but I
> prefer using the 0.705."* `[-izOcim8KRQ @ 00:00]`
> *"0.79 also a very good level."* `[@ 02:27]`

**Level set: 0.5, 0.62, 0.705, 0.79.**

## THE ENTRY/STOP RULE — `[stated]` and fully mechanical
> *"What I always do if I use the fib is I enter at 0.705 and I always put my stop like below
> the 0.79. Obviously, you can put it all the way down at the low, but that's just going to
> give you a stop that I'm not really a fan of."* `[@ 03:01]`

Worked: *"enter here, 10 point stop… Target 40 points. Target this high. Perfect. 1 to 4 in
literally three candles."* `[@ 03:29]`

## THE DISQUALIFIER — `[stated]`
> *"if there's one place where you wouldn't use it, it's this right here… Everything in this
> type of price action is just going to be drastically lower probability. Cuz it's accumulating
> for a reason."* `[@ 05:00]`
i.e. **do not fib inside a consolidation/accumulation range.**

## Where he draws it
The leg after a liquidity sweep into a level `[@ 00:49]`, best on lower timeframes `[@ 02:27]`.
Pairs with AMD / engineered liquidity `[@ 01:38]`.

## Timestamped index
| time | moment |
|---|---|
| 00:00 | **the levels — 0.5 and 0.705 most sensitive, 0.62 also usable** |
| 00:49 | draw it on the leg after a sweep into a level |
| 01:38 | pairs with AMD / engineered liquidity |
| 02:27 | best on lower timeframes; 0.79 also good |
| 03:01 | **enter 0.705, stop below 0.79** |
| 03:29 | 10-point stop, 40-point target, 1:4 |
| 04:35 | stacking example: PPI + 08:30 key open + 1m FVG + breaker + 0.5 of the leg |
| 05:00 | **disqualifier — do not use it inside accumulation** |

## Candidate strategies introduced
| id | name | one line | gap-entry? |
|---|---|---|---|
| `zxck-fib-705` | **Fib 0.705 entry** | Enter the 0.705 retrace of the leg out of a swept level, stop below 0.79, ~1:4 | no |

## Grounding notes
- **The entry/stop pair is fully specified**, which is rare here: entry 0.705, stop below 0.79.
  Risk is therefore ~8.5% of the leg, so stop size scales with leg size rather than being fixed.
- The leg-selection rule (*"the first rejection leg"* `[r5_yNjXsv6k @ 00:45]`) is the loose part.
