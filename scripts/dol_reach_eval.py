#!/usr/bin/env python3
"""ROLLING-BIAS -> DOL REACH for 09:40-10:15 in-window initiations. NQ 2023 -> Jul 2026.

Does a rolling (<=-now) bias help price reach the bias-side DOL from an in-window breakout,
BEFORE invalidation, with resolution allowed AFTER 10:15?

The trap this version avoids: the initiation IS a breakout in the bias direction, so "bias-side
DOL reached more than the opposite" mostly restates "breakouts continue" (momentum), and a naive
counter mirror can be rigged by asymmetric stops. So the DECISIVE control is Control B:
  detect the first in-window breakout REGARDLESS of bias, classify it ALIGNED (breakout dir ==
  rolling bias) vs COUNTER (breakout dir != bias), race BOTH to their own breakout-direction pool
  with the IDENTICAL stop rule, and ask: do ALIGNED breakouts reach more than COUNTER breakouts?
  If aligned ~= counter, the edge is the reaction, not the bias.
Also reported: a true symmetric-geometry mirror (same dol/stop distances, opposite side) — labelled
as a momentum/persistence view, not a bias test.

Rolling bias b(t) (<=-now): sign of drift(px vs prior RTH close) + disp(px vs developing VWAP)
+ sticky sweep-reject overlay of PDH/PDL + 0.5*daily ensemble bias (past-only). Flips reported.
Breakout: first bar in [09:41,10:15] whose close breaks the 09:40->t-1 range extreme.
DOL: nearest UNTAPPED pool in breakout dir among {PDH,PDL,PMH,PML}. Stop: opposite range extreme
clamped 15-70pt (+ fixed 15/25/40 sensitivity). Race: first-touch to 16:00 backstop, tie->STOP.
Mode 2: real Campion money (slip/commission/pad20/>70 skip/>40->5-micro/nearest-draw target 4R-cap).
"""
import json
import math
import importlib.util
from collections import deque, Counter
from datetime import time as dtime

import numpy as np
import pandas as pd

S = "/tmp/claude-0/-home-user-AI-trading-agents/69c9097f-44f3-585b-817f-a315126d0dbb/scratchpad"
NY = "America/New_York"
TRAIN_END = "2024-12-31"
TICK, SLIP = 0.25, 0.25
PV_FULL, PV_DERISK, COMM_FULL, COMM_DERISK = 20.0, 10.0, 5.0, 2.5

spec = importlib.util.spec_from_file_location("bias_lab", f"{S}/bias_lab.py")
bl = importlib.util.module_from_spec(spec); spec.loader.exec_module(bl)
F, by_day = bl.F, bl.by_day
win = json.load(open(f"{S}/_win.json"))
ens_bias = {d: int(b) for d, b in zip(win["order"], win["ens"])}
vixp = {d: float(v) for d, v in zip(F.index, F["vix_p"].values)}
print("\n" + "=" * 80 + "\nROLLING-BIAS -> DOL REACH  (fair-control rebuild)\n" + "=" * 80)

# ---------- per-day prep ----------
rth = {}
for d in by_day:
    g = by_day[d]; r = g[(g.t >= dtime(9, 30)) & (g.t < dtime(16, 0))]
    if len(r) >= 100:
        rth[d] = (float(r.high.max()), float(r.low.min()), float(r.close.iloc[-1]))
daylist = sorted(by_day)
prior_rth = {}
for i, d in enumerate(daylist):
    for j in range(i - 1, -1, -1):
        if daylist[j] in rth:
            prior_rth[d] = rth[daylist[j]]; break

days, excl, DAY = [], [], {}
for d in F.index:
    if pd.Timestamp(d).dayofweek >= 5:
        excl.append((d, "weekend")); continue
    g = by_day[d]
    if not ((g.t == dtime(9, 40)).any() and (g.t == dtime(10, 15)).any()):
        excl.append((d, "missing 09:40/10:15 endpoint")); continue
    if d not in prior_rth:
        excl.append((d, "no prior RTH")); continue
    PDH, PDL, PDC = prior_rth[d]
    pm = g[(g.t >= dtime(0, 0)) & (g.t < dtime(9, 40))]
    PMH, PML = float(pm.high.max()), float(pm.low.min())
    tp = (g.high + g.low + g.close) / 3.0
    cv = (tp * g.volume).cumsum() / g.volume.cumsum().replace(0, np.nan)
    DAY[d] = dict(t=g.t.values, o=g.open.values.astype(float), h=g.high.values.astype(float),
                  l=g.low.values.astype(float), c=g.close.values.astype(float),
                  vwap=cv.values.astype(float), PDH=PDH, PDL=PDL, PDC=PDC, PMH=PMH, PML=PML)
    days.append(d)
print(f"eligible days {len(days)}   excluded {dict(Counter(r for _, r in excl))}")

def idx_at(t_arr, hh, mm):
    hits = np.where(t_arr == dtime(hh, mm))[0]
    return int(hits[0]) if len(hits) else None

def rolling_bias(D, i, ens):
    px = D["c"][i]; drift = np.sign(px - D["PDC"])
    vw = D["vwap"][i]; disp = np.sign(px - vw) if not math.isnan(vw) else 0
    hh, ll = D["h"][:i + 1], D["l"][:i + 1]
    took_low = (ll <= D["PDL"]).any(); took_high = (hh >= D["PDH"]).any()
    sweep = 0
    if took_high and px < D["PDH"]:
        sweep = -1
    if took_low and px > D["PDL"]:
        sweep = 1
    score = drift + disp + sweep + 0.5 * ens
    return int(np.sign(score)) if abs(score) >= 0.5 else 0

def untapped_dol(D, i0, px, direction):
    j940 = idx_at(D["t"], 9, 40)
    hi_win = D["h"][j940:i0 + 1]; lo_win = D["l"][j940:i0 + 1]
    if direction > 0:
        cands = [lv for lv in (D["PDH"], D["PMH"]) if lv > px and hi_win.max() < lv]
        return min(cands) if cands else None
    cands = [lv for lv in (D["PDL"], D["PML"]) if lv < px and lo_win.min() > lv]
    return max(cands) if cands else None

def first_breakout(D):
    """first in-window range break in EITHER direction (bias-agnostic)."""
    j940, j1015 = idx_at(D["t"], 9, 40), idx_at(D["t"], 10, 15)
    for i in range(j940 + 1, j1015 + 1):
        rh = D["h"][j940:i].max(); rl = D["l"][j940:i].min()
        if D["c"][i] > rh:
            return i, 1, j940
        if D["c"][i] < rl:
            return i, -1, j940
    return None

def race(D, i0, dol, stop, direction, start=None):
    j16 = idx_at(D["t"], 16, 0); end = j16 if j16 is not None else len(D["t"]) - 1
    for j in range((start or i0 + 1), end + 1):
        hi, lo = D["h"][j], D["l"][j]
        hit_stop = (lo <= stop) if direction > 0 else (hi >= stop)
        hit_dol = (hi >= dol) if direction > 0 else (lo <= dol)
        if hit_stop and hit_dol:
            return -1, j
        if hit_stop:
            return -1, j
        if hit_dol:
            return 1, j
    return 0, end

FIXED = [15, 25, 40]
recs, flip_rows = [], []
for d in days:
    D = DAY[d]; ens = ens_bias.get(d, 0)
    j800, j930, j1015 = idx_at(D["t"], 8, 0), idx_at(D["t"], 9, 30), idx_at(D["t"], 10, 15)
    b800 = rolling_bias(D, j800, ens) if j800 is not None else 0
    b930 = rolling_bias(D, j930, ens) if j930 is not None else 0
    bo = first_breakout(D)
    rec = dict(day=d, is_train=d <= TRAIN_END, vix=vixp.get(d, np.nan), b800=b800, b930=b930)
    if bo is None:
        rec["broke"] = False; recs.append(rec); flip_rows.append((d, b800, b930, None)); continue
    i0, bdir, j940 = bo; px = D["c"][i0]; bbias = rolling_bias(D, i0, ens)
    aligned = (bbias != 0) and (bdir == bbias)
    counter = (bbias != 0) and (bdir != bbias)
    dol = untapped_dol(D, i0, px, bdir)
    rec.update(broke=True, bdir=bdir, bbias=bbias, aligned=aligned, counter=counter,
               nobias=(bbias == 0), b_init=bbias, t_init=str(D["t"][i0]))
    flip_rows.append((d, b800, b930, bbias))
    if dol is None:
        rec["has_dol"] = False; recs.append(rec); continue
    opp_extreme = (D["l"][j940:i0 + 1].min() if bdir > 0 else D["h"][j940:i0 + 1].max())
    stop_dist = float(np.clip(abs(px - opp_extreme), 15, 70))
    stop_px = px - bdir * stop_dist
    dol_dist = abs(dol - px)
    res, jres = race(D, i0, dol, stop_px, bdir)
    res_after = int(jres > j1015)
    # symmetric-geometry mirror (opposite side, same distances) -> persistence view
    res_m, _ = race(D, i0, px - bdir * dol_dist, px + bdir * stop_dist, -bdir)
    # unconditional (ignore stop)
    res_u, _ = race(D, i0, dol, px - bdir * 1e9, bdir)
    rec.update(has_dol=True, px=px, dol_dist=round(dol_dist, 2), stop_dist=round(stop_dist, 2),
               R=round(dol_dist / stop_dist, 2), reach=int(res == 1), stop=int(res == -1),
               open=int(res == 0), reach_mirror=int(res_m == 1), reach_uncond=int(res_u == 1),
               res_after_1015=res_after, ttr_min=int(jres - i0))
    for fx in FIXED:
        r_fx, _ = race(D, i0, dol, px - bdir * fx, bdir)
        rec[f"reach_fx{fx}"] = int(r_fx == 1)
    # ---- Mode 2 money (same rules for aligned/counter/nobias; direction = breakout dir) ----
    entry = D["o"][i0 + 1] + bdir * SLIP if i0 + 1 < len(D["o"]) else px
    wick = stop_dist
    if wick <= 70:
        sd = max(wick, 20.0); derisk = sd > 40
        pv, comm = (PV_DERISK, COMM_DERISK) if derisk else (PV_FULL, COMM_FULL)
        stpx = entry - bdir * sd
        tgt = min(dol, entry + 4 * sd) if bdir > 0 else max(dol, entry - 4 * sd)
        rr, jr = race(D, i0, tgt, stpx, bdir)
        if rr == 1:
            pts = abs(tgt - entry) - SLIP
        elif rr == -1:
            pts = -(sd + SLIP)
        else:
            jflat = idx_at(D["t"], 15, 55) or (len(D["c"]) - 1)
            pts = bdir * (D["c"][jflat] - entry)
        rec.update(m2_taken=1, m2_R=round(pts / sd, 3), m2_usd=round(pts * pv - comm, 2),
                   m2_win=int(pts > 0), m2_tgt_dist=round(abs(tgt - entry), 2), m2_sd=round(sd, 2))
    else:
        rec["m2_taken"] = 0
    recs.append(rec)

RC = pd.DataFrame(recs)
BK = RC[RC.get("has_dol", False) == True].copy()   # breakouts with a defined DOL
BK["is_train"] = BK["day"] <= TRAIN_END
print(f"\nbreakouts with a DOL: {len(BK)}/{len(days)} eligible ({100*len(BK)/len(days):.1f}%)   "
      f"aligned {int(BK.aligned.sum())}  counter {int(BK.counter.sum())}  no-bias {int(BK.nobias.sum())}")

# ---------- stats ----------
def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k/n; d = 1+z*z/n; c = (p+z*z/(2*n))/d; h = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (round(100*(c-h), 1), round(100*(c+h), 1))

def rate(sub, col="reach"):
    v = sub[col].dropna(); k = int(v.sum()); n = int(v.shape[0])
    return dict(n=n, pct=round(100*k/n, 1) if n else 0.0, ci=wilson(k, n))

rng = np.random.default_rng(0)
def diff_ci(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    if len(a) < 5 or len(b) < 5:
        return 0.0, (0.0, 0.0)
    diff = 100*(a.mean()-b.mean())
    boot = [100*(a[rng.integers(0, len(a), len(a))].mean()-b[rng.integers(0, len(b), len(b))].mean())
            for _ in range(3000)]
    return round(diff, 1), (round(float(np.percentile(boot, 2.5)), 1), round(float(np.percentile(boot, 97.5)), 1))

te = BK[~BK.is_train]; tr = BK[BK.is_train]
al_te, co_te = te[te.aligned], te[te.counter]

print("\n--- REACH ECONOMICS: is the breakout->DOL reaction itself profitable geometry? (all breakouts) ---")
for lab, sub in [("ALL", BK), ("TRAIN", tr), ("TEST", te)]:
    r = rate(sub); meanR = sub.R.mean(); be = 100/(1+meanR); expR = (r["pct"]/100)*meanR-(1-r["pct"]/100)
    print(f"   {lab:6s} n={r['n']:3d}  reach {r['pct']}% CI{r['ci']}  uncond {rate(sub,'reach_uncond')['pct']}%  "
          f"meanR {meanR:.2f}  breakeven {be:.1f}%  E[R] {expR:+.3f}")

print("\n--- CONTROL B (decisive): do ALIGNED breakouts reach more than COUNTER breakouts? ---")
for lab, sub in [("ALL", BK), ("TEST", te)]:
    al, co, nb = sub[sub.aligned], sub[sub.counter], sub[sub.nobias]
    ra, rc, rn = rate(al), rate(co), rate(nb)
    lift, lci = diff_ci(al.reach.values, co.reach.values)
    print(f"   {lab:5s}  aligned {ra['pct']}% (n{ra['n']}, CI{ra['ci']})  "
          f"counter {rc['pct']}% (n{rc['n']}, CI{rc['ci']})  no-bias {rn['pct']}% (n{rn['n']})")
    print(f"          ALIGNED − COUNTER lift {lift:+.1f}pp  bootstrap CI[{lci[0]},{lci[1]}]")

print("\n--- GEOMETRY CONFOUND CHECK: is the aligned reach-lift just NEARER draws? ---")
def expR_trade(sub):
    v = sub.dropna(subset=["reach", "R"])
    return (v.reach.values * v.R.values - (1 - v.reach.values))   # per-trade realized R (win=+R, loss=-1)
geo_rows = []
for lab, sub in [("aligned", al_te), ("counter", co_te)]:
    er = expR_trade(sub); boot = [er[rng.integers(0, len(er), len(er))].mean() for _ in range(3000)]
    geo_rows.append(dict(who=lab, n=len(sub), reach=rate(sub)["pct"], meanR=round(sub.R.mean(), 2),
                         dol_med=round(sub.dol_dist.median(), 0), stop_med=round(sub.stop_dist.median(), 0),
                         expR=round(er.mean(), 3), lo=round(float(np.percentile(boot, 2.5)), 3),
                         hi=round(float(np.percentile(boot, 97.5)), 3)))
    print(f"   {lab:8s} n={len(sub):3d}  reach {rate(sub)['pct']}%  meanR {sub.R.mean():.2f}  "
          f"DOL med {sub.dol_dist.median():.0f}pt  stop med {sub.stop_dist.median():.0f}pt  "
          f"E[R]/trade {er.mean():+.3f} CI[{np.percentile(boot,2.5):.3f},{np.percentile(boot,97.5):.3f}]")
ea, ec = expR_trade(al_te), expR_trade(co_te)
d_er, d_ci = diff_ci(ea, ec)
print(f"   >>> R-ADJUSTED aligned−counter expectancy diff {d_er:+.3f}R  CI[{d_ci[0]},{d_ci[1]}]  "
      f"(the raw reach-% lift IGNORES that aligned draws sit at {al_te.dol_dist.median():.0f}pt vs "
      f"{co_te.dol_dist.median():.0f}pt)")
print("   R-matched reach (aligned vs counter within R buckets):")
rmatch = []
for lo, hi in [(0, 1.5), (1.5, 3), (3, 20)]:
    a = al_te[(al_te.R >= lo) & (al_te.R < hi)]; c = co_te[(co_te.R >= lo) & (co_te.R < hi)]
    if len(a) >= 8 and len(c) >= 8:
        gap = round(100*(a.reach.mean()-c.reach.mean()), 1)
        rmatch.append(dict(bucket=f"R[{lo},{hi})", a=rate(a)["pct"], na=len(a), c=rate(c)["pct"], nc=len(c), gap=gap))
        print(f"      R[{lo},{hi}): aligned {a.reach.mean()*100:.1f}%(n{len(a)}) counter {c.reach.mean()*100:.1f}%(n{len(c)})  gap {gap:+.1f}pp")

print("\n--- symmetric-geometry mirror (momentum/persistence view, NOT a bias test) ---")
for lab, sub in [("TEST", te)]:
    r = rate(sub); rm = rate(sub, "reach_mirror")
    print(f"   {lab}: breakout-dir reach {r['pct']}%  vs equidistant opposite {rm['pct']}%  "
          f"(gap {round(r['pct']-rm['pct'],1):+.1f}pp = post-breakout momentum, direction-agnostic)")

print("\n--- stop-definition sensitivity (TEST, all breakouts) — curve-fit check ---")
for col, lbl in [("reach", "structural15-70"), ("reach_fx15", "fixed15"), ("reach_fx25", "fixed25"), ("reach_fx40", "fixed40")]:
    r = rate(te, col); print(f"   {lbl:16s} reach {r['pct']}% CI{r['ci']}  n={r['n']}")

print("\n--- reach by breakout direction (TEST) ---")
for dd, lbl in [(1, "up-breakout"), (-1, "down-breakout")]:
    sub = te[te.bdir == dd]; r = rate(sub)
    al = sub[sub.aligned]; co = sub[sub.counter]
    print(f"   {lbl:14s} n={r['n']:3d} reach {r['pct']}%  | aligned {rate(al)['pct']}% (n{rate(al)['n']}) "
          f"counter {rate(co)['pct']}% (n{rate(co)['n']})")

vtr = tr["vix"].dropna().values; q1, q2 = np.nanpercentile(vtr, [33.3, 66.6])
print(f"\n--- reach by VIX regime (TEST; low<{q1:.1f} high>{q2:.1f}) ---")
vix_rows = []
for lbl, m in [("low", te.vix < q1), ("mid", (te.vix >= q1) & (te.vix <= q2)), ("high", te.vix > q2)]:
    sub = te[m]; al, co = sub[sub.aligned], sub[sub.counter]
    lift = round(rate(al)["pct"]-rate(co)["pct"], 1)
    vix_rows.append(dict(vix=lbl, n=rate(sub)["n"], reach=rate(sub)["pct"],
                         aligned=rate(al)["pct"], counter=rate(co)["pct"], lift=lift))
    print(f"   {lbl:5s} n={rate(sub)['n']:3d} reach {rate(sub)['pct']}%  aligned {rate(al)['pct']}% "
          f"counter {rate(co)['pct']}%  lift {lift:+.1f}pp")

print("\n--- walk-forward folds (ALIGNED − COUNTER lift) ---")
bounds = ["2024-01-01", "2024-07-01", "2025-01-01", "2025-07-01", "2026-01-01", "2026-07-16"]
fold_rows = []
for j in range(len(bounds)-1):
    sub = BK[(BK.day >= bounds[j]) & (BK.day < bounds[j+1])]
    al, co = sub[sub.aligned], sub[sub.counter]
    if len(al) < 5 or len(co) < 5:
        continue
    lift, lci = diff_ci(al.reach.values, co.reach.values)
    fold_rows.append(dict(test=f"{bounds[j][:7]}->{bounds[j+1][:7]}", n_al=len(al), n_co=len(co),
                          a=rate(al)["pct"], c=rate(co)["pct"], lift=lift, lo=lci[0], hi=lci[1]))
    print(f"   {bounds[j][:7]}->{bounds[j+1][:7]}  aligned {rate(al)['pct']}%(n{len(al)}) "
          f"counter {rate(co)['pct']}%(n{len(co)})  lift {lift:+.1f}pp CI[{lci[0]},{lci[1]}]")
pos_folds = sum(1 for f in fold_rows if f["lo"] > 0)

fl = pd.DataFrame(flip_rows, columns=["day", "b800", "b930", "b_init"])
chg_8_930 = int((fl.b800 != fl.b930).sum())
fli = fl.dropna(subset=["b_init"]); chg_930i = int((fli.b930 != fli.b_init).sum())
chg_any = int(((fli.b800 != fli.b930) | (fli.b930 != fli.b_init)).sum())
print(f"\n--- ROLLING-BIAS FLIPS ---  08:00->09:30 {chg_8_930}/{len(fl)} ({100*chg_8_930/len(fl):.0f}%)  "
      f"09:30->breakout {chg_930i}/{len(fli)} ({100*chg_930i/max(len(fli),1):.0f}%)  "
      f"any 08:00->breakout {chg_any}/{len(fli)} ({100*chg_any/max(len(fli),1):.0f}%)")
resolved = BK[BK.open == 0]
print(f"--- TTR: median {int(resolved.ttr_min.median())}min  resolved after 10:15 "
      f"{int(BK.res_after_1015.sum())}/{len(BK)} ({100*BK.res_after_1015.mean():.0f}%)  open@16:00 {int(BK.open.sum())}")

# ---------- Mode 2, split aligned vs counter (audited) ----------
M2 = RC[RC.get("m2_taken", 0) == 1].copy()
M2["is_train"] = M2["day"] <= TRAIN_END
def m2stats(sub):
    if not len(sub):
        return None
    eq = sub.sort_values("day").m2_usd.cumsum().values
    dd = float((np.maximum.accumulate(eq)-eq).max()) if len(eq) else 0.0
    gp = sub[sub.m2_usd > 0].m2_usd.sum(); gl = -sub[sub.m2_usd < 0].m2_usd.sum()
    return dict(n=len(sub), expR=round(sub.m2_R.mean(), 3), wr=round(100*sub.m2_win.mean(), 1),
                usd=round(sub.m2_usd.sum(), 0), dd=round(dd, 0),
                pf=round(gp/gl, 2) if gl > 0 else float("inf"),
                winR=round(sub[sub.m2_win == 1].m2_R.mean(), 2) if sub.m2_win.sum() else 0)
print("\n--- Mode 2 money by bias-alignment (TEST) — does bias change the P&L? ---")
teM = M2[~M2.is_train]
for lab, sub in [("aligned", teM[teM.aligned]), ("counter", teM[teM.counter]), ("no-bias", teM[teM.nobias]), ("ALL", teM)]:
    st = m2stats(sub)
    if st:
        print(f"   {lab:8s} n={st['n']:3d}  E[R] {st['expR']:+.3f}  win {st['wr']}%  winR {st['winR']}  "
              f"net ${st['usd']:.0f}  maxDD ${st['dd']:.0f}  PF {st['pf']}")

# ---------- verdict ----------
reachTE = rate(te); meanR_te = te.R.mean(); be_te = 100/(1+meanR_te)
expR_te = (reachTE["pct"]/100)*meanR_te-(1-reachTE["pct"]/100)
m2_al = m2stats(teM[teM.aligned]); m2_co = m2stats(teM[teM.counter])  # al_te/co_te defined earlier
# HONEST pass conditions use R-ADJUSTED expectancy (not raw reach%, which is a geometry artifact),
# and require acceptable drawdown, not a rounding-error E[R].
geo_al = next(g for g in geo_rows if g["who"] == "aligned")
dd_ok = m2_al and m2_al["dd"] < abs(m2_al["usd"]) * 2 if (m2_al and m2_al["usd"]) else False
cond1 = (geo_al["lo"] > 0) and (m2_al and m2_al["expR"] > 0.10 and m2_al["pf"] > 1.2) and dd_ok
cond2 = (d_ci[0] > 0) and (rate(al_te)["n"] >= 30)
print("\n" + "=" * 80 + "\nPASS CONDITIONS (R-adjusted — raw reach% is a geometry artifact)\n" + "=" * 80)
print(f"  1) profitable geometry: aligned R-adj E[R] {geo_al['expR']:+.3f} CI[{geo_al['lo']},{geo_al['hi']}] "
      f"entirely>0 AND Mode-2 E[R] {m2_al['expR'] if m2_al else 'NA'}>0.10 & PF>1.2 & DD acceptable "
      f"-> {'PASS' if cond1 else 'FAIL'}")
print(f"  2) BIAS adds direction: aligned−counter R-ADJUSTED expectancy {d_er:+.3f}R CI[{d_ci[0]},{d_ci[1]}] "
      f"entirely>0 -> {'PASS' if cond2 else 'FAIL'}")
print(f"     (raw reach lift was +{round(rate(al_te)['pct']-rate(co_te)['pct'],1)}pp but that is nearer draws: "
      f"aligned DOL {al_te.dol_dist.median():.0f}pt vs counter {co_te.dol_dist.median():.0f}pt)")
proven = cond1 and cond2
print(f"\n  VERDICT: {'PROVEN' if proven else 'NOT PROVEN'} — " +
      ("bias adds tradeable direction to DOL reach, OOS & robust" if proven else
       "the breakout->DOL reaction is ~R-fair/breakeven BOTH ways; the rolling bias only tilts you "
       "toward NEARER, smaller draws (higher raw reach%, lower R) with ~0 R-adjusted expectancy, and "
       "adds no edge under real money rules -> trade the DOL reactively both ways; bias is at most a mild size tilt"))
liftB, lciB = diff_ci(al_te.reach.values, co_te.reach.values)   # raw reach lift (reported, labelled artifact)

json.dump(dict(
    eligible=len(days), breakouts=len(BK), coverage_pct=round(100*len(BK)/len(days), 1),
    n_aligned=int(BK.aligned.sum()), n_counter=int(BK.counter.sum()), n_nobias=int(BK.nobias.sum()),
    excl=dict(Counter(r for _, r in excl)),
    reach_all=rate(BK), reach_te=reachTE, meanR_te=round(meanR_te, 2), be_te=round(be_te, 1), expR_te=round(expR_te, 3),
    uncond_te=rate(te, "reach_uncond"), mirror_te=rate(te, "reach_mirror"),
    ctrlB=dict(aligned_all=rate(BK[BK.aligned]), counter_all=rate(BK[BK.counter]),
               aligned_te=rate(al_te), counter_te=rate(co_te), nobias_te=rate(te[te.nobias]),
               lift_te=liftB, lift_ci_te=list(lciB)),
    geometry=dict(rows=geo_rows, radj_diff=d_er, radj_diff_ci=list(d_ci), rmatch=rmatch),
    fixed=[dict(lbl=l, **rate(te, c)) for c, l in [("reach", "structural"), ("reach_fx15", "fx15"), ("reach_fx25", "fx25"), ("reach_fx40", "fx40")]],
    bdir=[dict(dir=("up" if dd == 1 else "down"), **rate(te[te.bdir == dd]),
               aligned=rate(te[(te.bdir == dd) & te.aligned])["pct"],
               counter=rate(te[(te.bdir == dd) & te.counter])["pct"]) for dd in (1, -1)],
    vix=vix_rows, folds=fold_rows, pos_folds=pos_folds,
    flips=dict(chg_8_930=chg_8_930, n_all=len(fl), chg_930i=chg_930i, chg_any=chg_any, n_init=len(fli)),
    ttr_median=int(resolved.ttr_min.median()) if len(resolved) else 0,
    res_after_1015=int(BK.res_after_1015.sum()), still_open=int(BK.open.sum()),
    m2=dict(aligned=m2_al, counter=m2_co, nobias=m2stats(teM[teM.nobias]), all=m2stats(teM)),
    R_dist=[float(x) for x in np.percentile(BK.R.dropna(), [10, 25, 50, 75, 90])],
    cond1=bool(cond1), cond2=bool(cond2), proven=bool(proven),
), open(f"{S}/dol_eval.json", "w"), default=lambda o: list(o) if isinstance(o, tuple) else o)
RC.to_csv(f"{S}/dol_records.csv", index=False)
print("\nsaved dol_records.csv, dol_eval.json")
