"""STAGE 6 — re-derive the holdout / replication arming claims with the independent rail."""
import gzip, json, numpy as np
from collections import defaultdict
QL="/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18"
def load(n,cell,frm=None,to=None):
    ts=[json.loads(l) for l in gzip.open(f"{QL}/output/analysis/{n}","rt")]
    return [t for t in ts if ((not cell) or (t["depth"]==3.0 and t["target_r"]==1.0)) and (frm is None or t["day"]>=frm) and (to is None or t["day"]<=to)]
def rail(books):
    byday=defaultdict(list)
    for v in books:
        for t in v: byday[t["day"]].append(t)
    kept=defaultdict(list)
    for d,ts in byday.items():
        ts.sort(key=lambda t:(t["fill_hrs"],t["t_sig_hrs"])); op=[]
        for t in ts:
            f=t["fill_hrs"]; e=f+t["hold_min"]/60; op=[q for q in op if q[1]>f]
            if any(q[2]==t["dir"] and abs(q[3]-t["entry"])<=5.0 for q in op): continue
            if len(op)>=4 or sum(1 for q in op if q[2]==t["dir"])>=3: continue
            op.append((f,e,t["dir"],t["entry"])); kept[d].append(t)
    return kept
net=lambda t:t["r"]-0.5/t["risk"]; dd=lambda v:float((np.cumsum(v)-np.maximum.accumulate(np.cumsum(v))).min())
def test(era, files, frm=None, to=None, claim=""):
    kf=rail([load(n.format(a=""),c,frm,to) for n,c in files]); ka=rail([load(n.format(a="_arm1"),c,frm,to) for n,c in files])
    days=sorted(set(kf)&set(ka)); vF=np.array([sum(map(net,kf[d])) for d in days]); vA=np.array([sum(map(net,ka[d])) for d in days])
    MID=days[len(days)//2]; m=np.array([d<MID for d in days]); sc=abs(dd(vF))/abs(dd(vA)); vs=vA*sc
    TF=[t for d in days for t in kf[d]]; TA=[t for d in days for t in ka[d]]
    print(f"{era}: flat EV {sum(map(net,TF))/len(TF):+.4f} maxDD {dd(vF):+.1f} | armed EV {sum(map(net,TA))/len(TA):+.4f} maxDD {dd(vA):+.1f} | dd-matched IS {vs[m].mean()/vF[m].mean()-1:+.1%} OOS {vs[~m].mean()/vF[~m].mean()-1:+.1%}   claimed: {claim}")
print("=== STAGE 6: HOLDOUT ARMING CLAIMS, INDEPENDENT RAIL ===")
test("2020-22", [("pd_va_trades_nq20a_lvall_xr30_sar_through_tf1{a}.jsonl.gz",False),("vwap_rev_tf1_retest_nq20a_ng0_xr30_dd{a}.jsonl.gz",True),("vwap_rev_tf1_retest_nq20a_ng0_xr30_nyanc_dd{a}.jsonl.gz",True)], claim="flat +0.1348/-39.4, armed +0.1666/-30.1, lift +29.0%/+34.2%")
test("2017-19", [("pd_va_trades_nq17a_lvall_xr30_sar_through_tf1{a}.jsonl.gz",False),("vwap_rev_tf1_retest_nq17a_ng0_xr30_dd{a}.jsonl.gz",True),("vwap_rev_tf1_retest_nq17a_ng0_xr30_nyanc_dd{a}.jsonl.gz",True)], "2017-01-01","2019-12-31", claim="flat +0.0700/-84.8, armed +0.1031/-55.4, lift +135.7%/+71.9%")
# the VA-book holdout headline
va=[t for t in load("pd_va_trades_nq20a_xr30_sar_through_tf1_ng.jsonl.gz",True)]
tp=sum(t["res"]=="TARGET" for t in va); st=sum(t["res"]=="STOP" for t in va)
print(f"2020-22 VA book: n {len(va):,} WR {tp/(tp+st):.1%} EV {sum(map(net,va))/len(va):+.4f} netR {sum(map(net,va)):+.0f}   claimed: 5,478 / 65.4% / +0.1354 / +742")
va=[t for t in load("pd_va_trades_nq17a_xr30_sar_through_tf1.jsonl.gz",True,"2017-01-01","2019-12-31")]
tp=sum(t["res"]=="TARGET" for t in va); st=sum(t["res"]=="STOP" for t in va)
print(f"2017-19 VA book: n {len(va):,} WR {tp/(tp+st):.1%} EV {sum(map(net,va))/len(va):+.4f}   claimed: 1,385 / 62.7% / +0.0740 (FAIL vs +0.08)")
