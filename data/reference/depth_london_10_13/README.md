# NQ MBP-10 depth — LONDON 10:00–13:00 window (Jun 2025 → …)

Per-minute top-10 order-book snapshots for the **10:00–13:00 Europe/London** window, condensed
from raw Databento `GLBX.MDP3` `mbp-10` exports Angus pulled (298 daily files, 9.29 GB raw →
~0.15 MB per month here). For **Brake's London-session strategy work**.

**Status: ✅ COMPLETE — Jun 2025 → Jul 2026 (14 months, 298 trading days, 1,069,240 rows, 2.2 MB).**
Spans 2025-06-02 → 2026-07-24. All 298 source days condensed; only the two entries in
`KNOWN_GAPS.csv` are anything other than a full 180-minute session.

## This does NOT duplicate `depth_london/` — it extends it

| folder | window (London) | format | files |
|---|---|---|---|
| `depth_london/` | **08:00–10:00** (2h) | wide CSV, raw Databento columns | 295 daily |
| `depth_london_10_13/` ← this | **10:00–13:00** (3h) | long parquet, condensed | monthly |

They are **adjacent, not overlapping**. Together: continuous **08:00–13:00 London** coverage over
the same date range (2025-06-02 → 2026-07-22).

## Schema (long format)

| column | meaning |
|---|---|
| `ts` | minute timestamp, tz-aware **UTC** (last book state within that minute) |
| `side` | `bid` or `ask` |
| `level` | 0–9 (0 = best) |
| `price` | level price, 0.25 tick (decoded from Databento 1e-9 fixed-point) |
| `size` | resting contracts at that level |
| `ct` | **order count** at that level — how many orders make up the size |

Exactly 10 bid + 10 ask rows per minute → **3,600 rows per full trading day**
(180 minutes × 20 levels).

**Timestamps are UTC, the window is London-local.** Convert with
`.dt.tz_convert('Europe/London')` (or `'America/New_York'` to line up with `depth_2026/`).
Because the window is London-anchored, the **UTC hour shifts at the DST boundary** — 09:00 UTC
during BST, 10:00 UTC during GMT. Verified correct across the 2025-10-26 switch: both UTC start
times appear in `2025-10`, with the London window pinned at 10:00–12:59 throughout. That is
expected behaviour, not drift.

## Validation (every committed month)

Checked on ingest — all months pass unless noted:
- row count == days × 180 × 20
- exactly **10 bid + 10 ask levels every single minute**
- **zero crossed books** (best bid < best ask on every snapshot; 3,780/3,780 for Jun)
- asks ascending / bids descending within each snapshot
- prices are real NQ (Jun-25 median 21,826 → Nov-25 median 25,220), no 1e-9 fixed-point leakage
- no nulls
- median spread 0.75pt (1.00pt in Nov-25)

## ⚠ KNOWN DATA GAPS — machine-readable in `KNOWN_GAPS.csv`

**Exclude these programmatically — do not rely on reading this prose.**

```python
gaps = pd.read_csv("data/reference/depth_london_10_13/KNOWN_GAPS.csv", parse_dates=["date"])
drop = set(gaps.loc[gaps.status == "MISSING", "date"].dt.date)
df = df[~df.ts.dt.tz_convert("Europe/London").dt.date.isin(drop)]
```

| date | minutes | status | note |
|---|---|---|---|
| 2025-09-09 | 181 | EXTRA | extra boundary minute at 09:59 London; harmless |
| 2025-11-28 | **1** | **MISSING** | day after US Thanksgiving; only 1 snapshot |

**2025-11-28 is the dangerous one:** a day with a single snapshot still looks like a valid day to
`groupby(date)`, so it will silently skew any per-day statistic. Treat it as absent.
**TODO: re-pull 2025-11-28 from Databento and replace** — the gap is in the source extraction,
so a fresh pull for that date should fix it.

`KNOWN_GAPS.csv` is regenerated from the data itself (any day whose minute-count != 180), so it
stays correct as new months are added. Every other day is exactly 180 minutes.

## DST verified across both switches

| switch | date | UTC start before → after | London window |
|---|---|---|---|
| BST → GMT | 2025-10-26 | 09:00 → 10:00 | 10:00–12:59 (unchanged) |
| GMT → BST | 2026-03-29 | 10:00 → 09:00 | 10:00–12:59 (unchanged) |

Both months contain both UTC start hours, confirming the extraction is **London-anchored**. Had it
been UTC-anchored, the session would have silently shifted by an hour at each switch.

## The book is genuinely thin

Median **2 contracts and 2 orders per level**; max seen 502 contracts. This matches what Brake
independently measured on Sierra's April depth (~72 contracts across all 20 levels). It is not a
data defect — NQ's resting book really is that thin. A "wall" in NQ is **tens** of contracts, not
thousands. Size any wall thresholds accordingly.

## Provenance

Raw Databento `GLBX.MDP3` / `mbp-10` / `NQ.v.0`, condensed in Colab: per-minute last book state,
zstd-19 dictionary-encoded parquet. Raw exports (9.29 GB) are NOT committed — repo policy is
condensed artifacts only.
