# Pre-registration: port of dearvn/tradovate-trading-bot's strategy to our harness

**Written before any result is computed. 2026-09-05.** Source: github.com/dearvn/tradovate-trading-bot
at commit 6056eb6, logic in `app/cronjob/trailingTradeHelper/strategy.js` (906 lines).

## What this repo is
A Tradovate execution bot with a React dashboard, forked in structure from a Binance trailing-trade
bot (the `trailingTradeIndicator` naming is inherited). It publishes **no backtest and no performance
claim**, which is a point in its favour - there is nothing to disprove, only a strategy to measure.
The entry gates are self-contained (RSI, WMA, MACD, a support test); the TradingView step exists but
the gates do not depend on its rating, so it is fully backtestable.

## A bug found while reading, documented BEFORE running
`is_crossdown_11_48` is declared false at line 25 and **never assigned true anywhere in the file**.
The crossdown loop at line 276 assigns to `crossdown_11_48` (a different variable, overwriting the
array it just computed). Consequences in the live bot:
- **PUT Logic #3** (`rsi_down && down_10m && is_crossdown_11_48 && ...`) can never fire.
- The CALL exit clause `is_crossdown_11_48 && close < wma11 && close < wma48` can never fire.
The port reproduces this faithfully as the **headline**, and reports a bug-fixed variant separately.

## The rules as ported (from the source, not from the README)
Indicators, computed continuously across the tape (the bot runs continuously, not per session):
RSI(9); WMA 11/48/200 on closes; ATR(14) with `atr_value = max(ATR*1.5, 2.5)`; MACD histogram with
`macd_bull = hist > 0 or hist rising`, `macd_bear = hist < 0 or hist falling`; WMA(6) of volume.

Latched state: `rsi_up` sets when RSI rises >5 through 40 from below; `rsi_down` sets when RSI falls
>7 through 70 from above; each clears the other. `is_crossup_11_48` latches on a WMA11/48 cross up and
clears on a cross down. `up_10m = wma11 > wma48 or close > wma11`, `down_10m = not up_10m`.
`up_5m = close > wma48 and close > wma11`, `down_5m = close < wma48 and close < wma11`.

`support()` per the source: if the 6-bar low pattern with a volume spike holds, return that bar's open
(or close if it closed down); else the lowest low of 6. `bottomsupport = close > support and
close > close[1] and rsi[1] > rsi[2] + 10`. `big_drop = rsi fell >8 and close > wma48`.
`is_out` after three `is_br` bars. `pb` per the source's two-branch pullback pattern.

CALL entries, first match wins: **#2** rsi_up & up_10m & bottomsupport & close>wma48 & close>wma200
(stop = low - 5) · **#1** same but close>wma48 OR close>wma200 (stop = low - 5) · **#3** rsi_up &
up_10m & is_crossup_11_48 & close>wma11 & close>wma48 & macd_bull (stop = low - atr) · **#4** rsi_up &
up_10m & wma11>wma48 & close>wma11 & close>close[1] & macd_bull (stop = low - atr).
PUT entries mirrored per the source. Entry at the signal bar's close. 2-minute cooldown between orders.

Exits, checked from the bar AFTER entry (the source does the same via its status gate): trailing ATR
stop that only ratchets; discretionary exit on `big_drop or pb or is_out` (or the crossdown clause,
which is dead); stop-out when the trailing stop is breached and `not up_5m`. Exit at that bar's close.

## Test design
- Instrument NQ. Timeframes **1m, 5m and 15m** (the repo does not fix one; all three are reported).
- Tapes: 2023-01 to 2026-09 | 2020-2022 | 2017-2019.
- Cost **0.5 points** per round trip, charged in R against each trade's own initial stop; stressed at
  **1.25 points** (both legs are market orders in the source).

## Pass/fail, declared now
A timeframe **PASSES** only if all five hold:
1. Net R per trade > 0 on **all three** tapes.
2. Pooled t-statistic > **2.5**.
3. `scripts/reality_gate.py` passes.
4. Still positive at 1.25 points cost.
5. At least **100 trades** per tape.
Anything else is a FAIL. No parameter changes: the constants are the repo's own defaults.

## Predictions (scored after)
- P1: the bug-fixed variant differs from the faithful port by less than 20% of net R (the dead clauses
  are rarely reachable anyway).
- P2: shorter timeframes produce more trades but worse per-trade expectancy.
- P3: no timeframe passes all five conditions.
