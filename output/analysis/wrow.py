"""CLI wrapper over mrow.write - the single path for writing a manage row.

Everything the row needs beyond the verdict is derived from the briefing that produced
it (window, reason_for_call, the working stop the manager was shown), so a row can never
disagree with the call that generated it. `mrow` itself is a module; before this wrapper
existed a hand-rolled `python mrow.py ...` invocation silently wrote nothing.

usage: wrow.py <run> <sd> <cid> <dec> <verdict.json>
"""
import json, sys
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
sys.path.insert(0, "/Users/barbelldaddy/.claude/jobs/2411401a/tmp")
import mrow

run, sd, cid, dec, vp = sys.argv[1:6]
out = json.load(open(vp))
b = json.load(open(f"output/briefings/{run}_{sd}_{cid}_{dec.replace(':','')}_manage.json"))
before = b["position"]["stop"]
after = out.get("new_stop") if out.get("action") in ("breakeven", "trail") and out.get("new_stop") else before
mrow.write(run, sd, cid, dec, b["window_note"]["window"], out,
           reason_for_call=b["reason_for_call"], stop_before=before, stop_after=after)
