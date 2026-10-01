#!/usr/bin/env python3
"""Is the ORDER-FLOW filter real, or is it just selecting a delta sign?

The pin-bar entry already failed its random control (docs/FINDINGS-random-control-verdict.txt).
The only thing that ever moved its number was the order-flow filter. So: apply the SAME filter
to RANDOM entries and see whether filtered-random scores like filtered-pin-bar.

Only the BAR-DELTA half of the filter is testable this way - it is defined on any bar. The
wick-absorption half needs a wick, so a random bar has no counterpart. Tested: bar delta
running AGAINST the trade direction (condition B), on real signals and on matched randoms.

Matched exactly: same session day, same NY window, same direction, same risk in points,
same target multiple, same max hold, same cost. ONLY the entry bar is randomised.
"""
import argparse, numpy as np, pandas as pd, sys
sys.path.insert(0, "scripts")
from sma20_pinbar import load, resample, pivots, trend_flags, SESSIONS, TICK
from sma20_orderflow import load_footprint

def bar_delta(fts, fsg, fvl, ns0, ns1):
    a = np.searchsorted(fts, ns0); z = np.searchsorted(fts, ns1)
    if z - a < 5: return np.nan
    return float((fsg[a:z] * fvl[a:z]).sum())

def outcome(h, l, c, i, d, E, stop, risk, mult, hold, n, cost):
    tgt = E + d*mult*risk
    for k in range(i+1, min(n, i+1+hold)):
        hs = (l[k] <= stop) if d == 1 else (h[k] >= stop)
        ht = (h[k] >= tgt)  if d == 1 else (l[k] <= tgt)
        if hs: return (-risk - cost)/risk, "STOP"
        if ht: return (mult*risk - cost)/risk, "TARGET"
    k = min(n-1, i+hold)
    return (d*(c[k]-E) - cost)/risk, "FLAT"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tape", default="2023-26"); ap.add_argument("--tf", type=int, default=1)
    ap.add_argument("--trend", default="SIDE"); ap.add_argument("--W", type=float, default=1.0)
    ap.add_argument("--U", type=float, default=0.5); ap.add_argument("--buf", type=int, default=2)
    ap.add_argument("--mult", type=float, default=3.0); ap.add_argument("--cost", type=float, default=0.75)
    ap.add_argument("--minrisk", type=float, default=8.0); ap.add_argument("--maxhold", type=int, default=120)
    ap.add_argument("--repeats", type=int, default=10); ap.add_argument("--seed", type=int, default=11)
    a = ap.parse_args()

    print("loading footprint...", flush=True)
    fts, fpx, fsg, fvl = load_footprint()
    b = resample(load(a.tape), a.tf)
    o,h,l,c = (b[x].values.astype(float) for x in ("open","high","low","close"))
    sma = pd.Series(c).rolling(20).mean().values
    ph, pl = pivots(h, l)
    lo_t, sh_t = trend_flags(c, sma, h, l, ph, pl, a.trend)
    tmin = (b.index.hour*60 + b.index.minute).values
    t0, t1 = SESSIONS["NY"]; inwin = (tmin >= t0) & (tmin < t1)
    body=np.abs(c-o); rg=h-l; lw=np.minimum(o,c)-l; uw=h-np.maximum(o,c)
    with np.errstate(invalid="ignore"):
        lg = inwin & lo_t & (l<sma)&(c>sma)&(c>o)&(lw>=a.W*body)&(uw<=a.U*rg)
        sh = inwin & sh_t & (h>sma)&(c<sma)&(c<o)&(uw>=a.W*body)&(lw<=a.U*rg)
    lg=np.nan_to_num(lg,nan=False).astype(bool); sh=np.nan_to_num(sh,nan=False).astype(bool)
    ns = b.index.values.astype("datetime64[ns]").astype(np.int64); barns = a.tf*60*1_000_000_000
    day = b.index.normalize().values
    hold = max(1, a.maxhold//a.tf); n = len(c)
    rng = np.random.default_rng(a.seed)
    day_bars = {}
    for dd in np.unique(day[inwin]):
        day_bars[dd] = np.where((day == dd) & inwin)[0]

    real, rand = [], []
    busy = -1
    for i in np.where(lg | sh)[0]:
        if i <= 25 or i >= n-2 or i < busy: continue
        d = 1 if lg[i] else -1; E = c[i]
        stop = (l[i]-a.buf*TICK) if d==1 else (h[i]+a.buf*TICK)
        risk = (E-stop) if d==1 else (stop-E)
        if risk <= 0 or risk < a.minrisk: continue
        bd = bar_delta(fts, fsg, fvl, ns[i], ns[i]+barns)
        if not np.isfinite(bd): continue           # no footprint coverage -> skip both arms
        busy = i+1
        r, res = outcome(h,l,c,i,d,E,stop,risk,a.mult,hold,n,a.cost)
        real.append(dict(r=r, res=res, B=(d*bd) < 0))
        pool = day_bars.get(day[i])
        if pool is None or len(pool) < 3: continue
        for _ in range(a.repeats):
            j = int(rng.choice(pool[:-1]))
            if j <= 25 or j >= n-2: continue
            bdj = bar_delta(fts, fsg, fvl, ns[j], ns[j]+barns)
            if not np.isfinite(bdj): continue
            Ej = c[j]
            sj = Ej - d*risk                        # SAME risk in points, same direction
            rr, rs = outcome(h,l,c,j,d,Ej,sj,risk,a.mult,hold,n,a.cost)
            rand.append(dict(r=rr, res=rs, B=(d*bdj) < 0))
    R = pd.DataFrame(real); Q = pd.DataFrame(rand)
    print(f"\n{a.tape} {a.tf}min NY {a.trend} W{a.W} R{a.mult} cost{a.cost} minrisk{a.minrisk}")
    print(f"  real signals with footprint: {len(R)} | matched randoms: {len(Q)}\n")
    def line(lab, s):
        if len(s) < 10: print(f"  {lab:34s} n={len(s):5d}  --too few"); return None
        se = s.r.std(ddof=1)/np.sqrt(len(s))
        print(f"  {lab:34s} n={len(s):5d}  R {s.r.mean():+.4f}  t {s.r.mean()/se:+.2f}  "
              f"win {(s.res=='TARGET').mean():5.1%}")
        return s.r.mean()
    a1 = line("PIN BAR, unfiltered", R)
    a2 = line("RANDOM, unfiltered", Q)
    print()
    b1 = line("PIN BAR + bar-delta filter", R[R.B])
    b2 = line("RANDOM  + bar-delta filter", Q[Q.B])
    print()
    if None not in (a1,a2): print(f"  edge, unfiltered      : {a1-a2:+.4f} R")
    if None not in (b1,b2): print(f"  edge, both filtered   : {b1-b2:+.4f} R")
    if None not in (b2,a2): print(f"  filter lift on RANDOM : {b2-a2:+.4f} R   <-- does the filter work on noise?")
    if None not in (b1,a1): print(f"  filter lift on PIN BAR: {b1-a1:+.4f} R")

if __name__ == "__main__":
    main()
