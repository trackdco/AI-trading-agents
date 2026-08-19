#!/usr/bin/env bash
# SETUP — runtime dependencies for the /watch plugin (watch@claude-video).
# Idempotent: safe to re-run any time. Installs nothing Python-side.
#
# Declaring the plugin is the other half, and it is NOT done yet — add these two keys
# to .claude/settings.json by hand (the equivalent of `/plugin marketplace add
# bradautomates/claude-video` + `/plugin install watch@claude-video`, which is how you
# install it where the interactive /plugin panel doesn't exist, e.g. Claude Code on
# the web). Takes effect on the next session, not the running one:
#
#   "extraKnownMarketplaces": {
#     "claude-video": { "source": { "source": "github", "repo": "bradautomates/claude-video" } }
#   },
#   "enabledPlugins": { "watch@claude-video": true }
#
# Claude Code then fetches the skill itself. What it CANNOT do is install the two
# binaries the skill shells out to. The skill's own installer auto-installs only on
# macOS via brew; on Linux it just prints the commands. This script does it.
#
#   ffmpeg + ffprobe  frame extraction and audio slicing
#   yt-dlp            URL downloads and native-caption pulls (not needed for local files)
#
# Run it when /watch reports missing binaries:  bash scripts/setup_watch_deps.sh
#
# What it deliberately does NOT do: touch this repo's git state, write any API key,
# install Python deps for the trading engine (requirements.txt owns those), or add
# itself to a SessionStart hook — the trading sessions that never touch video
# shouldn't pay an apt round-trip on every start.
#
# KNOWN LIMIT — YouTube URLs do not work from Claude Code on the web. yt-dlp gets
# HTTP 429 then "Sign in to confirm you're not a bot": YouTube blocks the datacenter
# IP, and every request (including a headless Chromium) egresses through the same
# agent proxy, so it is the same IP either way. Measured Aug 2026; player_client
# android_vr got through once and then stopped. Installing a JS runtime (npm i -g
# deno) clears yt-dlp's EJS deprecation warning but does NOT lift the block.
#   What still works from here: local video files (/watch <path> is unaffected), and
#   the youtube MCP server (scripts/setup_youtube_mcp.sh) — the Data API and the
#   transcript scraper hit googleapis.com/i.ytimg.com, which are not IP-blocked.
#   For a URL /watch must download: run it on a laptop, or fetch the file first and
#   pass the local path.
#
# Whisper is OPTIONAL. Without a key, /watch still returns frames, and videos that
# carry captions (most public YouTube) still return a full transcript. A key is only
# needed to transcribe caption-less sources — local recordings, most TikToks. Set
# GROQ_API_KEY (preferred) or OPENAI_API_KEY in ~/.config/watch/.env, mode 0600.
# Never put those keys in this repo's .env.
set -euo pipefail

say()  { printf '\n== %s\n' "$*"; }
note() { printf '   %s\n' "$*"; }
fail() { printf '\nXX %s\n' "$*" >&2; exit 1; }

need_ffmpeg=0
need_ytdlp=0
command -v ffmpeg  >/dev/null && command -v ffprobe >/dev/null || need_ffmpeg=1
command -v yt-dlp  >/dev/null || need_ytdlp=1

if [ "$need_ffmpeg" = 0 ] && [ "$need_ytdlp" = 0 ]; then
  say "already satisfied"
  note "ffmpeg  $(ffmpeg -version | head -1 | cut -d' ' -f3)"
  note "yt-dlp  $(yt-dlp --version)"
  exit 0
fi

say "1/2 ffmpeg + ffprobe"
if [ "$need_ffmpeg" = 0 ]; then
  note "present — skipping"
elif [ "$(uname)" = "Darwin" ]; then
  command -v brew >/dev/null || fail "Homebrew not found. Install from brew.sh, then re-run."
  brew install ffmpeg
elif command -v apt-get >/dev/null; then
  # Ubuntu/Debian, incl. Claude Code on the web. The update is required: the base
  # image ships a stale index and the install 404s on moved .deb files without it.
  ${SUDO:-} apt-get update -qq
  ${SUDO:-} apt-get install -y --no-install-recommends ffmpeg
elif command -v dnf >/dev/null; then
  ${SUDO:-} dnf install -y ffmpeg
else
  fail "No brew/apt-get/dnf found. Install ffmpeg (with ffprobe) by hand, then re-run."
fi

say "2/2 yt-dlp"
if [ "$need_ytdlp" = 0 ]; then
  note "present — skipping"
elif [ "$(uname)" = "Darwin" ] && command -v brew >/dev/null; then
  brew install yt-dlp
else
  # pip over the distro package on purpose: yt-dlp breaks whenever a site changes its
  # player, so the apt build is routinely months stale and fails on live URLs.
  python3 -m pip install --upgrade --timeout 120 --retries 5 yt-dlp
fi

say "verify"
command -v ffmpeg  >/dev/null || fail "ffmpeg still missing"
command -v ffprobe >/dev/null || fail "ffprobe still missing (some minimal ffmpeg builds omit it)"
command -v yt-dlp  >/dev/null || fail "yt-dlp still missing"
note "ffmpeg  $(ffmpeg -version | head -1 | cut -d' ' -f3)"
note "yt-dlp  $(yt-dlp --version)"
note "ready — /watch <url-or-path> [question]"
