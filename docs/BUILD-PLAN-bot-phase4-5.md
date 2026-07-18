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

## Stage 6 — Journaling 🔨
Every live decision + trade appended to a journal (reuse `src/desk/journal.py` schema) —
so live can be reconciled against backtest and audited. Same blob discipline as the replay.
- **Done-when:** a replayed day's journal matches the backtest trade log row-for-row.

## Stage 7 — PARITY CHECK 🔒 (live loop == backtest) — the gate before trusting paper
Run Stages 2–6 over several historical days via the replay feed and assert the Vault
produces the SAME trades, P&L, and journal as `simulate()` on those days. This proves the
live loop faithfully implements the champion. **Do not proceed to real-time paper until
parity is exact.**
- **Done-when:** N historical days reconcile to zero difference vs the backtest.

## Stage 8 — Live paper trading 👤🔨
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
