"""Diff the blind agent's trades against the engine's armed VA-book dump, trade by trade."""
import gzip, json, sys, pandas as pd
from collections import Counter, defaultdict
QL="/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18"
ref=[json.loads(l) for l in gzip.open(f"{QL}/output/analysis/pd_va_trades_xr30_sar_through_tf1_ng_arm1.jsonl.gz","rt")]
ref=[t for t in ref if t["depth"]==3.0 and t["target_r"]==1.0]
bl=[json.loads(l) for l in open("/tmp/blind/trades.jsonl")]
def key_ref(t):  # (day, signal minute from 18:00, dir, level)
    return (t["day"], int(round(t["t_sig_hrs"]*60)), t["dir"], round(t["entry"]*4)/4)
def key_bl(t):
    ts=pd.Timestamp(t["t_sig"]); t0=pd.Timestamp(f"{t['day']} 18:00",tz=ts.tz if ts.tzinfo else "America/New_York")
    if ts.tzinfo is None: ts=ts.tz_localize("America/New_York")
    return (t["day"], int(round((ts-t0).total_seconds()/60)), t["dir"], round(t["level"]*4)/4)
R={key_ref(t):t for t in ref}; B={key_bl(t):t for t in bl}
both=set(R)&set(B); only_r=set(R)-set(B); only_b=set(B)-set(R)
net=lambda t: t["r"]-0.5/t["risk"]
print(f"engine {len(ref):,} trades   blind {len(bl):,} trades   matched on (day, signal minute, dir, level): {len(both):,}")
print(f"  only in engine: {len(only_r):,}   only in blind: {len(only_b):,}")
same=sum(1 for k in both if R[k]["res"]==B[k]["res"] and abs(R[k]["r"]-B[k]["r"])<1e-3 and abs(R[k]["risk"]-B[k]["risk"])<1e-6)
print(f"  of matched: identical res, r and risk: {same:,} ({same/max(len(both),1):.1%})")
dif=[k for k in both if not (R[k]["res"]==B[k]["res"] and abs(R[k]["r"]-B[k]["r"])<1e-3 and abs(R[k]["risk"]-B[k]["risk"])<1e-6)]
print("  mismatch types:", Counter((R[k]["res"],B[k]["res"]) for k in dif).most_common(6))
print(f"\nengine: EV {sum(map(net,ref))/len(ref):+.4f}  netR {sum(map(net,ref)):+.0f}   blind: EV {sum(map(net,bl))/len(bl):+.4f}  netR {sum(map(net,bl)):+.0f}")
byd=defaultdict(lambda:[0,0])
for k in only_r: byd[k[0]][0]+=1
for k in only_b: byd[k[0]][1]+=1
worst=sorted(byd.items(), key=lambda x:-(x[1][0]+x[1][1]))[:8]
print("days with most unmatched (engine-only, blind-only):", worst)
if dif[:5]: print("example mismatches:", [(k, R[k]["res"], R[k]["r"], B[k]["res"], B[k]["r"]) for k in dif[:5]])
