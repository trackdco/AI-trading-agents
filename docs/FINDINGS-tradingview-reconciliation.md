# TradingView reconciliation of the armed empire: the edge sits inside the fill bar

**Date:** 2026-09-04. **Status:** the single most important finding in this repository. Supersedes the
headline numbers in every earlier FINDINGS file until the intrabar test below is run.

## What was done
Pat ran the Pine port (`docs/pine/nq_armed_empire.pine`, one strategy instance per book) on a
TradingView 1-minute NQ1! chart from 2023-09-05 to 2026-09-04 and exported the List of Trades for all
seven books (`data/reference/tv_exports/`). `scripts/tv_compare.py` and `scripts/tv_compare_outcomes.py`
match every TradingView trade to the engine's armed dumps by direction, level and fill minute (chart
timezone Australia/Sydney).

## Entries agree, exits do not
| book | TV trades | engine | matched to the minute | engine net R | TV net R/trade |
|---|---|---|---|---|---|
| PD value area | 5,644 | 5,549 | 97% | +988 | -0.059 |
| Weekly value area | 3,717 | 3,618 | 98% | +618 | -0.070 |
| PD high/low | 3,441 | 3,360 | 97% | +625 | -0.073 |
| PD POC | 3,093 | 3,053 | 98% | +496 | -0.071 |
| Weekly POC | 1,203 | 1,187 | 98% | +211 | -0.076 |
| Session VWAP | 24,500 | 23,777 | 97% | +3,814 | -0.081 |
| NY VWAP | 12,980 | 12,892 | 96% | +2,635 | -0.079 |

All seven books, same span: engine +9,388R (+97,874 pts). TradingView -1,954 pts gross (about -$39k on
one NQ) and -$584,865 after $10 round-trip commissions on 54,578 trades.

On matched trades: engine STOPs score -0.92R in TradingView (the 0.25pt fill improvement), engine SARs
-0.45R vs -0.48R. Both agree. Engine TARGETs that took one minute or longer win **100%** of the time in
TradingView at +1.04R. Engine TARGETs with `hold_min == 0` win only **62-64%** at +0.35R.

## The mechanism
The spec scans for the exit **from the fill bar inclusive**: if the fill bar's high reaches the target,
the trade is a TARGET with a zero-minute hold. But a resting buy limit fills on the way DOWN, so a fill
bar whose high is at the target almost always printed that high BEFORE the pullback that filled the order.
The engine books a win for a move that happened before it was in the trade.

| | count | share | net R |
|---|---|---|---|
| all engine trades (7 books, TV span) | 53,436 | | +9,388 |
| engine TARGETs | 31,794 | | |
| of which zero-minute (same bar as fill) | 23,626 | 74% of targets | +22,027 |
| everything except the zero-minute targets | 29,810 | | **-12,639** |

TradingView resolves the order inside a bar from its shape (up bar: open, low, high, close; down bar: open,
high, low, close), so it credits the same-bar target only when the fill bar closed in the trade's direction.
`scripts/fillbar_rescore.py` applies that rule to the engine's own trades: every book flips from about
+0.17R per trade to about -0.16R per trade (SAR rescue ignored, so slightly harsher than TradingView's
actual -0.07R).

## What this means
- The backtest edge is an accounting assumption about the inside of one-minute bars, not a market edge.
  Every downstream number (the 954-day headline, holdouts, gold, Monte Carlo, funded-account odds, the
  scaling plan) inherits it.
- The audit, the blind re-implementation, Angus's PBO/WFE work and the holdouts all reproduced the spec
  faithfully. None of them tested the spec's intrabar assumption against finer data. This is exactly what
  shadow trading would have exposed on the first day of resting orders.
- TradingView's bar-shape rule is also an assumption. It is far more realistic than "always credit", but the
  true answer needs intrabar data.

## Definitive test (next)
Pull Databento `GLBX.MDP3`, schema `ohlcv-1s`, symbol `NQ.FUT` (parent), for 5 to 10 trading days. Replay
every zero-minute TARGET: after the first second whose low is at or below the limit, does a later second in
the same minute reach the target before any second reaches the stop? The share that does is the real
same-bar win rate. If it is near TradingView's 62%, the strategy is a loser after costs. If it is near 100%,
TradingView is wrong and the engine stands.

Until that test is run, nothing in this repository should be traded or funded.
