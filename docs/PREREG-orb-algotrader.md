# Pre-registration: 15-minute Opening Range Breakout, ported from johnamcruz/algoTraderBot

**Written before any result is computed. 2026-09-05.** Source: `strategies/orb.py` and `config.py`
at commit c4ad831. Data imported from the same repo to `data/reference/algotrader_3min/`.

## Why this one
Of ten ideas tested in this repository, all were level retests, band reversions or sweeps. ORB is
different in the way that matters: the 09:30 ET open is a **scheduled liquidity event** with forced
participants (funds executing at the open, overnight positions being reconciled). That is the "someone
must trade on a calendar" property, which is the filter this programme adopted after the overnight and
calendar tests.

## The source repo, assessed
It publishes **no performance claims**, ships its data, and independently implements the rule that cost
this repository a day and a half: *"Entry and exit are never the same candle."* Bars straddling both
stop and target are scored as the stop. Its ML entry grader is NOT used here - the `.joblib` bundles
ship pre-trained with **no training script in the repo**, so lookahead cannot be audited. Only the
mechanical entry is ported. That is stated as a limitation, not a criticism.

## Data, verified before use
5 instruments x 3-minute bars, 2021-04 to 2026-06: NQ 603,715 · ES 602,766 · RTY 601,700 ·
YM 602,656 · GC 603,710 = 3,014,547 bars, ~1,590 sessions each. Zero malformed OHLC rows, zero
non-positive volume, 99.6-99.8% of gaps exactly 3 minutes. Their NQ matches our Databento tape on
**99.4% of 403,945 overlapping bars** (differences are roll days).

## The rules as ported (verbatim from the source)
- **Opening range**: high/low of the first **5 bars** at or after **09:30 ET**. Active only from the
  bar AFTER that window closes, so the range is entirely in the past.
- **Gate**: ADX(14) >= **18**. No entries at or after **16:00 ET**.
- **Long**: `close[i-1] <= or_high[i-1]` and `close[i] > or_high[i]`. **Short**: mirrored on or_low.
- **Entry** at the signal bar's close. **Stop** = **0.5 x ATR(20)** from entry. One position at a time.
- **Exits scanned from the bar AFTER entry.** A bar touching both stop and target scores the stop.
  Flat at the session end.

**Exit variants.** Headline is the repo's own shaping, expressed as a plain rule (no ML):
- **GIVEBACK** — hold the initial 1R stop until the peak reaches **+2.0R**; thereafter the stop never
  sits more than **0.75R** below the running peak, ratcheting only. Peak measured from each bar's
  favourable extreme, as the source does.
Controls: fixed **1R**, **2R**, **3R** targets on the same trades.

**Cost**: **2 ticks** per round trip of the instrument traded, charged in R against each trade's own
stop; stressed at **5 ticks** (both legs are market orders). Ticks: NQ/ES 0.25, RTY/GC 0.10, YM 1.0.

## Pass/fail, declared now
The GIVEBACK variant **PASSES** only if all six hold:
1. Net R per trade > 0 on **NQ** and on at least **3 of 5** instruments.
2. Pooled t-statistic > **2.5**.
3. `scripts/reality_gate.py` passes on the NQ dump.
4. Still positive at the **5-tick** cost, on NQ and on at least 3 of 5.
5. At least **100 trades** per instrument.
6. Positive in **both halves** (2021-2023 vs 2024-2026) on NQ.
Anything else is a FAIL. The fixed-R controls are reported but cannot themselves constitute a pass -
they exist to show whether the giveback shaping earns its complexity.

## Predictions (scored after)
- P1: ORB fires on more than 40% of sessions.
- P2: GIVEBACK beats fixed 1R but loses to fixed 2R or 3R.
- P3: no variant passes all six conditions.
