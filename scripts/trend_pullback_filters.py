#!/usr/bin/env python3
"""TREND PULLBACK — concept-filter battery. Which of OUR concepts makes it more reliable? NQ M15.

Base = the bare stacked-MA trend-pullback trigger (fixed params from trend_pullback.py: touch=wick,
fade vol<1.0x mean(prior 10), target 3R). We add each of our concepts as an ADDITIONAL GATE and ask,
out-of-sample: does the filtered setup's expectancy/PF/win improve AND clear its counter-baseline,
N>=30, CI excluding it, holding across folds -- and does it beat a REGIME-MATCHED placebo (random
bars in the same trend+filter permission set)? A filter that lifts expectancy but ties the placebo
is only selecting a better regime (useful for WHEN to trade), not validating the trigger.

Concepts tested (all <=-now, a priori, no tuning): weekly_bias align, daily_trend_20_50 align,
momentum_5d align, daily RSI not-extreme, VIX-low regime, HTF-draw-exists (untapped PDH/PMH in
trade dir = a target to run to), sweep-first (pullback grabbed a prior 5h extreme then reclaimed),
morning-only (09:30-11:00), near-VWAP (not extended). BH across all filters; placebo on survivors.
"""
import json
import math
from datetime import time as dtime

import numpy as np
import pandas as pd
import importlib.util

S = "/tmp/claude-0/-home-user-AI-trading-agents/69c9097f-44f3-585b-817f-a315126d0dbb/scratchpad"
NY = "America/New_York"
TRAIN_END = "2024-12-31"
TICK = 0.25
TM, NV, TH, TG = "wick", 10, 1.0, 3.0     # fixed base params
rng = np.random.default_rng(42)

print("=" * 80 + "\nTREND PULLBACK — concept-filter battery (make it more reliable?)\n" + "=" * 80)
spec = importlib.util.spec_from_file_location("bias_lab", f"{S}/bias_lab.py")
bl = importlib.util.module_from_spec(spec); spec.loader.exec_module(bl)
Fd = bl.F
vixp = {d: float(v) for d, v in zip(Fd.index, Fd["vix_p"].values)}
w = json.load(open(f"{S}/_win.json")); SIG = np.load(f"{S}/_win_sig.npy")
sigmap = {w["names"][k]: dict(zip(w["order"], SIG[k])) for k in range(len(w["names"]))}
rsi_map = {d: float(r) for d, r in zip(Fd.index, Fd["rsi"].values)}

bars = pd.read_parquet("/home/user/gs/data/reference/nq_1m_master.parquet")
bars["ts"] = pd.to_datetime(bars["ts_event"], utc=True).dt.tz_convert(NY)
bars = bars.sort_values("ts").reset_index(drop=True)
bars["day"] = bars["ts"].dt.strftime("%Y-%m-%d")
# prior RTH H/L + premarket H/L per day (for HTF-draw + sweep)
rthhl, pmhl = {}, {}
for d, g in bars.groupby("day"):
    r = g[(g.ts.dt.time >= dtime(9, 30)) & (g.ts.dt.time < dtime(16, 0))]
    if len(r) >= 100:
        rthhl[d] = (float(r.high.max()), float(r.low.min()))
    pm = g[g.ts.dt.time < dtime(9, 40)]
    if len(pm):
        pmhl[d] = (float(pm.high.max()), float(pm.low.min()))
dl = sorted(rthhl)
prior_rthhl = {}
for i, d in enumerate([x for x in sorted(set(bars.day))]):
    for j in range(len([x for x in dl if x < d]) - 1, -1, -1):
        pass
# simpler prior-RTH map
allday = sorted(set(bars.day))
prior_rthhl = {}
last = None
for d in allday:
    if last is not None:
        prior_rthhl[d] = rthhl[last]
    if d in rthhl:
        last = d

m = bars.set_index("ts").resample("15min", label="right", closed="right").agg(
    open=("open", "first"), high=("high", "max"), low=("low", "min"),
    close=("close", "last"), volume=("volume", "sum")).dropna(subset=["close"])
m["day"] = m.index.strftime("%Y-%m-%d"); m["t"] = m.index.time
for p in (20, 50, 200):
    m[f"ma{p}"] = m.close.rolling(p).mean()
m["vol_maN"] = m.volume.rolling(NV).mean().shift(1)
m["swing_lo5"] = m.low.rolling(5).min(); m["swing_hi5"] = m.high.rolling(5).max()
m["roll_lo20"] = m.low.rolling(20).min().shift(1); m["roll_hi20"] = m.high.rolling(20).max().shift(1)
# session-cumulative VWAP (<=-now) + developing session hi/lo up to each bar
vw, sess_hi, sess_lo = {}, {}, {}
for d, g in bars.groupby("day", sort=True):
    tp = ((g.high + g.low + g.close) / 3).values; vol = g.volume.values
    ts_int = g.ts.values.astype("int64"); cpv = np.cumsum(tp * vol); cv = np.cumsum(vol)
    chi = np.maximum.accumulate(g.high.values); clo = np.minimum.accumulate(g.low.values)
    ends = m.index[m.day == d]; bi = 0
    for e in ends:
        ev = e.value
        while bi < len(ts_int) and ts_int[bi] <= ev:
            bi += 1
        if bi == 0:
            continue
        vw[e] = cpv[bi - 1] / max(cv[bi - 1], 1e-9); sess_hi[e] = chi[bi - 1]; sess_lo[e] = clo[bi - 1]
m["vwap"] = m.index.map(vw); m["sess_hi"] = m.index.map(sess_hi); m["sess_lo"] = m.index.map(sess_lo)

M = m.reset_index().rename(columns={"index": "ts"})
M = M[M.ma200.notna()].reset_index(drop=True)
a = {c: M[c].values for c in ["open", "high", "low", "close", "ma20", "ma50", "ma200", "vol_maN",
                              "swing_lo5", "swing_hi5", "roll_lo20", "roll_hi20", "vwap", "sess_hi", "sess_lo"]}
day_a = M.day.values; t_a = M.t.values
rth = np.array([dtime(9, 30) <= t <= dtime(15, 0) for t in t_a])

trigs = []
for i in range(1, len(M)):
    if not rth[i] or np.isnan(a["vol_maN"][i]) or a["vol_maN"][i] <= 0:
        continue
    if M.volume.values[i] >= TH * a["vol_maN"][i]:
        continue
    up = a["ma20"][i] > a["ma50"][i] > a["ma200"][i] and a["close"][i] > a["ma50"][i] and a["close"][i] > a["ma200"][i]
    dn = a["ma20"][i] < a["ma50"][i] < a["ma200"][i] and a["close"][i] < a["ma50"][i] and a["close"][i] < a["ma200"][i]
    if up and a["low"][i] <= a["ma50"][i] and a["close"][i] > a["ma50"][i]:
        trigs.append((i, 1))
    elif dn and a["high"][i] >= a["ma50"][i] and a["close"][i] < a["ma50"][i]:
        trigs.append((i, -1))

def resolve(i, dr, invert=False):
    if i + 1 >= len(M) or day_a[i + 1] != day_a[i]:
        return None
    ed = -dr if invert else dr
    entry = a["open"][i + 1] + ed * TICK
    if invert:
        ref = a["swing_hi5"][i] if dr > 0 else a["swing_lo5"][i]; risk = abs(ref - entry)
    else:
        ref = min(a["swing_lo5"][i], a["ma50"][i]) if dr > 0 else max(a["swing_hi5"][i], a["ma50"][i])
        risk = abs(entry - ref) + TICK
    if risk < 5 or risk > 70:
        return None
    stop = entry - ed * risk; tgt = entry + ed * TG * risk; j = i + 1
    while j < len(M) and day_a[j] == day_a[i]:
        if t_a[j] >= dtime(15, 55):
            return ed * (a["close"][j] - entry) / risk
        if (a["low"][j] <= stop) if ed > 0 else (a["high"][j] >= stop):
            return -1.0 - TICK / risk
        if (a["high"][j] >= tgt) if ed > 0 else (a["low"][j] <= tgt):
            return TG - TICK / risk
        j += 1
    return ed * (a["close"][j - 1] - entry) / risk

# base records
rec = []
for i, dr in trigs:
    r = resolve(i, dr)
    if r is None:
        continue
    d = day_a[i]
    prh = prior_rthhl.get(d, (np.nan, np.nan)); pmh = pmhl.get(d, (np.nan, np.nan))
    draw = (max(prh[0], pmh[0]) > a["sess_hi"][i]) if dr > 0 else (min(prh[1], pmh[1]) < a["sess_lo"][i])
    swept = (a["low"][i] < a["roll_lo20"][i]) if dr > 0 else (a["high"][i] > a["roll_hi20"][i])
    def sg(name):
        return sigmap.get(name, {}).get(d, 0)
    rsi = rsi_map.get(d, 50)
    rec.append(dict(i=i, dir=dr, day=d, R=r, train=d <= TRAIN_END,
                    vix=vixp.get(d, np.nan),
                    f_weekly=int(sg("weekly_bias") == dr),
                    f_dtrend=int(sg("daily_trend_20_50") == dr),
                    f_mom5=int(sg("momentum_5d") == dr),
                    f_rsi_ok=int((40 <= rsi <= 70) if dr > 0 else (30 <= rsi <= 60)),
                    f_draw=int(bool(draw)),
                    f_sweep=int(bool(swept)),
                    f_morning=int(dtime(9, 30) <= t_a[i] <= dtime(11, 0)),
                    f_nearvwap=int(abs(a["close"][i] - a["vwap"][i]) <= 0.25 * abs(a["close"][i] - (min(a["swing_lo5"][i], a["ma50"][i]) if dr > 0 else max(a["swing_hi5"][i], a["ma50"][i]))) + 15)))
    rec[-1]["ctrR"] = resolve(i, dr, invert=True)
RC = pd.DataFrame(rec)
q33 = np.nanpercentile(RC[RC.train].vix.dropna(), 33)
RC["f_vixlow"] = (RC.vix < q33).astype(int)
FILTERS = ["f_weekly", "f_dtrend", "f_mom5", "f_rsi_ok", "f_vixlow", "f_draw", "f_sweep", "f_morning", "f_nearvwap"]
te = ~RC.train
print(f"base bare trigger: train n={int(RC.train.sum())} E[R]={RC[RC.train].R.mean():+.3f}  "
      f"test n={int(te.sum())} E[R]={RC[te].R.mean():+.3f}  (VIX-low cut {q33:.1f})")

def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n; dd = 1 + z * z / n; c = (p + z * z / (2 * n)) / dd
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / dd
    return (round(100 * (c - h), 1), round(100 * (c + h), 1))

def boot_ci_p(v, ref=0.0):
    bm = np.array([v[rng.integers(0, len(v), len(v))].mean() for _ in range(2000)])
    return (round(float(np.percentile(bm, 2.5)), 3), round(float(np.percentile(bm, 97.5)), 3)), \
           float(max((bm <= ref).mean(), 1 / 2000))

bounds = ["2025-01-01", "2025-07-01", "2026-01-01", "2026-07-16"]
rows = []
for f in FILTERS:
    sub = RC[(RC[f] == 1) & te]; subtr = RC[(RC[f] == 1) & RC.train]
    n = len(sub)
    if n == 0:
        continue
    v = sub.R.values; ctr = sub.ctrR.dropna().values
    ci, _ = boot_ci_p(v)
    _, p_vs_ctr = boot_ci_p(v - sub.ctrR.fillna(0).values, 0.0)
    pf = (v[v > 0].sum() / -v[v < 0].sum()) if (v < 0).any() else float("inf")
    pos = valid = 0
    for j in range(len(bounds) - 1):
        fm = sub[(sub.day >= bounds[j]) & (sub.day < bounds[j + 1])]
        if len(fm) >= 10:
            valid += 1; pos += int(fm.R.mean() > 0)
    rows.append(dict(filter=f, n_te=n, expR=round(float(v.mean()), 3), ci=ci,
                     win=round(100 * (v > 0).mean(), 1), pf=round(float(pf), 2),
                     ctr=round(float(ctr.mean()), 3) if len(ctr) else None,
                     p_vs_ctr=round(p_vs_ctr, 4), folds=f"{pos}/{valid}",
                     tr_expR=round(float(subtr.R.mean()), 3) if len(subtr) else None,
                     gap=round(float(subtr.R.mean() - v.mean()), 3) if len(subtr) else None))
R = pd.DataFrame(rows).sort_values("expR", ascending=False).reset_index(drop=True)

def bh(ps, q=0.10):
    mm = len(ps); idx = sorted(range(mm), key=lambda i: ps[i]); kmax = -1
    for r_, i in enumerate(idx, 1):
        if ps[i] <= q * r_ / mm:
            kmax = r_
    return [idx.index(i) < kmax if kmax > 0 else False for i in range(mm)]
R["bh"] = bh(R.p_vs_ctr.tolist())
R["clears"] = R.apply(lambda r: r.n_te >= 30 and r.ci[0] > (r.ctr or 0) and r.bh, axis=1)

print("\n--- concept filters on the bare trigger (TEST 2025->now), sorted by E[R] ---")
print(f"  {'filter':12s} {'n':>4s} {'E[R]':>7s} {'95% CI':>16s} {'win':>5s} {'PF':>5s} "
      f"{'ctr':>7s} {'p_ctr':>6s} {'folds':>5s} {'train':>6s} {'gap':>6s}")
for _, r in R.iterrows():
    print(f"  {r['filter']:12s} {r.n_te:4d} {r.expR:+7.3f} [{r.ci[0]:+.2f},{r.ci[1]:+.2f}] {r.win:5.1f} "
          f"{r.pf:5.2f} {str(r.ctr):>7s} {r.p_vs_ctr:6.3f} {r.folds:>5s} "
          f"{str(r.tr_expR):>6s} {str(r.gap):>6s}  {'CLEARS' if r.clears else ''}{' [BH]' if r.bh else ''}"
          f"{' LOW-N' if r.n_te < 30 else ''}")

# combine the two best economically-sensible filters (draw + trend align) as an illustration, honestly labeled
combo = RC[(RC.f_draw == 1) & (RC.f_dtrend == 1) & te]
if len(combo):
    ci, _ = boot_ci_p(combo.R.values)
    print(f"\n  [illustrative combo] draw-exists AND daily-trend-align: n={len(combo)} "
          f"E[R] {combo.R.mean():+.3f} CI{ci} win {100*(combo.R>0).mean():.1f}% "
          f"(train n={len(RC[(RC.f_draw==1)&(RC.f_dtrend==1)&RC.train])})")

survivors = R[R.clears]["filter"].tolist()
# placebo on survivors: random bars in the SAME trend+filter permission set
placebo = {}
perm = {1: [i for i in range(len(M)) if rth[i] and a["ma20"][i] > a["ma50"][i] > a["ma200"][i] and a["close"][i] > a["ma50"][i] and day_a[i] > TRAIN_END],
        -1: [i for i in range(len(M)) if rth[i] and a["ma20"][i] < a["ma50"][i] < a["ma200"][i] and a["close"][i] < a["ma50"][i] and day_a[i] > TRAIN_END]}
for f in survivors:
    sub = RC[(RC[f] == 1) & te]; real = sub.R.mean()
    nL = int((sub.dir == 1).sum()); nS = len(sub) - nL
    sims = []
    for _ in range(200):
        idxs = ([(int(x), 1) for x in rng.choice(perm[1], min(nL, len(perm[1])), replace=False)] +
                [(int(x), -1) for x in rng.choice(perm[-1], min(nS, len(perm[-1])), replace=False)])
        rr = [resolve(i, d) for i, d in idxs]; rr = [x for x in rr if x is not None]
        if rr:
            sims.append(np.mean(rr))
    pp = float((np.array(sims) >= real).mean()) if sims else 1.0
    placebo[f] = round(pp, 3)
    print(f"  placebo[{f}]: real {real:+.3f} vs random-in-regime {np.mean(sims):+.3f}  p={pp:.3f} "
          f"({'trigger adds signal' if pp < 0.05 else 'just regime selection'})")

print("\n" + "=" * 80)
final = [f for f in survivors if placebo.get(f, 1) < 0.05]
print(f"filters that clear counter+BH AND beat regime-placebo: {final or 'NONE'}")
print("=" * 80)
R.assign(ci=R.ci.apply(list)).to_csv(f"{S}/trend_pullback_filters.csv", index=False)
json.dump(dict(base_test_expR=round(float(RC[te].R.mean()), 3), base_test_n=int(te.sum()),
               vix_cut=round(float(q33), 1),
               filters=R.assign(ci=R.ci.apply(list)).to_dict("records"),
               survivors=survivors, placebo=placebo, final=final),
          open(f"{S}/trend_pullback_filters.json", "w"), default=str)
print("saved trend_pullback_filters.csv/json")
