# NQ per-minute top-10 depth — full year (Feb–Jul 2026)

Long-format per-minute order-book snapshots for the NY morning window, condensed from the
raw MBP-10 exports Angus pulled via Databento (uploaded to trackd-co-app as
`condensed_GLBX-*.csv`, reshaped here by `scripts/condense_heatmap_csv.py`).

## Files
- `nq_depth_YYYY-MM-DD_ny.csv` — one per trading day, **08:00–10:29 ET** (the entry window).
- 100 days: Feb 17, Mar 18, Apr 18, May 20, Jun 21, Jul 6 (Feb 2 → Jul 8).

## Schema (identical to depth_apr2026)
| column | meaning |
|--------|---------|
| `ts` | minute timestamp, tz-aware `America/New_York` (last book state in the minute) |
| `side` | `bid` or `ask` |
| `price` | level price (0.25 tick; decoded from 1e-9 fixed-int) |
| `size` | resting contracts at that level |

Up to 10 bid + 10 ask levels per minute. **Validated:** the April overlap matches
`depth_apr2026` exactly (3,000/3,000 rows, 0 size mismatches).

## Note
Window is 08:00–10:29 (vs depth_apr2026's 08:00–11:00) — covers the 09:40–10:15 golden
window fully. Human-study / conviction-filter reference; NOT a replay-accurate engine input.
