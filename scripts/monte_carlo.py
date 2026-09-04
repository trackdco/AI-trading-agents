"""MONTE CARLO on the armed empire, union tape 2020-26 (news gate inert on 2020-22).
Unit = one session-day's net NQ points after 0.5pt/RT cost, rails applied (same reducer as union_funded.py).
Resampling = 5-day block bootstrap (keeps the loss-chaining seen 2022-11-27..30). 10,000 paths per test.
Tests: (1) one-year distribution at 1 micro; (2) same with the edge cut 25/50/75% (real cost/slippage/decay);
(3) chance of a $2,000 peak-to-trough hit within a year by micro count; (4) trade-shuffle vs block MDD (why clustering matters)."""
import gzip, json, numpy as np, sys
from collections import defaultdict
QL="/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18"
def load(n,c):
    ts=[json.loads(l) for l in gzip.open(f"{QL}/output/analysis/{n}","rt")]
    return [t for t in ts if (not c) or (t["depth"]==3.0 and t["target_r"]==1.0)]
def daily(files):
    byday=defaultdict(list)
    for n,c in files:
        for t in load(n,c): byday[t["day"]].append(t)
    pts={}; rs={}; tr=[]
    for d,ts in byday.items():
        ts.sort(key=lambda t:(t["fill_hrs"],t["t_sig_hrs"])); op=[]; s=0.0; r=0.0
        for t in ts:
            f=t["fill_hrs"]; e=f+t["hold_min"]/60; op=[q for q in op if q[1]>f]
            if any(q[2]==t["dir"] and abs(q[3]-t["entry"])<=5.0 for q in op): continue
            if len(op)>=4 or sum(1 for q in op if q[2]==t["dir"])>=3: continue
            op.append((f,e,t["dir"],t["entry"])); s+=t["pts"]-0.5
            risk=t.get("risk") or abs(t["entry"]-t.get("stop",t["entry"]-t["pts"])) or 1
            rn=(t["pts"]-0.5)/max(risk,5.0); r+=rn; tr.append(rn)
        pts[d]=s; rs[d]=r
    return pts, rs, np.array(tr)
A23=daily([("pd_va_trades_lvall_xr30_sar_through_tf1_ng_arm1.jsonl.gz",False),("vwap_rev_tf1_retest_xr30_dd_arm1.jsonl.gz",True),("vwap_rev_tf1_retest_xr30_nyanc_dd_arm1.jsonl.gz",True)])
A20=daily([("pd_va_trades_nq20a_lvall_xr30_sar_through_tf1_arm1.jsonl.gz",False),("vwap_rev_tf1_retest_nq20a_ng0_xr30_dd_arm1.jsonl.gz",True),("vwap_rev_tf1_retest_nq20a_ng0_xr30_nyanc_dd_arm1.jsonl.gz",True)])
U={**A20[0],**A23[0]}; days=sorted(U); P=np.array([U[d] for d in days])
R={**A20[1],**A23[1]}; DR=np.array([R[d] for d in days]); TR=np.concatenate([A20[2],A23[2]])
print(f"union armed: {len(days)} days | {P.mean():+.1f} pt/day, sd {P.std():.1f} | {DR.mean():+.2f} R/day | {len(TR):,} trades, {TR.mean():+.4f} R/trade")
def mdd(c):
    pk=np.maximum.accumulate(np.concatenate([[0.0],c])); return float((np.concatenate([[0.0],c])-pk).min())
lit=P*2; print(f"literal path at 1 micro: total ${lit.sum():,.0f}, max DD ${-mdd(lit.cumsum()):,.0f}, worst day ${lit.min():,.0f}, worst 20-day ${np.convolve(lit,np.ones(20),'valid').min():,.0f}")
rng=np.random.default_rng(7); BL=5; NS=10000; YEAR=250
def paths(x, k, ns=NS):
    n=len(x); nb=int(np.ceil(k/BL)); starts=rng.integers(0,n-BL+1,size=(ns,nb))
    idx=(starts[:,:,None]+np.arange(BL)[None,None,:]).reshape(ns,-1)[:,:k]; return x[idx]
def year_stats(x, label):
    X=paths(x,YEAR); tot=X.sum(1); cum=X.cumsum(1); pk=np.maximum.accumulate(np.concatenate([np.zeros((NS,1)),cum],1),axis=1)
    dd=(np.concatenate([np.zeros((NS,1)),cum],1)-pk).min(1); w20=np.array([np.convolve(r,np.ones(20),'valid').min() for r in X[:2000]])
    neg=(X<0); streak=np.zeros(NS,int)
    for i in range(2000):
        s=m=0
        for v in neg[i]: s=s+1 if v else 0; m=max(m,s)
        streak[i]=m
    q=lambda a,p: np.percentile(a,p)
    print(f"  {label:<22} year P&L: median ${q(tot,50):>7,.0f}  bad5% ${q(tot,5):>7,.0f}  good95% ${q(tot,95):>7,.0f} | losing-year odds {np.mean(tot<0):5.1%} | maxDD median ${-q(dd,50):,.0f} bad5% ${-q(dd,5):,.0f} worst ${-dd.min():,.0f} | worst-20d median ${q(w20,50):,.0f} | longest red streak median {int(np.median(streak[:2000]))}d, 95th {int(np.percentile(streak[:2000],95))}d")
    return tot,dd
print(f"\n(1) ONE YEAR ({YEAR} days) AT 1 MICRO, block bootstrap x{NS:,}")
year_stats(lit,"backtest edge")
print(f"\n(2) SAME, BUT THE REAL EDGE IS SMALLER THAN THE BACKTEST (subtract a slice of the mean from every day)")
for h in (0.25,0.50,0.75,1.0): year_stats(lit-h*lit.mean(), f"edge cut {int(h*100)}%")
print(f"\n(3) ODDS OF A $2,000 PEAK-TO-TROUGH HIT (account death on a $2k trailing drawdown) — within 120 days / within a year")
print(f"  {'micros':>6}{'120d':>10}{'1yr':>8}   | edge cut 50%: {'120d':>6}{'1yr':>6}")
for m in (1,2,4,6,8,10,12,16):
    out=[]
    for x in (lit, lit-0.5*lit.mean()):
        X=paths(x*m,YEAR); cum=np.concatenate([np.zeros((NS,1)),X.cumsum(1)],1); pk=np.maximum.accumulate(cum,axis=1); dd=cum-pk
        out+=[np.mean((dd[:,:121]<=-2000).any(1)), np.mean((dd<=-2000).any(1))]
    print(f"  {m:>6}{out[0]:>10.1%}{out[1]:>8.1%}   |               {out[2]:>6.1%}{out[3]:>6.1%}")
print(f"\n(4) DOES CLUSTERING MATTER?  max DD in R over one year: trades shuffled independently vs days kept in 5-day blocks")
T=len(TR); ntr=int(T/len(days)*YEAR); sh=[mdd(rng.choice(TR,ntr).cumsum()) for _ in range(2000)]
bl=paths(DR,YEAR,2000); bd=[mdd(r.cumsum()) for r in bl]
print(f"  trade-shuffle MDD: median {np.median(sh):+.1f}R, bad5% {np.percentile(sh,5):+.1f}R | block-day MDD: median {np.median(bd):+.1f}R, bad5% {np.percentile(bd,5):+.1f}R | literal 7-yr: {mdd(DR.cumsum()):+.1f}R")
print(f"\n(3b) SAME BUT THE FLOOR LOCKS AT BREAKEVEN once you are $2,000 up (how Lucid-style trailing DD actually works) — death odds within a year")
print(f"  {'micros':>6}{'full edge':>11}{'cut 25%':>9}{'cut 50%':>9}")
for m in (1,2,4,6,8,10,12,16):
    out=[]
    for h in (0.0,0.25,0.5):
        X=paths((lit-h*lit.mean())*m,YEAR); cum=np.concatenate([np.zeros((NS,1)),X.cumsum(1)],1); pk=np.maximum.accumulate(cum,axis=1)
        floor=np.minimum(pk-2000,0.0); out.append(np.mean((cum<=floor)[:,1:].any(1)))
    print(f"  {m:>6}{out[0]:>11.1%}{out[1]:>9.1%}{out[2]:>9.1%}")
