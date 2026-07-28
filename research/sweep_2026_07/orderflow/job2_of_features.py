#!/usr/bin/env python3
"""JOB 2 final step: rebuild the order-flow feature file against the re-derived books.
v2 methodology exactly (Amendment 1): SOURCE-band-cleaned tape (ET-day bar band +/-25pt,
dropped before ANY aggregation), strict pre-fill windows (30/15/5 completed minutes before
the floored fill minute), binary stacks (3:1 x >=3 frozen constant), delta_div_15 carries
LOW-POWER wherever used. stamp_edge policy: every union fill is limit-containment-tested
against its stamped minute's bar (+/-1 tick); failures are flagged stamp_edge=1 (primary
scoring, when it is ever unblocked, excludes them). NO outcome columns are written.
"""
import glob
import json
import os

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = "/home/user/AI-trading-agents"
OUT = os.path.join(REPO, "research/sweep_2026_07/orderflow")
W_LONG, W_MID, W_SHORT = 30, 15, 5
STACK_RATIO, STACK_MIN = 3.0, 3
PAD = 25.0
VARIANTS = ("L_nonews", "L_news", "C_nonews", "C_news")

frames = {}
for v in VARIANTS:
    d = pd.read_parquet(f"{OUT}/job2_books/mech_{v}.parquet")
    d = d[(d["size"] > 0) & (d.win_ == "pre") & (d.fillhm >= 480) & (d.fillhm < 570)]
    f = pd.DataFrame(dict(day=d.day.astype(str),
                          ft=pd.to_datetime(d.fill.astype(str).str.replace("T", " "), utc=True),
                          direction=d.direction.astype(str), entry=d.entry.astype(float)))
    frames[v] = f.reset_index(drop=True)
U = pd.concat(frames.values()).drop_duplicates(["day", "ft", "direction"]).reset_index(drop=True)
print("PM trades per variant:", {v: len(f) for v, f in frames.items()},
      "| union unique:", len(U))

bars = pd.read_parquet(f"{REPO}/data/reference/nq_1m_master.parquet",
                       columns=["ts_event", "high", "low", "close"])
bars["ts"] = pd.to_datetime(bars.ts_event).dt.tz_convert("UTC")
bars = bars.drop_duplicates("ts").set_index("ts").sort_index()
H, L, BI = bars.high, bars.low, bars.index

def contains(minute, px, tol=0.25):
    k = BI.searchsorted(minute)
    if k >= len(BI) or BI[k] != minute:
        return None
    return bool(L.iloc[k] - tol <= px <= H.iloc[k] + tol)

edge = []
for r in U.itertuples(index=False):
    if contains(r.ft.floor("min"), r.entry) is False:
        edge.append((r.day, str(r.ft)))
U["stamp_edge"] = [int((r.day, str(r.ft)) in set(edge)) for r in U.itertuples(index=False)]
print(f"stamp_edge (containment fails at +/-1 tick) in union: {len(edge)}")
for e in edge:
    print(f"   {e[0]}  {e[1]}")

print("load + band-clean tape ...", flush=True)
T = pd.concat([pq.read_table(f, columns=["ts_minute", "price", "side", "volume"]).to_pandas()
               for f in sorted(glob.glob(f"{REPO}/data/reference/cvd/footprint_*.parquet"))],
              ignore_index=True)
T["ts_minute"] = pd.to_datetime(T.ts_minute, utc=True)
T["volume"] = T.volume.astype("int64")
band = bars.groupby(bars.index.tz_convert("America/New_York").strftime("%Y-%m-%d")) \
           .agg(lo=("low", "min"), hi=("high", "max"))
T["eday"] = T.ts_minute.dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
T = T.join(band, on="eday")
T = T[T.hi.isna() | ((T.price >= T.lo - PAD) & (T.price <= T.hi + PAD))]
M = T.assign(signed=T.volume.values * np.where(T.side.values == "B", 1, -1)) \
     .groupby("ts_minute", observed=True).agg(vol=("volume", "sum"), delta=("signed", "sum"))
fm1 = pd.DatetimeIndex(sorted(set(U.ft.dt.floor("min") - pd.Timedelta(minutes=1))))
G = {k: g for k, g in T[T.ts_minute.isin(fm1)].groupby("ts_minute")}

def stack_from(d):
    if d is None or not len(d):
        return np.nan, np.nan
    p = d.pivot_table(index="price", columns="side", values="volume", aggfunc="sum") \
         .fillna(0).sort_index()
    if p.empty or "B" not in p or "A" not in p:
        return 0, 0
    def run(mask):
        best = cur = 0
        for v in mask:
            cur = cur + 1 if v else 0
            best = max(best, cur)
        return best
    sb = run((p["B"].values >= STACK_RATIO * p["A"].values) & (p["B"].values > 0))
    sa = run((p["A"].values >= STACK_RATIO * p["B"].values) & (p["A"].values > 0))
    return (sb if sb >= STACK_MIN else 0), (sa if sa >= STACK_MIN else 0)

print("build features on union ...", flush=True)
pc = bars.close
rows = []
for r in U.itertuples(index=False):
    fm = r.ft.floor("min")
    def window(n):
        return M.loc[fm - pd.Timedelta(minutes=n): fm - pd.Timedelta(minutes=1)]
    w30, w15, w5 = window(W_LONG), window(W_MID), window(W_SHORT)
    k1 = pc.index.searchsorted(fm - pd.Timedelta(minutes=1), side="right") - 1
    k16 = pc.index.searchsorted(fm - pd.Timedelta(minutes=16), side="right") - 1
    dpx = float(pc.iloc[k1] - pc.iloc[k16]) if k1 > k16 >= 0 else np.nan
    brange = float(bars.high.iloc[max(k16, 0):k1 + 1].max()
                   - bars.low.iloc[max(k16, 0):k1 + 1].min()) if k1 > k16 >= 0 else np.nan
    cvd15 = float(w15.delta.sum()) if len(w15) else np.nan
    sb, sa = stack_from(G.get(fm - pd.Timedelta(minutes=1)))
    rows.append(dict(
        day=r.day, ft=str(r.ft), direction=r.direction, stamp_edge=int(r.stamp_edge),
        cvd_5=float(w5.delta.sum()) if len(w5) else np.nan,
        cvd_15=cvd15,
        cvd_30=float(w30.delta.sum()) if len(w30) else np.nan,
        cvd_norm_15=float(w15.delta.sum() / w15.vol.sum()) if len(w15) and w15.vol.sum() else np.nan,
        delta_div_15=(float(np.sign(dpx) != np.sign(cvd15))
                      if np.isfinite(dpx) and np.isfinite(cvd15) and dpx != 0 and cvd15 != 0 else np.nan),
        fp_imb_15=(float((w15.delta.sum() / w15.vol.sum() + 1) / 2 - 0.5)
                   if len(w15) and w15.vol.sum() else np.nan),
        absorp_15=(float(w15.vol.sum() / brange) if np.isfinite(brange) and brange > 0
                   and len(w15) else np.nan),
        stack_bid_bin=int(sb > 0) if np.isfinite(sb) else np.nan,
        stack_ask_bin=int(sa > 0) if np.isfinite(sa) else np.nan,
        vol_15=float(w15.vol.sum()) if len(w15) else np.nan,
        vol_30=float(w30.vol.sum()) if len(w30) else np.nan,
        abs_cvd_15=abs(cvd15) if np.isfinite(cvd15) else np.nan,
    ))
X = pd.DataFrame(rows)

# coverage: every union trade must have full 30-minute pre-fill tape
cover = X.vol_30.notna() & X.cvd_30.notna()
print(f"coverage: {int(cover.sum())}/{len(X)} union trades with full pre-fill windows")

for v, f in frames.items():
    kf = f[["day", "direction"]].assign(ft=f.ft.astype(str))
    xv = kf.merge(X, on=["day", "ft", "direction"], how="left")
    assert len(xv) == len(f) and xv.cvd_15.notna().all()
    xv.to_csv(f"{OUT}/of_features_job2_{v}.csv", index=False)
    print(f"wrote of_features_job2_{v}.csv  ({len(xv)} rows, "
          f"stamp_edge {int(xv.stamp_edge.sum())})")

json.dump(dict(union=len(U), per_variant={v: len(f) for v, f in frames.items()},
               stamp_edge=edge),
          open(f"{OUT}/job2_features_report.json", "w"), indent=1, default=str)
print("STOPPED. Features written; nothing scored, no outcomes joined.")
