# RESEARCH — placing orders through the TradingView MCP (paper), 2026-08-14

His ask: *"figure out how we can calibrate the MCP to be able to place orders.
Just so we have that in advance."* Answer: **the capability exists as an open
upstream PR, it uses the exact internal surface our replay probe never found
for replay, and it is fail-closed to the Paper broker.** Nothing needs to be
invented; it needs to be vendored, verified, and wired. Procedure below.

## THE FIND — tradesdontlie/tradingview-mcp PR #440

"Native Paper Trading tools via Desktop CDP (fail-closed)" — open PR by
`sraphaz` (branch `feat/paper-trading-native-complete`, 16 commits, ~2,700
lines across 13 files, opened 2026-08-08, unmerged as of today, reviewed only
by a bot).

**Tools it adds (MCP + `tv paper` CLI, total tool count → 97):**

| read-only | mutations (guarded) |
|---|---|
| `paper_get_status` | `paper_place_order` — market / **limit** / stop / stop-limit, qty, **TP/SL brackets**, TIF DAY/WEEK/MONTH/GTD |
| `paper_get_accounts` | `paper_modify_order`, `paper_cancel_order` |
| `paper_get_positions` | `paper_close_position` |
| `paper_get_orders` | `paper_set_brackets`, `paper_clear_brackets`, `paper_switch_account` |

**Limit orders and brackets are supported natively** — the whole reason the
replay path had to simulate them.

**The surface (why replay came up empty and this doesn't):** it does not
drive the DOM and does not touch any REST endpoint. It reaches the desktop
app's internal Trading Platform objects over CDP:
`bottomWidgetBar._widgetControllers` → `controller._trading` (broker
registry) → the active broker's own `placeOrder(order)` — i.e. the same
Broker-API architecture TradingView documents for its Trading Platform
product. The replay order ticket exposed no such objects; the trading panel
does.

**The fail-closed guard, verified in the diff itself:** every one of the
eight mutation tools calls `assertPaperContext()` and a page-side
`tvRequirePaperBroker(ab)` before acting:

```
safe_for_paper_mutation = !isGuest && connectStatus === 1 && brokerId === "Paper"
```

Typed refusals otherwise (`TRADINGVIEW_AUTH_REQUIRED`, `PAPER_NOT_CONNECTED`,
`NOT_PAPER_PROVIDER`). **A connected Tradovate/Lucid broker is refused by
string match on the broker id** — the guard cannot be satisfied by a live
broker. No bypass path found in the diff. Errors are typed and caught;
mutation success is checked explicitly, not assumed.

**Residual risk, stated honestly:** it is an unmerged third-party PR
co-authored with an AI agent, reviewed by nobody but a bot. My reading of the
diff was thorough on the guard and placement paths but it is not a line-by-line
audit of 2,700 lines. Hence the verification ladder below — and the PR
usefully ships its own read-only discovery probe (~296 lines), which replaces
the probe script I was going to write.

## THE PROCEDURE (for the Mac, next week — not before)

```bash
cd ~/tradingview-mcp
git remote add sraphaz https://github.com/sraphaz/tradingview-mcp 2>/dev/null || true
git fetch sraphaz feat/paper-trading-native-complete
git checkout -B paper-pinned sraphaz/feat/paper-trading-native-complete
git rev-parse HEAD   # RECORD this SHA in every run header that places orders
npm install --no-fund --no-audit
# restart Claude Code so the new tools register
```

**Verification ladder — every rung before the first agent-driven order:**

1. Local session SKIMS the guard code itself (`assertPaperContext`,
   `tvRequirePaperBroker`) — trust but verify, it is running on his machine.
2. Run the PR's own read-only discovery probe with Paper Trading connected.
3. `paper_get_status` → `safe_for_paper_mutation: true` ONLY when the Paper
   broker is active; switch broker/disconnect → expect typed refusal.
4. ONE hand-invoked `paper_place_order`: minimum size, limit far from market;
   confirm it appears in the TradingView panel; `paper_cancel_order`; confirm
   gone. This proves the full round-trip before any agent touches it.
5. Only then wire the orchestrator, keeping the journal as the authoritative
   record. **Dual-record the first sessions**: our simulated-limit lifecycle
   logs alongside TradingView's paper fills — their engine gives us a real
   fill model to calibrate our `fill_model: "touch"` optimism against.

**Standing safety rules, unchanged:** paper account only (the guard enforces
it; we also verify it); minimum size; the kill switch is quitting
TradingView; no unattended sessions until the supervised ladder says so; and
the funded-account path remains **Tradovate's demo→live API**
(`demo.tradovateapi.com/v1`, REST `POST /order/placeOrder`, documented auth) —
server-side brackets and real acknowledgments, exactly as decided in the
runbook. The MCP paper tools are the bridge that lets him watch the agents
trade on HIS chart; they are not the funded-account execution path.

## PATHS CONSIDERED AND SET ASIDE

- **Alerts → webhook → broker**: TradingView's sanctioned automation route,
  but backwards for us — it puts Pine alerts in charge, not the agents.
- **DOM/UI automation of the order ticket**: brittle, last resort, unneeded
  now.
- **Reverse-engineered paper REST endpoints**: nothing credible public, and
  the internal-object route is cleaner and already built.
- **Waiting for upstream merge**: no maintainer signal on #440; pinning the
  contributor branch (with the SHA recorded) beats waiting.
