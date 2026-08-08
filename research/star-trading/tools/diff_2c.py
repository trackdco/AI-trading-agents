#!/usr/bin/env python3
"""2c — DIFFERENTIAL: detector vs the blind second implementation.

Compares on (session_date, signal_minute, entry_tf, direction, entry, stop, target).
'entry' is the FILL price on both sides. No outcome is read or computed.
"""
import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]
import json, collections
from pathlib import Path
from invariants_2b import build_trade_list

BLIND = Path("/tmp/claude-0/-home-user-AI-trading-agents/"
             "90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/blind_build/blind_trades.json")
TOL = 0.01


def key(d, m, tf, dr):
    return (d, int(m), int(tf), dr)


def main():
    mine, processed, excl, ndays = build_trade_list()
    A = {key(t["session_date"], t["cm"], t["tf"], t["direction"]):
         (round(t["fill_px"], 4), round(t["stop_px"], 4), round(t["tgt_px"], 4))
         for t in mine}
    raw = json.loads(BLIND.read_text())
    B = {key(t["session_date"], t["signal_minute"], t["entry_tf"], t["direction"]):
         (round(float(t["entry"]), 4), round(float(t["stop"]), 4), round(float(t["target"]), 4))
         for t in raw}

    only_a = sorted(set(A) - set(B))
    only_b = sorted(set(B) - set(A))
    both = sorted(set(A) & set(B))
    geom = [(k, A[k], B[k]) for k in both
            if any(abs(x - y) > TOL for x, y in zip(A[k], B[k]))]

    print("=" * 92)
    print("2c — DIFFERENTIAL IMPLEMENTATION")
    print("=" * 92)
    print(f"  detector trades            : {len(A):,}")
    print(f"  blind build trades         : {len(B):,}")
    print(f"  present in BOTH (key match): {len(both):,}")
    print(f"  detector only              : {len(only_a):,}")
    print(f"  blind only                 : {len(only_b):,}")
    print(f"  key match, geometry differs: {len(geom):,}  (tolerance {TOL})")
    print(f"  TOTAL DIFF                 : {len(only_a) + len(only_b) + len(geom):,}")
    print()
    if only_a:
        ca = collections.Counter((k[2], k[3]) for k in only_a)
        print(f"  detector-only by (tf, dir): {dict(ca)}")
        print(f"  first 15: {only_a[:15]}")
    if only_b:
        cb = collections.Counter((k[2], k[3]) for k in only_b)
        print(f"  blind-only by (tf, dir)   : {dict(cb)}")
        print(f"  first 15: {only_b[:15]}")
    if geom:
        print("  first 15 geometry diffs (key, detector(e,s,t), blind(e,s,t)):")
        for k, a, b in geom[:15]:
            print(f"    {k}  {a}  vs  {b}")
        fields = collections.Counter()
        for k, a, b in geom:
            for nm, x, y in zip(("entry", "stop", "target"), a, b):
                if abs(x - y) > TOL:
                    fields[nm] += 1
        print(f"  geometry diffs by field: {dict(fields)}")
    Path(__file__).with_name("diff_2c_result.json").write_text(json.dumps(
        {"n_detector": len(A), "n_blind": len(B), "n_both": len(both),
         "only_detector": [list(k) for k in only_a],
         "only_blind": [list(k) for k in only_b],
         "geometry": [[list(k), a, b] for k, a, b in geom]}, indent=1))


if __name__ == "__main__":
    main()
