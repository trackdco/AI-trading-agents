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

2. PROBE FOR NATIVE LIMIT ORDERS IN REPLAY. The MCP only wraps market
   buy/sell/close from window.TradingViewApi._replayApi, but the object
   may carry more. From the MCP checkout, run a small node script that
   uses its own src/connection.js to evaluate, in the TradingView page:
     - Object.getOwnPropertyNames(window.TradingViewApi._replayApi)
     - plus getOwnPropertyNames of its prototype chain (2 levels)
   and report every method name you find, verbatim. We are looking for
   anything shaped like limit/stop/order placement. If such methods
   exist, say so and STOP — we will extend the MCP with a
   replay_limit_order tool before running the loop, so limits are native.
   If they don't exist, say so — the runbook's simulated-limit path (with
   the drawn limit lines) is the fallback and it is already specced.

3. Python deps for the repo scripts: python3 --version; if 3.12+,
   pip install -r requirements.txt into a venv; if 3.11, install the same
   packages unpinned (the numpy pin needs 3.12 — known, documented).
   Verify: python3 -m scripts.phase0_parity 2026-06-25 04:06 reproduces
   VWAP 29492.65 and bb_ma_3m 29510.94.

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
