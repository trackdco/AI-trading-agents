# GATE L1 — behaviour census verdict

`output/news_census.parquet` — 444 print events measured against the repo's
NQ 1-minute bars (1,089,712 bars, 2023-01-02 → 2026-01-30).

## VERDICT: **PASS on 2 of 3 gates; 1 needs your eyes (5 minutes)**

| SPEC gate | requirement | result |
|---|---|---|
| coverage | ≥ 90% of events inside bar range | **99.5%** (442/444) — PASS |
| timezone tripwire | 08:30 CPI bar is 08:30 ET in a January AND a July event | **PASS**, now a permanent test |
| hand-verify | 3 events vs TradingView, OHLC + 30m within 1pt | **OUTSTANDING** — no TradingView access from here |

## 1. Coverage — PASS

442 of 444 events measured (99.5%). The 2 misses are events whose ±120-minute
window is not fully covered by the bar files.

Unsealed (discovery): 407. Sealed: 37, untouched.

## 2. Timezone tripwire — PASS, and it validates every downstream verdict

Every number in `CEILING-TEST.md` and `VERDICT.md` rests on the release bar
being the bar that actually contains the release. An hour's error in one half
of the year would silently shift everything.

Checked against the **bars**, not the tz library (a library can be
self-consistently wrong — the data cannot):

| event | stamp | UTC offset | max-volume bar |
|---|---|---|---|
| CPI 2023-01-12 | 08:30 EST | −05:00 | 08:30 ✓ |
| CPI 2023-07-12 | 08:30 EDT | −04:00 | 08:30 ✓ |

Then across all 167 high-impact events:

- **max-volume bar sits exactly on T: 86.8%**
- **max-range bar sits exactly on T: 94.0%**
- every deviation is **forward** (+1/+2/+3m) — the reaction continuing, which
  is expected. Backward drift, which would mean the stamps are late, occurs
  **once in 167**.

No systematic offset. Locked in as `tests/test_timezone_tripwire.py` (3 tests)
so a future DST regression fails loudly instead of quietly poisoning results.

### One real anomaly, explained but not dismissed

**CPI 2023-01-12** is the single event where the T−1m bar is *larger* than the
release bar: the 08:29 bar spans **157 points** and closes at its low, before
the 08:30 print. It is 1 of 167 (0.6%), it is not a timestamp artifact (the
08:30 bar still carries peak volume), and it does not move any verdict.

It is recorded here because it is exactly the shape a pre-release information
leak would take, and because it means `ref` = close(T−1m) is contaminated for
that one event — the move had already happened.

## 3. Hand-verification — OUTSTANDING, needs you

The SPEC requires 3 events checked by eye against TradingView. There is no
TradingView access from this container, and I will not sign off a gate I did
not perform. **Check these three** (NQ front contract, 1-minute, ET). Chosen to
span both DST halves and both release times:

**CPI 2024-01-11, 08:30 EST**
- release bar: O 17028.50 · H 17057.00 · L 16933.50 · C 16956.00 (range 123.50, vol 5,890)
- ref (08:29 close) 17025.75 → +30m close 16910.25 → **move_30m −115.50**

**CPI 2024-07-11, 08:30 EDT**
- release bar: O 20884.75 · H 20976.00 · L 20884.00 · C 20955.75 (range 92.00, vol 5,382)
- ref (08:29 close) 20890.75 → +30m close 20881.50 → **move_30m −9.25**

**FOMC 2024-12-18, 14:00 EST**
- release bar: O 22288.50 · H 22295.00 · L 22225.00 · C 22230.00 (range 70.00, vol 3,294)
- ref (13:59 close) 22288.50 → +30m close 22033.25 → **move_30m −255.25**

Tolerance: OHLC exact, +30m move within 1 point. If all three match, GATE L1 is
fully PASS. If any fails, `VERDICT.md` must be re-run — the conclusions depend
on these bars being right.

> Note: the census picks the per-ET-day dominant contract by volume, so around
> a roll TradingView's continuous chart may show a different contract. All
> three above are mid-cycle dates chosen to avoid roll ambiguity.

## Outputs

- `output/news_census.parquet` — 444 rows: drift, release bar OHLC/volume,
  horizon moves (5/15/30/60/120m), MFE/MAE, gap-fill bounds at 10/20/30/50pt
  both sides, sealed flag.
- The gap-fill tables are reusable evidence for **any** strategy holding a stop
  through a scheduled release, not just this lane.
