---
videoId: rQUMdf1gLJk
title: "Powell Trades | Risk Management | Dumb Money Concepts Whop"
date: 2025-07-13
duration: 8m26s
source_stream: Dumb Money Concepts Whop
trader: zxcked
prefix: zxck-
GAP_ENTRY: no
NY_SESSION: not stated
---

# Risk Management — trailing stops, stated as a structure rule

## What it covers
Despite the title this is **entirely about trailing**. It is the management layer for every
zxcked model.

## THE TRAILING LADDER — `[stated]`
| step | rule | quote |
|---|---|---|
| 1 | after the entry-trigger CISD, trail to **the low it made, or break-even** | *"after we get this change in state of delivery I would either always trail my stop to the low that we made or my break even"* `[@ 00:50]` |
| 2 | on tapping opposing LTF structure, trail **below the last 1m/3m/5m order block** | *"if we tap into 3 minute or 5 minute or 15 minute bearish structure… I would trail my stop to below the last one minute order block"* `[@ 01:37]` |
| 3 | trail to **swing lows once they are validated** | *"a swing low becomes valid when we take out this high"* `[@ 02:00]` |

**Why that level**: *"we closed above this down-closed candle. And as you guys know, every
down-close candle that we close above should support price going up"* `[@ 02:50]` — the trail
sits on the same CISD logic as the entry.

## The safest version — `[stated]`
> *"five minute structure is probably the best and safest way to trail your stop."* `[@ 06:30]`

## A stated mistake
He trailed to 170 instead of 160 and was stopped *"at exactly 170"* `[@ 04:02]`. *"I realized
that was a mistake."*

## Why he trails aggressively — context that matters
> *"the reason that I'm that aggressive with my stops, even on micros, is because I'm on 14
> accounts. So $100 is like $1,400."* `[@ 04:02]`

**His trailing is prop-account-driven, not market-driven.** Anyone testing this should know the
aggression has an account reason behind it.

## The closing rule
> *"trailing your stop where it makes sense and then have like a minimum profit day, maximum
> loss day and just stick to that."* `[@ 08:01]`

## Timestamped index
| time | moment |
|---|---|
| 00:50 | **step 1** — trail to the trigger low / break-even |
| 01:37 | **step 2** — below the last 1m (or 3m/5m) order block on opposing structure |
| 02:00 | **step 3** — validated swing lows |
| 02:50 | the justification — down-close candles support price up |
| 04:02 | **the 14-account context**; the stated mistake |
| 05:14 | *"the reason that I trade the way I trade is because I'm impatient"* |
| 06:04 | keep trailing until stopped; or split contracts |
| 06:30 | **5-minute structure is the safest trail** |
| 08:01 | minimum profit day / maximum loss day |

## Candidate strategies introduced
None — this is the **management layer**, shared across all zxcked cards.

## Grounding notes
- **Directly comparable to ash10hazard's A4/A5.** ash10hazard states a 50% break-even then
  disowns systematic trailing; zxcked gives a three-step structure-based ladder and keeps it.
  Both are structure-based; zxcked's is more specified.
- Trailing is what makes his 1:8–1:17 claims hard to reproduce — a trailed exit is not a fixed-R
  exit, so his RR figures and a fixed-target backtest are **not measuring the same thing**.
