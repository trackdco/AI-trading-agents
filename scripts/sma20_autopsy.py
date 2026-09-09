#!/usr/bin/env python3
"""Stage 4 - loser autopsy for the 20-SMA pin-bar rule.

Builds one wide feature row per trade, all of it knowable AT ENTRY, then asks which
features separate winners from losers. Confluences measured as distance-to-entry:

  levels   prior day H/L, prior session (Asia/London) H/L, overnight H/L,
           prior-day POC/VAH/VAL, NY opening-range H/L, round numbers,
           higher-timeframe 20 SMA, fib 0.382/0.5/0.618/0.705/0.786 of the last
           prominent leg (drawn the way the video describes: pivot low -> pivot high
           in an uptrend, invalidated if price makes a new extreme first)
  context  how far price stretched from the SMA before pulling back, retrace depth,
           minutes into the session, wick/body ratio, wick size in ATR, stop size,
           ATR, SMA slope, trend age, day range so far vs ATR, direction, VIX
"""
import argparse, numpy as np, pandas as pd, sys
sys.path.insert(0, "scripts")
from sma20_pinbar import load, resample, pivots, trend_flags, SESSIONS, TICK

FIBS = [0.382, 0.5, 0.618, 0.705, 0.786]

def atr(h, l, c, n=14):
    pc = np.roll(c, 1); pc[0] = c[0]
    tr = np.maximum(h - l, np.maximum(abs(h - pc), abs(l - pc)))
    return pd.Series(tr).rolling(n).mean().values

def profile_levels(day_bars, binsz=1.0):
    """POC / VAH / VAL from a session's 1-min bars, volume placed at each bar's close."""
    if len(day_bars) < 30: return (np.nan,)*3
    px = (day_bars.close.values / binsz).round() * binsz
    v = pd.Series(day_bars.volume.values).groupby(px).sum().sort_index()
    if v.empty: return (np.nan,)*3
    poc = v.idxmax(); tot = v.sum(); order = v.sort_values(ascending=False)
    keep = order.cumsum() <= 0.70 * tot
    sel = order[keep].index if keep.any() else pd.Index([poc])
    return float(poc), float(max(sel)), float(min(sel))

def fib_leg(h, l, dph, dpl, i, d):
    """Last prominent leg in the trade's direction, invalidated if price made a new
    extreme past the leg origin before retracing. Returns (lo, hi) or None."""
    k = 12
    hi_j = lo_j = None
    for j in range(i - k, max(0, i - 500), -1):
        if d == 1 and dph[j] and hi_j is None: hi_j = j
        if d == -1 and dpl[j] and lo_j is None: lo_j = j
        if d == 1 and hi_j is not None and dpl[j] and j < hi_j: lo_j = j; break
        if d == -1 and lo_j is not None and dph[j] and j < lo_j: hi_j = j; break
    if hi_j is None or lo_j is None: return None
    if d == 1:
        if l[lo_j:i+1].min() < l[lo_j]: return None          # broke the leg origin
        return l[lo_j], h[hi_j]
    if h[hi_j:i+1].max() > h[hi_j]: return None
    return l[lo_j], h[hi_j]

def build(tape, tf, trend, W, U, B, mult, cost, minrisk, maxhold):
    raw = load(tape); b = resample(raw, tf)
    o,h,l,c = (b[x].values.astype(float) for x in ("open","high","low","close"))
    vol = b.volume.values.astype(float)
    sma = pd.Series(c).rolling(20).mean().values
    a14 = atr(h, l, c)
    ph, pl = pivots(h, l); dph, dpl = pivots(h, l, k=10)
    lo_t, sh_t = trend_flags(c, sma, h, l, ph, pl, trend)
    # higher-timeframe SMA20 (15-min), reindexed onto the traded bars, causal
    h15 = resample(raw, 15); s15 = pd.Series(h15.close.values, index=h15.index).rolling(20).mean()
    sma15 = s15.reindex(b.index, method="ffill").values
    tmin = (b.index.hour*60 + b.index.minute).values
    day = b.index.normalize()
    t0,t1 = SESSIONS["NY"]; inwin = (tmin>=t0)&(tmin<t1)
    body=np.abs(c-o); rg=h-l; lw=np.minimum(o,c)-l; uw=h-np.maximum(o,c)
    with np.errstate(invalid="ignore"):
        lg = inwin & lo_t & (l<sma)&(c>sma)&(c>o)&(lw>=W*body)&(uw<=U*rg)
        sh = inwin & sh_t & (h>sma)&(c<sma)&(c<o)&(uw>=W*body)&(lw<=U*rg)
    lg=np.nan_to_num(lg,nan=False).astype(bool); sh=np.nan_to_num(sh,nan=False).astype(bool)

    # ---- per-session reference levels, all from bars strictly BEFORE the NY open ----
    m1 = raw.copy(); m1["tmin"] = m1.index.hour*60 + m1.index.minute
    m1["sess"] = np.where(m1.tmin >= 18*60, (m1.index.normalize()+pd.Timedelta(days=1)).values,
                          m1.index.normalize().values)
    rth = m1[(m1.tmin>=570)&(m1.tmin<960)]
    pdh = rth.groupby(rth.index.normalize()).high.max().shift(1)
    pdl_ = rth.groupby(rth.index.normalize()).low.min().shift(1)
    prof = {d_: profile_levels(g) for d_, g in rth.groupby(rth.index.normalize())}
    prof_prev = {}
    keys = sorted(prof); 
    for n_, d_ in enumerate(keys):
        if n_: prof_prev[d_] = prof[keys[n_-1]]
    pre = m1[m1.tmin < 570]
    onh = pre.groupby("sess").high.max(); onl = pre.groupby("sess").low.min()
    asia = m1[(m1.tmin>=18*60)|(m1.tmin<3*60)]
    ah = asia.groupby("sess").high.max(); al = asia.groupby("sess").low.min()
    ldn = m1[(m1.tmin>=3*60)&(m1.tmin<570)]
    lh = ldn.groupby("sess").high.max(); ll = ldn.groupby("sess").low.min()
    orb = m1[(m1.tmin>=570)&(m1.tmin<585)]
    oh_ = orb.groupby(orb.index.normalize()).high.max()
    ol_ = orb.groupby(orb.index.normalize()).low.min()
    try:
        vix = pd.read_csv("data/reference/vix_daily.csv", parse_dates=["date"]).set_index("date").vix
    except Exception: vix = pd.Series(dtype=float)

    hold = max(1, maxhold//tf); n=len(c); rows=[]; busy=-1
    for i in np.where(lg|sh)[0]:
        if i<=40 or i>=n-2 or i<busy: continue
        d = 1 if lg[i] else -1
        E=c[i]; stop=(l[i]-B*TICK) if d==1 else (h[i]+B*TICK)
        risk=(E-stop) if d==1 else (stop-E)
        if risk<=0 or risk<minrisk: continue
        busy=i+1
        tgt=E+d*mult*risk; res="FLAT"; pnl=None
        for k in range(i+1, min(n,i+1+hold)):
            hs=(l[k]<=stop) if d==1 else (h[k]>=stop)
            ht=(h[k]>=tgt)  if d==1 else (l[k]<=tgt)
            if hs: res,pnl="STOP",-risk; break
            if ht: res,pnl="TARGET",mult*risk; break
        if pnl is None: k=min(n-1,i+hold); pnl=d*(c[k]-E)

        D = day[i]; S = D
        lv = {}
        lv["pdh"]=pdh.get(D,np.nan); lv["pdl"]=pdl_.get(D,np.nan)
        p = prof_prev.get(D,(np.nan,)*3)
        lv["ppoc"],lv["pvah"],lv["pval"]=p
        lv["onh"]=onh.get(S,np.nan); lv["onl"]=onl.get(S,np.nan)
        lv["asiah"]=ah.get(S,np.nan); lv["asial"]=al.get(S,np.nan)
        lv["ldnh"]=lh.get(S,np.nan);  lv["ldnl"]=ll.get(S,np.nan)
        lv["orh"]=oh_.get(D,np.nan);  lv["orl"]=ol_.get(D,np.nan)
        lv["sma15"]=sma15[i]
        lv["round50"]=round(E/50)*50; lv["round100"]=round(E/100)*100
        leg = fib_leg(h,l,dph,dpl,i,d)
        if leg:
            lo_,hi_ = leg
            for f in FIBS: lv[f"fib{f}"] = hi_ - f*(hi_-lo_)
            depth = (hi_-E)/(hi_-lo_) if hi_>lo_ else np.nan
            if d==-1: depth = (E-lo_)/(hi_-lo_) if hi_>lo_ else np.nan
        else:
            for f in FIBS: lv[f"fib{f}"]=np.nan
            depth=np.nan
        A = a14[i] if np.isfinite(a14[i]) and a14[i]>0 else np.nan
        row = dict(tape=tape, day=str(D.date()), ts=str(b.index[i]), i=i, dir=d,
                   entry=E, risk=risk, res=res, r=(pnl-cost)/risk, held=(k-i)*tf,
                   atr=A, risk_atr=risk/A if A==A else np.nan,
                   wick=(lw[i] if d==1 else uw[i]),
                   wick_atr=(lw[i] if d==1 else uw[i])/A if A==A else np.nan,
                   wick_body=(lw[i] if d==1 else uw[i])/max(body[i],1e-9),
                   bar_rng_atr=rg[i]/A if A==A else np.nan,
                   mins_in=tmin[i]-t0,
                   stretch=(np.nanmax(np.abs(c[i-20:i]-sma[i-20:i]))/A) if A==A else np.nan,
                   slope=(sma[i]-sma[i-10])/A if A==A else np.nan,
                   vol_z=vol[i]/np.nanmean(vol[max(0,i-20):i]),
                   day_rng_atr=(np.nanmax(h[max(0,i-60):i+1])-np.nanmin(l[max(0,i-60):i+1]))/A if A==A else np.nan,
                   fib_depth=depth,
                   vix=float(vix.get(D, np.nan)) if len(vix) else np.nan)
        for nm,val in lv.items():
            row[f"d_{nm}"] = abs(E-val)/A if (val==val and A==A) else np.nan
        rows.append(row)
    return pd.DataFrame(rows)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--tapes", default="2023-26,2020-22,2017-19")
    ap.add_argument("--tf", type=int, default=1); ap.add_argument("--trend", default="SIDE")
    ap.add_argument("--W", type=float, default=1.0); ap.add_argument("--U", type=float, default=0.5)
    ap.add_argument("--buf", type=int, default=2); ap.add_argument("--mult", type=float, default=3.0)
    ap.add_argument("--cost", type=float, default=0.75); ap.add_argument("--minrisk", type=float, default=8.0)
    ap.add_argument("--maxhold", type=int, default=120)
    ap.add_argument("--out", default="data/debug/autopsy.csv")
    a=ap.parse_args()
    out=[]
    for t in a.tapes.split(","):
        d=build(t,a.tf,a.trend,a.W,a.U,a.buf,a.mult,a.cost,a.minrisk,a.maxhold)
        print(f"  {t}: {len(d)} trades", flush=True); out.append(d)
    d=pd.concat(out); d.to_csv(a.out,index=False)
    print(f"\n{len(d)} trades, {len([c for c in d.columns if c.startswith('d_')])} level features -> {a.out}")
