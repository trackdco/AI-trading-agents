"""Log a batch of tv-trigger verdicts across runs/days from one JSON file.

file shape: [{"run","sd","cid","dec","window","tool_uses","out":{...},"extra":{...}}, ...]
usage: lgv.py <batch.json>
"""
import json, sys
sys.path.insert(0, "/Users/barbelldaddy/.claude/jobs/2411401a/tmp")
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
import trigrow

for v in json.load(open(sys.argv[1])):
    trigrow.write(v["run"], v["sd"], v["cid"], v["dec"], v["window"], v["out"],
                  tool_uses=v.get("tool_uses", 2), extra=v.get("extra"))
