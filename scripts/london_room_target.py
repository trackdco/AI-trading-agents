#!/usr/bin/env python3
"""ROOM-conditional TARGET (magnet at the overnight extreme) - the last live idea.
Confirmed losers cluster where ROOM<2.5 (the 3R target sits BEYOND the overnight high/low = a
liquidity wall). Fix attempt: when a wall sits within reach ahead (0<room<CAP), take profit AT the
overnight extreme instead of holding for 3R. Overnight H/L are fixed by 10:00 UK -> entry-observable,
no lookahead. This is a proxy for heatmap magnet-targeting (the level I CAN see without depth data).
Sweep CAP; also a 'wall-minus-buffer' variant (exit just ahead of the level). Full Scheme-A book,
funded fixed-$ lens: must beat baseline on net $ AND maxDD. q4 CVD. Honest N/multiplicity caveat."""
from datetime import time as dtime
import numpy as np, pandas as pd
import os as _os
S=_os.environ.get("LONDON_SCRATCH", _os.path.expanduser("~/london_out"))
WT=_os.environ.get("LONDON_WT", f"{S}/canon_wt")
_os.makedirs(S, exist_ok=True)
TICK,PV,COMM=0.25,20.0,5.0; TG=3.0; BASE=300.0
print("load...",flush=True)
b=pd.read_parquet(f"{WT}/data/reference/nq_1m_master.parquet")
b["ts"]=pd.to_datetime(b.ts_event,utc=True); b["uk"]=b.ts.dt.tz_convert("Europe/London"); b=b.sort_values("ts").reset_index(drop=True); b["ukt"]=b.uk.dt.time
FILES=["footprint_q3_2025","footprint_q4_2025","footprint_feb_mar2026","footprint_apr2026","footprint_may_jul2026"]
cvd_days=set(); dparts=[]
MISSING_CVD=[f for f in FILES if not _os.path.exists(f"{WT}/data/reference/cvd/{f}.parquet")]
if MISSING_CVD: print("WARN missing CVD (those days -> unconfirmed):", MISSING_CVD, flush=True)
for f in [f for f in FILES if f not in MISSING_CVD]:
    d=pd.read_parquet(f"{WT}/data/reference/cvd/{f}.parquet",columns=["ts_minute","side","volume"])
    cvd_days|=set(pd.to_datetime(d.ts_minute,utc=True).dt.tz_convert("Europe/London").dt.strftime("%Y-%m-%d").unique())
    d["s"]=np.where(d.side=="B",d.volume,-d.volume); dparts.append(d.groupby("ts_minute")["s"].sum()); del d
delta=pd.concat(dparts).groupby(level=0).sum().sort_index(); delta.index=pd.to_datetime(delta.index,utc=True); delta3=delta.rolling(3).sum(); del dparts
onov=b[(b.ukt>=dtime(22,0))|(b.ukt<dtime(8,0))].copy(); onov["sess"]=(onov.uk+pd.Timedelta(hours=2)).dt.strftime("%Y-%m-%d")
ONH=onov.groupby("sess").high.max().to_dict(); ONL=onov.groupby("sess").low.min().to_dict()
m=b.set_index("ts").resample("15min",label="right",closed="right").agg(open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),volume=("volume","sum")).dropna(subset=["close"])
_uk=m.index.tz_convert("Europe/London"); m["ukt"]=_uk.time; m["ukday"]=_uk.strftime("%Y-%m-%d")
for p in(20,50,200): m[f"ma{p}"]=m.close.rolling(p).mean()
m["v10"]=m.volume.rolling(10).mean().shift(1); m["slo"]=m.low.rolling(5).min(); m["shi"]=m.high.rolling(5).max()
M=m.reset_index(names="uts").dropna(subset=["ma200"]); M=M[(M.ukday>="2025-07-01")&(M.ukday<="2026-07-15")].reset_index(drop=True)
a={c:M[c].values for c in["uts","open","high","low","close","volume","ma20","ma50","ma200","v10","slo","shi"]}; ud=M.ukday.values; utt=M.ukt.values
N=len(M)
def resolve(i,dr,en,rk,onh,onl,cap,buf):
    """3R target, but if 0<room<cap take profit at the overnight extreme (buf: fraction of the way, 1.0=at wall)."""
    st=en-dr*rk; tgt=en+dr*TG*rk
    wall=onh if dr>0 else onl; room=((onh-en) if dr>0 else (en-onl))/rk if (onh==onh and onl==onl) else np.nan
    if (room==room) and (0<room<cap):
        tgt=en+dr*(room*buf)*rk                      # magnet target at (buf * wall distance)
    j=i+1
    while j<N and ud[j]==ud[i]:
        if utt[j]>=dtime(16,30): return dr*(a["close"][j]-en)
        if (a["low"][j]<=st) if dr>0 else (a["high"][j]>=st): return -rk-TICK
        if (a["high"][j]>=tgt) if dr>0 else (a["low"][j]<=tgt): return dr*(tgt-en)-TICK
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
    em=pd.Timestamp(a["uts"][i+1]); em=em.tz_localize("UTC") if em.tzinfo is None else em.tz_convert("UTC")
    v3=delta3.get(em-pd.Timedelta(minutes=1),np.nan); cov=(d in cvd_days) and not np.isnan(v3); conf=bool((v3>0) if dr>0 else (v3<0)) if cov else False
    onh=ONH.get(d,np.nan); onl=ONL.get(d,np.nan); room=((onh-en) if dr>0 else (en-onl))/rk if (onh==onh) else np.nan
    rows.append(dict(i=i,day=d,ent=str(utt[i]),dir=dr,rk=rk,en=en,onh=onh,onl=onl,conf=conf,room=room))
T=pd.DataFrame(rows).sort_values(["day","ent"]).reset_index(drop=True)
def bookR(cap,buf):
    return np.array([(resolve(r.i,r.dir,r.en,r.rk,r.onh,r.onl,cap,buf)*PV-COMM)/(r.rk*PV) for r in T.itertuples()])
def funded(Rv):
    df=T.assign(R=Rv); keep=[]
    for d,g in df.groupby("day",sort=True):
        stp=False
        for idx,r in g.iterrows():
            if stp: continue
            keep.append(idx)
            if r.R<0: stp=True
    k=df.loc[keep]; sz=np.where(k.conf,1.0,0.5); doll=k.R.values*sz*BASE; e=np.cumsum(doll)
    dd=float((np.maximum.accumulate(e)-e).max()) if len(e) else 0
    rr=k.R.values*sz; er=np.cumsum(rr); rdd=float((np.maximum.accumulate(er)-er).max()) if len(er) else 0
    return doll.sum(),dd,rdd,len(k),int((k.R.values>0).sum())
print("="*112); print(f"ROOM-CONDITIONAL TARGET  |  {len(T)} triggers  |  walls-in-reach(0<room<3): {int(((T.room>0)&(T.room<3)).sum())}"); print("="*112)
Rbase=bookR(0.0,1.0); nb,db,rb,kb,wb=funded(Rbase)
print(f"\n  {'BASELINE flat 3R':34s} net ${nb:+8,.0f}  maxDD ${db:6,.0f}  worstRdd {rb:.2f}R  n={kb} WR {100*wb/kb:.0f}%")
print("\n-- sweep target-cap (take profit AT overnight extreme when 0<room<CAP) --")
best=None
for cap in (1.5,2.0,2.5,3.0):
    Rv=bookR(cap,1.0); n,dd,rd,kk,ww=funded(Rv)
    conv=int(((Rbase<0)&(Rv>0)).sum()); capd=int(((Rbase>2.5)&(Rv<Rbase-0.01)).sum())
    print(f"  cap room<{cap:.1f} (exit AT wall)  net ${n:+8,.0f} ({n-nb:+7,.0f})  maxDD ${dd:6,.0f}  worstRdd {rd:.2f}R  WR {100*ww/kk:.0f}%   converted {conv} losers, capped {capd} winners")
    if best is None or n>best[0]: best=(n,dd,cap,1.0,Rv)
print("\n-- best cap, but exit 15% AHEAD of the wall (buf=0.85) --")
cap=best[2]; Rv=bookR(cap,0.85); n,dd,rd,kk,ww=funded(Rv)
conv=int(((Rbase<0)&(Rv>0)).sum()); capd=int(((Rbase>2.5)&(Rv<Rbase-0.01)).sum())
print(f"  cap room<{cap:.1f} (exit 0.85*wall) net ${n:+8,.0f} ({n-nb:+7,.0f})  maxDD ${dd:6,.0f}  worstRdd {rd:.2f}R  WR {100*ww/kk:.0f}%   converted {conv}, capped {capd}")
if n>best[0]: best=(n,dd,cap,0.85,Rv)
# verdict + per-year on best
bn,bd,bcap,bbuf,bRv=best
print("\n"+"="*112)
print(f"BEST: cap room<{bcap:.1f}, buf {bbuf}  -> net ${bn:+,.0f} (vs base ${nb:+,.0f}, d${bn-nb:+,.0f})  maxDD ${bd:,.0f} (vs ${db:,.0f})")
better = bn>nb and bd<=db
print(f"  -> {'IMPROVES net AND drawdown' if better else ('more net but check DD' if bn>nb else 'does NOT beat flat 3R')}")
kd=T.assign(R=bRv)
for y in("2025","2026"):
    s=kd[kd.day.str[:4]==y]; sb=T.assign(R=Rbase); sb=sb[sb.day.str[:4]==y]
    print(f"    {y}: best sumR {s.R.sum():+.1f}  vs baseline sumR {sb.R.sum():+.1f}")
for nm,lo,hi in[("25Q3","2025-07","2025-09"),("25Q4","2025-10","2025-12"),("26Q1","2026-01","2026-03"),("26Q2+","2026-04","2026-07")]:
    s=kd[(kd.day.str[:7]>=lo)&(kd.day.str[:7]<=hi)]; sb=T.assign(R=Rbase); sb=sb[(sb.day.str[:7]>=lo)&(sb.day.str[:7]<=hi)]
    print(f"    {nm}: best sumR {s.R.sum():+5.1f}  base {sb.R.sum():+5.1f}")
print("\n  CAVEAT: N~55, thresholds tuned in-sample on a book sliced many times, no 2023-24 London holdout")
print("  -> even if it wins here it is a HOLDOUT CANDIDATE, not a ship.")
T.assign(Rbase=Rbase,Rbest=bRv).to_csv(f"{S}/london_room_target_book.csv",index=False); print("saved london_room_target_book.csv")
