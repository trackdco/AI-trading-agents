#!/usr/bin/env python3
"""CONFLUENCE STUDY — step 1: build the NEW single-bar entry-candle features.

Brake, 2026-07-29: "everything built so far uses 5-minute windows or longer, so the entry
candle itself has never been tested." These four are built on the bar at FILL-1 — the last
COMPLETED bar before the fill minute, so strictly pre-fill.

  ec_delta        signed delta (buy - sell aggressor volume) of the fill-1 bar
  ec_fp_imb       FOOTPRINT IMBALANCE ACROSS PRICE LEVELS inside that bar:
                  (#levels where bid >= 3x ask  -  #levels where ask >= 3x bid) / #levels.
                  Deliberately a LEVEL-COUNT measure, not (B-A)/(B+A), which would merely
                  duplicate ec_delta normalised.
  ec_delta_hi_lo  (delta at the bar's highest traded price - delta at its lowest) / bar volume
  ec_aggr_flip    aggressor flip inside the bar: sign(delta in the lower half of the bar's
                  price range) != sign(delta in the upper half). Binary.

Each is shift-tested against the same contaminated twins as the rest of the study (+1 twin =
the FILL bar itself; +15 twin = fill+14) and exchangeability-tested across the re-fixed
2025-12-23 split by day-block permutation. ANY THAT FAIL EXCHANGEABILITY ARE EXCLUDED — not
remedied mid-run, per the brief.

BASELINE: partially remediated (C only) + news filter. W and dep_* remain LEAKY.
"""
import glob
import json
import os

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = "/home/user/AI-trading-agents"
os.chdir(REPO)
SRC = f"{REPO}/research/sweep_2026_07/orderflow"
OUT = f"{REPO}/research/sweep_2026_07/confluence"
os.makedirs(f"{OUT}/raw", exist_ok=True)
PAD, NPERM = 25.0, 2000
rng = np.random.default_rng(20260729)

F = pd.read_csv(f"{SRC}/part0_frame.csv")
F["ft"] = pd.to_datetime(F.ft, utc=True)
print(f"{len(F)} trades | IS {int((~F.oos).sum())} OOS {int(F.oos.sum())}")

bars = pd.read_parquet(f"{REPO}/data/reference/nq_1m_master.parquet",
                       columns=["ts_event", "high", "low"])
bars["ts"] = pd.to_datetime(bars.ts_event, utc=True)
bars = bars.drop_duplicates("ts").set_index("ts").sort_index()

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

# the only minutes we ever need: fill-1, fill (the +1 twin), fill+14 (the +15 twin)
need = set()
for r in F.itertuples(index=False):
    fm = r.ft.floor("min")
    for off in (-1, 0, 14):
        need.add(fm + pd.Timedelta(minutes=off))
piv = T[T.ts_minute.isin(need)].groupby(["ts_minute", "price", "side"], observed=True) \
       .volume.sum().unstack("side", fill_value=0)
for c in ("A", "B"):
    if c not in piv:
        piv[c] = 0
piv = piv.sort_index()
print(f"minutes materialised: {piv.index.get_level_values(0).nunique():,}")

CACHE = {}
for m, g in piv.groupby(level=0):
    px = g.index.get_level_values(1).to_numpy(float)
    b = g["B"].to_numpy(float)
    a = g["A"].to_numpy(float)
    o = np.argsort(px)
    CACHE[m] = (px[o], b[o], a[o])

def candle(m):
    """The four entry-candle features on minute `m`. Direction-free by construction."""
    if m not in CACHE:
        return dict(ec_delta=np.nan, ec_fp_imb=np.nan, ec_delta_hi_lo=np.nan,
                    ec_aggr_flip=np.nan)
    px, b, a = CACHE[m]
    vol = float((b + a).sum())
    d = b - a
    n = len(px)
    if n == 0 or vol <= 0:
        return dict(ec_delta=np.nan, ec_fp_imb=np.nan, ec_delta_hi_lo=np.nan,
                    ec_aggr_flip=np.nan)
    buy_imb = int(((b >= 3.0 * a) & (b > 0)).sum())
    sell_imb = int(((a >= 3.0 * b) & (a > 0)).sum())
    fp_imb = (buy_imb - sell_imb) / n
    hi_lo = (d[-1] - d[0]) / vol if n >= 2 else np.nan
    if n >= 2:
        mid = (px[0] + px[-1]) / 2.0
        low_half, up_half = d[px <= mid].sum(), d[px > mid].sum()
        flip = float(np.sign(low_half) != np.sign(up_half)
                     if low_half != 0 and up_half != 0 else 0.0)
    else:
        flip = np.nan
    return dict(ec_delta=float(d.sum()), ec_fp_imb=float(fp_imb),
                ec_delta_hi_lo=float(hi_lo), ec_aggr_flip=flip)

NEW = ["ec_delta", "ec_fp_imb", "ec_delta_hi_lo", "ec_aggr_flip"]
rows = {}
for off, tag in ((-1, "strict"), (0, "shift1"), (14, "leak15")):
    out = []
    for r in F.itertuples(index=False):
        out.append(candle(r.ft.floor("min") + pd.Timedelta(minutes=off)))
    rows[tag] = pd.DataFrame(out)

X = rows["strict"].copy()
X.insert(0, "ft", F.ft.astype(str).values)
X.insert(0, "day", F.day.values)
X["oos"] = F.oos.values

print("\n" + "=" * 92)
print("SHIFT TEST — strict (fill-1) vs +1 twin (the FILL bar) vs +15 leaky control")
print("=" * 92)
print(f"{'feature':16s} {'n':>4} {'+1 differs':>11} {'+15 differs':>12}  verdict")
shift_rep = {}
for c in NEW:
    a_, b1, b15 = X[c], rows["shift1"][c], rows["leak15"][c]
    d1 = int(((a_ != b1) & a_.notna() & b1.notna()).sum())
    d15 = int(((a_ != b15) & a_.notna() & b15.notna()).sum())
    ok = d1 > 0 and d15 > 0
    shift_rep[c] = dict(n=int(a_.notna().sum()), shift1=d1, leak15=d15, passes=ok)
    print(f"{c:16s} {int(a_.notna().sum()):>4} {d1:>11} {d15:>12}  "
          f"{'PASS' if ok else 'DEGENERATE'}")

print("\n" + "=" * 92)
print("EXCHANGEABILITY — day-block permutation KS across the re-fixed 2025-12-23 split")
print("=" * 92)
days = X.day.values
u_days = pd.unique(days)
is_m, oos_m = (~X.oos).values, X.oos.values
k_is = len(pd.unique(days[is_m]))

def ks(a, b):
    a, b = np.sort(a[~np.isnan(a)]), np.sort(b[~np.isnan(b)])
    if len(a) < 3 or len(b) < 3:
        return np.nan
    v = np.concatenate([a, b])
    return float(np.abs(np.searchsorted(a, v, "right") / len(a)
                        - np.searchsorted(b, v, "right") / len(b)).max())

exch = {}
print(f"{'feature':16s} {'KS':>7} {'p_perm':>9}  verdict")
for c in NEW:
    x = X[c].values.astype(float)
    obs = ks(x[is_m], x[oos_m])
    hits = 0
    for _ in range(NPERM):
        pick = set(rng.choice(u_days, size=k_is, replace=False))
        m_ = np.array([d in pick for d in days])
        s = ks(x[m_], x[~m_])
        if np.isfinite(s) and np.isfinite(obs) and s >= obs - 1e-12:
            hits += 1
    p = (hits + 1) / (NPERM + 1) if np.isfinite(obs) else np.nan
    ok = bool(np.isfinite(p) and p >= 0.05)
    exch[c] = dict(ks=obs, p=p, passes=ok)
    print(f"{c:16s} {obs:>7.3f} {p:>9.4f}  {'PASS' if ok else 'FAIL -> EXCLUDED'}")

admitted = [c for c in NEW if shift_rep[c]["passes"] and exch[c]["passes"]]
excluded = [c for c in NEW if c not in admitted]
print(f"\nADMITTED to the pool: {admitted}")
print(f"EXCLUDED (not remedied, per the brief): {excluded}")

X.to_csv(f"{OUT}/entry_candle_features.csv", index=False)
json.dump(dict(shift=shift_rep, exchangeability=exch, admitted=admitted, excluded=excluded),
          open(f"{OUT}/entry_candle_report.json", "w"), indent=1, default=float)
print(f"\nwrote {OUT}/entry_candle_features.csv + entry_candle_report.json")
