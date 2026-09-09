# Pre-registration: Asia sweep of a NY PM extreme, confirmed by absorption

**Written before any result is computed. 2026-09-05.** First test in this repository to use the
aggressor-tagged footprint data in `data/reference/cvd/` (517 session-days).

## Sign correction made first
`scripts/build_cvd_minute.py` computed delta = A - B. Measured across 207,520 minutes against the 1m
master bars, corr(minute price change, B - A) = **+0.657**. **B is the buy aggressor; delta = B - A.**
The builder has been corrected. Footprint volume matches bar volume at corr 0.990, ratio 1.000.

## Hypothesis
Overnight, price runs up through the previous New York afternoon's high (or down through its low),
sweeping the stops resting there. If a large amount of aggressive buying goes through at that level
and price does NOT continue, someone big was selling into it - absorption. The sweep has failed, the
aggressors are trapped, and price works back across the range toward the opposite extreme.

Someone paying: the trapped breakout aggressor. Absorption is the direct evidence that a passive
seller met them, which is exactly what a footprint can see and a bar chart cannot.

## Rules (frozen)
- **NY PM extremes**: highest high and lowest low between 12:00 and 16:00 ET.
- **Asia window**: 18:00 to 03:00 ET that evening.
- **Sweep**: the first 1m bar whose high >= PM high + 1 tick, or low <= PM low - 1 tick.
- **Absorption window**: the sweep minute plus the following 4 (5 minutes), counting only footprint
  rows priced within **5 ticks (1.25 points)** of the swept level. Absorption requires ALL THREE:
  1. volume in that window >= **3x** the median per-minute volume of the Asia session so far;
  2. signed delta (B - A) is in the sweep's direction - aggressors genuinely pushing through;
  3. price at the end of the window is back on the original side of the swept level - it failed.
- **Entry** at the close of that 5-minute window, direction OPPOSITE the sweep.
- **Stop** one tick beyond the sweep's extreme. **Target** the opposing NY PM extreme.
- Exits scanned from the bar AFTER entry; a bar touching both scores the stop; flat at session end;
  cost **0.5 points** per round trip. One trade per session.

## THE CONTROL (this is the point of the test)
The identical setup with **condition 2 and 3 only and no volume test**, and separately with **no
absorption test at all** - just sweep and reject. If absorption adds nothing over a plain
sweep-and-reject, the footprint data is not earning its place, and that is the finding.

## Data and split
517 session-days: 2023-07/09/11 and 2024-03/04/10 (158 days), and 2025-06 to 2026-07 (359 days).
Split for the both-halves condition: **2023-24 versus 2025-26**.

## Pass/fail, declared now
**PASSES** only if all six hold:
1. Net R per trade > 0 on the full sample AND on both eras.
2. Pooled t-statistic > **2.5**.
3. `scripts/reality_gate.py` passes.
4. Still positive at a **1.25-point** cost.
5. At least **60 trades** (the data cannot supply many more; if the count is under 60 the test is
   declared UNDERPOWERED rather than passed or failed).
6. **The absorption version beats both controls** on net R per trade.

## Predictions (scored after)
- P1: a PM extreme is swept during Asia on 30-60% of sessions.
- P2: the absorption filter does NOT beat the plain sweep-and-reject control.
- P3: no pass.
