#!/usr/bin/env python3
"""London 10:00-13:00 UK pullback book, RE-RUN with footprint_q4_2025 loaded (Oct-Dec 2025 now
has real CVD). Day-stop + CVD-sizing V1. Compares vs the pre-q4 numbers. Net of costs, no lookahead."""
from datetime import time as dtime
import glob, numpy as np, pandas as pd
import os as _os
S=_os.environ.get("LONDON_SCRATCH", _os.path.expanduser("~/london_out"))
WT=_os.environ.get("LONDON_WT", f"{S}/canon_wt")
_os.makedirs(S, exist_ok=True)
TICK,PV,COMM=0.25,20.0,5.0
print("load...",flush=True)
b=pd.read_parquet(f"{WT}/data/reference/nq_1m_master.parquet")
b["ts"]=pd.to_datetime(b.ts_event,utc=True); b["uk"]=b.ts.dt.tz_convert("Europe/London")
b=b.sort_values("ts").reset_index(drop=True)
# --- CVD 3-min delta, NOW INCLUDING q4_2025 ---
FILES=["footprint_q3_2025","footprint_q4_2025","footprint_feb_mar2026","footprint_apr2026","footprint_may_jul2026"]
cvd_days=set(); dparts=[]
MISSING_CVD=[f for f in FILES if not _os.path.exists(f"{WT}/data/reference/cvd/{f}.parquet")]
if MISSING_CVD: print("WARN missing CVD (those days -> unconfirmed):", MISSING_CVD, flush=True)
for f in [f for f in FILES if f not in MISSING_CVD]:
    d=pd.read_parquet(f"{WT}/data/reference/cvd/{f}.parquet",columns=["ts_minute","side","volume"])
    cvd_days|=set(pd.to_datetime(d.ts_minute,utc=True).dt.tz_convert("Europe/London").dt.strftime("%Y-%m-%d").unique())
    d["s"]=np.where(d.side=="B",d.volume,-d.volume); dparts.append(d.groupby("ts_minute")["s"].sum()); del d
delta=pd.concat(dparts).groupby(level=0).sum().sort_index(); delta.index=pd.to_datetime(delta.index,utc=True)
delta3=delta.rolling(3).sum(); del dparts
print(f"  cvd days={len(cvd_days)} (q4 incl)",flush=True)
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
    st=en-dr*rk; tg=en+dr*3*rk; gg=None; j=i+1
    while j<len(M) and ud[j]==d:
        if utt[j]>=dtime(16,30): gg=dr*(a["close"][j]-en); break
        hs=(a["low"][j]<=st) if dr>0 else (a["high"][j]>=st); ht=(a["high"][j]>=tg) if dr>0 else (a["low"][j]<=tg)
        if hs: gg=-rk-TICK; break
        if ht: gg=3*rk-TICK; break
        j+=1
    if gg is None: gg=dr*(a["close"][min(j,len(M)-1)]-en)
    em=pd.Timestamp(a["uts"][i]); em=em.tz_localize("UTC") if em.tzinfo is None else em.tz_convert("UTC")
    v3=delta3.get(em-pd.Timedelta(minutes=1),np.nan); cov=(d in cvd_days) and not np.isnan(v3)
    ok=bool((v3>0) if dr>0 else (v3<0)) if cov else False
    rows.append(dict(day=d,ent=str(utt[i]),dir=dr,net=gg*PV-COMM,R=(gg*PV-COMM)/(rk*PV),win=gg>0,cvd_cov=cov,cvd_ok=ok))
A=pd.DataFrame(rows).sort_values(["day","ent"]).reset_index(drop=True)
# day-stop: stop after first loss of day
keep=[]
for d,g in A.groupby("day"):
    st=False
    for _,r in g.iterrows():
        if st: continue
        keep.append(r.name)
        if r.net<0: st=True
Sd=A.loc[keep].copy()
def dd(s): e=s.sort_values("day").net.cumsum().values; return float((np.maximum.accumulate(e)-e).max()) if len(s) else 0
def rep(df,lab,w=None):
    n=df.net if w is None else df.net*w
    v=df.R.values; print(f"  {lab:32s} n={len(df):3d} WR {100*(v>0).mean():3.0f}% net ${n.sum():+8,.0f} maxDD ${dd(df.assign(net=n)):,.0f}")
print(f"\n=== FULL BASELINE (all 10-13 trades) ===  cov trades={int(A.cvd_cov.sum())}/{len(A)}  confirm={int((A.cvd_cov&A.cvd_ok).sum())}")
rep(A,"base")
print("\n=== DAY-STOP BOOK ===")
rep(Sd,"day-stop base")
w1=np.where(Sd.cvd_cov&Sd.cvd_ok,1.5,1.0)
rep(Sd,"V1: 1.5x CVD-confirm",pd.Series(w1,index=Sd.index))
# confirm-only
CO=Sd[Sd.cvd_cov&Sd.cvd_ok]
rep(CO,"confirm-ONLY (hard filter)")
print(f"\n=== VERIFICATION: V1 sized, both years + 4 halves ===")
Sd2=Sd.assign(w=w1, netw=Sd.net*w1)
for y in("2025","2026"):
    s=Sd2[Sd2.day.str[:4]==y]; print(f"  {y}: net ${s.netw.sum():+8,.0f} DD ${dd(s.assign(net=s.netw)):,.0f} n={len(s)}")
for nm,lo,hi in[("25Q3","2025-07","2025-09"),("25Q4","2025-10","2025-12"),("26Q1","2026-01","2026-03"),("26Q2+","2026-04","2026-07")]:
    s=Sd2[(Sd2.day.str[:7]>=lo)&(Sd2.day.str[:7]<=hi)]; print(f"  {nm}: net ${s.netw.sum():+8,.0f} n={len(s)} confirm={int((s.cvd_cov&s.cvd_ok).sum())}")
print(f"\n  vs PRE-Q4 V1 (Oct-Dec blind): +$72,140 / maxDD $3,522")
print(f"  NOW           V1 (Oct-Dec CVD live): +${(Sd.net*w1).sum():,.0f} / maxDD ${dd(Sd.assign(net=Sd.net*w1)):,.0f}")
# how many Oct-Dec trades flipped to confirmed
octdec=Sd[(Sd.day.str[:7]>="2025-10")&(Sd.day.str[:7]<="2025-12")]
print(f"\n  Oct-Dec 2025: {len(octdec)} day-stop trades, now {int((octdec.cvd_cov&octdec.cvd_ok).sum())} CVD-confirmed (were 0 before q4)")
A.to_csv(f"{S}/london_1013_book_q4.csv",index=False); print("\nsaved london_1013_book_q4.csv")