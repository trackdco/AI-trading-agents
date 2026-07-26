#!/usr/bin/env python3
"""SYNTHESIS of winner-heat (MAE) + loser-MFE -> one adjustment: an ARMED REDUCED-RISK stop.
Winners breathe (median MAE 0.42R, cross back through entry) -> plain breakeven clipped them (tested, lost).
~27% of losers reach +1R on a close then round-trip to -1R -> those are the 'unnecessary' losses.
Idea: once price reaches +X R (trade has proven itself), move stop to +L R (L can be <0 = still below
entry, giving winners room). Catches round-trippers without clipping breathers - IF winners retrace less
than losers after going green. We MEASURE that separation first, then sweep (X,L) on the real
day-stopped + Scheme-A sized book. Adverse-first intrabar (conservative). q4 CVD loaded. No lookahead.
Verdict vs baseline in net $ AND maxDD; report winners_clipped vs losers_saved so both halves are shown."""
from datetime import time as dtime
import numpy as np, pandas as pd
S="/tmp/claude-0/-home-user-AI-trading-agents/69c9097f-44f3-585b-817f-a315126d0dbb/scratchpad"; WT=f"{S}/canon_wt"
TICK,PV,COMM=0.25,20.0,5.0; TG=3.0; RISKD=300.0
print("load...",flush=True)
b=pd.read_parquet("/home/user/gs/data/reference/nq_1m_master.parquet")
b["ts"]=pd.to_datetime(b.ts_event,utc=True); b["uk"]=b.ts.dt.tz_convert("Europe/London"); b=b.sort_values("ts").reset_index(drop=True)
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

def resolve_trail(i,dr,en,rk,X,L):
    """arm reduced-risk stop at +X R -> move stop to +L R. adverse-first. -> gross_pts."""
    orig=en-dr*rk; trail=en+dr*L*rk; tgt=en+dr*TG*rk; armed=False; j=i+1
    while j<N and ud[j]==ud[i]:
        if utt[j]>=dtime(16,30): return dr*(a["close"][j]-en)
        cur=trail if armed else orig
        if (a["low"][j]<=cur) if dr>0 else (a["high"][j]>=cur): return dr*(cur-en)-TICK
        fav=(a["high"][j]-en) if dr>0 else (en-a["low"][j])
        if fav>=TG*rk: return TG*rk-TICK
        if (not armed) and fav>=X*rk: armed=True
        j+=1
    return dr*(a["close"][min(j,N-1)]-en)

def retrace(i,dr,en,rk,X):
    """book resolution (stop-first); if it reaches +X R, track deepest favorable (in R) AFTER that."""
    st=en-dr*rk; tg=en+dr*TG*rk; j=i+1; green=False; mn=None
    while j<N and ud[j]==ud[i]:
        favhi=(a["high"][j]-en) if dr>0 else (en-a["low"][j])
        favlo=(a["low"][j]-en)*dr if dr>0 else (a["high"][j]-en)*dr  # = dr*(low-en) long / dr*(high-en) short
        if green:
            v=favlo/rk; mn=v if mn is None else min(mn,v)
        if utt[j]>=dtime(16,30): break
        if (a["low"][j]<=st) if dr>0 else (a["high"][j]>=st): return green,False,mn
        if (a["high"][j]>=tg) if dr>0 else (a["low"][j]<=tg): return green,True,mn
        if favhi>=X*rk:
            if not green: green=True; mn=(favlo/rk)
        j+=1
    return green,None,mn

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
    rows.append(dict(i=i,day=d,ent=str(utt[i]),dir=dr,rk=rk,en=en,conf=conf))
T=pd.DataFrame(rows).sort_values(["day","ent"]).reset_index(drop=True)

def netR(i,dr,en,rk,X,L):
    g=resolve_trail(i,dr,en,rk,X,L); return (g*PV-COMM)/(rk*PV)
# baseline per-trade R (never arm)
T["Rbase"]=[netR(r.i,r.dir,r.en,r.rk,99,0) for r in T.itertuples()]

def daystop_sized(Rcol_vals):
    """apply day-stop (first loss) then Scheme-A size; return (net$, maxDD$)."""
    df=T.assign(R=Rcol_vals); keep=[]
    for d,g in df.groupby("day",sort=True):
        stp=False
        for idx,r in g.iterrows():
            if stp: continue
            keep.append(idx)
            if r.R<0: stp=True
    k=df.loc[keep]; sz=np.where(k.conf,1.0,0.5); doll=k.R.values*sz*RISKD
    e=np.cumsum(doll); dd=float((np.maximum.accumulate(e)-e).max()) if len(e) else 0.0
    return doll.sum(),dd,len(k),int((k.R.values>0).sum())

print("="*112)
print(f"TRAIL SYNTHESIS  |  {len(T)} raw triggers, London 10-13 UK  |  conf={int(T.conf.sum())}")
print("="*112)

# ---- (1) post-green retrace: do winners retrace LESS than losers after reaching +1R? ----
print("\n-- POST-GREEN RETRACE: after first reaching +1.0R, how deep does price come back (R, low-based)? --")
diag=[retrace(r.i,r.dir,r.en,r.rk,1.0) for r in T.itertuples()]
gw=[m for (g,w,m) in diag if g and w is True and m is not None]
gl=[m for (g,w,m) in diag if g and w is False and m is not None]
def qq(x): x=np.asarray(x,float); return f"n={len(x):2d} med {np.median(x):+.2f}R q25 {np.percentile(x,25):+.2f} q75 {np.percentile(x,75):+.2f} min {x.min():+.2f}R"
print(f"  eventual WINNERS that reached +1R: {qq(gw)}")
print(f"  eventual LOSERS  that reached +1R: {qq(gl)}")
print(f"  -> separation at -0.3R: winners below -0.3R = {sum(v<-0.3 for v in gw)}/{len(gw)}   losers below -0.3R = {sum(v<-0.3 for v in gl)}/{len(gl)}")

# ---- (2) baseline book ----
b0,dd0,n0,w0=daystop_sized(T.Rbase.values)
print(f"\n-- BASELINE (leave it) --  net ${b0:+,.0f}  maxDD ${dd0:,.0f}  n={n0} WR {100*w0/n0:.0f}%")

# ---- (3) sweep (X arm, L trail) ----
Xs=[0.75,1.0,1.5,2.0]; Ls=[-0.5,-0.3,0.0,0.3,0.5]
print("\n-- SWEEP: d$ vs baseline (day-stopped + Scheme-A sized), rows=arm X, cols=trail L --")
print("        "+"  ".join(f"L{L:+.1f}" for L in Ls))
best=None
grid={}
for X in Xs:
    line=f"  X{X:.2f} "
    for L in Ls:
        if L>=X: line+="     .  "; continue
        Rv=np.array([netR(r.i,r.dir,r.en,r.rk,X,L) for r in T.itertuples()])
        tot,dd,n,w=daystop_sized(Rv); grid[(X,L)]=(tot,dd,n,w,Rv)
        line+=f" {tot-b0:+6,.0f}"
        if (best is None) or (tot>best[0]): best=(tot,dd,X,L,n,w,Rv)
    print(line)

# ---- (4) detail on the best cell ----
tot,dd,X,L,n,w,Rv=best
clip=int(((T.Rbase.values>2.5)&(Rv<2.5)).sum())            # was ~3R target, now not
save=int(((T.Rbase.values<-0.99)&(Rv>-0.99)).sum())        # was full stop, now cut earlier/banked
clip_ex=((T.Rbase.values>2.5)&(Rv<2.5)); save_ex=((T.Rbase.values<-0.99)&(Rv>-0.99))
clip_cost=(Rv[clip_ex]-T.Rbase.values[clip_ex]).sum()*RISKD
save_gain=(Rv[save_ex]-T.Rbase.values[save_ex]).sum()*RISKD
print("\n"+"="*112)
print(f"BEST CELL: arm at +{X:.2f}R -> move stop to {L:+.2f}R")
print(f"  net ${tot:+,.0f} (vs base ${b0:+,.0f}, d${tot-b0:+,.0f})   maxDD ${dd:,.0f} (vs ${dd0:,.0f})   n={n} WR {100*w/n:.0f}%")
print(f"  winners clipped: {clip}  (cost ${clip_cost:+,.0f})    losers saved: {save}  (gain ${save_gain:+,.0f})")
better = tot>=b0 and dd<=dd0
print(f"  -> {'ADOPT: helps net AND drawdown' if better else ('marginal/positive net but check DD' if tot>b0 else 'does NOT beat leaving it alone')}")
print("\n  per-year & per-quarter (best cell, sized $):")
kd=T.assign(R=Rv)
for y in ("2025","2026"):
    s=kd[kd.day.str[:4]==y]; print(f"    {y}: raw sumR {s.R.sum():+.1f}")
print("\n  N=~55, one favourable regime, no 2023-24 London holdout -> any gain is a HOLDOUT CANDIDATE, not a ship.")
T.assign(Rbest=Rv).to_csv(f"{S}/london_trail_synth_book.csv",index=False); print("saved london_trail_synth_book.csv")
