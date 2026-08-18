"""Find live trigger rows whose briefing described a position state the book no longer agrees with.

RUNBOOK 10d licenses speculative parallel adjudication only while every prior candidate in the
window PASSES. The moment one takes and fills, every downstream verdict built against a flat
book is void. Tracking that by hand is exactly what went wrong in wr1 - four superseded
briefings from state that had moved.

This compares, for every live trigger row, the position_state the BRIEFING carried against what
mkps.py derives from the book NOW at that same decision minute. A disagreement means the row was
adjudicated against state that has since changed and must be superseded and re-run.

usage: stalecheck.py <run> [sd ...]
"""
import json, os, sys

T = "/Users/barbelldaddy/.claude/jobs/2411401a/tmp"
REPO = "/Users/barbelldaddy/AI-trading-agents"
sys.path.insert(0, T); sys.path.insert(0, f"{REPO}/output/analysis"); sys.path.insert(0, REPO)
import mkps
from scripts.replay_tools import book

DAYS = {"wr2": ["2026-06-21", "2026-06-22", "2026-06-23", "2026-06-24", "2026-06-25"],
        "jr1": ["2026-05-31", "2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04"]}


def audit(run, days):
    bad = []
    for sd in days:
        rows = book.read(run, sd)
        for r in rows:
            if r.get("row") != "trigger" or r.get("SUPERSEDED"):
                continue
            cid, window = r.get("candidate_id"), r.get("window")
            dec = str(r.get("decision_minute"))[-5:]
            bp = r.get("briefing") or ""
            p = bp if os.path.isabs(bp) else f"{REPO}/{bp}"
            if not os.path.exists(p):
                bad.append((sd, cid, dec, "BRIEFING_MISSING", bp)); continue
            try:
                b = json.load(open(p))
            except Exception as e:
                bad.append((sd, cid, dec, "BRIEFING_UNREADABLE", str(e))); continue
            said = b.get("position_state") or {}
            said_state = str(said.get("state", "")).upper()
            said_fills = said.get("fills_this_window")
            now = mkps.build(run, sd, window, dec)
            if said_state and said_state != now["state"]:
                bad.append((sd, cid, dec, "STATE_MOVED",
                            f"briefing said {said_state}, book now says {now['state']}"))
            elif said_fills is not None and said_fills != now["fills_this_window"]:
                bad.append((sd, cid, dec, "FILLS_MOVED",
                            f"briefing said {said_fills} fill(s), book now says "
                            f"{now['fills_this_window']}"))
    return bad


if __name__ == "__main__":
    run = sys.argv[1]
    days = sys.argv[2:] or DAYS.get(run, [])
    bad = audit(run, days)
    print(f"stalecheck {run}: {len(bad)} row(s) adjudicated against state the book has since moved")
    for sd, cid, dec, kind, det in bad:
        print(f"  {sd} {cid} @{dec}  {kind}: {det}")
