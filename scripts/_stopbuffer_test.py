#!/usr/bin/env python3
"""Test placing the stop N points BEYOND the rejection wick vs the current tip-of-wick.
Simulates each champion book ONCE over the full Feb-Jul 2026 range per buffer (fast),
then builds the champion (E3 non-WAR + E4 WAR, first-2-by-time/day). Same entries,
min-stop floor dropped so the buffer is the only change."""
import ast, sys
from datetime import time as dtime
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backtest.engine import load_backtest_config, simulate
from src.engine.triggers import Trigger

NY="America/New_York"
DATA="data/reference/nq_1m_feb_jul2026.parquet"

def load_triggers(buf):
    out=[]
    for p in ["output/triggers_feb_ob.csv","output/triggers_marjul_ob.csv"]:
        for r in pd.read_csv(p).to_dict("records"):
            ct=r.get("cluster_types"); r["cluster_types"]=ast.literal_eval(ct) if isinstance(ct,str) else []
            t=Trigger(**{k:v for k,v in r.items() if k!="session_day"})
            if t.pattern=="unclassified": continue
            sgn=1 if t.direction=="long" else -1
            if t.stop_ref is not None: t.stop_ref=t.stop_ref-sgn*buf   # beyond the wick
            if getattr(t,"ob_stop",None) is not None: t.ob_stop=t.ob_stop-sgn*buf
            out.append(t)
    return out

df=pd.read_parquet(DATA)
# champion only trades 08:00-10:15 ET; trim bars to 07:45-11:00 ET/day so simulate is ~6x faster
_et=pd.to_datetime(df.ts_event,utc=True).dt.tz_convert(NY)
df=df[(_et.dt.time>=dtime(7,45))&(_et.dt.time<=dtime(11,0))].reset_index(drop=True)
V=pd.read_csv("output/regime_vector.csv")
war={r.day for _,r in V.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20>=0.5}
cfg0=load_backtest_config()
UNCAP=cfg0.model_copy(update={"win_start":dtime(8,0),"win_end":dtime(10,15),
    "max_trades_per_day":6,"min_stop_points":0.25,"post_open_min_stop":0.0})
E3=UNCAP.model_copy(update={"mgmt_variant":"V8"}); E4=UNCAP.model_copy(update={"entry_variant":"E4"})

def book_trades(allt, cfg):
    tr,_,_=simulate(df, allt, cfg)
    return pd.DataFrame([dict(date=r.trade_date, fill_ts=r.fill_ts, dollars=r.dollars,
        R=r.r_multiple, win=r.dollars>0) for r in tr])

print("buffer  trades  win%    net$     avgR    @ $300 risk   avg$/t")
for buf in [0,3,5,10]:
    allt=load_triggers(buf)
    e3=book_trades(allt,E3); e4=book_trades(allt,E4)
    e3["war"]=e3.date.isin(war); e4["war"]=e4.date.isin(war)
    cand=pd.concat([e3[~e3.war], e4[e4.war]], ignore_index=True)
    champ=cand.sort_values("fill_ts").groupby("date",group_keys=False).head(2)
    win=champ.win.mean()*100; net=champ.dollars.sum(); pnl300=(champ.R*300).sum()
    print(f"{buf:>4}pt   {len(champ):4d}   {win:4.0f}   {net:+7.0f}   {champ.R.mean():+.2f}   {pnl300:+9.0f}   {champ.dollars.mean():+.0f}")
