"""AUDIT STAGE 5 — selection grid on the value-area book: is depth 3.0 / 1R really the best cell, and is the ridge monotone?"""
import gzip, json, numpy as np
from collections import defaultdict
QL="/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18"
ts=[json.loads(l) for l in gzip.open(f"{QL}/output/analysis/pd_va_trades_xr30_sar_through_tf1_ng.jsonl.gz","rt")]
g=defaultdict(list)
for t in ts: g[(t["depth"],t["target_r"])].append(t["r"]-0.5/t["risk"])
print("=== STAGE 5: VA-BOOK GRID (net R total / EV per trade) ===")
deps=sorted({k[0] for k in g}); tgs=sorted({k[1] for k in g})
print(f"{'depth/target':<14}"+"".join(f"{tg:>16}" for tg in tgs))
for dp in deps: print(f"{dp:<14}"+"".join(f"{sum(g[(dp,tg)]):>+8.0f}/{np.mean(g[(dp,tg)]):+.3f}" for tg in tgs))
best=max(g,key=lambda k:sum(g[k])); print(f"best cell by net R: {best} (certified cell is (3.0, 1.0))")
print("1R best at every depth?", all(max(tgs,key=lambda tg:sum(g[(dp,tg)]))==1.0 for dp in deps))
print("net R monotone in depth at 1R?", all(sum(g[(deps[i],1.0)])<=sum(g[(deps[i+1],1.0)]) for i in range(len(deps)-1)), [round(sum(g[(dp,1.0)])) for dp in deps])
