"""Build ONE manage briefing from a position spec held in a JSON state file.

p2chain/p6chain/a2chain each hard-code one position because each was written while that
position was live and needed prose specific to it. From j49 day 2 on there are many short
chains - most positions get one or two calls before they resolve - and a file per position
is churn with no benefit. This is the same builder with the position-specific parts moved
into the state file.

State file shape (one per position, `<key>_state.json`):

    {"run","sd","dn","cid","window","side","entry","original_r","conviction","opened_at",
     "captures": "<path to the capture json>", "capture_key": "<key inside frames{}>",
     "stop": <live stop>, "targets": [...], "prior_actions": [...],
     "sched": {"<dec>": [reason, level, level_price], ...},
     "thesis_ctx": {...}, "prior_positions": {...}, "window_note": {...}}

`window_note` is merged with the per-call additions, so it holds the standing text and this
adds only what is true AT this minute.

usage: mng1.py <state.json> <dec>
"""
import json, os, sys
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
sys.path.insert(0, "/Users/barbelldaddy/.claude/jobs/2411401a/tmp")
from scripts.replay_tools import runmanage
import fixbars, fixtp1, fixbe

T = "/Users/barbelldaddy/.claude/jobs/2411401a/tmp"


def _frame(st, hh):
    """Path to this call's chart frame, copied into place if it exists anywhere on disk."""
    import frameget
    p, _ = frameget.resolve(st["run"], st["sd"], st["cid"], f"{hh[:2]}:{hh[2:]}")
    return os.path.basename(p) if p else f'{st["run"]}_{st["sd"]}_{st["cid"]}_{hh}_manage.png'


def build(state_path, dec):
    st = json.load(open(state_path))
    reason, level, level_price = st["sched"][dec]
    caps = json.load(open(st["captures"]))
    frames = caps.get("frames", caps)
    cl = dict(frames[st["capture_key"].replace("<dec>", dec)])
    for k in ("cid", "cursor", "bar_start", "status"):
        cl.pop(k, None)
    cl["provenance"] = "captured live via the full runbook sequence."

    w = dict(st.get("window_note") or {})
    if st.get("followup_note"):
        w["follow_up_note"] = st["followup_note"]
    if level == "adverse_excursion_0.5R":
        # Same honest disclosure as p2chain: the scheduler measures adverse excursion on
        # 1-MINUTE closes, the briefing is anchored on grid_2m(dec). The 1m bar that tripped
        # the call can sit inside a 2m bar that has not closed yet, so open_pnl_in_R reads
        # shallower than the excursion that called the manager. Both numbers are true and
        # the manager is told so rather than left to think the harness is lying.
        w["why_this_call_fired"] = (
            "the trigger was a 1-minute close 0.5R+ against the position. Your grid is 2m, "
            "and the 1m bar that tripped it may not have closed a 2m bar yet - so "
            "open_pnl_in_R here can read shallower than the excursion that called you. "
            "Nothing is being withheld: the adverse extreme since entry is real and at "
            "least as deep as the last 2m close shows.")

    if reason == "tp1_reached":
        # The scheduler detects TP1 on a 1-MINUTE bar; BREAKEVEN_RULE.tp1_printed_yet is
        # recomputed on grid_2m(dec). Those disagree whenever the target trades on a 1m bar
        # inside a 2m bar that has not closed - which is the NORMAL case, because the
        # scheduler stamps the call one minute after the bar that reached it. Seen on j49
        # 2026-06-03 A3: target 30164.25 traded at 10:06 (1m low 30152.50) and the 10:07
        # briefing still read tp1_printed_yet false, because the newest CLOSED 2m bar ended
        # at 10:06 and did not contain it.
        #
        # Left unsaid, the briefing contradicts itself - reason_for_call says the target was
        # reached and the breakeven block says it was not - and the manager has to guess
        # which to believe. Both are true on their own grid, and it is told so.
        w["why_this_call_fired"] = (
            "your first target traded on a 1-MINUTE bar. Your grid is 2m, and the 2m bar "
            "containing that print has not closed yet, so BREAKEVEN_RULE.tp1_printed_yet "
            "may still read false. Both are accurate on their own timeframe. For the "
            "purpose of THIS call the target HAS been reached - that is why you were "
            "called - and breakeven is therefore available to you here.")
    hh = dec.replace(":", "")
    out = f"output/briefings/{st['run']}_{st['sd']}_{st['cid']}_{hh}_manage.json"
    runmanage.build(
        run=st["run"], sd=st["sd"], dn=st["dn"], dec=dec, cid=st["cid"],
        # Resolve the frame through frameget rather than just NAMING it: frameget copies
        # a matching PNG into place if one exists under any run or candidate at this same
        # session-day and minute. Naming it alone produced ten briefings that pointed at a
        # file which was never created, and the managers decided on the text alone.
        shot=_frame(st, hh),
        reason=reason, level=level, level_price=level_price,
        side=st["side"], entry=st["entry"], stop=st["stop"], targets=st["targets"],
        conviction=st["conviction"], chart_levels=cl, opened_at=st["opened_at"],
        prior_actions=st["prior_actions"], original_r=st["original_r"],
        thesis_ctx=st["thesis_ctx"], prior_positions=st["prior_positions"],
        window_note=w, out=out)
    p = f"/Users/barbelldaddy/AI-trading-agents/{out}"
    fixbars.recompute(p, verbose=False)
    fixtp1.recompute(p, verbose=False)
    fixbe.recompute(p, verbose=False)
    b = json.load(open(p))
    print(f"built {st['run']} {st['sd']} {st['cid']} {dec} ({reason}/{level}) "
          f"stop {st['stop']} | px {b['price_at_decision']} "
          f"| open_pnl {b['position']['open_pnl_in_R']}R "
          f"| tp1_printed {b['BREAKEVEN_RULE']['tp1_printed_yet']}")
    return p


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
