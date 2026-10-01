"""DISPLACEMENT DIRECTION — is the close-through WITH or AGAINST the session's drift?

Displacement itself (price ran past the level before the retest) is always
in the trade's own direction by construction. What is not yet tested is the
direction of that move relative to where the session already is:
  WITH drift    : long above the session open / short below it  (continuation)
  AGAINST drift : long below the session open / short above it  (fade)
Also relative to the prior session's close (the overnight gap side).
Both are known before the fill - causal. Armed empire, 2020-22 and 2023-26,
split-half within each. Reading bar: a feature only matters if the split is
the same sign in all four half-cells and >= 0.03R; otherwise NULL.
Even a survivor would be a FILTER, and every filter has died - so the
honest ceiling is a sizing input, never a cut.
"""
import sys, gzip, json, numpy as np, pandas as pd
from collections import defaultdict
QL="/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18"
sys.path.insert(0,QL); import scripts.conviction_sizing as CS, scripts.offline_briefings as OB
COST=0.5
def L(n,c): return [t for t in (json.loads(l) for l in gzip.open(f"{QL}/output/analysis/{n}","rt")) if (not c) or (t["depth"]==3.0 and t["target_r"]==1.0)]
def net(t): return t["r"]-COST/t["risk"]
def wr(ts):
    tp=sum(t["res"]=="TARGET" for t in ts); st=sum(t["res"]=="STOP" for t in ts); return tp/max(tp+st,1)
def ev(ts): return sum(map(net,ts))/len(ts) if ts else float('nan')
ERAS={"2020-22":(f"{QL}/data/reference/nq_2020_2022_1m.parquet","pd_va_trades_nq20a_lvall_xr30_sar_through_tf1_arm1.jsonl.gz","vwap_rev_tf1_retest_nq20a_ng0_xr30_dd_arm1.jsonl.gz","vwap_rev_tf1_retest_nq20a_ng0_xr30_nyanc_dd_arm1.jsonl.gz"),
      "2023-26":(None,"pd_va_trades_lvall_xr30_sar_through_tf1_ng_arm1.jsonl.gz","vwap_rev_tf1_retest_xr30_dd_arm1.jsonl.gz","vwap_rev_tf1_retest_xr30_nyanc_dd_arm1.jsonl.gz")}
def bars(p):
    if p is None: return OB.get_bars()
    b=pd.read_parquet(p); b["mi"]=pd.to_datetime(b.ts_event,utc=True).dt.tz_convert(OB.NY); return b.set_index("mi").sort_index()
print("DISPLACEMENT DIRECTION — armed empire, EV/trade (n)")
for era,(bp,lv,sv,nv) in ERAS.items():
    b=bars(bp); kept=CS.rail_pass([L(lv,False),L(sv,True),L(nv,True)]); days=sorted(kept); MID=days[len(days)//2]
    opens={}; pclose={}; prev=None
    for d in days:
        t0=pd.Timestamp(f"{d} 18:00",tz=OB.NY); s=b[(b.index>=t0)&(b.index<t0+pd.Timedelta(hours=23))]
        if len(s): opens[d]=float(s.open.iloc[0]); pclose[d]=float(prev) if prev is not None else None; prev=s.close.iloc[-1]
    cells=defaultdict(lambda: defaultdict(list))
    for d in days:
        for t in kept[d]:
            h="IS" if d<MID else "OOS"
            wd = "WITH drift" if (t["entry"]>opens[d])==(t["dir"]==1) else "AGAINST drift"
            cells["vs session open"][(wd,h)].append(t)
            if pclose.get(d) is not None:
                wg = "WITH gap side" if (t["entry"]>pclose[d])==(t["dir"]==1) else "AGAINST gap side"
                cells["vs prior close"][(wg,h)].append(t)
    for feat,cd in cells.items():
        print(f"\n{era} — {feat}")
        print(f"  {'':<18}{'IS':>22}{'OOS':>22}{'all':>22}{'WR':>7}")
        labs=sorted({k[0] for k in cd})
        rows={}
        for lab in labs:
            a=cd[(lab,"IS")]; o=cd[(lab,"OOS")]; al=a+o; rows[lab]=(ev(a),ev(o),ev(al))
            print(f"  {lab:<18}{ev(a):>+9.4f} ({len(a):>6,}){ev(o):>+9.4f} ({len(o):>6,}){ev(al):>+9.4f} ({len(al):>6,}){wr(al):>7.1%}")
        (l1,l2)=labs; d_is=rows[l1][0]-rows[l2][0]; d_oos=rows[l1][1]-rows[l2][1]
        print(f"  spread {l1} minus {l2}: IS {d_is:+.4f}  OOS {d_oos:+.4f}")
