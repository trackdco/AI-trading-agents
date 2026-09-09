# Pre-registration: the trend + band-rejection setup on GOLD

**Written before any result is computed. 2026-09-05.** Same rules as
docs/PREREG-trend-band-rejection.md (which FAILED all nine combinations on NQ), ported to gold.

## Why port it rather than drop it
The NQ run failed, but gold is a different market with different participants, and the setup was
selective enough (~1 per fortnight) that NQ's 92 trades on the strongest tape were never conclusive.
Gold is the only other instrument in this repository with a clean multi-year 1-minute tape.

## Two honest adjustments, declared before running
1. **Stops must be scaled, not copied.** A 20-point NQ stop at ~20,000 is 0.100% of price. Gold traded
   1,813 to 5,623 across this tape, so a fixed point stop means something different in 2023 than in
   2026. The fixed variants are therefore **P010 (0.100% of entry price)** and **P015 (0.150%)** - the
   exact economic equivalents of NQ's F20 and F30 - plus **X**, the rejection candle's extreme.
2. **Cost scales too.** NQ used 0.5 points = 2 ticks. Gold's tick is 0.10, so cost = **0.20 points**
   per round trip, charged in R. The 1.25-point NQ stress becomes **0.50 points** on gold.

## Only one tape exists
Gold covers 2023-01-02 to 2026-09-01, 947 sessions. There is no second or third gold tape, so the
"positive on all three tapes" condition is replaced by:
- **positive on the full tape**, AND
- **positive in BOTH halves** split by date at the median session.
A secondary split is also reported, 2023-24 versus 2025-26, because gold's median 1-minute candle runs
4, 5, 11 and 21 ticks by year - it fails this repository's >=20-tick tradeability screen until 2026.
That secondary split is descriptive only and cannot make a fail into a pass.

**No volatility dial.** Earlier work fitted a gold volatility filter on gold's own data. Applying it
here would import a previously-fitted parameter, so the headline runs WITHOUT it. Any dialled result
is reported separately and labelled as previously fitted.

## Everything else is unchanged
5-minute bars, VWAP and Bollinger anchored/reset at 18:00 ET, 7-hour observation window, the >=90%
inside plus >=3 rejections zone test, the 0.15% VWAP trend threshold and 60% same-side rule, body of
the push candle fully through the opposing Bollinger band, strong return candle (body >= 50% of range,
closing with the trend), entry at its close, exits scanned from the bar AFTER entry, ties score the
stop, flat at session end. Targets: VWAP, +/-1 sigma, band edge.

## Pass/fail, declared now
Nine combinations (3 stops x 3 targets). A combination **PASSES** only if all six hold:
1. Net R per trade > 0 on the full tape AND in both halves.
2. Pooled t-statistic > **3.0**.
3. `scripts/reality_gate.py` passes on its dump.
4. Net edge > **3x** cost, AND still positive at a **0.50-point** cost.
5. **Ridge**: an adjacent stop AND an adjacent target are also positive on the full tape.
6. At least **100 trades**.

Anything else is a FAIL.

## Predictions (scored after)
- P1: fewer than 0.15 setups per session, as on NQ.
- P2: the second half (2025-26, when gold finally passes the tick screen) beats the first half.
- P3: no combination passes all six conditions.
