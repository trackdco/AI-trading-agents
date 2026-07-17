# Progress Tracker

Update at the END of every Claude Code session. This file is how sessions hand off to each other and how Angus audits without reading code.

## Current state

- **Active phase:** 1 — Market Engine & Backtester
- **Active spec:** spec-1-market-engine-backtester.md
- **Last completed step:** Step 4 code (indicators + parity-report tool) — **PARITY GATE now blocks all further steps**
- **Blocked on:** (1) Databento data in `data/raw/` — needed to generate the real parity report and full-dataset gap report; (2) Angus's reference-chart values + sign-off for Feb 11 09:48 ET and Feb 17 09:50 ET
- **Next action:** when data lands: `python -m src.engine.data` then `python -m src.engine.indicators --parity`; send `output/parity_report.md` to Angus. Steps 5–9 do not start before his sign-off.

## Gates ledger (Angus sign-offs — append-only)

| Date | Gate | Result | Notes |
|---|---|---|---|
| 2026-07-17 | strategy-definition v1.0 locked | PASSED | Q&A incorporated; daily VWAP anchor confirmed 18:00 ET |
| — | Spec 1 Step 4 parity report | pending | |
| — | Spec 1 Step 8 calibration classification | pending | |

## Decision log (append-only; one line per decision, with source)

- 2026-07-17 — MIG LiquidityEdge excluded from mechanical system (Angus; strategy doc §2)
- 2026-07-17 — Agents never see P&L/prior outcomes; system proposes, human disposes on rule changes (Angus + Claude)
- 2026-07-17 — Entry window W1 8:00–11:00 primary; W2 full-day priority test; BE-at-1R vs none = priority tournament (Angus)
- 2026-07-17 — Data: Jan 2026→present primary; 2025 as robustness check only (Angus regime rationale, honesty guard noted)

## Session log (newest first)

### 2026-07-17 — Spec 1 Steps 1–4 (Claude Code, remote session; Pat driving)
- Steps completed: step-1 repo scaffold (strategy.yaml fully §-traced, news calendar seed, tree, .gitignore, README); step-2 data ingest (Databento CSV/DBN -> validated parquet, 18:00-ET session dating, lead-contract roll tagging, gap report, 8 tests); step-3 resampler + sessions (close-labeled TF bars, §2 box classifier, running/frozen session extremes, prior-day/week H/L, post-release data levels, 12 tests incl. test_dst_boundary); step-4 indicators (TradingView-convention BB, 18:00/09:30 anchored VWAPs + sigma bands, volume profile with causal running daily POC, parity-report CLI, 13 tests incl. test_ny_vwap_absent_premarket)
- Checks passed: ruff clean; 32/32 pytest; one commit per step on branch claude/session-setup-lzzfzm
- Divergences/flags raised: dependency additions flagged in commits (pyarrow — required for spec-mandated parquet; pyproject.toml + .env.example as infra); volume-profile bar-volume allocation is an engineering approximation of TradingView's — first suspect if daily POC misses the 1.0 pt parity tolerance
- Questions parked for Angus: (1) session box boundaries (conventional 18:00/03:00/09:30/16:00 ET seeded); (2) T_cancel start value (10 pts seeded); (3) slippage/commission model (1 tick entry, 2 ticks stop, 4x news, $2.50/side seeded); (4) §9 sizing thresholds — oversized stop / late-window / thin target; (5) W2 window exact boundaries; (6) §2 data-level window: post-release [t, t+N) implemented vs symmetric ±N reading; (7) news_calendar.csv seed dates are UNVERIFIED estimates — verify against a real calendar before step 8; plus the four PNL Points quirks and the two reference-chart readings from the previous session
- Next session starts at: parity report generation once data/raw/ is populated; Steps 5–9 GATED on Angus sign-off

### 2026-07-16 — Repo initialization (Claude Code, remote session)
- Steps completed: repo created; full context pack committed (context/, strategy-definition-v1.0.md, spec-1); Angus's 28-trade hand log committed at data/reference/feb2026_hand_log.csv (as-is, per reported-not-fixed)
- Checks passed: all 28 reference trades present; hand-log P&L $ / R Multiple / Risk $ columns cross-check internally
- Divergences/flags raised: PNL Points column quirks in hand log, pending Angus confirmation — Feb 10 logged +11 pts on a −$220 loss (should be −11); Feb 18 09:42 logged 0 pts on −$400 stop (should be −20); Feb 19 logged 0 pts on −$150 discretionary close; Feb 27 09:40 logged 0 pts on −$324 stop (should be −27). Also noted: Feb 2 "BE stopped" means the hand sample already includes BE management (relevant to V0-vs-V1 tournament framing); Feb 19 discretionary close will never be matched by a mechanical exit (expected calibration divergence, not a bug)
- Questions parked for Angus: confirm the four PNL Points quirks above; provide reference-chart values (BB basis, daily VWAP ±1σ, NY VWAP, daily POC) for Feb 11 09:48 ET and Feb 17 09:50 ET for the Step 4 parity gate; formally confirm strategy-definition-v1.0.md final read-through (status line says "LOCKED pending final read-through")
- Next session starts at: Spec 1, Step 1 (repo scaffold)

### YYYY-MM-DD — (template)
- Steps completed:
- Checks passed:
- Divergences/flags raised:
- Questions parked for Angus:
- Next session starts at:
