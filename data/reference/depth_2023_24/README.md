# NQ MBP-10 depth — NY window, 2023/24 HOLDOUT

Per-minute top-10 order-book snapshots for the **08:00–10:30 ET** window, covering the 128
pre-registered holdout days (`docs/HOLDOUT-2023-24-PREREGISTRATION.md`, seal `f4e17f17…`).

**Status: ✅ COMPLETE — 128/128 sealed days, 384,020 rows, 16 MB.**

| | |
|---|---|
| files | 128 (`nq_depth_YYYY-MM-DD_ny.csv`) |
| rows | 384,020 |
| minutes/day | 150 (08:00–10:29), one day 151 |
| levels/minute | exactly 20 (10 bid + 10 ask) on every minute |
| price range | 14,411 – 20,788 |

Same long format and same filename pattern as `depth_2025/` and `depth_2026/`, so
`scripts/depth_features.load_depth`, `conviction_report`, `wall_refine`,
`book_support_2025` and `src/canon/features.depth_at` read it with no changes. Verified by
calling `depth_at` directly on a holdout day.

## Schema

| column | meaning |
|---|---|
| `ts` | minute timestamp, tz-aware **America/New_York** (last book state in that minute) |
| `side` | `bid` or `ask` |
| `price` | level price, 0.25 tick |
| `size` | resting contracts at that level |

## Window: 08:00–10:30, not 08:00–11:00

The fit-window folders run to 11:00. This one stops at 10:30 (Angus, 2026-07-27): the golden
window is 09:40–10:15 and depth is only ever read AT the fill minute. Checked against
`output/canon_book.parquet` before trimming — pre fills run 08:01–09:23, gold 09:41–10:12,
and **zero** fills land at or after 10:15 anywhere in the universe, including rejected
candidates. 10:30 leaves 18 minutes of headroom and cut ~17% off the MBP-10 bill.
`tests/test_colab_holdout_notebook.py` fails if anyone narrows it below a real fill.

## KNOWN GAP: no per-level order count (`ct`)

Like `depth_2025/` and `depth_2026/`, this format carries **size only, not `NumOrders`** —
so one order of 500 is indistinguishable from fifty of 10. `depth_london/` and
`depth_london_10_13/` DO keep it.

Not fixed, and deliberately not: the gap is **symmetric**. The fit-window NY folders lack
`ct` too, so adding it here alone would supply the field out-of-fit and not in-fit —
useless for deriving anything. Using `ct` for NY means re-pulling both spans.

## HARD LIMIT worth knowing before designing against this data

MBP-10 spans a **median 5.25 points** of book (2.25 each side). Anything about "structural
levels 40 points away" is outside what this data can represent by ~8x — see
`docs/FINDING-exit-discretion-headroom.md`. The canon's own `dep_wall_*` checks read
immediate microstructure at the touch (median 3.50 pts from entry), not structure.
