# Pre-registration: the overnight session in NQ futures

**Written before any result is computed. 2026-09-04.**

## Hypothesis
Someone has to hold index risk overnight, when the cash market is shut and news arrives with no way
to trade out. They are paid for that. So the return earned holding NQ from the 16:00 ET close to the
09:30 ET open should be positive, and should be a larger share of the total than the day session is.

Economic reason, stated up front: this is a risk-transfer payment, not a chart pattern. It is also a
documented effect in cash equities, so a negative result here is a decay finding, not a surprise.

## Definitions (frozen)
- **Overnight**: buy at the close of the 15:59 ET bar, sell at the open of the 09:30 ET bar of the
  next session that has one. Carries across the 17:00-18:00 halt.
- **Day**: buy at the open of the 09:30 bar, sell at the close of the 15:59 bar, same day.
- **Buy and hold**: close of 15:59 to close of the next 15:59.
- Result in NQ points. Cost **0.5 points per round trip**, charged to every leg pair.
- A day is skipped if either required bar is missing (holidays, early closes without a 15:59 bar).

## Roll contamination (declared before looking)
The continuous tape is volume-rolled and **not** back-adjusted, so the quarterly roll prints a false
jump. **Headline excludes the 10 trading days ending on the third Friday of Mar/Jun/Sep/Dec.** The
all-days version is reported beside it, and any large gap between the two is a roll artefact, not a
result.

## Tapes
2023-01-02 to 2026-09-03 | 2020-2022 | 2017-2019. Cross-check on ES.

## Pass/fail, declared now
**PASS** requires all three:
1. Overnight mean net points per day > 0 on **all three** NQ tapes.
2. Overnight Sharpe > day-session Sharpe on **all three**.
3. Overnight total / max drawdown > **0.5** on all three (it has to be survivable, not just positive).

Anything else is a FAIL. No parameter changes, no time-of-day tuning, no filters. If it passes, the
next step is a pre-registered test of whether the effect survives on days following a large move.

## Predictions (scored after)
- P1: overnight is positive and the day session is near zero or negative.
- P2: overnight's worst single day is worse than the day session's (gap risk).
- P3: 2020-2022 is the weakest overnight tape (COVID gaps).
