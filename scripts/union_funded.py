"""UNION-ERA FUNDED SIM (Angus's ask to Brake): the funded-account odds on 2020-26, not 2023-26 alone.
Same rules as docs/FINDINGS-funded-sim-armed.md: day$ = micros*2*sum(pts-0.5); 30% haircut of mean day$; eval from 0 with
$2,000 EOD-trailing floor locking at start once ahead, target +3,000 (>=1 day); funded phase fresh to +4,000 (>=10 days);
5-day block bootstrap; 120-day cap. Armed empire. 2020-22 has no news gate (archive starts 2023)."""
import gzip, json, numpy as np
from collections import defaultdict
QL="/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18"
def load(n,c):
    ts=[json.loads(l) for l in gzip.open(f"{QL}/output/analysis/{n}","rt")]
    return [t for t in ts if (not c) or (t["depth"]==3.0 and t["target_r"]==1.0)]
def daily_pts(files):
    byday=defaultdict(list)
    for n,c in files:
        for t in load(n,c): byday[t["day"]].append(t)
    out={}
    for d,ts in byday.items():
        ts.sort(key=lambda t:(t["fill_hrs"],t["t_sig_hrs"])); op=[]; s=0.0
        for t in ts:
            f=t["fill_hrs"]; e=f+t["hold_min"]/60; op=[q for q in op if q[1]>f]
            if any(q[2]==t["dir"] and abs(q[3]-t["entry"])<=5.0 for q in op): continue
            if len(op)>=4 or sum(1 for q in op if q[2]==t["dir"])>=3: continue
            op.append((f,e,t["dir"],t["entry"])); s+=t["pts"]-0.5
        out[d]=s
    return out
A23=daily_pts([("pd_va_trades_lvall_xr30_sar_through_tf1_ng_arm1.jsonl.gz",False),("vwap_rev_tf1_retest_xr30_dd_arm1.jsonl.gz",True),("vwap_rev_tf1_retest_xr30_nyanc_dd_arm1.jsonl.gz",True)])
A20=daily_pts([("pd_va_trades_nq20a_lvall_xr30_sar_through_tf1_arm1.jsonl.gz",False),("vwap_rev_tf1_retest_nq20a_ng0_xr30_dd_arm1.jsonl.gz",True),("vwap_rev_tf1_retest_nq20a_ng0_xr30_nyanc_dd_arm1.jsonl.gz",True)])
U={**A20,**A23}; days=sorted(U); pts=np.array([U[d] for d in days])
print(f"union armed: {len(days)} days, mean {pts.mean():+.1f}pt/day, worst {pts.min():+.1f}pt")
rng=np.random.default_rng(5); BL=5; CAP=120; HC=0.30; NS=6000
def run(p, micros):
    d_all=p*2*micros; hc=HC*d_all.mean(); n=len(d_all)
    def draw(k):
        idx=[]
        while len(idx)<k:
            s=rng.integers(0,n-BL); idx+=range(s,s+BL)
        return d_all[np.array(idx[:k])]-hc
    ev=pay=0
    for _ in range(NS):
        x=draw(CAP); bal=peak=0.0; phase="eval"; pd_=0
        for i in range(CAP):
            bal+=x[i]; peak=max(peak,bal); pd_+=1
            if bal<=min(peak-2000,0): break
            if phase=="eval" and bal>=3000 and pd_>=1: ev+=1; phase="funded"; bal=peak=0.0; pd_=0; continue
            if phase=="funded" and bal>=4000 and pd_>=10: pay+=1; break
    return ev/NS, pay/NS
P23=np.array([A23[d] for d in sorted(A23)]); P20=np.array([A20[d] for d in sorted(A20)])
print(f"\n{'micros':>7}{'2023-26 payout':>16}{'2020-22 payout':>16}{'UNION payout':>14}   literal worst 60-day stretch at 1 micro (union): ${-min(np.convolve(pts*2,np.ones(1),'valid').cumsum()[i]-max(0,*(pts*2).cumsum()[:i+1]) for i in range(len(pts))) if False else 0:.0f}")
worst=0; bal=peak=0
for x in pts*2:
    bal+=x; peak=max(peak,bal); worst=min(worst,bal-peak)
print(f"(literal union path, 1 micro: worst peak-to-trough ${-worst:,.0f}; fits $2,000 at {int(2000/-worst)} micros)")
for m in (4,8,12,16,20):
    e23,p23=run(P23,m); e20,p20=run(P20,m); eu,pu=run(pts,m)
    print(f"{m:>7}{p23:>16.1%}{p20:>16.1%}{pu:>14.1%}")
print("\n>=80% start->payout odds: 2023-26 alone supports ~16 micros; union and 2020-22 columns give the size the fuller history supports.")
