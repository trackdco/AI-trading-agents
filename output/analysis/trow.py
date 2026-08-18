"""CLI over trigrow.write - write one `trigger` row from a verdict file.

usage: trow.py <run> <sd> <cid> <dec> <WINDOW> <verdict.json> [tool_uses]
"""
import json, sys
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
sys.path.insert(0, "/Users/barbelldaddy/.claude/jobs/2411401a/tmp")
import trigrow
run, sd, cid, dec, window, vp = sys.argv[1:7]
tu = int(sys.argv[7]) if len(sys.argv) > 7 else 2
out = json.load(open(vp))
trigrow.write(run, sd, cid, dec, window, out, tool_uses=tu)
print(f"  {sd} {cid} {dec} {window}: {out.get('decision')}")
