#!/usr/bin/env python3
"""Brake's pre-scoring tasks 1 & 2 (2026-07-28). No outcomes examined.

TASK 1 — reconcile the bucket censuses AT TRADE LEVEL. Phase 1: 138/47/31 (half-open
[480,510)/[510,540)/[540,570) on hm). Step 2: 139/47/30 (pd.cut (479,510]/(510,540]/(540,570]).
Brake's point: one 08:30 edge trade can only move bucket1<->bucket2; the observed shift is
b1 +1, b2 0, b3 -1, which requires TWO boundary trades (one at exactly 08:30 AND one at exactly
09:00) or something worse. Identify every trade whose bucket differs, with timestamps.

TASK 2 — floored vs rounded fill stamps. Entries are LIMIT-ONLY, so the fill price must trade
inside its true minute's bar range. Test each trade's entry against the STAMPED minute's bar
[low, high]; where it fails, test the PRIOR minute (rounded-up signature) and the NEXT minute.
Tolerance: exact bar range, +/- 1 tick (0.25) to absorb float representation only.
"""
import json
import os

import numpy as np
import pandas as pd

REPO = "/home/user/AI-trading-agents"
OUT = os.path.join(REPO, "research/sweep_2026_07/orderflow")

F = pd.read_csv(f"{REPO}/research/sweep_2026_07/phase2/phase2_frame.csv")
F["ft"] = pd.to_datetime(F.ft, utc=True)
F["et"] = F.ft.dt.tz_convert("America/New_York")
F["hm"] = F.et.dt.hour * 60 + F.et.dt.minute
assert len(F) == 216

# ---------------------------------------------------------------- TASK 1
print("=" * 88)
print("TASK 1 — TRADE-LEVEL BUCKET RECONCILIATION")
print("=" * 88)
lab = ["08:00-08:29", "08:30-08:59", "09:00-09:29"]
F["b_phase1"] = pd.cut(F.hm, [479.5, 509.5, 539.5, 569.5], labels=lab)   # == [480,510) etc on ints
F["b_step2"] = pd.cut(F.hm, [479, 510, 540, 570], labels=lab)            # the step-2 binning
c1 = F.b_phase1.value_counts().reindex(lab)
c2 = F.b_step2.value_counts().reindex(lab)
print(f"  phase1 convention: {c1.tolist()}   step2 convention: {c2.tolist()}")
diff = F[F.b_phase1 != F.b_step2]
print(f"  trades bucketed differently: {len(diff)}")
for r in diff.itertuples(index=False):
    print(f"    day {r.day}  fill_ET {r.et.strftime('%H:%M:%S')}  hm={r.hm}  "
          f"phase1 -> {r.b_phase1}   step2 -> {r.b_step2}")
print("  arithmetic check: the observed census shift is b1 +1, b2 0, b3 -1;")
print("  one 08:30 trade gives (+1,-1,0) and one 09:00 trade gives (0,+1,-1); sum = (+1,0,-1).")
print(f"  boundary trades at exactly 08:30 (hm=510): {int((F.hm==510).sum())}   "
      f"at exactly 09:00 (hm=540): {int((F.hm==540).sum())}")

# ---------------------------------------------------------------- TASK 2
print("\n" + "=" * 88)
print("TASK 2 — FLOORED vs ROUNDED FILL STAMPS (limit-entry containment test)")
print("=" * 88)
cb = pd.read_parquet(f"{REPO}/output/canon_book.parquet")
cb["ft"] = pd.to_datetime(cb.fill, utc=True)
cb["rk"] = cb["risk"].round(4)
F["rk"] = F.risk_pts.round(4)
J = F.merge(cb.drop_duplicates(["ft", "direction", "rk"])[["ft", "direction", "rk", "entry"]],
            on=["ft", "direction", "rk"], how="left")
assert J.entry.notna().all() and len(J) == 216

bars = pd.read_parquet(f"{REPO}/data/reference/nq_1m_master.parquet",
                       columns=["ts_event", "high", "low"])
bars["ts"] = pd.to_datetime(bars.ts_event).dt.tz_convert("UTC")
bars = bars.drop_duplicates("ts").set_index("ts").sort_index()
H, L, BI = bars.high, bars.low, bars.index
TOL = 0.25  # one tick, float-representation absorbtion only

def contains(minute, px):
    k = BI.searchsorted(minute)
    if k >= len(BI) or BI[k] != minute:
        return None                                   # no bar at that minute
    return bool(L.iloc[k] - TOL <= px <= H.iloc[k] + TOL)

res = dict(stamped=0, prior_only=0, next_only=0, both_adjacent_only=0, nowhere=0, nobar=0)
bad = []
for r in J.itertuples(index=False):
    m = r.ft.floor("min")
    # bars are stamped by minute START in this repo's convention: the bar whose ts == m covers
    # [m, m+1). A floored stamp means the fill happened inside [m, m+1) -> entry in bar(m).
    in_m = contains(m, r.entry)
    if in_m is None:
        res["nobar"] += 1
        continue
    if in_m:
        res["stamped"] += 1
        continue
    in_prev = contains(m - pd.Timedelta(minutes=1), r.entry)
    in_next = contains(m + pd.Timedelta(minutes=1), r.entry)
    if in_prev and not in_next:
        res["prior_only"] += 1
        bad.append((r.day, str(r.ft), "prior_only"))
    elif in_next and not in_prev:
        res["next_only"] += 1
        bad.append((r.day, str(r.ft), "next_only"))
    elif in_prev and in_next:
        res["both_adjacent_only"] += 1
        bad.append((r.day, str(r.ft), "both_adjacent"))
    else:
        res["nowhere"] += 1
        bad.append((r.day, str(r.ft), "nowhere"))
print(f"  entry price inside the STAMPED minute's bar range : {res['stamped']}/216")
print(f"  outside stamped, inside PRIOR minute only          : {res['prior_only']}   "
      f"<- the rounded-up signature")
print(f"  outside stamped, inside NEXT minute only           : {res['next_only']}")
print(f"  outside stamped, inside both adjacent              : {res['both_adjacent_only']}")
print(f"  in none of the three                               : {res['nowhere']}")
print(f"  no bar at stamped minute                           : {res['nobar']}")
if bad:
    print("  exceptions:")
    for d, t, w in bad:
        print(f"    {d}  {t}  {w}")
print("\n  reading: floored stamps -> ~100% inside the stamped bar (a limit fill's price must")
print("  trade within its own minute). A material prior_only count means rounded stamps and")
print("  every pre-fill window in the feature set shifts by one minute.")

json.dump(dict(task1=dict(phase1=c1.tolist(), step2=c2.tolist(),
                          moved=[dict(day=r.day, fill_et=r.et.strftime('%H:%M:%S'), hm=int(r.hm),
                                      phase1=str(r.b_phase1), step2=str(r.b_step2))
                                 for r in diff.itertuples(index=False)]),
               task2=res, task2_exceptions=bad),
          open(f"{OUT}/task12_report.json", "w"), indent=1)
print(f"\nwrote {OUT}/task12_report.json")
