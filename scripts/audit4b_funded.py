"""STAGE 4b — funded sim replicated under the ORIGINAL rules, independently coded:
day$ = micros*2*sum(pts-0.5) ; each day draw reduced by haircut*mean(day$) ; eval from 0, $2,000 EOD-trailing floor that
locks at start once peak >= +2,000 (floor = min(peak-2000, 0)) ; target +3,000, >=1 day ; funded phase fresh, same floor rule,
target +4,000, >=10 days ; 5-day block bootstrap ; 120-day cap on the whole journey ; 30% haircut."""
import json, gzip, numpy as np
from collections import defaultdict
QL="/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18"
days=json.load(open("/tmp/audit_armed_daily.json"))["days"]
def load(n,cell):
    ts=[json.loads(l) for l in gzip.open(f"{QL}/output/analysis/{n}","rt")]
    return [t for t in ts if (not cell) or (t["depth"]==3.0 and t["target_r"]==1.0)]
def series(names):
    B=[load(n,c) for n,c in names]; byday=defaultdict(list)
    for v in B:
        for t in v: byday[t["day"]].append(t)
    out=[]
    for d in days:
        ts=sorted(byday[d],key=lambda t:(t["fill_hrs"],t["t_sig_hrs"])); op=[]; s=0.0
        for t in ts:
            f=t["fill_hrs"]; e=f+t["hold_min"]/60; op=[q for q in op if q[1]>f]
            if any(q[2]==t["dir"] and abs(q[3]-t["entry"])<=5.0 for q in op): continue
            if len(op)>=4 or sum(1 for q in op if q[2]==t["dir"])>=3: continue
            op.append((f,e,t["dir"],t["entry"])); s+=t["pts"]-0.5
        out.append(s)
    return np.array(out)
ARMED=series([("pd_va_trades_lvall_xr30_sar_through_tf1_ng_arm1.jsonl.gz",False),("vwap_rev_tf1_retest_xr30_dd_arm1.jsonl.gz",True),("vwap_rev_tf1_retest_xr30_nyanc_dd_arm1.jsonl.gz",True)])
FLAT =series([("pd_va_trades_lvall_xr30_sar_through_tf1_ng.jsonl.gz",False),("vwap_rev_tf1_retest_xr30_dd.jsonl.gz",True),("vwap_rev_tf1_retest_xr30_nyanc_dd.jsonl.gz",True)])
rng=np.random.default_rng(3); BL=5; CAP=120; HC=0.30; NS=6000
def run(ptsnet, micros):
    d_all=ptsnet*2*micros; hc=HC*d_all.mean(); n=len(d_all)
    def draw(k):
        idx=[]
        while len(idx)<k:
            s=rng.integers(0,n-BL); idx+=range(s,s+BL)
        return d_all[np.array(idx[:k])]-hc
    ev=pay=0; days_pay=[]
    for _ in range(NS):
        x=draw(CAP); bal=peak=0.0; t=0; phase="eval"; pd_=0; ok=False
        for i in range(CAP):
            bal+=x[i]; peak=max(peak,bal); t+=1; pd_+=1
            floor=min(peak-2000,0)
            if bal<=floor: break
            if phase=="eval" and bal>=3000 and pd_>=1:
                ev+=1; phase="funded"; bal=peak=0.0; pd_=0; continue
            if phase=="funded" and bal>=4000 and pd_>=10:
                pay+=1; days_pay.append(t); ok=True; break
    return ev/NS, pay/NS, (int(np.median(days_pay)) if days_pay else None)
print("=== STAGE 4b: FUNDED SIM REPLICATED UNDER ITS OWN RULES (948-day tape, 6,000 sims/cell) ===")
print(f"{'micros':>7}{'flat pass':>11}{'flat payout':>13}{'armed pass':>12}{'armed payout':>14}{'med days':>10}   claimed (921-day): flat payout / armed payout")
claim={8:("83.6%","93.9%"),12:("74.9%","84.1%"),16:("70.0%","81.2%"),20:("67.0%","77.0%")}
for m in (8,12,16,20):
    fe,fp,_=run(FLAT,m); ae,ap,md=run(ARMED,m)
    print(f"{m:>7}{fe:>11.1%}{fp:>13.1%}{ae:>12.1%}{ap:>14.1%}{str(md):>10}   {claim[m][0]} / {claim[m][1]}")
