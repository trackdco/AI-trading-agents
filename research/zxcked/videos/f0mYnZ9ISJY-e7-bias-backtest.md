---
videoId: f0mYnZ9ISJY
title: "Powell - Top down analysis backtesting (E7 course)"
date: 2026-05-06
duration: 21m20s
source_channel: "Archive Vault (re-host of the E7 course)"
views: 992
trader: Powell
prefix: zxck-
GAP_ENTRY: partial — daily balanced price range (overlapping FVGs) drives the bias
NY_SESSION: YES — "when market opens, which daily high or low are we closest to"
---

# E7 bias backtesting — the daily-bias procedure, run blind on a random date

## Method — worth noting for its own sake
> *"I've asked ChatGPT to give me a random date, and I've flattened my chart. So we're going to
> go to that random date."* `[f0mYnZ9ISJY @ 00:00]`

**He randomises the start date rather than picking one.** A crude but real attempt at avoiding
cherry-picking, and more than most trading content does.

## THE BIAS STACK — `[stated]`, top down
1. **Daily**: is it a market maker buy/sell model? `[@ 01:13]`
2. **PXH/PXL state machine**, restated identically to the 2025 video:
   > *"price sweeps out this, closes back within, which means this is going to be the draw. And
   > then we sweep this, close back within, this is going to be the draw above; take that high,
   > close above again, take the high; close below, take the low."* `[@ 01:36]`
3. **Daily balanced price range** — *"a daily fair value gap overlapping with a daily fair value
   gap, which makes this our balanced price range"* `[@ 02:25]`
4. Then **scale down**: *"we start with the daily, break it down, we go into 4-hour, break it
   down, go into 1-hour, break it down, kind of like similar to what I just did with the daily"*
   `[@ 17:26]`

## THE OPEN-PROXIMITY QUESTION — `[stated]`, and it is a clean rule
> *"when market opens, which daily high or low are we closest to? Which 4-hour high and low?
> 1-hour high and low? What are we closest to? What are we most likely going to manipulate into?
> And what is the market expanding towards as the market opens?"* `[@ 17:49]`

**Nearest untested extreme = the likely manipulation target; the opposite = the draw.**
Mechanical and testable.

## THE LOSS TEST — the most useful idea in the video
> *"If you take a trade and you lose and you immediately have two or three reasons as to why it
> lost, it was probably not a good trade. If you get into a trade and you take a loss and you
> don't really know why that trade didn't work out, then GGs, you had a good trade setup."*
> `[@ 18:57–19:47]`

He then applies it to himself on a losing 1-minute rejection block into the 10:00 open: *"I don't
have a good reason as to why that lost. I just lost."* `[@ 20:09]`

**This is a post-trade classification rule, not an entry rule** — but it is the closest thing in
the corpus to an explicit setup-quality audit, and it maps onto what our own winner/loser autopsy
tries to do statistically.

## Timestamped index
| time | moment |
|---|---|
| 00:00 | **randomised start date** |
| 01:13 | daily MMXM read |
| 01:36 | **PXH/PXL restated — identical to `jBS22-pX3dU`, 10 months apart** |
| 02:25 | **daily balanced price range = two overlapping daily FVGs** |
| 15:32 | V-shape recovery = market maker buy model |
| 16:18 | how deep a retrace is acceptable before the model is damaged |
| 17:26 | **the recursive top-down procedure** |
| 17:49 | **the open-proximity question** |
| 18:57 | **the loss test** |
| 20:09 | applies it to his own loss at the 10:00 open |

## Candidate strategies introduced
| id | name | one line | gap-entry? |
|---|---|---|---|
| `zxck-open-proximity` | **Nearest-extreme manipulation prior** | At the open, the nearest untested D/4H/1H extreme is the manipulation target and the far side is the draw | no |

## Grounding notes
- **PXH/PXL is stated identically across 10 months and two products** (`jBS22-pX3dU` 2025-07 vs
  here 2026-05). That consistency is worth more than any single statement of it.
- The loss test is **not implementable as code**. Recorded because it is his own framing of setup
  quality, and it should not be quietly converted into a numeric filter.
