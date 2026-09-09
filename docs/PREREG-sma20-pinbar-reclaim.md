# PRE-REGISTRATION — NQ 20-SMA pin-bar reclaim (Pat's rule)

Written 2026-09-07, BEFORE the run. Frozen from Pat's description + 5 annotated replay charts.

## The idea in one line
Trend, pull back into the 20 SMA, and take the pin bar that wicks through the SMA and
closes back on the trend side. Stop past the wick, target 1R or the next draw.

## Data
NQ 1-minute, three tapes, kept separate throughout:
`nq_2017_2019_1m` / `nq_2020_2022_1m` / `nq_1m_master` + `nq_1m_jul_sep2026` (2023-26).
Bars resampled to the traded timeframe. All times America/New_York.

## Indicator
20-period SMA of close, on the traded timeframe. This is the basis line of BB(20, SMA,
close, 2). The bands themselves are NOT used.

## Frozen entry rule — LONG (short is the exact mirror)
On the traded timeframe, at bar `i`:
1. **Trend filter** is true (definition swept, see below).
2. **Wick crosses the SMA**: `low[i] < sma[i]`.
3. **Closes back through it**: `close[i] > sma[i]`.
4. **Bullish body**: `close[i] > open[i]`.
5. **Hammer shape**: `lower_wick >= W x body`, where
   `lower_wick = min(open,close) - low` and `body = |close - open|`.
6. **Little upper shadow**: `upper_wick <= U x (high - low)`.
7. Bar closes inside the session window.

**Entry** at the close of bar `i`. **Stop** at `low[i] - B ticks`. `risk = entry - stop`.

## Swept settings (declared now, all reported, no cherry-picking)
- timeframe `TF` .......... 1, 2, 3 min
- session ................. NY (09:30-10:30), LONDON (03:00-04:30), ALL DAY (control)
- trend `T` ............... SLOPE (sma above its value 10 bars back)
                            SIDE  (12 of last 15 closes on the trend side)
                            HHHL  (last two swing highs AND swing lows both rising)
                            NONE  (control - no trend filter at all)
- wick multiple `W` ....... 1.0, 1.5, 2.0, 2.5
- upper-shadow cap `U` .... 0.25, 0.50, 1.00 (1.00 = off)
- stop buffer `B` ......... 1, 2, 4 ticks
- target .................. R1, R1.5, R2, R3, and DOL (next prominent swing level,
                            floored at 1R because Pat's minimum is 1:1)

Exits are scanned from the bar AFTER entry. A bar that touches both stop and target
counts as a STOP. Max hold 120 minutes, then flat at market. One position at a time.
Cost 1.25 pt round turn (headline), 0.50 pt also reported.

## The bar — the rule is alive only if ALL of these hold
1. Positive net R/trade after 1.25 pt cost on ALL THREE tapes, same settings.
2. Positive in both halves of each tape.
3. Win rate above the break-even rate for its own realised reward ratio, by > 5 points.
4. Pooled t > 2.5 (raised because this is a large sweep).
5. Survives dropping its 3 best trades.
6. Beats a matched RANDOM entry (same session, same risk, same target) by > 0.10 R.
7. The winning settings form a RIDGE, not a spike - neighbouring settings also positive.

## Predictions, scored after the run
- **P1** The stop will be noise-width. A 1-min NQ wick that is 2x its body is still a
  small number of points; median risk will come in under 8 pts, which is where the last
  four ideas died.
- **P2** The trend filter will not matter much. NONE will score within 0.05 R of the
  best trend definition.
- **P3** London will be no better than NY, and the ALL-DAY control will not be much
  worse than either - i.e. the session gate carries little information.
- **P4** Higher timeframe (3 min) will show a higher win rate but fewer trades, and the
  net R will land in the same place as 1 min. Pat believes higher TF is stronger.
- **P5** The rule will beat random entry by less than 0.10 R.

## Phase 2 (only if phase 1 survives — not before)
Confluence filters, each declared and counted: fib 0.382/0.5/0.618/0.705/0.786 from the
last prominent swing, POC/VAH/VAL, prior day and prior session H/L, higher-timeframe
20 SMA, and pin-bar volume. Adding these to a dead rule is how you manufacture a fake
edge, so they are not touched until the plain rule has a verdict.
