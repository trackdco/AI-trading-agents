"""Cost of an engine-side daily loss cap (stop trading for the day once cum P&L <= -cap). Union armed 2020-26, 8 micros."""
import gzip, json, numpy as np
from collections import defaultdict
QL="/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18"
def load(n,c):
    ts=[json.loads(l) for l in gzip.open(f"{QL}/output/analysis/{n}","rt")]
    return [t for t in ts if (not c) or (t["depth"]==3.0 and t["target_r"]==1.0)]
def daypaths(files):
    byday=defaultdict(list)
    for n,c in files:
        for t in load(n,c): byday[t["day"]].append(t)
    out={}
    for d,ts in byday.items():
        ts.sort(key=lambda t:(t["fill_hrs"],t["t_sig_hrs"])); op=[]; path=[]
        for t in ts:
            f=t["fill_hrs"]; e=f+t["hold_min"]/60; op=[q for q in op if q[1]>f]
            if any(q[2]==t["dir"] and abs(q[3]-t["entry"])<=5.0 for q in op): continue
            if len(op)>=4 or sum(1 for q in op if q[2]==t["dir"])>=3: continue
            op.append((f,e,t["dir"],t["entry"])); path.append((e,t["pts"]-0.5))
        path.sort(); out[d]=np.cumsum([p for _,p in path])  # realised P&L in exit order
    return out
D={**daypaths([("pd_va_trades_nq20a_lvall_xr30_sar_through_tf1_arm1.jsonl.gz",False),("vwap_rev_tf1_retest_nq20a_ng0_xr30_dd_arm1.jsonl.gz",True),("vwap_rev_tf1_retest_nq20a_ng0_xr30_nyanc_dd_arm1.jsonl.gz",True)]),
   **daypaths([("pd_va_trades_lvall_xr30_sar_through_tf1_ng_arm1.jsonl.gz",False),("vwap_rev_tf1_retest_xr30_dd_arm1.jsonl.gz",True),("vwap_rev_tf1_retest_xr30_nyanc_dd_arm1.jsonl.gz",True)])}
M=8; paths=[D[d]*2*M for d in sorted(D)]; full=np.array([p[-1] if len(p) else 0 for p in paths])
print(f"8 micros, {len(paths)} days, no cap: mean ${full.mean():,.0f}/day, worst ${full.min():,.0f}, days <-$1,200: {np.mean(full<-1200):.1%}, days <-$2,000: {np.mean(full<-2000):.2%}")
for cap in (800,1000,1200,1500,2000):
    capped=[]
    for p in paths:
        if len(p)==0: capped.append(0); continue
        hit=np.where(p<=-cap)[0]; capped.append(p[hit[0]] if len(hit) else p[-1])
    c=np.array(capped)
    print(f"cap -${cap:>5}: mean ${c.mean():,.0f}/day ({c.mean()/full.mean()-1:+.1%}), worst ${c.min():,.0f}, days hitting cap {np.mean(c<=-cap):.1%}, days <-$2,000 {np.mean(c<-2000):.2%}")
