#!/usr/bin/env python3
"""ITEM 3 — re-check invariant 1 (the RR floor) under A14. Geometry only, no outcomes.

Runs the full workbench admission list twice, spec_current.A14_ROUND False then True,
and reports: admitted count before/after, how many individual trades changed status
(present before but not after, or vice versa, keyed on (date, cm, tf, direction) since
a trade's identity does not depend on the price rounding), and the R_int distribution
before and after.
"""
import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]
import collections
import json
from pathlib import Path

import spec_current as SC
from invariants_2b import build_trade_list

OUT = Path(__file__).resolve().parents[2] / "vwap-bb" / "data" / "item3_a14_recheck.json"
N_FLOOR = 661


def key(t):
    return (t["session_date"], t["cm"], t["tf"], t["direction"])


def quantiles(xs):
    xs = sorted(xs)
    n = len(xs)
    def q(p):
        return xs[min(n - 1, int(p * n))]
    return {"n": n, "min": xs[0], "p25": q(.25), "median": q(.5), "p75": q(.75),
            "p95": q(.95), "max": xs[-1], "mean": sum(xs) / n}


def main():
    SC.A14_ROUND = False
    before, before_proc, before_excl, ndays = build_trade_list()
    SC.A14_ROUND = True
    after, after_proc, after_excl, _ = build_trade_list()

    kb = {key(t): t for t in before}
    ka = {key(t): t for t in after}
    only_before = sorted(set(kb) - set(ka))
    only_after = sorted(set(ka) - set(kb))
    common = set(kb) & set(ka)

    rr_before = [abs(t["tgt_px"] - t["entry"]) / t["R_int"] for t in before]
    rr_after = [abs(t["tgt_px"] - t["entry"]) / t["R_int"] for t in after]
    r_before = [t["R_int"] for t in before]
    r_after = [t["R_int"] for t in after]

    # invariant 1 re-check on the AFTER list: every admitted trade must clear 1.5R
    # using its OWN (rounded) entry/stop/target - the actual quantities transmitted.
    bad = [key(t) for t in after
           if abs(t["tgt_px"] - t["entry"]) / t["R_int"] < 1.5 - 1e-9]

    # on-grid check, confirming the rounding actually landed on the tick grid
    def on_grid(x, tick=0.25, eps=1e-6):
        return abs(x / tick - round(x / tick)) < eps
    off_entry = sum(1 for t in after if not on_grid(t["entry"]))
    off_stop = sum(1 for t in after if not on_grid(t["stop_px"]))
    off_tgt = sum(1 for t in after if not on_grid(t["tgt_px"]))

    print("=" * 92)
    print("ITEM 3 — INVARIANT 1 RE-CHECK UNDER A14 (geometry only, no outcomes)")
    print("=" * 92)
    print(f"  sessions: {ndays} total, processed before {before_proc}, after {after_proc}")
    print(f"  excluded before: {before_excl}")
    print(f"  excluded after : {after_excl}")
    print()
    print(f"  ADMITTED COUNT  before A14: {len(before):,}")
    print(f"  ADMITTED COUNT  after  A14: {len(after):,}")
    print(f"  delta: {len(after) - len(before):+,}  ({(len(after)-len(before))/len(before)*100:+.2f}%)")
    print()
    print(f"  trades present before, ABSENT after (lost the RR floor under wider R): "
          f"{len(only_before):,}")
    print(f"  trades present after,  ABSENT before (gained under A14 geometry)     : "
          f"{len(only_after):,}")
    print(f"  trades in BOTH (same identity, rounded geometry)                     : "
          f"{len(common):,}")
    print(f"  TOTAL CHANGED STATUS (only_before + only_after)                      : "
          f"{len(only_before) + len(only_after):,}")
    print()
    print("  R_int (intended R, points) distribution:")
    qb, qa = quantiles(r_before), quantiles(r_after)
    for k in ("n", "min", "p25", "median", "p75", "p95", "max", "mean"):
        print(f"    {k:<8} before {qb[k]:>10.4f}   after {qa[k]:>10.4f}   "
              f"delta {qa[k]-qb[k]:>+9.4f}")
    print()
    print("  Realised RR (target distance / R_int) distribution:")
    qb2, qa2 = quantiles(rr_before), quantiles(rr_after)
    for k in ("n", "min", "p25", "median", "p75", "p95", "max", "mean"):
        print(f"    {k:<8} before {qb2[k]:>10.4f}   after {qa2[k]:>10.4f}   "
              f"delta {qa2[k]-qb2[k]:>+9.4f}")
    print()
    print(f"  INVARIANT 1 on the AFTER list: evaluated {len(after):,}, "
          f"violations {len(bad)}  ->  {'PASS' if not bad else 'FAIL'}")
    if bad:
        print(f"    violating ids (first 25): {bad[:25]}")
    print()
    print(f"  on-grid check on the AFTER list (should be 0 everywhere):")
    print(f"    entry off-grid: {off_entry}   stop off-grid: {off_stop}   "
          f"target off-grid: {off_tgt}")
    print()
    clears = len(after) >= N_FLOOR
    print(f"  Amendment 02 floor n >= {N_FLOOR}: after-A14 count {len(after):,}  "
          f"-> {'CLEARS' if clears else '*** BELOW FLOOR ***'}")
    if not clears:
        print("  " + "!" * 70)
        print("  *** FLAGGED: admitted count fell below the Amendment 02 power floor. ***")
        print("  *** This governs the Layer 01 study, not Stage 3 itself. Not aborting; ***")
        print("  *** this is Angus's call, per item 3's own instruction.               ***")
        print("  " + "!" * 70)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "admitted_before": len(before), "admitted_after": len(after),
        "only_before_count": len(only_before), "only_after_count": len(only_after),
        "common_count": len(common),
        "r_int_before": qb, "r_int_after": qa,
        "rr_before": qb2, "rr_after": qa2,
        "invariant1_evaluated": len(after), "invariant1_violations": len(bad),
        "off_grid_after": {"entry": off_entry, "stop": off_stop, "target": off_tgt},
        "n_floor": N_FLOOR, "clears_floor": clears,
    }, indent=1))
    print(f"\nwritten {OUT}")


if __name__ == "__main__":
    main()
