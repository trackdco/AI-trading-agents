"""AUDIT STAGE 1 — re-derive every headline number for the ARMED NQ EMPIRE with independent code.
Nothing here imports conviction_sizing.rail_pass; the rail is re-implemented from the stated rules."""
import gzip, json, sys, numpy as np, pandas as pd
from collections import defaultdict, Counter
QL="/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18"
COST, FLOOR, CAP, MID = 0.5, 5.0, 30.0, "2024-10-21"
def load(n, cell):
    ts=[json.loads(l) for l in gzip.open(f"{QL}/output/analysis/{n}","rt")]
    return [t for t in ts if (not cell) or (t["depth"]==3.0 and t["target_r"]==1.0)]
B={"8-level":load("pd_va_trades_lvall_xr30_sar_through_tf1_ng_arm1.jsonl.gz",False),
   "vwap-session":load("vwap_rev_tf1_retest_xr30_dd_arm1.jsonl.gz",True),
   "vwap-ny":load("vwap_rev_tf1_retest_xr30_nyanc_dd_arm1.jsonl.gz",True)}
for k,v in B.items():
    for t in v: t["_b"]=k
print("=== STAGE 1: HEADLINE RE-DERIVATION (independent rail) ===")
print("raw books:", {k:len(v) for k,v in B.items()}, "sum", sum(len(v) for v in B.values()))
# --- independent rail: G3 same-dir within FLOOR of an OPEN position; G5 cap 4; G6 same-dir cap 3; chronological by fill then signal
byday=defaultdict(list)
for v in B.values():
    for t in v: byday[t["day"]].append(t)
kept=defaultdict(list); g3=g5=g6=0
for d,ts in byday.items():
    ts.sort(key=lambda t:(t["fill_hrs"],t["t_sig_hrs"])); op=[]
    for t in ts:
        f=t["fill_hrs"]; e=f+t["hold_min"]/60
        op=[p for p in op if p[1]>f]
        if any(p[2]==t["dir"] and abs(p[3]-t["entry"])<=FLOOR for p in op): g3+=1; continue
        if len(op)>=4: g5+=1; continue
        if sum(1 for p in op if p[2]==t["dir"])>=3: g6+=1; continue
        op.append((f,e,t["dir"],t["entry"])); kept[d].append(t)
days=sorted(kept); T=[t for d in days for t in kept[d]]
net=lambda t:t["r"]-COST/t["risk"]
v=np.array([sum(map(net,kept[d])) for d in days]); eq=np.cumsum(v); dd=float((eq-np.maximum.accumulate(eq)).min())
tp=sum(t["res"]=="TARGET" for t in T); st=sum(t["res"]=="STOP" for t in T)
print(f"rail removed: G3 {g3}, G5 {g5}, G6 {g6}")
print(f"CLAIMED  61,194 trades  64.6/day  EV +0.1775  net +10,863  R/day +11.46  maxDD -14.0  Sharpe 1.208  green 91%  WR 66.0%")
print(f"DERIVED  {len(T):,} trades  {len(T)/len(days):.1f}/day  EV {sum(map(net,T))/len(T):+.4f}  net {v.sum():+,.0f}  R/day {v.mean():+.2f}  maxDD {dd:+.1f}  Sharpe {v.mean()/v.std(ddof=0):.3f} (ddof0) / {v.mean()/v.std(ddof=1):.3f} (ddof1)  green {(v>0).mean():.0%}  WR {tp/(tp+st):.1%}  days {len(days)}")
print(f"Sharpe annualised (x sqrt 252): {v.mean()/v.std()*np.sqrt(252):.1f}   <- daily ratio is what the page reports; state this")
print(f"worst day {v.min():+.1f} on {days[int(v.argmin())]}; maxDD == worst day? {abs(dd-v.min())<1e-9}")
# yearly / monthly
yr=defaultdict(float); mo=defaultdict(float)
for d,x in zip(days,v): yr[d[:4]]+=x; mo[d[:7]]+=x
print("CLAIMED by year +2,280 / +2,918 / +3,108 / +2,557 ; DERIVED", {k:round(x) for k,x in sorted(yr.items())})
print(f"months positive {sum(1 for x in mo.values() if x>0)}/{len(mo)} (claimed 45/45)  worst month {min(mo.values()):+.1f} (claimed +20.1)  median {np.median(list(mo.values())):+.1f}")
# split-half dd-matched vs flat (re-derive flat with the same rail)
Bf={"8-level":load("pd_va_trades_lvall_xr30_sar_through_tf1_ng.jsonl.gz",False),"vwap-session":load("vwap_rev_tf1_retest_xr30_dd.jsonl.gz",True),"vwap-ny":load("vwap_rev_tf1_retest_xr30_nyanc_dd.jsonl.gz",True)}
byd2=defaultdict(list)
for vv in Bf.values():
    for t in vv: byd2[t["day"]].append(t)
kf=defaultdict(list)
for d,ts in byd2.items():
    ts.sort(key=lambda t:(t["fill_hrs"],t["t_sig_hrs"])); op=[]
    for t in ts:
        f=t["fill_hrs"]; e=f+t["hold_min"]/60; op=[p for p in op if p[1]>f]
        if any(p[2]==t["dir"] and abs(p[3]-t["entry"])<=FLOOR for p in op): continue
        if len(op)>=4 or sum(1 for p in op if p[2]==t["dir"])>=3: continue
        op.append((f,e,t["dir"],t["entry"])); kf[d].append(t)
df=sorted(kf); vF=np.array([sum(map(net,kf[d])) for d in df]); eqF=np.cumsum(vF); ddF=float((eqF-np.maximum.accumulate(eqF)).min())
TF=[t for d in df for t in kf[d]]
print(f"FLAT derived: {len(TF):,} trades EV {sum(map(net,TF))/len(TF):+.4f} net {vF.sum():+,.0f} R/day {vF.mean():+.2f} maxDD {ddF:+.1f}  (claimed 75,481 / +0.1361 / +10,273 / +10.84 / -18.1)")
com=sorted(set(days)&set(df)); a=np.array([v[days.index(d)] for d in com]); f_=np.array([vF[df.index(d)] for d in com]); m=np.array([d<MID for d in com]); sc=abs(ddF)/abs(dd)
print(f"arming dd-matched lift IS {a[m].mean()*sc/f_[m].mean()-1:+.1%} OOS {a[~m].mean()*sc/f_[~m].mean()-1:+.1%}  (claimed +33.3% / +38.2%)  raw EV lift {sum(map(net,T))/len(T)/(sum(map(net,TF))/len(TF))-1:+.1%} (claimed +30%)")
# --- integrity checks on the armed set
risks=np.array([t["risk"] for t in T])
print(f"\nrisk: min {risks.min()} max {risks.max()} median {np.median(risks)}  floor violations {int((risks<FLOOR-1e-9).sum())}  cap violations {int((risks>CAP+1e-9).sum())}")
print(f"res mix: {dict(Counter(t['res'] for t in T))}")
amb=[t for t in T if t.get("ambig")]; print(f"ambiguous bars: {len(amb)} ({len(amb)/len(T):.2%}); all scored as loss? {all(t['res']=='STOP' and t['r']==-1.0 for t in amb)}")
print(f"r consistency: TARGET r==1.0: {all(t['r']==1.0 for t in T if t['res']=='TARGET')}; STOP r==-1.0: {all(t['r']==-1.0 for t in T if t['res']=='STOP')}; pts==r*risk: {np.max([abs(t['pts']-t['r']*t['risk']) for t in T]):.4f} max abs err")
print(f"fill strictly after signal (fill_hrs > t_sig_hrs - 1min): {all(t['fill_hrs']>=t['t_sig_hrs']-1e-9 for t in T)}; min gap min {min((t['fill_hrs']-t['t_sig_hrs'])*60 for t in T):.1f}")
print(f"holds: min {min(t['hold_min'] for t in T)} max {max(t['hold_min'] for t in T)} min; any exit past 23h session? {any(t['fill_hrs']+t['hold_min']/60>23.0001 for t in T)}")
# news gate: no fills 08:00-09:30 on high-impact days
nf=pd.read_csv(f"{QL}/data/reference/news_archive.csv"); nd=set(nf[(nf.impact=="high")&(nf.time_et>="08:00")&(nf.time_et<"09:30")].date)
viol=[t for t in T if (pd.Timestamp(t["day"])+pd.Timedelta(days=1)).strftime("%Y-%m-%d") in nd and 14.0<=t["fill_hrs"]<15.5]
print(f"news-gate: fills 08:00-09:30 on {len(nd)} high-impact mornings = {len(viol)} (must be 0)")
# duplicate rows within a book, and cross-book same-minute same-level same-dir survivors
dups=sum(len(vv)-len({(t['day'],t['t_sig_hrs'],t['fill_hrs'],t['entry'],t['dir']) for t in vv}) for vv in B.values())
print(f"exact duplicate rows inside books: {dups}")
x=Counter((t['day'],t['fill_hrs'],t['dir'],round(t['entry'])) for t in T); print(f"kept trades sharing day+fill-minute+dir+level (rail leak check): {sum(1 for k,c in x.items() if c>1)}")
# G4 check: vwap fills while a same-dir level position open within FLOOR
lv=[t for t in T if t['_b']=='8-level']; byl=defaultdict(list)
for t in lv: byl[t['day']].append(t)
g4=0
for t in T:
    if t['_b']=='8-level': continue
    for p in byl[t['day']]:
        if p['dir']==t['dir'] and p['fill_hrs']<=t['fill_hrs']<p['fill_hrs']+p['hold_min']/60 and abs(p['entry']-t['entry'])<=FLOOR: g4+=1; break
print(f"G4 check: vwap fills inside an open same-dir level position within {FLOOR}pt: {g4} (should be ~0 after rail)")
json.dump({"days":days,"v":v.tolist(),"pts_by_day":{d:sum(t['pts'] for t in kept[d]) for d in days}}, open("/tmp/audit_armed_daily.json","w"))
print("saved daily series -> /tmp/audit_armed_daily.json")
