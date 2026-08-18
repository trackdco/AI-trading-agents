"""Supersede + rebuild every trigger row stalecheck flags, so it can be re-adjudicated.

RUNBOOK 10d: the speculative licence holds only while every prior candidate in the window
PASSES. When one takes and fills, downstream flat-book verdicts are void. This does the whole
withdrawal mechanically - flag the row with its reason, delete the stale briefing, rebuild it
from the run's own book via buildwin/mkps - and prints what needs re-spawning.

usage: refresh.py <run>
"""
import json, os, subprocess, sys
T = "/Users/barbelldaddy/.claude/jobs/2411401a/tmp"
REPO = "/Users/barbelldaddy/AI-trading-agents"
PY = f"{REPO}/.venv/bin/python"
sys.path.insert(0, T); sys.path.insert(0, f"{REPO}/output/analysis")
import stalecheck, supersede

DN = {"2026-05-31": "2026-06-01", "2026-06-01": "2026-06-02", "2026-06-02": "2026-06-03",
      "2026-06-03": "2026-06-04", "2026-06-04": "2026-06-05", "2026-06-21": "2026-06-22",
      "2026-06-22": "2026-06-23", "2026-06-23": "2026-06-24", "2026-06-24": "2026-06-25",
      "2026-06-25": "2026-06-26"}
WK = {"LONDON": "LONDON", "NY_PRE": "NY_PRE", "NY_AM": "NY_AM"}

run = sys.argv[1]
bad = stalecheck.audit(run, stalecheck.DAYS[run])
if not bad:
    print(f"{run}: nothing stale"); sys.exit(0)

from scripts.replay_tools import book
todo = []
for sd, cid, dec, kind, det in bad:
    if kind not in ("STATE_MOVED", "FILLS_MOVED"):
        print(f"  {sd} {cid}: {kind} - not auto-refreshable, {det}"); continue
    row = next(r for r in book.read(run, sd) if r.get("row") == "trigger"
               and r.get("candidate_id") == cid and not r.get("SUPERSEDED"))
    window = row["window"]
    supersede.mark(run, sd, "SUPERSEDED_STATE_MOVED",
        (f"adjudicated under the RUNBOOK 10d speculative licence against a book state that has "
         f"since moved: {det}. The licence holds only while every prior candidate in the window "
         f"passes; it does not survive an upstream fill. Withdrawn and re-adjudicated against "
         f"state derived from {run}'s own book by mkps.py. Verdict retained above so the reviewer "
         f"can see what was withdrawn and why."),
        lambda r, c=cid: r.get("candidate_id") == c and r.get("row") == "trigger")
    bp = row.get("briefing")
    p = bp if os.path.isabs(bp) else f"{REPO}/{bp}"
    if os.path.exists(p):
        os.remove(p)
    r = subprocess.run([PY, f"{T}/buildwin.py", run, sd, DN[sd], window,
                        f"{T}/th_{run}_{sd}_{window}_inforce.json", "--only", cid, "--force"],
                       cwd=REPO, capture_output=True, text=True)
    ok = os.path.exists(p)
    print(f"  {sd} {cid} @{dec}: superseded, briefing {'REBUILT' if ok else 'REBUILD FAILED'}")
    if not ok:
        print("    " + (r.stderr or r.stdout).strip()[-300:])
    else:
        todo.append(os.path.basename(p))
print("\nRE-SPAWN these briefings:")
for t in todo:
    print("  " + t)
