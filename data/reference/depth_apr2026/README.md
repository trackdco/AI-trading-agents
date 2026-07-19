# NQ mbp-10 depth snapshots — April 2026 (full month)

Per-minute top-10 order-book snapshots for NQ front-month, condensed from raw Databento
`GLBX.MDP3` `mbp-10` exports (~13 GB compressed / ~144 GB raw → 7.2 MB here).

## Files
- `nq_depth_YYYY-MM-DD_ny.csv` — NY window, 08:00–11:00 ET
- `nq_depth_YYYY-MM-DD_london.csv` — London window, 02:00–05:59 ET
- 48 files covering every April 2026 trading day (weekends excluded; Sunday sessions have
  the NY-evening file only).

## Schema (long format, same as the Apr 1 hand sample)
| column | meaning |
|--------|---------|
| `ts` | minute timestamp, tz-aware `America/New_York` (last book state in that minute) |
| `side` | `bid` or `ask` |
| `price` | level price (0.25 tick) |
| `size` | resting contracts at that level |

One row per (minute, side, level); up to 10 bid + 10 ask levels per minute.

## Notes
- **Front-month only** — when a raw file carries multiple instrument_ids, the most active
  (modal) instrument is kept.
- **2026-04-10 is DEGRADED** — Databento flagged this session; use with care.
- Built with `scripts/condense_depth.py` (CSV.zst variant). Raw files were never committed
  (multi-GB); only these condensed snapshots.
- Source batch job: `GLBX-20260718-SKNCBEGBR8`.

## Intended use
Human study / live-phase reference for order-book behavior at confluence levels
(depth walls, pulls, absorption). **Not** an engine input — book depth is not
replay-accurate in the deterministic backtester.
