"""Which candidates has the run NOT adjudicated yet? want-vs-have over the deterministic id map.

Three verdicts in this batch were returned by an agent and never written to the book - they
arrive in notification batches and one gets dropped while the others are being logged. Prose
tracking does not catch that; comparing the candidate list against the book does.

usage: complete.py <run> [window]
"""
import json, sys
T = "/Users/barbelldaddy/.claude/jobs/2411401a/tmp"
sys.path.insert(0, T); sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
from buildwin import cid_map
from scripts.replay_tools import book

DAYS = {"wr2": ["2026-06-21", "2026-06-22", "2026-06-23", "2026-06-24", "2026-06-25"],
        "jr1": ["2026-05-31", "2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04"]}
run = sys.argv[1]
only_w = sys.argv[2] if len(sys.argv) > 2 else None
grand_missing = 0
for sd in DAYS[run]:
    cm = cid_map(sd)
    rows = book.read(run, sd)
    have = {r.get("candidate_id") for r in rows
            if r.get("row") in ("trigger", "gate_refusal") and not r.get("SUPERSEDED")}
    for w in ("LONDON", "NY_PRE", "NY_AM"):
        if only_w and w != only_w:
            continue
        want = {cid: dec for dec, (cid, c) in cm.items() if c["window"] == w}
        miss = {cid: dec for cid, dec in want.items() if cid not in have}
        if miss:
            grand_missing += len(miss)
            print(f"  {sd} {w}: {len(want)-len(miss)}/{len(want)} done, MISSING "
                  + ", ".join(f"{c}@{d}" for c, d in sorted(miss.items(), key=lambda x: x[1])))
print(f"{run}: {grand_missing} candidate(s) not yet in the book"
      + (f" (window {only_w})" if only_w else ""))
