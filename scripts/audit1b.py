"""Chase the three stage-1 flags: ambiguous-bar scoring, same-minute pairs, G4 boundary."""
import gzip, json, numpy as np
from collections import defaultdict, Counter
QL="/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18"
COST,FLOOR=0.5,5.0
def load(n,cell):
    ts=[json.loads(l) for l in gzip.open(f"{QL}/output/analysis/{n}","rt")]
    return [t for t in ts if (not cell) or (t["depth"]==3.0 and t["target_r"]==1.0)]
B={"8-level":load("pd_va_trades_lvall_xr30_sar_through_tf1_ng_arm1.jsonl.gz",False),"vwap-session":load("vwap_rev_tf1_retest_xr30_dd_arm1.jsonl.gz",True),"vwap-ny":load("vwap_rev_tf1_retest_xr30_nyanc_dd_arm1.jsonl.gz",True)}
for k,v in B.items():
    for t in v: t["_b"]=k
byday=defaultdict(list)
for v in B.values():
    for t in v: byday[t["day"]].append(t)
kept=defaultdict(list)
for d,ts in byday.items():
    ts.sort(key=lambda t:(t["fill_hrs"],t["t_sig_hrs"])); op=[]
    for t in ts:
        f=t["fill_hrs"]; e=f+t["hold_min"]/60; op=[p for p in op if p[1]>f]
        if any(p[2]==t["dir"] and abs(p[3]-t["entry"])<=FLOOR for p in op): continue
        if len(op)>=4 or sum(1 for p in op if p[2]==t["dir"])>=3: continue
        op.append((f,e,t["dir"],t["entry"])); kept[d].append(t)
T=[t for d in kept for t in kept[d]]; net=lambda t:t["r"]-COST/t["risk"]
print("=== FLAG A: ambiguous bars (stop AND target inside the same bar) ===")
amb=[t for t in T if t.get("ambig")]
print("res mix of ambiguous trades:", dict(Counter(t["res"] for t in amb)))
print("any ambiguous trade scored as TARGET (+1)?", any(t["res"]=="TARGET" for t in amb))
sar_amb=[t for t in amb if t["res"]=="SAR"]; print(f"ambiguous resolved by SAR pre-emption: {len(sar_amb)}, their mean r {np.mean([t['r'] for t in sar_amb]) if sar_amb else 0:+.3f} (SAR fires on an opposing CLOSE at the bar boundary before the touch bar; scored at that close, never at target)")
print("\n=== FLAG B: kept pairs sharing day + fill minute + direction + level ===")
grp=defaultdict(list)
for t in T: grp[(t["day"],t["fill_hrs"],t["dir"],round(t["entry"]))].append(t)
pairs=[v for v in grp.values() if len(v)>1]
first_hold0=sum(1 for v in pairs if min(v,key=lambda t:t["t_sig_hrs"])["hold_min"]==0)
diff_level=sum(1 for v in pairs if len({t["entry"] for t in v})>1)
print(f"groups: {len(pairs)}; earlier trade held 0 minutes (in-and-out inside the fill bar): {first_hold0}; levels differ by <1pt but not equal: {diff_level}")
second=[sorted(v,key=lambda t:t["t_sig_hrs"])[1] for v in pairs]
print(f"the later trade of each pair: n {len(second)}, net R {sum(map(net,second)):+.1f} of empire {sum(map(net,T)):+.0f} = {sum(map(net,second))/sum(map(net,T)):.2%}; WR {sum(t['res']=='TARGET' for t in second)/max(sum(t['res'] in ('TARGET','STOP') for t in second),1):.1%}")
print("if ALL later-of-pair trades were removed (strictest reading of G3): net R", f"{sum(map(net,T))-sum(map(net,second)):+.0f}")
print("\n=== FLAG C: the 3 G4 boundary cases ===")
lv=[t for t in T if t['_b']=='8-level']; byl=defaultdict(list)
for t in lv: byl[t['day']].append(t)
for t in T:
    if t['_b']=='8-level': continue
    for p in byl[t['day']]:
        if p['dir']==t['dir'] and p['fill_hrs']<=t['fill_hrs']<p['fill_hrs']+p['hold_min']/60 and abs(p['entry']-t['entry'])<=FLOOR:
            print(f"  {t['day']} {t['_b']} fill {t['fill_hrs']} entry {t['entry']} r {t['r']:+.2f} | level fill {p['fill_hrs']} hold {p['hold_min']}m entry {p['entry']} gap {abs(p['entry']-t['entry']):.2f}pt"); break
