import gzip, json, pandas as pd, numpy as np, collections
QL="ql18/output/analysis"
def load(n): return pd.DataFrame([json.loads(l) for l in gzip.open(f"{QL}/{n}","rt")])
def prep(df,book):
    df=df.copy(); df["book"]=book; df["netr"]=df.r-0.5/df.risk; df["half"]=np.where(df.day<sorted(df.day.unique())[len(df.day.unique())//2],"H1","H2")
    df["hour"]=((18+df.fill_hrs)%24).astype(int); df["fam"]=df.get("family",df.get("band")); return df
def empire(inst):
    i="" if inst=="nq" else f"_{inst}"; ng="_ng" if inst=="nq" else ""; ng0="" if inst=="nq" else "_ng0"
    lv=prep(load(f"pd_va_trades{i}_lvall_xr30_sar_through_tf1{ng}_arm1_xn.jsonl.gz"),"levels")
    vs=load(f"vwap_rev_tf1_retest{i}{ng0}_xr30_dd_arm1_xn.jsonl.gz"); vn=load(f"vwap_rev_tf1_retest{i}{ng0}_xr30_nyanc_dd_arm1_xn.jsonl.gz")
    return lv, prep(vs,"vwap-sess"), prep(vn,"vwap-ny")
lv,vs,vn=empire("nq"); lv2,vs2,vn2=empire("nq20a")
base=pd.concat([lv,vs[(vs.depth==3.0)&(vs.target_r==1.0)],vn[(vn.depth==3.0)&(vn.target_r==1.0)]]).reset_index(drop=True)
base2=pd.concat([lv2,vs2[(vs2.depth==3.0)&(vs2.target_r==1.0)],vn2[(vn2.depth==3.0)&(vn2.target_r==1.0)]]).reset_index(drop=True)
print(f"corrected armed 2023-26 (no rails): {len(base):,} trades, {base.netr.mean():+.4f} R/trade | 2020-22: {len(base2):,}, {base2.netr.mean():+.4f}")
def slice_report(col, cut=None, top=None):
    b=base.copy(); b2=base2.copy()
    if cut is not None: b[col]=cut(b); b2[col]=cut(b2)
    g=b.groupby(col).agg(n=("netr","size"),r=("netr","mean"))
    hh=b.groupby([col,"half"]).netr.mean().unstack(); g["h1"]=hh.get("H1"); g["h2"]=hh.get("H2")
    g["r_2020_22"]=b2.groupby(col).netr.mean(); g["n_2020_22"]=b2.groupby(col).size()
    g=g.sort_values("r",ascending=False)
    if top: g=g.head(top)
    print(f"\n--- by {col} ---"); print(g.round(3).to_string())
slice_report("book"); slice_report("fam"); slice_report("window"); slice_report("hour")
slice_report("tier"); slice_report("dir")
slice_report("risk_bucket", cut=lambda d: pd.cut(d.risk,[0,5.01,7.5,10,15,20,30],labels=["5","5-7.5","7.5-10","10-15","15-20","20-30"]))
slice_report("excur", cut=lambda d: pd.cut(d.excur_r.fillna(0),[-1,0.5,1,2,3,100],labels=["<0.5R","0.5-1","1-2","2-3","3+"]))
slice_report("year", cut=lambda d: d.day.str[:4])
slice_report("dow", cut=lambda d: pd.to_datetime(d.day).dt.dayofweek)
# target / depth grid on the vwap books (the corrected vwap dumps carry the whole grid)
print("\n--- vwap books: depth x target grid, corrected, 2023-26 (R/trade, n) ---")
for nm,df in (("vwap-sess",vs),("vwap-ny",vn)):
    g=df.groupby(["depth","target_r"]).agg(n=("netr","size"),r=("netr","mean"),win=("res",lambda x:(x=="TARGET").sum()/max(1,x.isin(["TARGET","STOP"]).sum())))
    print(nm); print(g.round(3).to_string())
# hold-time survivors: trades that lasted >= k minutes (post hoc, not causal - shown only to explain where R goes)
print("\n--- corrected results by hold time (NOT a tradeable filter, hold is unknown at entry) ---")
print(base.groupby(pd.cut(base.hold_min,[-1,0,1,3,10,30,1000],labels=["0","1","2-3","4-10","11-30","30+"])).agg(n=("netr","size"),r=("netr","mean")).round(3).to_string())
