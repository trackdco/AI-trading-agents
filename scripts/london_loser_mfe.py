#!/usr/bin/env python3
"""LOSER favorable excursion (MFE) - London 10:00-13:00 UK champion book (wide structural stop).
For every LOSER: how far into PROFIT did it go before reversing and hitting the stop?
Reported in R / points / $ at $300 risk, plus how many losers reached +0.5R..+2.5R.
Then a breakeven-rule counterfactual: move stop to entry once price reaches +X R, swept over X,
using an ADVERSE-FIRST intrabar convention (pessimistic/consistent) - reports net effect on the
WHOLE book (losers saved vs winners scratched) so we don't only look at the good half.
M15 OHLC -> excursions are bar-level; I report both intrabar-high (upper bound) and best-close
(actionable) versions. Same trigger/stop/costs as the book. No lookahead."""
from datetime import time as dtime
import numpy as np, pandas as pd
TICK,PV,COMM=0.25,20.0,5.0; TG=3.0; RISKD=300.0
b=pd.read_parquet("/home/user/gs/data/reference/nq_1m_master.parquet")
b["ts"]=pd.to_datetime(b.ts_event,utc=True); b["uk"]=b.ts.dt.tz_convert("Europe/London"); b=b.sort_values("ts").reset_index(drop=True)
m=b.set_index("ts").resample("15min",label="right",closed="right").agg(open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),volume=("volume","sum")).dropna(subset=["close"])
_uk=m.index.tz_convert("Europe/London"); m["ukt"]=_uk.time; m["ukday"]=_uk.strftime("%Y-%m-%d")
for p in(20,50,200): m[f"ma{p}"]=m.close.rolling(p).mean()
m["v10"]=m.volume.rolling(10).mean().shift(1); m["slo"]=m.low.rolling(5).min(); m["shi"]=m.high.rolling(5).max()
M=m.reset_index(names="uts").dropna(subset=["ma200"]); M=M[(M.ukday>="2025-07-01")&(M.ukday<="2026-07-15")].reset_index(drop=True)
a={c:M[c].values for c in["open","high","low","close","volume","ma20","ma50","ma200","v10","slo","shi"]}; ud=M.ukday.values; utt=M.ukt.values
N=len(M)

def walk(i,dr,en,rk):
    """book resolve (stop-first). Track favorable: mfe_incl(intrabar high, incl exit bar),
       mfe_pre(favorable before the exit bar), bestclose_pre(best favorable CLOSE before exit)."""
    st=en-dr*rk; tg=en+dr*TG*rk; j=i+1; mfe=0.0; mfe_pre=0.0; bestclose=0.0; bars=0
    while j<N and ud[j]==ud[i]:
        bars+=1; snap=mfe
        fav=(a["high"][j]-en) if dr>0 else (en-a["low"][j])
        if fav>mfe: mfe=fav
        if utt[j]>=dtime(16,30): return dr*(a["close"][j]-en),"flat",mfe,snap,bestclose,bars
        hs=(a["low"][j]<=st) if dr>0 else (a["high"][j]>=st)
        ht=(a["high"][j]>=tg) if dr>0 else (a["low"][j]<=tg)
        if hs: return -rk-TICK,"stop",mfe,snap,bestclose,bars
        if ht: return TG*rk-TICK,"target",mfe,snap,bestclose,bars
        cl=dr*(a["close"][j]-en)
        if cl>bestclose: bestclose=cl
        j+=1
    return dr*(a["close"][min(j,N-1)]-en),"eod",mfe,snap,bestclose,bars

def be_resolve(i,dr,en,rk,X):
    """move stop to entry once favorable reaches X*rk. ADVERSE-FIRST intrabar (low-first for longs).
       returns gross_pts (BE scratch = -TICK)."""
    st=en-dr*rk; tg=en+dr*TG*rk; armed=False; j=i+1
    while j<N and ud[j]==ud[i]:
        if utt[j]>=dtime(16,30): return dr*(a["close"][j]-en)
        cur=en if armed else st                                   # current stop
        adverse=(a["low"][j]<=cur) if dr>0 else (a["high"][j]>=cur)
        if adverse: return (-TICK) if armed else (-rk-TICK)       # BE scratch vs original stop
        fav=(a["high"][j]-en) if dr>0 else (en-a["low"][j])
        if fav>=TG*rk: return TG*rk-TICK                          # target
        if fav>=X*rk: armed=True                                  # arm BE for subsequent bars
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
    g,reason,mfe,mfe_pre,bestclose,bars=walk(i,dr,en,rk)
    rows.append(dict(day=d,dir=dr,risk=rk,win=g>0,reason=reason,gR=g/rk if reason!='stop' else -1,
                     mfe_R=mfe/rk,mfe_pre_R=mfe_pre/rk,bestclose_R=bestclose/rk,mfe_pts=mfe,bars=bars,i=i,en=en))
R=pd.DataFrame(rows); W=R[R.win]; L=R[~R.win]
print("="*100)
print(f"LOSER MFE (profit shown before losing)  |  {len(R)} trades ({len(W)} win / {len(L)} loss), London 10-13 UK")
print("="*100)
def q(x,u=""): x=np.asarray(x,float); return f"med {np.median(x):.2f}{u} | mean {np.mean(x):.2f}{u} | q25 {np.percentile(x,25):.2f} q75 {np.percentile(x,75):.2f} | max {x.max():.2f}{u}"

print("\n-- how far into PROFIT did LOSERS go before hitting the stop? --")
print(f"  intrabar-high (upper bound), R : {q(L.mfe_R.values)}")
print(f"  before the exit bar,      R    : {q(L.mfe_pre_R.values)}   <- profit that was clearly available earlier")
print(f"  best favorable CLOSE,     R    : {q(L.bestclose_R.values)}   <- what a close-based rule could act on")
print(f"  in $ @ $300 risk (intrabar-high): med ${np.median(L.mfe_R.values)*RISKD:.0f} | mean ${np.mean(L.mfe_R.values)*RISKD:.0f} | max ${L.mfe_R.max()*RISKD:.0f}")

print("\n-- how many LOSERS reached +X R before dying --")
for x in (0.25,0.5,0.75,1.0,1.5,2.0,2.5):
    kH=int((L.mfe_R>=x).sum()); kC=int((L.bestclose_R>=x).sum())
    print(f"  +{x:.2f}R : intrabar {kH:2d}/{len(L)} ({100*kH/len(L):3.0f}%)   |   on a close {kC:2d}/{len(L)} ({100*kC/len(L):3.0f}%)")

print("\n-- BREAKEVEN-RULE counterfactual: move stop to entry once price hits +X R (adverse-first, whole book) --")
base_sumR=sum((3-TICK/r.risk) if r.reason=='target' else (-1-TICK/r.risk) if r.reason=='stop' else r.gR for _,r in R.iterrows())
# recompute baseline cleanly from be_resolve with X huge (never arms) to keep conventions comparable:
def bookR(X):
    tgt=stp=scr=0; sR=0.0
    for _,r in R.iterrows():
        g=be_resolve(int(r.i),int(r.dir),r.en,r.risk,X); Rr=(g*PV-COMM)/(r.risk*PV); sR+=Rr
        if abs(g-(TG*r.risk-TICK))<1e-9: tgt+=1
        elif abs(g-(-r.risk-TICK))<1e-9: stp+=1
        elif abs(g-(-TICK))<1e-9: scr+=1
    return sR,tgt,stp,scr
b0=bookR(9.99)
print(f"  {'baseline (no BE)':22s} sumR {b0[0]:+6.1f}  ${b0[0]*RISKD:+8,.0f}   targets {b0[1]} stops {b0[2]} scratch {b0[3]}")
for X in (0.5,0.75,1.0,1.5,2.0):
    sR,tgt,stp,scr=bookR(X)
    print(f"  BE at +{X:.2f}R{'':11s} sumR {sR:+6.1f}  ${sR*RISKD:+8,.0f}   targets {tgt} stops {stp} scratch {scr}   d$ {(sR-b0[0])*RISKD:+7,.0f}")
print("  (fixed-$ risk lens: each target=+3R, stop=-1R, BE scratch~0. Raw 70 trades, flat, no day-stop.)")
print("  NOTE: adverse-first is conservative for the rule; folding a winning X into the day-stop book needs a full re-run.")
R.to_csv("/tmp/claude-0/-home-user-AI-trading-agents/69c9097f-44f3-585b-817f-a315126d0dbb/scratchpad/london_loser_mfe.csv",index=False)
print("\nsaved london_loser_mfe.csv")
