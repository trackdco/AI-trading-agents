#!/usr/bin/env python3
"""Trade-COUNT sensitivity of each documented ambiguity.  No outcome is computed."""
import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]
sys.path.insert(0, ".")
import copy
import blind_impl as B
import bars_api

s = bars_api.sessions()
dates = sorted(d for d in s if d <= B.SEAL_DATE)
prior = B.build_prior_levels(s, dates)
BASE_OPT = copy.deepcopy(B.OPT)
BASE_F = B.FRONT_RUN_F


def run(label):
    n = 0
    longs = 0
    qual = 0
    sig = set()
    for d in dates:
        tr, st = B.process_session(d, s[d], prior[d])
        n += len(tr)
        longs += sum(1 for t in tr if t["direction"] == "long")
        qual += st["qualified"]
        for t in tr:
            sig.add((d, t["signal_minute"], t["entry_tf"], t["direction"]))
    print("%-46s trades=%4d  (%.4f/sess)  qual/sess=%6.1f  L/S=%d/%d"
          % (label, n, n / len(dates), qual / len(dates), longs, n - longs))
    return sig


base = run("BASELINE (chosen readings)")
print()
for key, val in [("cluster", "chain"), ("atr", "wilder"), ("range_conf", 3),
                 ("invalidation", "against"), ("menu_prior", False)]:
    B.OPT = copy.deepcopy(BASE_OPT)
    B.OPT[key] = val
    sig = run("OPT %s = %r" % (key, val))
    print("%-46s   overlap with baseline: %d / %d" % ("", len(sig & base), len(base)))
B.OPT = copy.deepcopy(BASE_OPT)
for f in (2.0, 3.0):
    B.FRONT_RUN_F = f
    sig = run("FRONT_RUN_F = %.1f" % f)
    print("%-46s   overlap with baseline: %d / %d" % ("", len(sig & base), len(base)))
B.FRONT_RUN_F = BASE_F
