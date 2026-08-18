"""Apply a window's fill cap to every candidate after the take that reaches it.

His 2026-08-18 ruling makes the NY_PRE cap HARD at 1: once a PRE fill exists, every later PRE
candidate is a mechanical pass and is never adjudicated on merits. Where a merit verdict was
already produced - which 10d's speculative parallel run makes routine - it is RETAINED and
flagged, never deleted, and a mechanical window_cap row is written after it. That way the
reviewer can still read the argument the agent made, including any escalation it raised,
next to the reason it did not stand.

usage: capday.py <run> <sd> <WINDOW> <cap> <hard:0|1> <after_cid> <cid:HH:MM> [cid:HH:MM ...]
       after_cid is the candidate whose fill reaches the cap; every cid listed comes after it.
"""
import json, sys
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
sys.path.insert(0, "/Users/barbelldaddy/.claude/jobs/2411401a/tmp")
from scripts.replay_tools import book
import supersede

run, sd, window, cap, hard, after = sys.argv[1:7]
cap, hard = int(cap), bool(int(hard))
rows = book.read(run, sd)
fill = next((r for r in rows if r.get("row") == "fill" and r.get("candidate_id") == after
             and not r.get("SUPERSEDED")), None)
if fill is None:
    raise SystemExit(f"no live fill row for {after} - refusing to cap against a take that never filled")
fmin = str(fill.get("fill_minute"))[-5:]
FLAG = f"SUPERSEDED_{window}_HARD_CAP" if hard else f"SUPERSEDED_{window}_CAP"
WHY = (f"adjudicated on merits under RUNBOOK 10d against a briefing reporting fewer than {cap} "
       f"fill(s) in {window}. {after} had already taken and filled at {fmin}, reaching the cap of "
       f"{cap}" + (", and his 2026-08-18 ruling makes this cap HARD: once the fill exists, every "
       "later candidate in the window is a mechanical pass and is never adjudicated on merits."
       if hard else ". A cap is enforced by the orchestrator, not weighed by the agent."))

for spec in sys.argv[7:]:
    cid, dec = spec.split(":", 1)
    prior = [r for r in rows if r.get("row") == "trigger" and r.get("candidate_id") == cid
             and not r.get("SUPERSEDED")]
    if prior:
        supersede.mark(run, sd, FLAG, WHY,
                       lambda r, c=cid: r.get("row") == "trigger" and r.get("candidate_id") == c
                       and not r.get("SUPERSEDED"), verbose=False)
        supersede.mark(run, sd, "SUPERSEDED", f"see {FLAG} on this row",
                       lambda r, c=cid: r.get("row") == "trigger" and r.get("candidate_id") == c
                       and r.get(FLAG), verbose=False)
        took = (prior[-1].get("output") or {}).get("decision", "").startswith("take")
        note = (f"the agent verdict this replaces is retained immediately above, flagged {FLAG}. "
                + ("It returned a TAKE, so this DOES change the scoreboard: a fill the agent "
                   "wanted is removed, which is what the cap is for."
                   if took else "It also passed, so the scoreboard is unchanged; what changes is "
                   "that the row now carries the correct reason."))
    else:
        note = None
    row = {"row": "trigger", "candidate_id": cid, "window": window,
           "decision_minute": f"{book.NEXT[sd] if hasattr(book,'NEXT') else ''}T{dec}".lstrip("T"),
           "agent_spawn": "none - mechanical", "model": None, "tool_uses": 0,
           "output": {"decision": "pass",
                      "reason": f"window_cap: {window} allows {cap} fill(s) and {after} filled at {fmin}."
                                + (" Later candidates are mechanical passes, not adjudicated." if hard else ""),
                      "constraints_failed": ["window_cap"]},
           "pass_reason": "window_cap",
           "cap_state_at_decision": {"fills_this_window": cap, "cap": cap, "hard": hard}}
    if note:
        row["SUPERSEDES_AN_ADJUDICATED_ROW"] = note
    else:
        row["never_adjudicated"] = "no agent was spawned - the cap is mechanical and not escalatable."
    row["decision_minute"] = f"{dec}"
    book.write(run, sd, row)
    print(f"  {cid} {dec}: window_cap pass" + (" (superseded a take)" if note and "TAKE" in note else ""))
