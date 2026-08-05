# Data Inventory — what we actually have, as of 2026-08-05

Audited directly from the files in this repo, not from memory. Every number
below is reproducible with `python tools/audit_data.py` (see bottom).

**Read this before designing any strategy test.** The validation pipeline in
`context/strategy-research-protocol.md` assumes specific data exists for
specific windows. Three of the things that pipeline assumes are not here yet.

---

## 1. Minute bars (OHLCV-1m)

Four zstd archives at the repo root. Columns:
`ts_event, rtype, publisher_id, instrument_id, open, high, low, close, volume, symbol`.

| File | Rows | First bar | Last bar |
|---|---:|---|---|
| `glbx-mdp3-20230101-20250301.ohlcv-1m.csv.zst` | 1,102,836 | 2023-01-02 23:00Z | 2025-02-28 21:59Z |
| `glbx-mdp3-20250101-20250501.ohlcv-1m.csv.zst` | 175,785 | 2025-01-01 23:00Z | 2025-05-01 23:59Z |
| `glbx-mdp3-20250502-20251001.ohlcv-1m.csv.zst` | 214,857 | 2025-05-02 00:00Z | 2025-10-01 23:59Z |
| `glbx-mdp3-20251002-20260131.ohlcv-1m.csv.zst` | 162,748 | 2025-10-02 00:00Z | 2026-01-30 21:59Z |

**Continuous bar coverage: 2023-01-02 → 2026-01-30.** Archives 1 and 2 overlap
over Jan–Feb 2025; de-duplicate on ingest.

Three things about these bars that will bite if ignored:

- **🔴 They contain calendar spreads, not just outrights.** Alongside `NQH6`
  the files carry `NQH6-NQM6`, `NQZ5-NQH6` and friends — spread instruments
  whose price is a *differential*, not a price level. In the 2023–2025 archive
  that is **108,696 of 1,102,836 rows (9.9%), trading between 106 and 840**,
  sitting in the same column as outrights trading between 10,755 and 24,600.
  Ingest must filter to outrights (`"-" not in symbol`) as the very first step.
  Miss it and every VWAP, Bollinger band and volume profile in the system is
  quietly wrong — and it will not look like a bug, it will look like volatility.
- **They are raw quarterly contracts, not a stitched series.** Symbols run
  `NQH3 … NQH5 … NQM5 … NQZ5 … NQH6`. Roll handling is the ingest layer's job;
  a naive concatenation puts a fake gap in the series four times a year.
- **`volume` has no aggressor side.** You can compute volume profile, VWAP and
  POC from these. You **cannot** compute CVD from these. See §3.

### ⚠ Gap 1 — no bars after 2026-01-30

Nothing exists for **2026-02-01 → today**. That means:

- The Feb 2026 calibration gate in `spec-1` (28 hand-logged trades) **cannot
  run** — the month it calibrates against has no bars.
- Half of the intended optimisation window (2025-H2 → Jul 2026) has no price
  series, only the book snapshots in §2.

---

## 2. Order book snapshots — the "heatmap" substrate

510 CSV files at the repo root, MBP-10 schema (top 10 levels each side, with
size and order count). Three naming conventions, two sessions, **295 unique
trading days**.

| Set | Files | Session (local) | Dates | Symbol | Price format |
|---|---:|---|---|---|---|
| `glbx-mdp3-<date>.mbp-10_condensed.csv` | 295 | **London 08:00–10:00** | 2025-06-02 → 2026-07-22 | `NQ.v.0` | decimal (`29102.0`) |
| `condensed_glbx-mdp3-<date>.mbp-10.csv` | 115 | **New York 08:00–10:29 ET** | 2025-06-02 → 2025-11-20 | `NQ.c.0` | integer ×1e9 (`25270250000000`) |
| `condensed_GLBX-20260720-<id>.csv` | 100 | **New York 08:00–10:29 ET** | 2026-02-02 → 2026-07-08 | `NQ.c.0` | integer ×1e9 |

Sampling is **one snapshot per minute** (~120–150 rows per file), not the full
event stream. The session extraction is DST-correct in both sets — the UTC hour
shifts with BST and EST exactly as it should, so both are genuinely anchored to
local session open.

### ⚠ Two silent-corruption traps in this set

1. **Price scaling differs between the London and NY sets.** London is decimal;
   NY is fixed-point ×1e9. Concatenating without normalising produces prices
   off by a factor of a billion, which will not look like an error in an
   indicator — it will look like a regime.
2. **Continuous-contract convention differs.** London is `NQ.v.0` (volume-based
   roll), NY is `NQ.c.0` (calendar roll). Across a roll date the two sets can
   be quoting *different contracts*. Fine as long as each session is analysed
   on its own series; a cross-session strategy has to reconcile them.

### Session coverage

- **London: complete.** 295 trading days, 2025-06-02 → 2026-07-22, no gap
  longer than a long weekend.
- **New York: 215 days, with two holes.**
  - 2025-10-13 → 2025-10-23 (9 weekdays)
  - **2025-11-21 → 2026-01-30 (51 weekdays)** — this is the big one
  - and nothing after 2026-07-08

| Month | NY days | London days |
|---|---:|---:|
| 2025-06 | 21 | 21 |
| 2025-07 | 23 | 23 |
| 2025-08 | 21 | 21 |
| 2025-09 | 22 | 22 |
| 2025-10 | 14 | 23 |
| 2025-11 | 14 | 19 |
| 2025-12 | 0 | 22 |
| 2026-01 | 0 | 21 |
| 2026-02 | 17 | 20 |
| 2026-03 | 18 | 22 |
| 2026-04 | 18 | 22 |
| 2026-05 | 20 | 21 |
| 2026-06 | 21 | 22 |
| 2026-07 | 6 | 16 |

---

## 3. ⚠ Gap 2 — there is no CVD data anywhere in this repo

This one matters most, because the pipeline as described leans on CVD at the
refinement step ("what does the order flow say at entry?").

CVD (cumulative volume delta) is the running total of **volume that hit the ask
minus volume that hit the bid** — it requires knowing, trade by trade, which
side was the aggressor.

What we have instead:

- **OHLCV bars** carry total volume with no side. Not enough.
- **MBP-10 snapshots** carry *resting* liquidity — orders waiting, not orders
  executed. That is the heatmap. It is genuinely useful (it shows where size is
  stacked and where it gets pulled), but it is a different thing from CVD.
  Scanning all 510 book files: **29,574 adds, 22,212 cancels, 15,630 modifies,
  and 3 trades.** Three. The condensing kept the book state and discarded the
  tape.

So today we can ask "was there a wall of resting offers above the high?" We
cannot ask "were buyers lifting offers into it?" To get CVD we need the
`trades` (or `mbp-1`/`tbbo`) schema from Databento, which carries an aggressor
side per print.

---

## 4. ⚠ Gap 3 — no 2023 or 2024 book/flow data

The intended out-of-sample design is: optimise on 2025-H2→2026-H1, then test
the frozen rules on untouched months in 2023 and 2024.

For 2023–2024 we have **minute bars only**. No book, no flow.

Consequence: any strategy whose entry filter uses heatmap or CVD **cannot be
validated out-of-sample** on 2023/2024 as things stand. There are three honest
ways forward and they should be chosen deliberately:

| Option | What it costs | What it buys |
|---|---|---|
| **A. Buy the missing book/flow data** for 3 months in 2023 + 3 in 2024 | a Databento pull | the design as intended — genuine OOS on order-flow strategies |
| **B. Split the OOS window in two** — use 2023/24 bars to OOS the *price-based* rules, and hold back untouched 2026 months (e.g. Jun–Jul) to OOS the *flow-based* filters | free | weaker but real; the flow OOS is a shorter, same-regime sample |
| **C. Restrict the strategy book to price-only rules** | free | strongest OOS evidence, but throws away the heatmap edge |

**B is the pragmatic default and A is the right answer if the budget exists.**
Do not quietly do (C) while describing it as (A).

---

## 5. ⚠ Gap 4 — no gold data at all

The Asia-session plan is gold futures. There is no GC or MGC data in this repo
in any schema. Asia-session work is blocked until that is bought — and it is a
separate instrument with its own tick value, session profile and liquidity
regime, so it is a separate validation track, not a re-run of the NQ pipeline
with a different symbol.

---

## 6. Unstructured artifacts

At the repo root: ~40 chart screenshots (`IMG_*.jpg/PNG`, `Screenshot 2026-*.png`)
and `Backtesting March VWAP + Bollinger bands, New York session (April… 2.pdf`
(9.9 MB). These are human evidence — useful for eyeballing a setup and for the
parity gate, useless to the engine. They are already committed; leave them, but
nothing new of this kind should go in the repo root.

`data/reference/feb2026_hand_log.csv` — Angus's 28 hand-backtested trades.
Ground truth for calibration. Committed on purpose.

---

## 7. The shopping list, in priority order

| # | What | Why | Blocks |
|---|---|---|---|
| 1 | NQ `ohlcv-1m`, 2026-02-01 → present | closes Gap 1 | Feb calibration gate; any test on 2026-H1 |
| 2 | NQ `trades`, session windows only, 2025-06 → present | gives CVD where we already have heatmap | every order-flow refinement step |
| 3 | NQ `mbp-10` + `trades`, 3 months of 2023 + 3 months of 2024 | closes Gap 3 | true OOS for flow-based strategies |
| 4 | NQ `mbp-10`, NY session, 2025-11-21 → 2026-01-30 | closes the 51-day NY hole | continuity of the NY sample |
| 5 | GC `ohlcv-1m` + `trades`, Asia window | closes Gap 4 | the entire Asia track |

Sizing note for #2 and #3: the `trades` schema is large (NQ prints hundreds of
thousands of times per session). Pull it **restricted to the session windows**,
aggregate to 1-minute signed volume on ingest, and store only the aggregate.
That keeps the working set in megabytes instead of tens of gigabytes. Price the
actual pulls in the Databento portal before committing — don't estimate.

---

## Reproducing this audit

```bash
python tools/audit_data.py            # prints every table above
python tools/audit_data.py --json     # machine-readable, for CI
```

Re-run it after every data purchase and update this file. A stale inventory is
worse than none — it is how a backtest silently runs on a window with no data
and reports a flat equity curve as "no signals".
