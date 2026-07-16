# Next Tasks

Ordered. Do not start a task before its predecessor's gate clears.

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
