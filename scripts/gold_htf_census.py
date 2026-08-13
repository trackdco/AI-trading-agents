import pandas as pd, numpy as np
from src.research.tomtrades import data as D, autopsy as AU
from src.research.gold import htf_census as HC

gc = D.load("data/gc_1m.parquet")
b = gc.set_index(gc["ts_event"].dt.tz_convert(HC.NY))[["open","high","low","close","volume"]]
print(f"GC {len(b):,} bars {b.index.min()} -> {b.index.max()}", flush=True)

ep = HC.displacement_episodes(b)
ep = HC.add_placebo(ep, b)
print(f"episodes: {len(ep):,} over {ep.sess_day.nunique():,} session-days", flush=True)
ep.to_parquet("output/gold_htf_episodes.parquet")

def blk(d, label):
    if len(d) < 30: return None
    dd = d.rename(columns={"touched":"out"}); dd["sess_day"]=d["sess_day"]
    lo,hi = AU.dboot_mean(dd,"out")
    p = d.assign(out=d.placebo_touched)
    plo,phi = AU.dboot_mean(p,"out")
    return {"cell":label,"n":len(d),"days":d.sess_day.nunique(),
            "touch_pct":100*d.touched.mean(),"ci_lo":100*lo,"ci_hi":100*hi,
            "placebo_pct":100*d.placebo_touched.mean(),
            "p_lo":100*plo,"p_hi":100*phi,
            "edge_pp":100*(d.touched.mean()-d.placebo_touched.mean()),
            "before_1w_pct":100*d.before_1w.mean(),
            "adverse_p50":d.adverse_w.median(),"adverse_p90":d.adverse_w.quantile(.9),
            "mins_p50":d.minutes.median()}

rows=[blk(ep,"ALL")]
for w,g in ep.groupby("window"): rows.append(blk(g,f"window={w}"))
for s,g in ep.groupby("side"):   rows.append(blk(g,f"side={'up' if s>0 else 'down'}"))
days=np.array(sorted(ep.sess_day.unique())); mid=days[len(days)//2]
rows.append(blk(ep[ep.sess_day<mid],"era=H1")); rows.append(blk(ep[ep.sess_day>=mid],"era=H2"))
t=pd.DataFrame([r for r in rows if r])
pd.set_option("display.width",200)
print(t.round(2).to_string(index=False), flush=True)
t.to_csv("output/gold_htf_census.csv", index=False)

print("\n=== FIXED-HORIZON touch rate (confound removed) ===", flush=True)
rows=[]
for H in (30,60,120,240):
    e = HC.touch_within(ep, H)
    for lab,g in [("ALL",e)] + [(f"window={w}",gg) for w,gg in e.groupby("window")]:
        if len(g)<30: continue
        lo,hi = AU.dboot_mean(g,"out")
        rows.append({"horizon_min":H,"cell":lab,"n":len(g),"days":g.sess_day.nunique(),
                     "touch_pct":100*g["out"].mean(),"ci_lo":100*lo,"ci_hi":100*hi})
h=pd.DataFrame(rows)
print(h.round(2).to_string(index=False), flush=True)
h.to_csv("output/gold_htf_horizon.csv", index=False)
