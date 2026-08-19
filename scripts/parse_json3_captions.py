#!/usr/bin/env python3
"""Parse yt-dlp json3 auto-captions into de-duplicated, timestamped lines.

json3 rather than VTT on purpose. YouTube auto-caption VTT is ROLLING -- each cue
repeats the tail of the previous one, so a naive read inflates the corpus roughly
2x (2,659 cues -> 1,330 distinct lines on the last channel pass). json3 carries the
same text as discrete timed segments with no roll, so the de-duplication is exact
rather than heuristic.

It still needs cleaning: json3 emits one event per WORD at high cadence, so events
are re-agglomerated into sentence-ish lines on a pause threshold.

    python scripts/parse_json3_captions.py <in.json3> <out.jsonl> [--gap-ms 1200]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def parse(path: Path, gap_ms: int = 1200) -> list[dict]:
    doc = json.loads(path.read_text())
    words: list[tuple[int, str]] = []
    for ev in doc.get("events", []):
        t = ev.get("tStartMs")
        if t is None or "segs" not in ev:
            continue
        for seg in ev["segs"]:
            txt = seg.get("utf8", "")
            if not txt.strip():
                continue
            words.append((t + seg.get("tOffsetMs", 0), txt))
    words.sort(key=lambda w: w[0])

    # Re-agglomerate word events into lines on a pause threshold.
    lines: list[dict] = []
    buf, start, last = [], None, None
    for t, txt in words:
        if start is None:
            start = t
        elif last is not None and t - last > gap_ms:
            lines.append({"t_ms": start, "text": "".join(buf).strip()})
            buf, start = [], t
        buf.append(txt)
        last = t
    if buf:
        lines.append({"t_ms": start, "text": "".join(buf).strip()})
    return [ln for ln in lines if ln["text"]]


def hhmmss(ms: int) -> str:
    s, ms = divmod(int(ms), 1000)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def main() -> None:
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    gap = int(sys.argv[sys.argv.index("--gap-ms") + 1]) if "--gap-ms" in sys.argv else 1200
    lines = parse(src, gap)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("w") as fh:
        for ln in lines:
            ln["ts"] = hhmmss(ln["t_ms"])
            fh.write(json.dumps(ln) + "\n")
    words = sum(len(ln["text"].split()) for ln in lines)
    dur = hhmmss(lines[-1]["t_ms"]) if lines else "00:00:00"
    print(f"{src.name}: {len(lines):,} lines · {words:,} words · runs to {dur} · -> {dst}")


if __name__ == "__main__":
    main()
