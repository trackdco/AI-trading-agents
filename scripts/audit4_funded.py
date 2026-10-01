"""AUDIT STAGE 4 — the funded-account claim: 'armed book carries 16 micros at >=80% pass odds' ($2,000 EOD-trailing drawdown).
Independent block bootstrap on the 948-day armed DAILY POINT P&L (pts, not R): 5-day blocks, 4,000 paths of 60 trading days per path,
MNQ at $2/pt per micro, trailing floor = max(start, running-peak EOD balance) - $2,000, breach if EOD balance <= floor.
Also prints median days-to-$3,000 (eval target). Costs already in pts? NO - pts is raw; subtract 0.5pt/RT cost per trade in $ = 0.5*2*N per trade."""
import json, numpy as np, gzip
from collections import defaultdict
QL="/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18"
D=json.load(open("/tmp/audit_armed_daily.json")); days=D["days"]
# rebuild per-day (pts, trade count) from the kept set used in stage 1 -> re-derive here from dumps with the same rail
def load(n,cell):
    ts=[json.loads(l) for l in gzip.open(f"{QL}/output/analysis/{n}","rt")]
    return [t for t in ts if (not cell) or (t["depth"]==3.0 and t["target_r"]==1.0)]
B=[load("pd_va_trades_lvall_xr30_sar_through_tf1_ng_arm1.jsonl.gz",False),load("vwap_rev_tf1_retest_xr30_dd_arm1.jsonl.gz",True),load("vwap_rev_tf1_retest_xr30_nyanc_dd_arm1.jsonl.gz",True)]
byday=defaultdict(list)
for v in B:
    for t in v: byday[t["day"]].append(t)
pts=[]; cnt=[]
for d in days:
    ts=sorted(byday[d],key=lambda t:(t["fill_hrs"],t["t_sig_hrs"])); op=[]; p=0.0; c=0
    for t in ts:
        f=t["fill_hrs"]; e=f+t["hold_min"]/60; op=[q for q in op if q[1]>f]
        if any(q[2]==t["dir"] and abs(q[3]-t["entry"])<=5.0 for q in op): continue
        if len(op)>=4 or sum(1 for q in op if q[2]==t["dir"])>=3: continue
        op.append((f,e,t["dir"],t["entry"])); p+=t["pts"]; c+=1
    pts.append(p); cnt.append(c)
pts=np.array(pts); cnt=np.array(cnt)
print("=== STAGE 4: FUNDED-ACCOUNT BOOTSTRAP (independent) ===")
print(f"daily point P&L: mean {pts.mean():+.1f}pt  std {pts.std():.1f}  worst {pts.min():+.1f}  trades/day {cnt.mean():.1f}")
rng=np.random.default_rng(11); n=len(pts); BL=5; NP=4000; H=60
def path():
    idx=[]
    while len(idx)<H:
        s=rng.integers(0,n-BL); idx+=list(range(s,s+BL))
    return np.array(idx[:H])
for micros in (4,8,12,16,20,24):
    surv=0; hit3k=[]
    for _ in range(NP):
        ix=path(); daily=(pts[ix]-0.5*cnt[ix])*2*micros   # $ per day net of 0.5pt/RT cost
        bal=0.0; peak=0.0; alive=True; d3=None
        for i,x in enumerate(daily):
            bal+=x; peak=max(peak,bal)
            if d3 is None and bal>=3000: d3=i+1
            if bal<=peak-2000: alive=False; break
        surv+=alive
        if d3: hit3k.append(d3)
    print(f"  {micros:>2} micros: survive 60 days {surv/NP:5.1%}   reach +$3,000 {len(hit3k)/NP:5.1%} (median {int(np.median(hit3k)) if hit3k else '-'} days)   $/day mean {((pts-0.5*cnt)*2*micros).mean():+.0f}")
print("claim on the page: flat 8 micros / armed 16 micros at >=80% survival")
