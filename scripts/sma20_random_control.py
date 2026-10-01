#!/usr/bin/env python3
"""Matched random-entry control for the 20-SMA pin-bar rule (declared in the prereg).

For every real signal we generate REPEATS matched random trades: same session day,
same NY window, same risk in points, same target multiple, same max hold, same cost.
Only the ENTRY BAR is randomised. If the rule scores no better than this, the pin bar
carries no information and the geometry is doing all the work.
"""
import argparse, numpy as np, pandas as pd, sys
sys.path.insert(0, "scripts")
from sma20_pinbar import load, resample, pivots, trend_flags, SESSIONS, TICK

def signals(b, tf, sess, T, W, U, B, minrisk):
    o,h,l,c = (b[x].values.astype(float) for x in ("open","high","low","close"))
    sma = pd.Series(c).rolling(20).mean().values
    ph, pl = pivots(h, l)
    lo_t, sh_t = trend_flags(c, sma, h, l, ph, pl, T)
    tmin = (b.index.hour*60 + b.index.minute).values
    t0, t1 = SESSIONS[sess]; inwin = (tmin>=t0)&(tmin<t1)
    body=np.abs(c-o); rg=h-l; lw=np.minimum(o,c)-l; uw=h-np.maximum(o,c)
    with np.errstate(invalid="ignore"):
        lg = inwin & lo_t & (l<sma)&(c>sma)&(c>o)&(lw>=W*body)&(uw<=U*rg)
        sh = inwin & sh_t & (h>sma)&(c<sma)&(c<o)&(uw>=W*body)&(lw<=U*rg)
    lg = np.nan_to_num(lg,nan=False).astype(bool); sh = np.nan_to_num(sh,nan=False).astype(bool)
    out=[]; busy=-1
    for i in np.where(lg|sh)[0]:
        if i<=20 or i>=len(c)-2 or i<busy: continue
        d = 1 if lg[i] else -1
        E=c[i]; stop=(l[i]-B*TICK) if d==1 else (h[i]+B*TICK)
        risk=(E-stop) if d==1 else (stop-E)
        if risk<=0 or risk<minrisk: continue
        busy=i+1; out.append((i,d,E,risk))
    return out, (o,h,l,c), inwin

def play(px, i, d, E, risk, mult, hold, cost):
    o,h,l,c = px; n=len(c)
    stop = E - d*risk; tgt = E + d*mult*risk
    for k in range(i+1, min(n, i+1+hold)):
        hs = (l[k]<=stop) if d==1 else (h[k]>=stop)
        ht = (h[k]>=tgt)  if d==1 else (l[k]<=tgt)
        if hs: return (-risk-cost)/risk
        if ht: return (mult*risk-cost)/risk
    k = min(n-1, i+hold)
    return (d*(c[k]-E)-cost)/risk

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tape", default="2023-26"); ap.add_argument("--tf", type=int, default=3)
    ap.add_argument("--trend", default="SIDE"); ap.add_argument("--W", type=float, default=2.0)
    ap.add_argument("--U", type=float, default=0.5); ap.add_argument("--buf", type=int, default=2)
    ap.add_argument("--mult", type=float, default=2.0); ap.add_argument("--cost", type=float, default=0.75)
    ap.add_argument("--minrisk", type=float, default=0.0)
    ap.add_argument("--maxhold", type=int, default=120); ap.add_argument("--repeats", type=int, default=20)
    ap.add_argument("--seed", type=int, default=11)
    a = ap.parse_args()

    b = resample(load(a.tape), a.tf)
    sigs, px, inwin = signals(b, a.tf, "NY", a.trend, a.W, a.U, a.buf, a.minrisk)
    hold = max(1, a.maxhold//a.tf)
    real = np.array([play(px, i, d, E, r, a.mult, hold, a.cost) for i,d,E,r in sigs])

    # candidate random entry bars: any bar inside the same NY window, same day
    day = b.index.normalize().values
    ok = np.where(inwin)[0]
    by_day = {}
    for j in ok: by_day.setdefault(day[j], []).append(j)
    rng = np.random.default_rng(a.seed)
    means = []
    for _ in range(a.repeats):
        rr=[]
        for i,d,E,r in sigs:
            cand = by_day.get(day[i], [])
            cand = [j for j in cand if 20 < j < len(px[3])-2]
            if not cand: continue
            j = int(rng.choice(cand))
            rr.append(play(px, j, d, px[3][j], r, a.mult, hold, a.cost))
        means.append(np.mean(rr))
    means = np.array(means)
    z = (real.mean()-means.mean())/means.std(ddof=1) if means.std(ddof=1)>0 else np.nan
    print(f"{a.tape} {a.tf}min NY {a.trend} W{a.W} R{a.mult} cost{a.cost} minrisk{a.minrisk}")
    print(f"  rule   : {real.mean():+.4f} R over {len(real)} trades")
    print(f"  random : {means.mean():+.4f} R  (sd {means.std(ddof=1):.4f} over {a.repeats} draws,"
          f" range {means.min():+.4f} to {means.max():+.4f})")
    print(f"  EDGE   : {real.mean()-means.mean():+.4f} R   ({z:+.2f} sd above the random mean)")

if __name__ == "__main__":
    main()
