#!/usr/bin/env python3
"""PRE-MARKET MICROSTRUCTURE STUDY — MFE ceilings, liquidity walls, and chop by time of day.

Brake's questions, 2026-07-29:
  Q-A  Is there a pattern where trades at certain pre-market times only reach +1-2R and then
       come back down?
  Q-B  Is early pre-market choppy for lack of volume? Test with heatmap liquidity: do entries
       with NO WALL ahead behave differently (nothing to target)?
  Q-C  Do later trades, near the open, get chopped or swept one way so no TP is hit, only SL?

WALLS ARE REBUILT CLEAN. The canon's dep_* family FAILED the Phase-0 lookahead audit (the W
check flips on 41.6% of trades when re-read pre-fill). The raw MBP-10 archive survived the
container wipes, so the wall features here are rebuilt from the snapshot at FILL MINUTE MINUS
ONE — provably before the fill minute even begins, regardless of intra-minute fill timing. The
at-fill-minute version is ALSO computed so the size of the original leak is measured, not
asserted. Definitions follow src/canon/features.py::depth_at exactly, only the timestamp moves.

Everything here is DESCRIPTIVE. No rule is proposed and no threshold is fitted in this file;
the exit sweep is a separate, noise-floored script.

BASELINE: partially remediated (C only) + news filter, 182 PM trades. W and dep_* leaky in the
book's own SELECTION path — that is not fixed by this rebuild, which only makes the ANALYSIS
features here clean.
"""
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

REPO = "/home/user/AI-trading-agents"
os.chdir(REPO)
SRC = f"{REPO}/research/sweep_2026_07/orderflow"
OUT = f"{REPO}/research/sweep_2026_07/micro"
os.makedirs(OUT, exist_ok=True)
NY = "America/New_York"

F = pd.read_csv(f"{SRC}/part0_frame.csv")
F["ft"] = pd.to_datetime(F.ft, utc=True)
F["et"] = F.ft.dt.tz_convert(NY)
F["buck"] = ((F.fillhm - 480) // 5).astype(int)
F["seg"] = np.where(F.fillhm < 510, "early 08:00-08:29",
                    np.where(F.fillhm < 540, "mid 08:30-08:59", "late 09:00-09:29"))
print(f"{len(F)} trades")

bars = pd.read_parquet(f"{REPO}/data/reference/nq_1m_master.parquet",
                       columns=["ts_event", "high", "low", "close"])
bars["ts"] = pd.to_datetime(bars.ts_event, utc=True)
bars = bars.drop_duplicates("ts").set_index("ts").sort_index()
BI, BH, BL, BC = bars.index, bars.high.values, bars.low.values, bars.close.values


def load_depth_day(day):
    for folder in ("depth_2025", "depth_2026", "depth_apr2026"):
        p = Path(f"data/reference/{folder}/nq_depth_{day}_ny.csv")
        if p.exists():
            d = pd.read_csv(p)
            d["ts"] = pd.to_datetime(d.ts, utc=True).dt.tz_convert(NY)
            return d
    return None


def depth_at(dep, minute, entry, direction):
    """src/canon/features.py::depth_at, verbatim definition. Only the caller's `minute` moves."""
    sub = dep[dep.ts <= minute]
    if sub.empty:
        return {}
    b = sub[sub.ts == sub.ts.max()]
    bid, ask = b[b.side == "bid"], b[b.side == "ask"]
    if bid.empty or ask.empty:
        return {}
    tb, ta = bid["size"].sum(), ask["size"].sum()
    f = {"thick": tb + ta, "imb": (tb - ta) / max(tb + ta, 1),
         "spread": ask.price.min() - bid.price.max()}
    above, below = b[b.price > entry], b[b.price < entry]
    if len(above):
        w = above.loc[above["size"].idxmax()]
        f["wall_above_d"] = float(w.price - entry)
        f["wall_above_sz"] = float(w["size"])
    if len(below):
        w = below.loc[below["size"].idxmax()]
        f["wall_below_d"] = float(entry - w.price)
        f["wall_below_sz"] = float(w["size"])
    return f


print("rebuild walls at fill-1 (strictly pre-fill) and at fill (the leaky convention) ...",
      flush=True)
cache, rows = {}, []
for r in F.itertuples(index=False):
    if r.day not in cache:
        cache[r.day] = load_depth_day(r.day)
    dep = cache[r.day]
    fm = r.et.floor("min")
    clean = depth_at(dep, fm - pd.Timedelta(minutes=1), r.entry, r.direction) if dep is not None else {}
    leaky = depth_at(dep, fm, r.entry, r.direction) if dep is not None else {}
    d = 1 if r.direction == "long" else -1
    ahead_d = clean.get("wall_above_d") if d > 0 else clean.get("wall_below_d")
    ahead_sz = clean.get("wall_above_sz") if d > 0 else clean.get("wall_below_sz")
    behind_d = clean.get("wall_below_d") if d > 0 else clean.get("wall_above_d")
    lk_ahead = leaky.get("wall_above_d") if d > 0 else leaky.get("wall_below_d")
    rows.append(dict(has_depth=dep is not None and bool(clean),
                     wall_ahead_d=ahead_d, wall_ahead_sz=ahead_sz, wall_behind_d=behind_d,
                     thick=clean.get("thick"), imb=clean.get("imb"),
                     leak_wall_ahead_d=lk_ahead))
D = pd.DataFrame(rows)
for c in D.columns:
    F[c] = D[c].values
cov = int(F.has_depth.sum())
print(f"  depth coverage: {cov}/{len(F)} trades ({cov/len(F)*100:.0f}%)")
both = F[F.wall_ahead_d.notna() & F.leak_wall_ahead_d.notna()]
if len(both):
    diff = (both.wall_ahead_d != both.leak_wall_ahead_d).mean()
    print(f"  LEAK MEASURED: the wall-ahead distance differs between the fill-1 snapshot and "
          f"the at-fill snapshot on {diff*100:.1f}% of trades ({int((both.wall_ahead_d != both.leak_wall_ahead_d).sum())}/{len(both)})")

# ---------------------------------------------------------------- path shape per trade
print("path metrics ...", flush=True)
pm = []
for r in F.itertuples(index=False):
    d = 1 if r.direction == "long" else -1
    k0, kx = int(r.k0), int(r.k0) + int(r.life_min)
    kx = max(kx, k0 + 1)
    hi = ((BH[k0:kx + 1] - r.entry) if d > 0 else (r.entry - BL[k0:kx + 1])) / r.risk_pts
    lo = ((BL[k0:kx + 1] - r.entry) if d > 0 else (r.entry - BH[k0:kx + 1])) / r.risk_pts
    cl = ((BC[k0:kx + 1] - r.entry) if d > 0 else (r.entry - BC[k0:kx + 1])) / r.risk_pts
    k30 = min(k0 + 30, len(BI) - 1)
    c30 = ((BC[k0:k30 + 1] - r.entry) if d > 0 else (r.entry - BC[k0:k30 + 1])) / r.risk_pts
    path = float(np.abs(np.diff(c30)).sum())
    eff30 = float(abs(c30[-1] - c30[0]) / path) if path > 0 else np.nan
    s = np.sign(cl - cl.mean())
    pm.append(dict(t_mfe=int(np.argmax(hi)), t_mae=int(np.argmin(lo)),
                   eff30=eff30, crosses=float((np.abs(np.diff(s)) > 0).sum()),
                   mfe30=float(np.max(((BH[k0:k30 + 1] - r.entry) if d > 0
                                       else (r.entry - BL[k0:k30 + 1])) / r.risk_pts))))
P = pd.DataFrame(pm)
for c in P.columns:
    F[c] = P[c].values
F["adverse_first"] = F.t_mae < F.t_mfe
F["stalled_1_2R"] = (F.mfe_R >= 1.0) & (F.mfe_R < 2.0)
F["gave_back"] = (F.mfe_R >= 1.0) & (F.pl < 0)
F["sl_no_1R"] = (F.mfe_R < 1.0) & (F.pl < 0)
F.to_csv(f"{OUT}/micro_frame.csv", index=False)

REP = {"n": len(F), "depth_coverage": cov,
       "leak_pct": float(diff * 100) if len(both) else None}

# ---------------------------------------------------------------- Q-A: MFE ceiling by time
print("\n" + "=" * 108)
print("Q-A — DOES IT ONLY GO +1-2R THEN COME BACK? MFE ceiling by 5-minute bucket")
print("=" * 108)
lab = lambda k: f"{8 + (480 + 5 * k - 480) // 60:02d}:{(480 + 5 * k) % 60:02d}"
print(f"{'bucket':8s} {'n':>4} {'med MFE':>8} {'<1R':>6} {'1-2R':>6} {'2-4R':>6} {'4R+':>6} "
       f"{'gave back':>10} {'SL no 1R':>9} {'net':>9}")
qa = {}
for k in range(18):
    g = F[F.buck == k]
    if not len(g):
        continue
    b = [float((g.mfe_R < 1).mean()), float(((g.mfe_R >= 1) & (g.mfe_R < 2)).mean()),
         float(((g.mfe_R >= 2) & (g.mfe_R < 4)).mean()), float((g.mfe_R >= 4).mean())]
    qa[lab(k)] = dict(n=len(g), med_mfe=float(g.mfe_R.median()), bins=b,
                      gave_back=float(g.gave_back.mean()), sl_no_1r=float(g.sl_no_1R.mean()),
                      net=float(g.pl.sum()), insufficient=bool(len(g) < 10))
    flag = " *" if len(g) < 10 else ""
    print(f"{lab(k):8s} {len(g):>4} {g.mfe_R.median():>8.2f} {b[0]*100:>5.0f}% {b[1]*100:>5.0f}% "
          f"{b[2]*100:>5.0f}% {b[3]*100:>5.0f}% {g.gave_back.mean()*100:>9.0f}% "
          f"{g.sl_no_1R.mean()*100:>8.0f}% {g.pl.sum():>+9,.0f}{flag}")
print("  * = fewer than 10 trades, insufficient to distinguish edge from luck")
REP["qa_buckets"] = qa
print(f"\n{'segment':22s} {'n':>4} {'med MFE':>8} {'stall 1-2R':>11} {'gave back':>10} "
      f"{'SL no 1R':>9} {'meanR':>8} {'net':>9}")
for s in ("early 08:00-08:29", "mid 08:30-08:59", "late 09:00-09:29"):
    g = F[F.seg == s]
    print(f"{s:22s} {len(g):>4} {g.mfe_R.median():>8.2f} {g.stalled_1_2R.mean()*100:>10.0f}% "
          f"{g.gave_back.mean()*100:>9.0f}% {g.sl_no_1R.mean()*100:>8.0f}% {g.R.mean():>+8.3f} "
          f"{g.pl.sum():>+9,.0f}")
    REP.setdefault("qa_seg", {})[s] = dict(n=len(g), med_mfe=float(g.mfe_R.median()),
                                           stall=float(g.stalled_1_2R.mean()),
                                           gave_back=float(g.gave_back.mean()),
                                           sl_no_1r=float(g.sl_no_1R.mean()),
                                           meanR=float(g.R.mean()), net=float(g.pl.sum()))

# ---------------------------------------------------------------- Q-B: liquidity walls
print("\n" + "=" * 108)
print("Q-B — LIQUIDITY MAGNET: does a wall AHEAD (something to target) change behaviour?")
print("     walls rebuilt from the fill-1 snapshot, strictly pre-fill")
print("=" * 108)
W = F[F.has_depth & F.wall_ahead_d.notna()].copy()
print(f"  trades with a usable pre-fill book: {len(W)}/{len(F)}")
W["wall_far"] = W.wall_ahead_d / W.risk_pts          # wall distance in R units
med = W.wall_far.median()
print(f"  wall-ahead distance: median {W.wall_ahead_d.median():.1f} pts "
      f"({med:.2f}R)  size median {W.wall_ahead_sz.median():.0f}")
print(f"\n{'group':30s} {'n':>4} {'med MFE':>8} {'gave back':>10} {'SL no 1R':>9} "
      f"{'meanR':>8} {'net':>9}")
qb = {}
for nm, m in (("wall ahead WITHIN 2R", W.wall_far <= 2.0),
              ("wall ahead BEYOND 2R", W.wall_far > 2.0),
              ("wall ahead nearer than 1R", W.wall_far <= 1.0),
              ("big wall (size >= median)", W.wall_ahead_sz >= W.wall_ahead_sz.median()),
              ("small wall (size < median)", W.wall_ahead_sz < W.wall_ahead_sz.median())):
    g = W[m]
    if len(g) < 10:
        print(f"{nm:30s} {len(g):>4}   insufficient")
        qb[nm] = dict(n=len(g), insufficient=True)
        continue
    qb[nm] = dict(n=len(g), med_mfe=float(g.mfe_R.median()),
                  gave_back=float(g.gave_back.mean()), sl_no_1r=float(g.sl_no_1R.mean()),
                  meanR=float(g.R.mean()), net=float(g.pl.sum()))
    print(f"{nm:30s} {len(g):>4} {g.mfe_R.median():>8.2f} {g.gave_back.mean()*100:>9.0f}% "
          f"{g.sl_no_1R.mean()*100:>8.0f}% {g.R.mean():>+8.3f} {g.pl.sum():>+9,.0f}")
print("\n  DOES PRICE STALL AT THE WALL? (MFE vs the wall distance, both in R)")
q = W[(W.wall_far > 0.25) & (W.wall_far < 8)]
print(f"    n={len(q)}  Spearman(wall distance R, MFE R) = "
      f"{q[['wall_far','mfe_R']].corr(method='spearman').iloc[0,1]:+.3f}")
reach = (q.mfe_R >= q.wall_far).mean()
print(f"    trades whose MFE reached AT LEAST the wall: {reach*100:.0f}%  "
      f"(if the wall capped moves, this would be low)")
qb["stall"] = dict(n=len(q), rho=float(q[["wall_far", "mfe_R"]].corr(method="spearman").iloc[0, 1]),
                   reach_rate=float(reach))
print(f"\n  BY SEGMENT — is the early window short of walls (nothing to target)?")
for s in ("early 08:00-08:29", "mid 08:30-08:59", "late 09:00-09:29"):
    g = W[W.seg == s]
    if len(g) < 10:
        print(f"    {s:22s} n={len(g):>3}  insufficient")
        continue
    print(f"    {s:22s} n={len(g):>3}  median wall {g.wall_ahead_d.median():>6.1f}pt "
          f"({(g.wall_ahead_d/g.risk_pts).median():.2f}R)  book thickness "
          f"{g.thick.median():>6.0f}")
    qb.setdefault("by_seg", {})[s] = dict(n=len(g), wall_pts=float(g.wall_ahead_d.median()),
                                          wall_R=float((g.wall_ahead_d / g.risk_pts).median()),
                                          thick=float(g.thick.median()))
REP["qb"] = qb

# ---------------------------------------------------------------- Q-C: chop near the open
print("\n" + "=" * 108)
print("Q-C — CHOP AND SWEEPS NEAR THE OPEN")
print("     eff30 = |net move| / total path travelled over 30 min (1.0 = clean trend, 0 = chop)")
print("=" * 108)
print(f"{'segment':22s} {'n':>4} {'eff30':>7} {'crosses':>8} {'adverse first':>14} "
      f"{'SL no 1R':>9} {'med MFE(30m)':>13}")
qc = {}
for s in ("early 08:00-08:29", "mid 08:30-08:59", "late 09:00-09:29"):
    g = F[F.seg == s]
    qc[s] = dict(n=len(g), eff30=float(g.eff30.median()), crosses=float(g.crosses.median()),
                 adverse_first=float(g.adverse_first.mean()), sl_no_1r=float(g.sl_no_1R.mean()),
                 mfe30=float(g.mfe30.median()))
    print(f"{s:22s} {len(g):>4} {g.eff30.median():>7.3f} {g.crosses.median():>8.1f} "
          f"{g.adverse_first.mean()*100:>13.0f}% {g.sl_no_1R.mean()*100:>8.0f}% "
          f"{g.mfe30.median():>13.2f}")
print(f"\n  by 5-min bucket (eff30 median, chop proxy):")
for k in range(18):
    g = F[F.buck == k]
    if not len(g):
        continue
    flag = " *" if len(g) < 10 else ""
    print(f"    {lab(k)}  n={len(g):>3}  eff30 {g.eff30.median():.3f}  "
          f"adverse-first {g.adverse_first.mean()*100:>3.0f}%  "
          f"SL-no-1R {g.sl_no_1R.mean()*100:>3.0f}%{flag}")
REP["qc"] = qc
json.dump(REP, open(f"{OUT}/micro_report.json", "w"), indent=1, default=float)
print(f"\nwrote {OUT}/micro_frame.csv + micro_report.json")
