#!/usr/bin/env python3
"""Emit dashboard data (stats, equity curve, quarters, trades) for the base Scheme-A London book -> JSON."""
from datetime import time as dtime
import json, numpy as np, pandas as pd
import os as _os
S=_os.environ.get("LONDON_SCRATCH", _os.path.expanduser("~/london_out"))
WT=_os.environ.get("LONDON_WT", f"{S}/canon_wt")
_os.makedirs(S, exist_ok=True)
TICK,PV,COMM=0.25,20.0,5.0; TG=3.0; RISKD=300.0
b=pd.read_parquet(f"{WT}/data/reference/nq_1m_master.parquet")
b["ts"]=pd.to_datetime(b.ts_event,utc=True); b["uk"]=b.ts.dt.tz_convert("Europe/London"); b=b.sort_values("ts").reset_index(drop=True)
FILES=["footprint_q3_2025","footprint_q4_2025","footprint_feb_mar2026","footprint_apr2026","footprint_may_jul2026"]
cvd_days=set(); dparts=[]
MISSING_CVD=[f for f in FILES if not _os.path.exists(f"{WT}/data/reference/cvd/{f}.parquet")]
if MISSING_CVD: print("WARN missing CVD (those days -> unconfirmed):", MISSING_CVD, flush=True)
for f in [f for f in FILES if f not in MISSING_CVD]:
    d=pd.read_parquet(f"{WT}/data/reference/cvd/{f}.parquet",columns=["ts_minute","side","volume"])
    cvd_days|=set(pd.to_datetime(d.ts_minute,utc=True).dt.tz_convert("Europe/London").dt.strftime("%Y-%m-%d").unique())
    d["s"]=np.where(d.side=="B",d.volume,-d.volume); dparts.append(d.groupby("ts_minute")["s"].sum()); del d
delta=pd.concat(dparts).groupby(level=0).sum().sort_index(); delta.index=pd.to_datetime(delta.index,utc=True); delta3=delta.rolling(3).sum(); del dparts
m=b.set_index("ts").resample("15min",label="right",closed="right").agg(open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),volume=("volume","sum")).dropna(subset=["close"])
_uk=m.index.tz_convert("Europe/London"); m["ukt"]=_uk.time; m["ukday"]=_uk.strftime("%Y-%m-%d")
for p in(20,50,200): m[f"ma{p}"]=m.close.rolling(p).mean()
m["v10"]=m.volume.rolling(10).mean().shift(1); m["slo"]=m.low.rolling(5).min(); m["shi"]=m.high.rolling(5).max()
M=m.reset_index(names="uts").dropna(subset=["ma200"]); M=M[(M.ukday>="2025-07-01")&(M.ukday<="2026-07-15")].reset_index(drop=True)
a={c:M[c].values for c in["uts","open","high","low","close","volume","ma20","ma50","ma200","v10","slo","shi"]}; ud=M.ukday.values; utt=M.ukt.values
N=len(M)
def walk(i,dr,en,rk):
    st=en-dr*rk; tg=en+dr*TG*rk; j=i+1
    while j<N and ud[j]==ud[i]:
        if utt[j]>=dtime(16,30): return dr*(a["close"][j]-en)
        if (a["low"][j]<=st) if dr>0 else (a["high"][j]>=st): return -rk-TICK
        if (a["high"][j]>=tg) if dr>0 else (a["low"][j]<=tg): return TG*rk-TICK
        j+=1
    return dr*(a["close"][min(j,N-1)]-en)
rows=[]
for i in range(1,N-1):
    d=ud[i]
    if d in("2025-11-28","2026-04-03") or ud[i+1]!=d or not(dtime(10,0)<=utt[i]<dtime(13,0)): continue
    up=a["ma20"][i]>a["ma50"][i]>a["ma200"][i] and a["close"][i]>a["ma50"][i] and a["close"][i]>a["ma200"][i]
    dn=a["ma20"][i]<a["ma50"][i]<a["ma200"][i] and a["close"][i]<a["ma50"][i] and a["close"][i]<a["ma200"][i]
    dr=1 if(up and a["low"][i]<=a["ma50"][i]) else(-1 if(dn and a["high"][i]>=a["ma50"][i]) else 0)
    if dr==0 or not(a["v10"][i]>0 and a["volume"][i]<a["v10"][i]): continue
    en=a["open"][i+1]+dr*TICK; rf=min(a["slo"][i],a["ma50"][i]) if dr>0 else max(a["shi"][i],a["ma50"][i]); rk=abs(en-rf)+TICK
    if rk<5 or rk>70: continue
    g=walk(i,dr,en,rk); Rr=(g*PV-COMM)/(rk*PV)
    tu=pd.Timestamp(a["uts"][i]).tz_localize("UTC")
    em=pd.Timestamp(a["uts"][i+1]).tz_localize("UTC"); v3=delta3.get(em-pd.Timedelta(minutes=1),np.nan)
    cov=(d in cvd_days) and not np.isnan(v3); conf=bool((v3>0) if dr>0 else (v3<0)) if cov else False
    rows.append(dict(_o=(d,str(utt[i])),utc=tu,rk=rk,dir=dr,conf=conf,R=Rr))
T=pd.DataFrame(rows).sort_values("_o").reset_index(drop=True); T["day"]=[o[0] for o in T._o]
keep=[]
for d,g in T.groupby("day",sort=True):
    stp=False
    for idx,r in g.iterrows():
        if stp: continue
        keep.append(idx)
        if r.R<0: stp=True
K=T.loc[keep].reset_index(drop=True)
uk=K.utc.dt.tz_convert("Europe/London"); et=K.utc.dt.tz_convert("America/New_York")
sz=np.where(K.conf,1.0,0.5); doll=K.R.values*sz*RISKD; cum=np.cumsum(doll); peak=np.maximum.accumulate(cum); ddser=peak-cum
rr=K.R.values*sz; rcum=np.cumsum(rr); worstRdd=float((np.maximum.accumulate(rcum)-rcum).max())
flat=K.R.values*RISKD; flatcum=np.cumsum(flat); flatdd=float((np.maximum.accumulate(flatcum)-flatcum).max())
mon=uk.dt.strftime("%Y-%m").values; quarters=[]
for nm,lo,hi in[("25 Q3","2025-07","2025-09"),("25 Q4","2025-10","2025-12"),("26 Q1","2026-01","2026-03"),("26 Q2+","2026-04","2026-07")]:
    msk=(mon>=lo)&(mon<=hi); quarters.append(dict(name=nm,net=round(float(doll[msk].sum())),n=int(msk.sum())))
# confirm-only book (own day-stop)
CO=T[T.conf].copy(); keep2=[]
for d,g in CO.groupby("day",sort=True):
    stp=False
    for idx,r in g.iterrows():
        if stp: continue
        keep2.append(idx)
        if r.R<0: stp=True
CK=CO.loc[keep2]; co_doll=CK.R.values*RISKD; co_cum=np.cumsum(co_doll); co_dd=float((np.maximum.accumulate(co_cum)-co_cum).max())
n=len(K); wins=int((K.R>0).sum())
trades=[]
for idx in range(n):
    r=K.iloc[idx]
    trades.append(dict(date=uk.dt.strftime("%Y-%m-%d").iloc[idx],dow=uk.dt.strftime("%a").iloc[idx],
        uk=uk.dt.strftime("%H:%M").iloc[idx],et=et.dt.strftime("%H:%M").iloc[idx],
        dir=("LONG" if r.dir>0 else "SHORT"),stop=round(float(r.rk),1),conf=bool(r.conf),
        outcome=("WIN" if r.R>0 else "LOSS"),R=round(float(r.R),2),cum=round(float(cum[idx]))))
data=dict(
 stats=dict(net=round(float(doll.sum())),maxdd=round(float(ddser.max())),wr=round(100*wins/n),n=n,wins=wins,losses=n-wins,
   worstRdd=round(worstRdd,2),avgWin=round(float(K.R[K.R>0].mean()),2),avgLoss=round(float(K.R[K.R<=0].mean()),2),
   qGreen=sum(1 for q in quarters if q['net']>0),qTotal=len(quarters),confN=int(K.conf.sum()),
   spanStart=uk.dt.strftime("%b %Y").iloc[0],spanEnd=uk.dt.strftime("%b %Y").iloc[-1]),
 equity=[dict(i=i+1,cum=round(float(cum[i])),dd=round(float(ddser[i]))) for i in range(n)],
 quarters=quarters,
 sizing=[dict(name="Flat 1.0x",net=round(float(flat.sum())),dd=round(flatdd),note="max profit / higher DD"),
         dict(name="Scheme A",net=round(float(doll.sum())),dd=round(float(ddser.max())),note="the book"),
         dict(name="Confirm-only",net=round(float(co_doll.sum())),dd=round(co_dd),note="cleaner, fewer trades")],
 interventions=[dict(name="Baseline (leave it)",net=round(float(doll.sum())),base=True),
   dict(name="Stop mgmt (trail/BE)",net=16698,base=False),
   dict(name="Entry trim",net=16452,base=False),
   dict(name="ROOM target",net=13481,base=False),
   dict(name="Tighter (wick) stop",net=10147,base=False)],
 trades=trades)
open(f"{S}/london_dash_data.json","w").write(json.dumps(data,separators=(",",":")))
print(json.dumps(data["stats"],indent=1)); print("sizing",data["sizing"]); print("quarters",data["quarters"]); print("saved json, trades",len(trades))
