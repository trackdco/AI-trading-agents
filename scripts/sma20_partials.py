"""Partial at 1R + runner, versus flat targets. Exits scanned from the bar AFTER entry."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,"scripts")
from sma20_pinbar import load, resample, pivots, trend_flags, SESSIONS, TICK

def run(tape, tf, trend, W, U, B, cost, minrisk, maxhold, scheme):
    b=resample(load(tape),tf)
    o,h,l,c=(b[x].values.astype(float) for x in ("open","high","low","close"))
    sma=pd.Series(c).rolling(20).mean().values
    ph,pl=pivots(h,l); lo_t,sh_t=trend_flags(c,sma,h,l,ph,pl,trend)
    tmin=(b.index.hour*60+b.index.minute).values; t0,t1=SESSIONS["NY"]
    inwin=(tmin>=t0)&(tmin<t1)
    body=np.abs(c-o); rg=h-l; lw=np.minimum(o,c)-l; uw=h-np.maximum(o,c)
    with np.errstate(invalid="ignore"):
        lg=inwin&lo_t&(l<sma)&(c>sma)&(c>o)&(lw>=W*body)&(uw<=U*rg)
        sh=inwin&sh_t&(h>sma)&(c<sma)&(c<o)&(uw>=W*body)&(lw<=U*rg)
    lg=np.nan_to_num(lg,nan=False).astype(bool); sh=np.nan_to_num(sh,nan=False).astype(bool)
    hold=max(1,maxhold//tf); n=len(c); rows=[]; busy=-1
    for i in np.where(lg|sh)[0]:
        if i<=25 or i>=n-2 or i<busy: continue
        d=1 if lg[i] else -1; E=c[i]
        stop=(l[i]-B*TICK) if d==1 else (h[i]+B*TICK)
        risk=(E-stop) if d==1 else (stop-E)
        if risk<=0 or risk<minrisk: continue
        busy=i+1
        half, runner_tgt, be_move = scheme
        booked=0.0; open_frac=1.0; cur_stop=stop; took_partial=False; res="OPEN"
        for k in range(i+1, min(n,i+1+hold)):
            hi=(h[k]-E)/risk if d==1 else (E-l[k])/risk       # favourable excursion in R
            lo=(l[k]-E)/risk if d==1 else (E-h[k])/risk       # adverse excursion in R
            stop_r=(cur_stop-E)/risk if d==1 else (E-cur_stop)/risk
            if lo<=stop_r:                                     # stopped (same bar as target = stop)
                booked += open_frac*stop_r; open_frac=0.0
                res="STOP" if not took_partial else "PARTIAL+STOP"; break
            if (not took_partial) and hi>=1.0 and half>0:
                booked += half*1.0; open_frac-=half; took_partial=True
                if be_move: cur_stop=E
            if hi>=runner_tgt and open_frac>0:
                booked += open_frac*runner_tgt; open_frac=0.0
                res="TARGET" if not took_partial else "PARTIAL+TARGET"; break
        if open_frac>0:
            k=min(n-1,i+hold); booked += open_frac*(d*(c[k]-E)/risk)
            res="FLAT" if not took_partial else "PARTIAL+FLAT"
        rows.append(dict(tape=tape,day=str(b.index[i].date()),ts=str(b.index[i]),
                         dir=d,risk=risk,res=res,r=booked-cost/risk,
                         hit1R=took_partial or res=="TARGET"))
    return pd.DataFrame(rows)

SCHEMES={
 "flat 1R":        (1.0, 1.0, False),
 "flat 3R":        (0.0, 3.0, False),
 "half@1R -> 3R":  (0.5, 3.0, False),
 "half@1R BE ->3R":(0.5, 3.0, True),
 "half@1R -> 5R":  (0.5, 5.0, False),
 "third@1R ->3R":  (0.334,3.0, False),
}
out=[]
for tape in ["2023-26","2020-22","2017-19"]:
    for nm,sc in SCHEMES.items():
        t=run(tape,1,"SIDE",1.0,0.5,2,0.75,8.0,120,sc)
        se=t.r.std(ddof=1)/np.sqrt(len(t))
        out.append(dict(tape=tape,scheme=nm,n=len(t),R=t.r.mean(),t=t.r.mean()/se,
                        hit1R=t.hit1R.mean(), pos=(t.r>0).mean()))
d=pd.DataFrame(out); d.to_csv("data/debug/partial_schemes.csv",index=False)
pd.set_option("display.width",200)
print("PARTIAL SCHEMES — 1-min SIDE, all three tapes, cost 0.75, min stop 8pt\n")
print(d.pivot_table(index="scheme",columns="tape",values="R").reindex(SCHEMES).to_string(float_format=lambda x:f"{x:+.4f}"))
print("\nshare of trades that finished POSITIVE (the 'win rate' you actually feel):")
print(d.pivot_table(index="scheme",columns="tape",values="pos").reindex(SCHEMES).to_string(float_format=lambda x:f"{x:.1%}"))
print("\nshare that reached 1R at all:")
print(d.pivot_table(index="scheme",columns="tape",values="hit1R").reindex(SCHEMES).to_string(float_format=lambda x:f"{x:.1%}"))
