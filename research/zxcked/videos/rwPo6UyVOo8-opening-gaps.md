---
videoId: rwPo6UyVOo8
title: "Powell Trades | Opening Gaps | Dumb Money Concepts Whop"
date: 2025-08-09
duration: 6m37s
source_stream: Dumb Money Concepts Whop
trader: zxcked
prefix: zxck-
GAP_ENTRY: YES
NY_SESSION: implied (new day / new week opens)
---

# Opening gaps — new week and new day opening gaps as bias and as level

## What it covers
The **New Week Opening Gap (NWOG)** and **New Day Opening Gap (NDOG)** as (a) a free
directional bias and (b) a level to trade from.

Tooling is named explicitly: *"It's called the ICT NOG by Lux ALGO. It's literally the only
indicator I use"* `[rwPo6UyVOo8 @ 00:01]`, with **the last four or five** gaps plotted `[@ 00:26]`.

## The rules he actually states
- **Unfilled gap ⇒ free bias.** *"if you see a gap like this… that is unfilled, like there's
  zero trading inside of that gap… That's a free bias. That's going to be your bias."*
  `[@ 03:18]`
- **Gaps get filled.** *"if you see a gap with no volume inside, just know that 90% of the
  time we're going to — 95% of the time we're going to come back and fill that gap"*
  `[@ 05:40]` `[trader-claimed, unverified]`
- **Entry treatment = like a key open.** *"I would kind of treat it as a key open like you
  wait for a candle to close above or below um to actually enter on it"* `[@ 01:39]`
- **Or as a gap fill** — take the complete fill `[@ 02:01]`.
- **Or break-and-retest** after price has spent time inside the gap `[@ 06:05]`.

## Risk / management stated here
- *"1 to three minimum preferably one to four"* `[@ 02:51]`
- **Daily stop rule**: *"if the first trade is a win then get off. If the first trade is a
  loss, d-risk 50%; if that's a loss get off. If that's a win get off"* `[@ 02:51]`
- Prefers **5-minute** entries over 1-minute for psychological reasons `[@ 04:52]`.

## Timestamped index
| time | moment |
|---|---|
| 00:01 | indicator named (Lux Algo ICT NOG), last 4–5 gaps |
| 01:15 | **the best use** — gap rallies away without being tapped ⇒ bias |
| 01:39 | **entry rule**: treat as a key open, wait for a candle close through |
| 02:01 | alternative — trade the complete fill |
| 02:51 | **risk rules**: 1:3 min / 1:4 preferred; the two-trade daily stop |
| 03:18 | **unfilled gap = bias**, stated flatly |
| 05:40 | 90–95% fill claim |
| 06:05 | break-and-retest usage after consolidation inside the gap |

## Candidate strategies introduced
| id | name | one line | gap-entry? |
|---|---|---|---|
| `zxck-nwog-bias` | **Unfilled NWOG/NDOG bias** | An untouched opening gap sets the day's directional bias | **YES** |
| `zxck-gap-close-through` | **Opening-gap close-through entry** | Wait for a candle to close beyond the gap, then enter on the retest | **YES** |

## Grounding notes
- The 90–95% fill rate is his estimate, given verbally, with no sample. Flagged
  `[trader-claimed, unverified]` and it is directly testable.
- *"This is kind of hard to teach"* `[@ 01:39]` — his own words; the entry is the least
  specified part.
