"""Write an `exit` book row from an exitcalc.replay() result.

Every number in the row comes from exitcalc (which replays the committed 1m bars under the
logged management actions) and from lifecycle.resolve (the unmanaged full-target hold).
Nothing is retyped, so the row cannot disagree with the chain that produced it.

usage (module): exitrow.write(run, sd, cid, window, side, entry, stop, targets, fill_minute,
                              actions, conviction=..., exit_reason=..., structure=...,
                              summary=..., extra={...})
"""
import sys, json
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
sys.path.insert(0, "/Users/barbelldaddy/.claude/jobs/2411401a/tmp")
from scripts.replay_tools import book, lifecycle
import exitcalc

NEXT = {"2026-06-21": "2026-06-22", "2026-06-22": "2026-06-23", "2026-06-23": "2026-06-24",
        "2026-06-24": "2026-06-25", "2026-06-25": "2026-06-26",
        "2026-05-31": "2026-06-01", "2026-06-01": "2026-06-02", "2026-06-02": "2026-06-03",
        "2026-06-03": "2026-06-04", "2026-06-04": "2026-06-05"}


def write(run, sd, cid, window, side, entry, stop, targets, fill_minute, actions,
          conviction=None, exit_reason=None, structure=None, summary=None,
          leg_notes=None, extra=None, dry=False, horizon_hours=6):
    dn = NEXT[sd]
    res = exitcalc.replay(dn, fill_minute, side, entry, stop, targets, actions,
                          horizon_hours=horizon_hours)
    if res["unclosed_fraction"] > 1e-9:
        raise SystemExit(f"{cid}: {res['unclosed_fraction']} of the position never closed - "
                         "resolve it before writing an exit row.")
    R = res["R_points"]
    # full-target = the SAME position held whole, original stop, to the final target
    unm = lifecycle.resolve(dn, fill_minute, side, entry, stop, targets[-1],
                            upto_hours=horizon_hours) if targets else None
    if unm and unm["type"] == "target":
        r_full = round((entry - unm["price"]) / R if str(side).startswith("s")
                       else (unm["price"] - entry) / R, 4)
    elif unm:
        r_full = -1.0
    else:
        r_full = None
    legs = []
    for i, l in enumerate(res["legs"]):
        d = dict(l)
        if leg_notes and i < len(leg_notes) and leg_notes[i]:
            d["note"] = leg_notes[i]
        legs.append(d)
    row = {"row": "exit", "candidate_id": cid, "window": window, "side": side,
           "entry": entry, "original_r_pts": R, "conviction": conviction,
           "exit_structure": structure, "legs": legs,
           "exit_minute": legs[-1]["minute"], "exit_price": legs[-1]["price"],
           "exit_reason": exit_reason,
           "r_multiple": res["r_blended"], "r_blended": res["r_blended"],
           "r_full_target": r_full,
           "final_stop": res["final_stop"],
           "management_summary": summary,
           "unmanaged_full_target_hold": unm,
           "_derivation": ("legs and r_blended computed by exitcalc.replay over the committed "
                           "1-minute bars under the manage actions logged in this book; "
                           "r_full_target from lifecycle.resolve on the same bars holding the "
                           "whole position on its original stop to the final target. No number "
                           "in this row was typed by hand.")}
    if extra:
        row.update(extra)
    if not dry:
        book.write(run, sd, row)
    print(f"  EXIT {run} {sd} {cid}: {res['r_blended']:+.4f}R blended / "
          f"{r_full if r_full is None else format(r_full,'+.4f')}R full-target  "
          f"[{' -> '.join(l['leg'] for l in legs)}]")
    return row
