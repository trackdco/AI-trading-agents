#!/usr/bin/env python3
"""Asia-open level break -> retest limit -> next-level target.
Rules frozen in docs/PREREG-asia-open-level-break.md. Exits scanned from the bar AFTER the fill bar."""
import argparse, gzip, json, numpy as np, pandas as pd

TICK, BIN = 0.25, 1.0

def profile(seg):
    if seg.empty or seg.volume.sum() <= 0: return (np.nan, np.nan, np.nan)
    lo = np.floor(seg.low.values / BIN).astype(np.int64); hi = np.floor(seg.high.values / BIN).astype(np.int64)
    vol = seg.volume.values.astype(float)
    b0, b1 = int(lo.min()), int(hi.max())
    acc = np.zeros(b1 - b0 + 2)
    np.add.at(acc, lo - b0, vol / (hi - lo + 1)); np.add.at(acc, hi - b0 + 1, -vol / (hi - lo + 1))
    rows = np.cumsum(acc)[:-1]
    if rows.sum() <= 0: return (np.nan, np.nan, np.nan)
    i = int(rows.argmax()); tot = rows.sum(); l_i = h_i = i; cum = rows[i]
    while cum < 0.70 * tot and (l_i > 0 or h_i < len(rows) - 1):
        up = rows[h_i+1:h_i+3].sum() if h_i < len(rows)-1 else -1.0
        dn = rows[max(l_i-2,0):l_i].sum() if l_i > 0 else -1.0
        if up >= dn and h_i < len(rows)-1: h_i = min(h_i+2, len(rows)-1)
        elif l_i > 0: l_i = max(l_i-2, 0)
        else: break
        cum = rows[l_i:h_i+1].sum()
    return (float((b0+i)*BIN), float((b0+l_i)*BIN), float((b0+h_i+1)*BIN))   # poc, val, vah

def load(path):
    b = pd.read_parquet(path); t = pd.to_datetime(b.ts_event)
    t = t.dt.tz_convert("America/New_York") if t.dt.tz is not None else t.dt.tz_localize("UTC").dt.tz_convert("America/New_York")
    b = b.set_index(t.dt.tz_localize(None))[["open","high","low","close","volume"]].sort_index()
    b["sess"] = (b.index - pd.Timedelta(hours=18)).normalize()
    return b

def run(bars, stop_mode, cost=0.5):
    out = []
    days = sorted(bars.sess.unique()); prev = None
    for day in days:
        s = bars[bars.sess == day]
        if prev is None or len(prev) < 300 or len(s) < 600: prev = s; continue
        poc, val, vah = profile(prev)
        pdh, pdl = float(prev.high.max()), float(prev.low.min())
        prev = s
        if not all(np.isfinite(x) for x in (poc, val, vah)): continue
        rnd = lambda x: round(x / TICK) * TICK
        levels = sorted({rnd(x) for x in (poc, val, vah, pdh, pdl)})
        breakers = [rnd(x) for x in (vah, val, poc)]
        m = s.resample("5min").agg(open=("open","first"),high=("high","max"),low=("low","min"),
                                   close=("close","last")).dropna()
        if m.empty: continue
        end = m.index + pd.Timedelta(minutes=5)
        t0 = pd.Timestamp(day) + pd.Timedelta(hours=18)
        win = (end > t0) & (end <= t0 + pd.Timedelta(minutes=90))
        o, h, l, c = m.open.values, m.high.values, m.low.values, m.close.values
        sig = None
        for i in np.where(win)[0]:
            rng = h[i] - l[i]
            if rng <= 0: continue
            body = abs(c[i] - o[i])
            if body < 0.5 * rng: continue
            for L in breakers:
                if c[i] > L and o[i] <= L: sig = (i, 1, L); break
                if c[i] < L and o[i] >= L: sig = (i, -1, L); break
            if sig: break
        if sig is None: continue
        i, d, L = sig
        beyond = [x for x in levels if (x > L if d == 1 else x < L)]
        if not beyond: continue
        tgt = min(beyond) if d == 1 else max(beyond)
        stop = (l[i] - TICK if d == 1 else h[i] + TICK) if stop_mode == "S" else L - d * float(stop_mode[1:])
        risk = abs(L - stop)
        if risk <= 0 or abs(tgt - L) <= 0: continue
        ts = s.index.values; H, Lo = s.high.values, s.low.values
        f0 = int(np.searchsorted(ts, np.datetime64(end[i]))); n = len(ts)
        f1 = int(np.searchsorted(ts, np.datetime64(end[i] + pd.Timedelta(hours=4))))
        if f0 >= n: continue
        seg = (Lo[f0:f1] <= L - TICK) if d == 1 else (H[f0:f1] >= L + TICK)
        if not seg.any(): continue
        fill = f0 + int(np.argmax(seg))
        res, r = "FLAT", None
        for k in range(fill + 1, n):                       # exits from the bar AFTER the fill
            hit_s = (Lo[k] <= stop) if d == 1 else (H[k] >= stop)
            hit_t = (H[k] >= tgt) if d == 1 else (Lo[k] <= tgt)
            if hit_s: res, r, ex = "STOP", -1.0, k; break
            if hit_t: res, r, ex = "TARGET", abs(tgt - L)/risk, k; break
        if r is None: ex = n-1; r = d*(s.close.values[-1] - L)/risk
        out.append(dict(day=str(pd.Timestamp(day).date()), dir=d, level=float(L), entry=float(L), stop=float(stop),
                        risk=float(risk), target=float(tgt), rr=float(abs(tgt-L)/risk), res=res, r=float(r),
                        hold_min=int((ts[ex]-ts[fill])/np.timedelta64(1,'m')), fill_hrs=float(fill),
                        target_r=float(abs(tgt-L)/risk), depth=0.0))
    return pd.DataFrame(out)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--bars", required=True); ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True); a = ap.parse_args()
    bars = load(a.bars); nd = bars.sess.nunique()
    print(f"\n{a.label}  ({nd:,} sessions)")
    print(f"  {'stop':<5}{'trades':>8}{'/sess':>7}{'R/trade':>10}{'net R':>9}{'win':>7}{'medRR':>7}{'maxDD':>8}{'medRisk':>9}")
    for sm in ("S","F10","F15","F20","F25","F30"):
        tr = run(bars, sm)
        if len(tr) == 0: print(f"  {sm:<5}   no trades"); continue
        tr["netr"] = tr.r - 0.5/tr.risk
        day = tr.groupby("day").netr.sum(); cum = day.cumsum(); dd = (cum-cum.cummax()).min()
        print(f"  {sm:<5}{len(tr):>8}{len(tr)/nd:>7.2f}{tr.netr.mean():>+10.4f}{tr.netr.sum():>+9.0f}"
              f"{(tr.res=='TARGET').mean():>7.1%}{tr.rr.median():>7.2f}{dd:>+8.1f}{tr.risk.median():>9.1f}")
        with gzip.open(f"{a.out}_{sm}.jsonl.gz","wt") as fh:
            for _, t in tr.iterrows(): fh.write(json.dumps({k:(v.item() if hasattr(v,'item') else v) for k,v in t.items()})+"\n")
