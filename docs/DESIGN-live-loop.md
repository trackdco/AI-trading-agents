# DESIGN — the live loop: always-on agents, instant placement (build: week of 2026-08-17)

His requirement, 2026-08-15: *"It takes 5 minutes to decide whether it wants
to take a trade — it's going to have to make that decision much quicker on
live. And live should have LLM calls and the agents constantly working, not
only when there's a trigger."*

## Why replay is slow, and why live isn't bound by it

Replay's latency is the price of measurement honesty. Every agent call is a
COLD START — fresh spawn, full contract re-read, one truncated moment —
because statelessness is the leak-proofing: an agent with memory of the day
could carry the future backward. **Live has no future to leak.** The
anti-leak scaffolding (cold starts, per-decision truncation, one-briefing-
one-call) is replay-only. Live keeps the DOCTRINE and the JOURNAL, and drops
the scaffolding.

## The three changes

### 1. The loop becomes a daemon, not a Claude session driving by hand

The replay orchestrator is a Claude session clicking a chart — fine for
replay, wrong for live. The live loop is a small SCRIPT: poll each 2m close,
maintain levels, evaluate armed conditions, place/modify/cancel orders (MCP
paper tools per docs/RESEARCH-mcp-paper-orders.md, later Tradovate demo),
route events to agents, write the journal. Milliseconds per tick, zero
discretion — §0c enforced by construction, because a script cannot
editorialise.

### 2. The agents become PERSISTENT sessions — his "constantly working"

One long-running session per agent role, contract loaded ONCE at start,
then fed a compact DELTA every 2m close: the new bar, changed levels, any
event flags (~200 tokens). The reply is either `no_change` (seconds,
near-free with prompt caching) or an updated JSON — thesis with armed
plans, or a management action.

- **tv-thesis, always on:** re-reads the tape every candle like he does.
  The thesis evolves in place; armed plans and the other_side_tripwire are
  standing output, not per-event ceremony. Tick cost: ~5–20s.
- **tv-trigger, confirm-or-cancel:** adjudicates candidates as deltas
  against its resident contract — no 750-line re-read — target < 60s.
- **tv-manage, per open position:** bar-by-bar deltas while a position is
  open; `hold` replies cost almost nothing. This is "how is the trade
  favouring me RIGHT NOW" made literal.

**Session hygiene (the new risk this creates):** a persistent session can
accumulate tilt — a morning of being wrong colouring the afternoon. Control:
rotate each session at window boundaries; the successor inherits ONLY the
written state (thesis JSON, open-position state, journal rows), never the
chatter. Same principle as the replay no-leak gate, pointed at mood instead
of time.

### 3. Decisions are PRE-ARMED — his own habit as architecture

> *"When I see something happen, I'm like: OK, if we close through these
> levels now, I'm gonna enter this trade. I don't wait for the trigger and
> then decide."*

The thesis's armed plans carry entry/stop/target pre-computed. When a close
matches an armed plan, the DAEMON places the limit immediately —
milliseconds, no LLM in the hot path. tv-trigger then confirms or cancels
WHILE THE LIMIT RESTS: limit-on-retest entries give a natural 2–10 minute
grace window between signal and fill, so a sub-minute adjudication rides
inside it. If the trigger votes pass, the order is pulled before it fills.
Unarmed candidates (a valid break matching no plan) keep adjudicate-first.

## Latency budget (target)

| step | replay today | live target |
|---|---|---|
| placement after signal close | minutes (agent-first) | **milliseconds** (armed plan, daemon) |
| trigger adjudication | ~5 min cold | **< 60s**, in parallel with the resting limit |
| thesis update | ~2 min per re-fire | **5–20s per candle**, continuous |
| management response | ~2 min per call | **bar-by-bar**, `hold` ≈ free |

## What does NOT change

- **The contracts are the doctrine.** Persistent sessions are bound by the
  same tv-* contracts, loaded at session start. No live-only rules.
- **The journal is the record.** Every armed plan, placement, confirmation,
  cancel, flip and management action logs exactly as in replay — the
  reasoning-first review survives the speed.
- **Replay remains the measuring instrument.** Scoring, regression weeks and
  teaching-loop work stay on the cold-start replay harness — its slowness is
  its honesty. Live-paper and replay are two harnesses over one doctrine.

## The bridge test, before any live session

Dress rehearsal: run one known day in replay at autoplay (~1000ms/bar) on
the PERSISTENT stack — the daemon consuming bars as if live, agents
resident — then diff its journal against the cold-start replay journal of
the same day. Same doctrine, two architectures: the decisions should match.
Where they diverge, the persistent stack has drift the rotation hygiene
missed, and that gets fixed before paper money moves.

## Build order (next week)

1. Daemon skeleton: bar feed → armed-plan matcher → journal (no orders yet).
2. Persistent-session harness for the three agents + delta format + window
   rotation.
3. Paper-order tools per the vendored PR #440 plan (verification ladder in
   docs/RESEARCH-mcp-paper-orders.md).
4. The bridge test on a burned day (2026-06-23).
5. First supervised live-paper session, him watching, minimum size.
