#!/usr/bin/env python3
"""Winner HEAT (max adverse excursion) - London 10:00-13:00 UK champion book (wide structural stop).
For every WINNER: how far did price go AGAINST entry (toward the stop) before it hit the 3R target?
Reported as MAE in R (fraction of the stop distance), points, and $ at $300 fixed risk. Also the
'stop-fraction survival curve': how many winners a tighter stop at f*risk would have pre-killed
(this is the quantitative version of why the wick-stop test shed winners). M15 OHLC -> MAE is a
bar-level UPPER bound (intrabar order unknown; conservative). Same trigger/stop/costs as the book."""
from datetime import time as dtime
import numpy as np, pandas as pd
TICK,PV,COMM=0.25,20.0,3.0*0+5.0; TG=3.0; RISKD=300.0
b=pd.read_parquet(f"{WT}/data/reference/nq_1m_master.parquet")
b["ts"]=pd.to_datetime(b.ts_event,utc=True); b["uk"]=b.ts.dt.tz_convert("Europe/London"); b=b.sort_values("ts").reset_index(drop=True)
m=b.set_index("ts").resample("15min",label="right",closed="right").agg(open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),volume=("volume","sum")).dropna(subset=["close"])
_uk=m.index.tz_convert("Europe/London"); m["ukt"]=_uk.time; m["ukday"]=_uk.strftime("%Y-%m-%d")
for p in(20,50,200): m[f"ma{p}"]=m.close.rolling(p).mean()
m["v10"]=m.volume.rolling(10).mean().shift(1); m["slo"]=m.low.rolling(5).min(); m["shi"]=m.high.rolling(5).max()
M=m.reset_index(names="uts").dropna(subset=["ma200"]); M=M[(M.ukday>="2025-07-01")&(M.ukday<="2026-07-15")].reset_index(drop=True)
a={c:M[c].values for c in["open","high","low","close","volume","ma20","ma50","ma200","v10","slo","shi"]}; ud=M.ukday.values; utt=M.ukt.values
N=len(M)

def walk(i,dr,en,rk):
    """-> (gross_pts, reason, mae_pts, bars). MAE = deepest heat vs entry up to & incl exit bar."""
    st=en-dr*rk; tg=en+dr*TG*rk; j=i+1; mae=0.0; bars=0
    while j<N and ud[j]==ud[i]:
        bars+=1
        adv=(en-a["low"][j]) if dr>0 else (a["high"][j]-en)
        if adv>mae: mae=adv
        if utt[j]>=dtime(16,30): return dr*(a["close"][j]-en),"flat",mae,bars
        hs=(a["low"][j]<=st) if dr>0 else (a["high"][j]>=st)
        ht=(a["high"][j]>=tg) if dr>0 else (a["low"][j]<=tg)
        if hs: return -rk-TICK,"stop",mae,bars
        if ht: return TG*rk-TICK,"target",mae,bars
        j+=1
    return dr*(a["close"][min(j,N-1)]-en),"eod",mae,bars

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
    g,reason,mae,bars=walk(i,dr,en,rk)
    rows.append(dict(day=d,dir=dr,risk=rk,win=g>0,reason=reason,mae_pts=mae,mae_R=mae/rk,bars=bars))
R=pd.DataFrame(rows)
W=R[R.win]; L=R[~R.win]
print("="*100)
print(f"WINNER HEAT  |  {len(R)} trades ({len(W)} win / {len(L)} loss), London 10-13 UK champion (wide stop)")
print("="*100)

def q(x,unit=""):
    x=np.asarray(x,float)
    return f"med {np.median(x):.2f}{unit} | mean {np.mean(x):.2f}{unit} | q25 {np.percentile(x,25):.2f} q75 {np.percentile(x,75):.2f} | max {x.max():.2f}{unit}"

print("\n-- MAE of WINNERS (heat taken before the 3R target hit) --")
print(f"  in R (fraction of stop): {q(W.mae_R.values)}")
print(f"  in points              : {q(W.mae_pts.values,'pt')}")
print(f"  in $ @ $300 fixed risk : med ${np.median(W.mae_R.values)*RISKD:.0f} | mean ${np.mean(W.mae_R.values)*RISKD:.0f} | max ${W.mae_R.max()*RISKD:.0f}   (target pays ~+$900 = 3R)")
print(f"  bars in trade (M15)    : {q(W.bars.values,'')}  -> med {np.median(W.bars.values)*15:.0f} min, max {W.bars.max()*15:.0f} min in the trade")

print("\n-- how many winners took DEEP heat (>= f of the stop) --")
for f in (0.25,0.4,0.5,0.6,0.75,0.9):
    k=int((W.mae_R>=f).sum()); print(f"  MAE >= {f:.2f}R : {k:2d}/{len(W)} winners ({100*k/len(W):3.0f}%)")

print("\n-- STOP-FRACTION SURVIVAL: winners a tighter stop at f*risk would have PRE-KILLED --")
print("  (a stop at f*risk kills any winner whose heat reached f -> this is why tightening sheds winners)")
for f in (0.4,0.5,0.55,0.6,0.75):
    killed=int((W.mae_R>=f).sum())
    print(f"  stop at {f:.2f}R  (~{f*np.median(W.risk):.0f}pt on the median winner): kills {killed:2d}/{len(W)} winners = give back ${killed*3*RISKD:,.0f} of target profit")
print(f"  NOTE: the wick-stop test used ~20pt vs ~36pt wide  = ~0.55R  -> matches the ~8 shed winners we saw.")

print("\n-- LOSERS for contrast (they don't get a 'before target' - they hit the wall) --")
print(f"  loser exit reasons: {L.reason.value_counts().to_dict()}")
print(f"  winner exit reasons: {W.reason.value_counts().to_dict()}")
print(f"  losers' MAE in R: {q(L.mae_R.values)}  (->1.0 = rode to the stop)")

# the single deepest-heat winner (the trade that most needed the room)
dw=W.loc[W.mae_R.idxmax()]
print(f"\n-- deepest-heat WINNER: {dw.day} {'long' if dw.dir>0 else 'short'}  risk {dw.risk:.0f}pt, "
      f"went {dw.mae_R:.2f}R (${dw.mae_R*RISKD:.0f}) against before paying 3R  <- a stop tighter than {dw.mae_R:.2f}R loses this one")
R.to_csv(f"{S}/london_winner_heat.csv",index=False)
print("\nsaved london_winner_heat.csv")
