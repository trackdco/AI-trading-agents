#!/usr/bin/env bash
# SETUP — TradingView MCP on the trader's Mac. Idempotent: safe to re-run any time.
#
# Does everything scriptable from docs/SETUP-tradingview-mcp.md:
#   1. checks Node 18+
#   2. clones/updates tradesdontlie/tradingview-mcp to ~/tradingview-mcp (public
#      repo, no auth needed) and npm-installs it — there is NO build step
#   3. persists TRADINGVIEW_MCP_PATH in ~/.zshrc (for this repo's .mcp.json)
#   4. registers the server with Claude Code (user scope) if `claude` exists
#   5. launches TradingView with the CDP debug port and verifies 127.0.0.1:9222
#
# What it deliberately does NOT do: touch this repo's git state, install Python
# deps (the local Claude session handles those in KICKOFF Phase B), or place any
# trade anywhere.
set -euo pipefail

MCP_DIR="${TRADINGVIEW_MCP_PATH:-$HOME/tradingview-mcp}"
TV_BIN="/Applications/TradingView.app/Contents/MacOS/TradingView"
PORT=9222

say()  { printf '\n== %s\n' "$*"; }
note() { printf '   %s\n' "$*"; }
fail() { printf '\nXX %s\n' "$*" >&2; exit 1; }

[ "$(uname)" = "Darwin" ] || note "WARNING: written for macOS; on other platforms follow docs/SETUP-tradingview-mcp.md by hand."

say "1/5 Node"
command -v node >/dev/null || fail "node not found. Install it first:  brew install node   (or nodejs.org), then re-run this script."
node -e 'process.exit(parseInt(process.versions.node.split(".")[0],10)>=18?0:1)' \
  || fail "Node 18+ required, found $(node -v). Upgrade:  brew upgrade node"
note "$(node -v) ok"

say "2/5 MCP server -> $MCP_DIR"
if [ -d "$MCP_DIR/.git" ]; then
  git -C "$MCP_DIR" pull --ff-only 2>/dev/null || note "pull skipped (local changes or offline) — existing checkout kept"
else
  git clone https://github.com/tradesdontlie/tradingview-mcp "$MCP_DIR"
fi
( cd "$MCP_DIR" && npm install --no-fund --no-audit --loglevel=error )
[ -f "$MCP_DIR/src/server.js" ] || fail "$MCP_DIR/src/server.js missing — clone looks wrong"
note "installed (entry: src/server.js — no build step exists)"

say "3/5 shell env"
ZP="$HOME/.zshrc"
LINE="export TRADINGVIEW_MCP_PATH=\"$MCP_DIR\""
touch "$ZP"
if grep -qs "TRADINGVIEW_MCP_PATH=" "$ZP"; then
  note "TRADINGVIEW_MCP_PATH already set in ~/.zshrc — left as is"
else
  printf '\n# TradingView MCP (AI-trading-agents)\n%s\n' "$LINE" >> "$ZP"
  note "added to ~/.zshrc"
fi

say "4/5 register with Claude Code"
if command -v claude >/dev/null; then
  claude mcp remove tradingview -s user >/dev/null 2>&1 || true
  if claude mcp add tradingview -s user -- node "$MCP_DIR/src/server.js"; then
    note "registered (user scope) — restart Claude Code to load it"
  else
    note "claude mcp add failed — check 'claude mcp list' after restarting"
  fi
else
  note "claude CLI not found. Install Claude Code first:  npm install -g @anthropic-ai/claude-code"
  note "then re-run this script (or run:  claude mcp add tradingview -s user -- node $MCP_DIR/src/server.js )"
fi

say "5/5 TradingView with the debug port"
if curl -s --max-time 2 "http://127.0.0.1:$PORT/json/version" >/dev/null; then
  note "already listening on $PORT — nothing to do"
else
  if pgrep -x TradingView >/dev/null; then
    printf '   TradingView is running WITHOUT the debug port. Quit and relaunch it now? [y/N] '
    read -r a || a=n
    case "$a" in
      y|Y|yes|YES)
        osascript -e 'quit app "TradingView"' || true
        for _ in 1 2 3 4 5 6 7 8 9 10; do pgrep -x TradingView >/dev/null || break; sleep 1; done
        ;;
      *) note "left running. Quit it (Cmd+Q) and re-run this script, or use the tv_launch tool from Claude." ;;
    esac
  fi
  if ! pgrep -x TradingView >/dev/null; then
    [ -x "$TV_BIN" ] || fail "TradingView.app not found at $TV_BIN — install TradingView Desktop first."
    nohup "$TV_BIN" --remote-debugging-port=$PORT >/dev/null 2>&1 &
    disown || true
    note "launched — waiting for the port"
    for _ in 1 2 3 4 5 6 7 8 9 10 11 12; do
      curl -s --max-time 2 "http://127.0.0.1:$PORT/json/version" >/dev/null && break
      sleep 1
    done
  fi
  if curl -s --max-time 3 "http://127.0.0.1:$PORT/json/version" >/dev/null; then
    note "port $PORT is up"
  else
    note "port $PORT not answering yet. Give it ~10s and check:  curl -s http://127.0.0.1:$PORT/json/version"
    note "(or, once Claude Code is restarted, just run the tv_launch tool)"
  fi
fi

say "done"
note "next: restart Claude Code, open it in the AI-trading-agents repo,"
note "and follow docs/KICKOFF-local-session.md — Phase B."
