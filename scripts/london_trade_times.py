#!/usr/bin/env python3
"""Emit chart-ready timestamps for the base Scheme-A day-stopped book (London 10-13 UK pullback).
Entry moment = right edge of the setup candle = open of the next M15 candle. Given in UK / ET / UTC
(tz-correct incl DST). Columns: date, entry times, dir, stop_pts, confirm(Y=1.0x/N=0.5x), outcome, R.
The pullback SETUP is the 15-min candle ENDING at the entry time; you fill on the next candle's open."""
from datetime import time as dtime
import numpy as np, pandas as pd
S="/tmp/claude-0/-home-user-AI-trading-agents/69c9097f-44f3-585b-817f-a315126d0dbb/scratchpad"; WT=f"{S}/canon_wt"
TICK,PV,COMM=0.25,20.0,5.0; TG=3.0
print("load...",flush=True)
b=pd.read_parquet("/home/user/gs/data/reference/nq_1m_master.parquet")
b["ts"]=pd.to_datetime(b.ts_event,utc=True); b["uk"]=b.ts.dt.tz_convert("Europe/London"); b=b.sort_values("ts").reset_index(drop=True)
FILES=["footprint_q3_2025","footprint_q4_2025","footprint_feb_mar2026","footprint_apr2026","footprint_may_jul2026"]
cvd_days=set(); dparts=[]
for f in FILES:
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
    em=pd.Timestamp(a["uts"][i+1]); em=(em.tz_localize("UTC") if em.tzinfo is None else em)
    v3=delta3.get(em-pd.Timedelta(minutes=1),np.nan); cov=(d in cvd_days) and not np.isnan(v3); conf=bool((v3>0) if dr>0 else (v3<0)) if cov else False
    rows.append(dict(_ord=(d,str(utt[i])),utc=tu,rk=rk,dir=dr,conf=conf,R=Rr))
T=pd.DataFrame(rows).sort_values("_ord").reset_index(drop=True)
# day-stop (Scheme A takes all; stop after first loss of day)
T["day"]=[o[0] for o in T._ord]; keep=[]
for d,g in T.groupby("day",sort=True):
    stp=False
    for idx,r in g.iterrows():
        if stp: continue
        keep.append(idx)
        if r.R<0: stp=True
K=T.loc[keep].reset_index(drop=True)
uk=K.utc.dt.tz_convert("Europe/London"); et=K.utc.dt.tz_convert("America/New_York")
out=pd.DataFrame({
 "date": uk.dt.strftime("%Y-%m-%d (%a)"),
 "entry_UK": uk.dt.strftime("%H:%M"),
 "entry_ET": et.dt.strftime("%H:%M"),
 "entry_UTC": K.utc.dt.strftime("%Y-%m-%d %H:%M"),
 "dir": np.where(K.dir>0,"LONG","SHORT"),
 "stop_pts": K.rk.round(1),
 "confirm": np.where(K.conf,"Y (1.0x)","N (0.5x)"),
 "outcome": np.where(K.R>0,"WIN","LOSS"),
 "R": K.R.round(2),
})
out.to_csv(f"{S}/london_base_trades.csv",index=False)
print(f"\nbase Scheme-A book: {len(out)} trades ({int((K.R>0).sum())} win / {int((K.R<=0).sum())} loss)\n")
print(out.to_string(index=False))
print(f"\nsaved london_base_trades.csv")
