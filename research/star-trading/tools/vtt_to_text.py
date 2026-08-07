#!/usr/bin/env python3
"""Convert YouTube VTT captions to text, KEEPING TIMESTAMPS.

The timestamped form is the primary output. The extraction schema requires a
timestamp on every quoted rule and every discretion marker, so a conversion that
drops them has to be redone from the VTT — which is exactly what happened on the
first pass. Flowing prose is emitted too, as a secondary convenience.

Outputs, per video:
  transcripts/<id>.txt        [MM:SS] prefixed lines   <- PRIMARY, feed this to extraction
  transcripts/<id>.plain.txt  wrapped prose, no stamps  <- secondary, for reading

Usage:
  python3 vtt_to_text.py <captions_dir> <transcripts_dir>
"""
from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path

TAG_RE = re.compile(r"<[^>]+>")
CUE_RE = re.compile(r"^(\d{2}):(\d{2}):(\d{2})\.\d{3}\s+-->")
SKIP_PREFIX = ("Kind:", "Language:", "NOTE", "STYLE", "REGION")


def parse(path: Path) -> list[tuple[str, str]]:
    """Return [(mm:ss, line)]. YouTube auto-captions roll — each cue repeats the
    tail of the one before — so consecutive duplicate lines are dropped, keeping
    the first occurrence and therefore the earliest timestamp for that text."""
    stamped: list[tuple[str, str]] = []
    cur = "00:00"
    prev = None
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        m = CUE_RE.match(line)
        if m:
            h, mm, s = int(m.group(1)), int(m.group(2)), int(m.group(3))
            cur = f"{h * 60 + mm:02d}:{s:02d}"
            continue
        if not line or line == "WEBVTT" or line.startswith(SKIP_PREFIX) or line.isdigit():
            continue
        line = TAG_RE.sub("", line).strip()
        line = (line.replace("&nbsp;", " ").replace("&amp;", "&")
                    .replace("&gt;", ">").replace("&lt;", "<").replace("&#39;", "'"))
        if not line or line == prev:
            continue
        prev = line
        stamped.append((cur, line))
    return stamped


def merge(stamped: list[tuple[str, str]]) -> list[tuple[str, list[str]]]:
    """Group consecutive lines sharing a timestamp into one block."""
    blocks: list[tuple[str, list[str]]] = []
    for ts, ln in stamped:
        if blocks and blocks[-1][0] == ts:
            blocks[-1][1].append(ln)
        else:
            blocks.append((ts, [ln]))
    return blocks


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    dst.mkdir(parents=True, exist_ok=True)

    vtts = sorted(src.glob("*.vtt"))
    if not vtts:
        sys.exit(f"No .vtt files in {src}")

    for vtt in vtts:
        vid = vtt.name.split(".")[0]
        stamped = parse(vtt)
        if not stamped:
            print(f"  {vid}: EMPTY caption track — skipped")
            continue

        with (dst / f"{vid}.txt").open("w", encoding="utf-8") as fh:
            for ts, lns in merge(stamped):
                fh.write(f"[{ts}] {' '.join(lns)}\n")

        prose = re.sub(r"\s+", " ", " ".join(l for _, l in stamped)).strip()
        (dst / f"{vid}.plain.txt").write_text(
            "\n".join(textwrap.wrap(prose, width=100)) + "\n", encoding="utf-8")

        mins = stamped[-1][0]
        print(f"  {vid}: {len(stamped):5d} lines, runs to {mins}")

    print(f"\n{len(vtts)} file(s) -> {dst}  (primary = <id>.txt, timestamped)")


if __name__ == "__main__":
    main()
