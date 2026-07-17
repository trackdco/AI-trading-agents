# Progress Tracker

Update at the END of every Claude Code session. This file is how sessions hand off to each other and how Angus audits without reading code.

## Current state

- **Active phase:** 1 — Market Engine & Backtester
- **Active spec:** spec-1-market-engine-backtester.md
- **Last completed step:** Spec 1, Step 1 (repo scaffold) — check passed, committed
- **Blocked on:** Databento data download (blocks Steps 2+ on real data; Steps 2–3 checks run on fixtures); Angus's reference-chart values for the Step 4 parity gate (Feb 11 09:48 ET, Feb 17 09:50 ET)
- **Next action:** Spec 1, Step 2 (data ingest) — after human confirmation of Step 1 per workflow rules

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

### 2026-07-17 — News calendar extended Mar–Jul 2026 (Claude Code, remote session, Brake driving)
- Work done: parsed three Forex Factory calendar PDF exports Angus provided (Mar 1–May 2, May 2–Jul 3, Jul 3–present) into config/news_calendar.csv. Added 219 rows (2026-03-02 → 2026-07-17); file now holds 236 total (Feb seed kept as-is). Committed the reproducible extractor at scripts/extract_news_calendar.py.
- Data-quality issues caught and handled (these would have silently corrupted the backtest): (1) exports are in **Australia/Melbourne (GMT+10)**, not ET — every timestamp converted to America/New_York with zoneinfo (DST-aware; exports straddle the Apr 5 AU DST change), verified against known ET release times (NFP/CPI 8:30, ISM 10:00); (2) impact colour lives only in the PDF folder-icon graphics — read from rendered pixels (red→high, orange→medium, grey→holiday); (3) the two PDFs overlap on May 2 and Jul 3 — deduped; (4) fixed a July-page layout quirk that leaked the Actual value into event names; (5) US market holidays validated to the known set (Memorial Day May 25, Juneteenth Jun 19, Jul 3 obs); (6) AHE / Unemployment Rate snapped to travel with the payrolls print (correctly Thu Jul 2 that week, since Jul 3 is the holiday).
- Checks passed: 236 rows parse; columns intact; ruff clean on scripts/; committed script reproduces the committed rows byte-for-byte; 0 weekday violations on recurring releases (NFP=Fri, Claims=Thu) except the legitimate Jul-2 holiday shift.
- Flags for Angus (also in the news_calendar.csv header): confirm impact ratings match how we want news days classified; decide whether non-data rows (Trump/Fed speeches, DST shift, OPEC) should be ignored by the engine (Phase 2); dates around the Apr 5 AU DST change + holiday weeks are the least certain (recurring releases were weekday-validated, others worth a spot-check); all-day/tentative rows carry a 00:00 placeholder time. New TODO: extend calendar past 2026-07-17 before backtesting beyond that date.
- Note: input PDFs are NOT committed (gitignored under data/reference/news_pdfs/); Pillow used dev-only for pixel colour reading (not an engine runtime dependency).
- Next action unchanged: Spec 1, Step 2 (data ingest).

### 2026-07-16 — Spec 1 Step 1: repo scaffold (Claude Code, remote session, Brake driving)
- Steps completed: Step 1 — README.md, config/strategy.yaml (76 leaf parameters, all §-traced), config/news_calendar.csv (17 Feb 2026 seed rows), src/engine/, src/backtest/, tests/, data/raw/, output/, .gitignore (data/raw/ + output/ + .env ignored)
- Checks passed: repo tree matches Step 1 list; strategy.yaml parses via PyYAML; automated scan confirms every parameter line carries a §/spec-1 trace comment; news_calendar.csv parses with expected columns
- Divergences/flags raised — PLACEHOLDER values in strategy.yaml (doc names the parameter but gives no start value; all marked PLACEHOLDER in-file): T_cancel start value (§5.5, set 15.0 pts); session box times (§2, standard Asia 18:00–03:00 / London 03:00–09:30 / NY 09:30–16:00 used); W2 "full trading day" scope read as full CME session 18:00→15:55 (§1); volume-profile value-area % (set 70, industry standard); slippage S_normal=1 / S_news=4 ticks, N_news=15 min, commission $2.50/side (spec-1 §3, engineering placeholders). News calendar seeded from the hand log's News detail column because the reference journals are not in the repo — times use the log where stated, standard release times otherwise; impact ratings best-effort. `.env.example` flagged in next-tasks.md (required by code-standards, not named in Step 1) rather than silently added.
- Questions parked for Angus: confirm the PLACEHOLDER values above; prior session's four PNL Points quirks, Step 4 reference-chart values, and strategy-doc final read-through all still pending
- Next session starts at: Spec 1, Step 2 (data ingest) — Step 1 result shown to human for confirmation first

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
