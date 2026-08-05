# Next Tasks

Ordered. Do not start a task before its predecessor's gate clears.

## BLOCKING — data gaps found in the 2026-08-05 audit

Full detail in `context/data-inventory.md`. These block work already scheduled
below, so they come first.

- [ ] **NQ 1-minute bars, 2026-02-01 → present.** Coverage currently stops at
      2026-01-30. This blocks the Spec 1 Step 8 calibration gate (the 28 hand
      trades are February 2026 — we have no bars for the month we calibrate
      against) and half the strategy-intake in-sample window.
- [ ] **NQ `trades` schema, session windows, 2025-06 → present.** There is no
      CVD data in this repo — the MBP-10 files are depth snapshots (3 trade
      records across all 510 files). Blocks every order-flow refinement step.
- [ ] **Decide the 2023/24 out-of-sample approach** (buy book+flow for 6 months,
      or split the OOS design — `data-inventory.md` §4). Blocks Stage 7 for any
      flow-based strategy.
- [ ] NQ MBP-10, NY session, 2025-11-21 → 2026-01-30 — fills a 51-weekday hole.
- [ ] GC/MGC data — the entire Asia-session track is blocked on this.
- [ ] Ingest must filter calendar spreads (`"-" in symbol`) — ~10% of bar rows
      are spread instruments priced 106–840 sitting next to outrights at 10,000+.

## Strategy intake pipeline (new track, runs alongside Phase 1)

- [ ] Install the YouTube MCP: `cd tools/youtube-mcp && uv venv --python 3.11 .venv && uv pip install --python .venv/bin/python -e .`
- [ ] Get a YouTube Data API v3 key → `.env`
- [ ] First candidate strategy through `context/strategy-research-protocol.md`
      Stages 0–3 (research + mechanism + spec — no compute needed, and it
      exercises the pipeline before the harness exists)
- [ ] **Spec 2: the validation harness** — substrate generation, slice reports,
      refinement metrics, correlation matrix. Write after the first strategy has
      been through Stage 3, so the harness is built against a real example
      rather than an imagined one.

## Setup (Angus, ~1 hour)
- [ ] Databento account created; NQ 1-minute data Jan 2026 → present purchased and downloaded to `data/raw/`
- [ ] Repo created from this file pack; Angus's 28-trade CSV placed at `data/reference/feb2026_hand_log.csv`
- [ ] Claude subscription confirmed adequate for Claude Code usage (Max tier recommended)
- [ ] Telegram bot created via @BotFather; token + Angus chat ID stored in `.env` (used Phase 4, cheap to do now)

## Phase 1 — Market Engine & Backtester (Pat/Brakey via Claude Code)
- [ ] Execute `spec-1-market-engine-backtester.md` steps 1–3
- [ ] **GATE: Step 4 parity report → Angus sign-off** (indicators vs Feb 11 + Feb 17 reference charts, within 1 pt)
- [ ] Execute steps 5–9
- [ ] **GATE: Step 8 calibration report → Angus classifies every MISSED and EXTRA trade** ("my setup, I missed it" vs "not my setup, detector too loose")

## Phase 2 — Calibration review (Angus + Claude chat)
- [ ] Bring calibration report + diagnostics back to Claude chat; tear-down session
- [ ] Output: Spec 2 (detector corrections and/or tournament runs), written by Claude, approved by Angus

## Phase 3 — The Desk (spec written after Phase 2)
- [ ] Spec 3: agent files (atlas/helios/apollo/hephaestus/hermes) + Hermes orchestration + Snapshot wiring

## Phase 4 — Vault live loop, Telegram, Monte Carlo (spec after Phase 3)
- [ ] Spec 4: Monte Carlo vs 50K eval rules (3K target / 2K trailing DD) → sizing config → firm shortlist
- [ ] Spec 5: live loop on VPS + Telegram alerts + /status /pause /flatten commands

## Phase 5 — Live conditions
- [ ] Paper via TradingView, agents grading real-time, Angus executing manually
- [ ] Buy sim/eval only after paper track record reviewed against backtest expectations

## Parked / flagged (do not build without promotion to a spec)
- Weekly volume profile variant (config-flagged, test in Phase 2 tournaments)
- H3 session expansion (London / full-day W2 results will inform)
- H4 news-buffer filter
- Native absorption/exhaustion zone detector (MIG replacement) — separate validated module, someday
