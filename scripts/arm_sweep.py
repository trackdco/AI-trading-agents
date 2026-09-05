"""ARMING THRESHOLD SWEEP on the full empire (three books railed), 2023-26.
Thresholds 0.5 / 0.75 / 1.0 / 1.25 / 1.5 / 2.0 x risk, plus flat (0).
Scored the way arming was adopted: drawdown-matched R/day vs flat, both halves.
A threshold earns nothing unless it beats 1.0 (the adopted value, chosen
BEFORE results as the audit's own tier line) in both halves - otherwise
this is picking noise off a ridge already shown to be flat past 1R.
"""
import sys, gzip, json, numpy as np
QL="/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18"
sys.path.insert(0,QL); import scripts.conviction_sizing as CS
COST=0.5; MID="2024-10-21"
def L(n,c): return [t for t in (json.loads(l) for l in gzip.open(f"{QL}/output/analysis/{n}","rt")) if (not c) or (t["depth"]==3.0 and t["target_r"]==1.0)]
def net(t): return t["r"]-COST/t["risk"]
def dd(v): e=np.cumsum(v); return float((e-np.maximum.accumulate(e)).min())
def emp(a):
    s="" if a is None else f"_arm{a:g}"
    return CS.rail_pass([L(f"pd_va_trades_lvall_xr30_sar_through_tf1_ng{s}.jsonl.gz",False),L(f"vwap_rev_tf1_retest_xr30_dd{s}.jsonl.gz",True),L(f"vwap_rev_tf1_retest_xr30_nyanc_dd{s}.jsonl.gz",True)])
flat=emp(None); days=sorted(flat); vF=np.array([sum(map(net,flat[d])) for d in days]); m=np.array([d<MID for d in days])
print(f"{'arm x risk':<12}{'trades':>8}{'/day':>6}{'EV':>9}{'net R':>8}{'R/day':>7}{'maxDD':>7}{'Sharpe':>7}{'green':>6}   {'dd-matched IS':>14}{'OOS':>8}")
print("-"*100)
print(f"{'flat (0)':<12}{sum(len(v) for v in flat.values()):>8,}{sum(len(v) for v in flat.values())/len(days):>6.1f}{sum(net(t) for d in flat for t in flat[d])/sum(len(v) for v in flat.values()):>+9.4f}{vF.sum():>+8.0f}{vF.mean():>+7.2f}{dd(vF):>+7.1f}{vF.mean()/vF.std():>7.3f}{(vF>0).mean():>6.0%}")
for a in (0.5,0.75,1.0,1.25,1.5,2.0):
    try: k=emp(a)
    except FileNotFoundError as e: print(f"{a:<12} missing {e.filename.split('/')[-1]}"); continue
    v=np.array([sum(map(net,k.get(d,[]))) for d in days]); ts=[t for d in k for t in k[d]]
    sc=abs(dd(vF))/abs(dd(v)); vs=v*sc
    li=vs[m].mean()/vF[m].mean()-1; lo=vs[~m].mean()/vF[~m].mean()-1
    print(f"{a:<12}{len(ts):>8,}{len(ts)/len(days):>6.1f}{sum(map(net,ts))/len(ts):>+9.4f}{v.sum():>+8.0f}{v.mean():>+7.2f}{dd(v):>+7.1f}{v.mean()/v.std():>7.3f}{(v>0).mean():>6.0%}   {li:>+14.1%}{lo:>+8.1%}")
