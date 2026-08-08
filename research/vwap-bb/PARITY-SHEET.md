# PARITY QUESTION SHEET — for Angus to complete from his own charts

**Do not read any other document in this repo before filling this in.** No computed
value appears anywhere below. The point of the exercise is that your readings are recorded
*before* you see the detector's, so a disagreement cannot be rationalised away.

Fill it in, save it, and send it back. Only then will the comparison be run.

---

## Setup

| | |
|---|---|
| Instrument | **NQ**, front month = **NQH5** (March 2025) on both dates |
| Timezone | **US Eastern (ET)**, all times |
| Session convention | Globex, 18:00 ET previous day → 16:59 ET |
| Price units | **NQ index points**, quote to the tick (**0.25**) |
| Distance units | **NQ points**, one decimal is enough |

**Two readings, at two instants:**

| | date | instant |
|---|---|---|
| **P1** | **Wednesday 2025-01-15** | **09:48 ET** |
| **P2** | **Wednesday 2025-01-22** | **09:50 ET** |

> **What "at 09:48" means.** Read the values **as they stood at the moment the 09:47 one-minute
> candle closed** — i.e. with every bar up to and including 09:47 complete, and *nothing* from
> the 09:48 candle. If your platform labels candles by close time rather than open time, that
> is the candle labelled **09:48**. If it labels by open time, that is the candle labelled
> **09:47**. Please tick which convention your chart uses:
>
> - [ ] my chart labels candles by **open** time
> - [ ] my chart labels candles by **close** time

Indicator settings, so we are reading the same thing:

- **Bollinger Bands** — length 20, basis SMA, source **close**, 2σ
- **Daily VWAP** — standard TradingView VWAP, anchored to the CME daily session open
  (18:00 ET), source **HLC/3**
- **NY session VWAP** — anchored **09:30 ET**, source HLC/3. Does not exist before 09:30.
- **Volume profile** — session profile, anchored to the same 18:00 ET session open

---

# P1 · 2025-01-15 · 09:48 ET

## 1. Level menu — price of every level (§2, §6)

Leave blank any level your chart does not show, and write **"n/a"** rather than guessing.

| level | price |
|---|---|
| Daily VWAP — mid | |
| Daily VWAP — +1σ | |
| Daily VWAP — −1σ | |
| Daily VWAP — +2σ | |
| Daily VWAP — −2σ | |
| Daily VWAP — +3σ | |
| Daily VWAP — −3σ | |
| NY VWAP — mid | |
| NY VWAP — +1σ | |
| NY VWAP — −1σ | |
| NY VWAP — +2σ | |
| NY VWAP — −2σ | |
| Volume profile — POC | |
| Volume profile — VAH | |
| Volume profile — VAL | |
| Session high so far (from 18:00 ET) | |
| Session low so far (from 18:00 ET) | |
| Prior-day high | |
| Prior-day low | |
| Pre-market high (18:00 → 09:29) | |
| Pre-market low (18:00 → 09:29) | |

## 2. Bollinger basis and bands, per entry timeframe

| entry TF | BB basis (20 SMA) | upper 2σ | lower 2σ |
|---|---|---|---|
| 1m | | | |
| 2m | | | |
| 3m | | | |
| 5m | | | |

## 3. Last completed candle on each entry timeframe

The candle in force at the instant defined above.

| entry TF | open | high | low | close |
|---|---|---|---|---|
| 1m | | | | |
| 2m | | | | |
| 3m | | | | |
| 5m | | | | |

## 4. Confluence clusters (§3)

A cluster is **≥2 levels of different types** within **~10 NQ points**. Types are: VWAP family
(counts once), BB (once), POC/profile (once), structural (once).

| # | levels in the cluster (name them) | lowest price in cluster | highest price | span (pts) | distinct types |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

*(Add rows if you see more. Write **"none"** in row 1 if no cluster qualifies.)*

## 5. HTF classification (§1, §4)

15-minute chart, swing highs and lows with 2 bars either side.

- [ ] uptrend (higher high **and** higher low)
- [ ] downtrend (lower high **and** lower low)
- [ ] range (anything else)

Last two confirmed swing highs: ______________ , ______________
Last two confirmed swing lows: ______________ , ______________

## 6. Does a trigger fire? (§3, §5)

- [ ] **No trigger.** → skip to P2.
- [ ] **Yes** — complete the rest of this section.

| | |
|---|---|
| Entry timeframe it fires on | |
| Direction (long / short) | |
| Type — rejection block / displacement | |
| Which cluster (row # from §4) | |
| Pattern per §4 — A reversal / B reclaim / B2 continuation | |

## 7. Resulting trade

| | value | note |
|---|---|---|
| **Entry** (E1 = limit at the BB MA) | | price |
| **Stop** — beyond the wick extreme of the trigger candle | | price |
| Stop distance | | points |
| **Target** — first opposing menu level giving ≥1.5R, less 2.0 pts front-run | | price |
| Which level is the target | | name it |
| Target distance | | points |
| Resulting R multiple | | |

## 8. Anything the sheet did not ask for

If your chart shows something that changes the read — a level not in the menu, a session
boundary you treat differently, an indicator setting that differs — write it here. **This box
is the most useful one on the sheet.**

```


```

---

# P2 · 2025-01-22 · 09:50 ET

## 1. Level menu — price of every level

| level | price |
|---|---|
| Daily VWAP — mid | |
| Daily VWAP — +1σ | |
| Daily VWAP — −1σ | |
| Daily VWAP — +2σ | |
| Daily VWAP — −2σ | |
| Daily VWAP — +3σ | |
| Daily VWAP — −3σ | |
| NY VWAP — mid | |
| NY VWAP — +1σ | |
| NY VWAP — −1σ | |
| NY VWAP — +2σ | |
| NY VWAP — −2σ | |
| Volume profile — POC | |
| Volume profile — VAH | |
| Volume profile — VAL | |
| Session high so far (from 18:00 ET) | |
| Session low so far (from 18:00 ET) | |
| Prior-day high | |
| Prior-day low | |
| Pre-market high (18:00 → 09:29) | |
| Pre-market low (18:00 → 09:29) | |

## 2. Bollinger basis and bands, per entry timeframe

| entry TF | BB basis (20 SMA) | upper 2σ | lower 2σ |
|---|---|---|---|
| 1m | | | |
| 2m | | | |
| 3m | | | |
| 5m | | | |

## 3. Last completed candle on each entry timeframe

| entry TF | open | high | low | close |
|---|---|---|---|---|
| 1m | | | | |
| 2m | | | | |
| 3m | | | | |
| 5m | | | | |

## 4. Confluence clusters

| # | levels in the cluster (name them) | lowest price | highest price | span (pts) | distinct types |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

## 5. HTF classification

- [ ] uptrend  - [ ] downtrend  - [ ] range

Last two confirmed swing highs: ______________ , ______________
Last two confirmed swing lows: ______________ , ______________

## 6. Does a trigger fire?

- [ ] **No trigger.**
- [ ] **Yes** — complete below.

| | |
|---|---|
| Entry timeframe | |
| Direction | |
| Type — rejection / displacement | |
| Which cluster (row #) | |
| Pattern — A / B / B2 | |

## 7. Resulting trade

| | value | note |
|---|---|---|
| **Entry** (E1 = limit at the BB MA) | | price |
| **Stop** — beyond the wick extreme | | price |
| Stop distance | | points |
| **Target** — first opposing level ≥1.5R, less 2.0 pts front-run | | price |
| Which level is the target | | name it |
| Target distance | | points |
| Resulting R multiple | | |

## 8. Anything the sheet did not ask for

```


```

---

## What happens next

When this comes back, each field is compared at **1.00 point tolerance** and marked
MATCH or MISMATCH with **both** values shown. For every mismatch the comparison states which
side is more likely correct and why, choosing between: **spec ambiguity**, **implementation
bug**, **charting difference**, or **reading error**.

**The detector is not assumed to be right, and it will not be adjusted to match in that pass.**

**A FAIL here is the valuable outcome.** It means the detector does not implement the strategy,
and finding that before a result is read saves the run rather than wasting it. A sheet that
disagrees with the code is worth more than one that agrees.

Two fields matter more than the rest:

- **§1 daily VWAP mid.** Every cluster in the strategy is anchored to the VWAP family. If the
  anchor or the source price differs, nothing downstream can agree.
- **§7 stop.** The detector places it one tick beyond the trigger wick, floored at 10.00 points
  (Amendment A5). If you place it somewhere structurally different, **that is the answer to an
  open question**, not a mismatch to be reconciled — and it is the single most valuable thing
  this sheet can produce.
