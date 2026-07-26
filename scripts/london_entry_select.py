#!/usr/bin/env python3
"""ENTRY-SELECTION lever (exits proven dead 3x). 'Unnecessary losses' = the ~65% of losers that go
straight to the stop showing no profit. Only entry-observable validated signal = CVD-confirm.
Q: does trimming UNCONFIRMED exposure cut those losses without killing profit? Funded fixed-$ lens.
Diagnostic: loser composition (confirmed vs unconfirmed, never-green) + $ each side contributes.
Schemes (all day-stopped, $300 base): baseline A(1.0/0.5), confirm-only, A-trim(1.0/0.25),
drop-wide-unconf (cut unconfirmed trades whose stop>median, an entry-observable gamble).
Reports net$, maxDD$, worst R-drawdown (blow proxy), WR, N. q4 CVD. No lookahead."""
from datetime import time as dtime
import numpy as np, pandas as pd
import os as _os
S=_os.environ.get("LONDON_SCRATCH", _os.path.expanduser("~/london_out"))
WT=_os.environ.get("LONDON_WT", f"{S}/canon_wt")
_os.makedirs(S, exist_ok=True)
TICK,PV,COMM=0.25,20.0,5.0; TG=3.0; BASE=300.0
print("load...",flush=True)
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
delta=pd.concat(dparts).groupby(level=0).sum().sort_index(); delta.index=pd.to_datetime(delta.index,utc=True)
delta3=delta.rolling(3).sum(); del dparts
print(f"  cvd days={len(cvd_days)}",flush=True)
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
    em=pd.Timestamp(a["uts"][i]); em=em.tz_localize("UTC") if em.tzinfo is None else em.tz_convert("UTC")
    v3=delta3.get(em-pd.Timedelta(minutes=1),np.nan); cov=(d in cvd_days) and not np.isnan(v3); conf=bool((v3>0) if dr>0 else (v3<0)) if cov else False
    rows.append(dict(day=d,ent=str(utt[i]),rk=rk,R=Rr,win=Rr>0,conf=conf,mfe_R=mfe/rk,never_green=(mfe/rk)<0.5))
T=pd.DataFrame(rows).sort_values(["day","ent"]).reset_index(drop=True)
medrk=T.rk.median()

def funded(w,lab):
    df=T.assign(w=w); df=df[df.w>0]
    keep=[]
    for d,g in df.groupby("day",sort=True):
        stp=False
        for idx,r in g.iterrows():
            if stp: continue
            keep.append(idx)
            if r.R<0: stp=True
    k=df.loc[keep]; doll=k.R.values*k.w.values*BASE; e=np.cumsum(doll)
    dd=float((np.maximum.accumulate(e)-e).max()) if len(e) else 0
    rr=k.R.values*k.w.values; er=np.cumsum(rr); rdd=float((np.maximum.accumulate(er)-er).max()) if len(er) else 0
    n=len(k); wn=int((k.R.values>0).sum())
    print(f"  {lab:34s} n={n:3d} WR {100*wn/n if n else 0:3.0f}%  net ${doll.sum():+8,.0f}  maxDD ${dd:6,.0f}  worstRdd {rdd:.2f}R  histDD@base ${rdd*BASE:,.0f}")
    return doll.sum(),dd,rdd,n

print("="*116); print(f"ENTRY SELECTION  |  {len(T)} triggers  |  conf={int(T.conf.sum())} unconf={int((~T.conf).sum())}"); print("="*116)
L=T[~T.win]
print("\n-- LOSER composition (the 'unnecessary' losses) --")
print(f"  {len(L)} losers: confirmed {int(L.conf.sum())} | unconfirmed {int((~L.conf).sum())}")
print(f"  never-green losers (MFE<0.5R, went straight to stop): {int(L.never_green.sum())}/{len(L)}  "
      f"-> of those, unconfirmed {int((L.never_green&~L.conf).sum())}, confirmed {int((L.never_green&L.conf).sum())}")
print(f"\n-- profit contribution by side (flat 1 unit, no day-stop) --")
for lab,msk in [("confirmed",T.conf),("unconfirmed",~T.conf)]:
    s=T[msk]; print(f"  {lab:12s} n={len(s):2d} WR {100*s.win.mean():3.0f}%  sumR {s.R.sum():+6.1f}  (wins {s[s.win].R.sum():+.1f} / losses {s[~s.win].R.sum():+.1f})")

print("\n-- SELECTION SCHEMES (funded fixed-$ lens, day-stopped) --")
funded(np.where(T.conf,1.0,0.5),"A baseline (conf 1.0 / unconf 0.5)")
funded(np.where(T.conf,1.0,0.0),"confirm-ONLY (drop unconfirmed)")
funded(np.where(T.conf,1.0,0.25),"A-trim (conf 1.0 / unconf 0.25)")
funded(np.where(T.conf,1.0,np.where(T.rk<=medrk,0.5,0.0)),"drop-wide-unconf (unconf & stop>med -> 0)")
funded(np.where(T.conf,1.0,np.where(T.rk<=medrk,0.5,0.25)),"trim-wide-unconf (wide unconf -> 0.25)")
print("\n  NOTE: never-green / round-trip are OUTCOMES (not knowable at entry) -> can only filter on CVD-confirm & stop size.")
print("  N~55, one favourable regime, no 2023-24 London holdout -> holdout candidate, not a ship.")
T.to_csv(f"{S}/london_entry_select_book.csv",index=False); print("saved london_entry_select_book.csv")
