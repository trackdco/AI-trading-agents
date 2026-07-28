#!/usr/bin/env python3
"""Tasks 3 & 4 (Brake, 2026-07-28): rebuild ALL features from a SOURCE-band-cleaned tape,
stacks demoted to binary (no calibrated edges), stamp-edge trade flagged, shift tests rerun,
stack_ask +1/+15 asymmetry investigated. NO outcomes examined.

WHY A FULL REBUILD (task 3). The IS half (pre 2025-12-11) is the contaminated half of the tape.
Band-cleaning only inside stacked() left DELTA/VOLUME aggregates (cvd_*, vol_*, absorp_15
numerator) carrying off-band rows in 2025 (up to ~3.2%/2.1% of q3/q4 volume, concentrated on 7
contract-mixture days). Tercile edges calibrated on that half would be calibrated on
differently-built data. Fix at source: every tape row outside its ET-day bar band
[low-25, high+25] is dropped BEFORE any aggregation, both halves treated identically.

STACKS (task 3 decision, amended in 02_of_prereg.md): stack_bid / stack_ask are scored BINARY
(a >=3-level 3:1 stack exists: value > 0) — the threshold is the textbook constant already
frozen, so no tercile edge is ever calibrated for them, on any half.

STAMP EDGE (task 2 follow-through): 2026-03-13 08:31 ET is the one trade whose stamp behaves
next-minute (fill = the 08:30->08:31 boundary print; stamped bar never traded the limit price).
Its strict window's last minute contains its own fill print. Flagged stamp_edge=1; the
pre-registration's primary scoring EXCLUDES it (score also run with it, reported second).
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
BAND_PAD = 25.0
STAMP_EDGE = {("2026-03-13", "2026-03-13 12:31:00+00:00")}

print("load tape ...", flush=True)
T = pd.concat([pq.read_table(f, columns=["ts_minute", "price", "side", "volume"]).to_pandas()
               for f in sorted(glob.glob(f"{REPO}/data/reference/cvd/footprint_*.parquet"))],
              ignore_index=True)
T["ts_minute"] = pd.to_datetime(T.ts_minute, utc=True)
T["volume"] = T.volume.astype("int64")
n0, v0 = len(T), int(T.volume.sum())

bars = pd.read_parquet(f"{REPO}/data/reference/nq_1m_master.parquet",
                       columns=["ts_event", "high", "low", "close"])
bars["ts"] = pd.to_datetime(bars.ts_event).dt.tz_convert("UTC")
bars = bars.drop_duplicates("ts").set_index("ts").sort_index()
band = bars.groupby(bars.index.tz_convert("America/New_York").strftime("%Y-%m-%d")) \
           .agg(lo=("low", "min"), hi=("high", "max"))

print("band-clean at source ...", flush=True)
T["eday"] = T.ts_minute.dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
T = T.join(band, on="eday")
keep = T.hi.isna() | ((T.price >= T.lo - BAND_PAD) & (T.price <= T.hi + BAND_PAD))
dropped = T[~keep]
by_half = dropped.assign(h=np.where(dropped.eday < "2025-12-11", "IS(2025h)", "OOS(2026h)")) \
                 .groupby("h").agg(rows=("volume", "size"), vol=("volume", "sum"))
T = T[keep].drop(columns=["lo", "hi"])
print(f"  dropped {n0-len(T):,} rows / {v0-int(T.volume.sum()):,} contracts "
      f"({(v0-int(T.volume.sum()))/v0*100:.3f}% of volume)")
print(by_half.to_string())

print("aggregate per minute (cleaned) ...", flush=True)
sgn = np.where(T.side.values == "B", 1, -1)
M = T.assign(signed=T.volume.values * sgn).groupby("ts_minute", observed=True) \
     .agg(vol=("volume", "sum"), delta=("signed", "sum"))

F = pd.read_csv(f"{REPO}/research/sweep_2026_07/phase2/phase2_frame.csv",
                usecols=["day", "ft", "direction"])
F["ft"] = pd.to_datetime(F.ft, utc=True)

def window(fm, n):
    return M.loc[fm - pd.Timedelta(minutes=n): fm - pd.Timedelta(minutes=1)]

def stack_minute(m):
    d = T[T.ts_minute == m]
    if not len(d):
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

def build(shift_min=0):
    rows = []
    for r in F.itertuples(index=False):
        fm = r.ft.floor("min") + pd.Timedelta(minutes=shift_min)
        w30, w15, w5 = window(fm, W_LONG), window(fm, W_MID), window(fm, W_SHORT)
        pc = bars.close
        k1 = pc.index.searchsorted(fm - pd.Timedelta(minutes=1), side="right") - 1
        k16 = pc.index.searchsorted(fm - pd.Timedelta(minutes=16), side="right") - 1
        dpx = float(pc.iloc[k1] - pc.iloc[k16]) if k1 > k16 >= 0 else np.nan
        brange = float(bars.high.iloc[max(k16, 0):k1 + 1].max()
                       - bars.low.iloc[max(k16, 0):k1 + 1].min()) if k1 > k16 >= 0 else np.nan
        cvd15 = float(w15.delta.sum()) if len(w15) else np.nan
        sb, sa = stack_minute(fm - pd.Timedelta(minutes=1))
        rows.append(dict(
            day=r.day, ft=str(r.ft),
            stamp_edge=int((r.day, str(r.ft)) in STAMP_EDGE),
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
    return pd.DataFrame(rows)

print("build strict / +1 / +15 ...", flush=True)
X0, X1, X15 = build(0), build(1), build(15)

FEATS = [c for c in X0.columns if c not in ("day", "ft", "stamp_edge")]
LOW_POWER = {"delta_div_15"}          # task 4a: flagged wherever it appears
report = {}
print(f"\n{'column':16s} {'n':>4} {'+1 differs':>11} {'+15 differs':>12}  verdict")
for c in FEATS:
    a, b1, b15 = X0[c], X1[c], X15[c]
    d1 = int(((a != b1) & a.notna() & b1.notna()).sum())
    d15 = int(((a != b15) & a.notna() & b15.notna()).sum())
    v = "PASS" + (" (LOW-POWER)" if c in LOW_POWER else "") if d1 > 0 and d15 > 0 else "DEGENERATE"
    report[c] = dict(n=int(a.notna().sum()), shift1=d1, leaky15=d15, verdict=v,
                     low_power=c in LOW_POWER)
    print(f"{c:16s} {a.notna().sum():>4} {d1:>11} {d15:>12}  {v}")

# ---------------------------------------------------------------- task 4b: stack asymmetry
print("\nTASK 4b — stack_ask differed LESS under +15 than +1 in v1. Mechanics on clean build:")
minutes = {k: [] for k in ("fm_1", "fm", "fm_14")}
for r in F.itertuples(index=False):
    fm = r.ft.floor("min")
    for k, m in (("fm_1", fm - pd.Timedelta(minutes=1)), ("fm", fm),
                 ("fm_14", fm + pd.Timedelta(minutes=14))):
        sb, sa = stack_minute(m)
        minutes[k].append((sb, sa))
for side_i, side_n in ((0, "stack_bid"), (1, "stack_ask")):
    nz = {k: np.mean([1 if v[side_i] > 0 else 0 for v in minutes[k]]) for k in minutes}
    d1 = np.mean([minutes["fm"][i][side_i] != minutes["fm_1"][i][side_i] for i in range(216)])
    d15 = np.mean([minutes["fm_14"][i][side_i] != minutes["fm_1"][i][side_i] for i in range(216)])
    se = np.sqrt(0.8 * 0.2 / 216)
    print(f"  {side_n}: stack-present rate  fill-1 {nz['fm_1']*100:.1f}%  FILL {nz['fm']*100:.1f}%  "
          f"fill+14 {nz['fm_14']*100:.1f}%   differ(+1) {d1*100:.1f}%  differ(+15) {d15*100:.1f}%  "
          f"(binomial se ~{se*100:.1f}pp)")
    report[f"{side_n}_asym"] = dict(rate_fm_1=nz["fm_1"], rate_fm=nz["fm"], rate_fm14=nz["fm_14"],
                                    differ1=d1, differ15=d15)
print("  structural read: if the FILL minute's stack-present rate is elevated vs both fill-1 and")
print("  fill+14, the fill minute is the trigger bar (unusually active) and the +1 twin differs")
print("  MORE than +15 for structural reasons, not leakage. If rates are flat, it was noise.")

X0.to_csv(f"{OUT}/of_features_premarket_v2.csv", index=False)
json.dump(report, open(f"{OUT}/step5b_shift_report.json", "w"), indent=1, default=float)
print(f"\nwrote {OUT}/of_features_premarket_v2.csv (v2 SUPERSEDES v1) + step5b_shift_report.json")
print("STOPPED. No outcomes examined.")
