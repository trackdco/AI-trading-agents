#!/usr/bin/env python3
"""15-minute pivot breakout - the plain core of the nq-asim idea, no KNN, no macro filters.
Rules frozen in docs/PREREG-pivot-breakout-15m.md. Exits scanned from the bar AFTER entry."""
import argparse, gzip, json, sys
import numpy as np, pandas as pd

TICK = 0.25
def wilder(x, n):
    a = np.empty_like(x); a[:] = np.nan
    if len(x) < n: return a
    a[n-1] = np.nanmean(x[:n])
    for i in range(n, len(x)):
        a[i] = (a[i-1]*(n-1) + x[i]) / n
    return a

def indicators(df):
    h, l, c = df.high.values, df.low.values, df.close.values
    pc = np.roll(c, 1); pc[0] = c[0]
    tr = np.maximum(h-l, np.maximum(np.abs(h-pc), np.abs(l-pc)))
    atr = wilder(tr, 14)
    up = h - np.roll(h, 1); dn = np.roll(l, 1) - l
    up[0] = dn[0] = 0.0
    pdm = np.where((up > dn) & (up > 0), up, 0.0)
    ndm = np.where((dn > up) & (dn > 0), dn, 0.0)
    pdi = 100 * wilder(pdm, 14) / np.where(atr > 0, atr, np.nan)
    ndi = 100 * wilder(ndm, 14) / np.where(atr > 0, atr, np.nan)
    dx = 100 * np.abs(pdi - ndi) / np.where((pdi+ndi) > 0, pdi+ndi, np.nan)
    adx = wilder(np.nan_to_num(dx), 14)
    ema = pd.Series(c).ewm(span=200, adjust=False).mean().values
    rvol = df.volume.values / pd.Series(df.volume.values).rolling(20).mean().values
    return ema, rvol, adx, atr

def pivots(h, l, lb):
    """pivot_low[i] = level of the most recent pivot low CONFIRMED at or before bar i (and its index)."""
    n = len(h); plo = np.full(n, np.nan); phi = np.full(n, np.nan)
    lo_lvl = hi_lvl = np.nan
    for i in range(n):
        j = i - lb                       # candidate pivot bar, confirmed now
        if j - lb >= 0:
            w_l = l[j-lb:j+lb+1]; w_h = h[j-lb:j+lb+1]
            if l[j] == w_l.min() and (w_l < l[j]).sum() == 0 and (w_l == l[j]).sum() == 1: lo_lvl = l[j]
            if h[j] == w_h.max() and (w_h > h[j]).sum() == 0 and (w_h == h[j]).sum() == 1: hi_lvl = h[j]
        plo[i] = lo_lvl; phi[i] = hi_lvl
    return plo, phi

def run(bars, side, lb=6, rvol_min=1.2, adx_min=20.0, tp1_r=None, trail_x=None, cost=0.5):
    tp1_r = tp1_r if tp1_r is not None else (2.6 if side == "short" else 1.7)
    trail_x = trail_x if trail_x is not None else (2.0 if side == "short" else 1.25)
    d = -1 if side == "short" else 1
    trades = []
    for day, g in bars.groupby("sess"):
        g = g.reset_index(drop=True)
        if len(g) < 30: continue
        ema, rvol, adx, atr = g.ema.values, g.rvol.values, g.adx.values, g.atr.values
        plo, phi = g.plo.values, g.phi.values
        h, l, c = g.high.values, g.low.values, g.close.values
        n = len(g); used = set(); i = 0
        while i < n - 1:
            lvl = plo[i] if d == -1 else phi[i]
            ok = (not np.isnan(lvl)) and (not np.isnan(ema[i])) and (not np.isnan(adx[i])) \
                 and (not np.isnan(rvol[i])) and (not np.isnan(atr[i])) and atr[i] > 0
            if ok:
                broke = (c[i] < lvl) if d == -1 else (c[i] > lvl)
                trend = (c[i] < ema[i]) if d == -1 else (c[i] > ema[i])
                if broke and trend and rvol[i] >= rvol_min and adx[i] >= adx_min and round(lvl, 2) not in used:
                    used.add(round(lvl, 2))
                    E = c[i]
                    stop = (h[max(0, i-lb):i+1].max() + TICK) if d == -1 else (l[max(0, i-lb):i+1].min() - TICK)
                    risk = abs(E - stop)
                    if risk <= 0: i += 1; continue
                    tp1 = E + d * tp1_r * risk
                    r1 = r2 = None; stop_run = stop; trail = np.nan; k = i + 1
                    while k < n:
                        hit_stop = (h[k] >= stop_run) if d == -1 else (l[k] <= stop_run)
                        hit_tp1 = (l[k] <= tp1) if d == -1 else (h[k] >= tp1)
                        if r1 is None:
                            if hit_stop: r1 = r2 = -1.0; break            # tie -> stop
                            if hit_tp1:
                                r1 = tp1_r                                 # half off at the target
                                stop_run = E                               # runner to breakeven
                                trail = c[k] + trail_x*atr[k] if d == -1 else c[k] - trail_x*atr[k]
                                stop_run = min(stop_run, trail) if d == -1 else max(stop_run, trail)
                                k += 1; continue
                        else:
                            if hit_stop:
                                r2 = d * (stop_run - E) / risk; break
                            t = c[k] + trail_x*atr[k] if d == -1 else c[k] - trail_x*atr[k]
                            trail = min(trail, t) if d == -1 else max(trail, t)
                            stop_run = min(stop_run, trail) if d == -1 else max(stop_run, trail)
                        k += 1
                    if r1 is None:
                        r1 = d * (c[n-1] - E) / risk; r2 = r1                    # flat at session end
                    elif r2 is None:
                        r2 = d * (c[n-1] - E) / risk                              # runner flat at end
                    r = 0.5*r1 + 0.5*r2
                    trades.append(dict(day=str(day), dir=d, entry=float(E), stop=float(stop), risk=float(risk),
                                       r=float(r), r1=float(r1), r2=float(r2),
                                       res="TARGET" if r > 0 else ("STOP" if r <= -0.999 else "SCRATCH"),
                                       hold_min=int((min(k, n-1) - i) * 15), fill_hrs=float(i), target_r=tp1_r, depth=0.0))
                    i = min(k, n-1) + 1; continue
            i += 1
    return pd.DataFrame(trades)

def load(path):
    b = pd.read_parquet(path)
    t = pd.to_datetime(b.ts_event)
    t = t.dt.tz_convert("America/New_York") if t.dt.tz is not None else t.dt.tz_localize("UTC").dt.tz_convert("America/New_York")
    b = b.set_index(t.dt.tz_localize(None))[["open","high","low","close","volume"]].sort_index()
    m = b.resample("15min").agg(open=("open","first"),high=("high","max"),low=("low","min"),
                                close=("close","last"),volume=("volume","sum")).dropna(subset=["close"])
    m["sess"] = (m.index - pd.Timedelta(hours=18)).date
    ema, rvol, adx, atr = indicators(m)
    m["ema"], m["rvol"], m["adx"], m["atr"] = ema, rvol, adx, atr
    plo, phi = pivots(m.high.values, m.low.values, 6)
    m["plo"], m["phi"] = plo, phi
    m = m.reset_index(); m.columns = ["ts"] + list(m.columns[1:]); return m

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--bars", required=True); ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    m = load(a.bars)
    print(f"{a.label}: {len(m):,} 15m bars, {m.sess.nunique():,} sessions, {m.ts.min()} -> {m.ts.max()}", flush=True)
    for side in ("short","long"):
        tr = run(m, side)
        if len(tr) == 0: print(f"  {side}: no trades"); continue
        tr["netr"] = tr.r - 0.5/tr.risk
        day = tr.groupby("day").netr.sum(); cum = day.cumsum(); dd = (cum-cum.cummax()).min()
        print(f"  {side:<5}: {len(tr):>5} trades | {tr.netr.mean():+.4f} R/trade | net {tr.netr.sum():+,.0f}R | "
              f"win {(tr.r>0).mean():.1%} | maxDD {dd:+.1f} | median risk {tr.risk.median():.1f}pt", flush=True)
        with gzip.open(f"{a.out}_{side}.jsonl.gz","wt") as fh:
            for _,t in tr.iterrows(): fh.write(json.dumps({k:(v.item() if hasattr(v,'item') else v) for k,v in t.items()})+"\n")
