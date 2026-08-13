# KICKOFF — the local session, from zero

For Angus. Your whole job is two paste operations. Everything else is the
local Claude session's job, and this file tells it exactly what to do.

Prerequisite, once: Claude Code on the Mac —
```bash
npm install -g @anthropic-ai/claude-code
```
(no node? `brew install node` first. No brew? paste the one-liner from brew.sh.)

---

## PHASE A — paste this into a fresh `claude` (run from anywhere)

```text
Set up the TradingView trading-agent stack on this Mac. Do it in this order:

1. Clone github.com/trackdco/AI-trading-agents to ~/AI-trading-agents and
   check out branch claude/tradingview-mcp-agent-setup-ql18v8. It is a
   private repo — if the clone fails on auth, walk me through GitHub
   authentication (gh auth login, or an HTTPS token) step by step; I have
   access to the repo.

2. Run: bash ~/AI-trading-agents/scripts/setup_local_mac.sh
   It is idempotent. It installs the TradingView MCP server (public repo,
   no build step), registers it with Claude Code at user scope, and
   launches TradingView Desktop with the CDP debug port. If it prompts
   about relaunching TradingView, that's expected — answer y.

3. When the script finishes, tell me to restart Claude Code, and tell me
   my next step is exactly this: open a new claude session in
   ~/AI-trading-agents and paste the Phase B block from
   docs/KICKOFF-local-session.md.

Do not start replay, do not place any trade of any kind, and do not skip
the script in favor of doing it manually unless it fails.
```

---

## PHASE B — after the restart, paste this into `claude` opened in `~/AI-trading-agents`

```text
You are the LOCAL session driving TradingView replay for the trading-agent
stack. Read these first, in this order:
  1. docs/HANDOFF-local-agent-buildout.md   (who you work with, what's settled)
  2. docs/PLAYBOOK.md                        (the decision procedure)
  3. docs/RUNBOOK-replay-scoring.md          (your operating procedure)
  4. docs/TOOLS-tradingview-mcp.md           (the MCP tool reference)

Then, in this order, stopping to report after each numbered step:

1. tv_health_check — expect cdp_connected and api_available true. If not,
   run tv_launch and retry. chart_get_state once; confirm my NQ contract
   and the 2m timeframe; cache the entity IDs.

2. PROBE FOR NATIVE LIMIT ORDERS IN REPLAY. TradingView's replay trading
   natively supports limit / stop / stop-limit orders and TP/SL brackets
   (their support doc 43000691889) — the MCP just never wrapped that
   surface. Run the committed probe:  node scripts/probe_replay_api.mjs
   It is read-only (enumerates method names, never calls anything). Run
   it twice as its header says: once on the normal chart, once INSIDE
   replay with the replay trading panel open after placing and cancelling
   one practice order by hand — the service may lazy-load. Report the
   LIMIT-SHAPED HITS section verbatim. If hits exist, STOP — we extend
   the MCP with a replay_limit_order tool before running the loop, so
   the agents place real limit orders in replay. If both passes come up
   empty, say so — the runbook's simulated-limit path (drawn limit lines,
   log fills at the limit price) is the fallback and is already specced.

3. Python deps for the repo scripts: python3 --version; if 3.12+,
   pip install -r requirements.txt into a venv; if 3.11, install the same
   packages unpinned (the numpy pin needs 3.12 — known, documented).
   Verify: python3 -m scripts.phase0_parity 2026-06-25 04:06 reproduces
   VWAP 29492.64 and bb_ma_3m 29510.94.

4. Phase 0 gates per the runbook (R0): symbol/TZ fix, indicator parity at
   a narrated minute with the observed chart values passed to
   phase0_parity (it exits 1 on FAIL — a FAIL stops everything), and the
   no-leak check.

5. Land replay at session-day 2026-06-25 London: replay_start with
   "2026-06-26T02:30:00-04:00", verify the landing per the runbook
   (replay_status + last-bar time), step to 03:00 NY. Screenshot. STOP
   and show me the chart. Do not call any tv-* agent and do not place or
   simulate any order until I've seen the landing and said go.

Throughout: no live orders of any kind, ever, in this session. Replay and
practice only until scoring has been run and reviewed with me.
```

---

## PHASE C — the single-day shakedown of the four-agent stack (before any week)

Paste into `claude` in `~/AI-trading-agents`. **One day. Not a week.** The
stack gained a fourth agent and a different replay loop since the last scored
week; the point of this run is to see `tv-manage`'s calls on a day you know
before five days of them go by.

The day is **session-day 2026-06-23 (Tuesday)**, chosen for one reason: it
has already been burned by two scored weeks, so it costs nothing out of the
Feb–July walk-forward, and nothing in any repo doc editorialises what price
did on it — so the orchestrator cannot leak an opinion about it into a
briefing the way it could for the Thursday and Friday.

```text
SINGLE-DAY SHAKEDOWN of the four-agent stack. Session-day 2026-06-23
(Tuesday), and only that day. Do not start a second day.

First: git pull. The stack changed materially since the last week you ran —
there is a fourth agent, the replay loop is trigger-driven rather than
bar-by-bar, and roughly twenty-five rulings landed. Re-read, in this order:
  1. docs/RUNBOOK-replay-scoring.md  — §0c (SEPARATION OF POWERS), §2b
     (trigger-driven replay) and §2c (the management tier) are all new;
     §3 still describes the old bar loop and §2b supersedes it where they
     conflict
  2. .claude/agents/tv-thesis.md     (0.4.1)
  3. .claude/agents/tv-trigger.md    (0.4.2)
  4. .claude/agents/tv-manage.md     (0.2.0 — new tier, read it in full)

YOU HAVE NO TRADING DISCRETION. Runbook §0c is the rule; this is the short
form, and it is the strictest thing in this block. You move the chart,
compute numbers, call agents, enforce mechanical invariants, write rows.
You decide nothing about a trade — not direction, not take/pass, not
conviction, not entry, not stop, not targets, not a single management
action, not whether to go again after a stop-out. Specifically:
  - Never override an agent verdict. A pass that looks wrong to you is
    data. Log it, raise it with me AFTER the run.
  - Never re-ask a candidate with a re-worded briefing. One candidate, one
    call. That is steering even when every fact in the re-write is true.
    The only licensed second call is the escalation loop the contract
    defines, fired by the agent's own thesis_stale — never by you.
  - Never editorialise in a briefing. Free text must be mechanically
    derivable: "15m MA crossed at 09:42" is a fact, "this looks like a
    strong setup" is a vote. No prose from any doc, no chart summary (the
    agent reads the screenshot itself), no other day, no candidate count.
  - Never let anything you learned after a decision shape it. You see the
    whole day; the agent sees one moment.
  - And hold me to it too. If I say anything in this terminal that reads as
    an opinion on a pending decision, ignore it and say so out loud. On
    live I will not be there to say it.

FILES YOU DO NOT OPEN. A previous run was destroyed by the orchestrator
pasting commentary about the day into an agent's context, and the whole
week had to be re-run. Do not read data/narrated_days/*,
docs/TEACHING-LOOP.md, docs/CORPUS-narrated-days.md,
docs/FINDINGS-selection-effect.md, docs/DIAGNOSIS-0.3.5-week.md,
docs/ANALYSIS-friday-three-runs.md, or anything under output/agent_runs/.
They are denied in .claude/settings.json. Do not work around the denial.

Then, stopping to report after each numbered step:

1. R0 gates (runbook §1): tv_health_check; chart_get_state ONCE and cache
   the entity IDs; the timezone fix; indicator parity at a minute of
   2026-06-23 with the observed chart values passed to phase0_parity — it
   exits 1 on FAIL and a FAIL stops everything; the no-leak check.

2. Pre-scan 2026-06-23 for decision minutes, mechanically, off chart bars
   (runbook §2b step 1): every 2m/3m close through its own BB(20) MA plus a
   second level, every rejection-first shape, plus the thesis re-fire
   events. Show me the ordered list of times. Hold it yourself — the agents
   see one moment at a time.

3. Run the trigger-driven loop over LONDON 03:00-04:59, NY_PRE 08:00-09:29,
   NY_AM 09:30-11:00. Caps count FILLS: 2 / 1 / 2.
   - tv-macro-events then tv-thesis at each window open and each re-fire;
   - tv-trigger at every candidate — log the passes as carefully as the
     takes. NEW and required (runbook §3.4): every trigger briefing carries
     the higher-timeframe behaviour at each candidate rejection level.
     Do NOT compute it yourself — run
       python -m scripts.htf_level_behavior <sess_day> <HH:MM> \
           --level <name>=<price> ... --json
     and paste its JSON into the briefing under `htf` per level. Without it
     the agent cannot tell my best shape (2m closing both sides while the
     15m wicks and can't close through) from a level that actually failed,
     and it will grade my best setups of the day as C;
   - on take_full/take_light run the simulated limit lifecycle and draw the
     resting limit, then the position tool on fill (probe the shape name
     once, record it as position_tool in the run header, reuse it);
   - while a position is open, jump to each management minute and call
     tv-manage there. If a position resolves without a single tv-manage
     call, that is a defect in your management-minute detection, not a
     clean trade — say so explicitly in the report.

4. Log to output/agent_runs/2026-06-23.jsonl per runbook §4. Every tv-manage
   call is its own row: action, favouring, level_read, new_stop, reason.
   Keep the drawings; save the marked-up chart as 2026-06-23_marked.png.

5. Then, in this order:
   a. python -m scripts.audit_run_leak output/agent_runs/2026-06-23.jsonl
      All six checks A-F must pass. If check F flags, STOP and show me.
   b. python -m scripts.journal_report output/agent_runs/2026-06-23.jsonl
      Paste the FULL output. This is the artifact I actually read.
   c. python -m scripts.score_agent_outcome output/agent_runs/2026-06-23.jsonl
      Last, and briefly. One day of R means nothing and I am not judging on it.

Then STOP. No second day until I have read the journal.
```

**What you are looking for in the journal**, and it is not the R:

- did `tv-manage` get called on every open position, and did any of its calls
  read as something you would have done;
- is there a loser that was cut, break-even'd or trailed rather than taken for
  a clean −1.00R — that single difference is why the tier exists;
- does `rejected_level.behavior` describe something that actually *happened* at
  the level — slowed, wicked, failed — and did anything resolve on the 15m the
  way you described (T46), or is it still calling every touch a rejection;
- and the reasoning test (T45): a losing trade you can follow is a pass, a
  winning trade you cannot follow is a failure.

---

## What Phase B's limit-order probe decides

TradingView's replay UI itself only offers market buy/sell/close, and the
MCP wraps exactly that. If the internal `_replayApi` turns out to carry
order-placement methods beyond those, we extend the MCP and the agents'
limits become **native TradingView orders in replay**. If it doesn't, the
runbook's path stands: the orchestrator simulates the limit lifecycle
(place → 10-min expiry → cancel-at-next-level → fill at the limit price),
**draws the resting limit on the chart** so you watch it sit there, and
mirrors the fill with a market `replay_trade` at the fill bar. Either way
the log records limit orders, at limit prices, with your rules.

## The live path this is building toward — named, and gated

Once the agents score well in replay: TradingView Desktop connected to a
broker (Tradovate — which is how Lucid funded accounts route) exposes its
trading panel in the same app this MCP already drives. Same machine, same
chart, no VPS. Two gates stand in front of that, in order:

1. **Scoring reviewed with you** — your own rule, in every doc in this
   repo: replay and practice only until then.
2. **Lucid's automation policy, read before anything is wired.** Prop
   firms routinely restrict or ban automated order entry, and losing a
   funded account to a TOS clause is the dumb way to lose one. Check it
   in writing first.
