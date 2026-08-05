---
videoId: y7KMT9CIVMo
title: "Powell Trades E7 Mentorship - FIB Explanation"
date: 2026-05-19
duration: 14m22s
source_stream: E7 Mentorship  ← DIFFERENT PRODUCT from the Dumb Money Concepts Whop
trader: zxcked (channel) / Powell (material)
prefix: zxck-
GAP_ENTRY: partial — entries taken at 5-minute gaps in fib discount
NY_SESSION: partial — market-open behaviour discussed
---

# E7 FIB Explanation — the fib as a live decision procedure

## ⚠️ SOURCE-STREAM FLAG
This is **E7 Mentorship**, not the Dumb Money Concepts Whop, and it is 9 months later
(2026-05 vs 2025-08). Register and delivery differ markedly from the 2025 batch: structured,
no profanity filler, replay-driven. Statements here should be attributed to the E7 stream so a
later contradiction with a 2025 statement stays traceable. `[inferred from the transcript
itself — I make no claim about who is speaking.]`

## What it covers
The fib video the 2025 set never got: *"I realized there's not an official fib only video."*
`[y7KMT9CIVMo @ 00:01]`

## THE PROCEDURE — `[stated]`
1. **Bias first.** *"First step obviously to using a fib… is to identify bias. Where are we
   going to draw our fib? What leg is going to be valid?"* `[@ 00:01]`
2. **Wait for a reason to place it.** *"first of all, we got to kind of wait for a reason to
   place a fib… If I got like a bearish close right there, I will start looking for a re-entry
   in this bullish leg."* `[@ 01:58]`
3. **Re-anchor on each new high** `[@ 02:46]`.
4. **Enter in discount, with an LTF trigger** `[@ 03:32]`.

## THE LIMIT-ORDER LEVELS — `[stated]`, and this refines the 2025 fib video
> *"limiting the 0.5 — not really a big fan. The best levels to limit on the fib are going to
> be 0.62 and 0.705."* `[@ 11:14]`

> *"If you limit 0.62 with a stop below 705, you're getting a 1:5. Below 79, you're getting a
> 1:3, which is like the minimum risk reward that I would use."* `[@ 11:37]`

**Two stop conventions, both stated: below 0.705, or below 0.79.** He leaves the choice open
and states the trade-off: *"Are you comfortable taking more setups, getting more stop losses,
but having a higher chance of getting into the trade? Or would you rather wait for the most
discounted entry every time, running the risk of not getting in the trade at all?"* `[@ 12:49]`

## THE EDGE-TOLERANCE RULE — genuinely new, and it matters for backtesting
> *"it hits 41, and the discount is at 40. So if I get a reason to enter here, I'm not really
> going to care… It edges the discount itself by a point. But we sweep liquidity into a
> discounted PD array."* `[@ 03:32–03:54]`

> *"if you do 5-minute and you have a limit there, you're just going to get edged waiting for
> your limit to get tapped. If you get edged like this though by one point, scale down into the
> 1-minute and be like, am I getting a 1-minute reason to go long here?"* `[@ 05:04]`

**A stated tolerance for a level being missed by ~1 point, resolved with an LTF trigger.** A
strict limit-only backtest will therefore *understate* his fill rate. This is a specification
detail that would otherwise have been invented by us.

## A LOSS, shown in full
> *"13-point stop, very acceptable… this only gets a 13-point reaction, not enough to go break
> even in my opinion. But yeah, this is a loss."* `[@ 07:08]`
Then the frequency argument: *"it is important that we actually take the good setups that get
presented to us… If I take this loss which was 17 points, for 1 to 10, and then I lose and then
15 minutes later I get a new entry and it plays for a 1 to 8, I don't care about the previous
loss."* `[@ 09:01–09:44]`

## Timestamped index
| time | moment |
|---|---|
| 00:01 | bias before fib; which leg is valid |
| 01:11 | HTF context — equal highs above, tapped a daily rejection block |
| 01:34 | prefers the **5-minute** for structure and fibs |
| 01:58 | **wait for a bearish close before placing the fib** |
| 03:32 | **edge tolerance** — 1 point past discount is acceptable with a trigger |
| 03:54 | 1-minute rejection block as the confirmation |
| 04:16 | stop a couple of ticks below the discount; 15pt stop, 1:6 |
| 07:08 | **a full loss shown**, 13pt stop |
| 07:32 | re-entry at 0.62, 5-minute rejection block, 17pt stop, 1:8 |
| 08:16 | entering at the rejection-block **start** vs CE, stated as a choice |
| 09:01 | the frequency argument for taking presented setups |
| 11:14 | **limit at 0.62 / 0.705, not 0.5** |
| 11:37 | **stop below 0.705 (1:5) or below 0.79 (1:3 minimum)** |
| 12:49 | the fill-rate vs entry-quality trade-off stated explicitly |

## Candidate strategies introduced
| id | name | one line | gap-entry? |
|---|---|---|---|
| `zxck-fib-limit` | **Fib limit entry (E7 refinement)** | Limit 0.62 or 0.705 of a validated leg, stop below 0.705/0.79, 1:3 minimum | no |

## Grounding notes
- **Refines, does not contradict, `zxck-fib-705`.** 2025 said "enter 0.705, stop below 0.79";
  E7 adds 0.62 as a limit level and 0.705 as an alternative stop. Both recorded.
- *"1:3 is the minimum risk reward that I would use"* `[@ 11:37]` matches the 2025 opening-gaps
  video exactly `[rwPo6UyVOo8 @ 02:51]`. Consistent across 9 months and two products.
