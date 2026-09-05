"""Compare TradingView 'List of Trades' exports of the Pine port against the engine's armed dumps, book by book."""
import csv, gzip, json, sys, collections, re
import pandas as pd
QL="ql18/output/analysis"; UP="/root/.claude/uploads/8561fb22-7a6d-585e-9576-98688737845d"
FILES={"e05587c7":"e05587c7-Armed_Empire_CME_MINI_NQ1_20260904_1.csv","6c18d1fc":"6c18d1fc-Armed_Empire_CME_MINI_NQ1_20260904_2.csv","805183e4":"805183e4-Armed_Empire_CME_MINI_NQ1_20260904.csv","f4772c3f":"f4772c3f-Armed_Empire_CME_MINI_NQ1_20260904_6.csv",
       "d841ec08":"d841ec08-Armed_Empire_CME_MINI_NQ1_20260904_5.csv","ed38df67":"ed38df67-Armed_Empire_CME_MINI_NQ1_20260904_4.csv",
       "2fa30a79":"2fa30a79-Armed_Empire_CME_MINI_NQ1_20260904_3.csv"}
def parse_tv(fn):
    rows=list(csv.DictReader(open(f"{UP}/{fn}",encoding="utf-8-sig")))
    by=collections.defaultdict(dict)
    for r in rows:
        n=int(r["Trade number"]); t=r["Type"]
        if t.startswith("Entry"):
            m=re.match(r"([LS]) @ ([\d.]+)",r["Signal"])
            by[n].update(dir=1 if t=="Entry long" else -1, level=float(m.group(2)) if m else None,
                         t_in=pd.Timestamp(r["Date and time"]).as_unit("ns"), px_in=float(r["Price USD"]), pnl=float(r["Net PnL USD"]))
        else:
            by[n].update(t_out=pd.Timestamp(r["Date and time"]).as_unit("ns"), px_out=float(r["Price USD"]), exit=r["Signal"])
    df=pd.DataFrame([dict(n=k,**v) for k,v in by.items()]).sort_values("t_in").reset_index(drop=True)
    df["t_in"]=df["t_in"].astype("datetime64[ns]"); df["t_out"]=df["t_out"].astype("datetime64[ns]"); return df
def load_engine():
    a=[json.loads(l) for l in gzip.open(f"{QL}/pd_va_trades_lvall_xr30_sar_through_tf1_ng_arm1.jsonl.gz","rt")]
    b=[t for t in (json.loads(l) for l in gzip.open(f"{QL}/vwap_rev_tf1_retest_xr30_dd_arm1.jsonl.gz","rt")) if t["depth"]==3.0 and t["target_r"]==1.0]
    c=[t for t in (json.loads(l) for l in gzip.open(f"{QL}/vwap_rev_tf1_retest_xr30_nyanc_dd_arm1.jsonl.gz","rt")) if t["depth"]==3.0 and t["target_r"]==1.0]
    books={"PD value area":[t for t in a if t["family"]=="va"],"Weekly value area":[t for t in a if t["family"]=="wva"],"PD high/low":[t for t in a if t["family"]=="pdhl"],
           "PD POC":[t for t in a if t["family"]=="poc"],"Weekly POC":[t for t in a if t["family"]=="wpoc"],"Session VWAP":b,"NY VWAP":c}
    out={}
    for k,ts in books.items():
        df=pd.DataFrame(ts)
        t0=pd.to_datetime(df["day"])+pd.Timedelta(hours=18)
        df["t_fill"]=(t0+pd.to_timedelta((df["fill_hrs"]*60).round(),unit="m")).astype("datetime64[ns]")
        df["level"]=df["entry"]
        df["netr"]=df["r"]-0.5/df["risk"]
        out[k]=df
    return out
ENG=load_engine()
TV={k:parse_tv(v) for k,v in FILES.items()}
for k,df in TV.items():
    print(f"{k}: {len(df)} trades  {df.t_in.min()} -> {df.t_in.max()}  net ${df.pnl.sum():,.0f}  exits {dict(collections.Counter(df.exit))}")
# find the timezone offset: try offsets, count exact (dir, level, minute) matches vs the PD VA engine book
def match_count(tv, eng, off_h):
    key=set(zip(eng.dir, eng.level.round(2), (eng.t_fill).astype("int64")//60_000_000_000))
    tt=(tv.t_in - pd.Timedelta(hours=off_h)).astype("int64")//60_000_000_000
    return sum((d,round(l,2),m) in key for d,l,m in zip(tv.dir, tv.level, tt))
best={}
for k,tv in TV.items():
    scores={}
    for bk,eng in ENG.items():
        for off in range(-14,15):
            scores[(bk,off)]=match_count(tv,eng,off)
    (bk,off),sc=max(scores.items(),key=lambda x:x[1])
    best[k]=(bk,off,sc); print(f"{k}: best book={bk} offset={off:+d}h matches={sc}/{len(tv)} ({sc/len(tv):.0%})")
import pickle; pickle.dump((TV,best),open("tv_parsed.pkl","wb"))
