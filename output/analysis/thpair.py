"""CLI over thesisrow.write_pair - write the fresh/reconciled thesis pair for one window open.

Also drops the reconciled read to th_<run>_<sd>_<WINDOW>_inforce.json, which is what buildwin
reads as the thesis in force. The reconciled thesis is the one that governs; the fresh row is
kept so the reviewer can see what moved.

usage: thpair.py <run> <sd> <WINDOW> <dec> <fresh.json> <reconciled.json>
"""
import json, sys
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
sys.path.insert(0, "/Users/barbelldaddy/.claude/jobs/2411401a/tmp")
import thesisrow
T = "/Users/barbelldaddy/.claude/jobs/2411401a/tmp"
run, sd, window, dec, fp, rp = sys.argv[1:7]
fresh = json.load(open(fp)); rec = json.load(open(rp))
thesisrow.write_pair(run, sd, window, dec, fresh, rec)
json.dump(rec, open(f"{T}/th_{run}_{sd}_{window}_inforce.json", "w"), indent=1)
print(f"  {sd} {window} {dec}: fresh={fresh.get('bias')} reconciled={rec.get('bias')}"
      f" ({rec.get('escalation_response') or 'n/a'})")
