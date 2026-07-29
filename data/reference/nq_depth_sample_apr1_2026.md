# NQ order-book depth sample — April 1 2026, 08:00–11:00 ET

`nq_depth_sample_apr1_2026.csv` — condensed liquidity (heatmap) data for ONE morning session.

- **Source:** Databento batch job `GLBX-20260718-7TJ76U958U` (GLBX.MDP3, schema `mbp-10`,
  parent pull `NQ.FUT`, Apr 1–11 2026). Raw files are ~4.9 GB compressed and stay OUT of git
  on Brake's machine — this file is the hand-off artifact, condensed locally by Brake.
- **Condensing:** front-month outright only (busiest symbol), 08:00–11:00 ET window,
  one book snapshot per minute, all 10 bid + 10 ask levels.
  Columns: `ts` (ET), `side` (bid/ask), `price`, `size` (contracts resting).
  3,600 rows = 180 min × 20 levels. Prices cross-validated against `data/nq_1m.parquet`
  (same window: 24,036–24,270 ✓).
- **Job condition notes (whole Apr 1–11 job):** Apr 4 & 11 missing (weekend), Apr 10
  flagged `degraded` by Databento — avoid that day if more sessions are condensed later.
- **GUARDRAIL (unchanged):** order-flow is NOT an input to the mechanical engine or any
  backtest — it is replay-inaccurate by nature (same reason MIG LiquidityEdge was excluded,
  strategy-doc §2). This sample exists for HUMAN study (where liquidity walls sat vs the
  engine's levels) and for prototyping live-phase visual tools only.

## London window added (2026-07-18)
`nq_depth_sample_apr1_2026_london.csv` — same day/recipe, **02:00–05:59 ET** (Angus's London
request, pass-28): 4,800 rows = 240 min x 20 levels, prices 24,004.5–24,177.5. NY-window file
unchanged. Remaining Apr 2–9 sessions pending (Brake's condenser had a date-parsing bug that
skipped them; fixed, re-run in progress).
