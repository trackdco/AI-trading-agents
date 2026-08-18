"""CLI wrapper over exitrow.write - resolve one position and write its `exit` row.

Side, entry, stop, conviction, the target ladder and the full management action chain are
all read back off the run's own book, the same source mkmng2 briefs the manager from, so an
exit row can never disagree with the calls that produced it. Nothing is retyped.

usage: xrow.py <run> <sd> <cid> [--dry]
"""
import sys
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
sys.path.insert(0, "/Users/barbelldaddy/.claude/jobs/2411401a/tmp")
from scripts.replay_tools import book
import exitrow

run, sd, cid = sys.argv[1:4]
dry = "--dry" in sys.argv
rows = book.read(run, sd)
live = lambda k: [r for r in rows if r.get("row") == k
                  and not r.get("SUPERSEDED") and not r.get("VOID")]

fill = next(r for r in live("fill") if r.get("candidate_id") == cid)
trig = next(r for r in live("trigger") if r.get("candidate_id") == cid)
out = trig.get("output") or {}

actions = []
for r in sorted([r for r in live("manage") if r.get("candidate_id") == cid],
                key=lambda r: str(r.get("manage_minute"))[-5:]):
    o = r.get("output") or {}
    actions.append({"minute": str(r.get("manage_minute"))[-5:],
                    "action": r.get("action") or o.get("action"),
                    "partial_pct": r.get("partial_pct") or o.get("partial_pct"),
                    "new_stop": r.get("new_stop") or o.get("new_stop")})

targets = [t["price"] if isinstance(t, dict) else t for t in (out.get("targets") or [])]
res = exitrow.write(run, sd, cid, fill["window"], fill["side"], fill["entry"], fill["stop"],
                    targets, str(fill.get("fill_minute"))[-5:], actions,
                    conviction=fill.get("conviction"), dry=dry)
print(res if dry else "written")
