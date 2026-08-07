# Constitution — 1m MNQ displacement setup (v1)

Rules as pinned by the owner in the interrogation of 2026-08-07. Long side stated; short side is the exact mirror (owner-specified). Parameters marked `OPEN-n` have no value yet — see `docs/open-questions.md`. The strategy is not codable or testable until every `OPEN-n` in a rule it needs has a value.

## Conventions this document uses

- Candle `C` = the 1-minute bar spanning `[T, T+60s)`; `close(C)` occurs at `T+60s`. (Bar-label convention of the data source must be verified empirically before coding — CLAUDE.md §7.1; see open-questions §D.)
- `P` = the 1-minute bar immediately preceding `C` in the continuous (24h) series.
- All clock times are America/New_York wall clock.
- Instrument: MNQ. Point value $2.00 per contract. Tick 0.25.
- `range(C) = high(C) − low(C)`. `body(C) = close(C) − open(C)` (long side).

## S. Signal (long)

A signal fires at `close(C)` iff all of:

- S1. `close(C) − open(C) > 0`. (Strict. `close == open` fires nothing, in either direction.)
- S2. `body(C) ≥ 0.70 × range(C)`.
- S3. `range(C) ≥ OPEN-1 × ATR14`, where ATR14 = 14-bar Wilder ATR on continuous 24h 1-minute bars. (Evaluation bar of the ATR: `OPEN-6`.)
- S4. `open(C) ≥ high(P) + 0.25`.
- S5. `close(C)` falls inside the session window 09:30:00–10:30:00. (Earliest eligible candle: `OPEN-5a`. Latest eligible candle: `OPEN-5b`.)
- S6. Single candle. No streak, no structure-break, no volume, and no close-location condition beyond S1–S2.

## L. Liquidity level (long)

- L1. Candidate structure price = a pivot high: a 1-minute bar whose high exceeds the high of each of the 3 bars on both sides. A pivot is eligible only if its confirming 3rd subsequent bar has closed at or before `close(C)`.
- L2. The level used = the nearest eligible pivot-high price above the reference price `OPEN-7`.
- L3. The level is valid only if a resting order-book level within 5.00 points of it has displayed size `≥ 3 ×` the average visible level size (`averaging basis: OPEN-8`) sustained over the trailing `OPEN-2` minutes before `close(C)`.
- L4. If no valid level exists: no trade for this signal.

## E. Entry

- E1. Order type: limit. Price = `low(C) + 0.5 × range(C)`.
- E2. Order is placed at `close(C)`.
- E3. Cancel the unfilled order when the liquidity level is taken (equality treatment: `OPEN-5c`) or at the flatten time X3, whichever is first.

## X. Exit

- X1. Stop-market at `low(C) − 0.25`, placed on fill.
- X2. Take-profit limit at the L2 level price.
- X3. Flatten: at 10:30:00, cancel all unfilled orders and close any open position at market.
- X4. No break-even move, no partials, no trailing. Stop and target do not move.

## Z. Sizing

- Z1. Risk per trade = $250.00, fixed.
- Z2. Contracts = `floor(250 / ((entry_price − stop_price) × 2))`.
- Z3. If Z2 = 0: no trade.
- Z4. No minimum stop distance. Z2 output is traded as computed.
- Z5. No maximum contract cap.

## F. Frequency and skips

- F1. Trades per session and behaviour of a new signal while an order is pending or a position is open: `OPEN-3`.
- F2. Skip conditions (news or otherwise): `OPEN-4`.

## Supersessions

- The session window was first given as 09:30–12:00 and later corrected by the owner to 09:30–10:30 for signals, orders, and positions alike. Both answers are retained in the interrogation log; the 09:30–12:00 answer is superseded.
