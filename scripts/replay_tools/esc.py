"""Orchestrator-side escalation state, persisted across my tool calls."""
import json, sys, os
sys.path.insert(0,"/Users/barbelldaddy/AI-trading-agents")
from scripts.escalation_gate import EscalationGate, EscalationRecord
STATE=os.path.join(os.environ.get("CLAUDE_JOB_DIR", "/tmp"), "tmp", "esc_state.json")

def load():
    g=EscalationGate()
    if os.path.exists(STATE):
        d=json.load(open(STATE))
        g.budget=d["budget"]; g.price_tol=d["price_tol"]; g._window=d["window"]
        g._used=d["used"]; g._levels=[tuple(x) for x in d["levels"]]
        g._candidates=set(d["candidates"]); g.log=[EscalationRecord(**r) for r in d["log"]]
    return g

def save(g):
    json.dump({"budget":g.budget,"price_tol":g.price_tol,"window":g._window,"used":g._used,
               "levels":g._levels,"candidates":sorted(g._candidates),
               "log":[vars(r) for r in g.log]}, open(STATE,"w"), indent=1)

if __name__=="__main__":
    cmd=sys.argv[1]
    if cmd=="reset":
        if os.path.exists(STATE): os.remove(STATE)
        print("escalation state cleared")
    elif cmd=="open":
        g=load(); g.open_window(sys.argv[2]); save(g); print(f"window {sys.argv[2]} open, budget {g.budget}")
    elif cmd=="request":
        g=load(); cid=sys.argv[2]; verdict=json.loads(sys.argv[3])
        mech=sys.argv[4] if len(sys.argv)>4 and sys.argv[4] not in ("","-") else None
        rec=g.request(cid,verdict,mech); save(g); print(json.dumps(vars(rec),indent=1))
    elif cmd=="outcome":
        g=load(); g.record_outcome(sys.argv[2],sys.argv[3]); save(g); print("recorded")
    elif cmd=="report":
        print(json.dumps(load().report(),indent=1))
