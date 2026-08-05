---
videoId: c15YLeAKc2A
title: "Powell Trades | News Highs / Lows | Dumb Money Concepts Whop"
date: 2025-08-09
duration: 7m41s
source_stream: Dumb Money Concepts Whop
trader: zxcked
prefix: zxck-
GAP_ENTRY: partial — inverse FVGs named as an entry after the sweep
NY_SESSION: YES — 08:30 and 10:00 ET, CPI/PPI/NFP
---

# News (data) highs and lows — the free draw on news days

## THE RULE — `[stated]`, and it is simple enough to test directly
> *"whichever side we take first, we're going to go for that other opposing liquidity pool. So
> if we take data low first, we're going to have a clear draw at data highs."* `[c15YLeAKc2A @ 00:00]`

> *"that's why I like trading news days because the draw on liquidity is pretty much free."*
> `[@ 03:11]`

**Definition**: the high and low made by the news candle/reaction at the release.

## THE ENTRY — `[stated]`
> *"after this got swept… you could have just taken the first 30 second change in state of
> delivery. 10 point stop, target data low, for a one to four, 40 points."* `[@ 02:47]`
> *"you can use inverse fair value gaps, whatever you want, after the data high gets swept."*
> `[@ 03:11]`

**Timeframe**: *"price action is really really fast. So you can use the 30-second or even the
15-second"* `[@ 02:24]`.

## SECOND USE — data highs/lows as key opens `[stated]`
> *"if you get a strong close above, you can basically use it as like a key open."* `[@ 04:45]`
And their wicks as wick-theory levels: *"if they leave a decent sized wick on the 15 minute, you
can use the 50% mark of that for an entry"* `[@ 06:45]`.

## THE GATE HE REPEATS
> *"engineered liquidity is the absolute most important criteria to be able to enter on a 50%
> on a wick. That's the whole trade idea… if you just try to enter on every 50% of every wick,
> you're going to get merked."* `[@ 06:45]`

## Which news
> *"only use 08:30 if there's news days — some decent news, CPI, PPI, NFP."* `[@ 05:36]`

## An honest counter-example
> *"if you tried taking the first entry after data high got swept yesterday you would have
> gotten [wrecked] because of this price action."* `[@ 01:10]` — CPI Thursday, *"absolutely
> atrocious"* `[@ 00:00]`.

## Timestamped index
| time | moment |
|---|---|
| 00:00 | **the rule — first side taken, the other is the draw** |
| 01:10 | **the CPI counter-example where it failed** |
| 02:01 | clean PPI example with equal lows at the data low |
| 02:24 | 15s/30s timeframes because news price action is fast |
| 02:47 | **first 30s CISD, 10pt stop, 40pt target, 1:4** |
| 03:11 | inverse FVGs as an alternative entry; *"the draw is free"* |
| 03:59 | second use: data highs/lows as points of control |
| 04:45 | strong close through ⇒ treat as a key open |
| 05:36 | **only 08:30 on CPI / PPI / NFP** |
| 06:45 | 50% of the data wick — but **only with engineered liquidity** |

## Candidate strategies introduced
| id | name | one line | gap-entry? |
|---|---|---|---|
| `zxck-news-draw` | **News high/low opposing draw** | Whichever side of the news range is taken first, target the other; enter on the first LTF CISD or inverse FVG | **partial** |

## Grounding notes
- **Requires the news calendar** — we hold `config/news_calendar_hist.csv` and
  `config/news_calendar.csv`, and CPI/PPI/NFP are all US releases, so this is implementable.
- 15s/30s entries are **not testable on our 1-minute data**. The rule itself (opposing draw) is
  testable on 1-minute; the entry trigger is not.
