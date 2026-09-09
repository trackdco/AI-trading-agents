#!/usr/bin/env python3
"""Does the DTE execution trigger add anything GIVEN delivery?

The D gate (price inside an un-inverted 1h/4h fair value gap, direction matching) is
positive on all three tapes. The E trigger alone is negative on all three. So the question
is whether E contributes at all, or whether the edge is simply "be inside a higher-timeframe
FVG in the right direction" and the inversion pattern is decoration.

Test: matched random entries with the SAME D gate applied. Same day, same session window,
same direction, same risk in points, same 2R target, same max hold, same cost. Only the
entry bar is randomised, and the random bar must itself pass D.
"""
import argparse, numpy as np, pandas as pd, sys
sys.path.insert(0, "scripts")
from dte_method import load, resample, find_fvgs, htf_zones, TICK, YRS

def zone_arrays(bars, tfs):
    z = htf_zones(bars, tfs)
    if not z: return (np.empty(0),)*5
    s = np.array([x[0] for x in z], np.int64); e = np.array([x[1] for x in z], np.int64)
    lo = np.array([x[2] for x in z]); hi = np.array([x[3] for x in z])
    ib = np.array([x[4] for x in z], bool)
    return s, e, lo, hi, ib

def d_ok(Z, t_ns, px, d):
    """True if price sits inside a matching un-inverted HTF FVG and there is no conflict."""
    s, e, lo, hi, ib = Z
    if len(s) == 0: return False
    m = (s <= t_ns) & (t_ns <= e) & (lo <= px) & (px <= hi)
    if not m.any(): return False
    bull = bool(ib[m].any()); bear = bool((~ib[m]).any())
    if bull and bear: return False                     # conflicting delivery -> skip
    return bull if d == 1 else bear

def outcome(h, l, c, i, d, E, stop, risk, T, hold, n, cost):
    tgt = E + d*T*risk
    for k in range(i+1, min(n, i+1+hold)):
        hs = (h[k] >= stop) if d == -1 else (l[k] <= stop)
        ht = (l[k] <= tgt) if d == -1 else (h[k] >= tgt)
        if hs: return (-risk-cost)/risk, "STOP"
        if ht: return (T*risk-cost)/risk, "TARGET"
    k = min(n-1, i+hold)
    return (d*(c[k]-E)-cost)/risk, "FLAT"

def run(tape, tf, W, B, T, cost, sess, tfs, repeats, seed, maxhold=120):
    raw = load(tape); b = resample(raw, tf)
    o, h, l, c = (b[x].values.astype(float) for x in ("open", "high", "low", "close"))
    n = len(c)
    bull, bear, zlo, zhi = find_fvgs(h, l)
    Z = zone_arrays(raw, tfs)
    ns = b.index.values.astype("datetime64[ns]").astype(np.int64)
    tmin = (b.index.hour*60 + b.index.minute).values
    t0, t1 = sess; inwin = (tmin >= t0) & (tmin < t1)
    day = b.index.normalize().values
    body = np.abs(c-o); rng = h-l
    hold = max(1, maxhold//tf)
    rng_ = np.random.default_rng(seed)
    dayb = {dd: np.where((day == dd) & inwin)[0] for dd in np.unique(day[inwin])}
    real, rand = [], []
    busy = -1
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
            stop = apex + TICK if d == -1 else apex - TICK
            risk = (stop-E) if d == -1 else (E-stop)
            if risk <= 0 or risk > 80: break
            if not d_ok(Z, ns[i], E, d): break          # D gate on the REAL entry
            busy = i+1
            r, res = outcome(h, l, c, i, d, E, stop, risk, T, hold, n, cost)
            real.append(dict(tape=tape, r=r, res=res))
            pool = dayb.get(day[i])
            if pool is None or len(pool) < 3: continue
            for _ in range(repeats):
                j = int(rng_.choice(pool[:-1]))
                if j <= 40 or j >= n-2: continue
                Ej = c[j]
                if not d_ok(Z, ns[j], Ej, d): continue   # D gate on the RANDOM entry too
                sj = Ej + d*(-risk) if False else (Ej + risk if d == -1 else Ej - risk)
                rr, rs = outcome(h, l, c, j, d, Ej, sj, risk, T, hold, n, cost)
                rand.append(dict(tape=tape, r=rr, res=rs))
            break
    return pd.DataFrame(real), pd.DataFrame(rand)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tapes", default="2023-26,2020-22,2017-19")
    ap.add_argument("--tf", type=int, default=1); ap.add_argument("--W", type=int, default=6)
    ap.add_argument("--B", type=float, default=0.6); ap.add_argument("--T", type=float, default=2.0)
    ap.add_argument("--cost", type=float, default=0.75); ap.add_argument("--sess", default="570,660")
    ap.add_argument("--htf", default="60,240"); ap.add_argument("--repeats", type=int, default=10)
    ap.add_argument("--seed", type=int, default=31)
    a = ap.parse_args()
    s0, s1 = (int(x) for x in a.sess.split(","))
    tfs = [int(x) for x in a.htf.split(",")]
    print(f"D gate = inside an un-inverted {'/'.join(str(x)+'m' for x in tfs)} FVG, direction matching\n")
    allR, allQ = [], []
    for tp in a.tapes.split(","):
        R, Q = run(tp, a.tf, a.W, a.B, a.T, a.cost, (s0, s1), tfs, a.repeats, a.seed)
        allR.append(R); allQ.append(Q)
        if len(R) < 20 or len(Q) < 20:
            print(f"  {tp}: too few ({len(R)}/{len(Q)})"); continue
        se = R.r.std(ddof=1)/np.sqrt(len(R))
        print(f"  {tp}:  DTE+D  n={len(R):5d}  R {R.r.mean():+.4f}  t {R.r.mean()/se:+.2f}  "
              f"win {(R.res=='TARGET').mean():5.1%}   |   RANDOM+D  n={len(Q):6d}  "
              f"R {Q.r.mean():+.4f}  win {(Q.res=='TARGET').mean():5.1%}   |   "
              f"EDGE {R.r.mean()-Q.r.mean():+.4f}")
    R = pd.concat(allR); Q = pd.concat(allQ)
    se = R.r.std(ddof=1)/np.sqrt(len(R))
    print(f"\n  POOLED: DTE+D n={len(R)} R {R.r.mean():+.4f} t {R.r.mean()/se:+.2f} "
          f"win {(R.res=='TARGET').mean():.1%}  |  RANDOM+D n={len(Q)} R {Q.r.mean():+.4f} "
          f"win {(Q.res=='TARGET').mean():.1%}  |  EDGE {R.r.mean()-Q.r.mean():+.4f}")
    print(f"\n  declared bar wanted the rule to beat random by > +0.10 R")
