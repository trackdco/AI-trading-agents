# Pre-registration: 15-minute pivot breakout (the plain core of nq-asim)

**Written before any result is computed. 2026-09-04.**

Source of the idea: github.com/asalvador-ASIM/nq-asim. Its published numbers are not usable (no
strategy source in the repo, hardcoded equity curve, six versions tuned on one 159-calendar-day
window with no holdout, internally inconsistent trade counts and Sharpe/drawdown). Only the plain
hypothesis is being tested here, with none of its filters.

## Hypothesis
In an index future, a break of a recent swing low while price is below its long trend average, on
above-average volume and in a trending tape, is followed by continuation often enough to pay a
two-stage exit after costs. Mirrored for longs above the trend average.

## Frozen rules (no tuning; these are the repo's stated values)
- Bars: 1-minute tapes resampled to **15 minutes**, clock-aligned. Session-day = 18:00 ET to 17:00 ET.
- Trend: EMA200 of 15m closes. Shorts require close < EMA200, longs close > EMA200.
- Volume: RVOL = volume / SMA20(volume) >= **1.2**.
- Trend strength: Wilder **ADX(14) >= 20**.
- Pivot: lookback **6** bars each side, strict. A pivot is only usable 6 bars after it forms.
- Entry: first 15m close through the most recent confirmed pivot (below for shorts, above for longs),
  at that bar's close. One position at a time, one entry per pivot level.
- Stop: extreme of the last 6 bars, one tick beyond. risk = |entry - stop|.
- Stage 1: half the position at **2.6R** (short) / **1.7R** (long); stop to breakeven on the runner.
- Stage 2: runner trails at **2.0x** (short) / **1.25x** (long) ATR(14), ratcheting only.
- Exits are scanned from the bar AFTER the entry bar (the 2026-09-04 fill-bar rule). A bar that
  touches both stop and target is scored as the stop.
- Flat at the last bar of the session. Cost 0.5 points per round trip, charged in R.
- Trade r = 0.5 x stage-1 result + 0.5 x runner result.

## Tapes (all three, no peeking order)
2023-01-02 to 2026-09-03 | 2020-2022 | 2017-2019.

## Pass/fail, declared now
- **PASS** requires: net R per trade > 0 on **all three** tapes, for the same side, AND
  `scripts/reality_gate.py` passing on the dump.
- Anything else is a FAIL and the idea is dropped. No parameter changes, no added filters, no
  re-runs on a subset. The KNN filter is only considered if the plain version passes, because a
  filter can concentrate an edge but cannot create one.

## Predictions (scored after)
- P1: shorts beat longs on net R per trade, on at least 2 of 3 tapes.
- P2: the plain version is negative after costs on at least one tape.
- P3: 2017-2019 is the weakest tape (the tick-screen law).
