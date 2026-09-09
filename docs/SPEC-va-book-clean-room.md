# NQ VALUE-AREA RETEST STRATEGY — COMPLETE RULES (implement from this document only)

You are re-implementing a fully mechanical intraday strategy from scratch. Everything you need is in this file and the two data files beside it. Do not consult any other source.

## Data
- `/tmp/blind/nq_1m.parquet` — 1-minute OHLCV bars, NQ continuous front month. Columns: `ts_event` (bar START time, timezone America/New_York), `open, high, low, close, volume`. Tick size 0.25 points. 2023-01-02 → 2026-09-02.
- `/tmp/blind/news_archive.csv` — columns `datetime_ET,date,time_et,currency,event,impact`. A "news day" is any `date` that has at least one row with `impact == "high"` and `08:00 <= time_et < 09:30`.

## Sessions
- A **session-day D** is the 23-hour window from 18:00 ET on date D up to (not including) 17:00 ET on the following calendar date. Bars with 18:00 ≤ t < 18:00+23h.
- Session-days are every distinct date obtained by subtracting 18 hours from each bar timestamp and taking the date; iterate them in order.
- The **prior session** of D is all bars with prior_t0 ≤ t < t0, where t0 = D 18:00 and prior_t0 = the previous session-day's 18:00 (the previous entry in the ordered list, even if that session was skipped for trading).
- Skip session-day D entirely if the prior session has fewer than 300 bars, or the session has fewer than 600 bars. The first session-day has no prior session and is skipped.

## Levels (computed once per session-day from the prior session's bars)
Volume profile with 1.0-point bins. Bin index of a price p is floor(p / 1.0).
1. For each prior-session bar, spread its volume UNIFORMLY across every bin from floor(low) to floor(high) inclusive (volume / number_of_bins per bin).
2. POC = the bin with the largest volume (lowest index on a tie).
3. Value area: start with lo = hi = POC. Repeat while cumulative volume in [lo, hi] < 70% of total volume and expansion is possible: let up = sum of the next two bins above hi (fewer if at the top), dn = sum of the next two bins below lo (fewer if at the bottom); if up ≥ dn and hi is not the top bin, hi = min(hi + 2, top); else if lo > bottom, lo = max(lo − 2, bottom); else stop. (Missing side counts as −1 so the other side wins.)
4. VAL = lo × 1.0 ; VAH = (hi + 1) × 1.0. Round each to the nearest 0.25.
If VAH or VAL is not finite, skip the day.

## Signal candles
Use the session's 1-minute bars in order. Let h = hours since 18:00 of the bar's START. Consider only bars with h ≥ 0.9633 and (h + 1/60) ≤ 21.9167 (i.e. starting from the 18:58 bar, ending with the bar that closes at 15:55 ET). Within that filtered list, for each index i ≥ 1 (the previous bar i−1 must also be in the list), and for each level L in {VAH, VAL}:
- LONG signal if close[i−1] ≤ L and close[i] ≥ L + 3.0
- SHORT signal if close[i−1] ≥ L and close[i] ≤ L − 3.0
(both directions are tested against BOTH levels.)
A signal's **time** is the END of candle i (start + 1 minute). If several signals share the same end time, keep only the one whose level is nearest to close[i]. Sort signals by time. Record for each signal: direction d (+1/−1), level L, the signal candle's open/high/low/close, and the previous candle's high/low.

## Stop (structural)
For a LONG signal: ref = low of the signal candle; if |signal candle open − L| < 5.0, ref = min(signal candle low, previous candle low). stop = ref − 0.25. If L − stop < 5.0, stop = L − 5.0.
For a SHORT signal: mirror (ref = high, or max of the two highs; stop = ref + 0.25; if stop − L < 5.0, stop = L + 5.0).
risk = |L − stop|. **If risk > 30.0 the signal is never placed** (skip it and move to the next signal).

## Working a signal (one position at a time)
Let `ts` be the session's bar start times, `n` the bar count. `start` = index of the first bar whose start time ≥ the signal time. `cancel` = the minimum of: the `start` index of the NEXT signal in the list, the index of the first bar at or after 16:00 ET (t0 + 22h), and n.
- **Occupancy:** maintain `t_free`, initially before the session. A signal whose time ≤ t_free is skipped.
- **News gate:** if the calendar date of (t0 + 15h) is a news day, define block = [index of first bar ≥ t0+14h (08:00), index of first bar ≥ t0+15.5h (09:30)). A signal whose `start` falls inside the block is skipped. If `start` is before the block, cancel = min(cancel, block start) — a resting order is pulled at 08:00.
- **Arming (the order is dark until displacement):** si0 = max(start − 1, 0) (the signal candle itself counts). If si0 ≥ cancel → skip. Threshold = L + d × 1.0 × risk. Find the first bar index a in [si0, cancel) with high ≥ threshold (long) / low ≤ threshold (short). If none → skip (unarmed). live = a + 1. If live ≥ cancel → skip.
- **Fill:** the first bar index f in [live, cancel) with low ≤ L − 0.25 (long) / high ≥ L + 0.25 (short). If none → skip (expired). Entry price E = L.
- **Exit** (scan from the fill bar f INCLUSIVE to the end of the session): target = E + d × risk.
  - s_idx = first bar with low ≤ stop (long) / high ≥ stop (short), else n.
  - t_idx = first bar with high ≥ target (long) / low ≤ target (short), else n.
  - **SAR:** look at later signals in the list with direction −d whose signal time > ts[f]; take the first; sar_idx = index of the first bar whose start ≥ that signal time; sar_px = that opposing signal candle's close. If sar_idx ≤ min(s_idx, t_idx) and sar_idx ≤ n: exit at bar min(sar_idx, n−1), r = d × (sar_px − E) / risk, res = "SAR", and set t_free = ts[min(sar_idx, n−1)] − 1 nanosecond (so the opposing signal itself is NOT skipped and is worked next).
  - else if s_idx ≤ t_idx and s_idx < n: res = "STOP", r = −1, exit bar s_idx. (A bar that touches both stop and target is a STOP.)
  - else if t_idx < s_idx: res = "TARGET", r = +1, exit bar t_idx.
  - else: res = "FLAT", exit at the last bar of the session (n−1), r = d × (last close − E) / risk.
  - For STOP/TARGET/FLAT set t_free = ts[exit bar].
- Then continue with the next signal in the list (whether or not this one traded).

## Costs and scoring
net_r = r − 0.5 / risk. Win rate = TARGET / (TARGET + STOP).

## Output
Write `/tmp/blind/trades.jsonl`, one JSON object per trade: `{"day": "YYYY-MM-DD" (session-day), "dir": ±1, "level": L, "t_sig": ISO time of the signal (candle end), "t_fill": ISO start time of the fill bar, "entry": E, "stop": stop, "risk": risk, "res": "TARGET|STOP|SAR|FLAT", "r": r, "t_exit": ISO start time of the exit bar}`.
Write `/tmp/blind/summary.txt` with: session-days traded, trade count, win rate, mean net_r, total net_r, count by res, and per-year trade count / total net_r.
