#!/usr/bin/env python3
"""London 10-13 UK day-stop book: conviction-based sizing grid, target maxDD<=$2000.
Conviction signals: CVD-confirm (verified best), Angus score (StopFloor+ROOM+ASIA+NotEarlyTight).
q4_2025 CVD loaded. Reports net + maxDD + per-year + 4-halves for each scheme; finds max-$ under $2000."""
from datetime import time as dtime
import numpy as np, pandas as pd
S="/tmp/claude-0/-home-user-AI-trading-agents/69c9097f-44f3-585b-817f-a315126d0dbb/scratchpad"; WT=f"{S}/canon_wt"
TICK,PV,COMM=0.25,20.0,5.0
print("load...",flush=True)
b=pd.read_parquet("/home/user/gs/data/reference/nq_1m_master.parquet")
b["ts"]=pd.to_datetime(b.ts_event,utc=True); b["uk"]=b.ts.dt.tz_convert("Europe/London")
b=b.sort_values("ts").reset_index(drop=True); b["ukt"]=b.uk.dt.time
FILES=["footprint_q3_2025","footprint_q4_2025","footprint_feb_mar2026","footprint_apr2026","footprint_may_jul2026"]
cvd_days=set(); dparts=[]; cvd_ASIA={}
for f in FILES:
    d=pd.read_parquet(f"{WT}/data/reference/cvd/{f}.parquet",columns=["ts_minute","side","volume"])
    uk=pd.to_datetime(d.ts_minute,utc=True).dt.tz_convert("Europe/London"); dd_=uk.dt.strftime("%Y-%m-%d")
    cvd_days|=set(dd_.unique()); d["s"]=np.where(d.side=="B",d.volume,-d.volume)
    for k,v in d[uk.dt.time<dtime(8,0)].assign(dk=dd_).groupby("dk")["s"].sum().items(): cvd_ASIA[k]=cvd_ASIA.get(k,0)+float(v)
    dparts.append(d.groupby("ts_minute")["s"].sum()); del d
delta=pd.concat(dparts).groupby(level=0).sum().sort_index(); delta.index=pd.to_datetime(delta.index,utc=True)
delta3=delta.rolling(3).sum(); del dparts
onov=b[(b.ukt>=dtime(22,0))|(b.ukt<dtime(8,0))].copy(); onov["sess"]=(onov.uk+pd.Timedelta(hours=2)).dt.strftime("%Y-%m-%d")
ONH=onov.groupby("sess").high.max().to_dict(); ONL=onov.groupby("sess").low.min().to_dict()
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
    em=pd.Timestamp(a["uts"][i+1]); em=em.tz_localize("UTC") if em.tzinfo is None else em.tz_convert("UTC")
    v3=delta3.get(em-pd.Timedelta(minutes=1),np.nan); cov=(d in cvd_days) and not np.isnan(v3); ok=bool((v3>0) if dr>0 else (v3<0)) if cov else False
    onh=ONH.get(d,np.nan); onl=ONL.get(d,np.nan); room=((onh-en) if dr>0 else (en-onl))/rk
    ca=cvd_ASIA.get(d,np.nan); asia_ok=(np.isnan(ca)) or (dr*ca>=-748)
    score=int(rk>=9.5)+int(2.5<=room<=9.6)+int(asia_ok)+1  # +1 NotEarlyTight
    rows.append(dict(day=d,ent=str(utt[i]),net=gg*PV-COMM,R=(gg*PV-COMM)/(rk*PV),win=gg>0,cov=cov,ok=ok,score=score))
A=pd.DataFrame(rows).sort_values(["day","ent"]).reset_index(drop=True)
keep=[]
for d,g in A.groupby("day"):
    stp=False
    for _,r in g.iterrows():
        if stp: continue
        keep.append(r.name)
        if r.net<0: stp=True
Sd=A.loc[keep].copy().reset_index(drop=True)
def dd(net): e=net.cumsum().values; return float((np.maximum.accumulate(e)-e).max())
def evalw(w,lab):
    net=Sd.net.values*w
    D=dd(pd.Series(net))
    ok4=all(net[(Sd.day.str[:7]>=lo)&(Sd.day.str[:7]<=hi)].sum()>0 for lo,hi in[("2025-07","2025-09"),("2025-10","2025-12"),("2026-01","2026-03"),("2026-04","2026-07")])
    y25=net[Sd.day.str[:4]=="2025"].sum(); y26=net[Sd.day.str[:4]=="2026"].sum()
    print(f"  {lab:42s} net ${net.sum():+8,.0f}  maxDD ${D:6,.0f}  {'<=2k' if D<=2000 else '    '}  25 ${y25:+,.0f} 26 ${y26:+,.0f} {'4/4' if ok4 else 'FAIL'}")
    return net.sum(),D
conf=(Sd.cov&Sd.ok).values; covfail=(Sd.cov&~Sd.ok).values; uncov=(~Sd.cov).values; s4=(Sd.score>=4).values
print(f"\nday-stop book: {len(Sd)} trades, confirm={conf.sum()}, covered-fail={covfail.sum()}, uncov={uncov.sum()}, score>=4={s4.sum()}")
print("=== conviction sizing grid (target maxDD<=$2000) ===")
evalw(np.ones(len(Sd)),"flat 1.0x (base)")
evalw(np.full(len(Sd),0.66),"flat 0.66x (scalar benchmark)")
evalw(np.where(conf,1.5,1.0),"V1: confirm 1.5 / else 1.0")
evalw(np.where(conf,1.0,0.5),"A: confirm 1.0 / else 0.5")
evalw(np.where(conf,1.5,0.5),"B: confirm 1.5 / else 0.5")
evalw(np.where(conf,1.0,np.where(covfail,0.25,0.5)),"C: confirm1.0/covfail0.25/uncov0.5")
evalw(np.where(conf&s4,1.5,np.where(conf|s4,1.0,0.5)),"D: conf&s4 1.5/either 1.0/neither 0.5")
evalw(np.where(conf,1.0,np.where(covfail,0.0,0.5)),"E: confirm1.0/covfail0/uncov0.5")
evalw(np.where(conf,1.0,0.0),"confirm-ONLY (1/0)")
evalw(np.where(conf,0.75,0.4),"F: confirm 0.75 / else 0.4 (scaled B)")
evalw(np.where(conf,1.25,0.4),"G: confirm 1.25 / else 0.4")
Sd.to_csv(f"{S}/london_conviction_book.csv",index=False); print("\nsaved london_conviction_book.csv")