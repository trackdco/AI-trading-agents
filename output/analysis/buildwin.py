"""Build every candidate briefing for one window of one session-day, with position and
escalation state GENERATED FROM THE RUN'S OWN BOOK at each candidate's decision minute.

This replaces the hand-written ps_*.json / esc_*.json files that produced every
orchestrator error in wr1. Nothing about run state is typed here: mkps.py and mkesc.py
each replay the book up to the cursor and emit what is true then. Re-running this after
a fill is not a repair, it is the normal path - the briefings downstream of the fill are
rebuilt from a book that now contains it.

usage: buildwin.py <run> <sd> <dn> <WINDOW> <thesis_path> [--only CID,CID] [--force]
"""
import json, os, subprocess, sys

T = "/Users/barbelldaddy/.claude/jobs/2411401a/tmp"
REPO = "/Users/barbelldaddy/AI-trading-agents"
PY = f"{REPO}/.venv/bin/python"
sys.path.insert(0, T)
sys.path.insert(0, f"{REPO}/output/analysis")
import mkps, mkesc, entrygate, leakcheck
sys.path.insert(0, REPO)
from scripts.replay_tools import book

PFX = {"LONDON": "L", "NY_PRE": "P", "NY_AM": "A"}


def cid_map(sd):
    """Deterministic: per window, in decision-minute order. Verified to reproduce every
    candidate_id wr1 assigned, so the two books line up candidate-by-candidate."""
    cands = json.load(open(f"{T}/cands/{sd}.json"))
    n, out = {}, {}
    for x in sorted(cands, key=lambda z: z["dec"]):
        w = x["window"]
        n[w] = n.get(w, 0) + 1
        out[x["dec"]] = (PFX[w] + str(n[w]), x)
    return out


def main():
    run, sd, dn, window, thesis = sys.argv[1:6]
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    force = "--force" in sys.argv
    macro = f"{T}/{run}_{sd}_macro_{window}_out.json"

    cm = cid_map(sd)
    todo = [(dec, cid, c) for dec, (cid, c) in sorted(cm.items()) if c["window"] == window]
    if only:
        todo = [t for t in todo if t[1] in only]

    already = {r.get("candidate_id") for r in book.read(run, sd)
               if r.get("row") in ("trigger", "gate_refusal")}

    for dec, cid, c in todo:
        hh = dec.replace(":", "")
        bpath = f"{REPO}/output/briefings/{run}_{sd}_{cid}_{hh}_trigger.json"

        ok, why = entrygate.check(sd, dec, window, raise_on_fail=False)
        if not ok:
            if cid in already:
                print(f"  {cid} {dec}: gate row already in book"); continue
            book.write(run, sd, {
                "row": "gate_refusal", "candidate_id": cid, "window": window,
                "decision_minute": f"{dn}T{dec}", "pass_reason": why,
                "adjudicated": False, "agent_spawn": None,
                "detail": ("mechanically refused by entrygate.py before any briefing was built "
                           "or any agent spawned - the entry window is not open at this minute. "
                           "His ruling 2026-08-18 made a pre-09:35 NY_AM fill forbidden and its "
                           "result void, which is an orchestrator-level gate, not a judgement "
                           "handed to the agent.")})
            print(f"  {cid} {dec}: GATE REFUSED ({why})")
            continue

        if os.path.exists(bpath) and not force:
            print(f"  {cid} {dec}: briefing exists (use --force to rebuild)"); continue

        # ---- run state, derived, never typed ----
        ps = mkps.build(run, sd, window, dec)
        pspath = f"{T}/ps_{run}_{sd}_{window}_{hh}.json"
        json.dump(ps, open(pspath, "w"), indent=1)
        esc = mkesc.build(run, sd, window)

        r = subprocess.run(
            [PY, "-m", "scripts.replay_tools.runcand", run, sd, dn, dec, cid,
             thesis, macro, str(ps["fills_this_window"]), pspath, json.dumps(esc), "-"],
            cwd=REPO, capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(bpath):
            print(f"  {cid} {dec}: BUILD FAILED rc={r.returncode} {r.stderr.strip()[-300:]}")
            continue
        for fx in ("fixgate.py", "fixnews.py"):
            subprocess.run([PY, f"{T}/{fx}", bpath], capture_output=True)
        try:
            leakcheck.check_briefing(bpath, dec, cid)
            print(f"  {cid} {dec}: OK  [{ps['state']}, {ps['fills_this_window']} fill(s)]")
        except SystemExit as e:
            print(f"  {cid} {dec}: LEAK REFUSED: {e}")


if __name__ == "__main__":
    main()
