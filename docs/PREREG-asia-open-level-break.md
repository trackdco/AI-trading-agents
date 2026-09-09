# Pre-registration: Asia-open level break, retest entry, next-level target

**Written before any result is computed. 2026-09-05.**

## Relationship to earlier work, stated up front
The break-and-retest family was measured at no edge on 2026-09-04 once the fill-bar accounting was
fixed (docs/FINDINGS-exit-next-bar-rerun.txt). Four things here are genuinely different and are the
reason this is worth a run: **5-minute** signal bars, a **body-through** filter instead of any close,
a fixed **90-minute window** at the Asia open, and a target that is **the next structural level**
rather than a fixed 1R. The last changes the payoff shape entirely - reward varies per trade.

## The rules (frozen)
**Levels**, computed once per session-day from the prior session (18:00-17:00 ET), five in total:
prior-day VAH, VAL, POC (1.0-point bins, 70% value area, the repo's standard construction), plus the
prior session's high and low.

**Signal window**: the 5-minute candle must CLOSE between 18:00 and 19:30 ET (the first 90 minutes of
the Asia session). At most **one trade per session-day** - the first qualifying signal.

**Signal (body through, not a wick)**, tested against VAH, VAL and POC only:
- LONG: candle closes above the level, the candle's OPEN is at or below the level (the body spans it),
  and body size >= **50%** of the candle's high-low range.
- SHORT: mirrored.

**Entry**: a limit at the level, armed when the signal candle closes. Filled when price trades one
tick through the level on the way back. Pending expires **4 hours** after the signal.

**Target**: the nearest of the five levels beyond the entry in the trade's direction. **If there is no
level in that direction, the trade is skipped** - no substitute target.

**Stop** - six variants swept, all declared now:
  S: the signal candle's opposite extreme, one tick beyond
  F10, F15, F20, F25, F30: fixed 10 / 15 / 20 / 25 / 30 points from the level

**Exit**: scanned from the bar AFTER the fill bar (the 2026-09-04 fill-bar rule). A bar touching both
stop and target scores the stop. Flat at session end. Cost **0.5 points per round trip**, charged in R.

## Tapes
NQ 2023-01-02 to 2026-09-03 | NQ 2020-2022 | NQ 2017-2019.

## Pass/fail, declared now
A stop variant **PASSES** only if all five hold:
1. Net R per trade > 0 on **all three** tapes.
2. Pooled t-statistic > **2.5**.
3. `scripts/reality_gate.py` passes on the dump.
4. Net edge per trade > **3x** the cost per trade.
5. **Ridge, not spike**: at least one neighbouring stop variant in the sweep is also positive on all
   three tapes. Six variants are being tested; one passing alone is the multiple-comparisons trap
   that the calendar test already demonstrated.

Anything else is a FAIL. No changing the window, the body threshold, the target rule or the pending
life after seeing results.

## Predictions (scored after)
- P1: fewer than 0.6 qualifying setups per session (the window and body filter are restrictive).
- P2: wider fixed stops show higher raw net R than tight ones, because the target is fixed in points
  while the stop is not - this is mechanical, not edge.
- P3: no stop variant passes all five conditions.
