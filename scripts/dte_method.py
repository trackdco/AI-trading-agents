#!/usr/bin/env python3
"""The DTE method — delivery / target / execution. Frozen in docs/PREREG-dte-method.md.

D  price inside an un-inverted higher-timeframe FVG, direction matching (conflict = skip)
T  >= L untapped swing levels in the trade direction (low-resistance liquidity)
E  a V-spike inversion FVG: FVG forms, price closes through it within W bars, with
   displacement on the inverting candle

Entry at the inversion bar's close. Stop at the V's apex. Exits scanned from the bar AFTER
entry; a bar touching both stop and target counts STOP.
"""
import argparse, itertools, numpy as np, pandas as pd

TICK = 0.25
TAPES = {
    "2017-19": ["data/reference/nq_2017_2019_1m.parquet"],
    "2020-22": ["data/reference/nq_2020_2022_1m.parquet"],
    "2023-26": ["data/reference/nq_1m_master.parquet",
                "data/reference/nq_1m_jul_sep2026.parquet"],
}

def to_et(s):
    s = pd.to_datetime(s)
    s = s.dt.tz_convert("America/New_York") if s.dt.tz is not None else \
        s.dt.tz_localize("UTC").dt.tz_convert("America/New_York")
    return s.dt.tz_localize(None)

def load(tape):
    out = []
    for f in TAPES[tape]:
        b = pd.read_parquet(f); b.index = to_et(b.ts_event)
        out.append(b[["open", "high", "low", "close", "volume"]])
    b = pd.concat(out)
    return b[~b.index.duplicated()].sort_index()

def resample(b, tf):
    if tf == 1: return b
    r = b.resample(f"{tf}min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
    return r.dropna()

def find_fvgs(h, l):
    """Returns (idx, is_bull, zone_lo, zone_hi) for every FVG. Detected at bar i using i-2..i."""
    n = len(h)
    bull = np.zeros(n, bool); bear = np.zeros(n, bool)
    zlo = np.full(n, np.nan); zhi = np.full(n, np.nan)
    for i in range(2, n):
        if l[i] > h[i-2]:
            bull[i] = True; zlo[i] = h[i-2]; zhi[i] = l[i]
        elif h[i] < l[i-2]:
            bear[i] = True; zlo[i] = h[i]; zhi[i] = l[i-2]
    return bull, bear, zlo, zhi

def htf_zones(bars, tfs):
    """Un-inverted HTF FVG zones as (start_ns, end_ns, lo, hi, is_bull) tuples."""
    zones = []
    for tf in tfs:
        r = resample(bars, tf)
        h, l, c = (r[x].values.astype(float) for x in ("high", "low", "close"))
        ns = r.index.values.astype("datetime64[ns]").astype(np.int64)
        bull, bear, zlo, zhi = find_fvgs(h, l)
        step = tf * 60 * 1_000_000_000
        for i in np.where(bull | bear)[0]:
            lo, hi = zlo[i], zhi[i]
            is_bull = bool(bull[i])
            # the zone lives until a close inverts it (below lo if bullish, above hi if bearish)
            end = len(c) - 1
            for j in range(i+1, len(c)):
                if (is_bull and c[j] < lo) or ((not is_bull) and c[j] > hi):
                    end = j; break
            zones.append((ns[i] + step, ns[end], lo, hi, is_bull))
    return zones

def htf_state(zones, t_ns, px):
    """Returns (in_bull, in_bear) for a price/time against the HTF zone set."""
    ib = ie = False
    for s, e, lo, hi, is_bull in zones:
        if s <= t_ns <= e and lo <= px <= hi:
            if is_bull: ib = True
            else: ie = True
    return ib, ie

def untapped_counts(h, l, k=2, look=240):
    """For every bar: how many untapped swing lows sit below, and swing highs above."""
    n = len(h)
    ph = np.zeros(n, bool); pl = np.zeros(n, bool)
    for i in range(k, n-k):
        w = slice(i-k, i+k+1)
        if h[i] == h[w].max() and (h[w] == h[i]).sum() == 1: ph[i] = True
        if l[i] == l[w].min() and (l[w] == l[i]).sum() == 1: pl[i] = True
    lows_below = np.zeros(n, int); highs_above = np.zeros(n, int)
    for i in range(n):
        a = max(0, i-look)
        cl = 0
        for j in range(a, i-k):
            if pl[j] and l[j] < l[i] and l[j+1:i+1].min() > l[j]:  # untapped since forming
                cl += 1
        ch = 0
        for j in range(a, i-k):
            if ph[j] and h[j] > h[i] and h[j+1:i+1].max() < h[j]:
                ch += 1
        lows_below[i] = cl; highs_above[i] = ch
    return lows_below, highs_above

def run(bars, tf, W, B, L, T, htfs, cost, sess, maxhold=120):
    b = resample(bars, tf)
    o, h, l, c = (b[x].values.astype(float) for x in ("open", "high", "low", "close"))
    n = len(c)
    bull, bear, zlo, zhi = find_fvgs(h, l)
    zones = htf_zones(bars, htfs) if htfs else None
    lows_below, highs_above = untapped_counts(h, l) if L > 0 else (None, None)
    ns = b.index.values.astype("datetime64[ns]").astype(np.int64)
    tmin = (b.index.hour*60 + b.index.minute).values
    t0, t1 = sess
    body = np.abs(c-o); rng = h-l
    hold = max(1, maxhold//tf)
    rows = []; busy = -1

    fvg_idx = np.where(bull | bear)[0]
    for f in fvg_idx:
        lo, hi = zlo[f], zhi[f]
        is_bull = bool(bull[f])
        for i in range(f+1, min(n, f+1+W)):
            inverted = (c[i] < lo) if is_bull else (c[i] > hi)
            if not inverted: continue
            d = -1 if is_bull else 1              # bullish FVG inverted -> SHORT
            if i <= 5 or i >= n-2 or i < busy: break
            if not (t0 <= tmin[i] < t1): break
            if rng[i] <= 0 or body[i]/rng[i] < B: break
            if (d == 1 and c[i] <= o[i]) or (d == -1 and c[i] >= o[i]): break
            E = c[i]
            if zones is not None:
                ib, ie = htf_state(zones, ns[i], E)
                if ib and ie: break                       # conflicting HTF FVGs
                if d == 1 and not ib: break               # long needs bullish delivery
                if d == -1 and not ie: break
            if L > 0:
                have = lows_below[i] if d == -1 else highs_above[i]
                if have < L: break
            apex = h[f:i+1].max() if d == -1 else l[f:i+1].min()
            stop = apex + TICK if d == -1 else apex - TICK
            risk = (stop - E) if d == -1 else (E - stop)
            if risk <= 0 or risk > 80: break
            busy = i + 1
            tgt = E + d*T*risk; res = "FLAT"; pnl = None
            for k in range(i+1, min(n, i+1+hold)):
                hs = (h[k] >= stop) if d == -1 else (l[k] <= stop)
                ht = (l[k] <= tgt) if d == -1 else (h[k] >= tgt)
                if hs: pnl, res = -risk, "STOP"; break
                if ht: pnl, res = T*risk, "TARGET"; break
            if pnl is None: k = min(n-1, i+hold); pnl = d*(c[k]-E)
            rows.append(dict(day=str(b.index[i].date()), ts=str(b.index[i]), dir=d,
                             entry=E, risk=risk, res=res, r=(pnl-cost)/risk,
                             hold=(k-i)*tf, vwin=i-f))
            break
    return pd.DataFrame(rows)

def summarise(t, tape, tag, yrs):
    if len(t) < 10: return None
    r = t.r.values; w = r[r > 0]; ls = r[r < 0]
    eq = np.cumsum(r); pk = np.maximum.accumulate(np.concatenate([[0], eq]))[1:]
    cut = t.day.sort_values().iloc[len(t)//2]
    be = 1/(1+tag["T"])
    return dict(tape=tape, **tag, n=len(t), per_wk=len(t)/yrs/52,
                R=r.mean(), win=(t.res == "TARGET").mean(), be=be,
                excess=(t.res == "TARGET").mean()-be,
                PF=(w.sum()/-ls.sum()) if len(ls) else np.inf,
                t=r.mean()/(r.std(ddof=1)/np.sqrt(len(r))) if len(r) > 2 else np.nan,
                H1=t[t.day < cut].r.mean(), H2=t[t.day >= cut].r.mean(),
                drop3=np.sort(r)[:-3].mean() if len(r) > 4 else np.nan,
                maxDD=float(np.max(pk-eq)), medRisk=t.risk.median())

HTFSETS = {"15": [15], "15+60": [15, 60], "15+60+240": [15, 60, 240], "none": []}
YRS = {"2017-19": 3.0, "2020-22": 3.0, "2023-26": 3.68}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tapes", default="2023-26,2020-22,2017-19")
    ap.add_argument("--tfs", default="1,2,3")
    ap.add_argument("--W", default="6")
    ap.add_argument("--B", default="0.6")
    ap.add_argument("--L", default="0,3")
    ap.add_argument("--T", default="1.0,2.0")
    ap.add_argument("--htf", default="none,15,15+60+240")
    ap.add_argument("--cost", type=float, default=0.75)
    ap.add_argument("--sess", default="570,660")
    ap.add_argument("--out", default="data/debug/dte.csv")
    a = ap.parse_args()
    s0, s1 = (int(x) for x in a.sess.split(","))
    out = []
    for tape in a.tapes.split(","):
        raw = load(tape)
        for tf in [int(x) for x in a.tfs.split(",")]:
            for W, B, L, T, hs in itertools.product(
                    [int(x) for x in a.W.split(",")], [float(x) for x in a.B.split(",")],
                    [int(x) for x in a.L.split(",")], [float(x) for x in a.T.split(",")],
                    a.htf.split(",")):
                t = run(raw, tf, W, B, L, T, HTFSETS[hs], a.cost, (s0, s1))
                s = summarise(t, tape, dict(tf=tf, W=W, B=B, L=L, T=T, htf=hs), YRS[tape])
                if s: out.append(s)
        print(f"  ..{tape} done", flush=True)
    d = pd.DataFrame(out); d.to_csv(a.out, index=False)
    pd.set_option("display.width", 250, "display.max_columns", 40, "display.max_rows", 300)
    print(f"\n{len(d)} cells -> {a.out}")
    print(d.sort_values("R", ascending=False).head(20).to_string(index=False,
          float_format=lambda x: f"{x:+.3f}"))
