# Progress Tracker

Update at the END of every Claude Code session. This file is how sessions hand off to each other and how Angus audits without reading code.

## Current state

- **Active phase:** 1 — Market Engine & Backtester
- **Active spec:** spec-1-market-engine-backtester.md
- **Last completed step:** (none — awaiting setup tasks)
- **Blocked on:** Databento data download; repo initialization
- **Next action:** Spec 1, Step 1 (repo scaffold)

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

### YYYY-MM-DD — (template)
- Steps completed:
- Checks passed:
- Divergences/flags raised:
- Questions parked for Angus:
- Next session starts at:
