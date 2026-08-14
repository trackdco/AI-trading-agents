#!/usr/bin/env python3
"""Surface rule-bearing sentences from a transcript corpus, with citations.

The audit bottleneck is context. Half a million characters of transcript cannot be
read into a window, and skimming a sample is how you end up quoting the three videos
you happened to open. This scans everything on disk and returns only sentences that
look like RULES, each carrying its video id and timestamp so the quote can be checked.

What counts as rule-bearing: a sentence containing a domain term AND a
modal/definitional marker ("always", "never", "you want to see", "has to be", "the
rule is", "I only", "criteria"). That is a deliberately crude filter — it over-returns
and that is the right direction, because a missed rule is invisible while a spurious
one is obvious on reading.

Numbers are extracted separately. Every figure a channel states — a percentage, a
point count, a time — is a testable claim, and the ones stated once in passing are
exactly the ones a human skim loses.

    python scripts/mine_rules.py dodgysdd --term macro
    python scripts/mine_rules.py dodgysdd --numbers
"""
from __future__ import annotations

import argparse
import glob
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TERMS = [
    "ifvg", "inversion", "inverse", "fair value gap", "fvg", "order block", "breaker",
    "bpr", "macro", "liquidity", "entry", "stop", "target", "break even", "breakeven",
    "risk", "session", "swing", "displacement", "smt", "discount", "premium",
    "data high", "data low", "wick", "candle clos", "model", "setup", "confluence",
]
MARKERS = [
    "always", "never", "you want to see", "you want", "has to be", "have to",
    "must ", "the rule", "i only", "criteria", "i look for", "what i do",
    "make sure", "don't take", "do not take", "i avoid", "i skip", "requires",
    "needs to", "should be", "is when", "defined as", "i define",
]


def sentences(doc: dict):
    """Split into sentences, carrying the nearest preceding timestamp."""
    segs = doc.get("segments") or []
    text, marks = [], []
    for s in segs:
        marks.append((len("".join(text)), s["t"]))
        text.append(s["x"] + " ")
    full = "".join(text)
    for m in re.finditer(r"[^.!?]{25,400}(?:[.!?]|$)", full):
        pos = m.start()
        t = 0.0
        for off, ts in marks:
            if off <= pos:
                t = ts
            else:
                break
        yield m.group(0).strip(), t


def load(slug: str) -> list[dict]:
    d = ROOT / "data/transcripts" / slug
    return [json.load(open(f)) for f in glob.glob(str(d / "*.json"))
            if "index" not in Path(f).name]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--term", default="", help="restrict to sentences containing this")
    ap.add_argument("--numbers", action="store_true", help="stated figures instead")
    ap.add_argument("--max", type=int, default=60)
    a = ap.parse_args()

    docs = load(a.slug)
    print(f"# {len(docs)} transcripts, {sum(len(d['text']) for d in docs):,} chars\n")

    if a.numbers:
        pat = re.compile(
            r"[^.!?]{0,150}?\b(\d{1,3}(?:\.\d+)?\s?%|\d{1,3}\s?(?:points?|ticks?|"
            r"handles?)|\d{1,2}:\d{2}|\$\d[\d,]*|\b[1-9]\d?\s?(?:r|rr)\b)[^.!?]{0,150}",
            re.IGNORECASE)
        seen = set()
        for d in sorted(docs, key=lambda x: x["title"]):
            hits = []
            for sent, t in sentences(d):
                for m in pat.finditer(sent):
                    frag = " ".join(m.group(0).split())
                    k = frag.lower()[:90]
                    if k in seen:
                        continue
                    seen.add(k)
                    hits.append((t, frag))
            if hits:
                print(f"\n## {d['title']}  [{d['video_id']}]")
                for t, frag in hits[:14]:
                    print(f"  {int(t)//60:>3}:{int(t)%60:02d}  {frag[:200]}")
        return

    want = a.term.lower()
    for d in sorted(docs, key=lambda x: x["title"]):
        hits = []
        for sent, t in sentences(d):
            low = sent.lower()
            if want and want not in low:
                continue
            if not any(x in low for x in TERMS):
                continue
            if not any(mk in low for mk in MARKERS):
                continue
            hits.append((t, " ".join(sent.split())))
        if hits:
            print(f"\n## {d['title']}  [{d['video_id']}]")
            for t, s in hits[:a.max]:
                print(f"  {int(t)//60:>3}:{int(t)%60:02d}  {s[:230]}")


if __name__ == "__main__":
    main()
