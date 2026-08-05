---
videoId: r5_yNjXsv6k
title: "Powell Trades | Entry Triggers #2 | Dumb Money Concepts Whop"
date: 2025-08-09
duration: 5m11s
source_stream: Dumb Money Concepts Whop
trader: zxcked
prefix: zxck-
GAP_ENTRY: YES — the inverse-FVG 50% trigger
NY_SESSION: not stated
---

# Entry Triggers #2 — the inverse-FVG trigger, the fib trigger, and the closing list

## What it covers
Completes the trigger list started in `BOuJLWIisMI`.

## TRIGGER 4 — inverse FVG `[stated]`
> *"you can either enter at the 50% mark of the inverse fair value gap, but a lot of the times
> it's just going to tap slightly into it. Maybe even just barely tap it, and then go."*
> `[BOuJLWIisMI @ 04:39 → r5_yNjXsv6k @ 00:00]`

Worked: *"say we entered on the 50% mark and you keep your stop above this high… That's five
points exactly. That's perfect. And then we aim for the first swing low which is 37 points."*
`[@ 01:34]` — **5-point stop, first swing low as target, ≈1:7.**

## TRIGGER 5 — the fib `[stated]`
> *"the fifth one is like not something I really use a lot for this on the lower time frame,
> but it works and it's going to be the fib. So the first rejection leg… often times it's going
> to get retraced to 0.5 or 0.62 or 0.705."* `[@ 00:45]`
> *"the fib is better to use on the five minute time frame and then use the actual candlestick
> structure for the lower time frame confirmation entries."* `[@ 01:10]`

## THE CLOSING LIST — the canonical statement
> *"it's going to be either straight at the level, rejection block, change in state of
> delivery, or inverse fair value gap. And these are all on the one minute or three minute time
> frame."* `[@ 02:20]`

**Timeframe of the trigger: 1-minute or 3-minute.** A 5-minute trigger is allowed and he states
the trade-off explicitly:
> *"if you want even more confirmation, you can get five minute, but then you're going to lose
> a lot of entries or get slightly worse risk-to-reward, which is fine because your win rate is
> going to be higher."* `[@ 02:43]`

**That is a directly testable claim about a fill-rate / win-rate trade-off.**

## Timestamped index
| time | moment |
|---|---|
| 00:00 | inverse FVG often only barely taps — a fill-rate warning |
| 00:23 | *"price usually gives you a fair amount of entry opportunities if you look on the lower time frame"* |
| 00:45 | **trigger 5** — the fib, 0.5 / 0.62 / 0.705 |
| 01:10 | fib on the 5-minute, candlestick triggers on the LTF |
| 01:34 | worked: 50% of the inverse FVG, 5-point stop, first swing low, ≈1:7 |
| 02:20 | **the canonical four-trigger list** |
| 02:43 | **1m/3m vs 5m trigger: fewer entries + worse RR, higher win rate** |
| 03:29 | *"you have to watch the concept videos first… everything is derived from the concept videos"* |
| 04:15 | advocates taking a week off; *"five micros per account"* |

## Candidate strategies introduced
| id | name | one line | gap-entry? |
|---|---|---|---|
| `zxck-ifvg-trigger` | **Inverse-FVG 50% as entry trigger** | After a level tap, enter the 50% of a 1m/3m inverse FVG, 5-point stop, target the first swing point | **YES** |

## Grounding notes
- `zxck-ifvg-trigger` and `zxck-ifvg-50` (from the FVG video) are the **same object at
  different scales** — 1m/3m as a trigger here, 5m/15m as a standalone model there. Test both;
  do not merge them.
- The trigger-timeframe trade-off `[@ 02:43]` is a **free hypothesis** we can test at no extra
  search cost, since it is stated in advance.
