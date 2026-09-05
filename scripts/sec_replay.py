"""Second-by-second replay of the engine's trades on the six 1-second sessions.
For each trade: fill second = first second in the fill minute that trades one tick through the level.
Then scan forward second by second: first touch of stop vs target (same second -> STOP, the engine's tie rule)."""
import pickle, pandas as pd, numpy as np
ALL=pickle.load(open("tv_matched.pkl","rb"))
s=pd.read_parquet("sec/all_1s.parquet").sort_values("ts").reset_index(drop=True)
TS=s.ts.values.astype("datetime64[ns]"); H=s.high.values; L=s.low.values
DAYS={"2026-08-04","2026-08-05","2025-04-10","2024-06-20","2023-12-26","2023-12-27"}
rows=[]
for bk,(tv,e,both,tvonly,engonly) in ALL.items():
    e=e[e.day.isin(DAYS)].copy()
    tvmap=both.set_index(["dir","lv","t_et"]) if len(both) else None
    for _,t in e.iterrows():
        d=int(t.dir); E=float(t.entry); risk=float(t.risk); stop=E-d*risk; tgt=E+d*risk
        f0=np.datetime64(pd.Timestamp(t.t_fill)); f1=f0+np.timedelta64(60,"s")
        i0=np.searchsorted(TS,f0); i1=np.searchsorted(TS,f1)
        if i1<=i0: rows.append(dict(book=bk,day=t.day,res=t.res,hold=t.hold_min,cls="no 1s data",rep=np.nan)); continue
        thru=(L[i0:i1]<=E-0.25) if d==1 else (H[i0:i1]>=E+0.25)
        if not thru.any(): rows.append(dict(book=bk,day=t.day,res=t.res,hold=t.hold_min,cls="no fill second",rep=np.nan)); continue
        fs=i0+int(np.argmax(thru))
        # where was the minute's extreme (the engine's 'target touch') relative to the fill second?
        hit_fill_sec = (H[fs]>=tgt) if d==1 else (L[fs]<=tgt)
        # forward scan strictly after the fill second, to the end of the loaded data (session)
        rest_h=H[fs+1:]; rest_l=L[fs+1:]
        ts_hit = np.where(rest_h>=tgt)[0] if d==1 else np.where(rest_l<=tgt)[0]
        st_hit = np.where(rest_l<=stop)[0] if d==1 else np.where(rest_h>=stop)[0]
        ti=ts_hit[0] if len(ts_hit) else 10**9; si=st_hit[0] if len(st_hit) else 10**9
        if ti==si==10**9: outcome="open at data end"; rep=np.nan
        elif si<=ti: outcome="LOSS"; rep=-1.0
        else: outcome="WIN"; rep=1.0
        within=(ti<10**9) and (fs+1+ti<i1) and outcome=="WIN"
        secs_to_exit=(min(ti,si)+1) if outcome in("WIN","LOSS") else np.nan
        # the minute's extreme before or after the fill second?
        ext_before = (H[i0:fs].max()>=tgt) if (d==1 and fs>i0) else ((L[i0:fs].min()<=tgt) if (d==-1 and fs>i0) else False)
        cls = "target after fill, same minute" if within else ("target only inside the fill second" if (hit_fill_sec and outcome!="WIN" and not within) else ("target later minute" if outcome=="WIN" else ("stopped" if outcome=="LOSS" else outcome)))
        key=(d,round(E,2),pd.Timestamp(t.t_fill))
        tvr=np.nan
        if tvmap is not None and key in tvmap.index:
            r=tvmap.loc[key]; tvr=float((r.pts/r.risk).iloc[0] if hasattr(r.pts,"iloc") else r.pts/r.risk)
        rows.append(dict(book=bk,day=t.day,res=t.res,hold=t.hold_min,cls=cls,rep=rep,ext_before=ext_before,hit_fill_sec=hit_fill_sec,secs=secs_to_exit,tv_r=tvr,risk=risk))
R=pd.DataFrame(rows)
R.to_csv("sec/replay_results.csv",index=False)
Z=R[(R.res=="TARGET")&(R.hold==0)]
print(f"engine trades on the six sessions: {len(R)} | zero-minute TARGETs: {len(Z)} | no 1s data/fill: {(R.cls.isin(['no 1s data','no fill second'])).sum()}")
print("\nZERO-MINUTE TARGETS, what the seconds say:")
print(Z.cls.value_counts().to_string())
print(f"\n  minute's high/low (the engine's 'target') printed BEFORE the fill second: {Z.ext_before.mean():.0%}")
print(f"  replay result: WIN {(Z.rep==1).mean():.0%}  LOSS {(Z.rep==-1).mean():.0%}  net R {Z.rep.sum():+.0f} over {len(Z)} (engine +{len(Z)})  | TradingView on the same trades: {Z.tv_r.mean():+.2f} R/trade")
print("  by day:"); print(Z.groupby("day").agg(n=("rep","size"),win=("rep",lambda x:(x==1).mean()),ext_before=("ext_before","mean"),netR=("rep","sum")).round(2).to_string())
print("  by book:"); print(Z.groupby("book").agg(n=("rep","size"),win=("rep",lambda x:(x==1).mean()),netR=("rep","sum")).round(2).to_string())
print("\nCONTROLS (the replay must agree with the engine here):")
C=R[(R.res=="TARGET")&(R.hold>0)]; print(f"  TARGETs held >0 min: {len(C)}  replay WIN {(C.rep==1).mean():.0%}")
S=R[R.res=="STOP"]; print(f"  STOPs: {len(S)}  replay LOSS {(S.rep==-1).mean():.0%}")
allR=R[R.res.isin(["TARGET","STOP"])]
print(f"\nALL TARGET+STOP trades on the six sessions: engine net {allR.r.sum() if 'r' in allR else (allR.res.eq('TARGET').sum()-allR.res.eq('STOP').sum()):+d}R  vs 1-second replay {allR.rep.sum():+.0f}R")
