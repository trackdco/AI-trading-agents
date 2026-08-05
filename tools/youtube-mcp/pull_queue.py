#!/usr/bin/env python3
"""Work a transcript queue slowly and survive YouTube's rate limiter.

A channel dive is a burst of hundreds of requests, which is exactly what YouTube
throttles — and once tripped, every client context answers "Sign in to confirm
you're not a bot" for a cooldown of unknown length. So this does not try to be
fast. It paces, backs off hard when blocked, never loses its place, and can be
killed and restarted at any time because the on-disk cache is the state.

    python tools/youtube-mcp/pull_queue.py <queue.json> [--log FILE] [--max-hours N]

queue.json: [{"video_id": ..., "title": ..., "channel": ..., "priority": ...}, ...]
Progress is appended to the log as one JSON line per video, so a later session
can reconstruct exactly what happened without re-running anything.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import server

# Escalating cooldowns. YouTube's block is measured in minutes-to-hours, so
# there is no point hammering it — each step buys a cheap retry later.
BACKOFF = [60, 180, 600, 1800, 3600]
PACE = float(server._THROTTLE_SECONDS)


def log(handle, payload: dict) -> None:
    payload["at"] = datetime.now(UTC).isoformat(timespec="seconds")
    handle.write(json.dumps(payload) + "\n")
    handle.flush()
    print(f"  {payload.get('status'):<9} {payload.get('video_id','')}  "
          f"{str(payload.get('detail',''))[:80]}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("queue")
    ap.add_argument("--log", default="output/transcript_pull.jsonl")
    ap.add_argument("--max-hours", type=float, default=12.0)
    args = ap.parse_args()

    queue = json.loads(Path(args.queue).read_text())
    queue.sort(key=lambda q: (q.get("priority", 9), -q.get("minutes", 0)))
    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    deadline = time.time() + args.max_hours * 3600
    done = skipped = failed = 0
    consecutive_blocks = 0

    with log_path.open("a") as handle:
        log(handle, {"status": "start", "detail": f"{len(queue)} queued"})
        for item in queue:
            if time.time() > deadline:
                log(handle, {"status": "timeup", "detail": f"{done} pulled this run"})
                break

            vid = item["video_id"]
            text_path, meta_path = server._cache_paths(vid)
            if text_path.exists() and meta_path.exists():
                skipped += 1
                continue

            attempt = 0
            while True:
                try:
                    cached = server._fetch_transcript(vid, ["en"], False)
                    done += 1
                    consecutive_blocks = 0
                    log(handle, {
                        "status": "ok", "video_id": vid, "priority": item.get("priority"),
                        "channel": item.get("channel"), "title": item.get("title", "")[:120],
                        "chars": len(cached.text),
                        "rule_hits": server._rule_density(cached.text),
                        "detail": f"{len(cached.text):,} chars",
                    })
                    break
                except Exception as exc:  # noqa: BLE001 - classified here
                    name = type(exc).__name__
                    blocked = name in server._BLOCKED
                    if not blocked:
                        failed += 1
                        log(handle, {"status": "nocaps", "video_id": vid,
                                     "title": item.get("title", "")[:120], "detail": name})
                        break
                    consecutive_blocks += 1
                    if attempt >= len(BACKOFF) - 1:
                        failed += 1
                        log(handle, {"status": "blocked", "video_id": vid,
                                     "detail": "gave up after full backoff"})
                        break
                    wait = BACKOFF[attempt]
                    log(handle, {"status": "cooldown", "video_id": vid,
                                 "detail": f"{name}, sleeping {wait}s "
                                           f"(streak {consecutive_blocks})"})
                    time.sleep(wait)
                    attempt += 1
            time.sleep(PACE)

        log(handle, {"status": "end",
                     "detail": f"pulled {done}, already-cached {skipped}, failed {failed}"})
    print(f"\npulled {done} | cached {skipped} | failed {failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
