"""Score the corrected-exit runs (target scanned from the bar after the fill) versus the original dumps.
Rail pass = G3 first-in-wins within one floor, G5 cap 4, G6 same-dir cap 3 (as conviction_sizing.rail_pass)."""
import gzip, json, sys, collections, numpy as np, pandas as pd
QL="ql18/output/analysis"
def load(n,c):
    try: ts=[json.loads(l) for l in gzip.open(f"{QL}/{n}","rt")]
    except FileNotFoundError: return None
    return [t for t in ts if (not c) or (t["depth"]==3.0 and t["target_r"]==1.0)]
def names(inst, arm, xn):
    i="" if inst=="nq" else f"_{inst}"; ng="_ng" if inst=="nq" else ""; ng0="" if inst=="nq" else "_ng0"
    a="_arm1" if arm else ""; x="_xn" if xn else ""
    return [(f"pd_va_trades{i}_lvall_xr30_sar_through_tf1{ng}{a}{x}.jsonl.gz",False),
            (f"vwap_rev_tf1_retest{i}{ng0}_xr30_dd{a}{x}.jsonl.gz",True),
            (f"vwap_rev_tf1_retest{i}{ng0}_xr30_nyanc_dd{a}{x}.jsonl.gz",True)]
def rail(books):
    byday=collections.defaultdict(list)
    for b in books:
        for t in b: byday[t["day"]].append(t)
    kept=[]
    for d,ts in byday.items():
        ts.sort(key=lambda t:(t["fill_hrs"],t["t_sig_hrs"])); op=[]
        for t in ts:
            f=t["fill_hrs"]; e=f+t["hold_min"]/60; op=[q for q in op if q[1]>f]
            if any(q[2]==t["dir"] and abs(q[3]-t["entry"])<=5.0 for q in op): continue
            if len(op)>=4 or sum(1 for q in op if q[2]==t["dir"])>=3: continue
            op.append((f,e,t["dir"],t["entry"])); kept.append(t)
    return kept
def stats(kept):
    df=pd.DataFrame(kept); df["netr"]=df.r-0.5/df.risk; df["year"]=df.day.str[:4]
    day=df.groupby("day").netr.sum(); cum=day.cumsum(); dd=(cum-cum.cummax()).min()
    wr=(df.res=="TARGET").sum()/max(1,df.res.isin(["TARGET","STOP"]).sum())
    return dict(trades=len(df),days=len(day),win=wr,per_trade=df.netr.mean(),netR=df.netr.sum(),Rday=day.mean(),maxDD=dd,worst=day.min(),green=(day>0).mean(),
                years=df.groupby("year").netr.sum().round(0).to_dict(), zero=((df.res=="TARGET")&(df.hold_min==0)).mean())
rows=[]
for inst,label in (("nq","2023-26"),("nq20a","2020-22"),("nq17a","2017-19")):
    for arm in (True,False):
        for xn in (True,False):
            books=[load(n,c) for n,c in names(inst,arm,xn)]
            if any(b is None for b in books): print(f"missing: {label} {'armed' if arm else 'flat'} {'corrected' if xn else 'original'}"); continue
            st=stats(rail(books)); st.update(tape=label,mode="armed" if arm else "flat",rule="corrected" if xn else "original"); rows.append(st)
R=pd.DataFrame(rows)
if len(R):
    cols=["tape","mode","rule","trades","win","per_trade","netR","Rday","maxDD","worst","green","zero"]
    print(R[cols].to_string(index=False,formatters={"win":"{:.1%}".format,"per_trade":"{:+.4f}".format,"netR":"{:+,.0f}".format,"Rday":"{:+.2f}".format,"maxDD":"{:+.1f}".format,"worst":"{:+.1f}".format,"green":"{:.0%}".format,"zero":"{:.0%}".format}))
    print("\nby year (net R):")
    for _,r in R.iterrows(): print(f"  {r.tape} {r['mode']:<5} {r.rule:<9} {r.years}")
