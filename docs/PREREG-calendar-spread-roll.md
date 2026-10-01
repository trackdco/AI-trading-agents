# Pre-registration: the NQ calendar spread through the quarterly roll

**Written before any data is pulled. 2026-09-04.**

## Hypothesis
Every quarter, everyone holding the front NQ contract must move to the next one before expiry, on a
published deadline they cannot miss. That flow is one-directional (longs sell the front and buy the
back), concentrated into about eight sessions, and forced. Forced flow pushes the front-to-back
spread away from its fair carry value, and it should snap back once the flow is done.

Someone paying: the rolling long is paying for immediacy and certainty of execution before a hard
deadline. That is a fee, not a forecast.

Two things make this different from everything tested so far: it is **market neutral** (long one
contract, short another), so the buy-and-hold benchmark that killed the overnight idea does not
apply; and the flow is **visible in advance on a calendar**, not inferred from a chart.

## Declared limitation, stated before looking
NQ rolls four times a year. Ten years is about **40 observations**. This test can only detect a large,
consistent effect. A FAIL here means "no large effect", not "no effect". No amount of slicing 40
numbers will change that, and none will be attempted.

## Measurement (frozen)
- Instrument: the front-to-back spread, front minus back, in NQ points. Use the exchange-listed
  spread instrument (e.g. NQZ6-NQH7) where present; otherwise the difference of the two outright
  settlement prices on the same session.
- Roll cycle day 0 = the third Friday of Mar/Jun/Sep/Dec (front expiry). Sessions are numbered
  backwards from it: day -15 through day 0.
- **Trade A (fade the flow):** enter at the close of day -12, exit at the close of day -2.
- **Trade B (ride the flow):** the exact opposite of A.
Direction of A is fixed before looking: rolling longs SELL the front and BUY the back, which pushes
front-minus-back DOWN, so **A is long the spread** (buy front / sell back) at day -12.
- Cost: **0.5 points per round trip**, charged to every roll.
- One trade per roll. No stops, no targets, no filters, no sizing rules.

## Pass/fail, declared now
Trade A **PASSES** only if all five hold:
1. Mean P&L per roll > 0 after cost.
2. Positive in **all three** eras (2017-19, 2020-22, 2023-26).
3. Pooled t-statistic > **2.5**.
4. Win rate > **55%**.
5. Worst single roll loss smaller than 3x the mean win (it must be survivable at 40 observations).
If Trade A fails every condition and Trade B passes all five, that is recorded as a **direction error
in the hypothesis, not a pass** - the economic story would then be wrong and the result would need a
fresh pre-registration to mean anything.

Anything else is a FAIL. No changing the entry or exit days after seeing the data.

## Predictions (scored after)
- P1: the spread does move down into the roll (the flow direction is real and visible).
- P2: Trade A fails condition 3 (t>2.5) on 40 observations even if the sign is right.
- P3: the effect, if any, is larger in 2020-22 (high volatility, wider carry uncertainty).

## Data order (Databento, cheap pass first)
Pull 1 - daily, whole history, all NQ contracts and spreads:
    dataset  GLBX.MDP3
    schema   ohlcv-1d
    symbols  NQ.FUT
    stype_in parent
    start    2016-09-01
    end      2026-09-05
    encoding csv, compression zstd, pretty_px + pretty_ts + map_symbols on
This is a few thousand rows per contract across ~40 contracts. It should cost very little.

Pull 2 - only if Pull 1 passes: ohlcv-1m over the day -15 to day 0 windows, to check the intraday
shape of the flow and whether the entry can actually be filled.
