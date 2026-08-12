# NEWS LAB — SPEC v1 (12 Aug 2026)

Owner: Angus. Executor: Claude Code. Discipline: layered build, verdict gate
at every boundary (same as the canon rebuild). Units: R first, points
alongside, NQ $20/pt. Nothing ships without its gate passing.

## Objective
Primary lane (Angus's ask): **enter before red-folder releases and predict
the direction** — test whether anything knowable pre-print predicts the
post-print NQ move well enough to beat gap-adjusted stop fills.
Fallback lane (same tables, free): the post-print reaction map
(continuation vs fade by surprise size), which needs no prediction.

## Non-negotiables
1. **No revised data anywhere.** Every actual is a FIRST PRINT (ALFRED
   vintage or the calendar's own as-of row). Joining a current FRED series
   is the same bug class that killed the canon. `vintage.py` is the only
   door for actuals.
2. **Causal z only.** Surprise z-scores use strictly-past events
   (min history 8). `vintage.causal_z` — already tested.
3. **Seal enforced in code.** Rows dated ≥ `NEWSLAB_SEAL_FROM` are
   invisible to discovery. Sealed scoring requires `NEWSLAB_UNSEAL=1` AND a
   committed PREREG-L3.md sha. One shot.
4. **No invented dates or values.** Generators flag `needs_verification`;
   scrapers raise on parse failure. A gap in the event table is a task,
   never a guess.
5. **Gap-fill bounds, not point estimates.** Stop fills through a print are
   reported as [best = stop, worst = bar-extreme] ranges. All L3 expectancy
   uses the WORST bound.

## Layers & gates
**L0 — event table.** Static seeds (FOMC 2023–26, verified rows) + rule
generators (claims Thursdays, ISM business-day rule) + BLS/BEA schedule
scrapers + the consensus calendar's own dates.
GATE L0: every Tier-1 family ≥ 95% of expected event count over
2023-01→2026-01 (bar coverage), zero unexplained duplicate/missing months,
all `needs_verification` rows resolved for Tier-1. Verdict doc committed.

**L0b — actuals & consensus.** ALFRED first prints for all mapped fields;
consensus from FF scrape (manual CSV overrides win). Surprise + causal z.
GATE L0b: spot-check 10 randomly drawn events against the original release
PDFs/articles (actual AND consensus). 10/10 or stop and fix. Special check:
one NFP event straddling a benchmark revision, to prove the first print is
what's stored (e.g. a 2025 month later revised by the −911k benchmark).

**L1 — behaviour census.** `census.run_census` over every L0 event with bar
coverage: drift, release bar, horizons, MFE/MAE, gap-fill bounds.
Outputs: `output/news_census.parquet`, `continuation_table`, `gapfill_table`.
GATE L1: coverage_ok ≥ 90% of events inside bar range; 3 hand-verified
events against TradingView (release-bar OHLC + 30m move within 1pt);
timezone tripwire — assert the 08:30 CPI bar is 08:30 ET in BOTH a January
and a July event (DST, the house speciality).

**L2 — predictor table.** Cleveland nowcast gap (as-of enforced), feeder
chain (PCE from CPI+PPI), Kalshi skew (after ticker discovery), pre-drift
(from L1). Every predictor column carries its as-of timestamp.
GATE L2: for each predictor, assert as-of < release ts on 100% of rows.

**L3 — the test.** `l3.pooled_direction_test` per predictor at +30m
(sensitivity at +15/+60), stop 20pt (sensitivity 30/50).
CEILING test first: predictor = `surprise_z` itself (uses the actual — a
deliberate lookahead run, clearly labelled, ONLY to measure the best case:
"if you knew the print, was the direction even tradable after gap costs?"
If the ceiling fails, every honest predictor fails and the lane closes).
Then the honest predictors. Kill rule per PREREG-L3.md.
GATE L3: prereg sha committed BEFORE `NEWSLAB_UNSEAL=1`; sealed era scored
once; verdicts (R first) appended to the verdict log regardless of outcome.

## Data gap to resolve (task, not blocker)
Bars in repo end **2026-01-31**; Angus's stated window runs to Jul 2026.
Fill Feb–Jul 2026 via a Databento OHLCV-1m top-up (price with the cost
endpoint first) or Sierra .scid export from the box. Until filled, the
census runs 2023-01→2026-01 and the seal boundary is set accordingly.

## Explicitly out of scope for v1
Live execution, order routing, sizing, any Hermes wiring. This is a
research lane. If L3 says TRADE-CANDIDATE, the promotion path is the
existing ARM gate — with one addition: a news-slippage force-test, because
B1's "median 0-tick entry slippage" invariant is from limit-entry logic and
does NOT hold for anything resting through a print.
