"""AUDIT STAGE 2 — replay a random sample of ARMED trades against the raw 1m bars.
For each trade: signal candle closed >=3pt through the level (and prior close on the other side);
stop = one tick past the signal candle (prior candle too if open within 5pt), floor 5, cap 30;
arming: some bar in [signal candle, fill) ran >=1x risk past the level, and the fill bar is STRICTLY after it;
fill bar traded one tick THROUGH the level; exit: TARGET/STOP first-touch order from the fill bar (ties -> STOP);
SAR/FLAT: r == d*(close at exit bar - E)/risk. Engine conventions from pd_va_backtest.simulate_day."""
import gzip, json, sys, random, numpy as np, pandas as pd
QL="/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18"
sys.path.insert(0,QL); import scripts.offline_briefings as OB
TICK, FLOOR, CAP, DEPTH = 0.25, 5.0, 30.0, 3.0
random.seed(7)
def load(n, cell):
    ts=[json.loads(l) for l in gzip.open(f"{QL}/output/analysis/{n}","rt")]
    return [t for t in ts if (not cell) or (t["depth"]==3.0 and t["target_r"]==1.0)]
S=[]
for nm,n,c in (("8-level","pd_va_trades_lvall_xr30_sar_through_tf1_ng_arm1.jsonl.gz",False),("vwap-session","vwap_rev_tf1_retest_xr30_dd_arm1.jsonl.gz",True),("vwap-ny","vwap_rev_tf1_retest_xr30_nyanc_dd_arm1.jsonl.gz",True)):
    ts=load(n,c); random.shuffle(ts); S+= [dict(t,_b=nm) for t in ts[:1000]]
bars=OB.get_bars()
cache={}
def sess(day):
    if day not in cache:
        t0=pd.Timestamp(f"{day} 18:00",tz=OB.NY); s=bars[(bars.index>=t0)&(bars.index<t0+pd.Timedelta(hours=23))]
        cache[day]=(s.index.asi8, s.open.to_numpy(), s.high.to_numpy(), s.low.to_numpy(), s.close.to_numpy())
    return cache[day]
fails={}; n_ok=0; checks=0; ties_unflagged_books=set(); tie_stop_ok=[]
def fail(k,t,msg):
    fails.setdefault(k,[]); fails[k].append((t["_b"],t["day"],t["t_sig_hrs"],msg))
for t in S:
    ts,op,hi,lo,cl=sess(t["day"]); n=len(ts)
    E,d,risk=t["entry"],t["dir"],t["risk"]; stop=t.get("stop", E-d*risk)
    t_sig=ts[0]+int(round(t["t_sig_hrs"]*60))*60_000_000_000; start=int(np.searchsorted(ts,t_sig)); si=start-1   # SNAP to the minute: dump rounds hrs to 3dp (+-1.8s)
    fill=int(np.searchsorted(ts, ts[0]+int(round(t["fill_hrs"]*60))*60_000_000_000))
    ok=True
    # (1) signal candle close-through (levels are exact for 8-level; band values rounded to tick for vwap)
    checks+=1
    if not (0<=si<n): fail("index",t,"signal bar out of session"); continue
    thru_ok = (cl[si]>=E+DEPTH-TICK) if d==1 else (cl[si]<=E-DEPTH+TICK)
    prev_ok = (cl[si-1]<=E+TICK) if d==1 else (cl[si-1]>=E-TICK)   # prior close on the other side (tick slack for vwap rounding)
    if not thru_ok: ok=False; fail("close_through",t,f"close {cl[si]} vs level {E}")
    if si>=1 and not prev_ok and t["_b"]=="8-level": ok=False; fail("prev_close_side",t,f"prev close {cl[si-1]} vs level {E}")
    # (2) stop rule
    if t["_b"]=="8-level":
        use_prev = abs(op[si]-E)<FLOOR
        if d==1: ref=min(lo[si],lo[si-1]) if (use_prev and si>=1) else lo[si]; s_exp=ref-TICK; s_exp=min(s_exp,E-FLOOR) if E-s_exp<FLOOR else s_exp
        else:    ref=max(hi[si],hi[si-1]) if (use_prev and si>=1) else hi[si]; s_exp=ref+TICK; s_exp=max(s_exp,E+FLOOR) if s_exp-E<FLOOR else s_exp
        if abs(s_exp-stop)>1e-6: ok=False; fail("stop_rule",t,f"expected {s_exp} got {stop}")
    if not (FLOOR-1e-9<=risk<=CAP+1e-9): ok=False; fail("risk_bounds",t,f"risk {risk}")
    if abs(abs(E-stop)-risk)>1e-6: ok=False; fail("risk_calc",t,f"|E-stop| {abs(E-stop)} vs risk {risk}")
    # (3) arming: first bar in [si, fill) with run past level >= 1*risk; fill must be > that bar
    thr=E+d*1.0*risk; seg=hi[si:fill] if d==1 else lo[si:fill]
    armed=(seg>=thr) if d==1 else (seg<=thr)
    if not armed.any(): ok=False; fail("not_armed_before_fill",t,f"no bar in [{si},{fill}) reached {thr}")
    else:
        ab=si+int(np.argmax(armed))
        if not fill>ab: ok=False; fail("fill_not_after_arming",t,f"arm bar {ab} fill {fill}")
        # and the fill bar is the FIRST touch after live=ab+1
        live=ab+1; seg2=lo[live:fill+1] if d==1 else hi[live:fill+1]; touch=(seg2<=E-TICK) if d==1 else (seg2>=E+TICK)
        if not touch.any() or live+int(np.argmax(touch))!=fill: ok=False; fail("fill_not_first_touch",t,f"live {live} fill {fill}")
    # (4) fill bar traded one tick THROUGH
    if not ((lo[fill]<=E-TICK) if d==1 else (hi[fill]>=E+TICK)): ok=False; fail("fill_not_through",t,f"fill bar lo/hi {lo[fill]}/{hi[fill]} vs E {E}")
    # (5) exit
    tgt=E+d*risk; w_lo,w_hi=lo[fill:],hi[fill:]
    s_hit=(w_lo<=stop) if d==1 else (w_hi>=stop); t_hit=(w_hi>=tgt) if d==1 else (w_lo<=tgt)
    s_idx=fill+int(np.argmax(s_hit)) if s_hit.any() else n; t_idx=fill+int(np.argmax(t_hit)) if t_hit.any() else n
    ex=fill+t["hold_min"]
    if t["res"]=="TARGET":
        if not (t_idx<s_idx): ok=False; fail("target_but_stop_first_or_tie",t,f"s {s_idx} t {t_idx}")
        elif t_idx!=ex: ok=False; fail("target_exit_bar",t,f"t_idx {t_idx} vs fill+hold {ex}")
    elif t["res"]=="STOP":
        if not (s_idx<=t_idx and s_idx<n): ok=False; fail("stop_but_target_first",t,f"s {s_idx} t {t_idx}")
        elif s_idx!=ex: ok=False; fail("stop_exit_bar",t,f"s_idx {s_idx} vs fill+hold {ex}")
        if s_idx==t_idx and "ambig" in t and not t["ambig"]: ok=False; fail("ambig_not_flagged",t,"")
        if s_idx==t_idx and "ambig" not in t: ties_unflagged_books.add(t["_b"]); tie_stop_ok.append(t["res"]=="STOP" and t["r"]==-1.0)
    elif t["res"] in ("SAR","FLAT"):
        if ex>=n: ex=n-1
        # engine: SAR exit index = bar AFTER the opposing signal candle; price = that candle's close = cl[ex-1]. FLAT = cl[n-1].
        px = cl[ex-1] if (t["res"]=="SAR" and ex-1>=fill) else cl[ex]
        r_exp=d*(px-E)/risk
        if abs(r_exp-t["r"])>0.02: ok=False; fail("sar_flat_r",t,f"expected {r_exp:+.3f} got {t['r']:+.3f}")
        if min(s_idx,t_idx)<ex and t["res"]=="SAR": ok=False; fail("sar_after_stop_or_target",t,f"first touch {min(s_idx,t_idx)} exit {ex}")
    if ok: n_ok+=1
print(f"=== STAGE 2: BAR REPLAY of {len(S):,} random armed trades (1,000 per book) ===")
print(f"fully consistent with the bars: {n_ok:,} / {len(S):,} = {n_ok/len(S):.2%}")
for k,v in sorted(fails.items(), key=lambda x:-len(x[1])):
    print(f"  {k:<32}{len(v):>5}   e.g. {v[0]}")
if not fails: print("  no discrepancies of any kind")
print(f"schema note: books without an ambig field: {sorted(ties_unflagged_books)}; their tie bars scored STOP/-1: {sum(tie_stop_ok)}/{len(tie_stop_ok)}")
from collections import Counter; print("res mix of sample:", dict(Counter(t['res'] for t in S)))
