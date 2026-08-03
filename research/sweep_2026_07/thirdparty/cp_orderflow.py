#!/usr/bin/env python3
"""Does order flow refine the Currency-Pros entries? Scored against OF_FILTER_PREREG.md,
which was committed before any filtered outcome was computed. Research only.

Filters, sign-based, no swept thresholds:
  CVD aligned          cvd_15 * direction > 0
  Delta divergence     sign(dPrice 15m) != sign(cvd_15), both non-zero
  Heatmap wall ahead   largest resting level on the target side exists at the fill-1 snapshot
  All three            on the depth-covered subset

Breakeven is 25.0% by construction (payoff fixed at 3.00R). Sidak alpha over 4 tests = 0.0127.
Each filter's COMPLEMENT is reported as the registered falsifier.
"""
import glob
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy import stats

REPO = "/home/user/AI-trading-agents"
os.chdir(REPO)
OUT = f"{REPO}/research/sweep_2026_07/thirdparty"
NY, PAD, BE = "America/New_York", 25.0, 0.25
ALPHA = 1 - 0.95 ** (1 / 4)
rng = np.random.default_rng(20260803)

T = pd.read_csv(f"{OUT}/cp_trades_all.csv")
P = T[(T.hm >= 570) & (T.hm < 960) & (T.fib == 0.75) & (T.score >= 3)
      & (T.day >= "2025-06-01")].copy().reset_index(drop=True)
P["ft"] = pd.to_datetime(P.fill, utc=True)
P["dir"] = np.where(P.side == "long", 1, -1)
print(f"sample: {len(P)} CP trades over {P.day.nunique()} days, {P.day.min()} .. {P.day.max()}")
P["won"] = P.R > 0

bars = pd.read_parquet(f"{REPO}/data/reference/nq_1m_master.parquet",
                       columns=["ts_event", "high", "low", "close"])
bars["ts"] = pd.to_datetime(bars.ts_event, utc=True)
bars = bars.drop_duplicates("ts").set_index("ts").sort_index()

print("load + band-clean tape ...", flush=True)
tp = pd.concat([pq.read_table(f, columns=["ts_minute", "price", "side", "volume"]).to_pandas()
                for f in sorted(glob.glob(f"{REPO}/data/reference/cvd/footprint_*.parquet"))],
               ignore_index=True)
tp["ts_minute"] = pd.to_datetime(tp.ts_minute, utc=True)
tp["volume"] = tp.volume.astype("int64")
band = bars.groupby(bars.index.tz_convert(NY).strftime("%Y-%m-%d")).agg(
    lo=("low", "min"), hi=("high", "max"))
tp["eday"] = tp.ts_minute.dt.tz_convert(NY).dt.strftime("%Y-%m-%d")
tp = tp.join(band, on="eday")
tp = tp[tp.hi.isna() | ((tp.price >= tp.lo - PAD) & (tp.price <= tp.hi + PAD))]
M = tp.assign(sg=tp.volume.values * np.where(tp.side.values == "B", 1, -1)) \
      .groupby("ts_minute", observed=True).agg(vol=("volume", "sum"), delta=("sg", "sum"))
M = M.reindex(pd.date_range(M.index.min(), M.index.max(), freq="min", tz="UTC"), fill_value=0)
d15 = M.delta.rolling(15).sum().shift(1)
dpx = bars.close.diff(15).shift(1)
print(f"minute grid {len(M):,}")


def load_depth(day):
    for f in ("depth_2025", "depth_2026", "depth_apr2026"):
        p = Path(f"data/reference/{f}/nq_depth_{day}_ny.csv")
        if p.exists():
            d = pd.read_csv(p)
            d["ts"] = pd.to_datetime(d.ts, utc=True).dt.tz_convert(NY)
            return d
    return None


print("build filters at fills ...", flush=True)
cache, rows = {}, []
for r in P.itertuples(index=False):
    fm = r.ft.floor("min")
    c15 = float(d15.get(fm, np.nan))
    dp = float(dpx.get(fm, np.nan))
    cvd_al = (c15 * r.dir > 0) if np.isfinite(c15) and c15 != 0 else False
    div = (bool(np.sign(dp) != np.sign(c15)) if np.isfinite(dp) and np.isfinite(c15)
           and dp != 0 and c15 != 0 else False)
    if r.day not in cache:
        cache[r.day] = load_depth(r.day)
    dep = cache[r.day]
    wall, has_dep = False, False
    if dep is not None:
        et = r.ft.tz_convert(NY)
        sub = dep[dep.ts <= et.floor("min") - pd.Timedelta(minutes=1)]
        if len(sub):
            b = sub[sub.ts == sub.ts.max()]
            has_dep = True
            side = "ask" if r.dir > 0 else "bid"   # wall AHEAD = in the target direction
            s = b[b.side == side]
            wall = bool(len(s) and s["size"].max() > 0)
    rows.append(dict(cvd_aligned=cvd_al, divergence=div, wall_ahead=wall, has_depth=has_dep,
                     cvd15=c15))
F = pd.DataFrame(rows)
for c in F.columns:
    P[c] = F[c].values
P.to_csv(f"{OUT}/cp_of_trades.csv", index=False)
print(f"  cvd computable {int(np.isfinite(P.cvd15).sum())}/{len(P)} | "
      f"depth available {int(P.has_depth.sum())}/{len(P)}")

days = P.day.values
u_days = pd.unique(days)


def dayboot(mask, nb=4000):
    sub = P[mask]
    if not len(sub):
        return np.nan, np.nan
    idx = {d: sub.index[sub.day == d].to_numpy() for d in sub.day.unique()}
    dd = list(idx)
    out = []
    for _ in range(nb):
        pick = rng.choice(dd, size=len(dd), replace=True)
        ix = np.concatenate([idx[d] for d in pick])
        out.append(P.won.values[ix].mean())
    o = np.array(out)
    return float(np.percentile(o, 2.5)), float(np.percentile(o, 97.5))


def perm_p(mask, nperm=2000):
    """Day-block permutation: shuffle outcomes in whole-day blocks, filter fixed."""
    obs = P.won.values[mask.values].mean()
    blocks = [np.flatnonzero(days == d) for d in u_days]
    flat = np.concatenate(blocks)
    w = P.won.values
    hits = 0
    m = mask.values
    for _ in range(nperm):
        order = rng.permutation(len(blocks))
        perm = np.concatenate([blocks[k] for k in order])
        w2 = np.empty_like(w)
        w2[flat] = w[perm]
        if w2[m].mean() >= obs - 1e-12:
            hits += 1
    return (hits + 1) / (nperm + 1)


print("\n" + "=" * 108)
print("DOES ORDER FLOW REFINE THE ENTRIES?  breakeven = 25.0%, Sidak alpha = "
      f"{ALPHA:.4f} over 4 tests")
print("=" * 108)
TESTS = [("CVD aligned", P.cvd_aligned, P.index.isin(P.index)),
         ("Delta divergence", P.divergence, P.index.isin(P.index)),
         ("Heatmap wall ahead", P.wall_ahead & P.has_depth, P.has_depth),
         ("All three combined", P.cvd_aligned & P.divergence & P.wall_ahead & P.has_depth,
          P.has_depth)]
print(f"{'filter':22s} {'kept n':>7} {'WR':>7} {'95% CI':>18} {'mean R':>8} {'binom p':>9} "
      f"{'perm p':>8} | {'complement n':>12} {'compl WR':>9}")
res = {}
for name, mask, univ in TESTS:
    keep = P[mask]
    comp = P[univ & ~mask]
    if len(keep) < 30:
        print(f"{name:22s} {len(keep):>7}   INSUFFICIENT (floor 30)")
        res[name] = dict(n=len(keep), insufficient=True)
        continue
    wr = keep.won.mean()
    bp = stats.binomtest(int(keep.won.sum()), len(keep), BE, alternative="greater").pvalue
    lo, hi = dayboot(mask)
    pp = perm_p(mask)
    cwr = comp.won.mean() if len(comp) else np.nan
    res[name] = dict(n=len(keep), wr=float(wr), ci=[lo, hi], meanR=float(keep.R.mean()),
                     binom_p=float(bp), perm_p=float(pp), n_comp=len(comp),
                     comp_wr=float(cwr) if len(comp) else None,
                     beats=bool(bp < ALPHA and lo > BE and (cwr < wr if len(comp) else False)))
    print(f"{name:22s} {len(keep):>7} {wr*100:>6.1f}% [{lo*100:>5.1f}%,{hi*100:>5.1f}%] "
          f"{keep.R.mean():>+8.3f} {bp:>9.4f} {pp:>8.4f} | {len(comp):>12} {cwr*100:>8.1f}%")

base = P.won.mean()
print(f"\n  unfiltered baseline: n={len(P)}  WR {base*100:.1f}%  mean R {P.R.mean():+.3f}")
print(f"  registered rule: beat 25.0% at p<{ALPHA:.4f}, CI excluding 25.0%, AND complement worse")
win = [k for k, v in res.items() if v.get("beats")]
print(f"  FILTERS THAT PASS: {win if win else 'NONE'}")
res["_baseline"] = dict(n=len(P), wr=float(base), meanR=float(P.R.mean()))
res["_alpha"] = ALPHA
res["_passing"] = win
json.dump(res, open(f"{OUT}/cp_of_results.json", "w"), indent=1, default=float)
print(f"\nwrote {OUT}/cp_of_results.json")
