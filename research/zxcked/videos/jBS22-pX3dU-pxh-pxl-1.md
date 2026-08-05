---
videoId: jBS22-pX3dU
title: "Powell Trades | PXH / PXL #1 | Dumb Money Concepts Whop"
date: 2025-07-13
duration: 7m51s
source_stream: Dumb Money Concepts Whop
trader: zxcked
prefix: zxck-
GAP_ENTRY: no (but NWOG overrides the rule — see below)
NY_SESSION: partial — daily-level bias, applied intraday
---

# PXH / PXL — previous-day high/low as a daily bias state machine

## What it covers
The first thing he marks every day. **A fully mechanical bias rule**, walked bar by bar
across ~25 daily candles.

## THE RULE — `[stated]`, and it is unusually complete
> *"all it is is just open, high, low, close. So we close above this, which means that we now
> want this high to get taken."* `[jBS22-pX3dU @ 00:23]`

**State machine:**
| observation | expectation |
|---|---|
| daily candle **closes above** the previous day's high | the **next** high gets taken |
| closes **back below** a high after taking it | the **low** gets taken |
| closes **below** the previous day's low | the next **low** gets taken |
| bullish candle, ambiguous close | default to the **high** `[@ 03:31]` |

## THE OVERRIDE — `[stated]`
> *"we have this huge new week opening gap. So we're not going to expect price to come all the
> way back down here… New week opening gaps is the most powerful PD array there is. So fading
> this PD array is so dumb."* `[@ 04:46–05:34]`

**An unfilled NWOG in the path overrides the PXH/PXL expectation.** This is a stated
interaction between two of his own models — rare and valuable for implementation.

## Scope
> *"you can use this pretty much anywhere with context — previous session high/low, previous
> 4-hour high and low, 1 hour high and low. But the daily is what has the biggest win rate.
> The daily is probably the most powerful time frame."* `[@ 00:01]` `[trader-claimed, unverified]`

## Honest failure disclosure
He narrates the failures as they occur: *"fails right there. Doesn't matter"* `[@ 01:35]`,
*"that fails miserably"* `[@ 03:54]`, *"I'm not going to sit here and pretend like everything
is 100% win rate"* `[@ 02:00]`.

## Timestamped index
| time | moment |
|---|---|
| 00:01 | scope — daily has the biggest win rate |
| 00:23 | **the rule stated** |
| 01:12 | pairing with the CISD it creates |
| 02:00 | explicit non-claim of 100% win rate |
| 02:45 | *"this little move from close to low is 100 points"* — scalp inside the bias |
| 03:31 | tie-break: bullish candle ⇒ expect the high |
| 04:46 | **NWOG override** |
| 06:00 | example resolving into a wick CE — cross-ref to wick theory |
| 07:11 | this is step 1 of the top-down analysis |

## Candidate strategies introduced
| id | name | one line | gap-entry? |
|---|---|---|---|
| `zxck-pxh-pxl` | **PXH/PXL daily bias state machine** | Daily close beyond the prior high/low sets which side gets taken next; unfilled NWOG overrides | no |

## Grounding notes
- **This is the closest analogue to `ash-unicorn-sb`'s A6 daily-bias state machine**, and it is
  *better specified* than ash10hazard's — the transitions are stated, not inferred.
- It is a **bias input**, not a standalone entry. No stop or target is given.
