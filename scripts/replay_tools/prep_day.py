"""Per-day prep: causal level table (vwap/BB MAs/fibs), event map, candidate list, profiles."""
import sys, json
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
import pandas as pd
from scripts.build_l2_outcomes import load_bars
from src.htf_ma.levels import NY, bb_ma_asof, vwap_bands

def prep(sess_day, out_path):
    nxt = (pd.Timestamp(sess_day) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    b = load_bars(); b["mi"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
    b = b.set_index("mi").sort_index()[["open","high","low","close","volume"]]
    day = b[f"{sess_day} 18:00":f"{nxt} 13:00"]
    vb = vwap_bands(day)
    ma2,_ = bb_ma_asof(day,2); ma3,_ = bb_ma_asof(day,3); ma15,w15 = bb_ma_asof(day,15); ma60,_ = bb_ma_asof(day,60)
    rows=[]
    for hh in range(3,12):
        for mm in range(0,60,2):
            t = pd.Timestamp(f"{nxt} {hh:02d}:{mm:02d}", tz=NY); u = t - pd.Timedelta(minutes=1)
            try:
                w = day[(day.index >= t - pd.Timedelta(minutes=2)) & (day.index < t)]
                sofar = day[day.index < t]; H,L = float(sofar.high.max()), float(sofar.low.min()); rng=H-L
                rows.append({"minute_et":f"{hh:02d}:{mm:02d}",
                  "vwap":round(float(vb.loc[u,"vwap"]),2),"p1":round(float(vb.loc[u,"vwap_p1"]),2),
                  "p2":round(float(vb.loc[u,"vwap_p2"]),2),"m1":round(float(vb.loc[u,"vwap_m1"]),2),
                  "m2":round(float(vb.loc[u,"vwap_m2"]),2),
                  "ma2":round(float(ma2.loc[u]),2),"ma3":round(float(ma3.loc[u]),2),
                  "ma15":round(float(ma15.loc[u]),2),
                  "ma60":(round(float(ma60.loc[u]),2) if not pd.isna(ma60.loc[u]) else None),
                  "day_h":H,"day_l":L,
                  "fib":{k:round(L+rng*f,2) for k,f in [("0.382",0.382),("0.5",0.5),("0.618",0.618),("0.705",0.705)]},
                  "bar_o":float(w.iloc[0].open),"bar_h":float(w.high.max()),"bar_l":float(w.low.min()),"bar_c":float(w.iloc[-1].close)})
            except Exception: pass
    ev = {"ma15_crosses":[], "displacements":[], "shape":{}}
    c15=day.close.resample("15min",label="right",closed="left").last().dropna()
    o15=day.open.resample("15min",label="right",closed="left").first().dropna()
    h15=day.high.resample("15min",label="right",closed="left").max().dropna()
    l15=day.low.resample("15min",label="right",closed="left").min().dropna()
    for t in c15.index:
        if not (pd.Timestamp(f"{nxt} 03:00",tz=NY) <= t <= pd.Timestamp(f"{nxt} 11:00",tz=NY)): continue
        u=t-pd.Timedelta(minutes=1)
        if u not in ma15.index: continue
        m=ma15.loc[u]; o,c=o15.loc[t],c15.loc[t]
        if (o-m)*(c-m)<0:
            br=abs(c-o)/max(h15.loc[t]-l15.loc[t],0.01)
            ev["ma15_crosses"].append({"t":t.strftime("%H:%M"),"dir":("DOWN" if c<m else "UP"),"ma":round(float(m),2),"close":float(c),"body_ratio":round(float(br),2)})
    r2h=day.high.resample("2min",label="right",closed="left").max().dropna()
    r2l=day.low.resample("2min",label="right",closed="left").min().dropna()
    for t in r2h.index:
        if not (pd.Timestamp(f"{nxt} 03:00",tz=NY) <= t <= pd.Timestamp(f"{nxt} 11:00",tz=NY)): continue
        u=t-pd.Timedelta(minutes=1)
        if u in w15.index and (r2h.loc[t]-r2l.loc[t]) >= 0.5*w15.loc[u]:
            ev["displacements"].append({"t":t.strftime("%H:%M"),"range":round(float(r2h.loc[t]-r2l.loc[t]),2)})
    for h in ["03:00","04:00","05:00","06:00","07:00","08:00","09:00","09:30","10:00","10:30","11:00"]:
        t=pd.Timestamp(f"{nxt} {h}",tz=NY); seg=day[day.index<t]
        if len(seg): ev["shape"][h]={"close":float(seg.iloc[-1].close),"H":float(seg.high.max()),"L":float(seg.low.min())}
    ov = day[(day.index>=f"{sess_day} 18:00")&(day.index<f"{nxt} 03:00")]
    ev["overnight"]={"open":float(ov.iloc[0].open),"close":float(ov.iloc[-1].close),
      "high":float(ov.high.max()),"high_t":str(ov.high.idxmax())[11:16],
      "low":float(ov.low.min()),"low_t":str(ov.low.idxmin())[11:16]}
    json.dump({"levels":rows,"events":ev}, open(out_path,"w"))
    return ev

if __name__ == "__main__":
    ev = prep(sys.argv[1], sys.argv[2])
    print(json.dumps(ev, indent=1))
