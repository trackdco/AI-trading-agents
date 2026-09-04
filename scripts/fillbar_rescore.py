"""Re-score the engine's own trades with TradingView's within-bar order: on the fill bar a target counts only if the bar
closed in the trade's direction (O->L->H->C for an up bar). Otherwise keep scanning from the next bar (stop/target, tie=STOP,
else flat at session end). Occupancy/SAR knock-on effects ignored (this is a per-trade bound, the proper engine run follows)."""
import pickle, pandas as pd, numpy as np
ALL=pickle.load(open("tv_matched.pkl","rb"))
bars=pd.read_parquet("ql18/data/reference/nq_live_tape.parquet")
t=pd.to_datetime(bars["ts_event"]); t=t.dt.tz_convert("America/New_York").dt.tz_localize(None)
bars.index=t.astype("datetime64[ns]"); bars=bars[["open","high","low","close"]]
ts=bars.index.values; O=bars.open.values; H=bars.high.values; L=bars.low.values; C=bars.close.values
def rescore(row):
    f=np.searchsorted(ts, np.datetime64(row.t_fill))
    if f>=len(ts) or ts[f]!=np.datetime64(row.t_fill): return row.r
    d=row.dir; E=row.entry; risk=row.risk; stop=E-d*risk; tgt=E+d*risk
    up = C[f]>=O[f]
    if (d==1 and up) or (d==-1 and not up): return 1.0          # TV credits the same-bar target
    end=np.searchsorted(ts, np.datetime64(pd.Timestamp(row.day)+pd.Timedelta(hours=41)))  # session end 17:00 next day
    for i in range(f+1, min(end,len(ts))):
        hs = L[i]<=stop if d==1 else H[i]>=stop
        ht = H[i]>=tgt if d==1 else L[i]<=tgt
        if hs: return -1.0
        if ht: return 1.0
    last=min(end,len(ts))-1
    return d*(C[last]-E)/risk
print(f"{'book':<18}{'engine net R':>13}{'TV-rule net R':>14}{'engine R/trade':>15}{'TV-rule R/trade':>16}{'TV actual R/trade':>18}")
for bk,(tv,e,both,tvonly,engonly) in ALL.items():
    e=e.copy(); e["r2"]=e.r
    m=(e.res=="TARGET")&(e.hold_min==0)
    e.loc[m,"r2"]=e[m].apply(rescore,axis=1)
    net1=(e.r-0.5/e.risk).sum(); net2=(e.r2-0.5/e.risk).sum()
    tvr=(tv.pts/ tv.level*0+ (tv.pts)).sum()  # placeholder
    print(f"{bk:<18}{net1:>+13,.0f}{net2:>+14,.0f}{net1/len(e):>+15.3f}{net2/len(e):>+16.3f}{(both.pts/both.risk - 0.5/both.risk).mean():>+18.3f}")
