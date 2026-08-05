---
videoId: 0u1L00q77bw
title: "Powell Trades | CISD | Dumb Money Concepts Whop"
date: 2025-07-13
duration: 11m20s
source_stream: Dumb Money Concepts Whop
trader: zxcked
prefix: zxck-
GAP_ENTRY: partial — the CISD+inversion pairing is imbalance-based
NY_SESSION: YES — the example is the 09:00 ET candle into the NY open
---

# CISD — change in state of delivery. His "if I threw everything else out" concept.

## What it covers
> *"If I were to just throw everything out the window and just focus on one thing, this would
> be that one thing."* `[0u1L00q77bw @ 00:22]`

## THE DEFINITION — `[stated]`, and he distinguishes it from an order block
**CISD (bullish):** the candle **closes above the OPENING PRICE of a down-close candle**, then
price **returns to test that opening price**, then expands `[@ 02:16–02:41]`.

**vs order block:** *"this is more like an order block scenario where we expand away from the
down-closed candle… that's what's called an order block. We come down, test it, expand up."*
`[@ 07:26]` — the CISD has an **immediate rebalancing wick back into the open**; the OB does not.

**The sensitive price is the OPEN, not the body or the wick:**
> *"What's most sensitive with this candle is going to be the opening price."* `[@ 05:53]`

## Entry / stop / target — `[stated]`
- Entry: **two ticks beyond the opening price** `[@ 06:15]`; he consistently accounts for
  *"two ticks of spread"* `[@ 05:27]`
- Stop: *"let's say it did a five-point stop. I think that's what I did… it was either a five
  or a three"* `[@ 06:38]`
- Target: **true day open** `[@ 06:15]`

## The universal statement
> *"down close candles should support price going up. And up close candles should support price
> going down. And that's on every time frame. Monthly, weekly, daily, 4-hour, you name it. Like
> even 15 second."* `[@ 08:13]`

## Scalping variant — `[stated]`
> *"When I'm scalping on the 15 second… I'm just looking for us to tap into a PD array or sweep
> some liquidity like a swing point. And then I'm taking the first 15 second change in state of
> delivery."* `[@ 08:35]`

## The confluence he calls "perfect"
CISD **paired with an FVG inversion** — the same candle that inverses an FVG also creates the
CISD: *"This is a really, really good change in state of delivery… this is like perfect."*
`[@ 09:46]`

## Timestamped index
| time | moment |
|---|---|
| 00:22 | *"if I threw everything out the window"* |
| 02:16 | **definition** — close above the down-candle's open, retest that open, expand |
| 03:03 | worked example on the 1-hour, price level 18152.5 |
| 03:27 | confluence: below true day open, little trading above ⇒ leg down is manipulation |
| 04:39 | **conditional** — lower probability if it taps true day open BEFORE the entry |
| 05:53 | **the opening price is the sensitive level** |
| 06:15 | **entry 2 ticks beyond the open, TP at true day open** |
| 06:38 | 5-point (or 3-point) stop |
| 07:26 | **CISD vs order block** distinction |
| 08:13 | the up/down-close universal rule |
| 08:35 | 15-second scalping variant |
| 09:46 | CISD + FVG inversion = "perfect" |

## Candidate strategies introduced
| id | name | one line | gap-entry? |
|---|---|---|---|
| `zxck-cisd` | **CISD retest** | Close beyond a prior candle's open, retest that open, expand; 2-tick entry, ~5pt stop, TP true day open | no |
| `zxck-cisd-inversion` | **CISD + FVG inversion** | The CISD candle also inverses an FVG — his highest-confluence version | **YES** |
| `zxck-15s-cisd-scalp` | **15-second CISD scalp** | After a PD-array tap or sweep, take the first 15s CISD for ~10 points | no |

## Grounding notes
- `zxck-15s-cisd-scalp` requires **sub-minute data we do not hold**. Flag as untestable with
  current data rather than approximating it on 1-minute bars.
- *"This is my first time teaching anything ever"* `[@ 10:58]`.
