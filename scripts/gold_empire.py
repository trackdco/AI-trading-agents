"""GOLD EMPIRE — the full modern suite on GC, for the first time.

What gold already had (receipts S22-S27): value-area book, 8-level book, a
volatility dial (trade only when the trailing-20-day median 1m candle >= 1.0pt,
which keeps GC on ~29% of days and captures ~all of its R), and the finding
that 2023-24 is a friction era where the constants cannot clear costs.

What it never had: the two VWAP books, the three-book rail pass, ARMING, and
conviction sizing. This runs all of it, flat and armed, with and without the
dial. The dial is a day-level filter computed from prior days only, so per the
autopsy's structural argument its bucket IS the rule effect.

Preregistered reads (same bars as NQ): arming ADOPT if dd-matched R/day >= +5%
in both halves; a book earns its seat at EV >= +0.08 standalone. Split-half at
the sample midpoint. Cost 0.15pt/RT (S22). Post-hoc on data already read for
the VA book; the VWAP books and arming are first-look but not sealed.
"""
import sys, gzip, json
from collections import defaultdict
import numpy as np, pandas as pd
QL = "/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18"
sys.path.insert(0, QL)
import scripts.conviction_sizing as CS, scripts.offline_briefings as OB
COST, TICK, DIAL_PT = 0.15, 0.10, 1.0

def L(n, cell=None):
    ts=[json.loads(l) for l in gzip.open(f"{QL}/output/analysis/{n}","rt")]
    return [t for t in ts if (cell is None) or (abs(t["depth"]-cell[0])<1e-9 and t["target_r"]==cell[1])]
def net(t): return t["r"]-COST/t["risk"]
def wr(ts):
    tp=sum(t["res"]=="TARGET" for t in ts); st=sum(t["res"]=="STOP" for t in ts); return tp/max(tp+st,1)
def ev(ts): return sum(map(net,ts))/len(ts) if ts else float("nan")
def dd(v): e=np.cumsum(v); return float((e-np.maximum.accumulate(e)).min())

# ---- the dial, causal
b=pd.read_parquet(f"{QL}/data/reference/gc_1m.parquet"); b["mi"]=pd.to_datetime(b.ts_event,utc=True).dt.tz_convert(OB.NY)
b=b.set_index("mi").sort_index(); sess=(b.index-pd.Timedelta(hours=18)).normalize().strftime("%Y-%m-%d")
act=b[(b.index.hour>=2)&(b.index.hour<16)]; asess=pd.Series(sess,index=b.index)[act.index]
daily=(act.high-act.low).groupby(asess.values).median().sort_index()
trail=daily.shift(1).rolling(20,min_periods=20).median()
dial_on={d:bool(v>=DIAL_PT) for d,v in trail.items() if np.isfinite(v)}
print("TICK SCREEN, gold, 02:00-16:00 median 1m candle in ticks (law >=20; NQ 28):")
for y,g in daily.groupby(daily.index.str[:4]): print(f"  {y}: {g.median()/TICK:.1f} ticks   dial on {np.mean([dial_on.get(d,False) for d in g.index]):.0%} of days")

def empire(arm):
    a="_arm1" if arm else ""
    lv=L(f"pd_va_trades_gc_lvall_xr9_sar_through_tf1_ng{a}.jsonl.gz")
    sv=L(f"vwap_rev_tf1_retest_gc_xr9_dd{a}.jsonl.gz",(0.9,1.0)); nv=L(f"vwap_rev_tf1_retest_gc_xr9_nyanc_dd{a}.jsonl.gz",(0.9,1.0))
    return {"8-level":lv,"vwap-session":sv,"vwap-ny":nv}

def series(kept, dial):
    days=[d for d in sorted(kept) if (not dial) or dial_on.get(d,False)]
    return days, np.array([sum(map(net,kept[d])) for d in days])

HDR=f"{'':<26}{'days':>6}{'trades':>8}{'/day':>6}{'WR':>7}{'EV':>8}{'net R':>7}{'R/day':>7}{'maxDD':>7}{'Sharpe':>7}{'green':>6}"
def row(lbl, kept, dial):
    days,v=series(kept,dial); ts=[t for d in days for t in kept[d]]
    if not days: return f"{lbl:<26}   (no days)"
    return (f"{lbl:<26}{len(days):>6}{len(ts):>8,}{len(ts)/len(days):>6.1f}{wr(ts):>7.1%}{ev(ts):>+8.4f}"
            f"{v.sum():>+7.0f}{v.mean():>+7.2f}{dd(v):>+7.1f}{v.mean()/v.std():>7.3f}{(v>0).mean():>6.0%}")

K={}
for arm in (False,True):
    books=empire(arm); K[arm]=CS.rail_pass(list(books.values()))
    if not arm:
        print("\nPER BOOK standalone, flat (seat needs EV >= +0.08):")
        for n,bk in books.items():
            print(f"  {n:<14} n {len(bk):>7,}  WR {wr(bk):.1%}  EV {ev(bk):+.4f}  netR {sum(map(net,bk)):+.0f}   {'SEAT' if ev(bk)>=0.08 else 'below bar'}")
            by=defaultdict(list)
            for t in bk: by[t["day"][:4]].append(t)
            print("     by year: "+"  ".join(f"{y} {ev(v):+.3f}({len(v)})" for y,v in sorted(by.items())))

print("\n"+"="*100); print("GOLD EMPIRE — railed, 2023-01 -> 2026-09"); print("="*100); print(HDR); print("-"*100)
for arm in (False,True):
    for dial in (False,True):
        print(row(("armed" if arm else "flat")+(" + vol dial" if dial else ""), K[arm], dial))
print("\nby year (net R):")
for arm in (False,True):
    for dial in (False,True):
        days,v=series(K[arm],dial); yr=defaultdict(float)
        for d,x in zip(days,v): yr[d[:4]]+=x
        print(f"  {('armed' if arm else 'flat')+(' + dial' if dial else ''):<16}"+"  ".join(f"{y} {r:+.0f}" for y,r in sorted(yr.items())))

print("\nARMING TEST (dd-matched R/day >= +5% both halves):")
for dial in (False,True):
    dF,vF=series(K[False],dial); dA,vA=series(K[True],dial); com=sorted(set(dF)&set(dA))
    vF=np.array([vF[dF.index(d)] for d in com]); vA=np.array([vA[dA.index(d)] for d in com])
    sc=abs(dd(vF))/abs(dd(vA)); vAs=vA*sc; MID=com[len(com)//2]; m=np.array([d<MID for d in com]); lifts=[]
    for h,msk in (("IS",m),("OOS",~m)):
        l=vAs[msk].mean()/vF[msk].mean()-1; lifts.append(l)
        print(f"  {'dial' if dial else 'nodial':<7}{h:<4} flat {vF[msk].mean():+.3f}  armed {vA[msk].mean():+.3f}  dd-matched {vAs[msk].mean():+.3f}  lift {l:+.1%}")
    fl=[t for d in com for t in K[False][d]]; ar=[t for d in com for t in K[True][d]]
    print(f"  {'dial' if dial else 'nodial':<7}raw EV {ev(fl):+.4f} -> {ev(ar):+.4f} ({ev(ar)/ev(fl)-1:+.1%})  maxDD {dd(vF):+.1f} -> {dd(vA):+.1f}   -> {'PASS' if all(x>=0.05 for x in lifts) else 'FAIL'}")
