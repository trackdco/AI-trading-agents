#!/usr/bin/env bash
# Pull captions for the Star Trading channel, then convert to timestamped text.
#
# This is a thin wrapper over pull_captions.py, which does the real work:
# a manifest, a per-run cap, sleeps between requests, exponential backoff and a
# hard stop after 3 consecutive failures. The old version of this script swept
# all 117 videos in one pass with a 3s sleep, which is what got the IP flagged.
#
# Run it from a normal home connection. Cloud and datacentre ranges are refused
# by YouTube's bot check regardless of how slowly you go.
#
#   ./pull_channel.sh                       # priority set, 20 max, 4s apart
#   ./pull_channel.sh --limit 5             # smaller bite
#   ./pull_channel.sh --cookies-from-browser chrome
#   ./pull_channel.sh --status              # show manifest state, pull nothing
#
# If the run reports "bot_check", cookies are not optional — pass
# --cookies-from-browser with a browser that is logged in to YouTube.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"

if ! command -v yt-dlp >/dev/null 2>&1 && [ ! -x "$HERE/yt-dlp" ]; then
  echo "yt-dlp not found. Install with:  pipx install yt-dlp   (or brew install yt-dlp)" >&2
  exit 1
fi

[ -f "$ROOT/manifest.json" ] || python3 "$HERE/build_manifest.py"

python3 "$HERE/pull_captions.py" "$@"

# Convert whatever is now on disk. Safe to re-run; it simply rewrites.
if compgen -G "$ROOT/captions/*.vtt" >/dev/null; then
  echo
  echo "Converting to timestamped text..."
  python3 "$HERE/vtt_to_text.py" "$ROOT/captions" "$ROOT/transcripts"
  echo "Primary output: $ROOT/transcripts/<video_id>.txt  (timestamped)"
fi
