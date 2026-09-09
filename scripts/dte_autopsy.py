#!/usr/bin/env python3
"""DTE loser autopsy — every gate recorded as a FEATURE, not applied as a filter.

Runs the E trigger (V-spike inversion FVG) with D and T switched OFF, then records for
each trade: whether D would have passed, how much low-resistance liquidity existed, and a
full feature set — order flow from the footprint, session VWAP bands, fib levels of the
last prominent leg, and the BB(20) middle SMA. Then asks which of them separate winners
from losers, which is the only way to test the claim that the gates ARE the edge.
"""
import argparse, sys, numpy as np, pandas as pd
sys.path.insert(0, "scripts")
from dte_method import load, resample, find_fvgs, htf_zones, htf_state, TICK, YRS
from sma20_orderflow import load_footprint

FIBS = [0.382, 0.5, 0.618, 0.705, 0.786]

def atr(h, l, c, n=14):
    pc = np.roll(c, 1); pc[0] = c[0]
    tr = np.maximum(h-l, np.maximum(abs(h-pc), abs(l-pc)))
    return pd.Series(tr).rolling(n).mean().values

def session_vwap(b):
    """18:00-anchored session VWAP on the open, with +/-1/2 sd bands. Causal."""
    sess = (b.index - pd.Timedelta(hours=18)).normalize()
    px = b.open.values.astype(float); v = b.volume.values.astype(float)
    df = pd.DataFrame({"s": sess, "pv": px*v, "v": v, "pv2": px*px*v})
    g = df.groupby("s").cumsum()
    vwap = g.pv/g.v
    var = (g.pv2/g.v - vwap**2).clip(lower=0)
    sd = np.sqrt(var)
    return vwap.values, sd.values

def pivots(h, l, k):
    n = len(h); ph = np.zeros(n, bool); pl = np.zeros(n, bool)
    for i in range(k, n-k):
        w = slice(i-k, i+k+1)
        if h[i] == h[w].max() and (h[w] == h[i]).sum() == 1: ph[i] = True
        if l[i] == l[w].min() and (l[w] == l[i]).sum() == 1: pl[i] = True
    return ph, pl

def fib_leg(h, l, dph, dpl, i, d):
    """Last prominent leg in the trade direction; None if price broke its origin first."""
    k = 12; hi_j = lo_j = None
    for j in range(i-k, max(0, i-500), -1):
        if d == 1 and dph[j] and hi_j is None: hi_j = j
        if d == -1 and dpl[j] and lo_j is None: lo_j = j
        if d == 1 and hi_j is not None and dpl[j] and j < hi_j: lo_j = j; break
        if d == -1 and lo_j is not None and dph[j] and j < lo_j: hi_j = j; break
    if hi_j is None or lo_j is None: return None
    if d == 1 and l[lo_j:i+1].min() < l[lo_j]: return None
    if d == -1 and h[hi_j:i+1].max() > h[hi_j]: return None
    return l[lo_j], h[hi_j]

def untapped(h, l, ph, pl, i, look=240, k=2):
    lows = highs = 0
    a = max(0, i-look)
    for j in range(a, i-k):
        if pl[j] and l[j] < l[i] and l[j+1:i+1].min() > l[j]: lows += 1
        if ph[j] and h[j] > h[i] and h[j+1:i+1].max() < h[j]: highs += 1
    return lows, highs

def bar_delta(fts, fsg, fvl, ns0, ns1):
    a = np.searchsorted(fts, ns0); z = np.searchsorted(fts, ns1)
    if z-a < 5: return np.nan, np.nan
    return float((fsg[a:z]*fvl[a:z]).sum()), float(fvl[a:z].sum())

def wick_delta(fts, fpx, fsg, fvl, ns0, ns1, edge, d):
    a = np.searchsorted(fts, ns0); z = np.searchsorted(fts, ns1)
    if z-a < 5: return np.nan
    px = fpx[a:z]; sg = fsg[a:z]; vl = fvl[a:z]
    m = (px <= edge) if d == 1 else (px >= edge)
    if not m.any(): return np.nan
    return float((sg[m]*vl[m]).sum())

def build(tape, tf, W, B, T, cost, sess, fpk, maxhold=120):
    raw = load(tape); b = resample(raw, tf)
    o, h, l, c = (b[x].values.astype(float) for x in ("open", "high", "low", "close"))
    vol = b.volume.values.astype(float); n = len(c)
    bull, bear, zlo, zhi = find_fvgs(h, l)
    a14 = atr(h, l, c)
    sma20 = pd.Series(c).rolling(20).mean().values
    bbsd = pd.Series(c).rolling(20).std().values
    vwap, vsd = session_vwap(b)
    ph2, pl2 = pivots(h, l, 2); dph, dpl = pivots(h, l, 10)
    z15 = htf_zones(raw, [15]); z60 = htf_zones(raw, [60]); z240 = htf_zones(raw, [240])
    ns = b.index.values.astype("datetime64[ns]").astype(np.int64)
    barns = tf*60*1_000_000_000
    tmin = (b.index.hour*60 + b.index.minute).values
    t0, t1 = sess
    body = np.abs(c-o); rng = h-l
    hold = max(1, maxhold//tf)
    fts, fpx, fsg, fvl = fpk if fpk else (None,)*4
    rows = []; busy = -1

    for f in np.where(bull | bear)[0]:
        lo_, hi_ = zlo[f], zhi[f]; is_bull = bool(bull[f])
        for i in range(f+1, min(n, f+1+W)):
            if not ((c[i] < lo_) if is_bull else (c[i] > hi_)): continue
            d = -1 if is_bull else 1
            if i <= 40 or i >= n-2 or i < busy: break
            if not (t0 <= tmin[i] < t1): break
            if rng[i] <= 0 or body[i]/rng[i] < B: break
            if (d == 1 and c[i] <= o[i]) or (d == -1 and c[i] >= o[i]): break
            E = c[i]
            apex = h[f:i+1].max() if d == -1 else l[f:i+1].min()
            stop = apex + TICK if d == -1 else apex - TICK
            risk = (stop-E) if d == -1 else (E-stop)
            if risk <= 0 or risk > 80: break
            busy = i+1
            tgt = E + d*T*risk; res = "FLAT"; pnl = None
            for k in range(i+1, min(n, i+1+hold)):
                hs = (h[k] >= stop) if d == -1 else (l[k] <= stop)
                ht = (l[k] <= tgt) if d == -1 else (h[k] >= tgt)
                if hs: pnl, res = -risk, "STOP"; break
                if ht: pnl, res = T*risk, "TARGET"; break
            if pnl is None: k = min(n-1, i+hold); pnl = d*(c[k]-E)

            A = a14[i] if np.isfinite(a14[i]) and a14[i] > 0 else np.nan
            lows, highs = untapped(h, l, ph2, pl2, i)
            # --- D gate as a FEATURE, per higher timeframe ---
            dfl = {}
            for nm, zz in (("15", z15), ("60", z60), ("240", z240)):
                ib, ie = htf_state(zz, ns[i], E)
                dfl[f"D{nm}_ok"] = (ib if d == 1 else ie)
                dfl[f"D{nm}_conflict"] = (ib and ie)
            # --- order flow ---
            bd = bv = wd = np.nan
            if fts is not None:
                bd, bv = bar_delta(fts, fsg, fvl, ns[i], ns[i]+barns)
                vd, _ = bar_delta(fts, fsg, fvl, ns[f], ns[i]+barns)
                edge = min(o[i], c[i]) if d == 1 else max(o[i], c[i])
                wd = wick_delta(fts, fpx, fsg, fvl, ns[i], ns[i]+barns, edge, d)
            else:
                vd = np.nan
            leg = fib_leg(h, l, dph, dpl, i, d)
            row = dict(tape=tape, day=str(b.index[i].date()), ts=str(b.index[i]), dir=d,
                       entry=E, risk=risk, res=res, r=(pnl-cost)/risk, hold=(k-i)*tf,
                       vwin=i-f, disp=body[i]/rng[i], risk_atr=risk/A if A == A else np.nan,
                       atr=A, mins_in=tmin[i]-t0, vol_z=vol[i]/np.nanmean(vol[max(0,i-20):i]),
                       lrlq=(lows if d == -1 else highs),
                       lrlq_wrong=(highs if d == -1 else lows),
                       # order flow, signed so positive = flow WITH the trade
                       bar_delta=d*bd, bar_ratio=(d*bd/bv) if bv and bv == bv else np.nan,
                       vwin_delta=d*vd, wick_delta=d*wd,
                       # bands and levels, distance in ATR
                       d_sma20=abs(E-sma20[i])/A if A == A else np.nan,
                       bb_w=(2*bbsd[i]/A) if A == A else np.nan,
                       d_vwap=abs(E-vwap[i])/A if A == A else np.nan,
                       d_vwap_p1=abs(E-(vwap[i]+vsd[i]))/A if A == A else np.nan,
                       d_vwap_m1=abs(E-(vwap[i]-vsd[i]))/A if A == A else np.nan,
                       d_vwap_p2=abs(E-(vwap[i]+2*vsd[i]))/A if A == A else np.nan,
                       d_vwap_m2=abs(E-(vwap[i]-2*vsd[i]))/A if A == A else np.nan,
                       vwap_sd=(E-vwap[i])/vsd[i] if vsd[i] > 0 else np.nan,
                       **dfl)
            if leg:
                lo2, hi2 = leg
                for fb in FIBS:
                    row[f"d_fib{fb}"] = abs(E-(hi2-fb*(hi2-lo2)))/A if A == A else np.nan
                row["fib_depth"] = ((hi2-E)/(hi2-lo2)) if d == 1 else ((E-lo2)/(hi2-lo2))
            else:
                for fb in FIBS: row[f"d_fib{fb}"] = np.nan
                row["fib_depth"] = np.nan
            rows.append(row)
            break
    return pd.DataFrame(rows)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tapes", default="2023-26,2020-22,2017-19")
    ap.add_argument("--tf", type=int, default=1); ap.add_argument("--W", type=int, default=6)
    ap.add_argument("--B", type=float, default=0.6); ap.add_argument("--T", type=float, default=2.0)
    ap.add_argument("--cost", type=float, default=0.75); ap.add_argument("--sess", default="570,660")
    ap.add_argument("--flow", action="store_true", help="attach footprint order flow (2023-26 only)")
    ap.add_argument("--out", default="data/debug/dte_autopsy.csv")
    a = ap.parse_args()
    s0, s1 = (int(x) for x in a.sess.split(","))
    fpk = None
    if a.flow:
        print("loading footprint...", flush=True); fpk = load_footprint(8*60, 12*60)
        print(f"  {len(fpk[0]):,} rows", flush=True)
    out = []
    for tp in a.tapes.split(","):
        d = build(tp, a.tf, a.W, a.B, a.T, a.cost, (s0, s1), fpk)
        print(f"  {tp}: {len(d)} trades", flush=True); out.append(d)
    d = pd.concat(out); d.to_csv(a.out, index=False)
    print(f"\n{len(d)} trades, {d.shape[1]} columns -> {a.out}")
