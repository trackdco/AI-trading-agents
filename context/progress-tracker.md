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

### 2026-07-20 — First-pass engine + full-period smoke backtest (Claude Code, remote)
- Steps completed (UNVALIDATED — jumped the gates deliberately, at Pat's request, to get a first read): Step 1 scaffold, Step 2 data ingest (per-day front-month stitching → 1,089,712 1m bars, Jan 2023–Jan 30 2026), Step 3 resampler/sessions (partial), Step 4 indicators (BB, developing daily+NY VWAP bands, developing POC — NOT parity-checked), Step 6 rejection-block detection (vectorized, TYPE-group confluence), Step 7 backtester (E1/V0/W1 defaults, Vault limits, slippage+commission). Config in config/strategy.yaml with documented starting values only — NO tuning.
- Results (first-pass, pre-parity, pre-calibration): 1,920 trades, win rate 34.1%, expectancy +0.012R/trade, PF 1.01, net +22.4R over 3yr, maxDD −106R. Year: 2023 −72R / 2024 +102R / 2025 −30R / 2026 +23R. → NO demonstrable mechanical edge in the naive translation.
- Divergences/flags raised: (1) HUGE gap vs hand log (71%WR/+2.8R) → detector too loose, fires ~2/day every day vs Angus's selective day-picking; his edge is largely in setup/day SELECTION which the mechanical version lacks. (2) Slice signal: 5m (+99R), shorts (+103R), with-trend (+137R), downtrend-HTF (+149R) carry all P&L — hypothesis for Angus, NOT tuned in. (3) Artifact: tiny-wick triggers give tiny risk → fixed slippage/commission blows R to −2.6/−4R, inflating avg loss to −1.38R; also stop-first same-bar assumption. Needs fixing before any real read. (4) Entry/target/pattern logic simplified; HTF flag uses SMA20-slope rule (documented in code).
- BLOCKERS: (a) Feb-2026 data NOT in dataset (ends 2026-01-30) → Step 8 calibration vs the 28 hand trades IMPOSSIBLE until Feb is pulled from Databento. (b) Step 4 parity gate still needs Angus's Feb 11 09:48 / Feb 17 09:50 reference values — indicators unverified.
- Questions parked for Angus: same 4 PNL-points quirks as prior session; parity-chart values; confirm whether to pull Feb 2026 (and ideally Feb–Jul) data next.
- Next session starts at: fix loss artifacts (min-risk floor, same-bar resolution), then either (i) pull Feb data + run real calibration, or (ii) build the parity harness for the Step 4 gate.

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
