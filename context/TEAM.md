# Team & Branch Coordination — READ FIRST

**If you are a Claude session opening this repo: switch to the canonical branch below and
read `context/progress-tracker.md` before doing anything. Do NOT start a new branch, and do
NOT rebuild the Market Engine — it already exists.**

## Canonical branch

**`claude/getting-started-6lwnvs`** is the single source of truth. It has Spec 1 Steps 1–4
built and tested, the real Databento data loaded, and the parity slice committed. Three
sessions independently built this engine on separate branches (`session-setup-lzzfzm`,
`tradingview-nq-readings-0rnr1l`, `ai-trading-agents-repo-r64muf`); those are **superseded** —
all useful work from them has been salvaged onto the canonical branch. Everyone works here now.

Git rules (keep it simple):
1. `git fetch origin && git checkout claude/getting-started-6lwnvs && git pull` before starting.
2. Push when you finish a step. Read `context/progress-tracker.md` first — it's the shared ledger.
3. **One engine-driver at a time** on `src/engine/` and `src/backtest/`. Don't build the same
   thing twice.
4. When a new Claude session spins up, its first action is to switch to this branch.

## ⚠️ BRAKE: DATA PULL WAITING (18 Jul, from Angus)

**Read `docs/TASK-FOR-BRAKE-orderbook-data.md`** — Angus has committed to order-book data
(Databento `trades` tick schema first; `mbp-10` if budget allows) to build the
absorption/exhaustion heat-map confluence (his MIG replacement). Feb–Mar first for cheap
validation against his hand logs.

## ⚠️ SUPERSEDED (18 Jul assignment → 24 Jul canon ruling)

**The LLM regime-context *gate* is retired.** The 18 Jul brief
(`docs/TASK-FOR-PAT-regime-agent.md`) directed a regime-context agent that *reads
macro/war/narrative context and gates the engine's bias/structure/size* — i.e. an LLM in the
trade path. Angus's authoritative canon ruling of **24 Jul** overrides it
(`docs/FOR-ANGUS-desk-spec-questions.md:262-267`): *"the strategy is now THE CANON … frozen
deterministic code … **There is no LLM judgment anywhere in the trade path.** Agent
intervention risks degrading performance (proven three times)."* So **no agent gates the
engine.** The only "regime" left on the live path is the deterministic pre-open E3/E4 switch
computed from bars (`src/live/vector.py::LiveVectorPolicy`), and the desk agents route /
relay / journal only (`docs/desk-skills/canon/*`). The old brief is kept for provenance but
is **not an active assignment**.

## Who does what

| Person | Owns | Touches (parallel-safe lanes) |
|---|---|---|
| **Angus** | Strategy authority + sign-offs | `strategy-definition-v1.2.md`, chart readings, gate approvals, answering "what number did you mean". |
| **Brake + Angus** | Data + running simulations to find leaks, then refine strategy/risk metrics before finalizing | data pulls, `config/`, `output/` reports, calibration/diagnostics review. |
| **Pat** | Builds the **agents** (Phase 3: atlas/helios/apollo/hephaestus/hermes in `.claude/agents/`) and the **bots** (Phase 4–5: Vault live loop, Telegram, paper trading) | `.claude/agents/`, live-loop code — comes AFTER the engine + calibration are validated. |
| **Claude Code (this branch)** | Builds the deterministic **Market Engine + Backtester** (Spec 1), one step at a time, flags anything questionable | `src/engine/`, `src/backtest/`, `tests/`. |

The engine steps are a **chain** (Step N needs N−1), so two people can't both "build the engine"
without colliding — that is the mistake that created the branch sprawl. Parallelism here is by
**role/files**: Angus in the strategy doc + chart reads, Claude Code in the engine, Brake on data —
those don't conflict.

## Current status (2026-07-17)

- **Done:** Spec 1 Steps 1–3 (data ingest → continuous NQ, resampler + sessions). Step 4
  (indicators) built and green; a final adversarial verification pass is confirming the VWAP /
  volume-profile formulas before the parity numbers are treated as final.
- **Blocked on:** the **Step 4 parity gate** — Angus's chart readings for Feb 11 09:48 ET and
  Feb 17 09:50 ET (see `data/reference/parity_chart_settings.md` and `output/parity_report.md`).
- **⚠️ Parity instrument fix (from `parity_chart_settings.md`):** read the chart on the dated
  front-month **NQH2026 (March 2026 NQ)** — NOT `MNQ1!` and NOT a back-adjusted `1!` continuous.
  The engine uses unspliced continuous NQ, which for Feb 11/17 IS NQH6 (verified). Back-adjustment
  and micro-volume would otherwise shift prices/VWAP/POC by tens of points and blow the 1-pt gate.
- **Next after sign-off:** Steps 5–9 (snapshot → triggers → backtester → calibration → diagnostics).
