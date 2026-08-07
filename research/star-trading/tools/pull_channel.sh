#!/usr/bin/env bash
# Pull captions + descriptions for every video on the Star Trading channel.
#
# Run this from a normal residential/home connection. Datacentre and cloud IPs
# are blocked by YouTube's bot check ("Sign in to confirm you're not a bot"),
# which is what stopped the original remote-session pull.
#
# Usage:
#   ./pull_channel.sh [output_dir]
#
# If you hit the bot check even from home, add cookies from a logged-in browser:
#   YTDLP_EXTRA="--cookies-from-browser chrome" ./pull_channel.sh
#
set -euo pipefail

CHANNEL="https://www.youtube.com/@StarTrading-n8t/videos"
OUT="${1:-captions}"
mkdir -p "$OUT"

if ! command -v yt-dlp >/dev/null 2>&1; then
  echo "yt-dlp not found. Install it: pipx install yt-dlp  (or brew install yt-dlp)" >&2
  exit 1
fi

# --sleep-requests keeps the pull under YouTube's rate limiter. Raising it is
# cheaper than getting the IP flagged and having to wait the block out.
yt-dlp \
  --skip-download \
  --write-auto-subs --write-subs --sub-langs "en" --sub-format vtt \
  --write-description \
  --sleep-requests 2 --sleep-subtitles 1 \
  --retries 10 --extractor-retries 5 \
  --ignore-errors \
  -o "$OUT/%(upload_date)s_%(id)s" \
  ${YTDLP_EXTRA:-} \
  "$CHANNEL"

echo
echo "Captions written to $OUT/"
echo "Now convert the VTT files to readable text:"
echo "  python3 $(dirname "$0")/vtt_to_text.py $OUT transcripts"
