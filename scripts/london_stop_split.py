#!/usr/bin/env python3
"""Stop distance (risk_pts) of winners vs losers, London 10-13 day-stop book."""
from datetime import time as dtime
import numpy as np, pandas as pd
TICK,PV,COMM=0.25,20.0,5.0
b=pd.read_parquet("/home/user/gs/data/reference/nq_1m_master.parquet")
b["ts"]=pd.to_datetime(b.ts_event,utc=True); b["uk"]=b.ts.dt.tz_convert("Europe/London"); b=b.sort_values("ts").reset_index(drop=True)
m=b.set_index("ts").resample("15min",label="right",closed="right").agg(open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),volume=("volume","sum")).dropna(subset=["close"])
_uk=m.index.tz_convert("Europe/London"); m["ukt"]=_uk.time; m["ukday"]=_uk.strftime("%Y-%m-%d")
for p in(20,50,200): m[f"ma{p}"]=m.close.rolling(p).mean()
m["v10"]=m.volume.rolling(10).mean().shift(1); m["slo"]=m.low.rolling(5).min(); m["shi"]=m.high.rolling(5).max()
M=m.reset_index(names="uts").dropna(subset=["ma200"]); M=M[(M.ukday>="2025-07-01")&(M.ukday<="2026-07-15")].reset_index(drop=True)
a={c:M[c].values for c in["uts","open","high","low","close","volume","ma20","ma50","ma200","v10","slo","shi"]}; ud=M.ukday.values; utt=M.ukt.values
rows=[]
for i in range(1,len(M)-1):
    d=ud[i]
    if d in("2025-11-28","2026-04-03") or ud[i+1]!=d or not(dtime(10,0)<=utt[i]<dtime(13,0)): continue
    up=a["ma20"][i]>a["ma50"][i]>a["ma200"][i] and a["close"][i]>a["ma50"][i] and a["close"][i]>a["ma200"][i]
    dn=a["ma20"][i]<a["ma50"][i]<a["ma200"][i] and a["close"][i]<a["ma50"][i] and a["close"][i]<a["ma200"][i]
    dr=1 if(up and a["low"][i]<=a["ma50"][i]) else(-1 if(dn and a["high"][i]>=a["ma50"][i]) else 0)
    if dr==0 or not(a["v10"][i]>0 and a["volume"][i]<a["v10"][i]): continue
    en=a["open"][i+1]+dr*TICK; rf=min(a["slo"][i],a["ma50"][i]) if dr>0 else max(a["shi"][i],a["ma50"][i]); rk=abs(en-rf)+TICK
    if rk<5 or rk>70: continue
    st=en-dr*rk; tg=en+dr*3*rk; gg=None; j=i+1; reason=None
    while j<len(M) and ud[j]==d:
        if utt[j]>=dtime(16,30): gg=dr*(a["close"][j]-en); reason="flat"; break
        hs=(a["low"][j]<=st) if dr>0 else (a["high"][j]>=st); ht=(a["high"][j]>=tg) if dr>0 else (a["low"][j]<=tg)
        if hs: gg=-rk-TICK; reason="stop"; break
        if ht: gg=3*rk-TICK; reason="target"; break
        j+=1
    if gg is None: gg=dr*(a["close"][min(j,len(M)-1)]-en); reason="eod"
    rows.append(dict(day=d,ent=str(utt[i]),net=gg*PV-COMM,win=gg>0,risk_pts=rk,reason=reason))
A=pd.DataFrame(rows).sort_values(["day","ent"]).reset_index(drop=True)
keep=[]
for d,g in A.groupby("day"):
    stp=False
    for _,r in g.iterrows():
        if stp: continue
        keep.append(r.name)
        if r.net<0: stp=True
S=A.loc[keep]
def q(x): return f"med {np.median(x):.1f} | mean {np.mean(x):.1f} | q25-q75 {np.percentile(x,25):.0f}-{np.percentile(x,75):.0f} | range {x.min():.0f}-{x.max():.0f}"
W=S[S.win]; L=S[~S.win]
print(f"day-stop book: {len(S)} trades ({len(W)} win / {len(L)} loss)\n")
print("STOP DISTANCE (points):")
print(f"  WINNERS (n={len(W)}): {q(W.risk_pts.values)}")
print(f"  LOSERS  (n={len(L)}): {q(L.risk_pts.values)}")
print(f"\n  in $ per 1 NQ (x$20/pt): winners med ${np.median(W.risk_pts)*20:.0f} | losers med ${np.median(L.risk_pts)*20:.0f}")
print("\nEXIT REASON of the losers:")
print(L.reason.value_counts().to_string())
print("\nEXIT REASON of winners:")
print(W.reason.value_counts().to_string())
# do bigger stops win more?
print("\nWIN RATE by stop-size bucket:")
for lo,hi in [(0,20),(20,35),(35,50),(50,70)]:
    sub=S[(S.risk_pts>=lo)&(S.risk_pts<hi)]
    if len(sub): print(f"  {lo}-{hi}pt: n={len(sub):2d} WR {100*sub.win.mean():.0f}% net ${sub.net.sum():+,.0f}")