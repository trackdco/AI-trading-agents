#!/usr/bin/env python3
"""Add a freshness proxy to the candidate corpus, at scale.

    python -m scripts.enrich_corpus_freshness

His hypothesis (2026-08-19): *"when it took trades on fresh levels that
hadn't been rejected before, the win rate was significantly better."*
Agent-fill receipt: fresh 62% WR / +0.69R avg vs recently-tested 53% /
+0.29R — n=64. This adds the corpus-scale test: for every candidate,
`zone_touches_session` = the number of PRIOR distinct 15-minute blocks
this session in which price came within 15pt of the candidate's price.
0-1 touches ~ his "fresh"; many touches ~ a hammered zone.

As-of by construction (only bars strictly before the decision minute).
Writes candidate_corpus_enriched.jsonl.gz and prints the headline table.
"""
from __future__ import annotations

import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.offline_briefings as OB                            # noqa: E402

TOL = 15.0

def main() -> int:
    src = ROOT / "output/analysis/candidate_corpus.jsonl.gz"
    dst = ROOT / "output/analysis/candidate_corpus_enriched.jsonl.gz"
    rows = [json.loads(l) for l in gzip.open(src, "rt")]
    byday = defaultdict(list)
    for r in rows:
        byday[r["sess_day"]].append(r)
    bars = OB.get_bars()

    out = []
    for i, (day, lst) in enumerate(sorted(byday.items())):
        t0 = pd.Timestamp(f"{day} 18:00", tz=OB.NY)
        seg = bars[(bars.index >= t0) & (bars.index < t0 + pd.Timedelta(hours=23))]
        if not len(seg):
            out.extend(lst)
            continue
        b15 = seg.resample("15min").agg({"high": "max", "low": "min"}).dropna()
        for r in lst:
            _, t = OB.session_bounds(day, r["minute"])
            px = r.get("price")
            if px is None:
                out.append(r)
                continue
            prior = b15[b15.index + pd.Timedelta(minutes=15) <= t]
            touches = int(((prior.low <= px + TOL) & (prior.high >= px - TOL)).sum())
            r["zone_touches_session"] = touches
            out.append(r)
        if i % 100 == 0:
            print(f"[{i}/{len(byday)}] {day}", flush=True)

    with gzip.open(dst, "wt") as fh:
        for r in out:
            fh.write(json.dumps(r) + "\n")

    scored = [r for r in out if r.get("mech_outcome") and "zone_touches_session" in r]
    def rate(rs):
        n = len(rs)
        return f"n={n:>5}  2R-rate={sum(1 for x in rs if x['mech_outcome']=='2R')/n:.1%}" if n else "n=0"
    print("\n=== freshness proxy at scale (prior 15m blocks touching price±15pt) ===")
    for lo, hi, lab in ((0, 1, "0-1 (fresh)"), (2, 4, "2-4"), (5, 8, "5-8"), (9, 999, "9+ (hammered)")):
        print(f"  {lab:14}", rate([r for r in scored if lo <= r["zone_touches_session"] <= hi]))
    print(f"\nDONE -> {dst}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
