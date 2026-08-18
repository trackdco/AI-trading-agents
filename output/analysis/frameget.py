"""Resolve a manage frame for (session_day, minute), reusing an existing capture if one exists.

A chart frame is a property of the TAPE and the CURSOR, not of the run that captured it: the
same session-day at the same minute is the same bars, the same indicators, the same cursor.
235 manage frames already exist across w49/j49/wr1, so most wr2 manage calls can be served
without a live MCP navigation pass - which is the slowest and most error-prone step in the
loop, and the one that produced wr1's wrong-tape-day frames.

usage: frameget.py <run> <sd> <cid> <HH:MM>   -> prints the frame path, or NEEDS_CAPTURE
"""
import glob, os, shutil, sys

S = "/Users/barbelldaddy/tradingview-mcp/screenshots"


def resolve(run, sd, cid, minute):
    hh = minute.replace(":", "")
    want = f"{S}/{run}_{sd}_{cid}_{hh}_manage.png"
    if os.path.exists(want):
        return want, "already_present"
    # any run's capture of this same session-day and minute is the same frame
    for cand in sorted(glob.glob(f"{S}/*_{sd}_*_{hh}_manage.png")):
        shutil.copy(cand, want)
        return want, f"reused from {os.path.basename(cand)} - same tape day, same cursor minute"
    return None, "NEEDS_CAPTURE"


if __name__ == "__main__":
    run, sd, cid, minute = sys.argv[1:5]
    p, why = resolve(run, sd, cid, minute)
    print(f"{p or 'NEEDS_CAPTURE'}\t{why}")
