#!/usr/bin/env python3
"""Bulk-fetch a YouTube channel's transcripts to disk, resumably.

Written because the audit bottleneck is context, not access: fifty transcripts will
not fit in a model's window, so they have to land on disk and be searched
programmatically. The MCP transcript tool returns straight into context and is fine
for three videos and useless for four hundred.

Resumable on purpose. YouTube throttles, the run will be interrupted, and refetching
what is already on disk wastes the rate limit that is the actual scarce resource —
so every call skips what it already has and only reports what is genuinely missing.

    python scripts/fetch_channel_transcripts.py @DodgysDD --limit 200

Writes one JSON per video to data/transcripts/<channel>/<video_id>.json and an
index.jsonl with id, title, duration and fetch status. A video with captions
disabled is recorded as a permanent failure so later runs do not retry it forever.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PERMANENT = ("TranscriptsDisabled", "NoTranscriptFound", "VideoUnavailable",
             "NotTranslatable", "AgeRestricted")


def enumerate_videos(handle: str) -> list[dict]:
    """Channel video list via yt-dlp --flat-playlist (no media downloaded)."""
    url = f"https://www.youtube.com/{handle}/videos"
    out = subprocess.run(
        ["yt-dlp", "--flat-playlist", "--print", "%(id)s\t%(duration)s\t%(title)s", url],
        capture_output=True, text=True, timeout=900)
    rows = []
    for line in out.stdout.splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 3:
            dur = None
            try:
                dur = int(float(parts[1]))
            except (TypeError, ValueError):
                pass
            rows.append({"video_id": parts[0], "duration": dur, "title": parts[2]})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("handle")
    ap.add_argument("--limit", type=int, default=0, help="max NEW fetches this run")
    ap.add_argument("--pace", type=float, default=0.4)
    ap.add_argument("--max-duration", type=int, default=0,
                    help="skip videos longer than this many seconds (0 = keep all)")
    a = ap.parse_args()

    from youtube_transcript_api import YouTubeTranscriptApi

    slug = a.handle.lstrip("@").lower()
    outdir = ROOT / "data/transcripts" / slug
    outdir.mkdir(parents=True, exist_ok=True)
    index_path = outdir / "index.jsonl"

    known = {}
    if index_path.exists():
        for line in index_path.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                known[r["video_id"]] = r

    vids = enumerate_videos(a.handle)
    print(f"{a.handle}: {len(vids):,} videos in /videos", flush=True)
    if a.max_duration:
        vids = [v for v in vids if not v["duration"] or v["duration"] <= a.max_duration]
        print(f"  {len(vids):,} within {a.max_duration}s", flush=True)

    todo = [v for v in vids
            if v["video_id"] not in known
            or known[v["video_id"]].get("status") == "retryable"]
    print(f"  {len(known):,} already on disk · {len(todo):,} to fetch", flush=True)
    if a.limit:
        todo = todo[:a.limit]

    api = YouTubeTranscriptApi()
    done = ok = 0
    with index_path.open("a") as idx:
        for v in todo:
            vid = v["video_id"]
            time.sleep(a.pace)
            rec = {**v}
            try:
                t = api.fetch(vid)
                text = " ".join(s.text for s in t.snippets)
                (outdir / f"{vid}.json").write_text(json.dumps({
                    **v, "text": text,
                    "segments": [{"t": round(s.start, 1), "x": s.text} for s in t.snippets],
                }))
                rec["status"] = "ok"
                rec["chars"] = len(text)
                ok += 1
            except Exception as e:
                name = type(e).__name__
                # a video with captions off will never have captions; retrying it every
                # run burns the rate limit that decides how much of the channel we get
                rec["status"] = "permanent" if any(p in name for p in PERMANENT) else "retryable"
                rec["error"] = name
            idx.write(json.dumps(rec) + "\n")
            idx.flush()
            done += 1
            if done % 25 == 0:
                print(f"  {done}/{len(todo)} · {ok} ok", flush=True)

    print(f"\nfetched {ok}/{done} this run", flush=True)
    tot = sum(1 for p in outdir.glob("*.json") if p.name != "index.jsonl")
    print(f"transcripts on disk: {tot:,}  ->  {outdir}", flush=True)


if __name__ == "__main__":
    main()
