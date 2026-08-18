"""Emit a window's position_state for a run, DERIVED FROM THAT RUN'S OWN BOOK.

WHY THIS EXISTS: in wr1 the position-state files were hand-written per briefing batch and
re-authored ad hoc whenever anything upstream changed. Four of the five orchestrator errors
in that run came from exactly here - a file saying a trade had closed at target while its
runner was still open, a file describing a stop that had since been trailed, a file built one
minute before the manage verdict that invalidated it. 21 of 125 book rows ended up superseded.
None of it was a tape leak; all of it was state that had already moved.

`mkesc.py` fixed the same class of bug for escalation state by reading it off the book. This
does it for position state: replay the day's LIVE fill / manage / exit rows in minute order up
to the decision minute and emit what is true at that moment. A generated file cannot disagree
with what happened; a hand-written one can, and did.

Causality: only rows whose minute is <= the decision minute are read, so the file cannot carry
information from after the cursor. Any event landing EXACTLY on the decision minute is listed
in `_ties` so the reviewer can see it was included on the decision-minute-open convention.

usage: mkps.py <run> <sess_day> <WINDOW> <HH:MM> <out.json>
"""
import json, sys

sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
from scripts.replay_tools import book

ORDER = ["LONDON", "NY_PRE", "NY_AM"]
WRITTEN_CAP = {"LONDON": 2, "NY_PRE": 1, "NY_AM": 2}
LIFTED = {
    "LONDON": "Caps are LIFTED-WITH-TAGS here: a fill past the written cap is taken and "
              "tagged beyond_written_cap, not refused.",
    "NY_AM": "Caps are LIFTED-WITH-TAGS here: a fill past the written cap is taken and "
             "tagged beyond_written_cap, not refused.",
    "NY_PRE": "NY_PRE is HARD-capped at 1 fill per session-day (his ruling 2026-08-18). Once a "
              "PRE fill exists, every later PRE candidate is a pass with reason window_cap - "
              "never tagged-and-taken. This cap is NOT lifted.",
}


def _hhmm(v):
    """Book minute fields are inconsistent - '03:00' on fills/exits, full ISO on manage rows."""
    if v is None:
        return None
    s = str(v)
    return s[-5:] if len(s) >= 5 else s


def _live(rows, kind):
    return [r for r in rows
            if r.get("row") == kind and not r.get("SUPERSEDED") and not r.get("VOID")]


def _targets_for(rows, cid):
    """The plan's ladder, off the trigger row that authorised the fill."""
    for r in _live(rows, "trigger"):
        if r.get("candidate_id") == cid:
            o = r.get("output") or {}
            t = o.get("targets")
            if t:
                return t
    return []


def _fmt_targets(tg):
    if not tg:
        return None
    return ", ".join(f"{t.get('level','?')} {t.get('price')}" for t in tg)


def build(run, sd, window, dec):
    rows = book.read(run, sd)
    dec = _hhmm(dec)

    # --- replay every live position event in this session-day, in minute order, up to dec ---
    ev = []
    for r in _live(rows, "fill"):
        ev.append((_hhmm(r.get("fill_minute")), 0, "fill", r))
    for r in _live(rows, "manage"):
        ev.append((_hhmm(r.get("manage_minute")), 1, "manage", r))
    for r in _live(rows, "exit"):
        ev.append((_hhmm(r.get("exit_minute")), 2, "exit", r))
    # STRICTLY BEFORE the decision minute. A decision at minute M is taken at M's OPEN - the
    # instant the prior bar closed - so anything that resolves during M's own bar (a fill from a
    # standing limit, a stop, a target) has NOT happened yet and must not appear in the state the
    # agent is handed. Using <= here instead counted same-minute events as already done, which
    # made a candidate adjudicated at the same minute its predecessor stopped out look like it
    # had been judged against stale state when it had not.
    ties = [f"{k} {r.get('candidate_id')} at {m}" for m, _, k, r in ev
            if m is not None and m == dec]
    ev = [e for e in ev if e[0] is not None and e[0] < dec]
    ev.sort(key=lambda e: (e[0], e[1]))

    pos = {}       # cid -> live position dict
    closed = []    # (cid, window, exit dict)
    fills_by_window = {w: [] for w in ORDER}

    for minute, _, kind, r in ev:
        cid = r.get("candidate_id")
        if kind == "fill":
            w = r.get("window")
            fills_by_window.setdefault(w, []).append(r)
            pos[cid] = {"cid": cid, "window": w, "side": r.get("side"),
                        "entry": r.get("entry"), "stop": r.get("stop"),
                        "conviction": r.get("conviction"),
                        "original_r_pts": r.get("original_r_pts"),
                        "fill_minute": minute, "remaining": 1.0, "banked": [],
                        "last_action": None, "last_action_minute": None,
                        "beyond_written_cap": bool(r.get("beyond_written_cap"))}
        elif kind == "manage":
            p = pos.get(cid)
            if not p:
                continue
            act = r.get("action")
            ws = r.get("working_stop_after")
            if ws is not None:
                p["stop"] = ws
            pct = r.get("partial_pct")
            if act == "partial" and pct:
                took = p["remaining"] * float(pct)
                p["banked"].append({"minute": minute, "fraction_of_position": round(took, 4),
                                    "pct_of_what_was_open": float(pct)})
                p["remaining"] = round(p["remaining"] - took, 6)
            p["last_action"] = act
            p["last_action_minute"] = minute
            if act == "exit_now":
                p["remaining"] = 0.0
        elif kind == "exit":
            p = pos.pop(cid, None)
            closed.append((cid, r.get("window"), r))

    # a position whose manage row said exit_now but whose exit row lands later is still gone
    for cid in [c for c, p in pos.items() if p["remaining"] <= 0]:
        closed.append((cid, pos[cid]["window"], None))
        pos.pop(cid)

    # --- the window in front of the agent ---
    here = [p for p in pos.values() if p["window"] == window]
    n_fills = len(fills_by_window.get(window, []))

    if not here:
        state, detail = "FLAT", "no open position."
    else:
        state = "OPEN"
        bits = []
        for p in here:
            tg = _fmt_targets(_targets_for(rows, p["cid"]))
            s = (f"a position is OPEN: {p['cid']} - {p['side']} {p['entry']:.2f} filled "
                 f"{p['fill_minute']}, conviction {p['conviction']}, original risk "
                 f"{p['original_r_pts']}pt.")
            if p["banked"]:
                took = " and ".join(f"{b['pct_of_what_was_open']*100:.0f}% of what was open at "
                                    f"{b['minute']}" for b in p["banked"])
                s += (f" It has been partially banked ({took}); {p['remaining']*100:.0f}% of the "
                      f"original position is still running.")
            else:
                s += " Nothing has been banked; the full position is still on."
            s += f" Working stop {p['stop']:.2f}"
            if p["last_action"]:
                s += f" (last manage action: {p['last_action']} at {p['last_action_minute']})."
            else:
                s += " (as placed at entry; no manage action yet)."
            # the runner's mandate, T78 / tv-manage 0.3.4
            if tg:
                s += f" The plan's ladder: {tg}."
            else:
                s += (" DEFECT: the plan named no targets - under T78 every plan must carry TP1 "
                      "and TP2, so a runner here has no destination in force.")
            bits.append(s)
        detail = " ".join(bits)

    # closed positions in THIS window are context the agent is entitled to
    done_here = [(c, r) for c, w, r in closed if w == window and r is not None]
    if done_here:
        detail += " Already resolved in this window: " + "; ".join(
            f"{c} exited {_hhmm(r.get('exit_minute'))} at {r.get('exit_price')} "
            f"({r.get('exit_reason')}, {r.get('r_multiple')}R)" for c, r in done_here) + "."

    # --- earlier windows ---
    idx = ORDER.index(window)
    if idx == 0:
        earlier = "none - LONDON is the first window of the session-day."
    else:
        parts = []
        for w in ORDER[:idx]:
            nf = len(fills_by_window.get(w, []))
            res = [(c, r) for c, ww, r in closed if ww == w and r is not None]
            still = [p["cid"] for p in pos.values() if p["window"] == w]
            t = f"{w}: {nf} fill(s)"
            if res:
                t += " - " + ", ".join(f"{c} {r.get('r_multiple')}R ({r.get('exit_reason')})"
                                       for c, r in res)
            if still:
                t += f" - STILL OPEN: {', '.join(still)}"
            parts.append(t)
        earlier = "; ".join(parts) + "."

    cap = WRITTEN_CAP[window]
    cap_note = (f"the written {window} cap is {cap} fill(s) and {n_fills} "
                f"{'is' if n_fills == 1 else 'are'} used. {LIFTED[window]}")

    return {"window": window, "as_of": dec, "state": state,
            "fills_this_window": n_fills, "detail": detail,
            "earlier_windows": earlier, "cap_note": cap_note,
            "note": "stated as run state.",
            "_ties": (ties or None) and
                     {"events_resolving_during_this_minute": ties,
                      "note": ("these land on the decision minute itself and are DELIBERATELY EXCLUDED "
                               "from the state above - at this minute's open they have not happened. "
                               "Listed so the reviewer can see the boundary was applied, not missed.")},
            "_derivation": (f"read off {run}'s own book for {sd} by mkps.py - every LIVE "
                            f"fill/manage/exit row with a minute STRICTLY BEFORE {dec}, replayed in "
                            "order. "
                            "Rows flagged SUPERSEDED or VOID are excluded. Nothing after the "
                            "cursor is read, and nothing here is carried over from another run "
                            "or hand-authored.")}


if __name__ == "__main__":
    run, sd, window, dec, out = sys.argv[1:6]
    d = build(run, sd, window, dec)
    json.dump(d, open(out, "w"), indent=1)
    print(f"  {sd} {window} @{d['as_of']}: {d['state']}, "
          f"{d['fills_this_window']}/{WRITTEN_CAP[window]} fills -> {out}")
