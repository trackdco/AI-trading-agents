#!/usr/bin/env python3
"""Convert YouTube auto-subtitle .vtt files into clean markdown transcripts.

Auto-subs are rolling two-line captions with heavy duplication; this dedups
them into flowing text with a [mm:ss] marker roughly every 30 seconds, so the
transcript is quotable and searchable in the research vault.

    python -m scripts.yt_transcript research/transcripts/orochi
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

TAG = re.compile(r"<[^>]+>")
STAMP = re.compile(r"(\d+):(\d+):(\d+)\.\d+ --> ")


def convert(vtt: Path) -> str:
    lines, last, out, t_mark, cur_t = vtt.read_text(errors="ignore").splitlines(), "", [], -999, 0
    for ln in lines:
        m = STAMP.match(ln)
        if m:
            cur_t = int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3])
            continue
        if "-->" in ln or ln.strip().isdigit() or ln.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        txt = TAG.sub("", ln).strip()
        if not txt or txt == last:
            continue
        # rolling captions repeat the previous line as their first line — drop overlaps
        if last and (txt in last or last in txt):
            last = max(txt, last, key=len)
            if out and out[-1].rstrip("\n").endswith(min(txt, last, key=len)):
                continue
        if cur_t - t_mark >= 30:
            out.append(f"\n\n[{cur_t // 60:02d}:{cur_t % 60:02d}] ")
            t_mark = cur_t
        out.append(txt + " ")
        last = txt
    return "".join(out).strip()


def main() -> None:
    d = Path(sys.argv[1] if len(sys.argv) > 1 else "research/transcripts/orochi")
    for vtt in sorted(d.glob("*.vtt")):
        md = d / (vtt.stem.replace(".en", "") + ".md")
        md.write_text(convert(vtt) + "\n")
        print(f"{md.name}: {len(md.read_text().split())} words")


if __name__ == "__main__":
    main()
