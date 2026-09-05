#!/usr/bin/env python3
"""Trend + hard counter-push rejected at the Bollinger band.
Rules frozen in docs/PREREG-trend-band-rejection.md. Exits from the bar AFTER entry."""
import argparse, gzip, json, numpy as np, pandas as pd
TICK = 0.25

def load(path):
    b = pd.read_parquet(path); t = pd.to_datetime(b.ts_event)
    t = t.dt.tz_convert("America/New_York") if t.dt.tz is not None else t.dt.tz_localize("UTC").dt.tz_convert("America/New_York")
    b = b.set_index(t.dt.tz_localize(None))[["open","high","low","close","volume"]].sort_index()
    b["sess"] = (b.index - pd.Timedelta(hours=18)).normalize()
    return b

def frame(s):
    tp = (s.high+s.low+s.close)/3.0; v = s.volume.clip(lower=0).astype(float)
    pv, vv, p2 = (tp*v).cumsum(), v.cumsum(), (tp*tp*v).cumsum()
    vwap = pv/vv.replace(0,np.nan); sd = np.sqrt((p2/vv.replace(0,np.nan)-vwap**2).clip(lower=0))
    m = s.resample("5min").agg(open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last")).dropna()
    m["vwap"] = vwap.resample("5min").last().reindex(m.index)
    m["sd"] = sd.resample("5min").last().reindex(m.index)
    c = m.close; ma = c.rolling(20).mean(); sv = c.rolling(20).std(ddof=0)
    m["bb_u"], m["bb_l"] = ma+2*sv, ma-2*sv
    return m.dropna(subset=["vwap","sd"])

def run(bars, stop_mode, target, cost=0.5):
    out = []
    for day, s in bars.groupby("sess"):
        if len(s) < 600: continue
        m = frame(s)
        if len(m) < 100: continue
        t0 = pd.Timestamp(day)+pd.Timedelta(hours=18); end = m.index+pd.Timedelta(minutes=5)
        w = m[(end > t0) & (end <= t0+pd.Timedelta(hours=7))]
        if len(w) < 60: continue
        k = None
        for kk in (1,2,3):
            up, lo = w.vwap+kk*w.sd, w.vwap-kk*w.sd
            if ((w.close<=up)&(w.close>=lo)).mean() >= 0.90 and \
               (((w.high>=up)|(w.low<=lo))&(w.close<=up)&(w.close>=lo)).sum() >= 3: k = kk; break
        if k is None: continue
        w1 = w[w.index >= t0+pd.Timedelta(hours=1)]
        if len(w1) < 20: continue
        v0, v1 = float(w1.vwap.iloc[0]), float(w1.vwap.iloc[-1])
        if v0 <= 0 or abs(v1-v0)/v0 <= 0.0015: continue
        trend = 1 if v1 > v0 else -1
        if ((w.close > w.vwap) if trend == 1 else (w.close < w.vwap)).mean() < 0.60: continue
        act = m[(end > t0+pd.Timedelta(hours=7)) & (end <= t0+pd.Timedelta(hours=22))].dropna(subset=["bb_u"])
        if len(act) < 5: continue
        o,c,h,l = act.open.values, act.close.values, act.high.values, act.low.values
        bu,bl,vw,sd = act.bb_u.values, act.bb_l.values, act.vwap.values, act.sd.values
        pushing = False; ext = np.nan; sig = None
        for i in range(len(act)):
            body_through = (o[i] < bl[i] and c[i] < bl[i]) if trend == 1 else (o[i] > bu[i] and c[i] > bu[i])
            if not pushing:
                if body_through: pushing = True; ext = l[i] if trend == 1 else h[i]
            else:
                if body_through:
                    ext = min(ext, l[i]) if trend == 1 else max(ext, h[i])
                else:
                    inside = (c[i] > bl[i]) if trend == 1 else (c[i] < bu[i])
                    rng = h[i]-l[i]; body = abs(c[i]-o[i])
                    strong = rng > 0 and body >= 0.5*rng and ((c[i] > o[i]) if trend == 1 else (c[i] < o[i]))
                    if inside and strong: sig = (i, trend, ext); break
                    if inside: pushing = False; ext = np.nan
        if sig is None: continue
        i, d, ext = sig; E = c[i]
        stop = (ext - TICK*d) if stop_mode == "X" else (E - d*float(stop_mode[1:]))
        risk = abs(E-stop)
        if risk <= 0: continue
        sfull = s[s.index >= act.index[i]+pd.Timedelta(minutes=5)]
        if len(sfull) < 2: continue
        H1,L1,C1 = sfull.high.values, sfull.low.values, sfull.close.values
        vwl = pd.Series(act.vwap.reindex(sfull.index, method="ffill")).ffill().bfill().values
        sdl = pd.Series(act.sd.reindex(sfull.index, method="ffill")).ffill().bfill().values
        r = None; res = "FLAT"
        for q in range(len(sfull)):
            tgt = vwl[q] if target=="VWAP" else (vwl[q]+d*sdl[q] if target=="1SIG" else vwl[q]+d*k*sdl[q])
            if (L1[q] <= stop) if d==1 else (H1[q] >= stop): r, res = -1.0, "STOP"; break
            if ((H1[q] >= tgt) if d==1 else (L1[q] <= tgt)) and (d*(tgt-E) > 0):
                r, res = abs(tgt-E)/risk, "TARGET"; break
        if r is None: r = d*(C1[-1]-E)/risk
        out.append(dict(day=str(pd.Timestamp(day).date()), dir=int(d), k=int(k), entry=float(E), stop=float(stop),
                        risk=float(risk), res=res, r=float(r), hold_min=int(q+1), fill_hrs=0.0,
                        target_r=1.0, depth=0.0))
    return pd.DataFrame(out)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--bars", required=True); ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True); a = ap.parse_args()
    bars = load(a.bars); nd = bars.sess.nunique()
    print(f"\n{a.label}  ({nd:,} sessions)")
    print(f"  {'stop':<5}{'target':<7}{'trades':>8}{'/sess':>7}{'R/trade':>10}{'net R':>8}{'win':>7}{'medRR':>7}{'maxDD':>8}{'medRisk':>9}")
    for sm in ("X","F20","F30"):
        for tg in ("VWAP","1SIG","EDGE"):
            tr = run(bars, sm, tg)
            if len(tr) == 0: print(f"  {sm:<5}{tg:<7}   no trades"); continue
            tr["netr"] = tr.r - 0.5/tr.risk
            day = tr.groupby("day").netr.sum(); cum = day.cumsum(); dd = (cum-cum.cummax()).min()
            wn = tr[tr.res=="TARGET"]
            print(f"  {sm:<5}{tg:<7}{len(tr):>8}{len(tr)/nd:>7.3f}{tr.netr.mean():>+10.4f}{tr.netr.sum():>+8.0f}"
                  f"{(tr.res=='TARGET').mean():>7.1%}{(wn.r.median() if len(wn) else float('nan')):>7.2f}{dd:>+8.1f}{tr.risk.median():>9.1f}")
            with gzip.open(f"{a.out}_{sm}_{tg}.jsonl.gz","wt") as fh:
                for _,t in tr.iterrows(): fh.write(json.dumps({q:(v.item() if hasattr(v,'item') else v) for q,v in t.items()})+"\n")
