#!/usr/bin/env python3
"""Stage 3 - order flow on the 20-SMA pin-bar rule.

Tests Pat's stated mechanism directly. His thesis: the long lower wick means
"sellers were absorbed". That is an order-flow claim, so it is falsifiable:

  On a real hammer, sell aggression should be HEAVY in the wick (delta negative
  at prices below the body) and price should still close back up. Sell pressure
  that failed to move price. If instead the wick shows POSITIVE delta, nobody was
  absorbed - price just dipped and got bought, which is a different animal.

Features measured on the signal bar (aggregated over its constituent minutes):
  wick_delta   delta at prices inside the rejected wick    (the absorption test)
  bar_delta    delta over the whole bar
  wick_ratio   -wick_delta / wick_volume, i.e. how one-sided the wick was
  vol_z        bar volume vs the trailing 20-bar mean
  cvd_div      cumulative delta over the prior 20 bars vs the price change
"""
import argparse, glob, numpy as np, pandas as pd, sys
sys.path.insert(0, "scripts")
from sma20_pinbar import load, resample, pivots, trend_flags, SESSIONS, TICK

def to_et(s):
    s = pd.to_datetime(s)
    s = s.dt.tz_convert("America/New_York") if s.dt.tz is not None else \
        s.dt.tz_localize("UTC").dt.tz_convert("America/New_York")
    return s.dt.tz_localize(None)

def load_footprint(lo_min=8*60, hi_min=12*60):
    parts = []
    for f in sorted(glob.glob("data/reference/cvd/footprint_*.parquet")):
        d = pd.read_parquet(f)
        d["ts"] = to_et(d.ts_minute)
        m = d.ts.dt.hour*60 + d.ts.dt.minute
        parts.append(d.loc[(m >= lo_min) & (m < hi_min), ["ts","price","side","volume"]])
    fp = pd.concat(parts).sort_values("ts", kind="mergesort").reset_index(drop=True)
    return (fp.ts.values.astype("datetime64[ns]").astype(np.int64),
            fp.price.values.astype(float),
            np.where(fp.side.values == "B", 1.0, -1.0),   # B = buy aggressor
            fp.volume.values.astype(float))

def signals_with_flow(tape, tf, trend, W, U, B, mult, cost, minrisk, maxhold, fpk):
    b = resample(load(tape), tf)
    o,h,l,c = (b[x].values.astype(float) for x in ("open","high","low","close"))
    vol = b["volume"].values.astype(float)
    sma = pd.Series(c).rolling(20).mean().values
    ph, pl = pivots(h, l)
    lo_t, sh_t = trend_flags(c, sma, h, l, ph, pl, trend)
    tmin = (b.index.hour*60 + b.index.minute).values
    t0,t1 = SESSIONS["NY"]; inwin = (tmin>=t0)&(tmin<t1)
    body=np.abs(c-o); rg=h-l; lw=np.minimum(o,c)-l; uw=h-np.maximum(o,c)
    with np.errstate(invalid="ignore"):
        lg = inwin & lo_t & (l<sma)&(c>sma)&(c>o)&(lw>=W*body)&(uw<=U*rg)
        sh = inwin & sh_t & (h>sma)&(c<sma)&(c<o)&(uw>=W*body)&(lw<=U*rg)
    lg=np.nan_to_num(lg,nan=False).astype(bool); sh=np.nan_to_num(sh,nan=False).astype(bool)

    fts, fpx, fsg, fvl = fpk
    volma = pd.Series(vol).rolling(20).mean().values
    idx_ns = b.index.values.astype("datetime64[ns]").astype(np.int64)
    bar_ns = tf*60*1_000_000_000
    hold = max(1, maxhold//tf); n=len(c); rows=[]; busy=-1

    for i in np.where(lg|sh)[0]:
        if i<=25 or i>=n-2 or i<busy: continue
        d = 1 if lg[i] else -1
        E=c[i]; stop=(l[i]-B*TICK) if d==1 else (h[i]+B*TICK)
        risk=(E-stop) if d==1 else (stop-E)
        if risk<=0 or risk<minrisk: continue
        busy=i+1
        # --- outcome ---
        tgt = E + d*mult*risk; res="FLAT"; pnl=None
        for k in range(i+1, min(n,i+1+hold)):
            hs=(l[k]<=stop) if d==1 else (h[k]>=stop)
            ht=(h[k]>=tgt)  if d==1 else (l[k]<=tgt)
            if hs: res,pnl="STOP",-risk; break
            if ht: res,pnl="TARGET",mult*risk; break
        if pnl is None: k=min(n-1,i+hold); pnl=d*(c[k]-E)
        # --- order flow on the signal bar ---
        a = np.searchsorted(fts, idx_ns[i]); z = np.searchsorted(fts, idx_ns[i]+bar_ns)
        if z-a < 5: continue                      # no footprint coverage for this bar
        px=fpx[a:z]; sg=fsg[a:z]; vl=fvl[a:z]
        body_edge = min(o[i],c[i]) if d==1 else max(o[i],c[i])
        inwick = (px <= body_edge) if d==1 else (px >= body_edge)
        wv = vl[inwick].sum(); wd = (sg[inwick]*vl[inwick]).sum()
        bd = (sg*vl).sum(); bv = vl.sum()
        # signed so that "expected direction" is positive for both longs and shorts
        rows.append(dict(
            tape=tape, day=str(b.index[i].date()), ts=str(b.index[i]), i=i, dir=d,
            entry=E, risk=risk, res=res, r=(pnl-cost)/risk,
            wick_delta = d*wd,                      # <0 = aggression against us in the wick
            wick_ratio = (d*wd/wv) if wv>0 else np.nan,
            bar_delta  = d*bd,
            bar_ratio  = (d*bd/bv) if bv>0 else np.nan,
            wick_vol_share = wv/bv if bv>0 else np.nan,
            vol_z = vol[i]/volma[i] if volma[i]>0 else np.nan,
            cvd_div = np.nan))
    return pd.DataFrame(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--tapes", default="2023-26")
    ap.add_argument("--tf", type=int, default=3); ap.add_argument("--trend", default="SIDE")
    ap.add_argument("--W", type=float, default=1.0); ap.add_argument("--U", type=float, default=0.5)
    ap.add_argument("--buf", type=int, default=2); ap.add_argument("--mult", type=float, default=3.0)
    ap.add_argument("--cost", type=float, default=0.75); ap.add_argument("--minrisk", type=float, default=8.0)
    ap.add_argument("--maxhold", type=int, default=120)
    ap.add_argument("--out", default="data/debug/sma20_orderflow.csv")
    a=ap.parse_args()
    print("loading footprint (NY window only)...", flush=True)
    fpk = load_footprint()
    print(f"  {len(fpk[0]):,} footprint rows in the 08:00-12:00 ET band\n", flush=True)
    out=[]
    for tape in a.tapes.split(","):
        t = signals_with_flow(tape, a.tf, a.trend, a.W, a.U, a.buf, a.mult,
                              a.cost, a.minrisk, a.maxhold, fpk)
        print(f"  {tape}: {len(t)} signals with footprint coverage", flush=True)
        out.append(t)
    t=pd.concat(out); t.to_csv(a.out, index=False)
    print(f"\n{len(t)} trades -> {a.out}")
    return t

if __name__=="__main__":
    main()
