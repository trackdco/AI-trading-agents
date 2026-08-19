#!/usr/bin/env python3
"""Bulk-fetch a YouTube channel's transcripts to disk, resumably.

Written because the audit bottleneck is context, not access: fifty transcripts will
not fit in a model's window, so they have to land on disk and be searched
programmatically. The MCP transcript tool returns straight into context and is fine
for three videos and useless for four hundred.

BACKEND: yt-dlp, NOT youtube-transcript-api. That is the whole reason this works.
`youtube-transcript-api` hits the timedtext endpoint directly, which rate-limits by
IP and blocks datacenter ranges hard: on this host it returned `IpBlocked` after
about 42 videos and stayed blocked, and slowing the pace to one request every two
seconds did not help because the block is a cooldown, not a rate window. yt-dlp
fetches captions through the player response instead, and that path was never
blocked — the same host that could not get video 43 pulled a 43-minute masterclass
in under a second. Do not "simplify" this back to the API.

Resumable on purpose: every call skips what is already on disk, so an interrupted
run costs nothing and coverage accumulates across passes.

    python scripts/fetch_channel_transcripts.py @DodgysDD --limit 200

Writes one JSON per video to data/transcripts/<channel>/<video_id>.json and an
index.jsonl with id, title, duration and status.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CUE = re.compile(r"(\d\d:\d\d:\d\d\.\d\d\d) --> .*?\n(.*?)(?=\n\n|\Z)", re.DOTALL)
TAG = re.compile(r"<[^>]+>")


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


def parse_vtt(path: Path) -> list[dict]:
    """VTT -> [{t, x}], de-rolled.

    YouTube's auto-captions roll: each cue repeats the previous line and appends a few
    new words, so a 43-minute video yields 2,659 cues carrying 1,330 distinct lines.
    Concatenating the cues naively doubles the text and wrecks any downstream
    frequency or quote matching. Inline karaoke tags (<00:00:01.234><c>) are stripped
    and a line identical to the one before it is dropped.
    """
    raw = path.read_text(encoding="utf-8", errors="replace")
    out: list[dict] = []
    last = None
    for ts, body in CUE.findall(raw):
        for line in body.split("\n"):
            t = TAG.sub("", line).strip()
            if not t or t == last:
                continue
            h, m, s = ts.split(":")
            out.append({"t": round(int(h) * 3600 + int(m) * 60 + float(s), 1), "x": t})
            last = t
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("handle")
    ap.add_argument("--limit", type=int, default=0, help="max NEW fetches this run")
    ap.add_argument("--batch", type=int, default=60, help="videos per yt-dlp invocation")
    a = ap.parse_args()

    slug = a.handle.lstrip("@").lower()
    outdir = ROOT / "data/transcripts" / slug
    outdir.mkdir(parents=True, exist_ok=True)
    index_path = outdir / "index.jsonl"

    have = {p.stem for p in outdir.glob("*.json") if p.stem != "index"}
    vids = enumerate_videos(a.handle)
    print(f"{a.handle}: {len(vids):,} videos in /videos · {len(have):,} on disk", flush=True)

    todo = [v for v in vids if v["video_id"] not in have]
    if a.limit:
        todo = todo[:a.limit]
    print(f"  fetching {len(todo):,}", flush=True)

    meta = {v["video_id"]: v for v in vids}
    got = 0
    with index_path.open("a") as idx:
        for i in range(0, len(todo), a.batch):
            chunk = todo[i:i + a.batch]
            tmp = Path(tempfile.mkdtemp())
            try:
                subprocess.run(
                    ["yt-dlp", "--skip-download", "--write-auto-sub", "--write-sub",
                     "--sub-lang", "en", "--sub-format", "vtt", "--ignore-errors",
                     "--no-warnings", "--sleep-requests", "0.3",
                     "-o", str(tmp / "%(id)s"),
                     *[f"https://www.youtube.com/watch?v={v['video_id']}" for v in chunk]],
                    capture_output=True, text=True, timeout=1800)
                for vtt in sorted(tmp.glob("*.vtt")):
                    vid = vtt.name.split(".")[0]
                    segs = parse_vtt(vtt)
                    if not segs:
                        continue
                    v = meta.get(vid, {"video_id": vid, "title": "", "duration": None})
                    text = " ".join(s["x"] for s in segs)
                    (outdir / f"{vid}.json").write_text(json.dumps(
                        {**v, "text": text, "segments": segs}))
                    idx.write(json.dumps({**v, "status": "ok", "chars": len(text)}) + "\n")
                    got += 1
                idx.flush()
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
            print(f"  {min(i + a.batch, len(todo)):,}/{len(todo):,} · {got:,} ok", flush=True)

    tot = len([p for p in outdir.glob("*.json") if p.stem != "index"])
    print(f"\nfetched {got:,} this run · {tot:,} on disk -> {outdir}", flush=True)


if __name__ == "__main__":
    main()
