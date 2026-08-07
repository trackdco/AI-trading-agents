---
date: 2026-08-07
status: TESTED — no edge found
tags: [ict, inversion, fvg, liquidity-sweep, prop, blake]
source: PB Blake charting-session transcript ("Blake's model" / PB Mech)
---

# PB Blake's mechanical inversion model — tested

## The model, as stated

1. Price sweeps a **significant** liquidity pool — PDH/PDL, overnight high/low, London high/low,
   or the AM session high/low. Not a random swing.
2. Structure: swing low → swing high → lower low (mirrored for shorts). The sweep is the
   **second** leg, not a first-leg breakdown.
3. After a sweep the market must **rebalance**, so the sweep leg must have left a fair value gap.
4. Entry = inversion of the **highest-timeframe** FVG in that leg. 15m → 10m → 5m → 3m, take the
   highest that exists. 3m is the floor.
5. Stop at the swept extreme.
6. TP1 = the nearest **unmitigated** FVG beyond entry (the *internal* draw). Half off, stop to
   break even.
7. Runner to *external* liquidity — equal highs/lows, session extremes.
8. Windows 09:30–11:10 and 13:00–15:00 only. No lunch.

SMT is not in the tested version: Blake removes it himself on reflection in the transcript
("I rarely see SMT fair value gaps… I'm just going to take that off").

Claim: **">80% win rate."**

## Result — 712 trades, 444 days, 2023–2026

| | win | PF | avg R | TP1 | median TP1 |
|---|---:|---:|---:|---:|---:|
| **all** | **48.2%** | **0.75** | **−0.131R** | 48.2% | 0.96R |
| 2023 | 53.4% | 0.81 | −0.087R | | 0.85R |
| 2024 | 50.0% | 0.67 | −0.165R | | 0.83R |
| 2025 | 40.7% | 0.74 | −0.153R | | 1.20R |
| 2026 | 43.8% | 0.81 | −0.106R | | 2.07R |

Negative in **every year** and in **every one of six** stop × target configurations tested
(stop at swept extreme / far edge of the inverted gap / local swing; TP1 with and without a 1R
floor). Best configuration PF 0.75; worst 0.47.

## Why the 80% claim isn't wrong — and still doesn't pay

Remove the requirement that TP1 be at least 1R away, and the hit rate jumps to **64%** with a
median payoff of **0.36R**. That is the 80%-win-rate feeling, and it is real: the nearest
unfilled FVG usually *is* close, and close targets usually *do* get hit. You just win a third of
what you lose.

Put the target at least 1R away and the hit rate collapses to **25–28%**.

Win rate and payoff are the same dial. The model does not beat that trade-off, it slides along it.

## The decisive test — the draw is not a draw

The premise is that after a sweep, price is *obliged* to rebalance toward an unfilled gap. If
true, the target should be reached more often than aimless wandering would produce.

For a driftless random walk, P(reach +kR before −1R) = 1/(1+k), exactly. Computing that per
trade from each trade's own geometry:

| | actual | random-walk null | diff |
|---|---:|---:|---:|
| **all 712** | **48.2%** | **50.4%** | **−2.3%** (z = −1.37) |
| 2023 | 53.4% | 53.1% | +0.3% |
| 2024 | 50.0% | 53.9% | −3.9% |
| 2025 | 40.7% | 48.3% | −7.6% |
| 2026 | 43.8% | 38.4% | +5.4% |
| long | 47.9% | 49.7% | −1.8% |
| short | 48.4% | 51.0% | −2.6% |

**The sweep, the structure, the highest-timeframe inversion and the unfilled-gap target together
add nothing over the geometry.** Price reaches the gap at exactly the rate a coin-flipping market
would take it there. The runner reaches external liquidity 26.5% of the time against a median
external target of 1.27R — also indistinguishable from chance.

This is the answer to "does the draw on liquidity work": as a *mechanical* object — sweep a
named pool, expect rebalancing to the nearest unmitigated gap — no. It has no measurable pull.

## Fidelity notes, because a negative result is only worth as much as the implementation

Two implementation faults were found and fixed before this verdict, both of which had been
suppressing the model:

- **Intraday bars were built from 09:30**, so no 15m gap could exist before 10:15 and the
  earliest entry in the entire book was 10:04 — starving the 09:30–11:10 window, which is the
  model's primary one. Rebuilt from 04:00 (clock-aligned for 3/5/10/15m). Trades 447 → 712,
  PF 0.60 → 0.75.
- **The sweep test also required the sweep bar to be the session extreme**, which produced 25
  trades in four years. A sweep is a level being taken, not a record being set.

Causality was held throughout: a fair value gap is not usable until its third bar has *closed*
(a 15m gap is not tradeable for up to 14 minutes after it forms), pivots are confirmed k bars
late, and entries fill at the **next** 1m open after the inverting close, never at that close.

Remaining gaps between this and what Blake trades: he does not take every trigger. He says so
directly — on live funds he waits for higher-timeframe narrative, calls the all-time-high shorts
in his own examples "very low probability", and describes the raw model as what he uses to
*pass evals*. That is the same split already measured on the FVT book: the mechanical layer
produces candidates, and the selection is doing the work.

## Reproduce

    python -m scripts.pb_blake --stop swept --min-tp1-r 0.0
    python -m scripts.pb_blake --stop {swept,gap,local} --min-tp1-r {0.0,1.0}
