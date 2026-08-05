---
videoId: tNyT7tHOmGI
title: "The setup that made me 60k in February"
date: 2026-02-19
duration: 23m46s
source_channel: "Powell trades (OWN)"
views: 176631
trader: Powell
prefix: zxck-
GAP_ENTRY: YES — 5m FVG + breaker (unicorn) at fib discount
NY_SESSION: YES — the traded example is the 10:00 ET open
---

# Fib + entry triggers — the backtest walkthrough, and the 10:00 trade

## THE FIB'S ROLE — stated flatly, and it settles a question
> *"The fib itself, in my opinion, is not a strategy. It is a confluence and a very consistent
> one."* `[tNyT7tHOmGI @ 02:23]`

**So `zxck-fib-705` should not be carded as a standalone strategy.** It is a level-refiner. That
is his own instruction and it changes how we card it.

## THE FIB VALIDITY CONDITIONS — `[stated]`
> *"for the fib to actually be valid and for us to know what leg we are trading from, we need
> this: a higher time frame PD array, some sort of liquidity that we can sweep, and for us to
> rebalance in the other direction or have a target in the other direction."* `[@ 02:45]`

**Procedure:** wait for a bearish close → anchor the fib at that high → if a new high forms,
**re-anchor** → wait for discount `[@ 03:31–03:54]`.

## THE ENTRY-TRIGGER TRADE-OFF — `[stated]`, quantified in direction
> *"instead of waiting for an inverse fair value gap, you just use a rejection block instead.
> Your win rate is going to be lower than an IFVG, but your risk reward is going to weigh up for
> it like tenfold."* `[@ 05:46]`

**A stated ordering: IFVG trigger = higher win rate, worse RR; rejection block = lower win rate,
better RR.** Testable directly, and pre-stated.

> *"5-minute entry trigger is better than a 1-minute, by the way."* `[@ 07:42]` — consistent with
`WEeXKMzaJjY`.

## THE ENTRY MECHANIC — `[stated]`
> *"you put your limit at the beginning of the rejection block. The rejection block gets made and
> the very next candle taps into it. You put your entry there, stop loss below the rejection
> block."* `[@ 06:09]`

## A LOSS, walked through deliberately
A 5-minute trigger at fib 0.5 **fails** for −12 points `[@ 08:06]`; the next one at fib 0.62
*"way better level, more discounted"* returns 1:8 `[@ 08:54–09:38]`. His conclusion:
> *"Do we care that that trade failed for a total loss of 12 points when we can hit a 1:8 right
> afterwards? No."* `[@ 09:38]`

## DAILY LIMITS — `[stated]`
> *"I usually say take max two losses a day, two to three trades per day, and stop. If you take
> three trades and they're all losers, you're offside. Just stop trading for the day."* `[@ 10:23]`

## THE 10:00 TRADE — fully specified
- 10:00 opens **lower**, wicks down 20 points — *"All we want with 10:00 a.m. is a lower wick, so
  that we can distribute to the upside"* `[@ 15:08]`
- Wants the retrace back to retest 10:00 `[@ 15:56]`
- Confluences: **fib 0.79**, a **1-minute AND 5-minute rejection block**, and the 10:00 framework
  `[@ 16:19]`
- Entry at the **start of the rejection block** (~485); **15-point stop to cover the PD-array
  midpoint** — *"that is a sensitive point usually within every single PD array"* `[@ 17:05]`
- Target 605, an unfilled gap and an old low ⇒ **1:8** (1:5 with the stop at the wick low) `[@ 17:27]`
- Break-even once the prior high was taken `[@ 18:14]`
- **$1,200 × 10 Apex accounts = $12,000** `[@ 15:30]` `[trader-claimed, unverified]`

## Timestamped index
| time | moment |
|---|---|
| 02:23 | **the fib is a confluence, not a strategy** |
| 02:45 | **fib validity conditions** |
| 03:31 | re-anchor on each new high |
| 05:46 | **IFVG vs rejection block: win rate vs RR** |
| 06:09 | **entry at the start of the rejection block, stop below it** |
| 07:42 | 5-minute trigger beats 1-minute |
| 08:06 | **a loss shown in full** |
| 08:54 | fib 0.62 as the better level |
| 10:23 | **max 2 losses / 2–3 trades per day** |
| 15:08 | **10:00 opens lower ⇒ want the lower wick ⇒ distribute up** |
| 16:19 | the confluence stack at the retest |
| 17:05 | **15-point stop to cover the PD-array midpoint** |
| 17:27 | 1:8, or 1:5 with the wider stop |
| 20:17 | Apex trailing-drawdown mechanics after the first payout |

## Candidate strategies introduced
| id | name | one line | gap-entry? |
|---|---|---|---|
| `zxck-fib-trigger-stack` | **Fib + rejection-block trigger at the 10:00 open** | Anchor the fib on the unbalanced leg, wait for discount/premium, take the 5m rejection block at the start of its wick, 15pt stop covering the PD-array midpoint | **YES** |

## Grounding notes
- **Supersedes `zxck-fib-705` as a card.** The fib is a component, per his own words `[@ 02:23]`.
- The stop rule here (*"cover the PD-array midpoint"*) is **different from and better specified
  than** the 2025 rule (*"below 0.79"*). Both recorded; this is the later statement.
