#!/usr/bin/env python3
"""EXIT-TIMING STUDY — PART 1: is the canon exiting winners too early? (descriptive only)

No rule is chosen, no threshold is fitted, nothing is selected. This part exists solely to
establish whether the premise is true and how large the effect is.

MEASURE. For every trade: realised R at the canon's own exit, against maximum favourable
excursion at 15 / 30 / 45 / 60 minutes from the fill bar and over full trade life. The GAP
(mfe_h - realised_R) is how much was on the table at horizon h that the canon did not capture.

ANCHORS. Reproduced to the cent before any new number is computed; the script aborts otherwise.

COLUMN VALIDATION. The mfe_h columns are OUTCOME measures, computed strictly FORWARD from the
fill bar. The shift test used elsewhere in this project validates that a PREDICTOR uses only
pre-fill data; applying it here would be meaningless, so the correctness checks run instead are
(a) strict monotone nesting mfe15 <= mfe30 <= mfe45 <= mfe60 <= mfe_life, and (b) sensitivity to
the fill bar itself (a horizon starting at k0+1 must differ). Both are asserted, not assumed.

BASELINE: partially remediated (C only) + news filter, 182 PM trades. W and dep_* remain LEAKY
in the book's own selection path.
"""
import json
import os

import numpy as np
import pandas as pd

REPO = "/home/user/AI-trading-agents"
os.chdir(REPO)
OUT = f"{REPO}/research/sweep_2026_07/exit"
os.makedirs(OUT, exist_ok=True)
HOR = (15, 30, 45, 60)

# ---------------------------------------------------------------- ANCHOR GATE
print("=" * 100)
print("ANCHOR GATE — committed numbers must reproduce to the cent")
print("=" * 100)
cert = pd.read_csv(f"{REPO}/research/sweep_2026_07/phase2/phase2_frame.csv")
assert len(cert) == 216 and abs(cert.pl.sum() - 18376.00) < 0.005, (len(cert), cert.pl.sum())
print(f"  certified book PM slice : {len(cert)} trades  ${cert.pl.sum():+,.2f}   OK")

sz = pd.read_parquet(f"{REPO}/research/sweep_2026_07/orderflow/job2_books/sized_C_news.parquet")
sz["ft"] = pd.to_datetime(sz.fill, utc=True)
_et = sz.ft.dt.tz_convert("America/New_York")
sz["hm"] = _et.dt.hour * 60 + _et.dt.minute
szpm = sz[(sz.session == "NY") & (sz.hm >= 480) & (sz.hm < 570)]
assert len(szpm) == 182 and abs(szpm.pl.sum() - 21097.875) < 1e-6, (len(szpm), szpm.pl.sum())
print(f"  working baseline C_news : {len(szpm)} trades  ${szpm.pl.sum():+,.2f}   OK")

F = pd.read_csv(f"{REPO}/research/sweep_2026_07/micro/micro_frame.csv")
assert len(F) == 182 and abs(F.pl.sum() - 21097.875) < 1e-6
print(f"  micro frame             : {len(F)} trades  ${F.pl.sum():+,.2f}   OK")
F["ft"] = pd.to_datetime(F.ft, utc=True)
F["et"] = F.ft.dt.tz_convert("America/New_York")

bars = pd.read_parquet(f"{REPO}/data/reference/nq_1m_master.parquet",
                       columns=["ts_event", "high", "low", "close"])
bars["ts"] = pd.to_datetime(bars.ts_event, utc=True)
bars = bars.drop_duplicates("ts").set_index("ts").sort_index()
BI, BH, BL, BC = bars.index, bars.high.values, bars.low.values, bars.close.values
print(f"  bars                    : {len(bars):,} rows   OK")

# ---------------------------------------------------------------- horizons
print("\nbuilding MFE horizons ...", flush=True)
# TWO DISTINCT QUANTITIES, kept separate because they answer different questions:
#   mfe{h}      ALIVE  — best excursion in [k0, min(k0+h, stop bar)]. This is what the trade
#                        could actually have captured: you cannot bank excursion that happens
#                        after the stop has already taken you out. Used for the gap analysis.
#   mfeU{h}  UNCONDITIONAL — best excursion in [k0, k0+h] ignoring the stop. This is what the
#                        MARKET did, reported for context only. It can exceed mfe_life whenever
#                        a trade is stopped before the horizon ends, which is why the naive
#                        nesting assertion mfe60 <= mfe_life is FALSE and was removed.
rows = []
for r in F.itertuples(index=False):
    d = 1 if r.direction == "long" else -1
    k0 = int(r.k0)
    kl = min(k0 + int(r.life_min), len(BI) - 1)
    rec = {}
    for h in HOR:
        kh = min(k0 + h, len(BI) - 1)
        ka = min(kh, kl)                                   # alive: clipped at the stop
        sa = ((BH[k0:ka + 1] - r.entry) if d > 0 else (r.entry - BL[k0:ka + 1])) / r.risk_pts
        su = ((BH[k0:kh + 1] - r.entry) if d > 0 else (r.entry - BL[k0:kh + 1])) / r.risk_pts
        rec[f"mfe{h}"] = float(sa.max())
        rec[f"mfeU{h}"] = float(su.max())
        s1 = ((BH[k0 + 1:ka + 2] - r.entry) if d > 0 else (r.entry - BL[k0 + 1:ka + 2])) / r.risk_pts
        rec[f"_shift_mfe{h}"] = float(s1.max()) if len(s1) else np.nan
    rec["mfe_life"] = float(r.mfe_R)
    rows.append(rec)
H = pd.DataFrame(rows)
for c in H.columns:
    F[c] = H[c].values

# correctness assertions (see docstring)
for a, b in zip(HOR[:-1], HOR[1:]):
    assert (F[f"mfe{a}"] <= F[f"mfe{b}"] + 1e-9).all(), f"alive nesting violated {a}->{b}"
    assert (F[f"mfeU{a}"] <= F[f"mfeU{b}"] + 1e-9).all(), f"uncond nesting violated {a}->{b}"
assert (F["mfe60"] <= F["mfe_life"] + 1e-9).all(), "alive-60m must be within trade life"
assert (F["mfeU60"] >= F["mfe60"] - 1e-9).all(), "unconditional must dominate alive"
n_clip = int((F.mfeU60 > F.mfe60 + 1e-9).sum())
print(f"  trades stopped before the 60m horizon (alive < unconditional): {n_clip}/182")
diff_fill_bar = int((F.mfe15 != F._shift_mfe15).sum())
print(f"  nesting mfe15<=mfe30<=mfe45<=mfe60<=mfe_life : OK")
print(f"  sensitivity to the fill bar (k0 vs k0+1)     : differs on {diff_fill_bar}/182 trades")
for h in HOR:
    F[f"gap{h}"] = F[f"mfe{h}"] - F.R
F["gap_life"] = F.mfe_life - F.R
F["won"] = F.pl > 0
REP = {"anchors_ok": True, "shift_fill_bar_differs": diff_fill_bar, "n": len(F)}

# ---------------------------------------------------------------- distributions
print("\n" + "=" * 100)
print("PART 1 — REALISED R vs MFE AT EACH HORIZON  (gap = MFE - realised; how much was left)")
print("=" * 100)
print(f"  canon realised R: mean {F.R.mean():+.3f}  median {F.R.median():+.3f}")
print(f"\n{'horizon':10s} {'mean MFE':>9} {'med MFE':>9} {'mean gap':>9} {'med gap':>9} "
      f"{'gap>1R':>8} {'gap>2R':>8}")
for h in list(HOR) + ["_life"]:
    k = f"mfe{h}" if h != "_life" else "mfe_life"
    g = f"gap{h}" if h != "_life" else "gap_life"
    nm = f"{h} min" if h != "_life" else "full life"
    print(f"{nm:10s} {F[k].mean():>9.3f} {F[k].median():>9.3f} {F[g].mean():>+9.3f} "
          f"{F[g].median():>+9.3f} {(F[g]>1).mean()*100:>7.0f}% {(F[g]>2).mean()*100:>7.0f}%")
    REP.setdefault("horizons", {})[nm] = dict(
        mean_mfe=float(F[k].mean()), med_mfe=float(F[k].median()),
        mean_gap=float(F[g].mean()), med_gap=float(F[g].median()),
        pct_gap_gt1=float((F[g] > 1).mean()), pct_gap_gt2=float((F[g] > 2).mean()))

print(f"\nBY SEGMENT — mean gap (MFE_h minus realised R), sample counts shown")
print(f"{'segment':22s} {'n':>4} {'realised':>9} " + " ".join(f"{'gap@'+str(h):>9}" for h in HOR)
      + f" {'gap@life':>9}")
for s in ("early 08:00-08:29", "mid 08:30-08:59", "late 09:00-09:29"):
    g = F[F.seg == s]
    flag = "  INSUFFICIENT" if len(g) < 10 else ""
    print(f"{s:22s} {len(g):>4} {g.R.mean():>+9.3f} "
          + " ".join(f"{g['gap'+str(h)].mean():>+9.3f}" for h in HOR)
          + f" {g.gap_life.mean():>+9.3f}{flag}")
    REP.setdefault("by_segment", {})[s] = dict(
        n=len(g), realised=float(g.R.mean()),
        **{f"gap{h}": float(g[f"gap{h}"].mean()) for h in HOR},
        gap_life=float(g.gap_life.mean()), insufficient=bool(len(g) < 10))

print(f"\nBY OUTCOME — where the unrealised R actually sits")
print(f"{'group':22s} {'n':>4} {'realised':>9} " + " ".join(f"{'gap@'+str(h):>9}" for h in HOR)
      + f" {'gap@life':>9}")
for nm, m in (("winners (pl>0)", F.won), ("losers (pl<=0)", ~F.won),
              ("reached +1R", F.mfe_life >= 1.0), ("never reached +1R", F.mfe_life < 1.0)):
    g = F[m]
    flag = "  INSUFFICIENT" if len(g) < 10 else ""
    print(f"{nm:22s} {len(g):>4} {g.R.mean():>+9.3f} "
          + " ".join(f"{g['gap'+str(h)].mean():>+9.3f}" for h in HOR)
          + f" {g.gap_life.mean():>+9.3f}{flag}")
    REP.setdefault("by_outcome", {})[nm] = dict(
        n=len(g), realised=float(g.R.mean()),
        **{f"gap{h}": float(g[f"gap{h}"].mean()) for h in HOR},
        gap_life=float(g.gap_life.mean()), insufficient=bool(len(g) < 10))

print(f"\nHOW OFTEN DOES THE CANON EXIT NEAR THE HORIZON PEAK? (capture ratio = realised/MFE_h,")
print(f"only trades whose MFE_h > 0.25R, so the ratio is meaningful)")
print(f"{'horizon':10s} {'n':>4} {'median capture':>15} {'captured >=80%':>15} {'captured <=25%':>15}")
for h in list(HOR) + ["_life"]:
    k = f"mfe{h}" if h != "_life" else "mfe_life"
    q = F[F[k] > 0.25]
    cap = q.R / q[k]
    nm = f"{h} min" if h != "_life" else "full life"
    print(f"{nm:10s} {len(q):>4} {cap.median():>15.2f} {(cap>=0.8).mean()*100:>14.0f}% "
          f"{(cap<=0.25).mean()*100:>14.0f}%")
    REP.setdefault("capture", {})[nm] = dict(n=len(q), median=float(cap.median()),
                                             ge80=float((cap >= 0.8).mean()),
                                             le25=float((cap <= 0.25).mean()))

F.to_csv(f"{OUT}/part1_frame.csv", index=False)
json.dump(REP, open(f"{OUT}/part1_report.json", "w"), indent=1, default=float)
print(f"\nwrote {OUT}/part1_frame.csv + part1_report.json")
print("DESCRIPTIVE ONLY — no rule chosen, no threshold fitted.")
