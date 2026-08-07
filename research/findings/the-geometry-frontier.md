---
date: 2026-08-06
status: RESULT — structural. Explains why every filter, entry and target change this session failed.
tags: [separator-scan, frontier, win-rate, expectancy, selection, ny]
script: scripts/separator_scan.py
report: output/separator_scan.md
---

# The geometry frontier — why nothing we record separates winners from losers

ANGUS 2026-08-06: *"thousands of triggers, there HAS to be something that can seperate the
winners from losers, wherever that gap is."*

There is separation. **It just doesn't pay.** And the reason is one number.

## The scan

Every causally-legal variable in the limit-entry book, identical test, ranked — 33 variables,
93 buckets, 12,131 fills over 269 sessions. Causally-legal means *knowable at order
placement*: trigger geometry, intended risk, clock time, and the daily context layer (built
from strictly prior sessions). Depth and footprint are excluded, because a limit fills mid-bar
so any bar-close read is one bar late.

| | |
|---|---:|
| base mean R | −0.111 |
| base win rate | 22.7% |
| **buckets with positive mean R** | **1 of 93** |
| spread of mean R across all 93 buckets | −0.342 → **+0.003** |
| standard deviation of mean R across buckets | 0.051 |

The single positive bucket is `risk_pts = MID` at **+0.003** — zero to three decimal places.

## The frontier

**`corr(win rate, average win size in R) = −0.855`.**

| win-rate quintile | buckets | win rate | avg win R | avg loss R | **mean R** |
|---|---:|---:|---:|---:|---:|
| lowest | 19 | 20.0% | +3.034 | −0.916 | −0.148 |
| low | 18 | 22.3% | +2.649 | −0.903 | −0.112 |
| mid | 19 | 22.7% | +2.610 | −0.899 | −0.103 |
| high | 18 | 23.3% | +2.538 | −0.902 | −0.101 |
| highest | 19 | 26.5% | +2.191 | −0.887 | **−0.088** |

Win rate moves **20.0% → 26.5%** across the book — a third more winners. Average win falls
**3.03R → 2.19R** in near-exact compensation. Mean R barely moves, and never reaches zero.

**Every variable we record is a rearrangement of the same geometry.** Filters do not select
better trades; they slide the same trade along a fixed trade-off between how often it wins and
how much it wins by. The mechanism is obvious once seen: all of these variables are proxies for
*how far the target is relative to the stop*. A nearer target wins more often for less. A
further one wins less often for more. It is one trade viewed from different distances.

## This explains the whole session

Every attempt today moved along the frontier rather than off it:

| attempt | what it changed | result |
|---|---|---|
| next-structural-level targets (rr0) | target distance | target-hit 2.8% → 24.0%, **mean R unchanged** (−0.022 → −0.015) |
| market-on-displacement entry (EC) | entry location | honest flow, **mean R ≈ 0**, stops 16.2 → 26.5pt |
| retest-close confirmation | entry timing | +8.90 pt/trade that was a **+10.57 pt head start** |
| daily trend alignment | selection | win rate **22.4–22.8% in every bucket** |
| 33-variable scan | selection | **1 of 93 buckets** above zero, and that one is zero |

Four different levers, one outcome. That is not four failures — it is one structural fact
found four ways.

## What it implies

**Selection on recorded geometry cannot fix this book.** Not because we picked the wrong
variables — because the variables available are all the same variable wearing different hats.

To leave the frontier requires information that is *not* a restatement of where the levels
are. Two candidates, and only two:

1. **Directional context that predicts whether the market will move at all** — a
   higher-timeframe thesis. Angus: *"a day im looking for shorts, im unlikely to go for a long
   unless i have strong reasoning."* Nothing in this book knows that. The trend proxy tested
   here (close vs 20-session mean in ATR units) is a lagging statistic, not a thesis, and it
   separates nothing.
2. **Order flow read at a legitimate decision point.** The limit entry structurally cannot
   provide this — it fills mid-bar, so every honest read is either before the information
   exists or after the decision. Established twice today.

Both sit *outside* the geometry. That is the whole content of this finding.

## What this does NOT say

It does not say the raw trigger population is worthless — win rate genuinely moves by a third
across buckets, so the variables carry real information. It says that information is already
priced into the target distance.

It also does not license an interaction hunt. Two variables that each slide along the frontier
will, in combination, still slide along the frontier; and 33 variables offer 528 pairs, which
is a machine for manufacturing false positives. An interaction is only worth testing if there
is a *mechanism* for it to escape the frontier — not because the singles failed.
