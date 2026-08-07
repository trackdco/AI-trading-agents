#!/usr/bin/env python3
"""Build (or refresh) manifest.json from the channel listing.

Priority set, in the order the extraction stage needs them:

  Tier A  The break-even video. It is the only known source for how a
          break-even trade is counted in a win rate, which is the highest-value
          unknown in the corpus — a "95% win rate" that excludes break-evens
          from the denominator is a different claim entirely.
  Tier B  The longest videos. Masterclasses and full breakdowns state rules
          explicitly; short videos demonstrate them and leave the rule implicit.
  Tier C  Titles carrying a backtest claim or a win-rate percentage. These hold
          the samples and the numbers the contradiction ledger is built from.

Refreshing is non-destructive: existing statuses, attempt counts and errors are
preserved. Only metadata and ranking are recomputed.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RAW = HERE / "channel_videos.raw.txt"
MANIFEST = ROOT / "manifest.json"

TIER_A = "n5TBiz17eA4"          # Why 90% of My Trades Break Even
ALREADY_HELD = "vlKZEA0x2X4"    # pulled before the block; do not re-pull
N_LONGEST = 10
N_CLAIM = 8

CLAIM_RE = re.compile(r"(\d+\s*%)|backtest|back test|1000 trades|win ?rate|winrate", re.I)


def parse_raw() -> list[dict]:
    out = []
    for line in RAW.read_text(encoding="utf-8").splitlines():
        p = line.rstrip("\n").split("|")
        if len(p) < 4 or not re.fullmatch(r"[\w-]{11}", p[0]):
            continue
        out.append({
            "video_id": p[0],
            "title": "|".join(p[1:-2]),
            "duration_s": int(p[-2]) if p[-2].isdigit() else 0,
            "views_at_pull": int(p[-1]) if p[-1].isdigit() else 0,
        })
    return out


def rank(videos: list[dict]) -> dict[str, tuple[int, str]]:
    by_dur = sorted(videos, key=lambda v: -v["duration_s"])
    taken = {TIER_A, ALREADY_HELD}

    tier_b = [v for v in by_dur if v["video_id"] not in taken][:N_LONGEST]
    taken |= {v["video_id"] for v in tier_b}

    tier_c = [v for v in by_dur
              if v["video_id"] not in taken and CLAIM_RE.search(v["title"])][:N_CLAIM]

    ordered = [(TIER_A, "A")] + [(v["video_id"], "B") for v in tier_b] \
                              + [(v["video_id"], "C") for v in tier_c]
    return {vid: (i, tier) for i, (vid, tier) in enumerate(ordered, 1)}


def main() -> None:
    videos = parse_raw()
    ranks = rank(videos)

    prior = {}
    if MANIFEST.exists():
        prior = {v["video_id"]: v for v in json.loads(MANIFEST.read_text())["videos"]}

    rows = []
    for v in videos:
        vid = v["video_id"]
        r, tier = ranks.get(vid, (None, None))
        old = prior.get(vid, {})
        held = vid == ALREADY_HELD
        rows.append({
            "video_id": vid,
            "title": v["title"],
            "duration_s": v["duration_s"],
            "views_at_pull": v["views_at_pull"],
            "priority_rank": r,
            "priority_tier": tier,
            # Preserve prior state. A refresh must never reset progress.
            "status": old.get("status", "downloaded" if held else "pending"),
            "caption_type": old.get("caption_type", "auto" if held else ""),
            "attempts": old.get("attempts", 0),
            "last_attempt_utc": old.get("last_attempt_utc", ""),
            "last_error": old.get("last_error", ""),
            "note": "pulled before the rate-limit block" if held else old.get("note", ""),
        })

    rows.sort(key=lambda v: (v["priority_rank"] or 10**6, -v["duration_s"]))

    man = {
        "channel": "https://www.youtube.com/@StarTrading-n8t",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "updated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "priority_set_size": len([r for r in rows if r["priority_rank"]]) + 1,
        "statuses": ["pending", "downloaded", "failed", "no_captions"],
        "videos": rows,
    }
    MANIFEST.write_text(json.dumps(man, indent=1) + "\n")

    n_prio = len([r for r in rows if r["priority_rank"]])
    print(f"manifest: {len(rows)} videos, priority set {n_prio} to pull + 1 held")
    for r in rows[:6]:
        if r["priority_rank"]:
            print(f"  #{r['priority_rank']:<3} [{r['priority_tier']}] {r['video_id']}  {r['title'][:52]}")


if __name__ == "__main__":
    main()
