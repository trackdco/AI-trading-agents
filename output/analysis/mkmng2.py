"""Build a tv-manage state file for one open position, DERIVED FROM THE RUN'S OWN BOOK.

The last hand-authored state class. wr1's st_*.json files were written by hand while a
position was live and re-written whenever anything moved; the manage calls that went out
against a closed position, and the briefing built one minute before the verdict that
invalidated it, both came from here. Everything below is read off the book or computed:
the fill row gives side/entry/conviction, the live manage rows give the working stop and the
prior actions, the trigger row gives the ladder, htf.management_minutes gives the schedule,
and the legend pool serves the frames.

usage: mkmng2.py <run> <sd> <dn> <cid> <win_end> <out_state.json>
"""
import json, sys

T = "/Users/barbelldaddy/.claude/jobs/2411401a/tmp"
REPO = "/Users/barbelldaddy/AI-trading-agents"
sys.path.insert(0, T); sys.path.insert(0, f"{REPO}/output/analysis"); sys.path.insert(0, REPO)
import mkps, legendpool
from levelset import levelset
from scripts.replay_tools import book, htf

WIN_TEXT = {
    "LONDON": ("the LONDON window runs 03:00-04:59. A position open at the window close is NOT "
               "force-flattened - the window gates TAKING trades, not holding them. T51 governs "
               "positions carried into the 09:30 cash open, which is hours away."),
    "NY_PRE": ("the NY_PRE window runs 08:00-09:29 with entries cut at 09:10. T51 DOES apply: "
               "this position must be flat by 09:29:59, before the cash open."),
    "NY_AM": ("the NY_AM window runs 09:30-11:00 with the earliest entry at 09:35. A position "
              "open at the window close is not force-flattened; it runs to target or stop."),
}


def build(run, sd, dn, cid, win_end):
    rows = book.read(run, sd)
    live = lambda k: [r for r in rows if r.get("row") == k
                      and not r.get("SUPERSEDED") and not r.get("VOID")]

    fill = next(r for r in live("fill") if r.get("candidate_id") == cid)
    trig = next(r for r in live("trigger") if r.get("candidate_id") == cid)
    out = trig.get("output") or {}
    window = fill["window"]
    opened_at = str(fill.get("fill_minute"))[-5:]

    # position state as of now, replayed off the book
    ps = mkps.build(run, sd, window, win_end)
    here = None
    mrows = sorted([r for r in live("manage") if r.get("candidate_id") == cid],
                   key=lambda r: str(r.get("manage_minute"))[-5:])
    stop = fill["stop"]
    remaining = 1.0
    prior_actions = []
    for r in mrows:
        if r.get("working_stop_after") is not None:
            stop = r["working_stop_after"]
        pct = r.get("partial_pct")
        if r.get("action") == "partial" and pct:
            remaining = round(remaining - remaining * float(pct), 6)
        o = r.get("output") or {}
        prior_actions.append({
            "minute": str(r.get("manage_minute"))[-5:],
            "reason_for_call": r.get("reason_for_call"),
            "action": r.get("action"), "partial_pct": pct,
            "new_stop": r.get("new_stop"), "reason": o.get("reason")})

    targets = [dict(t) for t in (out.get("targets") or [])]
    # The ladder advances: each banked partial retires one rung, so the schedule ahead is
    # computed from the last manage minute toward the rungs that are still live. Computing it
    # once at fill time against the whole ladder returns only "tp1 reached" and "window
    # closing" and leaves the runner unmanaged between them - which is how a runner with a
    # destination still ends up drifting.
    n_banked = sum(1 for r in mrows if r.get("action") == "partial" and r.get("partial_pct"))
    live_targets = targets[n_banked:]
    # Anchor the schedule on the last LADDER ADVANCE (a banked partial), not on the last
    # action of any kind. Recomputing after a trail or a hold re-derives the intermediate
    # minutes from a new start and makes them drift - the call list has to be stable between
    # rungs or the runner gets a different set of minutes every time it is touched.
    last_partial = [a["minute"] for a in prior_actions
                    if a.get("action") == "partial" and a.get("partial_pct")]
    sched_from = last_partial[-1] if last_partial else opened_at
    for i, t in enumerate(targets):
        if i < n_banked:
            t["status"] = f"REACHED and banked ({prior_actions[i]['minute']})" if i < len(prior_actions) else "REACHED"
    tg_prices = [float(t["price"]) for t in live_targets if t.get("price") is not None]

    lv = levelset(sd, dn, sched_from)
    sched_raw = htf.management_minutes(dn, sched_from, fill["side"], float(fill["entry"]),
                                       float(fill["stop"]), tg_prices, lv, win_end)
    sched = {x["minute"]: [x["reason"], x.get("level"), x.get("level_price")] for x in sched_raw}
    seen_min = prior_actions[-1]["minute"] if prior_actions else None
    sched = {m: v for m, v in sched.items() if seen_min is None or m > seen_min}

    # frames for every scheduled minute, served from the cross-run pool
    frames, misses, prov = legendpool.get(dn, sorted(sched))
    cap_path = f"{T}/cap_{run}_{sd}_{cid}.json"
    json.dump({"frames": frames}, open(cap_path, "w"), indent=1)

    th = None
    for r in rows:
        if r.get("row") == "thesis" and r.get("window") == window \
                and r.get("thesis_stage") == "reconciled":
            th = r.get("output")
    th = th or {}

    st = {
        "run": run, "sd": sd, "dn": dn, "cid": cid, "window": window,
        "side": fill["side"], "entry": float(fill["entry"]),
        "original_r": float(fill["original_r_pts"]), "conviction": fill.get("conviction"),
        "opened_at": opened_at,
        "captures": cap_path, "capture_key": "<dec>",
        "stop": stop, "targets": targets, "prior_actions": prior_actions,
        "sched": sched,
        "thesis_ctx": {
            "version": f"{window} window-open thesis, reconciled - the one in force",
            "primary_bias": th.get("bias"),
            "invalidation": (th.get("invalidation") or {}).get("price"),
            "aligned": ("stated as run state: compare this position's side against the bias above "
                        "yourself. The orchestrator does not judge alignment for you."),
        },
        "prior_positions": {"count": ps["fills_this_window"], "detail": ps["detail"],
                            "earlier_windows": ps["earlier_windows"]},
        "window_note": {"window": window, "entries_end": win_end,
                        "text": WIN_TEXT[window],
                        "disclosure": "Nothing about any later setup in this window is disclosed to you here."},
        "_derivation": ("every field read off the run's own book by mkmng2.py - fill row for the "
                        "position, live manage rows for the working stop and prior actions, "
                        "trigger row for the ladder, htf.management_minutes for the schedule, "
                        "the cross-run legend pool for the frames. Nothing hand-authored."),
        "_frames_missing": misses or None,
        "_frames_provenance": prov,
        "_remaining_fraction": remaining,
    }
    return st, misses


if __name__ == "__main__":
    run, sd, dn, cid, win_end, outp = sys.argv[1:7]
    st, misses = build(run, sd, dn, cid, win_end)
    json.dump(st, open(outp, "w"), indent=1)
    print(f"  {cid}: {st['side']} {st['entry']} stop {st['stop']} | sched {sorted(st['sched'])}")
    print(f"  frames: {len(st['sched']) - len(misses or [])}/{len(st['sched'])} pooled"
          + (f"  NEEDS LIVE CAPTURE: {misses}" if misses else ""))
