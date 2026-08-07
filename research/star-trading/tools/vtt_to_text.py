#!/usr/bin/env python3
"""Convert YouTube auto-generated VTT subtitles to clean plain-text transcripts.

Auto-caption VTTs repeat each line in overlapping cues (rolling captions).
This strips timestamps/markup and deduplicates consecutive repeats.
"""
import re
import sys
from pathlib import Path

TAG_RE = re.compile(r"<[^>]+>")
TS_LINE_RE = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3} --> ")


def vtt_to_lines(path: Path) -> list[str]:
    lines_out: list[str] = []
    prev = None
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if (not line or line == "WEBVTT" or line.startswith(("Kind:", "Language:", "NOTE"))
                or TS_LINE_RE.match(line)):
            continue
        line = TAG_RE.sub("", line).strip()
        line = line.replace("&nbsp;", " ").replace("&amp;", "&").replace("&gt;", ">").replace("&lt;", "<")
        if not line or line == prev:
            continue
        lines_out.append(line)
        prev = line
    return lines_out


def dedup_rolling(lines: list[str]) -> str:
    """Auto-captions emit each phrase twice (as the tail of one cue and head of
    the next). Keep first occurrence of consecutive duplicates, then join."""
    out: list[str] = []
    for ln in lines:
        if out and (ln == out[-1]):
            continue
        out.append(ln)
    text = " ".join(out)
    return re.sub(r"\s+", " ", text).strip()


def wrap(text: str, width: int = 100) -> str:
    import textwrap
    return "\n".join(textwrap.wrap(text, width=width))


def main(src_dir: str, out_dir: str) -> None:
    src, dst = Path(src_dir), Path(out_dir)
    dst.mkdir(parents=True, exist_ok=True)
    vtts = sorted(src.glob("*.en.vtt"))
    for vtt in vtts:
        stem = vtt.name.removesuffix(".en.vtt")
        text = dedup_rolling(vtt_to_lines(vtt))
        (dst / f"{stem}.txt").write_text(wrap(text) + "\n", encoding="utf-8")
    print(f"converted {len(vtts)} transcripts -> {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
