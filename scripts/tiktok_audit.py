#!/usr/bin/env python3
"""TikTok account audit — enumerate an account and cache its captions for grepping.

ANGUS 2026-08-05: *"are you able to audit tiktok accounts per chance"*. Yes.

WHY THIS EXISTS. YouTube transcript retrieval is IP-blocked from this cloud host, and it
is blocked at the network level rather than in one library: `youtube-transcript-api`
returns RequestBlocked, and `yt-dlp` — a completely independent code path — returns
"Sign in to confirm you're not a bot". Two libraries, one wall. TikTok is not blocked.

TWO ENVIRONMENT GOTCHAS, both burned in getting this working:

  1. DO NOT install `curl-cffi`. yt-dlp will then attempt TLS impersonation, which the
     agent proxy resets ("curl: (35) Recv failure"). The plain urllib path works because
     it honours the proxy's CA bundle. Impersonation is not needed for TikTok.
  2. The default 20s socket timeout is too short through the proxy — the first attempt
     read-timed-out on a page that later fetched fine. Use --socket-timeout 90.

Output mirrors the YouTube cache layout so the same greps work across both corpora:

    research/tiktok/<handle>/index.json     video list with ids, titles, durations
    research/tiktok/<handle>/<video_id>.vtt captions, timestamped

    python -m scripts.tiktok_audit @someaccount --limit 40
    python -m scripts.tiktok_audit @someaccount --index-only
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research/tiktok"
YTDLP = [sys.executable, "-m", "yt_dlp", "--socket-timeout", "90", "--retries", "3"]


def run(args: list[str], timeout: int = 300) -> tuple[int, str]:
    p = subprocess.run(YTDLP + args, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout + p.stderr


def index(handle: str, limit: int) -> list[dict]:
    """Enumerate WITHOUT downloading — cheap, and lets us pick before spending requests."""
    code, out = run(["--flat-playlist", "--playlist-end", str(limit),
                     "--print", "%(id)s\t%(title)s\t%(duration)s",
                     f"https://www.tiktok.com/{handle}"])
    vids = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0].isdigit():
            vids.append({"id": parts[0], "title": parts[1],
                         "duration": parts[2] if len(parts) > 2 else ""})
    if not vids and code != 0:
        print(out[-600:], file=sys.stderr)
    return vids


def captions(handle: str, vid: str, dest: Path) -> bool:
    if (dest / f"{vid}.eng-US.vtt").exists():
        return True
    code, out = run(["--skip-download", "--write-subs", "--write-auto-subs",
                     "--sub-langs", "eng-US,en.*", "--sub-format", "vtt",
                     "-o", str(dest / "%(id)s.%(ext)s"),
                     f"https://www.tiktok.com/{handle}/video/{vid}"])
    return any(dest.glob(f"{vid}*.vtt"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("handle", help="@account")
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--index-only", action="store_true")
    a = ap.parse_args()
    handle = a.handle if a.handle.startswith("@") else "@" + a.handle

    dest = OUT / handle.lstrip("@")
    dest.mkdir(parents=True, exist_ok=True)
    print(f"enumerating {handle} ...", flush=True)
    vids = index(handle, a.limit)
    (dest / "index.json").write_text(json.dumps(vids, indent=2))
    print(f"  {len(vids)} videos indexed -> {(dest/'index.json').relative_to(ROOT)}")
    for v in vids[:10]:
        print(f"    {v['id']}  {v['duration']:>5}s  {v['title'][:70]}")
    if a.index_only or not vids:
        return 0

    got = 0
    for i, v in enumerate(vids, 1):
        if captions(handle, v["id"], dest):
            got += 1
        if i % 10 == 0 or i == len(vids):
            print(f"  [{i}/{len(vids)}] captions cached: {got}", flush=True)
    print(f"\n{got} of {len(vids)} have captions -> {dest.relative_to(ROOT)}")
    print("grep them with:  rg -i 'absorption|delta' " + str(dest.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
