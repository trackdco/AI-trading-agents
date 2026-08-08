#!/usr/bin/env python3
"""H2 (target selection), H3 (stop anchor) and the FEASIBILITY MAP.

Diagnosis only. Nothing here adopts a rule, computes P&L, ranks cells or calls a
cell better. The map reports which constraints each cell satisfies, nothing more.
"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[3]
G = ROOT / "research" / "vwap-bb" / "data" / "geometry.parquet"

TRIPWIRE = 0.4862          # gate 6, /4 correction, p1=0.50, 539 sessions
RR_FLOOR = 1.5
HAND_MED_STOP = 35.00      # in-scope hand-log median
STOPS = (3, 5, 7, 10, 15, 20, 25, 35)
COSTS = (0.25, 0.50, 1.00)


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def load(reading="A"):
    t = pq.read_table(G).to_pydict()
    n = len(t["session_date"])
    return [{k: t[k][i] for k in t} for i in range(n) if t["trigger_reading"][i] == reading]


def dist(lbl, xs):
    if not xs:
        print(f"{lbl:>26} {'—':>7}")
        return
    print(f"{lbl:>26} {len(xs):>7} {min(xs):>8.2f} {pct(xs,.10):>8.2f} {pct(xs,.25):>8.2f} "
          f"{pct(xs,.50):>8.2f} {pct(xs,.75):>8.2f} {pct(xs,.90):>8.2f} {max(xs):>9.2f}")


HDR = (f"{'':>26} {'n':>7} {'min':>8} {'p10':>8} {'p25':>8} {'p50':>8} {'p75':>8} "
       f"{'p90':>8} {'max':>9}")


def main():
    reading = sys.argv[1] if len(sys.argv) > 1 else "A"
    rows = load(reading)
    NS = len({r["session_date"] for r in rows})
    print(f"geometry.parquet, reading {reading}: {len(rows)} pre-RR-floor records, "
          f"{NS} sessions\n")

    # ------------------------------------------------------------------ H2
    print("=" * 104)
    print("H2 — TARGET SELECTION.  Distance from entry to the 1st / 2nd / 3rd nearest")
    print("     opposing menu level, front-run adjusted by F=2.0 pts, deduped to 1 tick.")
    print("=" * 104)
    print(HDR)
    for k, lab in ((1, "nearest (spec rule 5)"), (2, "2nd nearest"), (3, "3rd nearest")):
        dist(lab, [r[f"tgt{k}_points"] for r in rows if r.get(f"tgt{k}_points")])
    dist("deepest rung in menu", [r["tgt_deepest_points"] for r in rows
                                  if r.get("tgt_deepest_points")])
    dist("nearest liquidity extreme", [r["tgt_nearest_extreme_points"] for r in rows
                                       if r.get("tgt_nearest_extreme_points")])
    dist("furthest liquidity extreme", [r["tgt_furthest_extreme_points"] for r in rows
                                        if r.get("tgt_furthest_extreme_points")])
    dm = [r["tgt_deepest_points"] for r in rows if r.get("tgt_deepest_points")]
    print(f"\n  can the spec's OWN level menu reach the hand log's 155.2-pt median?")
    print(f"     records whose DEEPEST available rung is >= 155.2 pts: "
          f"{sum(1 for x in dm if x >= 155.2)}/{len(dm)} = "
          f"{sum(1 for x in dm if x >= 155.2)/len(dm)*100:.1f}%")
    print(f"     >= 84.2 pts (hand-log minimum winner):              "
          f"{sum(1 for x in dm if x >= 84.2)/len(dm)*100:.1f}%")
    print()
    nt = collections.Counter(r["n_targets"] for r in rows)
    print("  levels available beyond entry: "
          + "  ".join(f"{k}:{nt[k]}" for k in sorted(nt)[:8])
          + f"   (>=3 on {sum(v for k,v in nt.items() if k>=3)/len(rows)*100:.1f}%)")
    print(f"\n  hand-log in-scope winners, implied target distance (stop x R):")
    print(f"     median 155.2 pts, range 84.2 - 201.2  (n=13, source feb2026_hand_log.csv)")
    print(f"  ratio hand-log median / detector nearest-target median: "
          f"{155.2 / pct([r['tgt1_points'] for r in rows], .5):.1f}x")
    print(f"  ratio hand-log median / detector 3rd-target median:     "
          f"{155.2 / pct([r['tgt3_points'] for r in rows if r['tgt3_points']], .5):.1f}x")

    # ------------------------------------------------------------------ H3
    print("\n" + "=" * 104)
    print("H3 — STOP ANCHOR.  Implied stop DISTANCE from the same E1 entry under")
    print("     four anchors. The hand log records distances only, never prices, so")
    print("     none of these can be confirmed as the anchor Angus actually used.")
    print("=" * 104)
    print(HDR)
    dist("wick + 1 tick [FROZEN]", [r["stop_wick_1tick"] for r in rows if r["stop_wick_1tick"]])
    dist("cluster far edge", [r["stop_cluster_far_edge"] for r in rows if r["stop_cluster_far_edge"]])
    dist("prior swing (fractal N=2)", [r["stop_prior_swing"] for r in rows if r["stop_prior_swing"]])
    dist("trigger-candle range", [r["stop_candle_range"] for r in rows if r["stop_candle_range"]])
    atr = [r["atr_entry_tf"] for r in rows if r["atr_entry_tf"]]
    for k in (1, 2, 3):
        dist(f"{k}.0 x ATR(20) entry TF", [x * k for x in atr])
    atd = [r["atr_daily"] for r in rows if r["atr_daily"]]
    for k in (0.05, 0.10, 0.20):
        dist(f"{k:.2f} x ATR(14) daily", [x * k for x in atd])
    print(f"\n{'':>26} {'median':>9} {'x to reach 35.0':>17} {'% >= 11.0 pts':>15} {'% >= 35.0 pts':>15}")
    for lab, key in (("wick + 1 tick", "stop_wick_1tick"),
                     ("cluster far edge", "stop_cluster_far_edge"),
                     ("prior swing", "stop_prior_swing"),
                     ("candle range", "stop_candle_range")):
        xs = [r[key] for r in rows if r[key]]
        m = pct(xs, .5)
        print(f"{lab:>26} {m:>9.2f} {HAND_MED_STOP/m:>16.1f}x "
              f"{sum(1 for x in xs if x>=11)/len(xs)*100:>14.1f}% "
              f"{sum(1 for x in xs if x>=35)/len(xs)*100:>14.1f}%")
    for k in (1, 2, 3):
        xs = [x * k for x in atr]
        m = pct(xs, .5)
        print(f"{str(k)+'.0 x ATR entry TF':>26} {m:>9.2f} {HAND_MED_STOP/m:>16.1f}x "
              f"{sum(1 for x in xs if x>=11)/len(xs)*100:>14.1f}% "
              f"{sum(1 for x in xs if x>=35)/len(xs)*100:>14.1f}%")

    print(f"\n  entry inside the firing cluster: "
          f"{sum(1 for r in rows if r['entry_inside_cluster'])/len(rows)*100:.1f}% of records")
    print(f"  prior swing resolvable:          "
          f"{sum(1 for r in rows if r['stop_prior_swing'])/len(rows)*100:.1f}%")

    # --------------------------------------------------------- FEASIBILITY
    print("\n" + "=" * 104)
    print("FEASIBILITY MAP.  Rows = minimum-stop floor (effective stop = max(wick stop, floor)).")
    print("Columns = which rung of the target ladder is taken. Constraints satisfied only.")
    print("NOT ranked, no P&L, no cell recommended.")
    print("=" * 104)
    print(f"\ntripwire = {TRIPWIRE} trades/session (gate 6). The tripwire column uses")
    print("SESSIONS WITH >=1 SURVIVOR / total sessions — a selector-free LOWER bound on")
    print("trades per session under one-position-at-a-time. The Vault cap of 3/day can")
    print("only reduce the raw count, never this floor.\n")

    for k in (1, 2, 3):
        key = f"tgt{k}_points"
        lab = {1: "NEAREST", 2: "2ND NEAREST", 3: "3RD NEAREST"}[k]
        print(f"\n--- target rule: {lab} ---")
        print(f"{'floor':>6} {'clears 1.5R':>12} {'survivors':>10} {'raw/sess':>9} "
              f"{'dedup/sess':>11} {'sess>=1':>9} {'floor/sess':>11} {'trip?':>6} "
              f"{'med stop':>9} {'p0 c=.25':>9} {'p0 c=.50':>9} {'p0 c=1.0':>9}")
        for S in STOPS:
            elig = [r for r in rows if r.get(key)]
            surv = [r for r in elig
                    if r[key] / max(r["stop_wick_1tick"] or 0.0, S) >= RR_FLOOR]
            frac = len(surv) / len(elig) * 100 if elig else 0.0
            dd = len({(r["session_date"], r["signal_minute"], r["direction"]) for r in surv})
            s1 = len({r["session_date"] for r in surv})
            floor_ps = s1 / NS
            ms = pct([max(r["stop_wick_1tick"] or 0.0, S) for r in surv], .5) if surv else float("nan")
            ps = [(ms + c) / (ms * (1 + RR_FLOOR)) * 100 for c in COSTS] if surv else [float("nan")] * 3
            print(f"{S:>5}pt {frac:>11.1f}% {len(surv):>10} {len(surv)/NS:>9.2f} "
                  f"{dd/NS:>11.2f} {s1:>9} {floor_ps:>11.3f} "
                  f"{'YES' if floor_ps >= TRIPWIRE else 'no':>6} {ms:>9.2f} "
                  + " ".join(f"{p:>8.2f}%" for p in ps))

    print("\n" + "=" * 104)
    print("SAME MAP, RESTRICTED TO entry_tf = 5m  (the hand log's most-used TF, 7 of 19)")
    print("=" * 104)
    r5 = [r for r in rows if r["entry_tf"] == 5]
    NS5 = len({r["session_date"] for r in r5})
    for k in (1, 3):
        key = f"tgt{k}_points"
        print(f"\n--- target rule: {'NEAREST' if k==1 else '3RD NEAREST'} (5m only, "
              f"{len(r5)} records, {NS5} sessions) ---")
        print(f"{'floor':>6} {'clears 1.5R':>12} {'survivors':>10} {'raw/sess':>9} "
              f"{'sess>=1':>9} {'floor/sess':>11} {'trip?':>6}")
        for S in STOPS:
            elig = [r for r in r5 if r.get(key)]
            surv = [r for r in elig
                    if r[key] / max(r["stop_wick_1tick"] or 0.0, S) >= RR_FLOOR]
            s1 = len({r["session_date"] for r in surv})
            print(f"{S:>5}pt {len(surv)/len(elig)*100 if elig else 0:>11.1f}% {len(surv):>10} "
                  f"{len(surv)/NS:>9.2f} {s1:>9} {s1/NS:>11.3f} "
                  f"{'YES' if s1/NS >= TRIPWIRE else 'no':>6}")


if __name__ == "__main__":
    main()
