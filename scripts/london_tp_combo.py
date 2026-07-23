#!/usr/bin/env python3
"""Joint test of the mechanism-justified combo: touch-reclaim trigger (prior bar CLOSES through
50MA, trigger bar closes back), NO vol filter, flatten 07:45 (no NY exposure), tgt 2R & 3R."""
from datetime import time as dtime
import numpy as np, pandas as pd
NY="America/New_York"; TICK,PV,COMM=0.25,20.0,5.0
bars=pd.read_parquet("/home/user/gs/data/reference/nq_1m_master.parquet")
bars["ts"]=pd.to_datetime(bars["ts_event"],utc=True).dt.tz_convert(NY)
bars=bars.sort_values("ts").reset_index(drop=True)
m=bars.set_index("ts").resample("15min",label="right",closed="right").agg(
 open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),volume=("volume","sum")).dropna(subset=["close"])
m["day"]=m.index.strftime("%Y-%m-%d"); m["t"]=m.index.time
for p in (20,50,200): m[f"ma{p}"]=m.close.rolling(p).mean()
m["swing_lo5"]=m.low.rolling(5).min(); m["swing_hi5"]=m.high.rolling(5).max()
M=m.reset_index().rename(columns={"index":"ts"}).dropna(subset=["ma200"]).reset_index(drop=True)
a={c:M[c].values for c in ["open","high","low","close","ma20","ma50","ma200","swing_lo5","swing_hi5"]}
day=M.day.values; t=M.t.values
LON=np.array([dtime(3,0)<=x<dtime(7,45) for x in t])
def run(TG,FLAT):
    rec=[]
    for i in range(1,len(M)):
        if not LON[i]: continue
        up=a["ma20"][i]>a["ma50"][i]>a["ma200"][i] and a["close"][i]>a["ma50"][i] and a["close"][i]>a["ma200"][i]
        dn=a["ma20"][i]<a["ma50"][i]<a["ma200"][i] and a["close"][i]<a["ma50"][i] and a["close"][i]<a["ma200"][i]
        dr=0
        if up and a["close"][i-1]<a["ma50"][i-1] and a["close"][i]>a["ma50"][i]: dr=1
        elif dn and a["close"][i-1]>a["ma50"][i-1] and a["close"][i]<a["ma50"][i]: dr=-1
        if dr==0 or i+1>=len(M) or day[i+1]!=day[i]: continue
        entry=a["open"][i+1]+dr*TICK
        ref=min(a["swing_lo5"][i],a["ma50"][i]) if dr>0 else max(a["swing_hi5"][i],a["ma50"][i])
        risk=abs(entry-ref)+TICK
        if risk<5 or risk>70: continue
        stop=entry-dr*risk; tgt=entry+dr*TG*risk; gross=None; j=i+1
        while j<len(M) and day[j]==day[i]:
            if t[j]>=FLAT: gross=dr*(a["close"][j]-entry); break
            hs=(a["low"][j]<=stop) if dr>0 else (a["high"][j]>=stop)
            ht=(a["high"][j]>=tgt) if dr>0 else (a["low"][j]<=tgt)
            if hs: gross=-risk-TICK; break
            if ht: gross=TG*risk-TICK; break
            j+=1
        if gross is None: gross=dr*(a["close"][min(j,len(M)-1)]-entry)
        net=gross*PV-COMM
        rec.append(dict(day=day[i],net=net,R=net/(risk*PV)))
    R=pd.DataFrame(rec)
    te=R[R.day>"2024-12-31"]
    eq=R.sort_values("day").net.cumsum().values
    dd=float((np.maximum.accumulate(eq)-eq).max()) if len(eq) else 0
    yr={y:R[R.day.str[:4]==y].net.sum() for y in ("2023","2024","2025","2026")}
    v=te.R.values; gp=v[v>0].sum(); gl=-v[v<0].sum()
    print(f"tgt {TG}R flat{FLAT}: ALL n={len(R)} net ${R.net.sum():+,.0f} DD ${dd:,.0f} | "
          f"TEST n={len(te)} E[R] {te.R.mean():+.3f} WR {100*(te.R>0).mean():.0f}% PF {gp/gl if gl>0 else 99:.2f} ${te.net.sum():+,.0f} | "
          f"23 ${yr['2023']:+,.0f} 24 ${yr['2024']:+,.0f} 25 ${yr['2025']:+,.0f} 26 ${yr['2026']:+,.0f}")
print("COMBO: touch-reclaim, NO vol filter, London 03:00-07:45")
for TG in (2.0,3.0):
    for FLAT in (dtime(7,45),dtime(9,25)):
        run(TG,FLAT)
