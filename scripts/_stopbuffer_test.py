#!/usr/bin/env python3
"""Test placing the stop N points BEYOND the rejection wick (extra room vs the current
tip-of-wick placement). Re-simulates the champion books over Feb-Jul 2026. Same entries
(min_stop floor dropped so the buffer is the only change), wider stops -> different fates."""
import ast, sys
from datetime import time as dtime
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backtest.engine import load_backtest_config, simulate
from src.engine.triggers import Trigger

NY="America/New_York"; MONTHS=["2026-02","2026-03","2026-04","2026-05","2026-06","2026-07"]
DATA="data/reference/nq_1m_feb_jul2026.parquet"

def load_triggers(buf):
    out=[]
    for p in ["output/triggers_feb_ob.csv","output/triggers_marjul_ob.csv"]:
        for r in pd.read_csv(p).to_dict("records"):
            ct=r.get("cluster_types"); r["cluster_types"]=ast.literal_eval(ct) if isinstance(ct,str) else []
            t=Trigger(**{k:v for k,v in r.items() if k!="session_day"})
            if t.pattern=="unclassified": continue
            sgn=1 if t.direction=="long" else -1
            # move stop BEYOND the wick: further from entry (long stop lower, short stop higher)
            if t.stop_ref is not None:
                t.stop_ref = t.stop_ref - sgn*buf
            if getattr(t,"ob_stop",None) is not None:
                t.ob_stop = t.ob_stop - sgn*buf
            out.append(t)
    return out

def champion(buf):
    df=pd.read_parquet(DATA)
    V=pd.read_csv("output/regime_vector.csv")
    war={r.day for _,r in V.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20>=0.5}
    cfg0=load_backtest_config()
    UNCAP=cfg0.model_copy(update={"win_start":dtime(8,0),"win_end":dtime(10,15),
        "max_trades_per_day":6,"min_stop_points":0.25,"post_open_min_stop":0.0})
    E3=UNCAP.model_copy(update={"mgmt_variant":"V8"}); E4=UNCAP.model_copy(update={"entry_variant":"E4"})
    allt=load_triggers(buf); rows=[]
    for m in MONTHS:
        end=pd.Timestamp((pd.Timestamp(m+"-01",tz=NY)+pd.offsets.MonthBegin(1)).tz_localize(None),tz=NY)
        seg=df[df.ts_event<=end].reset_index(drop=True)
        for book,wo in [(E3,False),(E4,True)]:
            trigs=[t for t in allt if t.ts[:7]==m]
            if wo: trigs=[t for t in trigs if t.ts[:10] in war and abs(t.close-t.stop_ref)<=15.0+buf]
            else:  trigs=[t for t in trigs if t.ts[:10] not in war]
            tr,_,_=simulate(seg,trigs,book)
            for r in tr: rows.append(dict(date=r.trade_date,fill_ts=r.fill_ts,dollars=r.dollars,
                risk=abs(r.entry-r.stop_initial),pts=(r.dollars/ (20* (1)) ) ))
    d=pd.DataFrame(rows)
    if d.empty: return d
    d=d.sort_values("fill_ts").groupby("date",group_keys=False).head(2)  # champion cap = first 2/day
    return d

print("buffer  trades  win%   net$     avgR    @ $300 risk")
for buf in [0,3,5,10]:
    d=champion(buf)
    if d.empty: print(f"{buf:>4}pt   (none)"); continue
    d["R"]=np.where(d.risk>0, (d.dollars/20)/d.risk, 0)  # dollars/20 = points (1 contract $20/pt)
    win=(d.dollars>0).mean()*100
    pnl300=(d["R"]*300).sum()
    print(f"{buf:>4}pt   {len(d):4d}   {win:4.0f}   {d.dollars.sum():+7.0f}   {d['R'].mean():+.2f}   {pnl300:+8.0f}")
