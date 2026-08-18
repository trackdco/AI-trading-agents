"""Advance one manage chain by one minute: write the verdict, re-check closure, build next.

Collapses the four things that must happen between two calls in a chain, in the one order
that is safe: write the row FIRST (so the next state is derived from a book that already
contains it), then replay forward to see whether the action just written closed the
position, and only brief the next minute if it did not. A trail can close a position, so
the closure check cannot be skipped for being 'probably fine' - that is precisely the wr1
failure this run exists to remove.

usage: step.py <run> <sd> <dn> <cid> <verdict.json> <this_minute>
"""
import json, subprocess, sys
T = "/Users/barbelldaddy/.claude/jobs/2411401a/tmp"
PY = "/Users/barbelldaddy/AI-trading-agents/.venv/bin/python"
REPO = "/Users/barbelldaddy/AI-trading-agents"
sys.path.insert(0, T); sys.path.insert(0, f"{REPO}/output/analysis")

run, sd, dn, cid, vp, dec = sys.argv[1:7]

def sh(*a):
    r = subprocess.run([PY, *a], capture_output=True, text=True, cwd=REPO)
    return (r.stdout + r.stderr).strip()

print(sh(f"{T}/wrow.py", run, sd, cid, dec, vp))
alive = sh(f"{T}/alive.py", run, sd, cid)
last = alive.split("\n")[-1]
print(last)
# "CLOSED at HH:MM" alone does NOT end the chain - a position that closes at 12:40 still owes
# every scheduled call before then. The chain ends only when no scheduled minute survives
# both the close AND the minute just written.
closed_at = last.split("CLOSED at ")[1].split()[0] if "CLOSED at " in last else None

st_path = f"{T}/st_{run}_{sd}_{cid}.json"
print(sh(f"{T}/mkmng2.py", run, sd, dn, cid, "11:00", st_path).split("\n")[-2 if True else -1])
st = json.load(open(st_path))
nxt = [m for m in st["sched"] if m > dec and (closed_at is None or m <= closed_at)]
if not nxt:
    print(f"  -> no minute left after {dec}; resolve with xrow.py {run} {sd} {cid}")
    sys.exit(0)
print(sh(f"{T}/mng1.py", st_path, nxt[0]).split("\n")[-1])
print(f"NEXT: {run}_{sd}_{cid}_{nxt[0].replace(':','')}_manage.json")
