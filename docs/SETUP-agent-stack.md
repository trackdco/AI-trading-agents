# SETUP — the agent stack, and what the local session still has to do

Companion to `docs/SETUP-tradingview-mcp.md` (which covers the MCP install
itself). This file covers the **three agents**, the **briefing contract** that
feeds them, and the **Phase 0 parity helper**.

Written from the cloud session, which per `SETUP-tradingview-mcp.md` §0
*"prepares the substrate, prompts and scoring"* while the local session does the
driving. Everything below is committed on
`claude/tradingview-mcp-agent-setup-ql18v8`.

---

## WHAT IS DONE, AND WHAT IS NOT

| | status |
|---|---|
| Three agent definitions | **done** — `.claude/agents/tv-*.md` (0.2.0: thesis/trigger carry `Read` for screenshots) |
| `.mcp.json` scaffold | **done** — `src/server.js` entry (the server has **no build step**), one env var locally |
| Phase 0 gate 3 (indicator parity) | **done and validated** — `scripts/phase0_parity.py` |
| Replay procedure | **done** — `docs/RUNBOOK-replay-scoring.md`, grounded in the MCP source |
| Agreement scorer v0 | **done** — `scripts/score_replay_run.py` |
| MCP tool reference | **done** — `docs/TOOLS-tradingview-mcp.md` (vendored) |
| MCP installed and connected | **NOT DONE — cannot be done from the cloud** |
| Phase 0 gates 1, 2, 4 | **NOT DONE** — all four need the live chart |
| Replay run itself | **NOT DONE** — downstream of the MCP |

**Why the MCP is not connected.** The server talks to TradingView Desktop over
Chrome DevTools Protocol on `127.0.0.1:9222`. That loopback address is the
*cloud container's* localhost, not the trader's Mac; there is no route from here
to his machine, by design. `curl 127.0.0.1:9222/json/version` from the cloud
returns nothing, and would still return nothing with TradingView running on his
desktop. This is the split the setup doc already anticipated, not a new problem.

---

## 1. THE THREE AGENTS

Named with a `tv-` prefix to separate them from the mechanical canon's agents
(`regime-context`, `trade-manager`, `htf-structure`), which belong to a
different system and share no doctrine. Do not cross-wire them.

| agent | role | fires |
|---|---|---|
| `tv-macro-events` | events bearing on NQ; one gate | per session-day, and before each window |
| `tv-thesis` | Tier 1 — the directional read | each window open + material structural events |
| `tv-trigger` | Tier 2 — take full / take light / pass | at each surviving candidate |

### None of the three holds MCP tools. This is deliberate.

The stack is scored on **replay** decisions, and the no-leak gate is the thing
this project's validity rests on (`AGENT-OPERATING-SPEC.md` Phase 0.4: *"A
decision made on a chart showing later bars is worthless, and the error is
invisible in aggregate"*).

An agent holding MCP tools could step the chart past its own decision minute.
An agent holding WebSearch — `tv-macro-events` especially — could search for a
2026-06-25 replay and find what happened on 2026-06-26. **No prompt instruction
reliably prevents a search result from carrying the future.**

So the orchestrator (the local Claude Code session) holds the tools, drives
replay, verifies no-leak, builds the briefing, and calls the agents. The agents
see only what they are handed. This matches the existing house pattern —
blueprint §6.1, and the integrity argument written into
`.claude/agents/trade-manager-replay.md`.

**As of 0.2.0, `tv-thesis` and `tv-trigger` carry `Read`** — on the
trade-manager-replay precedent — because the MCP saves chart screenshots as PNG
files and returns a ~300-byte path, so the agent opens its own screenshot
instead of having the chart described to it. The contract bounds it: **only the
paths named in the briefing**, and never `data/narrated_days/*.json` or
`docs/CORPUS-narrated-days.md`, which record what *he* did on the replayed day
— reading them during a scored run destroys the agreement axis.
`tv-macro-events` stays `tools: []`; it reads no chart and needs no files.

**Consequence for `tv-macro-events`:** its contract is identical in replay and
live; only the briefing builder differs. In replay, build `scheduled_events`
as-of from `data/reference/news_archive.csv` (red-folder US releases,
2023-01-04 → 2026-07-16, ET wall-clock) filtered to `datetime_ET <=
decision_minute`. In live, the orchestrator runs the search and drops results in
`headlines`. **Nothing dated after the decision minute may enter the briefing.**

---

## 2. THE BRIEFING CONTRACT

The agents reference these fields by name. An agent handed a briefing missing
them will pass rather than guess, which is correct but useless — so build them.

**Common to all three:**

```
decision_minute   ISO, NY. The minute the decision is made AT.
session_day       18:00-anchored. His Friday 26 June is session_day 2026-06-25.
window            LONDON | NY_PRE | NY_AM
```

**`tv-macro-events`** additionally:

```
scheduled_events  [ {event, time_et, impact} ]  as-of filtered, red-folder
headlines         [ ... ]                       live mode only; empty in replay
```

**`tv-thesis`** additionally:

```
event_trigger        why it is firing: window_open | extreme_taken | 15m_ma_close
                     | displacement | rebalance_complete | tp1_filled | destination_hit
daily_profile        {poc, val, vah}   developing
anchored_weekly_profile {poc, val, vah, high, low, anchor}
prev_day             {poc, val, vah, high, low}
fibs                 {level: price}
fib_source           marked_swing | session_range   -- he uses marked swings
asia_character       text
macro                the tv-macro-events output
```

**`tv-trigger`** additionally:

```
screenshot           PATH to the PNG (replay truncated at decision_minute);
                     the agent Reads it itself
thesis               the standing tv-thesis output
candle_start         START time -- his chart labels candles by start
timeframe            2 | 3
pair_shape           same_candle | sequential
levels_closed        ["own_ma_2m", "vwap", ...]  own MA is mandatory
candle_high/low      the signal candle's extremes
levels_near_extreme  which live levels the extreme sits ON (drives the stop rule)
next_level_beyond    for the headroom constraint
fills_this_window    for the cap -- counts FILLS, not attempts
```

`daily_profile` and `anchored_weekly_profile` are **both required**, always.
"Value area" means the daily profile some days and the weekly one others; they
sat 165pt apart on 2026-06-25 and the agents are instructed to reject an
unqualified `val`/`vah`.

---

## 3. PHASE 0 GATE 3 — mechanical now

```bash
# print the research-build side at a decision minute
python -m scripts.phase0_parity 2026-06-25 04:06

# gate it against what the chart shows -- exits 1 on FAIL
python -m scripts.phase0_parity 2026-06-25 04:06 \
    --vwap 29492.65 --bb-ma-2m 29522.59 --bb-ma-3m 29510.94
```

Thresholds are the spec's: **>1pt on VWAP or >0.5pt on a BB MA** means his chart
config differs from the research build — say so and stop.

**Profile levels print but are NOT gated.** `agent_context.volume_profile`
documents a ~30pt unresolved residual (real profiles distribute volume by traded
ticks, not uniformly, and his chart's row size is unknown). Gating on them would
fail a correct setup. Read profile levels off the chart.

### It is validated against the corpus, not just written

Run at session-day 2026-06-25, the script reproduces four independent values
that `data/narrated_days/2026-06-25.json` records from his own chart:

| | corpus | script | at |
|---|---|---|---|
| 2m BB MA | 29,523.97 | 29,523.97 | 04:02 |
| 3m BB MA | 29,510.94 | 29,510.94 | 04:06 |
| VWAP | 29,492.65 | 29,492.65 | 04:06 |
| signal candle close | 29,477.25 | 29,477.25 | 04:06 |

That also confirms the **time convention**, which is the thing most likely to
silently corrupt a run: his 2m candle labelled 04:04 spans 04:04–04:05 and
closes at 04:06, so **04:06 is the decision minute**. Pass the close time, not
the label.

---

## 4. WHAT THE LOCAL SESSION DOES, IN ORDER

**Starting from a bare Mac: `docs/KICKOFF-local-session.md`** — two paste
blocks; the local session does everything, including the MCP install via
`scripts/setup_local_mac.sh` and the first-session probe for native limit
orders in TradingView's internal replay API.

**The step-by-step replay procedure is `docs/RUNBOOK-replay-scoring.md`** —
grounded in the MCP's actual source, including the market-only `replay_trade`
constraint (limit lifecycle is orchestrator-simulated), the timezone trap in
`replay_start`, and the mechanical no-leak check. In outline:

1. **Install the MCP and launch TradingView** — `docs/SETUP-tradingview-mcp.md`
   (no build step; `tv_launch` + `tv_health_check` do the wiring).
2. **Point `.mcp.json` at it:**
   ```bash
   export TRADINGVIEW_MCP_PATH=~/tradingview-mcp
   # TV_CDP_PORT defaults to 9222
   ```
   Restart Claude Code, confirm with `/mcp`.
3. **Run Phase 0, all four gates** (runbook R0). Gate 3 is
   `scripts/phase0_parity.py`. **Gate 4 — no-leak — is the one that matters
   most**, re-verified after every replay jump.
4. **Run replay** (runbook R1–R3) and log **every candidate, taken or passed,
   with its full payload**, to `output/agent_runs/<sess_day>.jsonl`. Unfilled
   limits get their own rows.
5. **Score agreement** — `python -m scripts.score_replay_run
   output/agent_runs/<sess_day>.jsonl` against his recorded decisions. The
   outcome axis comes after agreement runs are stable.

**No live orders**, under any circumstances, until scoring has been run and
reviewed with him.

---

## 5. TWO THINGS THE SCORER MUST NOT MARK WRONG

Carried forward from `PLAYBOOK.md` §7 because it is the single most important
scoring instruction and a naive scorer marks both as errors:

- **2026-06-25.** A pre-market short moved to break-even before the cash open.
  The market then fell 897 points; **29.2R was available had he held.**
  *"That's straight gambling for me."*
- **2026-06-26.** A trigger he believed in with a stop he hated. He refused to
  limit a nearer level for a tighter fill. *"I'm sticking to my rules."*

**A rule that pays out over a year is not refuted by the day it costs the most.**
Score the process, not the counterfactual.

---

## 6. OPEN, AND CARRIED FORWARD

Unchanged from `HANDOFF-local-agent-buildout.md` — recorded here so they are not
lost when the agents start running:

1. **`SEQ_CANDLES = 3`** in `two_level_check.py` is a guess, not his number. It
   decides whether 2026-06-25 London had zero qualifying shorts or one.
   **First parameter to question if the agent takes trades he wouldn't.**
   `tv-trigger` is instructed to justify every `sequential` pair for this reason.
2. **Monday 22 June's London stop** is unrecoverable — excluded from R
   aggregates rather than estimated.
3. **Sample size.** His own 20 matched picks clear the outcome bar at only
   p ≈ 0.07. One month cannot settle this for the agent either.

### Noted while setting this up, not fixed

`requirements.txt` pins `numpy==2.5.1`, which requires **Python ≥ 3.12**. On
Python 3.11 the pinned install fails outright. The scripts themselves run fine
once the deps are present — this is a pin/interpreter mismatch, flagged rather
than changed, since the local machine may already be on 3.12.
