"""Write the limit_placed + fill (or expiry/cancel) rows for a take, resolving the limit
lifecycle mechanically off the bars.

Cap accounting: fills_this_window_after counts LIVE fills in the window, read off the book,
with flipped-out positions disregarded per his 2026-08-16 ruling ("id disregard the first
trade in that instance") - the flip inherits its slot rather than taking a new one. Only the
CAP accounting disregards it; the realised R still scores in full.

usage: fillrow.py <run> <sd> <dn> <cid> <win_end>
"""
import json, sys

T = "/Users/barbelldaddy/.claude/jobs/2411401a/tmp"
REPO = "/Users/barbelldaddy/AI-trading-agents"
sys.path.insert(0, T); sys.path.insert(0, f"{REPO}/output/analysis"); sys.path.insert(0, REPO)
import mkps
from scripts.replay_tools import book, lifecycle

WRITTEN_CAP = {"LONDON": 2, "NY_PRE": 1, "NY_AM": 2}


def run_one(run, sd, dn, cid, win_end):
    rows = book.read(run, sd)
    trig = next(r for r in rows if r.get("row") == "trigger"
                and r.get("candidate_id") == cid and not r.get("SUPERSEDED"))
    o = trig["output"]
    window = trig["window"]
    dec = str(trig["decision_minute"])[-5:]
    side = "short" if str(o.get("rejected_level", {}).get("level", "")) and o.get("stop", 0) \
        and float(o["stop"]) > float(o["entry"]) else "long"
    entry, stop = float(o["entry"]), float(o["stop"])
    side = "short" if stop > entry else "long"
    cancel = (o.get("cancel_if_reaches") or {}).get("price")
    expiry = o.get("limit_expiry_minutes") or 10

    if o.get("entry_type") == "limit_retest" and cancel is not None:
        status, minute, price = lifecycle.limit_lifecycle(dn, dec, side, entry,
                                                          float(cancel), int(expiry))
    else:
        status, minute, price = "filled", dec, entry

    book.write(run, sd, {
        "row": "limit_placed", "candidate_id": cid, "window": window,
        "placed_at": dec, "limit": entry, "side": side, "stop": stop,
        "expiry_minutes": expiry, "cancel_if_reaches": cancel,
        "outcome": status, "outcome_minute": minute, "outcome_price": price,
        "_derivation": ("resolved mechanically by lifecycle.limit_lifecycle over the committed "
                        "bars - no judgement, no agent.")})

    if status != "filled":
        print(f"  {cid}: limit {status} at {minute} - NO FILL")
        return None

    ps = mkps.build(run, sd, window, minute)
    n_after = ps["fills_this_window"] + 1
    cap = WRITTEN_CAP[window]
    row = {
        "row": "fill", "candidate_id": cid, "window": window, "side": side,
        "entry": price, "stop": stop, "fill_minute": minute, "filled_at": minute,
        "placed_at": dec, "limit": entry, "conviction": o.get("conviction"),
        "original_r_pts": round(abs(price - stop), 4),
        "fills_this_window_after": n_after,
        "beyond_written_cap": n_after > cap,
        "cap_note": (f"written {window} cap {cap}; this is fill {n_after}."
                     + (" BEYOND the written cap - taken and tagged under the lifted-caps ruling."
                        if n_after > cap else "")),
        "fill_model": ("limit at the stated price, filled on the first bar whose range covers it "
                       "inside the expiry, cancelled if the tripwire prints first."),
        "targets_at_fill": o.get("targets"),
        "T78_ladder_rungs": len(o.get("targets") or []),
    }
    book.write(run, sd, row)
    print(f"  {cid}: FILLED {minute} @ {price} {side}, stop {stop}, "
          f"R={row['original_r_pts']}pt, rungs={row['T78_ladder_rungs']}")
    return row


if __name__ == "__main__":
    run_one(*sys.argv[1:6])
