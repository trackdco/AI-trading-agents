#!/usr/bin/env python3
"""Attach every rule in the DodgysDD catalogue to a video id + timestamp.

The catalogue in docs/RESEARCH-dodgysdd-lecture.md was built from a pasted transcript
with no provenance. This re-attaches each quote to the fetched captions so the rules
meet the same citation standard as the rest of the corpus.

Search is over a stitched per-video string with a char->timestamp index, because the
caption line breaks fall mid-sentence and a per-line regex misses most quotes.

    python scripts/dodgy_cite.py            # print the citation table
"""
from __future__ import annotations

import glob
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/transcripts/dodgysdd"

# rule id -> (label, regex). Patterns are loose because auto-captions mangle his
# vocabulary: IFVG -> "IPG"/"IFG", fair value -> "for value"/"fair rally"/"fell",
# Judas -> "Judah", data wick -> "dataix".
RULES = [
    ("ID",   "identity: DD = due diligence",       r"DD stands for due diligence"),
    ("E1",   "iFVG is the whole strategy",         r"my whole strategy and everything I do"),
    ("E1b",  "bullish iFVG definition",            r"closes? above a bearish"),
    ("E2",   "entry = market on close of break",   r"get in the second th\w+ (candle|cannon) closes"),
    ("E2b",  "does NOT wait for retracement",      r"don't actually wait for us to go back into"),
    ("E3",   "bodies tell the story",              r"bodies tell the story"),
    ("E4",   "drake candle = displacement",        r"drake candle"),
    ("E5.1", "gap must be singular",               r"(IPG|IFG|gap) must be singular|focus on singular"),
    ("E5.2", "ten-foot obviousness test",          r"back away.{0,30}(from the screen|10 feet|all the way)"),
    ("E5.4", "target must still be unswept",       r"(50|fifty) million highs"),
    ("Q1",   "sweep required before any entry",    r"one thing.{0,40}looking for before any type of entry"),
    ("Q1b",  "manipulation leg = liquidity sweep", r"manipulation leg.{0,20}liquidity sweep"),
    ("Q2",   "displacement vs prior leg size",     r"same size as the range"),
    ("Q3",   "spent levels are deleted",           r"already been ran|no more stop losses"),
    ("L1",   "equal-highs probability ladder",     r"two wicks right next to each other"),
    ("L2",   "trend line 45-degree preference",    r"45 degree|prefer trend lines"),
    ("L2b",  "more touches = stronger",            r"eight touches.{0,140}two touches"),
    ("L9",   "intermediate-term high/low",         r"intermediate term low|itth|ITL"),
    ("X1",   "trade off of a trade (HTF nest)",    r"trade off ?of ?a ?trade"),
    ("X2",   "stop anchors to the HTF zone",       r"stopped out on the one minute.{0,60}five"),
    ("T1",   "targets are highs and lows, not R",  r"targets are always highs and lows"),
    ("T1b",  "market cannot see your RR tool",     r"see your little riskreward|sees your.{0,20}risk.{0,10}reward"),
    ("T3",   "breakeven at 1R",                    r"up one R.{0,60}break even|move.{0,20}stop.{0,20}break even"),
    ("T4",   "two-loss rule",                      r"done after two losses"),
    ("T4b",  "daily lockout feature",              r"daily lockout"),
    ("S1",   "SMT is fifth in the checklist",      r"fifth in my checklist"),
    ("S1b",  "do not trade SMT religiously",       r"[Dd]o not trade this religiously"),
    ("P2",   "order block = sandwich candle",      r"sandwich"),
    ("P4",   "breaker = failed order block",       r"breaker block.{0,30}failed order block|failed order block"),
    ("K2",   "NY AM is the primary session",       r"primary session"),
    ("M1",   "macro times",                        r"macro time"),
    ("R1",   "10am is a reversal time",            r"10 a\.?m\.? (equals|is a).{0,30}reversal"),
    ("J1",   "Judas swing = false move at open",   r"[Jj]ud(as|ah|ith) swing"),
    ("F1",   "big overnight move -> choppy AM",    r"big overnight move"),
    ("F1b",  "300 points is substantial",          r"300 points is pretty substantial|300ish"),
    ("DW",   "data wick ~85% same day",            r"85% of the time you form a"),
    ("DW2",  "one setup for life",                 r"one setup for life"),
    ("P5",   "premium/discount, buy discount",     r"buy here.{0,40}short up there|premium.{0,20}discount"),
]


def load() -> dict[str, tuple[str, str, list[int]]]:
    """video id -> (display text, whitespace-stripped text, stripped-index -> t_ms).

    Auto-captions join words across cue boundaries ("Butyeah", "ofa trade"), so a
    literal regex misses roughly one quote in six. Searching a whitespace-free
    projection removes the whole class of miss; the index maps back to a timestamp.
    """
    out = {}
    for f in sorted(glob.glob(str(SRC / "*.jsonl"))):
        vid = Path(f).stem
        parts, flat, idx = [], [], []
        with open(f) as fh:
            raw = fh.readlines()
        for line in raw:
            ln = json.loads(line)
            txt = ln["text"].replace("\n", " ") + " "
            parts.append(txt)
            for ch in txt:
                if not ch.isspace():
                    flat.append(ch)
                    idx.append(ln["t_ms"])
        out[vid] = ("".join(parts), "".join(flat), idx)
    return out


def hhmmss(ms: int) -> str:
    s, ms = divmod(int(ms), 1000)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def main() -> None:
    docs = load()
    hits = miss = 0
    print(f"{'rule':6s} {'video':13s} {'ts':10s} label / quote")
    print("-" * 110)
    for rid, label, pat in RULES:
        # strip whitespace from the pattern's literal runs so it matches the flat text
        flat_pat = re.sub(r"\s+", "", pat)
        rx = re.compile(flat_pat, re.IGNORECASE)
        found = None
        for vid, (_disp, flat, idx) in docs.items():
            m = rx.search(flat)
            if m:
                found = (vid, idx[m.start()], flat[max(0, m.start() - 55):m.end() + 85])
                break
        if found:
            vid, t, quote = found
            quote = " ".join(quote.split())
            print(f"{rid:6s} {vid:13s} {hhmmss(t):10s} {label}")
            print(f"{'':31s} \"...{quote}...\"")
            hits += 1
        else:
            print(f"{rid:6s} {'--':13s} {'--':10s} {label}   *** NOT FOUND ***")
            miss += 1
    print("-" * 110)
    print(f"attached {hits}/{hits + miss} rules; {miss} unattached")


if __name__ == "__main__":
    main()
