# SETUP — TradingView MCP + the local trading agent

The agent that drives TradingView must run **on your desktop**, because
the MCP server (`tradesdontlie/tradingview-mcp`) talks to a locally
running TradingView Desktop over Chrome DevTools Protocol. The cloud
session that built this repo cannot reach your machine; it prepares the
substrate, prompts and scoring, and the local session does the driving.

## 1. Launch TradingView with remote debugging

TradingView Desktop must be started with the CDP port open.

**macOS**
```bash
open -a "TradingView" --args --remote-debugging-port=9222
```

**Windows** (adjust the path if yours differs)
```powershell
& "$env:LOCALAPPDATA\Programs\TradingView\TradingView.exe" --remote-debugging-port=9222
```

Verify it is listening — this should return JSON, not an error:
```bash
curl -s http://127.0.0.1:9222/json/version
```

## 2. Install the MCP server

```bash
git clone https://github.com/tradesdontlie/tradingview-mcp
cd tradingview-mcp
npm install
npm run build          # if the repo defines a build step
```
Node 18+ required. Follow the repo's own README where it differs from
this — it is the authority, this file is a convenience.

## 3. Register it with Claude Code

Easiest is the CLI, run from anywhere:
```bash
claude mcp add tradingview -- node /ABSOLUTE/PATH/TO/tradingview-mcp/dist/index.js
```

Or add it by hand to your Claude Code MCP config:
```json
{
  "mcpServers": {
    "tradingview": {
      "command": "node",
      "args": ["/ABSOLUTE/PATH/TO/tradingview-mcp/dist/index.js"],
      "env": { "TV_CDP_PORT": "9222" }
    }
  }
}
```
Restart Claude Code, then confirm the tools are visible (`/mcp`).

## 4. Clone this repo locally

```bash
git clone https://github.com/trackdco/AI-trading-agents
cd AI-trading-agents
git checkout claude/hello-zfmoq6
```
The local agent needs: `scripts/raw_trigger_census.py` (the candidate
set), the constraint module, and the agent prompts — all versioned here.

## 5. Sanity checks before any agent runs

Do these first; they take two minutes and catch the failures that are
otherwise invisible:

1. **Symbol and timezone.** Ask the MCP for the current symbol and a
   handful of recent bars, and reconcile them against
   `output/htf_ma_census/raw_triggers.parquet` for the same minutes.
   The CSV export was UTC while the charts were per-session local — do
   not assume the MCP matches either.
2. **Indicator parity.** Read the BB(20) MA and VWAP band values off
   the chart at a known minute and compare with `bb_ma_asof` /
   `vwap_bands`. The earlier parity check matched TradingView to within
   0.01pt; anything worse means the chart settings differ from the
   research build.
3. **Replay does not leak.** Step replay to a decision minute and
   confirm the screenshot shows no future bars. Any agent decision made
   on a chart containing later bars is worthless.

## 6. What the local agent is allowed to do

Read-only against the market, and replay-only for execution, until the
scoring in `docs/ARCHITECTURE-trading-agent.md` has been run and
reviewed. No live orders. The MCP can place practice trades in replay —
that is the intended surface.
