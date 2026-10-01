import pickle, pandas as pd, numpy as np, collections
exec(open("tv_compare.py").read().split("ENG=load_engine()")[0])
ENG=load_engine(); TV,best=pickle.load(open("tv_parsed.pkl","rb"))
def to_et(s):
    return s.dt.tz_localize("Australia/Sydney", ambiguous="NaT", nonexistent="shift_forward").dt.tz_convert("America/New_York").dt.tz_localize(None).astype("datetime64[ns]")
ALL={}
for k,tv in TV.items():
    bk=best[k][0]; eng=ENG[bk].copy(); tv=tv.copy()
    tv["t_et"]=to_et(tv.t_in); tv["t_out_et"]=to_et(tv.t_out); tv["lv"]=tv.level.round(2); tv["gross"]=tv.pnl+10.0; tv["pts"]=tv.gross/20.0
    eng["lv"]=eng.level.round(2); eng["t_et"]=eng.t_fill
    lo,hi=tv.t_et.min(),tv.t_et.max(); e=eng[(eng.t_et>=lo)&(eng.t_et<=hi)].copy()
    mm=tv.merge(e,on=["dir","lv","t_et"],how="outer",suffixes=("","_e"),indicator=True)
    both=mm[mm._merge=="both"]; tvonly=mm[mm._merge=="left_only"]; engonly=mm[mm._merge=="right_only"]
    both=both.assign(tv_r=both.pts/both.risk, tv_win=both.gross>0)
    print(f"\n=== {bk}: TV {len(tv)} | engine {len(e)} | matched {len(both)} ({len(both)/len(e):.0%} of engine) | TV-only {len(tvonly)} | engine-only {len(engonly)}")
    print(f"  TV: net ${tv.pnl.sum():,.0f}, gross {tv.pts.sum():+,.0f} pts, win rate {(tv.gross>0).mean():.0%} | engine same span: gross {e.pts.sum():+,.0f} pts, net {(e.pts-0.5).sum():+,.0f}, win rate {(e.res=='TARGET').sum()/max(1,(e.res.isin(['TARGET','STOP'])).sum()):.0%}")
    print("  matched, engine result vs TV exit tag:\n"+pd.crosstab(both.res,both.exit).to_string())
    g=both.groupby("res").agg(n=("r","size"),eng_r=("r","mean"),tv_r=("tv_r","mean"),tv_win=("tv_win","mean")).round(2); print(g.to_string())
    print(f"  matched pts: TV {both.pts.sum():+,.0f} vs engine {both.pts_e.sum():+,.0f}")
    ALL[bk]=(tv,e,both,tvonly,engonly)
pickle.dump(ALL,open("tv_matched.pkl","wb"))
