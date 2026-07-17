# Step 4 Parity Report — engine vs reference charts

Spec-1 Step 4 PARITY GATE. Engine values below; Angus fills the blank columns from the reference charts.

## Wednesday February 11, 2026 — 09:48 ET

Angus traded the **3M** entry TF this day (short, 09:48) — check the 3min BB row first.

Last CLOSED bar used per TF (bar stamp): 1min: 09:47, 2min: 09:48, 3min: 09:48, 5min: 09:45. The 1m bar stamped 09:47 closed at 09:48; the 1m bar stamped 09:48 was still forming and is NOT used.

| Level | Engine value | Angus chart value | Δ | within 1.0 pt? |
|---|---|---|---|---|
| BB basis 1min | 25394.96 | ___ | ___ | ___ |
| BB basis 2min | 25408.44 | ___ | ___ | ___ |
| BB basis 3min | 25409.79 | ___ | ___ | ___ |
| BB basis 5min | 25360.00 | ___ | ___ | ___ |
| Daily VWAP mid | 25334.64 | ___ | ___ | ___ |
| Daily VWAP +1σ | 25414.18 | ___ | ___ | ___ |
| Daily VWAP −1σ | 25255.10 | ___ | ___ | ___ |
| NY VWAP mid | 25397.52 | ___ | ___ | ___ |
| Daily POC (as-of) | 25385.62 | ___ | ___ | ___ |

## Tuesday February 17, 2026 — 09:50 ET

Angus traded the **2M** entry TF for the 09:50 trade (short) — check the 2min BB row first.

Last CLOSED bar used per TF (bar stamp): 1min: 09:49, 2min: 09:50, 3min: 09:48, 5min: 09:50. The 1m bar stamped 09:49 closed at 09:50; the 1m bar stamped 09:50 was still forming and is NOT used.

| Level | Engine value | Angus chart value | Δ | within 1.0 pt? |
|---|---|---|---|---|
| BB basis 1min | 24719.55 | ___ | ___ | ___ |
| BB basis 2min | 24687.09 | ___ | ___ | ___ |
| BB basis 3min | 24666.80 | ___ | ___ | ___ |
| BB basis 5min | 24639.21 | ___ | ___ | ___ |
| Daily VWAP mid | 24672.57 | ___ | ___ | ___ |
| Daily VWAP +1σ | 24743.95 | ___ | ___ | ___ |
| Daily VWAP −1σ | 24601.19 | ___ | ___ | ___ |
| NY VWAP mid | 24713.80 | ___ | ___ | ___ |
| Daily POC (as-of) | 24662.88 | ___ | ___ | ___ |

## Conventions (what the engine computed, so chart comparison is apples-to-apples)

- **Last-CLOSED-candle semantics:** every value is taken from the last candle fully
  closed at the gate timestamp. The 1m base frame is start-labeled, so at T the last
  closed 1m bar is the one stamped T−1min. Resampled 2m/3m/5m frames are close-labeled
  (built only from already-closed 1m bars; trailing partial bins dropped) — the exact
  bars used are listed above each table. On the chart: read the indicator value of the
  **last completed candle**, not the forming one.
- **Bollinger Bands:** BB(20, SMA of close, 2.0σ), population stdev — TradingView
  ``ta.stdev`` — computed per entry TF (§2).
- **VWAP source:** hlc3 = (high+low+close)/3 per 1m bar — standard TradingView VWAP (§2).
- **VWAP band stdev:** VOLUME-WEIGHTED around the running VWAP
  (var = Σ(vol·src²)/Σ(vol) − vwap²), NOT a simple rolling stdev (spec-1 §3).
- **Anchors:** daily VWAP resets at the CME daily session open **18:00 ET**; NY VWAP
  anchors **09:30 ET** and does not exist pre-market (§2/§3).
- **Daily POC:** DEVELOPING (as-of) profile of the current CME session (18:00 boundary),
  built from 1m bars closed at the timestamp, volume spread uniformly across each bar's
  [low, high] range in **0.25-pt bins**; POC = center of the max-volume bin. On the
  chart: use the session volume profile *as of that time* if available; the end-of-day
  profile will differ.
- **Entry TF per the hand log:** Feb 11 = **3M**, Feb 17 09:50 = **2M** — check that BB
  row first; the others are secondary.

## Gate instruction

Angus: fill in the chart value for every row, plus Δ = engine − chart and whether
|Δ| <= 1.0 NQ point. **Every row must be within 1.0
NQ point to pass.** Per spec-1 Step 4: **DO NOT proceed to Step 5 (snapshot builder)
without sign-off on this report.**
