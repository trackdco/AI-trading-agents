"""Is this position still open at each of its scheduled manage minutes?

exitcalc replays the position forward under the actions already logged; if the stop or the
final target resolves before a scheduled minute, that minute must NOT be briefed - the
manager would be adjudicating a position that no longer exists. This is the guard the wr1
post-mortem asked for: a chain advances one minute at a time, and every trail can close it.

usage: alive.py <run> <sd> <cid>
"""
import sys
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
sys.path.insert(0, "/Users/barbelldaddy/.claude/jobs/2411401a/tmp")
from scripts.replay_tools import book
import exitcalc, mkmng2

NEXT = exitrow_next = {"2026-06-21": "2026-06-22", "2026-06-22": "2026-06-23",
    "2026-06-23": "2026-06-24", "2026-06-24": "2026-06-25", "2026-06-25": "2026-06-26",
    "2026-05-31": "2026-06-01", "2026-06-01": "2026-06-02", "2026-06-02": "2026-06-03",
    "2026-06-03": "2026-06-04", "2026-06-04": "2026-06-05"}

run, sd, cid = sys.argv[1:4]
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
res = exitcalc.replay(NEXT[sd], str(fill.get("fill_minute"))[-5:], fill["side"],
                      fill["entry"], fill["stop"], targets, actions)
closed = None
if res["unclosed_fraction"] <= 1e-9:
    closed = max(l["minute"] for l in res["legs"])
st, _ = mkmng2.build(run, sd, NEXT[sd], cid, "11:00")
sched = st["sched"] if isinstance(st.get("sched"), list) else list(st.get("sched", {}))
if closed:
    dead = [m for m in sched if m > closed]
    print(f"{sd} {cid}: CLOSED at {closed} -> "
          + (f"DROP {dead}" if dead else "every scheduled minute precedes it - all valid"))
else:
    print(f"{sd} {cid}: OPEN, {res['unclosed_fraction']:.3f} unclosed, sched {sched}")
