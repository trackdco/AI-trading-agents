"""GOLD STOP-FLOOR SWEEP on the current stack: 8-level book, flat and armed, dial-on days.

S22 swept floors 1.0-3.0 on the value-area book and found a flat ridge at
1.0-1.5 with >=2pt bleeding in every era; ruled 1.5. This re-asks the
question on the 8-level book with arming, which did not exist then.

HONESTY: this is a sweep on data already read. Picking the best cell here
is fitting. The question is whether the ridge is FLAT (robust: the choice
barely matters) or PEAKED (fragile: one cell wins). Reported by year so a
2025 pick can be checked on 2026, the way S22 did it.
"""
import sys, gzip, json
from collections import defaultdict
import numpy as np
sys.path.insert(0,'/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad')
import gold_empire as G
QL=G.QL; COST=0.15
def net(t): return t["r"]-COST/t["risk"]
def wr(ts):
    tp=sum(t["res"]=="TARGET" for t in ts); st=sum(t["res"]=="STOP" for t in ts); return tp/max(tp+st,1)
def dd(v): e=np.cumsum(v); return float((e-np.maximum.accumulate(e)).min())
def load(floor, arm):
    mr = "" if floor==1.5 else f"_mr{floor:g}"
    a = "_arm1" if arm else ""
    f=f"{QL}/output/analysis/pd_va_trades_gc_lvall{mr}_xr9_sar_through_tf1_ng{a}.jsonl.gz"
    ts=[json.loads(l) for l in gzip.open(f,"rt")]
    return [t for t in ts if G.dial_on.get(t["day"],False)]
print("\n"+"="*100)
print("GOLD 8-LEVEL BOOK — stop floor sweep, dial-on days, depth 0.9 / cap 9 held fixed")
print("="*100)
for arm in (False,True):
    print(f"\n{'ARMED' if arm else 'FLAT'}")
    print(f"  {'floor':<7}{'trades':>8}{'/day':>6}{'WR':>8}{'EV':>9}{'net R':>8}{'R/day':>8}{'maxDD':>8}{'Sharpe':>8}{'floored%':>10}   {'2025 EV (n)':>16}{'2026 EV (n)':>16}")
    for floor in (1.0,1.25,1.5,2.0,2.5):
        try: ts=load(floor,arm)
        except FileNotFoundError: print(f"  {floor:<7} (not run)"); continue
        byd=defaultdict(float)
        for t in ts: byd[t["day"]]+=net(t)
        v=np.array([byd[d] for d in sorted(byd)])
        fl=np.mean([abs(t["risk"]-floor)<1e-6 for t in ts])
        yr={y:[t for t in ts if t["day"].startswith(y)] for y in ("2025","2026")}
        ev=lambda x: sum(map(net,x))/len(x) if x else float('nan')
        print(f"  {floor:<7}{len(ts):>8,}{len(ts)/len(v):>6.1f}{wr(ts):>8.1%}{ev(ts):>+9.4f}{sum(map(net,ts)):>+8.0f}{v.mean():>+8.2f}{dd(v):>+8.1f}{v.mean()/v.std():>8.3f}{fl:>10.0%}   "
              f"{ev(yr['2025']):>+8.4f} ({len(yr['2025']):>5,}){ev(yr['2026']):>+8.4f} ({len(yr['2026']):>5,})")
