#!/usr/bin/env python3
"""VTT -> timestamped paragraph text, matching the ash10hazard transcript format.

YouTube auto-captions repeat each line as a rolling two-line window, so a naive dump
duplicates almost every word. This de-duplicates by tracking what has already been emitted
and appending only the new tail of each cue.

    python -m scripts.vtt_to_text <in_dir> <out_dir> [--ext .txt]
"""
from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

CUE = re.compile(r"^(\d{2}):(\d{2}):(\d{2})\.\d{3}\s+-->")
TAG = re.compile(r"<[^>]+>")


def parse(path: Path) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    stamp: int | None = None
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        m = CUE.match(line)
        if m:
            h, mi, s = (int(x) for x in m.groups())
            stamp = h * 3600 + mi * 60 + s
            continue
        if not line or line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
            continue
        if stamp is None:
            continue
        txt = html.unescape(TAG.sub("", line)).strip()
        if txt:
            out.append((stamp, txt))
    return out


def dedupe(cues: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Auto-caption cues overlap. Keep only the words not already emitted."""
    seen: list[str] = []
    out: list[tuple[int, str]] = []
    for ts, txt in cues:
        words = txt.split()
        # longest suffix of `seen` that prefixes `words`
        k = 0
        for n in range(min(len(seen), len(words)), 0, -1):
            if seen[-n:] == words[:n]:
                k = n
                break
        new = words[k:]
        if new:
            out.append((ts, " ".join(new)))
            seen.extend(new)
            seen = seen[-40:]
    return out


def paragraphs(cues: list[tuple[int, str]], every: int = 20) -> str:
    blocks, cur, start = [], [], None
    for ts, txt in cues:
        if start is None:
            start = ts
        cur.append(txt)
        if ts - start >= every:
            blocks.append(f"[{start//60:02d}:{start%60:02d}] " + " ".join(cur))
            cur, start = [], None
    if cur:
        blocks.append(f"[{(start or 0)//60:02d}:{(start or 0)%60:02d}] " + " ".join(cur))
    return "\n\n".join(blocks) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("in_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--ext", default=".txt")
    a = ap.parse_args()
    src, dst = Path(a.in_dir), Path(a.out_dir)
    dst.mkdir(parents=True, exist_ok=True)
    for p in sorted(src.glob("*.vtt")):
        vid = p.name.split(".")[0]
        cues = dedupe(parse(p))
        if not cues:
            print(f"  SKIP {vid} — no cues parsed")
            continue
        txt = paragraphs(cues)
        (dst / f"{vid}{a.ext}").write_text(txt)
        print(f"  {vid}  {len(cues):>4} cues  {len(txt.split()):>5} words")


if __name__ == "__main__":
    main()
