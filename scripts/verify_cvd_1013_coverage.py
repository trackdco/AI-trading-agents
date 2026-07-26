#!/usr/bin/env python3
"""TRIPLE-CHECK: does CVD actually cover the 10:00-13:00 UK session in footprint_q3_2025 / q4_2025?
Date-range coverage is NOT proof of intraday coverage. Three independent angles:
  A) hour-of-day histogram per file (UK time) - is 10-13 UK actually populated?
  B) per-trading-day minute counts inside 10:00-13:14 UK (the lookup span: entry-1min, 3-min rolling)
     -> how many days FULLY covered (>=180 of 195 min), partial, or ZERO
  C) reconcile against the real book: every Q3/Q4 trade's actual CVD lookup - hit or miss
Run from repo root (data/reference/cvd/ now on this branch)."""
from datetime import time as dtime
import numpy as np, pandas as pd
CVD="data/reference/cvd"
FILES=["footprint_q3_2025","footprint_q4_2025"]
LO,HI=dtime(10,0),dtime(13,15)      # lookup span incl. 3-min rolling tail past a 13:00 entry
print("="*104); print("TRIPLE-CHECK: CVD coverage of the 10:00-13:00 UK session, q3_2025 + q4_2025"); print("="*104)

store={}
for f in FILES:
    d=pd.read_parquet(f"{CVD}/{f}.parquet",columns=["ts_minute","side","volume"])
    uk=pd.to_datetime(d.ts_minute,utc=True).dt.tz_convert("Europe/London")
    d=d.assign(uk=uk,day=uk.dt.strftime("%Y-%m-%d"),hr=uk.dt.hour,t=uk.dt.time)
    store[f]=d

# ---------- ANGLE A: hour-of-day histogram ----------
print("\n[A] HOUR-OF-DAY coverage (UK), rows per hour  ->  is 10-13 populated at all?")
for f in FILES:
    d=store[f]; h=d.groupby("hr").size()
    tot=len(d)
    line="  "+f+":  "
    print(line)
    bars=[]
    for hr in range(24):
        n=int(h.get(hr,0)); pct=100*n/tot
        mark="<<<" if hr in (10,11,12) else ""
        bars.append(f"    {hr:02d}:00  {n:>9,}  {pct:5.2f}%  {'#'*int(pct*2.2)}{mark}")
    print("\n".join(bars))
    win=int(h.reindex([10,11,12]).fillna(0).sum())
    print(f"    -> hours 10,11,12 UK: {win:,} rows = {100*win/tot:.1f}% of the file\n")

# ---------- ANGLE B: per-day minute coverage inside the window ----------
print("[B] PER-DAY minute coverage inside 10:00-13:14 UK (195 possible minutes/day)")
allday={}
for f in FILES:
    d=store[f]; w=d[(d.t>=LO)&(d.t<HI)]
    per=w.groupby("day")["ts_minute"].nunique()
    alld=sorted(d.day.unique())
    # weekdays only (futures trade Sun-Fri; use presence in file as the day universe)
    full=int((per>=180).sum()); part=int(((per>0)&(per<180)).sum())
    zero=[x for x in alld if x not in per.index]
    print(f"  {f}:")
    print(f"    days in file: {len(alld)}   days WITH 10-13 data: {len(per)}   FULL(>=180min): {full}   partial: {part}   ZERO: {len(zero)}")
    print(f"    minutes/day in window: median {per.median():.0f}  min {per.min():.0f}  max {per.max():.0f}")
    if zero:
        z=[x for x in zero if pd.Timestamp(x).dayofweek<5]
        print(f"    ZERO-coverage days (weekday only, first 10): {z[:10]}  [total weekday-zero {len(z)}]")
    else:
        print(f"    ZERO-coverage days: NONE")
    allday.update(per.to_dict())
    # book-relevant subset
    if f=="footprint_q3_2025":
        bk=per[(per.index>="2025-07-01")]
        print(f"    book-relevant (Jul-Sep 2025): {len(bk)} days, median {bk.median():.0f} min/day, min {bk.min():.0f}")
    print()

# ---------- ANGLE C: reconcile against the actual book trades ----------
print("[C] RECONCILE vs the real book - every Q3/Q4 trade's actual CVD lookup")
TICK,PV,COMM=0.25,20.0,5.0
b=pd.read_parquet("/home/user/gs/data/reference/nq_1m_master.parquet")
b["ts"]=pd.to_datetime(b.ts_event,utc=True); b=b.sort_values("ts").reset_index(drop=True)
cvd_days=set(); dparts=[]
for f in FILES+["footprint_feb_mar2026","footprint_apr2026","footprint_may_jul2026"]:
    d=pd.read_parquet(f"{CVD}/{f}.parquet",columns=["ts_minute","side","volume"])
    cvd_days|=set(pd.to_datetime(d.ts_minute,utc=True).dt.tz_convert("Europe/London").dt.strftime("%Y-%m-%d").unique())
    d["s"]=np.where(d.side=="B",d.volume,-d.volume); dparts.append(d.groupby("ts_minute")["s"].sum()); del d
delta=pd.concat(dparts).groupby(level=0).sum().sort_index(); delta.index=pd.to_datetime(delta.index,utc=True)
delta3=delta.rolling(3).sum(); del dparts
m=b.set_index("ts").resample("15min",label="right",closed="right").agg(open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),volume=("volume","sum")).dropna(subset=["close"])
_uk=m.index.tz_convert("Europe/London"); m["ukt"]=_uk.time; m["ukday"]=_uk.strftime("%Y-%m-%d")
for p in(20,50,200): m[f"ma{p}"]=m.close.rolling(p).mean()
m["v10"]=m.volume.rolling(10).mean().shift(1); m["slo"]=m.low.rolling(5).min(); m["shi"]=m.high.rolling(5).max()
M=m.reset_index(names="uts").dropna(subset=["ma200"]); M=M[(M.ukday>="2025-07-01")&(M.ukday<="2026-07-15")].reset_index(drop=True)
a={c:M[c].values for c in["uts","open","high","low","close","volume","ma20","ma50","ma200","v10","slo","shi"]}; ud=M.ukday.values; utt=M.ukt.values
rows=[]
for i in range(1,len(M)-1):
    d=ud[i]
    if d in("2025-11-28","2026-04-03") or ud[i+1]!=d or not(dtime(10,0)<=utt[i]<dtime(13,0)): continue
    up=a["ma20"][i]>a["ma50"][i]>a["ma200"][i] and a["close"][i]>a["ma50"][i] and a["close"][i]>a["ma200"][i]
    dn=a["ma20"][i]<a["ma50"][i]<a["ma200"][i] and a["close"][i]<a["ma50"][i] and a["close"][i]<a["ma200"][i]
    dr=1 if(up and a["low"][i]<=a["ma50"][i]) else(-1 if(dn and a["high"][i]>=a["ma50"][i]) else 0)
    if dr==0 or not(a["v10"][i]>0 and a["volume"][i]<a["v10"][i]): continue
    en=a["open"][i+1]+dr*TICK; rf=min(a["slo"][i],a["ma50"][i]) if dr>0 else max(a["shi"][i],a["ma50"][i]); rk=abs(en-rf)+TICK
    if rk<5 or rk>70: continue
    em=pd.Timestamp(a["uts"][i+1]).tz_localize("UTC"); look=em-pd.Timedelta(minutes=1)
    v3=delta3.get(look,np.nan)
    rows.append(dict(day=d,ent=str(utt[i])[:5],inday=(d in cvd_days),hit=not (isinstance(v3,float) and np.isnan(v3)),v3=v3))
R=pd.DataFrame(rows)
for lab,lo,hi in [("Q3 2025 (Jul-Sep)","2025-07","2025-09"),("Q4 2025 (Oct-Dec)","2025-10","2025-12")]:
    s=R[(R.day.str[:7]>=lo)&(R.day.str[:7]<=hi)]
    print(f"  {lab}: {len(s)} triggers | day-in-cvd {int(s.inday.sum())}/{len(s)} | CVD LOOKUP HIT {int(s.hit.sum())}/{len(s)}"
          + ("  <- 100% COVERED" if len(s) and s.hit.all() else f"  <- MISSES: {s[~s.hit].day.tolist()}"))
tot=R[(R.day.str[:7]>="2025-07")&(R.day.str[:7]<="2025-12")]
print(f"\n  Q3+Q4 combined: {int(tot.hit.sum())}/{len(tot)} triggers have a real CVD value at the lookup minute")
print(f"  (nonzero deltas: {int((tot.v3.fillna(0)!=0).sum())}/{len(tot)} - a zero would be suspicious/flat tape)")
print("\n" + "="*104)
