# Spec 1 — Market Engine & Backtester

## Section 0 — Context

**Product:** A mechanical NQ futures trading system. Claude agents will later grade setups; deterministic Python owns all risk and execution. This spec builds the foundation layer only: the Market Engine (data + indicators + mechanical setup detection) and the event-driven Backtester, sharing one codebase so backtest and live use identical eyes.

**Stack ground truth:** Python 3.11+, pandas + numpy, pydantic v2 for configs/schemas, PyYAML, pytest, ruff. No other heavy dependencies without flagging. All timestamps timezone-aware `America/New_York` (DST-aware — never hardcode UTC offsets).

**Authoritative reference:** `strategy-definition-v1.0.md` in the repo root. Every rule implemented here is defined there; when this spec and that document appear to conflict, STOP and flag — do not guess. Section references below (§) point to that document.

**Working rules:** Implement ONE step at a time. Verify each step's check before starting the next (per `code-standards.md`). Commit after every completed step with the step number in the commit message. Ask clarifying questions before writing code if any step is ambiguous.

## Section 1 — Goal

A backtester that replays 1-minute NQ history through the exact mechanical rules of strategy-definition-v1.0.md and outputs a trade log, per-slice diagnostics, and a calibration report comparing its February 2026 trades against Angus's 28 hand-logged reference trades.

## Section 2 — Out of Scope

- Do NOT build any Claude agents, subagents, or LLM calls of any kind. This layer is 100% deterministic.
- Do NOT build Telegram, alerting, or any live-data connection. Historical data only.
- Do NOT build the Monte Carlo simulator (Spec 4 territory).
- Do NOT build order execution, broker/prop integration, or the Vault's live loop.
- Do NOT implement any MIG LiquidityEdge reconstruction or absorption-zone detector.
- Do NOT add trade-management variants beyond V0–V4 as defined in §8.
- Do NOT optimize parameters in this spec — build the machinery that CAN be swept; sweeping happens under human direction later.

## Section 3 — Design Decisions

- Config-driven everything: every CALIBRATE parameter and TOURNAMENT variant in strategy-definition-v1.0.md lives in `config/strategy.yaml` with the doc's starting values. No magic numbers in code.
- No lookahead, structurally: signals are computed strictly on CLOSED candles; a signal on bar *t* may place a working limit order active from bar *t+1* onward. Write it so lookahead is impossible, not merely avoided.
- Fill realism: a resting limit fills only when price trades strictly through it by ≥1 tick (0.25). Targets use the front-run offset F (§6.4). Slippage: S_normal ticks per side, S_news ticks per side within N_news minutes of a scheduled release; commissions per contract per side. All in config.
- VWAP bands = volume-weighted standard deviation of price around VWAP (TradingView formula), NOT simple stdev. Daily VWAP anchors 18:00 ET (CME daily session open). NY VWAP anchors 09:30 ET and DOES NOT EXIST before then — pre-9:30 cluster logic uses daily VWAP only (§2, §3).
- Volume profile from 1-minute bars (volume distributed across each bar's range) — approximate vs tick data; acceptable and documented. Daily + NY-session profiles required; weekly profile behind a config flag.
- Contract roll: use Databento's continuous NQ (volume-based roll) unspliced; tag roll dates in the data and exclude no days by default, but surface roll days in diagnostics.
- Entry TFs 1m/2m/3m/5m are resampled from the 1m base. MTF arbitration: highest TF wins on simultaneous triggers (§1).
- Output artifacts are files, not printouts: `output/trades.csv` (strict schema mirroring Angus's log columns + engine fields), `output/diagnostics.csv` (per-slice expectancy per §12.5), `output/equity.csv`, `output/calibration_report.md`.
- News calendar is an input file, not an API: `config/news_calendar.csv` (datetime_ET, event, impact). Seed February 2026 from the reference journals; leave the rest of 2026 as a marked TODO for Angus/Brakey/Pat to fill from an economic calendar export.

## Section 4 — Implementation (ordered, independently verifiable)

**Step 1 — Repo scaffold.** Create: `README.md`, `strategy-definition-v1.0.md` (copy in), `config/strategy.yaml` (all §-referenced parameters with starting values, commented with their § source), `config/news_calendar.csv` (header + Feb 2026 seed rows), `src/engine/`, `src/backtest/`, `tests/`, `data/raw/`, `data/reference/`, `output/`, `.gitignore` (ignore `data/raw/` and `output/`). Place Angus's 28-trade CSV at `data/reference/feb2026_hand_log.csv`.
*Check: repo tree matches; `strategy.yaml` parses; every parameter carries a § comment.*

**Step 2 — Data ingest.** `src/engine/data.py`: load Databento 1-minute NQ (DBN or CSV) → validated parquet at `data/nq_1m.parquet` with columns ts_event(NY tz), open, high, low, close, volume. Validation: monotonic timestamps, no duplicates, gap report (missing minutes per session), roll-date tags.
*Check: `pytest tests/test_data.py` passes on a bundled 2-day fixture; gap report generated for full dataset.*

**Step 3 — Resampler + sessions.** `src/engine/sessions.py`: 1m→2m/3m/5m/15m resampling (right-closed, label=close time); session classifier (Asia/London/NY per §2 boxes); running session extremes; prior-day/weekly H/L; data-level extractor (extremes within N_data minutes of calendar events).
*Check: unit tests with hand-computed fixtures for a known day, including a DST boundary date.*

**Step 4 — Indicators.** `src/engine/indicators.py`: BB(20, SMA, close, 2σ) per entry TF; daily VWAP (18:00 anchor) ±1/2/3σ; NY VWAP (09:30 anchor) ±1/2/3σ returning NaN pre-anchor; daily + session volume profile (POC/VAH/VAL, HVN/LVN), weekly behind flag.
*Check — PARITY GATE, requires Angus:* **[AMENDED 2026-08-07 — A3]** for **2025-01-15 09:48 ET and 2025-01-22 09:50 ET**, computed BB basis, daily VWAP ±1σ, NY VWAP, and daily POC each within 1.0 NQ point of the values visible on the reference charts. Produce `output/parity_report.md` listing computed vs chart values. **Do not proceed past this step until Angus signs off on the parity report.**

> **Why these dates changed.** The original targets were Feb 11 2026 09:48 ET and Feb 17 2026 09:50 ET. The held bar data ends **2026-01-30** — February 2026 does not exist in it, so the original gate was pointed at data we do not have and was therefore permanently unclosable. The replacements are both full 1380-bar Globex sessions inside the workbench period, mid-week, not roll sessions, and recent enough that TradingView history is easy to retrieve. Same clock times as the originals so the indicators sit at the same session position.
>
> **This substitution is clean and like-for-like.** Parity tests whether our indicator maths reproduces a charting platform's, which any date with a chart can answer. **Angus must supply fresh reference-chart readings for the two new timestamps** — the old readings are for dates that are no longer being tested.

**Step 5 — Snapshot builder.** `src/engine/snapshot.py`: for any timestamp, emit one pydantic-validated JSON snapshot: all indicator values per TF, cluster detection per §3 (with pre-9:30 daily-VWAP-only rule), session context, HTF flag (15m trend/range via swing HH/HL–LH/LL classification — document the exact rule chosen), data levels, distances to every target-menu level.
*Check: golden-file test — snapshot for one known timestamp matches a reviewed fixture exactly.*

**Step 6 — Trigger detection.** `src/engine/triggers.py`: rejection block (§3: trades into cluster, closes back on trade side of ALL cluster levels, wick zone recorded) and displacement (§3: body closes through ≥2 cluster levels, body/range ≥ B_min, close in extreme quartile, optional ATR floor), per entry TF; pattern classification A/B/B2 per §4 with HTF flag; MTF arbitration.
*Check:* **[AMENDED 2026-08-07 — A3]** run over **2025-01-06 → 2025-01-31**; emit `output/triggers_sample.csv`; verify triggers fire at a plausible rate and that none is timestamped before 09:36. The original check spot-verified triggers at four February 2026 reference timestamps; those bars are not in the held data, so no reference-trade spot-check is possible. This is a rate-and-boundary check only.

**Step 7 — Backtester core.** `src/backtest/engine.py`: event loop over closed 1m bars; working limit orders per §5 (entry variants E1/E2/E3 as config), stop per §5.4, target tree per §6 incl. news-day override and front-run F, cancel rule T_cancel, one-position-at-a-time, entry window W1/W2 config, management variants V0–V4 (§8), Vault constraints (max trades/day, daily halt, EOD flatten per §10), slippage + commissions. Outputs trades/diagnostics/equity files.
*Check: `pytest tests/test_backtest.py` — includes an explicit no-lookahead test (perturbing future bars must not change past signals) and a fill-logic test with hand-built bar sequences.*

**Step 8 — Behavioural sanity report.** **[AMENDED 2026-08-07 — A3. This step is DOWNGRADED, not relocated. Read the note before executing it.]** `src/backtest/calibrate.py`: run **2025-01-06 → 2025-01-31** (19 workbench sessions) with **RTH/E1/V0** defaults; emit `output/behaviour_report.md` covering: trades taken per session, entry-time distribution within the session, realised stop and target distances, pattern mix (A/B/B2), and the rate at which triggers are rejected by each gate. No tuning in this step: report honestly and stop.
*Check: report generated; realised trade frequency stated as the first line (it is a gate-6 input — see below).*

> **What was lost, stated plainly.** The original Step 8 matched engine output against Angus's 28 hand trades on (date, direction, entry time ±15 min), classifying every one as MATCHED / MISSED / EXTRA. That is the strongest validation in the whole build: it measures both detector fidelity *and* day-selection honesty against a human ground truth.
>
> **It cannot be run.** The 28 trades occurred in February 2026 and the held bar data ends 2026-01-30. Unlike the parity gate, this is **not** relocatable — the ground truth is welded to those specific dates. Moving the window to January 2025 gives us no reference trades to match against, so MATCHED/MISSED/EXTRA is undefined there.
>
> **The replacement is weaker and should not be described as calibration.** It answers "does the engine behave plausibly and at a sane rate?" — not "does the engine reproduce Angus?". Passing it is necessary, not sufficient, and it must not be presented to Angus as though the original gate had been cleared.
>
> **This is the one irrecoverable loss from the coverage shortfall.** Recorded here so it is not quietly forgotten when the sign-off ledger is reviewed.

**Step 9 — Diagnostics slices.** Extend outputs with per-slice expectancy tables (§12.5): pattern × TF × confluence count × HTF flag × time bucket × news flag; plus roll-day and gap-day flags.
*Check: `output/diagnostics.csv` populated from the Step 8 run; slices sum consistently to the headline totals.*

## Section 5 — Check When Done

- [ ] All steps committed individually; repo history shows one commit per step minimum
- [ ] `ruff check .` and `pytest` pass clean; no unflagged new dependencies
- [ ] Parity report (Step 4) signed off by Angus BEFORE Steps 5–9 were built
- [ ] No-lookahead test exists and passes
- [ ] NY VWAP returns no values before 09:30 ET; pre-market clusters use daily VWAP only (test proves it)
- [ ] Every parameter in `config/strategy.yaml` traces to a § in strategy-definition-v1.0.md via comment
- [ ] Behavioural sanity report generated over 2025-01-06 → 2025-01-31, realised trade frequency stated on line 1 **[AMENDED — A3; the original MATCHED/MISSED/EXTRA calibration against the 28 reference trades is NOT achievable on held data, see Step 8]**
- [ ] No parameter tuning, no optimization, no rule changes were made to improve the calibration numbers — divergences are REPORTED, not fixed
- [ ] No new components beyond the files named in Section 4 without flagging first
