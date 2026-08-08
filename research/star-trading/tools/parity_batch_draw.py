#!/usr/bin/env python3
"""P4-P9 DRAW — executes PARITY-BATCH-PREREG.md §3 exactly. Method committed first.

Seed = int(first 16 hex of the PART-1 commit SHA, 16). One rng stream, fixed order.
No outcome is computed. The archived pre-A8 result is never opened.
"""
import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]
import collections, json, random
from pathlib import Path

from vwapbb_signals import build_sessions, minute_of_day, RTH_OPEN, RTH_CLOSE
from vwapbb_opportunity import assert_workbench, WORKBENCH_END
from stage2_smoke import contract_key
import spec_current as SC

PART1_SHA = "4014d2e5c31fbeeefe579d35d19558a2850afe87"
SEED = int(PART1_SHA[:16], 16)
LO, HI = 9 * 60 + 36, 15 * 60 + 59          # 576 .. 959 inclusive
OUT = Path(__file__).resolve().parents[2] / "vwap-bb" / "data" / "parity_batch_draw.json"

SC.SIGMA_RULE = "live"                       # A13


def main():
    rng = random.Random(SEED)
    sess, sym_of = build_sessions()
    days = [d for d in sorted(sess) if d <= WORKBENCH_END]
    for d in days:
        assert_workbench(d)
    rolls, prev = set(), None
    for d in days:
        s = sorted(sym_of[d], key=contract_key)[-1]
        if prev and contract_key(s) > contract_key(prev):
            rolls.add(d)
        prev = s
    after = {days[i + 1] for i, d in enumerate(days) if d in rolls and i + 1 < len(days)}

    poolR, poolF, prev_hl = [], [], None
    excl = collections.Counter()
    for d in days:
        bars = sess[d]
        this_hl = (max(x[1] for x in bars.values()), min(x[2] for x in bars.values()))
        ok = True
        if d in rolls:
            excl["roll"] += 1; ok = False
        elif d in after:
            excl["after roll"] += 1; ok = False
        elif len(sym_of[d]) > 1:
            excl["mixed contract"] += 1; ok = False
        elif len([i for i in bars if RTH_OPEN <= minute_of_day(i) < RTH_CLOSE]) < 300:
            excl["holiday / short"] += 1; ok = False
        if ok:
            poolR.extend((d, m) for m in range(LO, HI + 1))          # step 1
            c = SC.signal_candidates_current(bars, prev_hl)          # step 2
            if c:
                for t in SC.admit_current(bars, c):
                    if t["tf"] in (2, 3, 5):
                        poolF.append((d, t["cm"], t["tf"]))
        prev_hl = None if d in rolls else this_hl

    poolR.sort(); poolF.sort()
    print(f"pool R: {len(poolR):,} (session, minute) pairs over "
          f"{len({x[0] for x in poolR})} sessions   excluded {dict(excl)}")
    print(f"pool F: {len(poolF):,} admitted trades on 2m/3m/5m under the current spec")
    print(f"seed  : {SEED}  (from PART-1 commit {PART1_SHA})")

    F = rng.sample(poolF, 3)                                          # step 3
    taken = {(d, m) for d, m, _ in F}
    R, discarded = [], []
    while len(R) < 3:                                                 # step 4
        cand = rng.sample(poolR, 1)[0]
        if cand in taken or cand in R:
            discarded.append({"instant": list(cand), "reason": "collides with a drawn instant"})
            continue
        R.append(cand)
    six = [{"date": d, "cm": m, "cls": "F", "tf": tf} for d, m, tf in F] + \
          [{"date": d, "cm": m, "cls": "R", "tf": None} for d, m in R]
    rng.shuffle(six)                                                  # step 6
    for k, x in enumerate(six, start=4):
        x["label"] = f"P{k}"
        x["hhmm"] = f"{x['cm']//60:02d}:{x['cm']%60:02d}"
        x["bar_exists"] = ((x["cm"] - 1 - 1080) % 1440) in sess[x["date"]]

    OUT.write_text(json.dumps(
        {"seed": SEED, "part1_sha": PART1_SHA, "poolR": len(poolR), "poolF": len(poolF),
         "discarded": discarded, "batch": six}, indent=1))
    print(f"\ndiscarded draws: {discarded or 'none'}")
    print("\nRELEASE (dates and times only, class NOT shown):")
    for x in sorted(six, key=lambda y: y["label"]):
        print(f"   {x['label']}   {x['date']}   {x['hhmm']} ET")
    print(f"\nbar present at every drawn instant: "
          f"{all(x['bar_exists'] for x in six)}")
    print(f"\nsealed detail -> {OUT}")


if __name__ == "__main__":
    main()
