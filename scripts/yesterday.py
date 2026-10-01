"""What the armed empire did on session-day 2026-09-02 (18:00 Sep 2 -> 17:00 Sep 3 ET)."""
import gzip, json, sys, numpy as np
from collections import defaultdict
QL="/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18"; sys.path.insert(0,QL)
import scripts.conviction_sizing as CS
DAY=sys.argv[1] if len(sys.argv)>1 else "2026-09-02"; COST=0.5
def L(n,c,tag):
    ts=[t for t in (json.loads(l) for l in gzip.open(f"{QL}/output/analysis/{n}","rt")) if (not c) or (t["depth"]==3.0 and t["target_r"]==1.0)]
    for t in ts: t["_b"]=tag
    return ts
def hhmm(h): m=int(round(h*60)); return f"{(18*60+m)//60%24:02d}:{m%60:02d}"
net=lambda t:t["r"]-COST/t["risk"]
for arm in (True,False):
    a="_arm1" if arm else ""
    books=[L(f"pd_va_trades_nqlive_lvall_xr30_sar_through_tf1_ng{a}.jsonl.gz",False,"8-level"),
           L(f"vwap_rev_tf1_retest_nqlive_xr30_dd{a}.jsonl.gz",True,"vwap-sess"),
           L(f"vwap_rev_tf1_retest_nqlive_xr30_nyanc_dd{a}.jsonl.gz",True,"vwap-ny")]
    kept=CS.rail_pass(books); days=sorted(kept); v=np.array([sum(map(net,kept[d])) for d in days])
    ts=sorted(kept.get(DAY,[]), key=lambda t:t["fill_hrs"])
    print("\n"+"="*104); print(f"{'ARMED' if arm else 'FLAT'} — session-day {DAY}  ({len(ts)} trades)   typical day: {v.mean():+.2f}R, {np.mean([len(kept[d]) for d in days]):.0f} trades"); print("="*104)
    print(f"{'fill ET':>8}{'book':>11}{'side':>6}{'level':>10}{'stop':>10}{'risk':>6}{'res':>8}{'r':>7}{'net':>7}{'held':>6}   {'sig ET':>7}")
    for t in ts:
        print(f"{hhmm(t['fill_hrs']):>8}{t['_b']:>11}{'LONG' if t['dir']==1 else 'SHORT':>6}{t['entry']:>10.2f}{t['stop'] if 'stop' in t else t['entry']-t['dir']*t['risk']:>10.2f}{t['risk']:>6.1f}{t['res']:>8}{t['r']:>+7.2f}{net(t):>+7.2f}{t['hold_min']:>5}m   {hhmm(t['t_sig_hrs']):>7}")
    if ts:
        tp=sum(t['res']=='TARGET' for t in ts); st=sum(t['res']=='STOP' for t in ts); sar=sum(t['res']=='SAR' for t in ts)
        dayR=sum(map(net,ts)); pts=sum(t['pts']-0.5 for t in ts)
        print("-"*104)
        print(f"day: {dayR:+.2f}R net   targets {tp}  stops {st}  SAR {sar}   WR {tp/max(tp+st,1):.0%}   = {pts:+.1f} NQ points net of cost = ${pts*2:+,.0f} per micro, ${pts*20:+,.0f} per full NQ")
        rank=int((v>dayR).sum()); print(f"vs history: better than {100*(1-rank/len(v)):.0f}% of the {len(v)} days on the tape")
        byb=defaultdict(float)
        for t in ts: byb[t['_b']]+=net(t)
        print("by book:", "  ".join(f"{k} {r:+.2f}R" for k,r in byb.items()))
    else: print("no trades kept on this day")
