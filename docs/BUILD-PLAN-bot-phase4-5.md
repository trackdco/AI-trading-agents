# Bot build plan — Phase 4–5 (live paper-trading on the champion)

The complete, ordered build to turn the finished engine + frozen champion into a live
paper-trading bot. Each stage has a **Done-when** checkpoint so nothing is skipped. The
agent/refined-strategy plugs in later at the seam that already exists (Stage 9); nothing
here waits on Angus.

Legend: ✅ already built · 🔨 to build · 👤 your action (outside code) · 🔒 safety-critical

---

## Stage 0 — Foundations (verify what's already done)
- ✅ Engine: `src/engine/` (data, indicators, sessions, triggers, snapshot) — reads NQ
  bars, computes VWAP/bands/POC/ATR, detects triggers.
- ✅ Champion decision logic: `src/backtest/engine.py` `simulate()` + `config/strategy.yaml`
  (Blend v1.1: E3/E4 book switch, window 08:00–10:15, max 2 trades/day, cuts C1/C2/C3).
- ✅ Swap seam: `simulate(day_gate=None)` = pure champion; agent plugs in later here.
- 👤 Fill `.env` (copy from `.env.example`): `DATABENTO_API_KEY`, `TELEGRAM_BOT_TOKEN`,
  `TELEGRAM_CHAT_ID` (-5356314891), `TELEGRAM_ANGUS_USER_ID`.
- 👤🔒 Regenerate the Telegram token via @BotFather `/revoke` (the old one leaked in a
  screenshot) and put the fresh one in `.env`.
- **Done-when:** `.env` filled, backtest still runs green (`pytest`), token regenerated.

## Stage 1 — Live data feed 🔨
Turn a real-time NQ source into the SAME 1-minute continuous front-month bars the engine
expects (columns `ts_event, open, high, low, close, volume`, 18:00-ET session boundary).
- Choose source: Databento **live** (matches our historical vendor — cleanest) 👤 needs
  the live subscription.
- Build `src/live/feed.py`: subscribe → assemble closed 1-min bars → apply the same
  continuous-front-month + timezone logic as `src/engine/data.py` (reuse `to_continuous_
  front_month`, `load_strategy_timezone`). Emit one event per **closed** bar.
- Build a **replay feed** too: stream historical parquet bars as if live (for testing
  Stages 2–7 without a live subscription).
- **Done-when:** the live feed and the replay feed both emit bars identical in shape to
  the backtest input; a replayed day reproduces the historical bar stream exactly.

## Stage 2 — The Vault: streaming champion loop 🔨 (the heart)
`simulate()` is batch (whole day at once); live must decide **bar-by-bar**. Build
`src/live/vault.py` that, on each closed bar, reuses the EXACT champion rules:
- update rolling indicators; run `detect_triggers` on the rolling window;
- apply champion entry rules (confluence, session window, the pre-open E3/E4 imbal switch,
  max 2 trades/day); manage open positions (stop, target, the C1/C2/C3 cuts, flat-by-
  window-end);
- hold the `day_gate` hook (default None = champion; agent later).
- Maintain state: open position, trades-today, daily reset at the session boundary.
- **Done-when:** given the replay feed, the Vault emits the same entries/exits as the
  backtest for that day (proven in Stage 7).

## Stage 3 — Paper broker 🔨
`src/live/paper_broker.py`: accepts the Vault's orders, simulates fills (at bar close or
next-bar open — match the backtest's fill assumption), tracks position + realized/unrealized
P&L in **points AND dollars** (kept separate, per the units rule). No real orders.
- **Done-when:** a replayed day's paper P&L matches the backtest's P&L for that day.

## Stage 4 — Risk guards 🔒🔨 (the Vault gate — before any order or alert)
`src/live/risk.py`, checked on every intended action:
- daily loss limit (hard stop for the day); max trades/day (already 2 in config);
- max position size / one-position-at-a-time; session-window enforcement (no entries
  outside 08:00–10:15; flat by end); a manual **kill-switch** (file/flag the Vault reads).
- **Done-when:** each guard is unit-tested to block the action it's meant to block; a
  simulated breach halts trading for the day and alerts.

## Stage 5 — Telegram alerts 🔨
`src/live/telegram.py` — the ONLY module importing the Telegram client (architecture
boundary: alerts fire from the Vault, after the risk check; no agent touches Telegram).
- Send: session start, setup/trigger, entry (price, size, book), exit (reason, P&L),
  daily summary, and any risk-halt.
- Optional inbound command lock to `TELEGRAM_ANGUS_USER_ID` (status / pause / kill).
- **Done-when:** a replayed day fires the full alert sequence into the group correctly.

## Stage 6 — Journaling ✅ (19 Jul)
Every live decision + trade appended to a journal (reuse `src/desk/journal.py` schema) —
so live can be reconciled against backtest and audited. Same blob discipline as the replay.
- **Done-when:** a replayed day's journal matches the backtest trade log row-for-row.
- Built: `src/live/journal.py` — `LiveJournal` writes `journal.jsonl` (frozen-schema
  `JournalRecord` per completed trade, lifted from the engine's FULL `TradeRecord` via a
  new `Vault.add_record_sink`, with `config_hash` + `playbook`) and `decisions.jsonl`
  (session book picks via `wrap_policy`, risk halts, notes). Restart-safe dedup,
  fail-soft writes. `scripts/parity_check.py` now also asserts journal==batch
  row-for-row; both standing windows (Feb 9–13, Mar 16–20) re-passed after the Vault
  change. 261 tests green.

## Stage 7 — PARITY CHECK 🔒✅ (19 Jul) (live loop == backtest)
Run Stages 2–6 over several historical days via the replay feed and assert the Vault
produces the SAME trades, P&L, and journal as `simulate()` on those days. This proves the
live loop faithfully implements the champion. **Do not proceed to real-time paper until
parity is exact.**
- **Done-when:** N historical days reconcile to zero difference vs the backtest.
- Closed on 40 days: Feb 9–13 (7 trades), Mar 16–20 (8), and ALL of April (30) —
  trades, P&L, and journal reconcile to zero difference. `scripts/parity_check.py`
  remains the standing gate: re-run after ANY Vault/champion/engine change.

## Stage 8 — Live paper trading 👤🔨 (in progress 19 Jul)
Live-input groundwork DONE and gated (the two things caches/CSVs provided until now):
- `src/live/detector.py` streams the REAL `detect_triggers` per closed bar
  (07:45–11:00 band, 10-min tail, ~0.8s/bar) — `scripts/detector_parity.py` matches
  the frozen cache trigger-for-trigger.
- `src/live/vector.py` computes the E3/E4 switch from bars; decides at the first
  ≥08:00 bar via the Vault's new PENDING sentinel (the switch provably uses the
  day's own overnight) — `scripts/vector_parity.py` matches `book_for_day` on all
  113 reference days.

The assembled runner is DONE: `src/live/runner.py` (`LiveRunner`) wires
feed → detector → Vault(live vector policy) → risk guard → broker → journal →
Telegram, with the correct startup order (restore broker → seed guard → seed
Vault's emitted-set so a restart re-fires nothing), the strategy-swap seam
(`strategy_gate` composes UNDER the risk guard — champion untouched when None), a
daily heartbeat summary (incl. 0-trade days), and `prime()` to preload warmup
history for a feed that starts at "now". 9 unit tests cover trade fan-out, the
crash-restart-with-no-duplicate-alerts drill, the kill switch, and the seam.

`scripts/runner_drill.py` — the strongest proof in the build — streams real bars
through the WHOLE assembled runner computing its OWN triggers and OWN book pick
(no pre-loaded caches/CSV), diffs against the batch backtest, and runs a restart
leg. **PASSED** on Mar 17 (2/2 trades, restart byte-identical, 0 duplicate
alerts) and the full Mar 16–20 week. A performance bug was found and fixed along
the way (see below) — the drill only became practical after the fix.

**Perf fix (found via the drill, not a review — worth recording):** the Vault
retries a PENDING session policy every bar of the ~14h overnight window (by
design — a late book pick is still safe). `LiveVectorPolicy.__call__` was
pulling the full accumulated-history frame on every one of those ~840 retries/
day, against a live runner's growing 16–20 day buffer — profiling showed
per-bar cost climbing (6.5ms → 17.5ms and rising) as history grew. Fixed with
`LiveVectorPolicy.note_bar(ts)`: an O(1) hook the runner calls every bar to
track only the latest bar seen per session day, so the expensive frame is
touched at most once/day, exactly when a real decision is made. 7 new unit
tests lock the call-count contract. A 16-day warmup leg went from
minutes-and-climbing to **44.6s flat (2.87ms/bar, constant)** — confirmed via
direct profiling, with the vector gate re-run afterward (still 113/113 match —
correctness unaffected).

Remaining: the live Databento feed (needs Pat's vendor decision + API key) —
the only piece left before real-time paper trading can start.
Point the Vault at the **live** feed in paper mode; run through real sessions. Watch via
Telegram; reconcile each day's paper results against what the backtest would have done on
the same bars.
- **Done-when:** a stretch of live sessions runs unattended, alerts fire, paper P&L is
  sane and matches a same-bars backtest.

## Stage 9 — Swap seam + go-live gate (mostly ✅)
- ✅ The seam: when Angus's refined strategy/agent is ready, pass it as `day_gate` — zero
  Vault rebuild; re-run Stages 7–8 on paper to validate the new version.
- 🔒 **Go-live gate (real money):** ONLY after the strategy is validated across regimes
  (the champion alone lost money 2023–25) AND paper trading is clean. Until then, paper only.

---

## Ownership
- **You (Pat):** drive the build, provide the Databento live key + regenerated Telegram
  token, run the paper sessions, make the go-live call.
- **Claude Code (me):** write the code for Stages 1–7 with you; wire Telegram; build the
  parity harness.
- **Angus:** refine the strategy for cross-regime robustness (plugs in at Stage 9).
- **Brake:** the data feeding Angus's refinement.

## Decisions you'll need to make (flagged early)
1. Live data vendor: Databento live (recommended — matches our historical data) vs a
   broker-native feed.
2. Eventual live execution broker (a futures broker with an API) — not needed for paper,
   but pick before go-live so the paper_broker interface matches it.
3. Where the bot runs (your machine vs a small always-on cloud box) for unattended sessions.

## Suggested build order (fastest path to a watchable paper bot)
Stage 0 → 1 (replay feed first) → 2 → 3 → 7 (parity) → 5 (Telegram) → 4 (risk) → 6
→ 1 (live feed) → 8. Parity (7) before Telegram so you're not alerting on a wrong loop.
