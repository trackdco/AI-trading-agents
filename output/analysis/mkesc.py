"""Emit a window's escalation_state for a run, DERIVED FROM THAT RUN'S OWN BOOK.

WHY THIS EXISTS: the escalation state files were hand-written per window, and two of them
were carried over from w49 into wr1 unchanged. They asserted escalations that never happened
in wr1 - "vwap_p1 SHORT was escalated at 03:00 and ACCOMMODATED, the thesis re-fired as v2" -
naming a thesis version wr1 does not have. That is not a tape leak (no future price is
revealed) but it is another run's history presented to an agent as its own, and it both
understates the remaining budget and forbids an escalation the agent was entitled to raise.

Reading it off the book makes the file unable to disagree with what happened.

usage: mkesc.py <run> <sess_day> <WINDOW> <out.json>
"""
import json, sys
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
from scripts.replay_tools import book

ORDER = ["LONDON", "NY_PRE", "NY_AM"]
BUDGET = 2


def build(run, sd, window):
    rows = book.read(run, sd)
    live = [r for r in rows if r.get("row") == "trigger" and not r.get("SUPERSEDED")]
    here = [r for r in live if r.get("window") == window and r.get("ESCALATION_RAISED")]
    used = len(here)
    parts = []
    if here:
        for r in here:
            o = r.get("output") or {}
            e = o.get("escalation") or {}
            parts.append(f"{e.get('level','?')} {str(e.get('direction','?')).upper()} was escalated at "
                         f"{str(r.get('decision_minute'))[-5:]} ({r.get('candidate_id')}). That "
                         "level+direction pair must NOT be escalated again in this window.")
        ratchet = " ".join(parts)
    else:
        ratchet = "no level+direction has been escalated in THIS window."
    # accurate cross-window carry, also read off the book
    prior = []
    for w in ORDER[:ORDER.index(window)]:
        n = len([r for r in live if r.get("window") == w and r.get("ESCALATION_RAISED")])
        done = any(r.get("row") == "window_close" and r.get("window") == w for r in rows)
        prior.append(f"{w} {'closed' if done else 'ran'} with {n} escalation(s) used")
    if prior:
        ratchet += " " + "; ".join(prior) + "."
    return {"window": window, "budget": BUDGET, "used": used, "remaining": BUDGET - used,
            "ratchet": ratchet,
            "note": "stated as run state.",
            "_derivation": (f"read off {run}'s own book for {sd} by mkesc.py - the count is the number of "
                            "live trigger rows in this window carrying ESCALATION_RAISED, and the "
                            "cross-window line counts the same flag in earlier windows. Nothing here is "
                            "carried over from another run.")}


if __name__ == "__main__":
    run, sd, window, out = sys.argv[1:5]
    d = build(run, sd, window)
    json.dump(d, open(out, "w"), indent=1)
    print(f"  {sd} {window}: used {d['used']}/{d['budget']} -> {out}")
