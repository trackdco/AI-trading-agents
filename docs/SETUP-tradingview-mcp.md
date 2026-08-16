# SETUP — TradingView MCP + the local trading agent

The agent that drives TradingView must run **on your desktop**, because
the MCP server (`tradesdontlie/tradingview-mcp`) talks to a locally
running TradingView Desktop over Chrome DevTools Protocol. The cloud
session that built this repo cannot reach your machine; it prepares the
substrate, prompts and scoring, and the local session does the driving.

> **DISAMBIGUATION — two unrelated projects share this name.** The
> desktop driver is **`tradesdontlie/tradingview-mcp`** (Node, 84 tools,
> CDP port 9222, replay/Pine/screenshots — its `CLAUDE.md` is vendored at
> `docs/TOOLS-tradingview-mcp.md`). **`atilaahmettaner/tradingview-mcp`**
> is a different, headless market-data/screener server (Python) that
> never touches TradingView Desktop and has **no replay** — its own README
> says to use tradesdontlie's for driving a chart. This confusion has
> already happened once (2026-08-11); the replay agent needs tradesdontlie's.

Facts below verified against the repo source on 2026-08-11
(`src/core/replay.js`, `src/connection.js`, `SETUP_GUIDE.md`).

> **From zero, don't do this by hand:** `docs/KICKOFF-local-session.md` is
> two paste blocks that make the local Claude session do all of it, and
> `scripts/setup_local_mac.sh` automates §§1–3 of this file idempotently.

## 1. Install the MCP server

```bash
git clone https://github.com/tradesdontlie/tradingview-mcp ~/tradingview-mcp
cd ~/tradingview-mcp
npm install
```
Node 18+ required. **There is no build step** — the server runs straight
from `src/server.js`. Follow the repo's own `SETUP_GUIDE.md` where it
differs from this — it is the authority, this file is a convenience.

## 2. Register it with Claude Code

Easiest is the CLI, run from anywhere:
```bash
claude mcp add tradingview -- node ~/tradingview-mcp/src/server.js
```

Or use this repo's committed `.mcp.json`, which expands env vars so no
repo edit is needed:
```bash
export TRADINGVIEW_MCP_PATH=~/tradingview-mcp   # in your shell profile
```
The server honors `TV_CDP_PORT` (default 9222) and `TV_CDP_HOST`
(default `127.0.0.1` — it deliberately avoids `localhost`, which
resolves to `::1` while Electron's debug port listens on IPv4 only).

Restart Claude Code, then confirm the tools are visible (`/mcp`).

## 3. Launch TradingView with remote debugging

**Preferred: let the MCP do it.** Once connected, the `tv_launch` tool
auto-detects and launches TradingView with the CDP flag on Mac, Windows
and Linux, and `tv_health_check` verifies the wiring end to end
(expect `cdp_connected: true, api_available: true`).

**Manual, macOS** (the repo's own form — flags after the binary, not
via `open --args`, which silently drops them if the app is running):
```bash
/Applications/TradingView.app/Contents/MacOS/TradingView --remote-debugging-port=9222
```

Verify it is listening — this should return JSON, not an error:
```bash
curl -s http://127.0.0.1:9222/json/version
```

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
