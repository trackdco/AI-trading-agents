# Pre-registration: trend + hard counter-push rejected at the Bollinger band

**Written before any result is computed. 2026-09-05.** Rules taken from the user's own description and
chart: 5-minute bars, VWAP and Bollinger both anchored/reset at the start of each trading day.

## Hypothesis
Through the first seven hours of the day the market establishes a clear trend, walking along one side
of its VWAP deviation bands and respecting them. Later a hard counter-trend push drives the BODY of a
5m candle clean through the opposing Bollinger band. That push fails and the next candle closes
strongly back inside. The counter-trend traders are trapped and must cover, and price resumes the
established trend.

Someone paying: the trapped counter-trend trader, on a forced exit.

## What is different from the 2026-09-05 failed-breakout test (which failed)
1. **Body through the band**, not merely a close outside - both open AND close beyond the Bollinger band.
2. **A strong return candle** - body >= 50% of its range and closing in the trade's direction.
3. **A trend requirement**, and the trade goes WITH the established trend. The previous test had no
   trend condition and traded mean reversion in both directions.
4. Because entry is at the Bollinger band (which sits inside the VWAP envelope), the target is a real
   distance. The previous test's target was ~0 by construction; that circularity is gone.

## Rules (frozen)
**Bars** 5-minute. **Day** 18:00-17:00 ET, VWAP and its sigma anchored at 18:00, hlc3 source.
**Bollinger** 20-period, 2 standard deviations, on 5m closes.

**Observation window** 18:00 to 01:00 ET (84 bars). The day qualifies only if BOTH:
- **respecting**: the tightest k in {1,2,3} with >=90% of window closes inside vwap +/- k*sigma AND
  >=3 bars that touched an edge and closed back inside; and
- **trending**: VWAP at 01:00 differs from VWAP at 19:00 by more than **0.15%**, and at least **60%**
  of window closes sit on that same side of VWAP. Trend direction = the sign of that VWAP change.

**Signal**, 01:00-16:00 ET, at most one trade per day, trading WITH the trend:
1. **Push**: a 5m candle whose OPEN and CLOSE are both beyond the Bollinger band on the counter-trend
   side. Track the excursion extreme while candles keep closing beyond it.
2. **Rejection**: the next candle to close back inside the Bollinger band, with body >= 50% of its
   range and closing in the trend's direction.
3. Entry at that candle's close, in the trend direction.

**Stop** - three variants: X (the excursion extreme, one tick beyond), F20, F30 (fixed points).
**Target** - three variants: T-VWAP (the VWAP line), T-1SIG (VWAP +/- 1 sigma on the trend side),
T-EDGE (VWAP +/- k*sigma on the trend side). All live values.

**Exit** scanned from the bar AFTER the entry bar. A bar touching both stop and target scores the stop.
Flat at session end. Cost 0.5 points per round trip, charged in R.

## Tapes
NQ 2023-01-02 to 2026-09-03 | NQ 2020-2022 | NQ 2017-2019.

## Pass/fail, declared now
Nine combinations are being tested (3 stops x 3 targets), so the bar is set accordingly. A combination
**PASSES** only if all six hold:
1. Net R per trade > 0 on **all three** tapes.
2. Pooled t-statistic > **3.0**.
3. `scripts/reality_gate.py` passes on its dump.
4. Net edge per trade > **3x** cost, AND still positive at a **1.25-point** cost (the market-order
   reality that killed the near-edge variant).
5. **Ridge**: an adjacent stop AND an adjacent target are also positive on all three tapes.
6. At least **100 trades** on each tape (no anecdote cells).

Anything else is a FAIL. No changing the window, the 0.15% trend threshold, the 60% side rule, the
body thresholds or the Bollinger settings after seeing results.

## Predictions (scored after)
- P1: fewer than 0.15 setups per session (body-through plus trend is very restrictive).
- P2: at least one cell of the nine is positive on all three tapes purely by chance.
- P3: no combination passes all six conditions.
