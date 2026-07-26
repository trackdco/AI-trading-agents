#!/usr/bin/env python3
"""BIAS PERCENTAGE LADDER — no trading, pure accuracy. NQ 2023 -> Jul 2026.

How often is the ROLLING bias right, and how high does the % go if it only speaks when
confident? Bias score s(t) = drift(px vs prior RTH close) + vwap side + sweep overlay
+ 0.5*daily walk-forward ensemble (all <=-now, same construction as the DOL run).

LOCKS x TARGETS (graded on net move beyond a deadband; side-accuracy also shown):
  08:00 -> 08:00-10:15 window   (deadband 15pt)     [reference: matches earlier test]
  09:30 -> 09:30-16:00 session  (deadband 0.10%)
  09:40 -> next 60 minutes      (deadband 10pt)
  09:40 -> 09:40-16:00 rest-of-day (deadband 0.10%)

CONVICTION TIERS (the ladder): any call |s|>=0.5; strong |s|>=1.5; max |s|>=2.5; and
UNANIMOUS = drift, vwap, sweep-or-ens all agreeing. Coverage shrinks as conviction rises —
the question is whether accuracy honestly rises with it, out-of-sample (test 2025-26).
Wilson CIs; base rate beside every number; BH across the battery's test cells.
"""
import json
import math
import importlib.util
from datetime import time as dtime

import numpy as np
import pandas as pd

import os as _os
S=_os.environ.get("LONDON_SCRATCH", _os.path.expanduser("~/london_out"))
WT=_os.environ.get("LONDON_WT", f"{S}/canon_wt")
_os.makedirs(S, exist_ok=True)
TRAIN_END = "2024-12-31"

spec = importlib.util.spec_from_file_location("bias_lab", f"{S}/bias_lab.py")
bl = importlib.util.module_from_spec(spec); spec.loader.exec_module(bl)
F, by_day = bl.F, bl.by_day
win = json.load(open(f"{S}/_win.json"))
ens_bias = {d: int(b) for d, b in zip(win["order"], win["ens"])}

rth = {}
for d in by_day:
    g = by_day[d]; r = g[(g.t >= dtime(9, 30)) & (g.t < dtime(16, 0))]
    if len(r) >= 100:
        rth[d] = float(r.close.iloc[-1])
daylist = sorted(by_day); prior_close = {}
for i, d in enumerate(daylist):
    for j in range(i - 1, -1, -1):
        if daylist[j] in rth:
            prior_close[d] = rth[daylist[j]]; break

prior_hl = {}
for i, d in enumerate(daylist):
    for j in range(i - 1, -1, -1):
        if daylist[j] in rth:
            g = by_day[daylist[j]]; r = g[(g.t >= dtime(9, 30)) & (g.t < dtime(16, 0))]
            prior_hl[d] = (float(r.high.max()), float(r.low.min())); break

def idx_at(t, hh, mm):
    w = np.where(t == dtime(hh, mm))[0]
    return int(w[0]) if len(w) else None

rows = []
for d in F.index:
    if pd.Timestamp(d).dayofweek >= 5 or d not in prior_close:
        continue
    g = by_day[d]; t = g.t.values
    o = g.open.values.astype(float); h = g.high.values.astype(float)
    l = g.low.values.astype(float); c = g.close.values.astype(float)
    tp = (g.high + g.low + g.close) / 3.0
    vw = ((tp * g.volume).cumsum() / g.volume.cumsum().replace(0, np.nan)).values
    PDH, PDL = prior_hl[d]; PDC = prior_close[d]
    idx = {k: idx_at(t, *k) for k in [(8, 0), (9, 30), (9, 40), (10, 15), (10, 40), (16, 0)]}
    if any(idx[k] is None for k in [(8, 0), (9, 30), (9, 40), (10, 15)]):
        continue
    i16 = idx[(16, 0)] if idx[(16, 0)] is not None else len(c) - 1
    ens = ens_bias.get(d, 0)
    def score(i):
        px = c[i]
        drift = np.sign(px - PDC)
        disp = np.sign(px - vw[i]) if not math.isnan(vw[i]) else 0
        sw = 0
        if (h[:i + 1] >= PDH).any() and px < PDH:
            sw = -1
        if (l[:i + 1] <= PDL).any() and px > PDL:
            sw = 1
        return drift + disp + sw + 0.5 * ens, (drift, disp, sw)
    s800, c800 = score(idx[(8, 0)])
    s930, c930 = score(idx[(9, 30)])
    s940, c940 = score(idx[(9, 40)])
    i940, i1015, i1040 = idx[(9, 40)], idx[(10, 15)], idx[(10, 40)]
    rows.append(dict(
        day=d, is_train=d <= TRAIN_END,
        s800=s800, s930=s930, s940=s940,
        u800=int(abs(c800[0] + c800[1] + c800[2]) == 3 or (c800[2] == 0 and abs(c800[0] + c800[1]) == 2 and np.sign(c800[0]) == np.sign(ens) and ens != 0)),
        u930=int(abs(c930[0] + c930[1] + c930[2]) == 3 or (c930[2] == 0 and abs(c930[0] + c930[1]) == 2 and np.sign(c930[0]) == np.sign(ens) and ens != 0)),
        u940=int(abs(c940[0] + c940[1] + c940[2]) == 3 or (c940[2] == 0 and abs(c940[0] + c940[1]) == 2 and np.sign(c940[0]) == np.sign(ens) and ens != 0)),
        m_win=c[i1015] - c[idx[(8, 0)]],
        m_sess=c[i16] - c[idx[(9, 30)]],
        m_60=(c[i1040] - c[i940]) if i1040 is not None else np.nan,
        m_rod=c[i16] - c[i940],
        px930=c[idx[(9, 30)]],
    ))
DF = pd.DataFrame(rows)
print("=" * 80 + "\nBIAS PERCENTAGE LADDER (no trading — pure accuracy, conviction tiers)\n" + "=" * 80)
print(f"days: {len(DF)} (train {int(DF.is_train.sum())} / test {int((~DF.is_train).sum())})")

def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n; dd = 1 + z * z / n; ctr = (p + z * z / (2 * n)) / dd
    hw = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / dd
    return (round(100 * (ctr - hw), 1), round(100 * (ctr + hw), 1))

def binom_sf(k, n, p):
    return float(sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))) if n else 1.0

TARGETS = [
    ("08:00 -> window 10:15", "s800", "u800", "m_win", 15.0, None),
    ("09:30 -> session 16:00", "s930", "u930", "m_sess", None, 0.0010),
    ("09:40 -> next 60 min", "s940", "u940", "m_60", 10.0, None),
    ("09:40 -> rest of day", "s940", "u940", "m_rod", None, 0.0010),
]
TIERS = [("any |s|>=0.5", 0.5), ("strong |s|>=1.5", 1.5), ("max |s|>=2.5", 2.5)]

cells = []
for tname, scol, ucol, mcol, db_pts, db_pct in TARGETS:
    sub = DF.dropna(subset=[mcol]).copy()
    db = db_pts if db_pts is not None else db_pct * sub.px930
    out = np.where(sub[mcol] > db, 1, np.where(sub[mcol] < -db, -1, 0))
    te = (~sub.is_train).values
    base_up = 100 * (out[te] == 1).mean()
    print(f"\n--- {tname}  (test base P(up) {base_up:.1f}%, neutral {100*(out[te]==0).mean():.0f}%) ---")
    for lname, thr in TIERS + [("UNANIMOUS", None)]:
        if thr is not None:
            pred = np.where(np.abs(sub[scol]) >= thr, np.sign(sub[scol]), 0).astype(int)
        else:
            pred = (np.sign(sub[scol]) * sub[ucol]).astype(int)
        for split, mask in [("test", te)]:
            fire = (pred != 0) & mask
            n = int(fire.sum())
            if n == 0:
                continue
            k = int((pred[fire] == out[fire]).sum())
            acc = 100 * k / n
            # side accuracy among non-flat outcomes
            fnf = fire & (out != 0)
            side = 100 * (pred[fnf] == out[fnf]).mean() if fnf.sum() else 0
            cov = 100 * n / mask.sum()
            p_up = (out[fire] == 1).mean()
            best_const = max(p_up, (out[fire] == -1).mean(), (out[fire] == 0).mean())
            pv = binom_sf(k, n, max(p_up, 1e-9))
            cells.append(dict(target=tname, tier=lname, n=n, acc=round(acc, 1),
                              base=round(100 * p_up, 1), skill=round(acc - 100 * p_up, 1),
                              ci=wilson(k, n), cov=round(cov, 1),
                              side=round(side, 1), n_side=int(fnf.sum()), p=round(pv, 4)))
            print(f"   {lname:16s} coverage {cov:5.1f}% (n={n:3d})  acc {acc:5.1f}% "
                  f"CI{wilson(k, n)} vs base {100*p_up:5.1f}%  skill {acc-100*p_up:+5.1f}  "
                  f"| side-acc(non-flat) {side:5.1f}% (n={int(fnf.sum())})  p={pv:.3f}")

ps = [c["p"] for c in cells]
def bh(ps, q=0.10):
    m = len(ps); idx2 = sorted(range(m), key=lambda i: ps[i]); kmax = -1
    for r_, i in enumerate(idx2, 1):
        if ps[i] <= q * r_ / m:
            kmax = r_
    return [sorted(range(m), key=lambda i: ps[i]).index(i) < kmax if kmax > 0 else False for i in range(m)]
rej = bh(ps)
sig = [cells[i] for i in range(len(cells)) if rej[i]]
print("\n" + "=" * 80)
print(f"BH FDR<=0.10 across {len(cells)} test cells: "
      f"{[(c['target'], c['tier'], c['acc']) for c in sig] if sig else 'NONE significant'}")
best60 = [c for c in cells if c["acc"] >= 60 and c["n"] >= 30]
print(f"cells reaching >=60% acc with n>=30: {[(c['target'], c['tier'], c['acc'], c['n']) for c in best60] or 'NONE'}")
print("=" * 80)
json.dump(dict(n_days=len(DF), cells=cells, bh_sig=sig), open(f"{S}/bias_pct_ladder.json", "w"))
pd.DataFrame(cells).to_csv(f"{S}/bias_pct_ladder.csv", index=False)
print("saved bias_pct_ladder.csv/json")
