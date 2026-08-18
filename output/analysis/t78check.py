"""T78 compliance: every take must carry TP1 AND TP2, and TP2 must be a LEVEL.

This is the reviewer check the kickoff names - "two targets on every plan, no fixed-R TP2".
It REPORTS, it does not repair. If the trigger agent emits a single-target plan under
0.4.12 that is a fact about whether T78 works, and hand-patching the plan would destroy the
only measurement this run exists to make. tv-manage 0.3.4 anticipates the same path from the
other side: a single-target plan reaching the manager is "a defect to flag in your reason,
not a licence to drift".

usage: t78check.py <run> [sd ...]
"""
import json, re, sys
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
from scripts.replay_tools import book

DAYS = {"wr2": ["2026-06-21", "2026-06-22", "2026-06-23", "2026-06-24", "2026-06-25"],
        "jr1": ["2026-05-31", "2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04"]}
FIXED_R = re.compile(r"^\s*(fixed[_\s-]?)?\d+(\.\d+)?\s*r\s*$", re.I)


def audit(run, days):
    rows_out, takes = [], 0
    for sd in days:
        for r in book.read(run, sd):
            if r.get("row") != "trigger" or r.get("SUPERSEDED"):
                continue
            o = r.get("output") or {}
            if not str(o.get("decision", "")).startswith("take"):
                continue
            takes += 1
            tg = o.get("targets") or []
            cid, dec = r.get("candidate_id"), str(r.get("decision_minute"))[-5:]
            if len(tg) < 2:
                rows_out.append((sd, cid, dec, "SINGLE_TARGET",
                                 f"{len(tg)} target(s): {json.dumps(tg)}"))
                continue
            lvl = str(tg[1].get("level", ""))
            if FIXED_R.match(lvl) or not lvl:
                rows_out.append((sd, cid, dec, "TP2_NOT_A_LEVEL", f"TP2 level={lvl!r}"))
            # spacing: TP2 should sit at least ~1R past TP1
            e, s = r.get("entry"), r.get("stop")
            if e and s and tg[0].get("price") and tg[1].get("price"):
                R = abs(float(e) - float(s))
                gap = abs(float(tg[1]["price"]) - float(tg[0]["price"]))
                if R and gap < 0.75 * R:
                    rows_out.append((sd, cid, dec, "TP2_TOO_CLOSE",
                                     f"gap {gap:.2f}pt = {gap/R:.2f}R past TP1"))
    return takes, rows_out


if __name__ == "__main__":
    run = sys.argv[1]
    days = sys.argv[2:] or DAYS.get(run, [])
    takes, bad = audit(run, days)
    print(f"T78 audit {run}: {takes} take(s) adjudicated, {len(bad)} defect(s)")
    for sd, cid, dec, kind, det in bad:
        print(f"  {sd} {cid} @{dec}  {kind}: {det}")
    if not bad and takes:
        print("  every take carries TP1 + TP2, TP2 is a level, spacing >= 0.75R past TP1")
