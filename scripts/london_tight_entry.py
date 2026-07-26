#!/usr/bin/env python3
"""Tight-entry crossover test - London 10:00-13:00 UK pullback book.
Does riding the rejection-wick (tighter stop) or entering AT the level SHED WINNERS
vs the wide swing-low stop? Same trigger set / span / costs / day-stop / DST-day drops.
  A champion  : market entry open[i+1]+slip, stop = min(slo,ma50)-tick   (WIDE structural)  [the book]
  B wick-stop : market entry open[i+1]+slip, stop = wick[i]-tick          (TIGHT, same entry)
  C cvd-gated : B (tight) when CVD confirms, else A (wide)                (the conviction-2 idea)
  B2 retest   : limit entry at ma50 on retest <=4 bars, stop=wick[i]-tick (enter AT level; SECONDARY)
All arms keep the 3R target, and the VERDICT is read in R / fixed-$-risk (each trade risks the same $,
a 3R winner pays 3R regardless of stop size). Raw 1-NQ $ is shown too but ONLY for reference - it
structurally favours wide stops (more points per 3R) and is the wrong lens for 'did we shed winners'.
Decisive metric: SHED WINNERS (A won, tight arm lost/missed) vs GAINED (A lost/flat, tight arm won).
No lookahead. q4_2025 CVD loaded. N~55 flagged; one favourable regime; no 2023-24 holdout for London."""
from datetime import time as dtime
import numpy as np, pandas as pd
S="/tmp/claude-0/-home-user-AI-trading-agents/69c9097f-44f3-585b-817f-a315126d0dbb/scratchpad"; WT=f"{S}/canon_wt"
TICK,PV,COMM=0.25,20.0,5.0
TG=3.0; FILLWIN=4; BASE=300.0            # BASE = fixed-$ risk per 1.0 size unit (funded ceiling)
print("load...",flush=True)
b=pd.read_parquet("/home/user/gs/data/reference/nq_1m_master.parquet")
b["ts"]=pd.to_datetime(b.ts_event,utc=True); b["uk"]=b.ts.dt.tz_convert("Europe/London")
b=b.sort_values("ts").reset_index(drop=True)
FILES=["footprint_q3_2025","footprint_q4_2025","footprint_feb_mar2026","footprint_apr2026","footprint_may_jul2026"]
cvd_days=set(); dparts=[]
for f in FILES:
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

def walk(i,dr,en,rk,startj):
    """walk price from bar startj -> (gross_pts, reason). 3R target, stop-first tie, 16:30 flat, day bound."""
    st=en-dr*rk; tg=en+dr*TG*rk; j=startj
    while j<N and ud[j]==ud[i]:
        if utt[j]>=dtime(16,30): return dr*(a["close"][j]-en),"flat"
        hs=(a["low"][j]<=st) if dr>0 else (a["high"][j]>=st)
        ht=(a["high"][j]>=tg) if dr>0 else (a["low"][j]<=tg)
        if hs: return -rk-TICK,"stop"
        if ht: return TG*rk-TICK,"target"
        j+=1
    return dr*(a["close"][min(j,N-1)]-en),"eod"

def net_of(g,rk): n=g*PV-COMM; return n,n/(rk*PV)

rows=[]
for i in range(1,N-1):
    d=ud[i]
    if d in("2025-11-28","2026-04-03") or ud[i+1]!=d or not(dtime(10,0)<=utt[i]<dtime(13,0)): continue
    up=a["ma20"][i]>a["ma50"][i]>a["ma200"][i] and a["close"][i]>a["ma50"][i] and a["close"][i]>a["ma200"][i]
    dn=a["ma20"][i]<a["ma50"][i]<a["ma200"][i] and a["close"][i]<a["ma50"][i] and a["close"][i]<a["ma200"][i]
    dr=1 if(up and a["low"][i]<=a["ma50"][i]) else(-1 if(dn and a["high"][i]>=a["ma50"][i]) else 0)
    if dr==0 or not(a["v10"][i]>0 and a["volume"][i]<a["v10"][i]): continue
    en=a["open"][i+1]+dr*TICK
    wide_rf=min(a["slo"][i],a["ma50"][i]) if dr>0 else max(a["shi"][i],a["ma50"][i])
    rk_w=abs(en-wide_rf)+TICK
    if rk_w<5 or rk_w>70: continue                       # SAME trigger gate as champion (wide qualifies)
    wick_rf=a["low"][i] if dr>0 else a["high"][i]
    rk_k=max(abs(en-wick_rf)+TICK,5.0)                   # tight stop rides the rejection wick, 5pt floor
    gA,exA=walk(i,dr,en,rk_w,i+1); netA,RA=net_of(gA,rk_w)
    gB,exB=walk(i,dr,en,rk_k,i+1); netB,RB=net_of(gB,rk_k)
    lvl=a["ma50"][i]; fillk=None                          # B2: resting limit at the level, filled on retest
    for k in range(i+1,min(i+1+FILLWIN,N)):
        if ud[k]!=d or utt[k]>=dtime(16,30): break
        if (a["low"][k]<=lvl) if dr>0 else (a["high"][k]>=lvl): fillk=k; break
    if fillk is not None:
        rk2=max(abs(lvl-wick_rf)+TICK,5.0); g2,ex2=walk(i,dr,lvl,rk2,fillk); net2,R2=net_of(g2,rk2); win2=g2>0; filled=True
    else:
        rk2,net2,R2,win2,filled=np.nan,0.0,0.0,False,False
    em=pd.Timestamp(a["uts"][i+1]); em=em.tz_localize("UTC") if em.tzinfo is None else em.tz_convert("UTC")
    v3=delta3.get(em-pd.Timedelta(minutes=1),np.nan); cov=(d in cvd_days) and not np.isnan(v3)
    conf=bool((v3>0) if dr>0 else (v3<0)) if cov else False
    rows.append(dict(day=d,ent=str(utt[i]),dir=int(dr),conf=conf,
        rkA=rk_w,netA=netA,RA=RA,winA=bool(gA>0),exA=exA,
        rkB=rk_k,netB=netB,RB=RB,winB=bool(gB>0),exB=exB,
        filled2=filled,rk2=rk2,net2=net2,R2=R2,win2=bool(win2)))
R=pd.DataFrame(rows).sort_values(["day","ent"]).reset_index(drop=True)
R["R_C"]=np.where(R.conf,R.RB,R.RA); R["net_C"]=np.where(R.conf,R.netB,R.netA); R["win_C"]=np.where(R.conf,R.winB,R.winA)
R["szflat"]=1.0; R["szA"]=np.where(R.conf,1.0,0.5)

def wilson(k,n,z=1.96):
    if n==0: return (0,0)
    p=k/n; dd=1+z*z/n; c=(p+z*z/(2*n))/dd; h=z*(p*(1-p)/n+z*z/(4*n*n))**0.5/dd; return (round(100*(c-h)),round(100*(c+h)))
def ddollar(x): e=np.cumsum(x); return float((np.maximum.accumulate(e)-e).max()) if len(x) else 0.0
def daystop(df,Rcol):
    keep=[]
    for d,g in df.groupby("day",sort=True):
        stp=False
        for idx,r in g.iterrows():
            if stp: continue
            keep.append(idx)
            if r[Rcol]<0: stp=True
    return df.loc[keep]

print("="*118)
print(f"TIGHT-ENTRY CROSSOVER  |  {len(R)} raw triggers (10:00-13:00 UK, Jul-2025 -> Jul-2026)  |  verdict read in R / fixed-${BASE:.0f} risk")
print("="*118)

# ---- (1) how much tighter is the stop? (answers 'did we limit SL size') ----
def q(x): x=np.asarray(x,float); return f"med {np.median(x):4.1f} | mean {np.mean(x):4.1f} | q25-q75 {np.percentile(x,25):4.1f}-{np.percentile(x,75):4.1f} | max {x.max():4.1f}"
print("\n-- STOP SIZE (points), all raw triggers --")
print(f"  A wide swing-low : {q(R.rkA.values)}")
print(f"  B wick-stop      : {q(R.rkB.values)}")
print(f"  B2 level+wick    : {q(R[R.filled2].rk2.values)}   (filled {int(R.filled2.sum())}/{len(R)} = {100*R.filled2.mean():.0f}%)")

# ---- (2) aligned shed/gain on the SAME triggers (pre-day-stop, hit-rate view) ----
print("\n-- SHED / GAIN vs A on identical triggers (pre-day-stop) --")
def sg(wincol,took,netcol,lab):
    Aw=R.winA.values; xw=(R[wincol].values)&took
    shed=Aw&~xw; gain=(~Aw)&xw
    miss=Aw&~took
    print(f"  {lab:12s} shed {int(shed.sum()):2d} of A's {int(Aw.sum())} winners (arm lost/missed)"
          f"   gained {int(gain.sum()):2d} (A lost/flat, arm won)"
          + (f"   [of shed: {int((Aw&~took).sum())} never filled]" if took is not R.winA.values and not took.all() else ""))
    print(f"               raw fixed-contract $: shed A-side {R.netA.values[shed].sum():+8,.0f}   gained arm-side {R[netcol].values[gain].sum():+8,.0f}")
sg("winB",np.ones(len(R),bool),"netB","B wick")
sg("win2",R.filled2.values,"net2","B2 level")
print(f"  (B keeps every A entry; a tighter stop can BOTH lose sooner and win sooner because the 3R target also comes in.)")

# ---- (3) full book: day-stop + sizing, verdict in R / fixed-$ risk ----
def bookline(df,Rcol,netcol,szcol,lab):
    d=df.sort_values(["day","ent"]); kept=daystop(d,Rcol)
    Rv=kept[Rcol].values; sz=kept[szcol].values; n=len(kept); k=int((Rv>0).sum())
    doll=Rv*sz*BASE; net_contract=(kept[netcol].values*(sz/ (0.5 if szcol=='szA' else 1.0) if False else sz))  # contract-$ ref (size-scaled)
    print(f"  {lab:30s} n={n:3d} WR {100*k/n if n else 0:3.0f}% CI{wilson(k,n)}  R(sz) {(Rv*sz).sum():+6.1f}  ${doll.sum():+8,.0f}  maxDD ${ddollar(doll):6,.0f}"+("  LOW-N" if n<30 else ""))
    return kept,doll
print("\n-- BOOK: flat 1.0x (isolates geometry, no conviction sizing) --")
bookline(R,"RA","netA","szflat","A wide  (the champion)")
bookline(R,"RB","netB","szflat","B wick  (tight, same entry)")
bookline(R[R.filled2],"R2","net2","szflat","B2 level (enter at level)")
print("\n-- BOOK: Scheme-A conviction sizing (confirm 1.0 / else 0.5) --")
kA,dA=bookline(R,"RA","netA","szA","A wide")
kB,dB=bookline(R,"RB","netB","szA","B wick")
kC,dC=bookline(R,"R_C","net_C","szA","C cvd-gated (tight if confirm)")

# ---- (4) per-quarter for A vs C (the two live candidates), fixed-$ risk Scheme-A ----
print("\n-- per-quarter (Scheme-A $, fixed-risk) A wide  vs  C cvd-gated --")
def quart(kept,Rcol):
    o={}
    for nm,lo,hi in[("25Q3","2025-07","2025-09"),("25Q4","2025-10","2025-12"),("26Q1","2026-01","2026-03"),("26Q2+","2026-04","2026-07")]:
        s=kept[(kept.day.str[:7]>=lo)&(kept.day.str[:7]<=hi)]; o[nm]=(s[Rcol].values*s.szA.values*BASE).sum()
    return o
qA=quart(kA,"RA"); qC=quart(kC,"R_C")
print("        "+"  ".join(f"{k:>7s}" for k in qA)); print("  A     "+"  ".join(f"{qA[k]:+7,.0f}" for k in qA)); print("  C     "+"  ".join(f"{qC[k]:+7,.0f}" for k in qC))

# ---- (5) verdict ----
print("\n"+"="*118)
totA=(kA.RA.values*kA.szA.values*BASE).sum(); ddA=ddollar(kA.RA.values*kA.szA.values*BASE)
totB=(kB.RB.values*kB.szA.values*BASE).sum(); ddB=ddollar(kB.RB.values*kB.szA.values*BASE)
totC=(kC.R_C.values*kC.szA.values*BASE).sum(); ddC=ddollar(kC.R_C.values*kC.szA.values*BASE)
shedB=int((R.winA.values&~R.winB.values).sum()); gainB=int((~R.winA.values&R.winB.values).sum())
print(f"VERDICT (Scheme-A, fixed-${BASE:.0f} risk):")
print(f"  A wide      ${totA:+8,.0f}  maxDD ${ddA:6,.0f}")
print(f"  B wick      ${totB:+8,.0f}  maxDD ${ddB:6,.0f}   (shed {shedB} winners, gained {gainB} vs A)")
print(f"  C cvd-gated ${totC:+8,.0f}  maxDD ${ddC:6,.0f}")
better = totC>=totA and ddC<=ddA
print(f"\n  -> C {'BEATS' if better else 'does NOT beat'} A on both net & maxDD."
      f"  Tight stop drops median SL {np.median(R.rkA):.0f}pt -> {np.median(R.rkB):.0f}pt but sheds {shedB} of A's {int(R.winA.sum())} winners.")
print("  N is small (one favourable regime, no 2023-24 London holdout) -> treat any winner as a HOLDOUT CANDIDATE, not a ship.")
R.to_csv(f"{S}/london_tight_entry_book.csv",index=False); print(f"\nsaved london_tight_entry_book.csv")
