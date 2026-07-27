# NQ trades footprint / CVD source — April 2026

Per-minute, per-price, per-aggressor-side footprint condensed from raw Databento
`GLBX.MDP3` `trades` ticks (aggressor-tagged tape). This is the source the engine derives
CVD (cumulative volume delta), footprints, delta, and absorption grading from.

## Files — FULL CONTIGUOUS TAPE 2025-06-01 → 2026-07-19 (six files, zero dup minutes)
- `footprint_q3_2025.parquet` / `footprint_q4_2025.parquet` — 2025-06 → 2026-01-01.
- `footprint_jan2026.parquet` — **2026-01-02 → 2026-01-30** (Angus pull 2026-07-26; 0.11%
  spread volume band-cleaned; trimmed to the exact q4/feb boundaries so concat never
  double-counts a minute). Closes the gap that made selection-gate `cvd` NaN for Jan.

## Original champion-span files (2026-02-01 → 2026-07-19)
- `footprint_feb_mar2026.parquet` — 2026-02-01 → 2026-03-31, **13.4 MB** (51 days).
- `footprint_apr2026.parquet` — 2026-04-01 → 2026-04-30, **5.1 MB** (~7.7 M ticks).
- `footprint_may_jul2026.parquet` — 2026-05-01 → 2026-07-19, **19.2 MB** (68 days).

Front-month NQ throughout. `volume`/`trades` int64. Load all three and concat for
the complete Feb–Jul 2026 CVD/footprint history.

## Schema
| column | meaning |
|--------|---------|
| `ts_minute` | 1-minute bar timestamp, tz-aware **UTC** |
| `price` | traded price level (0.25 tick) |
| `side` | `B` = buyer-aggressor (lifted the offer) / `A` = seller-aggressor (hit the bid) |
| `volume` | contracts traded at that (minute, price, side) |
| `trades` | tick count at that (minute, price, side) |

**CVD** = running cumsum of (per-bar B volume − A volume).

## Cleaning
- Front-month only. Raw pull carried a small amount of calendar-spread and back-month
  trades; removed by keeping only ticks inside each day's ground-truth
  `[low, high]` band from `nq_1m_feb_jul2026.parquet` (±1 tick). Dropped volume:
  **0.12%** (April) / **2.65%** (Feb–Mar) / **2.27%** (May–Jul).
- The 1m master bars end 2026-07-15; the 3 tail days (Jul 16, 17, 19) had no bar band,
  so they were cleaned with a per-day volume-weighted-median ±700 pt front band instead.
- **Signed integers:** `volume`/`trades` are int64. The DBN export delivered these as
  uint32, which silently wraps on subtraction (CVD delta = buys − sells) — cast to int64
  on ingest to prevent that.
- Validation: monthly CVD ran −655 → **+38,973** (net buying), consistent with the
  April front-month uptrend 23.7k → 27.7k. Aggressor tagging confirmed sane.

## Notes
- Built with `scripts/condense_trades.py`. Raw ticks never committed (multi-GB).
- **Scope: April 2026 only** — a first validation slice within the champion span
  (Feb–Jul 2026). Full-span pull is the next step if CVD proves it separates the
  give-back / entry-miss loser pools from winners.
- Unlike order-book depth, CVD is **causally replayable** and is a legitimate
  engine-feature candidate (not human-study-only).

---

## 2023/2024 HOLDOUT TAPE (added 2026-07-27)

Six monthly files for the pre-registered out-of-regime holdout
(`docs/HOLDOUT-2023-24-PREREGISTRATION.md`, seal `f4e17f17…`, 128 days):

| file | rows | ET days | volume |
|---|---|---|---|
| `footprint_holdout_2023-07.parquet` | 563,192 | 26 | 5,719,612 |
| `footprint_holdout_2023-09.parquet` | 619,941 | 26 | 5,833,598 |
| `footprint_holdout_2023-11.parquet` | 533,380 | 26 | 6,174,403 |
| `footprint_holdout_2024-03.parquet` | 623,699 | 25 | 5,836,644 |
| `footprint_holdout_2024-04.parquet` | 822,741 | 27 | 7,384,510 |
| `footprint_holdout_2024-10.parquet` | 847,165 | 28 | 5,470,783 |

Identical schema and dtypes to the fit-window files. Pulled and condensed by
`notebooks/colab_holdout_pull.ipynb`; per-day fetch record in
`MANIFEST_holdout_2023_24.csv` (128 days, **zero** with no data).

**Window is 18:00 ET (prior day) → 11:00 ET**, not the full session — the span every CVD
feature reaches back over (`cvd_ON` / `cvd_ASIA` / `cvd_LON` / `cvd_PM`) plus the forward
room the in-trade layer needs. That is why density is ~74% of the fit-window files
(811-838 minutes/day vs 1107-1135): 17h of 23h, exactly. The remaining difference is real —
2023/24 NQ traded 195-273k contracts/day against 400-420k in 2025/26, at roughly half the
index level.

ET day count exceeds the 128 sealed days (158) because each day's window opens at 18:00 ET
the previous evening, so Sundays appear. Every sealed day is present; verified by
`tests/test_holdout_cvd_integrity.py`.

### Known issue in the FIT-window files — not the holdout

`footprint_q3_2025.parquet` and `footprint_q4_2025.parquet` carry calendar-spread prints at
prices 200–493 that the band-clean removed from the 2026 files:

| file | off-band rows | volume | share |
|---|---|---|---|
| `footprint_q3_2025` | 71,516 | 795,211 | 1.90% |
| `footprint_q4_2025` | 55,345 | 539,335 | ~1.3% |
| jan/feb-mar/apr/may-jul 2026 | 0 | 0 | clean |

Impact measured: per-minute delta is unchanged on 82% of minutes, and where it moves the
median shift is ~40 contracts against a typical daily net delta of ~2,050 — about **2%**.
Noise-level, not distorting.

**NOT fixed, deliberately.** Cleaning it changes the CVD features, which changes the canon's
checks, which changes the arming reference — a Tier-1 change (`PROMOTION-GATE` §E). Post-
launch, behind freeze → OOS → sign-off. The holdout files above are clean by construction
and are asserted so by test.
