# Progress Tracker

Update at the END of every Claude Code session. This file is how sessions hand off to each other and how Angus audits without reading code.

## Current state

- **Active phase:** 1 — Market Engine & Backtester
- **Active spec:** spec-1-market-engine-backtester.md
- **Last completed step:** (none — setup nearly done; repo initialized, hand log committed)
- **Blocked on:** Databento data download (blocks Steps 2+ on real data; Steps 1–3 checks run on fixtures); Angus's reference-chart values for the Step 4 parity gate (Feb 11 09:48 ET, Feb 17 09:50 ET)
- **Next action:** Spec 1, Step 1 (repo scaffold) — can start immediately

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

### 2026-08-05 — Strategy intake pipeline + YouTube MCP (Claude Code, remote session)
- Steps completed: built `tools/youtube-mcp/` (9 tools: search, transcript fetch/cache, regex over cached corpus, sweep, dossier scaffold) registered in `.mcp.json`; wrote `context/strategy-research-protocol.md`, `context/validation-gate-v1.md`, `context/quant-in-plain-english.md`, `context/data-inventory.md`; scaffolded `strategies/` with `_TEMPLATE/`, `BOOK.md`, `GRAVEYARD.md`; added `tools/audit_data.py`, `.gitignore`, `.env.example`
- Checks passed: MCP server completes a stdio handshake and lists 9 tools; cache/grep/sweep-scope/dossier paths exercised against fixtures; missing-API-key path returns an actionable error; `tools/audit_data.py` reproduces the inventory tables from the actual files
- Divergences/flags raised — **all four block work already scheduled**:
  1. **No CVD data exists.** The 510 MBP-10 files are depth-only snapshots (1/minute): 29,574 adds, 22,212 cancels, 15,630 modifies, **3 trades**. Heatmap yes, CVD no.
  2. **No bars after 2026-01-30.** The Feb 2026 calibration gate cannot run — no bars for the month the 28 hand trades come from.
  3. **No 2023/24 book or flow data**, so flow-based strategies cannot be tested out-of-sample as designed. Three options in `data-inventory.md` §4.
  4. **~10% of bar rows are calendar spreads** (`NQH6-NQM6` etc.) priced 106–840 alongside outrights at 10,000+. Ingest must filter them or every indicator is silently wrong.
  Also: London book is `NQ.v.0` in decimal prices, NY book is `NQ.c.0` scaled ×1e9 — different roll convention and different price scaling between the two sets. NY book has a 51-weekday hole (2025-11-21 → 2026-01-30). No gold data at all.
- Questions parked for Angus: does the strategy-validation framework / correlation baseline referred to in chat exist as code anywhere? It is not in this repo or the other branch — both branches are identical and contain no source code. Also: data budget for the gaps above, and confirmation of the gate thresholds in `validation-gate-v1.md` before the first strategy runs against them.
- Next session starts at: install the MCP locally, then first candidate strategy through protocol Stages 0–3

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
