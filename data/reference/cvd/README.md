# NQ trades footprint / CVD source — April 2026

Per-minute, per-price, per-aggressor-side footprint condensed from raw Databento
`GLBX.MDP3` `trades` ticks (aggressor-tagged tape). This is the source the engine derives
CVD (cumulative volume delta), footprints, delta, and absorption grading from.

## Files — full champion span (2026-02-01 → 2026-07-19, contiguous)
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
