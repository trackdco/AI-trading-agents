#!/usr/bin/env python3
"""Cross-market port of DTE + D(1h/4h). Frozen rule, new instruments.

Declared in the addendum to docs/PREREG-dte-method.md. NQ-3min is the CONTROL: a positive
result on ES or GC means nothing unless NQ is also positive on the same 3-minute venue.
"""
import argparse, numpy as np, pandas as pd, sys
sys.path.insert(0, "scripts")
from dte_method import find_fvgs

TICKS = {"NQ": 0.25, "ES": 0.25, "RTY": 0.10, "YM": 1.0, "GC": 0.10}
COST_TICKS = 3.0
MAX_RISK_TICKS = 320.0

def resample(b, tf):
    if tf == 3: return b
    r = b.resample(f"{tf}min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
    return r.dropna()

def zone_arrays(bars, tfs):
    S, E, LO, HI, IB = [], [], [], [], []
    for tf in tfs:
        r = resample(bars, tf)
        h, l, c = (r[x].values.astype(float) for x in ("high", "low", "close"))
        ns = r.index.values.astype("datetime64[ns]").astype(np.int64)
        bull, bear, zlo, zhi = find_fvgs(h, l)
        step = tf*60*1_000_000_000
        for i in np.where(bull | bear)[0]:
            lo, hi = zlo[i], zhi[i]; is_bull = bool(bull[i])
            end = len(c)-1
            for j in range(i+1, len(c)):
                if (is_bull and c[j] < lo) or ((not is_bull) and c[j] > hi):
                    end = j; break
            S.append(ns[i]+step); E.append(ns[end]); LO.append(lo); HI.append(hi); IB.append(is_bull)
    return (np.array(S, np.int64), np.array(E, np.int64), np.array(LO),
            np.array(HI), np.array(IB, bool))

def d_ok(Z, t_ns, px, d):
    S, E, LO, HI, IB = Z
    if len(S) == 0: return False
    m = (S <= t_ns) & (t_ns <= E) & (LO <= px) & (px <= HI)
    if not m.any(): return False
    bull = bool(IB[m].any()); bear = bool((~IB[m]).any())
    if bull and bear: return False
    return bull if d == 1 else bear

def run(sym, tf, W, B, T, sess, maxhold=120):
    tick = TICKS[sym]; cost = COST_TICKS*tick; maxrisk = MAX_RISK_TICKS*tick
    raw = pd.read_parquet(f"data/reference/algotrader_3min/{sym}_3min.parquet")
    b = resample(raw, tf)
    o, h, l, c = (b[x].values.astype(float) for x in ("open", "high", "low", "close"))
    n = len(c)
    bull, bear, zlo, zhi = find_fvgs(h, l)
    Z = zone_arrays(raw, [60, 240])
    ns = b.index.values.astype("datetime64[ns]").astype(np.int64)
    tmin = (b.index.hour*60 + b.index.minute).values
    t0, t1 = sess; inwin = (tmin >= t0) & (tmin < t1)
    body = np.abs(c-o); rng = h-l
    hold = max(1, maxhold//tf); rows = []; busy = -1
    for f in np.where(bull | bear)[0]:
        lo_, hi_ = zlo[f], zhi[f]; is_bull = bool(bull[f])
        for i in range(f+1, min(n, f+1+W)):
            if not ((c[i] < lo_) if is_bull else (c[i] > hi_)): continue
            d = -1 if is_bull else 1
            if i <= 40 or i >= n-2 or i < busy: break
            if not inwin[i]: break
            if rng[i] <= 0 or body[i]/rng[i] < B: break
            if (d == 1 and c[i] <= o[i]) or (d == -1 and c[i] >= o[i]): break
            E = c[i]
            apex = h[f:i+1].max() if d == -1 else l[f:i+1].min()
            stop = apex + tick if d == -1 else apex - tick
            risk = (stop-E) if d == -1 else (E-stop)
            if risk <= 0 or risk > maxrisk: break
            if not d_ok(Z, ns[i], E, d): break
            busy = i+1
            tgt = E + d*T*risk; res = "FLAT"; pnl = None
            for k in range(i+1, min(n, i+1+hold)):
                hs = (h[k] >= stop) if d == -1 else (l[k] <= stop)
                ht = (l[k] <= tgt) if d == -1 else (h[k] >= tgt)
                if hs: pnl, res = -risk, "STOP"; break
                if ht: pnl, res = T*risk, "TARGET"; break
            if pnl is None: k = min(n-1, i+hold); pnl = d*(c[k]-E)
            rows.append(dict(sym=sym, day=str(b.index[i].date()), dir=d, risk=risk,
                             res=res, r=(pnl-cost)/risk))
            break
    return pd.DataFrame(rows)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--syms", default="NQ,ES,RTY,YM,GC")
    ap.add_argument("--tf", type=int, default=3); ap.add_argument("--W", type=int, default=6)
    ap.add_argument("--B", type=float, default=0.6); ap.add_argument("--T", type=float, default=2.0)
    ap.add_argument("--sess", default="570,660")
    ap.add_argument("--out", default="data/debug/dte_port.csv")
    a = ap.parse_args()
    s0, s1 = (int(x) for x in a.sess.split(","))
    rows, dumps = [], []
    for sym in a.syms.split(","):
        t = run(sym, a.tf, a.W, a.B, a.T, (s0, s1))
        if len(t) < 30:
            print(f"  {sym}: only {len(t)} trades"); continue
        dumps.append(t)
        r = t.r.values; w = r[r > 0]; L = r[r < 0]
        eq = np.cumsum(r); pk = np.maximum.accumulate(np.concatenate([[0], eq]))[1:]
        cut = t.day.sort_values().iloc[len(t)//2]
        rows.append(dict(sym=sym, n=len(r), per_wk=len(r)/5.17/52, R=r.mean(),
                         win=(t.res == "TARGET").mean(), PF=(w.sum()/-L.sum()) if len(L) else np.inf,
                         t=r.mean()/(r.std(ddof=1)/np.sqrt(len(r))),
                         H1=t[t.day < cut].r.mean(), H2=t[t.day >= cut].r.mean(),
                         maxDD=float(np.max(pk-eq)), medRisk_ticks=t.risk.median()/TICKS[sym],
                         drop3=np.sort(r)[:-3].mean()))
        print(f"  {sym} done", flush=True)
    d = pd.DataFrame(rows); pd.concat(dumps).to_csv(a.out, index=False)
    pd.set_option("display.width", 220)
    print(f"\nDTE + D(1h/4h) PORTED — 3-minute bars, 2021-04 to 2026-06, 3 ticks cost, "
          f"1:2 target, break-even 33.3%\n")
    print(d.to_string(index=False, float_format=lambda x: f"{x:+.4f}"))
    ok = d[(d.R > 0) & (d.H1 > 0) & (d.H2 > 0) & (d.win > 1/3)]
    print(f"\nmarkets passing the declared bar (R>0, both halves>0, win>33.3%): "
          f"{len(ok)} of {len(d)}  {list(ok.sym)}")
