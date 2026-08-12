#!/usr/bin/env bash
# SETUP — YouTube Data MCP server (wynandw87/claude-code-youtube-mcp).
# Idempotent: safe to re-run any time. Re-running also updates the checkout.
#
# Gives Claude the YouTube Data API v3 as tools: transcripts, search, metadata,
# channel/playlist info, comments, engagement. Complements the /watch skill rather
# than duplicating it — /watch SEES a video (frames + audio), this one QUERIES
# YouTube's catalogue as structured data and pulls transcripts without downloading.
#
#   1. checks Node 18+
#   2. clones/updates the repo to ~/claude-code-youtube-mcp and npm-installs it
#      (the package's `prepare` script runs `tsc`, so dist/ builds during install)
#   3. registers it with Claude Code at USER scope, so it is available in every
#      project rather than only this repo
#
# Usage — the key is required and comes from the environment, never an argument
# (an argument would land in your shell history):
#
#   export YOUTUBE_API_KEY=...        # or put YOUTUBE_API_KEY= in this repo's .env
#   bash scripts/setup_youtube_mcp.sh
#
# Get a key at https://console.cloud.google.com/apis/credentials — enable
# "YouTube Data API v3" on the project first. Free tier is 10,000 quota units/day;
# a search costs 100, most reads cost 1.
#
# WHERE THE KEY ENDS UP: `claude mcp add -e` writes it in plaintext into your
# user-scope Claude config (~/.claude.json). That file is outside this repo and must
# stay that way. Never commit the key; .env is gitignored and stays the only copy
# inside the repo.
#
# What it deliberately does NOT do: touch this repo's git state, write to .mcp.json
# (that file is project-scope and committed — a personal API key does not belong in
# it), or install Python deps.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MCP_DIR="${YOUTUBE_MCP_PATH:-$HOME/claude-code-youtube-mcp}"
MCP_NAME="${YOUTUBE_MCP_NAME:-youtube}"

say()  { printf '\n== %s\n' "$*"; }
note() { printf '   %s\n' "$*"; }
fail() { printf '\nXX %s\n' "$*" >&2; exit 1; }

# Fall back to the repo's .env (code-standards.md: keys live there). Read the one
# line rather than sourcing the file, so nothing else in .env gets executed.
if [ -z "${YOUTUBE_API_KEY:-}" ] && [ -f "$REPO_ROOT/.env" ]; then
  YOUTUBE_API_KEY="$(grep -E '^[[:space:]]*YOUTUBE_API_KEY=' "$REPO_ROOT/.env" \
    | tail -1 | cut -d= -f2- | tr -d '"'"'"' ' || true)"
fi

case "${YOUTUBE_API_KEY:-}" in
  "")            fail "YOUTUBE_API_KEY is not set. export it, or add it to $REPO_ROOT/.env, then re-run." ;;
  YOUR_KEY|your_api_key_here|CHANGEME|...)
                 fail "YOUTUBE_API_KEY is still a placeholder ('$YOUTUBE_API_KEY'). Put your real key in and re-run." ;;
esac

say "1/3 Node"
command -v node >/dev/null || fail "node not found. Install Node 18+ (brew install node, or nodejs.org), then re-run."
node -e 'process.exit(parseInt(process.versions.node.split(".")[0],10)>=18?0:1)' \
  || fail "Node 18+ required, found $(node -v). Upgrade:  brew upgrade node"
note "$(node -v) ok"

say "2/3 server -> $MCP_DIR"
if [ -d "$MCP_DIR/.git" ]; then
  git -C "$MCP_DIR" pull --ff-only 2>/dev/null || note "pull skipped (local changes or offline) — existing checkout kept"
else
  git clone https://github.com/wynandw87/claude-code-youtube-mcp.git "$MCP_DIR"
fi
( cd "$MCP_DIR" && npm install --no-fund --no-audit --loglevel=error )
[ -f "$MCP_DIR/dist/index.js" ] || fail "$MCP_DIR/dist/index.js missing — the tsc build did not run. Try: (cd $MCP_DIR && npm run build)"
note "built dist/index.js"

say "3/3 register with Claude Code (user scope)"
# `mcp add` errors on an existing name, so drop any previous registration first.
claude mcp remove -s user "$MCP_NAME" >/dev/null 2>&1 || true
claude mcp add -s user "$MCP_NAME" -e "YOUTUBE_API_KEY=$YOUTUBE_API_KEY" -- node "$MCP_DIR/dist/index.js"

say "verify"
claude mcp list 2>&1 | grep -E "^$MCP_NAME:" || note "not listed yet — restart Claude Code, then run: claude mcp list"
note "done — new sessions get the youtube tools; approve the server on first use."
