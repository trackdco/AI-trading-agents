#!/usr/bin/env python3
"""Polite, resumable caption puller for the Star Trading channel.

Design notes, because the obvious implementation is the wrong one:

  * Rate limiting is answered by going slower, not by retrying harder. There is
    a fixed sleep between videos, exponential backoff after a failure, and a
    hard stop after N consecutive failures. Hammering a 429 deepens the block.
  * Every result is committed to the manifest immediately and atomically, so a
    killed run loses at most the video currently in flight.
  * A run is capped (default 20 videos). Sweeping 117 in one pass is what got
    the IP flagged in the first place.

Usage
  python3 pull_captions.py                      # pull the priority set, cap 20
  python3 pull_captions.py --limit 5            # smaller bite
  python3 pull_captions.py --cookies-from-browser chrome
  python3 pull_captions.py --all                # beyond the priority set
  python3 pull_captions.py --status             # print manifest state, pull nothing
  python3 pull_captions.py --retry-failed       # re-queue previous failures
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MANIFEST = ROOT / "manifest.json"
CAPTIONS = ROOT / "captions"

# Terminal states — never re-attempted unless explicitly asked.
DONE = {"downloaded", "no_captions"}


# --------------------------------------------------------------------------
# manifest
# --------------------------------------------------------------------------
def load_manifest() -> dict:
    if not MANIFEST.exists():
        sys.exit(f"No manifest at {MANIFEST}. Run build_manifest.py first.")
    return json.loads(MANIFEST.read_text())


def save_manifest(m: dict) -> None:
    """Atomic: write beside the target, then rename. A crash mid-write leaves
    the previous manifest intact rather than a truncated one."""
    m["updated_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    tmp = MANIFEST.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(m, indent=1, sort_keys=False) + "\n")
    os.replace(tmp, MANIFEST)


# --------------------------------------------------------------------------
# yt-dlp
# --------------------------------------------------------------------------
def find_ytdlp() -> str:
    for cand in (shutil.which("yt-dlp"), str(HERE / "yt-dlp"), str(ROOT / "yt-dlp")):
        if cand and Path(cand).exists():
            return cand
    sys.exit("yt-dlp not found. Install it (pipx install yt-dlp) or drop the "
             "standalone binary next to this script.")


def classify(stderr: str, wrote_any: bool) -> tuple[str, str]:
    """Map yt-dlp output to (status, short_reason). Order matters: the bot check
    is reported alongside a 429, and it is the more actionable of the two."""
    s = stderr.lower()
    if "sign in to confirm you" in s and "bot" in s:
        return "failed", "bot_check: YouTube demands cookies for this IP"
    if "429" in s or "too many requests" in s:
        return "failed", "rate_limited: HTTP 429"
    if "video unavailable" in s or "private video" in s or "has been removed" in s:
        return "failed", "unavailable: video private/removed"
    if "no subtitles" in s or "there are no subtitles" in s:
        return "no_captions", "no caption track published"
    if wrote_any:
        return "downloaded", ""
    return "failed", "unknown: no captions written and no recognised error"


def caption_kind(path: Path) -> str:
    """Auto-generated YouTube VTTs carry inline <00:00:01.234> timing tags and
    <c> spans inside cue text; manual subtitle tracks do not. Cheaper and more
    reliable than a second request to ask which track we got."""
    head = path.read_text(encoding="utf-8", errors="replace")[:20000]
    return "auto" if re.search(r"<\d{2}:\d{2}:\d{2}\.\d{3}>|<c>", head) else "manual"


def fetch_one(ytdlp: str, vid: str, cookies: str | None,
              req_sleep: float) -> tuple[str, str, str, str]:
    """Returns (status, reason, caption_type, upload_date)."""
    CAPTIONS.mkdir(parents=True, exist_ok=True)
    before = set(CAPTIONS.glob(f"{vid}*"))

    cmd = [
        ytdlp, "--skip-download",
        # Ask for manual and auto in ONE request. Preference is resolved after
        # the fact by inspecting the file, not by making a second call.
        "--write-subs", "--write-auto-subs",
        "--sub-langs", "en.*", "--sub-format", "vtt",
        "--write-description",
        "--sleep-requests", str(req_sleep),
        # yt-dlp's own retries stay low; our backoff loop is the real control.
        "--retries", "2", "--extractor-retries", "1",
        "--no-warnings", "--no-progress",
        # Caption files are named by id alone so the manifest lookup stays
        # trivial, which loses the upload date the old template carried. Capture
        # it to a sidecar instead of paying a second request for it later.
        "--print-to-file", "%(upload_date)s", str(CAPTIONS / "%(id)s.date"),
        "-o", str(CAPTIONS / "%(id)s"),
        f"https://www.youtube.com/watch?v={vid}",
    ]
    if cookies:
        cmd[1:1] = ["--cookies-from-browser", cookies]

    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        err = (p.stderr or "") + (p.stdout or "")
    except subprocess.TimeoutExpired:
        return "failed", "timeout: no response in 300s", "", ""

    datef = CAPTIONS / f"{vid}.date"
    upload_date = ""
    if datef.exists():
        upload_date = datef.read_text().strip()
        datef.unlink(missing_ok=True)

    new = sorted(set(CAPTIONS.glob(f"{vid}*")) - before)
    vtts = [f for f in new if f.suffix == ".vtt"]
    status, reason = classify(err, bool(vtts))

    ctype = ""
    if vtts:
        # Prefer a manual track when both landed; drop the redundant auto file.
        kinds = {f: caption_kind(f) for f in vtts}
        manual = [f for f, k in kinds.items() if k == "manual"]
        keep = manual[0] if manual else vtts[0]
        ctype = "manual" if manual else "auto"
        for f in vtts:
            if f != keep:
                f.unlink(missing_ok=True)
        keep.rename(CAPTIONS / f"{vid}.en.vtt")
    return status, reason, ctype, upload_date


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=20, help="max videos this run (default 20)")
    ap.add_argument("--sleep", type=float, default=4.0, help="seconds between videos (default 4)")
    ap.add_argument("--cookies-from-browser", dest="cookies", default=None,
                    help="chrome | firefox | safari | edge — needed if the diagnosis is a bot check")
    ap.add_argument("--all", action="store_true", help="go beyond the priority set")
    ap.add_argument("--retry-failed", action="store_true", help="re-queue previously failed videos")
    ap.add_argument("--max-consecutive-failures", type=int, default=3)
    ap.add_argument("--status", action="store_true", help="print state and exit")
    args = ap.parse_args()

    man = load_manifest()
    vids = man["videos"]

    if args.status:
        report(man)
        return

    ytdlp = find_ytdlp()

    def eligible(v):
        if v["status"] in DONE:
            return False
        if v["status"] == "failed" and not args.retry_failed:
            return False
        if not args.all and v.get("priority_rank") is None:
            return False
        return True

    queue = [v for v in vids if eligible(v)]
    queue.sort(key=lambda v: (v.get("priority_rank") or 10**6, -v.get("duration_s", 0)))
    queue = queue[: args.limit]

    if not queue:
        print("Nothing to do — every eligible video is already downloaded.")
        report(man)
        return

    print(f"Queued {len(queue)} video(s). Sleep {args.sleep}s between, "
          f"stop after {args.max_consecutive_failures} consecutive failures.")
    print(f"Cookies: {args.cookies or 'NONE (add --cookies-from-browser if bot-checked)'}\n")

    consecutive = 0
    backoff = args.sleep
    counts = {"downloaded": 0, "failed": 0, "no_captions": 0}

    for i, v in enumerate(queue, 1):
        vid = v["video_id"]
        print(f"[{i}/{len(queue)}] {vid}  {v['title'][:56]}", flush=True)

        status, reason, ctype, up = fetch_one(ytdlp, vid, args.cookies, min(args.sleep, 3.0))

        v["status"] = status
        v["attempts"] = v.get("attempts", 0) + 1
        v["last_attempt_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        v["last_error"] = reason
        if ctype:
            v["caption_type"] = ctype
        if up and up != "NA":
            v["upload_date"] = up
        save_manifest(man)          # commit before sleeping — a kill loses nothing
        counts[status] = counts.get(status, 0) + 1

        if status == "downloaded":
            print(f"      OK ({ctype} captions)")
            consecutive = 0
            backoff = args.sleep
        else:
            print(f"      {status.upper()}: {reason}")
            consecutive += 1
            if consecutive >= args.max_consecutive_failures:
                print(f"\nSTOPPING: {consecutive} consecutive failures. "
                      f"Continuing would deepen the block, not clear it.")
                if "bot_check" in reason:
                    print("Diagnosis is a bot check — re-run with "
                          "--cookies-from-browser chrome from a logged-in browser.")
                break
            backoff = min(backoff * 2, 300)     # exponential, capped at 5 min
            print(f"      backing off {backoff:.0f}s")

        if i < len(queue):
            time.sleep(backoff + random.uniform(0, 1.5))   # jitter avoids a fixed cadence

    print(f"\nThis run: {counts.get('downloaded',0)} downloaded, "
          f"{counts.get('failed',0)} failed, {counts.get('no_captions',0)} no captions.")
    report(man)


def report(man: dict) -> None:
    vids = man["videos"]
    tally: dict[str, int] = {}
    for v in vids:
        tally[v["status"]] = tally.get(v["status"], 0) + 1
    print("\nMANIFEST STATE")
    for k in ("downloaded", "pending", "failed", "no_captions"):
        if k in tally:
            print(f"  {k:12s} {tally[k]:4d}")
    print(f"  {'TOTAL':12s} {len(vids):4d}")

    prio = sorted([v for v in vids if v.get("priority_rank") is not None],
                  key=lambda v: v["priority_rank"])
    got = [v for v in prio if v["status"] == "downloaded"]
    print(f"\nPRIORITY SET: {len(got)}/{len(prio)} held")
    missing = [v for v in prio if v["status"] != "downloaded"]
    if missing:
        print("  still missing:")
        for v in missing:
            print(f"    #{v['priority_rank']:<3} {v['video_id']}  {v['title'][:52]}"
                  f"   [{v['status']}]")


if __name__ == "__main__":
    main()
