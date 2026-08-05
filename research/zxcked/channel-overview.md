---
date: 2026-08-07
trader: Powell (surfaced via the zxcked channel; his own channel is "Powell trades")
prefix: zxck-
scope: POWELL TRADES MATERIAL ONLY
catalog: research/zxcked/CATALOG-INGESTED.txt
classification: research/zxcked/CLASSIFICATION.md
---

# Powell — channel overview

> **PB-course content is EXCLUDED and is not represented anywhere in this file.** The 7
> "PB Trading" videos on the zxcked channel are a different trader's material (Blake / PB
> Trading) that zxcked re-hosts. They were classified out at Stage 1, never transcribed, and
> contribute nothing below. See `CLASSIFICATION.md`.

## What was ingested

**39 transcripts, 38 unique videos, ~10.5 hours**, spanning **2025-05-31 → 2026-05-19**.

| source | n | what it is |
|---|---|---|
| zxcked / "Dumb Money Concepts Whop" | 24 | the 2025 private-Discord course, re-hosted |
| **"Powell trades" (his own channel)** | **6** | **the primary source — public, and the authority on any conflict** |
| Archive Vault ("E7 course") | 4 | the 2026 mentorship, re-hosted (1 is a duplicate) |
| zxcked / "E7 Mentorship" | 2 | same mentorship, different re-host |
| stef / YohanNQ / Angus | 3 | third parties; 2 re-host Powell, 1 teaches his concept independently |

**One confirmed duplicate**: `lW8FrJplMV0` (Archive Vault, "Powell's Model #1") is the same
recording as `wS-dBenAIlY` (zxcked, "Wick Theory #1") — Jaccard 0.953, next-highest pair below
0.45. It is excluded from the unique count and contributes no corroboration weight.

**Attribution rule applied throughout:** Powell's own channel > his re-hosted course material >
third parties. Third-party statements are never merged into Powell's cards.

## The approach, in one paragraph

Powell trades **NQ futures**, almost entirely the **New York AM session**, on **prop accounts**
(Apex, ~10–20 at a time). He is a **level trader**: the day is built from a small set of
pre-marked horizontal levels, and a trade happens when price sweeps liquidity into one of them
and rejects. He is explicit that he is not running an ICT model — *"I trade his concepts, but I
don't… like you guys act like ICT is the be-all end-all"* `[AGmRZ9Te9NY @ 00:23]` — and he
departs from ICT definitions where he prefers his own. His stated style is **high risk-reward,
decent win rate, low trade frequency**: *"I might take like three trades per week"*
`[Y-oqSZmNo4U @ 17:05]`, with a **1:3 floor and a 1:4–1:6 working band** `[WEeXKMzaJjY @ 15:56]`.

## Markets and sessions

| | |
|---|---|
| instrument | **NQ / MNQ** (named `[D-suu0f3XKI @ 01:32]`, `[rzfgAEYhxCg @ 03:35]`) |
| primary session | **New York AM** — *"I was busy during New York AM that day"* is given as the reason a London trade was an exception `[AGmRZ9Te9NY @ 00:23]` |
| the anchor time | **10:00 ET**, because it is the 4-hour candle open `[Y-oqSZmNo4U @ 00:49]` |
| secondary | **08:30 ET, but only on CPI / PPI / NFP** `[c15YLeAKc2A @ 05:36]`, `[Y-oqSZmNo4U @ 18:12]` |
| other levels | 18:00, midnight, 09:30, 13:00 ET `[38YtF6xFX4o @ 00:00]`, `[rsbBubev4PM @ 00:22]` |
| skipped | FOMC / Powell-testimony sessions `[xae9AiV5Ps4 @ 01:31]`; Mondays and holiday weeks by preference `[5pL41Pl7GM4 @ 02:23]` `[inferred — a habit, never stated as a rule]` |
| ES | used for **SMT**, both as an entry enhancer and as a live **exit** signal `[4COROwkO3DI @ 03:41]` |

## The building blocks, and how they fit

The corpus is not a set of independent strategies. It is **one stack**, and almost every video
is a layer of it.

```
  BIAS          PXH/PXL daily state machine  →  session extremes  →  MMXM (V/A shape)
                                    ↓
  LEVEL         key opens (10:00, midnight, 18:00, 09:30, 13:00, 08:30-news)
                opening gaps (NWOG/NDOG)  ·  FVGs  ·  order blocks  ·  breakers
                news highs/lows  ·  fib 0.5 / 0.62 / 0.705 / 0.79
                                    ↓
  GATE          engineered liquidity beyond the level  (equal highs/lows = best)
                                    ↓
  TRIGGER       straight limit  |  rejection block  |  CISD  |  inverse FVG  |  fib
                                    ↓
  MANAGEMENT    5-pt floor stop, sized to the PD array · BE on structure · trail to swing
                lows / 1m-5m order blocks · 1:3 min, 1:4-1:6 band · max 2 losses/day
```

### The gate that appears in almost every video

**Engineered liquidity beyond the level.** It is stated in wick theory `[D-suu0f3XKI @ 02:17]`,
gap fill `[86DOt135Wts @ 03:35]`, entry triggers `[BOuJLWIisMI @ 00:23]`, news highs/lows
`[c15YLeAKc2A @ 06:45]` and the FAQ `[xae9AiV5Ps4 @ 01:54]`. Without it he wants a confirmation
trigger; with it he will limit blind — *"the confirmation is to the left of the chart"*
`[EaxfhUS4eNg @ 02:45]`.

**And it is the only gate in the corpus with a number attached:**
> *"if it's like two points or less away from the CE, I'll just not take it, because at that
> point I count the CE as already mitigated"* `[xae9AiV5Ps4 @ 02:16]`, with the sweet spot being
> liquidity sitting **inside the rejection block's own range** `[@ 02:40]`.

### His own ranking of what matters

Stated, unprompted, more than once — and therefore a **pre-registered priority we did not
construct**:

| rank | concept | evidence |
|---|---|---|
| 1 | **rejection blocks / wick CE** | *"rejection blocks being number one"* `[Y-oqSZmNo4U @ 15:54]`; the "use nothing else" model `[dlSXQgM1ZpA @ 02:41]` |
| 2 | **key opens (10:00)** | *"key opens being number two"* `[Y-oqSZmNo4U @ 15:54]` |
| 3 | **inverse-FVG 50%** | stated as a standalone model three separate times `[lRgsHGWzO9E @ 07:44]`, `[r5_yNjXsv6k @ 01:34]`, `[dlSXQgM1ZpA @ 03:51]` |

He also gives a **hierarchy of entry types by how discounted they are**: rejection block → CISD
→ inverse FVG → breaker `[asi9nTJywN4 @ 03:53]`.

## The four mechanisms he actually claims

These are the falsifiable parts, and all four are stated before we looked at anything:

1. **~97% of 4-hour candles wick both sides of their open** — so the 10:00 open gets traded
   through in both directions `[Y-oqSZmNo4U @ 01:15]`. Midnight: ~95% `[@ 14:17]`.
2. **A displacement candle is what separates a good rejection block from a bad one** — one
   1-minute candle that is simultaneously a rejection block, an inverse FVG and a CISD
   `[pMv3USznFdU @ 06:39]`.
3. **NFP reverses at the open; CPI continues all day** `[WEeXKMzaJjY @ 03:58]`.
4. **Unfilled gaps get filled 90–95% of the time** `[rwPo6UyVOo8 @ 05:40]`, and an unfilled NWOG
   alone is sufficient bias `[AGmRZ9Te9NY @ 01:12]`.

## What he never specifies

Recorded so nobody fills these with generic ICT theory later:

| gap | where it bites |
|---|---|
| **"tap into something significant"** | the precondition for every rejection block. Undefined across 10 months and both products `[vWz5HvbuR-8 @ 05:16]`, `[asi9nTJywN4 @ 00:00]` |
| **"original consolidation" / the range** | MMXM and AMD both hinge on a range recognised by eye `[lPbKWoBShLI @ 00:23]`, `[EaxfhUS4eNg @ 00:46]` |
| **manipulation-wick size** | 2 points is *"not sufficient"*, 10 points is *"not very good"* `[5pL41Pl7GM4 @ 01:36, 02:46]` — the threshold is above 10 and he never names it |
| **which fib leg** | partly solved by the rebalance rule `[Y-oqSZmNo4U @ 09:30]`, but leg selection still needs *"a reason"* `[y7KMT9CIVMo @ 01:58]` |
| **target selection** | *"internal structure or a static RR"* `[a3LzCUZU5ko @ 06:18]` — a choice, never a rule |

## Two things that would be easy to get wrong

**1. His rejection block is not the ICT rejection block.** It requires a candle to CLOSE in the
trade's direction, and he says so while explicitly rejecting the ICT definition
`[a3LzCUZU5ko @ 01:34]`, `[AGmRZ9Te9NY @ 03:11]`. Implementing the ICT version would be testing
someone else's model under his name.

**2. His stop sizes are not a contradiction, they are a time series.** 2–3 point stops in 2025,
10–20 points in 2026, with the reason given: *"I used to do two to 10 point stops when I was
broke because I couldn't handle losses"* `[AGmRZ9Te9NY @ 05:06]`. The governing rule is that
**stop size follows the PD array's own size and the day's volatility** `[xae9AiV5Ps4 @ 06:51]`.
Test the later numbers.

Both his **break-even policy** and his **aggressive trailing** are explicitly driven by Apex
trailing-drawdown rules `[5pL41Pl7GM4 @ 24:46]`, `[rQUMdf1gLJk @ 04:02]` — account artefacts,
not market claims, and a fixed-target backtest is therefore **not measuring the same thing** as
his quoted R-multiples.

## Where this pools with ash10hazard

| | ash10hazard | Powell |
|---|---|---|
| session | AM1 macro **09:45–10:15 ET** | the **10:00 ET** key open |
| instrument | NQ | NQ / MNQ |
| entry object | FVG **near edge**, first touch | key open / wick CE; and FVG **far edge** on gap fill `[86DOt135Wts @ 00:50]` |
| stop | order-block edge, ~25pt median | 5–15pt, sized to the PD array |
| bias | daily FVG state machine (inferred aggregation) | **PXH/PXL state machine (stated transitions)** |
| quality gate | displacement delta (our F1) | **displacement candle (his, stated)** |
| ES | leading trigger — not implementable, no data | SMT entry filter **and exit** — same blocker |

**Two independent traders, same instrument, same half-hour, incompatible entries.** That is the
most valuable thing this ingest produced: a genuine A/B on the same 30 minutes of the day, where
neither spec was written with the other in mind. And **both are blocked on the same missing ES
data**, which raises the value of sourcing it.

Powell's gap-entry cluster (`zxck-ifvg-50`, `zxck-gap-fill-edge`, `zxck-displacement-rb`) is
what pools with `ash-unicorn-sb`'s retracement-participation work at Stage 3.

## Reliability — recorded, not editorialised

- Posts executions and payout screenshots routinely; claims *"$1,200 per account × 10 Apex
  accounts"* `[tNyT7tHOmGI @ 15:30]` and *"almost $100,000 on this cycle"* `[@ 23:18]`. All
  `[trader-claimed, unverified]`.
- **Shows losses in full**, including ones he caused: a 7-point stop he deviated to and was
  stopped on to the tick `[rzfgAEYhxCg @ 01:35]`, a 12-point loss walked through deliberately
  `[tNyT7tHOmGI @ 08:06]`, a day he took no trade at all `[Y-oqSZmNo4U @ 22:31]`.
- States non-claims plainly: *"I'm not going to sit here and pretend like everything is 100% win
  rate"* `[jBS22-pX3dU @ 02:00]`.
- Has a **commercial interest**: a $315 course `[AGmRZ9Te9NY @ 08:09]` and an Apex affiliate code
  `[tNyT7tHOmGI @ 19:55]`. Noted because it is a reason his framing favours prop accounts, not a
  reason to discount the technicals.

**No performance figure in this corpus has been verified and none should be carried into a card
without the `[trader-claimed, unverified]` tag.**
