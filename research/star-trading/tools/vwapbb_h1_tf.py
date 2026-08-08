#!/usr/bin/env python3
"""H1 — ENTRY TIMEFRAME. Does entry_tf explain the stop-distance gap between the
detector population and the hand log? Diagnosis only: no selector, no P&L."""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections
from pathlib import Path

import pyarrow.parquet as pq

P = Path(__file__).resolve().parents[2] / "vwap-bb" / "data" / "candidates.parquet"
HAND = Path(__file__).resolve().parents[3] / "data" / "reference" / "feb2026_hand_log.csv"


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def load(reading="A", warm="prior"):
    t = pq.read_table(P).to_pydict()
    n = len(t["session_date"])
    return [{k: t[k][i] for k in t} for i in range(n)
            if t["trigger_reading"][i] == reading and t["warmup_treatment"][i] == warm]


def handlog():
    import csv
    rows = list(csv.DictReader(HAND.read_text().splitlines()))
    def mins(s):
        s = (s or "").strip()
        if not s or ":" not in s:
            return None
        h, m = s.split(":")[:2]
        return int(h) * 60 + int(m)
    out = []
    for r in rows:
        k = {kk.strip(): (vv or "").strip() for kk, vv in r.items() if kk}
        t = mins(k.get("Entry Time"))
        try:
            stop = float(k.get("Stop pts", "") or "nan")
        except ValueError:
            stop = float("nan")
        out.append({"t": t, "stop": stop, "res": k.get("Result", ""),
                    "R": k.get("R Multiple", ""), "date": k.get("Date", "")})
    return out


def row(lbl, xs, extra=""):
    if not xs:
        print(f"{lbl:>14} {'—':>7}")
        return
    print(f"{lbl:>14} {len(xs):>7} {min(xs):>8.2f} {pct(xs,.10):>8.2f} "
          f"{pct(xs,.25):>8.2f} {pct(xs,.50):>8.2f} {pct(xs,.75):>8.2f} "
          f"{pct(xs,.90):>8.2f} {max(xs):>8.2f} {extra}")


HDR = (f"{'slice':>14} {'n':>7} {'min':>8} {'p10':>8} {'p25':>8} {'p50':>8} "
       f"{'p75':>8} {'p90':>8} {'max':>8}")


def main():
    for reading in ("A", "B", "C", "D"):
        rows = load(reading)
        nsess = len({r["session_date"] for r in rows})
        print(f"\n{'='*100}")
        print(f"READING {reading}  n={len(rows)}  sessions={nsess}")
        print(f"{'='*100}")

        print("\n-- STOP DISTANCE (points) by entry_tf --")
        print(HDR)
        for tf in (1, 2, 3, 5):
            g = [r for r in rows if r["entry_tf"] == tf]
            row(f"tf={tf}m", [r["stop_distance_points"] for r in g])
        row("ALL", [r["stop_distance_points"] for r in rows])

        print("\n-- TARGET DISTANCE (points, entry->spec target) by entry_tf --")
        print(HDR)
        for tf in (1, 2, 3, 5):
            g = [r for r in rows if r["entry_tf"] == tf]
            row(f"tf={tf}m", [r["stop_distance_points"] * r["available_R_to_spec_target"]
                              for r in g])
        row("ALL", [r["stop_distance_points"] * r["available_R_to_spec_target"] for r in rows])

        print("\n-- AVAILABLE R TO SPEC TARGET by entry_tf --")
        print(HDR)
        for tf in (1, 2, 3, 5):
            g = [r for r in rows if r["entry_tf"] == tf]
            row(f"tf={tf}m", [r["available_R_to_spec_target"] for r in g])

        print("\n-- CANDIDATES PER SESSION by entry_tf (raw, pre-cap) --")
        print(f"{'tf':>8} {'records':>9} {'/session':>9} {'sess w/ >=1':>12} "
              f"{'dedup close-min':>16} {'dedup/sess':>11}")
        for tf in (1, 2, 3, 5):
            g = [r for r in rows if r["entry_tf"] == tf]
            s1 = len({r["session_date"] for r in g})
            dd = len({(r["session_date"], r["signal_minute"], r["direction"]) for r in g})
            print(f"{tf:>7}m {len(g):>9} {len(g)/nsess:>9.2f} {s1:>12} "
                  f"{dd:>16} {dd/nsess:>11.2f}")

        print("\n-- FRACTION OF CANDIDATES WITH STOP >= X POINTS, by entry_tf --")
        print(f"{'tf':>8} " + " ".join(f"{'>='+str(x)+'pt':>9}" for x in (3,5,7,10,15,20,25,35)))
        for tf in (1, 2, 3, 5):
            g = [r["stop_distance_points"] for r in rows if r["entry_tf"] == tf]
            if not g:
                continue
            print(f"{tf:>7}m " + " ".join(
                f"{sum(1 for x in g if x>=t)/len(g)*100:>8.1f}%" for t in (3,5,7,10,15,20,25,35)))
        g = [r["stop_distance_points"] for r in rows]
        print(f"{'ALL':>8} " + " ".join(
            f"{sum(1 for x in g if x>=t)/len(g)*100:>8.1f}%" for t in (3,5,7,10,15,20,25,35)))
        if reading != "A":
            continue

    # hand log reference
    hl = handlog()
    ins = [h for h in hl if h["t"] is not None and h["t"] >= 9*60+36
           and h["stop"] == h["stop"]]
    allt = [h for h in hl if h["stop"] == h["stop"]]
    print(f"\n{'='*100}\nHAND LOG REFERENCE — stop distance (points)\n{'='*100}")
    print(HDR)
    row("full log", [h["stop"] for h in allt])
    row("in-scope", [h["stop"] for h in ins])

    # overlap test: what fraction of detector stops fall inside the hand-log range
    rows = load("A")
    lo, hi = min(h["stop"] for h in ins), max(h["stop"] for h in ins)
    print(f"\n-- OVERLAP with hand-log in-scope range [{lo:.2f}, {hi:.2f}] pts, reading A --")
    print(f"{'tf':>8} {'n':>8} {'in range':>10} {'%':>8} {'>= 11.0':>9} {'%':>8}")
    for tf in (1, 2, 3, 5):
        g = [r["stop_distance_points"] for r in rows if r["entry_tf"] == tf]
        if not g:
            continue
        inr = sum(1 for x in g if lo <= x <= hi)
        ge = sum(1 for x in g if x >= lo)
        print(f"{tf:>7}m {len(g):>8} {inr:>10} {inr/len(g)*100:>7.1f}% {ge:>9} {ge/len(g)*100:>7.1f}%")

    # what would a 5m-only, higher-TF-only population look like?
    print("\n-- MEDIAN STOP BY entry_tf ACROSS ALL READINGS (points) --")
    print(f"{'reading':>9} " + " ".join(f"{'tf='+str(t)+'m':>10}" for t in (1,2,3,5)))
    for reading in ("A", "B", "C", "D"):
        rr = load(reading)
        cells = []
        for tf in (1, 2, 3, 5):
            g = [r["stop_distance_points"] for r in rr if r["entry_tf"] == tf]
            cells.append(f"{pct(g,.5):>10.2f}" if g else f"{'—':>10}")
        print(f"{reading:>9} " + " ".join(cells))

    # trigger-candle range by tf, as the ceiling on any wick-anchored stop
    print("\n-- TRIGGER-CANDLE-DERIVED CEILING: stop dist vs cluster span, reading A --")
    print(f"{'tf':>8} {'med stop':>10} {'med span':>10} {'med headroom':>14}")
    for tf in (1, 2, 3, 5):
        g = [r for r in rows if r["entry_tf"] == tf]
        if not g:
            continue
        hd = [r["headroom_points"] for r in g if r["headroom_points"] is not None]
        print(f"{tf:>7}m {pct([r['stop_distance_points'] for r in g],.5):>10.2f} "
              f"{pct([r['cluster_span_points'] for r in g],.5):>10.2f} "
              f"{pct(hd,.5) if hd else float('nan'):>14.2f}")


if __name__ == "__main__":
    main()
