"""STAGE 7 — NO-LOOKAHEAD on levels: for prior-day high/low trades, the level must equal the PRIOR session's high or low
computed from bars in [prev 18:00, this 18:00). Also: the signal bar must be AFTER the session open (levels fixed at 18:00)."""
import gzip, json, random, sys, numpy as np, pandas as pd
QL="/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18"; sys.path.insert(0,QL)
import scripts.offline_briefings as OB
random.seed(5)
ts=[json.loads(l) for l in gzip.open(f"{QL}/output/analysis/pd_va_trades_lvall_xr30_sar_through_tf1_ng_arm1.jsonl.gz","rt")]
pdhl=[t for t in ts if t["family"]=="pdhl"]; random.shuffle(pdhl); S=pdhl[:400]
bars=OB.get_bars(); days=sorted({t["day"] for t in ts}); prev={days[i]:days[i-1] for i in range(1,len(days))}
ok=0; bad=[]; fut=0
for t in S:
    d=t["day"]
    if d not in prev: continue
    t0=pd.Timestamp(f"{d} 18:00",tz=OB.NY); p0=pd.Timestamp(f"{prev[d]} 18:00",tz=OB.NY)
    pseg=bars[(bars.index>=p0)&(bars.index<t0)]
    H,L=float(pseg.high.max()),float(pseg.low.min())
    if abs(t["entry"]-H)<1e-6 or abs(t["entry"]-L)<1e-6: ok+=1
    else: bad.append((d,t["entry"],H,L))
    if t["t_sig_hrs"]<=0: fut+=1
print("=== STAGE 7: NO-LOOKAHEAD, prior-day high/low family ===")
print(f"level equals prior SESSION high or low (bars strictly before this session's 18:00 open): {ok}/{ok+len(bad)}")
if bad: print("  mismatches e.g.", bad[:5])
print(f"signals at or before the 18:00 open: {fut} (must be 0)")
# session-anchored VWAP: the band value is frozen at the signal close; check the level lies inside the signal candle's move for a sample
vs=[json.loads(l) for l in gzip.open(f"{QL}/output/analysis/vwap_rev_tf1_retest_xr30_dd_arm1.jsonl.gz","rt")]
vs=[t for t in vs if t["depth"]==3.0 and t["target_r"]==1.0]; random.shuffle(vs); ok2=0; n2=0
for t in vs[:400]:
    t0=pd.Timestamp(f"{t['day']} 18:00",tz=OB.NY); s=bars[(bars.index>=t0)&(bars.index<t0+pd.Timedelta(hours=23))]
    i=int(round(t["t_sig_hrs"]*60))-1
    if not (1<=i<len(s)): continue
    n2+=1; c=float(s.close.iloc[i]); cp=float(s.close.iloc[i-1])
    # close-through: level between prior close and this close, >=3pt (minus tick rounding) beyond the level
    if (t["dir"]==1 and cp<=t["entry"]+0.25 and c>=t["entry"]+3-0.25) or (t["dir"]==-1 and cp>=t["entry"]-0.25 and c<=t["entry"]-3+0.25): ok2+=1
print(f"session-VWAP book: frozen band level sits between the prior close and a >=3pt close-through: {ok2}/{n2}")
