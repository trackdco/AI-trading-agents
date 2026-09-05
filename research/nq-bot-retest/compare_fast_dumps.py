#!/usr/bin/env python3
"""Compare two test_fast_features.py dumps field by field. usage: compare_fast_dumps.py ORIG.json FAST.json"""
import json
import sys

a = json.load(open(sys.argv[1]))
b = json.load(open(sys.argv[2]))
ok = True
for key in ("snapshots", "obs", "fvgs", "sweeps", "counters", "new_records", "pending"):
    same = a[key] == b[key]
    n = len(a[key]) if isinstance(a[key], list) else 1
    print(f"{key:12s} {'identical' if same else 'DIFFERENT'} (n={n})")
    if not same:
        ok = False
        if isinstance(a[key], list):
            m = min(len(a[key]), len(b[key]))
            i = next((i for i in range(m) if a[key][i] != b[key][i]), None)
            print(f"   lengths {len(a[key])} vs {len(b[key])}; first differing index {i}")
            if i is not None:
                print("   orig:", str(a[key][i])[:300])
                print("   fast:", str(b[key][i])[:300])
print(f"speed: original {a['bars_per_sec']} bars/s, fast {b['bars_per_sec']} bars/s (x{b['bars_per_sec']/a['bars_per_sec']:.1f})")
print("EQUIVALENT" if ok else "NOT EQUIVALENT")
sys.exit(0 if ok else 1)
