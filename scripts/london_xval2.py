#!/usr/bin/env python3
"""Cross-validate London SMA trend-pullback vs Angus's verified checks. Lean/vectorized."""
import glob, re, json
from datetime import time as dtime
import numpy as np, pandas as pd
S = "/tmp/claude-0/-home-user-AI-trading-agents/69c9097f-44f3-585b-817f-a315126d0dbb/scratchpad"
WT = f"{S}/canon_wt"; TICK, PV, COMM = 0.25, 20.0, 5.0
DEPTH = f"{WT}/data/reference/depth_london"
MISM = [("2025-10-26", "2025-11-01"), ("2026-03-08", "2026-03-28")]
print("load...", flush=True)
b = pd.read_parquet("/home/user/gs/data/reference/nq_1m_master.parquet")
b["ts"] = pd.to_datetime(b["ts_event"], utc=True); b["uk"] = b.ts.dt.tz_convert("Europe/London")
b = b.sort_values("ts").reset_index(drop=True); b["ukday"] = b.uk.dt.strftime("%Y-%m-%d")
b1 = {d: (g.ts.values.astype("int64"), g.low.values.astype(float), g.high.values.astype(float)) for d, g in b.groupby("ukday")}
# ASIA cvd (per-file, lean)
cvd_ASIA = {}; cvd_days = set()
for f in ["footprint_q3_2025","footprint_feb_mar2026","footprint_apr2026","footprint_may_jul2026"]:
    d = pd.read_parquet(f"{WT}/data/reference/cvd/{f}.parquet", columns=["ts_minute","side","volume"])
    uk = pd.to_datetime(d.ts_minute, utc=True).dt.tz_convert("Europe/London")
    d["ukday"] = uk.dt.strftime("%Y-%m-%d"); cvd_days |= set(d.ukday.unique())
    d["s"] = np.where(d.side=="B", d.volume, -d.volume)
    g = d[uk.dt.time < dtime(8,0)].groupby("ukday")["s"].sum()
    for k,v in g.items(): cvd_ASIA[k] = cvd_ASIA.get(k,0)+float(v)
    del d
print("  cvd loaded", flush=True)
onov = b[(b.uk.dt.time >= dtime(22, 0)) | (b.uk.dt.time < dtime(8, 0))].copy()
onov["sess"] = (onov.uk + pd.Timedelta(hours=2)).dt.strftime("%Y-%m-%d")  # 22:00->08:00 belongs to the 08:00 day
ONH = onov.groupby("sess").high.max().to_dict(); ONL = onov.groupby("sess").low.min().to_dict()
m = b.set_index("ts").resample("15min", label="right", closed="right").agg(open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),volume=("volume","sum")).dropna(subset=["close"])
m["uk"] = m.index.tz_convert("Europe/London"); m["ukday"] = m.uk.dt.strftime("%Y-%m-%d"); m["ukt"] = m.uk.dt.time
for p in (20,50,200): m[f"ma{p}"] = m.close.rolling(p).mean()
m["vol10"] = m.volume.rolling(10).mean().shift(1); m["slo5"] = m.low.rolling(5).min(); m["shi5"] = m.high.rolling(5).max()
m["pclose"] = m.close.shift(1); m["pma50"] = m.ma50.shift(1)
M = m.reset_index(names="uts").dropna(subset=["ma200"]).reset_index(drop=True)
A = {c: M[c].values for c in ["uts","open","high","low","close","volume","ma20","ma50","ma200","vol10","slo5","shi5","pclose","pma50"]}
ukday=M.ukday.values; ukt=M.ukt.values
depth_files = {re.search(r"(\d{8})",f).group(1): f for f in glob.glob(f"{DEPTH}/*.csv")}; _dc={}
def wall(day, ts, entry, dr):
    dk = day.replace("-","")
    if dk not in depth_files: return None, None, False
    if dk not in _dc:
        d = pd.read_csv(depth_files[dk]); d["min"] = pd.to_datetime(d.ts_event, utc=True).dt.floor("min"); _dc[dk]=d.set_index("min")
    d=_dc[dk]; kt=pd.Timestamp(ts); kt=kt.tz_localize("UTC") if kt.tzinfo is None else kt.tz_convert("UTC"); key=kt.floor("min")
    if key not in d.index:
        c=d.index[(d.index<=key)&(d.index>=key-pd.Timedelta(minutes=3))]
        if not len(c): return None,None,False
        key=c.max()
    r=d.loc[key]; r=r.iloc[-1] if isinstance(r,pd.DataFrame) else r
    bsz=np.array([r[f"bid_sz_0{i}"] for i in range(10)],float); bpx=np.array([r[f"bid_px_0{i}"] for i in range(10)],float)
    asz=np.array([r[f"ask_sz_0{i}"] for i in range(10)],float); apx=np.array([r[f"ask_px_0{i}"] for i in range(10)],float)
    (bhs,bhp,ahs,ahp)=(bsz,bpx,asz,apx) if dr>0 else (asz,apx,bsz,bpx)
    bm=np.median(bhs[bhs>0]) if (bhs>0).any() else 1; am=np.median(ahs[ahs>0]) if (ahs>0).any() else 1
    W = not (bhs>=3*bm).any()
    aw=np.where(ahs>=3*am)[0]
    FAR = True if not len(aw) else (min(abs(ahp[k]-entry) for k in aw) > 4.5)
    return W, FAR, True
def build(trig):
    R=[]
    for i in range(1,len(M)-1):
        d=ukday[i]
        if not("2025-07-01"<=d<="2026-07-15") or d in ("2025-11-28","2026-04-03") or ukday[i+1]!=d: continue
        t=ukt[i]; seg="R" if dtime(8,0)<=t<dtime(10,0) else ("F" if dtime(8,0)<=t<dtime(14,30) else None)
        if seg is None: continue
        up=A["ma20"][i]>A["ma50"][i]>A["ma200"][i] and A["close"][i]>A["ma50"][i] and A["close"][i]>A["ma200"][i]
        dn=A["ma20"][i]<A["ma50"][i]<A["ma200"][i] and A["close"][i]<A["ma50"][i] and A["close"][i]<A["ma200"][i]
        dr=1 if(up and A["low"][i]<=A["ma50"][i]) else(-1 if(dn and A["high"][i]>=A["ma50"][i]) else 0)
        if dr==0: continue
        if trig=="volfade" and not(A["vol10"][i]>0 and A["volume"][i]<A["vol10"][i]): continue
        if trig=="reclaim" and not((A["pclose"][i]<A["pma50"][i]) if dr>0 else (A["pclose"][i]>A["pma50"][i])): continue
        entry=A["open"][i+1]+dr*TICK; ref=min(A["slo5"][i],A["ma50"][i]) if dr>0 else max(A["shi5"][i],A["ma50"][i])
        risk=abs(entry-ref)+TICK
        if risk<5 or risk>70: continue
        stop=entry-dr*risk; tgt=entry+dr*3*risk; g=None; jx=i+1; j=i+1
        while j<len(M) and ukday[j]==d:
            if ukt[j]>=dtime(16,30): g=dr*(A["close"][j]-entry); jx=j; break
            hs=(A["low"][j]<=stop) if dr>0 else (A["high"][j]>=stop); ht=(A["high"][j]>=tgt) if dr>0 else (A["low"][j]<=tgt)
            if hs: g=-risk-TICK; jx=j; break
            if ht: g=3*risk-TICK; jx=j; break
            j+=1
        if g is None: jx=min(j,len(M)-1); g=dr*(A["close"][jx]-entry)
        net=g*PV-COMM; ti,lo1,hi1=b1[d]; t0=pd.Timestamp(A["uts"][i]).value; t1=pd.Timestamp(A["uts"][jx]).value
        msk=(ti>t0)&(ti<=t1); mae=(entry-lo1[msk].min()) if(dr>0 and msk.any()) else((hi1[msk].max()-entry) if msk.any() else 0.0)
        onh=ONH.get(d,np.nan); onl=ONL.get(d,np.nan); room=((onh-entry) if dr>0 else (entry-onl))/risk
        R.append(dict(day=d,ent=str(t),seg=seg,dir=dr,entry=entry,risk=risk,net=net,R=net/(risk*PV),win=net>0,
                      mae_R=max(0.,mae)/risk,room=room,cvd_ASIA=cvd_ASIA.get(d,np.nan),asia_cov=d in cvd_days,
                      early_tight=(t<dtime(8,30) and risk<8),sub7=risk<7,mism=any(a<=d<=b_ for a,b_ in MISM),uts=A["uts"][i]))
    return pd.DataFrame(R)
booksA=build("volfade"); booksB=build("reclaim")
# attach W/FAR on restricted
def attach(df):
    R=df[df.seg=="R"].copy(); W=[];F=[];C=[]
    for _,r in R.iterrows():
        w,f,c=wall(r.day,r.uts,r.entry,r.dir); W.append(w);F.append(f);C.append(c)
    R["W"]=W;R["FAR"]=F;R["depth_cov"]=C; return R
AR=attach(booksA); BR=attach(booksB)
def L(df):
    if not len(df): return dict(n=0)
    v=df.R.values; eq=df.sort_values("day").net.cumsum().values; dd=float((np.maximum.accumulate(eq)-eq).max())
    gp=v[v>0].sum(); gl=-v[v<0].sum()
    return dict(n=len(df),wr=round(100*(v>0).mean()),eR=round(float(v.mean()),3),pf=round(float(gp/gl),2) if gl>0 else 99.,net=round(float(df.net.sum())),dd=round(dd))
print("\n=== 1. RESTRICTED 08:00-10:00 UK vs FULL-SESSION (baseline A) ===")
print("  full   :",L(booksA)); print("  restr  :",L(AR))
ARk=AR[~AR.sub7].copy()
print(f"\n=== 2/4. CHECKS on restricted book (n={len(ARk)} post sub-7 kill; cells<20=DIRECTIONAL) ===")
ck=[("StopFloor>=9.5",ARk.risk>=9.5),("ROOM 2.5-9.6",(ARk.room>=2.5)&(ARk.room<=9.6)),
    ("ASIA_notopp",(~ARk.asia_cov)|(ARk.dir*ARk.cvd_ASIA>=-748)),("NotEarlyTight",~ARk.early_tight),
    ("W_absent",ARk.W==True),("FAR>4.5",ARk.FAR==True)]
print(f"  {'check':15}{'passN':>6}{'passNet':>9}{'failN':>6}{'failNet':>9}  verdict")
verd={}
for nm,cond in ck:
    cond=cond.fillna(False)
    base=ARk if nm not in ("W_absent","FAR>4.5") else ARk[ARk.depth_cov==True]
    c2=cond.loc[base.index]; p=base[c2]; f=base[~c2]
    v=("VETO(fail -$)" if (len(f)>=5 and f.net.sum()<0) else "score-check" if p.net.sum()>f.net.sum() else "no-transfer")
    if len(p)<8 or len(f)<8: v+="[thin]"
    verd[nm]=v; print(f"  {nm:15}{len(p):6}{p.net.sum():+9,.0f}{len(f):6}{f.net.sum():+9,.0f}  {v}")
ARk["score"]=sum([(c.loc[ARk.index].fillna(False)).astype(int) for _,c in ck])
print("\n=== 3. SCORE LADDER ===")
for sc in sorted(ARk.score.unique()): print(f"  score {sc}: {L(ARk[ARk.score==sc])}")
print("\n=== 5. RECONCILE ===")
wn=AR[AR.win]; print(f"  (a) my winners median MAE {wn.mae_R.median():+.2f}R vs Angus -0.4R -> {'MATCH (run-immediately)' if wn.mae_R.median()<0.6 else 'DIFFERENT: mine survive deep MAE (pullback vs retest physics)'}")
et=AR[AR.early_tight]; print(f"  (b) early+tight cell n={len(et)} net ${et.net.sum():+,.0f} -> {'toxic (matches Angus)' if et.net.sum()<0 else 'not toxic here (thin)'}")
print("  (c) windows: my restricted 08:00-10:00 UK == his London-open depth window")
print("\n=== 6. VERIFICATION (restricted A) ===")
for y in ("2025","2026"): print(f"  {y}: {L(AR[AR.day.str[:4]==y])}")
for nm,lo,hi in [("25Q3","2025-07","2025-09"),("25Q4","2025-10","2025-12"),("26Q1","2026-01","2026-03"),("26Q2+","2026-04","2026-07")]:
    print(f"  {nm}: {L(AR[(AR.day.str[:7]>=lo)&(AR.day.str[:7]<=hi)])}")
print(f"  DST-mismatch trades: {int(AR.mism.sum())} ({100*AR.mism.mean():.0f}%)")
print("\n=== B_reclaim restricted (ref) ===",L(BR))
json.dump(dict(full=L(booksA),restr=L(AR),verd=verd,depth_cov=int(AR.depth_cov.sum()),
               ladder={int(s):L(ARk[ARk.score==s]) for s in ARk.score.unique()},
               yr={y:L(AR[AR.day.str[:4]==y]) for y in ("2025","2026")},
               win_mae=float(wn.mae_R.median()),reclaim=L(BR)),open(f"{S}/london_xval_summary.json","w"),default=str)
AR.drop(columns=["uts"]).to_csv(f"{S}/london_xval_restricted.csv",index=False)
print("\nSAVED.")
