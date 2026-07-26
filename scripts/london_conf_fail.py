#!/usr/bin/env python3
"""Where do the CONFIRMED (67%-WR) trades fail? Profile the confirmed losers across entry-observable
dims: round-trip vs straight-to-stop, time-of-day, stop size, direction, month, and Angus's canon
checks ROOM (2.5-9.6R to overnight extreme) + ASIA (dir*cvd_ASIA>=-748). List each loser.
HARD CAVEAT: ~12 confirmed losers, and this book has been sliced many ways -> any 'pattern' is almost
certainly noise/overfit. Descriptive only. q4 CVD. No lookahead."""
from datetime import time as dtime
import numpy as np, pandas as pd
import os as _os
S=_os.environ.get("LONDON_SCRATCH", _os.path.expanduser("~/london_out"))
WT=_os.environ.get("LONDON_WT", f"{S}/canon_wt")
_os.makedirs(S, exist_ok=True)
TICK,PV,COMM=0.25,20.0,5.0; TG=3.0
print("load...",flush=True)
b=pd.read_parquet(f"{WT}/data/reference/nq_1m_master.parquet")
b["ts"]=pd.to_datetime(b.ts_event,utc=True); b["uk"]=b.ts.dt.tz_convert("Europe/London"); b=b.sort_values("ts").reset_index(drop=True); b["ukt"]=b.uk.dt.time
FILES=["footprint_q3_2025","footprint_q4_2025","footprint_feb_mar2026","footprint_apr2026","footprint_may_jul2026"]
cvd_days=set(); dparts=[]; cvd_ASIA={}
MISSING_CVD=[f for f in FILES if not _os.path.exists(f"{WT}/data/reference/cvd/{f}.parquet")]
if MISSING_CVD: print("WARN missing CVD (those days -> unconfirmed):", MISSING_CVD, flush=True)
for f in [f for f in FILES if f not in MISSING_CVD]:
    d=pd.read_parquet(f"{WT}/data/reference/cvd/{f}.parquet",columns=["ts_minute","side","volume"])
    uk=pd.to_datetime(d.ts_minute,utc=True).dt.tz_convert("Europe/London"); dd_=uk.dt.strftime("%Y-%m-%d")
    cvd_days|=set(dd_.unique()); d["s"]=np.where(d.side=="B",d.volume,-d.volume)
    for k,v in d[uk.dt.time<dtime(8,0)].assign(dk=dd_).groupby("dk")["s"].sum().items(): cvd_ASIA[k]=cvd_ASIA.get(k,0)+float(v)
    dparts.append(d.groupby("ts_minute")["s"].sum()); del d
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
def walk(i,dr,en,rk):
    st=en-dr*rk; tg=en+dr*TG*rk; j=i+1; mfe=0.0
    while j<N and ud[j]==ud[i]:
        fav=(a["high"][j]-en) if dr>0 else (en-a["low"][j])
        if fav>mfe: mfe=fav
        if utt[j]>=dtime(16,30): return dr*(a["close"][j]-en),mfe
        if (a["low"][j]<=st) if dr>0 else (a["high"][j]>=st): return -rk-TICK,mfe
        if (a["high"][j]>=tg) if dr>0 else (a["low"][j]<=tg): return TG*rk-TICK,mfe
        j+=1
    return dr*(a["close"][min(j,N-1)]-en),mfe
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
    g,mfe=walk(i,dr,en,rk); Rr=(g*PV-COMM)/(rk*PV)
    em=pd.Timestamp(a["uts"][i+1]); em=em.tz_localize("UTC") if em.tzinfo is None else em.tz_convert("UTC")
    v3=delta3.get(em-pd.Timedelta(minutes=1),np.nan); cov=(d in cvd_days) and not np.isnan(v3); conf=bool((v3>0) if dr>0 else (v3<0)) if cov else False
    onh=ONH.get(d,np.nan); onl=ONL.get(d,np.nan); room=((onh-en) if dr>0 else (en-onl))/rk
    ca=cvd_ASIA.get(d,np.nan); asia_ok=bool(np.isnan(ca) or (dr*ca>=-748))
    rows.append(dict(day=d,ent=str(utt[i])[:5],dir=dr,rk=round(rk,1),R=round(Rr,2),win=Rr>0,conf=conf,
                     rt=(mfe/rk)>=0.5, room=round(room,1), room_ok=bool(2.5<=room<=9.6), asia_ok=asia_ok,
                     cvdmag=round(dr*v3) if cov else np.nan, mon=d[:7]))
T=pd.DataFrame(rows); C=T[T.conf].reset_index(drop=True); L=C[~C.win]; Wc=C[C.win]
print("="*104); print(f"CONFIRMED book: {len(C)} trades, {int(C.win.sum())} win / {len(L)} loss (WR {100*C.win.mean():.0f}%)"); print("="*104)
print("\n-- THE CONFIRMED LOSERS (each one) --")
print("  day         time  dir  stop    R   round-trip?  room  room_ok  asia_ok  cvdmag")
for r in L.sort_values("day").itertuples():
    print(f"  {r.day}  {r.ent}  {'L' if r.dir>0 else 'S':>2}  {r.rk:5.1f}  {r.R:+5.2f}   "
          f"{'ROUND-TRIP' if r.rt else 'straight  '}   {r.room:5.1f}   {str(r.room_ok):5s}   {str(r.asia_ok):5s}   {r.cvdmag:+.0f}")
def split(dim,label,fn):
    print(f"\n-- {label} (losers vs winners, confirmed) --")
    for name,mask_fn in fn:
        lo=int(mask_fn(L).sum()); wi=int(mask_fn(Wc).sum()); tot=lo+wi
        print(f"   {name:22s} losers {lo:2d} / winners {wi:2d}   ({'loss-rate '+str(round(100*lo/tot))+'%' if tot else 'n=0'})")
split("rt","round-trip vs straight-to-stop",[("round-trip (went +0.5R)",lambda x:x.rt),("straight-to-stop",lambda x:~x.rt)])
split("t","time of day",[("10:00-11:00",lambda x:x.ent<'11:00'),("11:00-12:00",lambda x:(x.ent>='11:00')&(x.ent<'12:00')),("12:00-13:00",lambda x:x.ent>='12:00')])
split("rk","stop size",[("tight <25pt",lambda x:x.rk<25),("mid 25-45pt",lambda x:(x.rk>=25)&(x.rk<45)),("wide >=45pt",lambda x:x.rk>=45)])
split("dir","direction",[("long",lambda x:x.dir>0),("short",lambda x:x.dir<0)])
split("room","Angus ROOM band (2.5-9.6R)",[("IN band (room_ok)",lambda x:x.room_ok),("OUT of band",lambda x:~x.room_ok)])
split("asia","Angus ASIA check",[("asia_ok",lambda x:x.asia_ok),("fighting Asia",lambda x:~x.asia_ok)])
# would ROOM+ASIA filter help the confirmed book? (cross-check with his canon)
for lab,f in [("ROOM in-band only",C.room_ok),("ASIA ok only",C.asia_ok),("ROOM in-band AND ASIA ok",C.room_ok&C.asia_ok)]:
    s=C[f]; drop=C[~f]
    print(f"\n   filter [{lab}]: keeps {len(s)} (WR {100*s.win.mean():.0f}%, sumR {s.R.sum():+.1f})  |  drops {len(drop)} (WR {100*drop.win.mean() if len(drop) else 0:.0f}%, sumR {drop.R.sum():+.1f})")
print("\n  CAVEAT: ~12 confirmed losers, book sliced many ways -> treat every split as NOISE until a 2023-24 holdout says otherwise.")
C.to_csv(f"{S}/london_conf_fail_book.csv",index=False); print("saved london_conf_fail_book.csv")
