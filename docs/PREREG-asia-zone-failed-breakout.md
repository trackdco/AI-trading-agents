# Pre-registration: Asia-zone failed breakout, reverting to the respected VWAP band

**Written before any result is computed. 2026-09-05.** Timeframe and target set chosen by the user
before the run: 5-minute bars; all three target variants compared.

## Hypothesis
Through the first seven hours of the Asia session, price often settles inside one VWAP band envelope
and keeps rejecting its edges. Later, a move breaks out through a Bollinger band and then **closes
back inside it**. That failed breakout traps everyone who bought or sold the break; they must exit,
and their exit pushes price back toward the envelope it came from.

Someone paying: the trapped breakout trader, on a forced exit. That is flow, not a shape.

## Turning the words into rules (all frozen)
**Bars**: 5-minute, from 1-minute tapes. Session-day 18:00 to 17:00 ET.

**VWAP bands**: session VWAP anchored 18:00, hlc3 source, cumulative sigma, bands at +/-1, 2, 3 sigma.
Values are live at each bar, not frozen.

**"Consistently respecting"**, decided once at 01:00 ET from the 18:00-01:00 window (84 bars):
the **respected envelope** is the tightest k in {1, 2, 3} for which BOTH hold -
  (a) at least **90%** of the window's 5m closes sit inside vwap +/- k*sigma, and
  (b) at least **3** bars in the window touched an edge (high >= upper or low <= lower) and still
      closed back inside it - the "reacting within" part.
If no k qualifies, the session is skipped. No zone, no trade.

**Bollinger bands**: 20-period, 2 standard deviations, on 5m closes, rolling.

**Signal**, from 01:00 to 16:00 ET, at most **one trade per session-day**:
1. A bar CLOSES outside a Bollinger band (the excursion). Track the extreme while closes stay outside.
2. A later bar CLOSES back inside the Bollinger band - this is the signal candle.
3. At that close, price must still be **outside the respected VWAP envelope on the break side**,
   otherwise there is nothing to revert to and the trade is skipped.

**Direction**: opposite the break. Broke up, go short; broke down, go long.
**Entry**: market at the signal candle's close.
**Stop**: the excursion extreme, one tick beyond.
**Targets** - three variants, all live values, all run on the same trade set:
  T-NEAR  the near edge of the respected envelope (vwap -/+ k*sigma)
  T-VWAP  the VWAP line
  T-FAR   the far edge of the respected envelope

**Exit**: scanned from the bar AFTER the entry bar (the 2026-09-04 fill-bar rule). A bar touching both
stop and target scores the stop. Flat at session end. Cost 0.5 points per round trip, charged in R.

## Tapes
NQ 2023-01-02 to 2026-09-03 | NQ 2020-2022 | NQ 2017-2019.

## Pass/fail, declared now
A target variant **PASSES** only if all five hold:
1. Net R per trade > 0 on **all three** tapes.
2. Pooled t-statistic > **2.5** (three variants are being compared).
3. `scripts/reality_gate.py` passes on its dump.
4. Net edge per trade > **3x** the cost per trade.
5. **Ridge, not spike**: an adjacent target variant is also positive on all three tapes.

Anything else is a FAIL. No changing the window, the 90% threshold, the 3-touch rule, the Bollinger
settings or the stop after seeing results.

## Predictions (scored after)
- P1: fewer than 0.4 qualifying setups per session.
- P2: T-NEAR has the highest win rate and T-FAR the lowest (mechanical, not evidence of edge).
- P3: no variant passes all five conditions.
