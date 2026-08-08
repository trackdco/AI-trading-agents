#!/usr/bin/env python3
"""H1 second half — the hand log records its own Entry TF. Compare like with like.
Also H4's precondition: does the data contain any of the hand-log dates at all?"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections, csv
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[3]
HAND = ROOT / "data" / "reference" / "feb2026_hand_log.csv"
P = ROOT / "research" / "vwap-bb" / "data" / "candidates.parquet"


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def mins(s):
    s = (s or "").strip()
    if ":" not in s:
        return None
    h, m = s.split(":")[:2]
    return int(h) * 60 + int(m)


def handlog():
    out = []
    for r in csv.DictReader(HAND.read_text().splitlines()):
        k = {kk.strip(): (vv or "").strip() for kk, vv in r.items() if kk}
        out.append({
            "date": k.get("Date", ""), "t": mins(k.get("Entry Time")),
            "tf": k.get("Entry TF", "").upper().replace("M", ""),
            "dir": k.get("Direction", ""), "pattern": k.get("Pattern", ""),
            "stop": float(k["Stop pts"]), "R": float(k["R Multiple"] or 0),
            "mfe": float(k["MFE (R)"] or 0), "mae": float(k["MAE (R)"] or 0),
            "res": k.get("Result", ""), "htf": k.get("HTF (15M)", ""),
            "reason": k.get("Exit Reason", ""),
        })
    return out


def main():
    hl = handlog()
    ins = [h for h in hl if h["t"] is not None and h["t"] >= 9 * 60 + 36]
    print(f"hand log: {len(hl)} trades, {len(ins)} in scope (>=09:36)\n")

    print("=" * 92)
    print("HAND LOG — stop distance (points) by ITS OWN recorded Entry TF")
    print("=" * 92)
    print(f"{'entry TF':>10} {'n':>4} {'min':>8} {'p25':>8} {'median':>8} {'p75':>8} {'max':>8}   trades")
    for lab, pop in (("FULL", hl), ("IN-SCOPE", ins)):
        print(f"-- {lab} --")
        for tf in ("1", "2", "3", "5"):
            g = [h["stop"] for h in pop if h["tf"] == tf]
            if not g:
                print(f"{tf+'M':>10} {0:>4}")
                continue
            print(f"{tf+'M':>10} {len(g):>4} {min(g):>8.2f} {pct(g,.25):>8.2f} "
                  f"{pct(g,.5):>8.2f} {pct(g,.75):>8.2f} {max(g):>8.2f}   "
                  + " ".join(f"{x:g}" for x in sorted(g)))

    # detector, same cut
    t = pq.read_table(P).to_pydict()
    n = len(t["session_date"])
    rows = [{k: t[k][i] for k in t} for i in range(n)
            if t["warmup_treatment"][i] == "prior"]

    print("\n" + "=" * 92)
    print("SIDE BY SIDE — median stop distance, points")
    print("=" * 92)
    print(f"{'entry TF':>10} {'hand full':>11} {'hand in-scope':>15} "
          + " ".join(f"{'det '+m:>9}" for m in "ABCD") + f" {'ratio A':>9} {'ratio C':>9}")
    for tf in ("1", "2", "3", "5"):
        hf = [h["stop"] for h in hl if h["tf"] == tf]
        hi_ = [h["stop"] for h in ins if h["tf"] == tf]
        cells, med = [], {}
        for m in "ABCD":
            g = [r["stop_distance_points"] for r in rows
                 if r["trigger_reading"] == m and r["entry_tf"] == int(tf)]
            med[m] = pct(g, .5) if g else float("nan")
            cells.append(f"{med[m]:>9.2f}")
        rf = (pct(hi_, .5) / med["A"]) if hi_ else float("nan")
        rc = (pct(hi_, .5) / med["C"]) if hi_ else float("nan")
        print(f"{tf+'M':>10} {pct(hf,.5) if hf else float('nan'):>11.2f} "
              f"{pct(hi_,.5) if hi_ else float('nan'):>15.2f} " + " ".join(cells)
              + f" {rf:>8.1f}x {rc:>8.1f}x")

    print("\n-- how far into the detector's upper tail does the hand-log median sit? --")
    print(f"{'entry TF':>10} {'hand med':>10} " + " ".join(f"{'pctile '+m:>11}" for m in "ABCD"))
    for tf in ("1", "2", "3", "5"):
        hi_ = [h["stop"] for h in ins if h["tf"] == tf]
        if not hi_:
            continue
        hm = pct(hi_, .5)
        cells = []
        for m in "ABCD":
            g = [r["stop_distance_points"] for r in rows
                 if r["trigger_reading"] == m and r["entry_tf"] == int(tf)]
            cells.append(f"{sum(1 for x in g if x < hm)/len(g)*100:>10.2f}%" if g else f"{'—':>11}")
        print(f"{tf+'M':>10} {hm:>10.2f} " + " ".join(cells))

    print("\n" + "=" * 92)
    print("HAND LOG — implied target distance (stop x |R|), points")
    print("=" * 92)
    wins = [h for h in ins if h["res"] == "win"]
    print(f"in-scope winners n={len(wins)}: "
          f"median {pct([h['stop']*h['R'] for h in wins],.5):.1f}  "
          f"min {min(h['stop']*h['R'] for h in wins):.1f}  "
          f"max {max(h['stop']*h['R'] for h in wins):.1f}")
    print("detector tgt1 distance, reading A, median: "
          f"{pct([r['stop_distance_points']*r['available_R_to_spec_target'] for r in rows if r['trigger_reading']=='A'],.5):.1f}")

    print("\n" + "=" * 92)
    print("H4 PRECONDITION — are the hand-log sessions present in the data at all?")
    print("=" * 92)
    have = set(t["session_date"])
    dates = sorted({h["date"] for h in hl})
    print(f"distinct hand-log dates: {len(dates)}  ({dates[0]} .. {dates[-1]})")
    print(f"detector sessions in parquet: {len(have)}  max = {max(have)}")
    print(f"hand-log dates present in the detector output: "
          f"{len([d for d in dates if d in have])}")
    print("\nhand log by pattern (in scope): "
          + "  ".join(f"{k}={v}" for k, v in
                      sorted(collections.Counter(h['pattern'] for h in ins).items())))
    print("hand log by exit reason (in scope): "
          + "  ".join(f"{k}={v}" for k, v in
                      sorted(collections.Counter(h['reason'] for h in ins).items())))
    print("hand log by HTF flag (in scope): "
          + "  ".join(f"{k}={v}" for k, v in
                      sorted(collections.Counter(h['htf'] for h in ins).items())))


if __name__ == "__main__":
    main()
