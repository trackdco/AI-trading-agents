#!/usr/bin/env python3
"""NQ 20-SMA pin-bar reclaim. Rules frozen in docs/PREREG-sma20-pinbar-reclaim.md.
Entry at the pin's close; exits scanned from the bar AFTER entry; both-touched = STOP."""
import argparse, itertools, numpy as np, pandas as pd

TICK = 0.25
TAPES = {
    "2017-19": ["data/reference/nq_2017_2019_1m.parquet"],
    "2020-22": ["data/reference/nq_2020_2022_1m.parquet"],
    "2023-26": ["data/reference/nq_1m_master.parquet",
                "data/reference/nq_1m_jul_sep2026.parquet"],
}
SESSIONS = {"NY": (9*60+30, 10*60+30), "LONDON": (3*60, 4*60+30), "ALLDAY": (0, 24*60)}

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
    b = pd.concat(out); return b[~b.index.duplicated()].sort_index()

def resample(b, tf):
    if tf == 1: return b
    r = b.resample(f"{tf}min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
    return r.dropna()

def pivots(h, l, k=2):
    """Fractal swing highs/lows: extreme of a 2k+1 window, causal use only via index."""
    n = len(h); ph = np.zeros(n, bool); pl = np.zeros(n, bool)
    for i in range(k, n - k):
        w = slice(i - k, i + k + 1)
        if h[i] == h[w].max() and (h[w] == h[i]).sum() == 1: ph[i] = True
        if l[i] == l[w].min() and (l[w] == l[i]).sum() == 1: pl[i] = True
    return ph, pl

def trend_flags(c, sma, h, l, ph, pl, mode):
    """Returns (long_ok, short_ok) boolean arrays, all causal at bar i."""
    n = len(c)
    if mode == "NONE":
        return np.ones(n, bool), np.ones(n, bool)
    if mode == "SLOPE":
        s10 = np.roll(sma, 10); s10[:10] = np.nan
        return sma > s10, sma < s10
    if mode == "SIDE":
        above = pd.Series(c > sma).rolling(15).sum().values
        return above >= 12, (15 - np.nan_to_num(above, nan=-99)) >= 12
    if mode == "HHHL":
        # last two confirmed swing highs rising AND last two swing lows rising.
        # A pivot at j is only confirmed at j+k, so shift usage by k=2 bars.
        lo_ok = np.zeros(n, bool); sh_ok = np.zeros(n, bool)
        hs = []; ls = []
        for i in range(n):
            j = i - 2
            if j >= 0 and ph[j]: hs.append(h[j])
            if j >= 0 and pl[j]: ls.append(l[j])
            if len(hs) >= 2 and len(ls) >= 2:
                lo_ok[i] = hs[-1] > hs[-2] and ls[-1] > ls[-2]
                sh_ok[i] = hs[-1] < hs[-2] and ls[-1] < ls[-2]
        return lo_ok, sh_ok
    raise ValueError(mode)

def next_dol(h, l, ph, pl, i, d, E, risk, n):
    """Next prominent swing level in the trade's direction, floored at 1R."""
    lim = E + risk if d == 1 else E - risk
    if d == 1:
        for j in range(i - 1, max(0, i - 400), -1):
            if ph[j] and h[j] > E: return max(h[j], lim)
    else:
        for j in range(i - 1, max(0, i - 400), -1):
            if pl[j] and l[j] < E: return min(l[j], lim)
    return lim

def scan(b, tf, sess, T, W, U, B, targets, cost, maxhold, rng=None):
    o, h, l, c = (b[x].values.astype(float) for x in ("open", "high", "low", "close"))
    n = len(c)
    sma = pd.Series(c).rolling(20).mean().values
    ph, pl = pivots(h, l)
    lo_t, sh_t = trend_flags(c, sma, h, l, ph, pl, T)
    tmin = (b.index.hour * 60 + b.index.minute).values
    t0, t1 = SESSIONS[sess]
    inwin = (tmin >= t0) & (tmin < t1)
    body = np.abs(c - o); rng_ = h - l
    lw = np.minimum(o, c) - l; uw = h - np.maximum(o, c)
    with np.errstate(invalid="ignore"):
        long_sig  = inwin & lo_t & (l < sma) & (c > sma) & (c > o) & (lw >= W*body) & (uw <= U*rng_)
        short_sig = inwin & sh_t & (h > sma) & (c < sma) & (c < o) & (uw >= W*body) & (lw <= U*rng_)
    long_sig = np.nan_to_num(long_sig, nan=False).astype(bool)
    short_sig = np.nan_to_num(short_sig, nan=False).astype(bool)
    hold = max(1, maxhold // tf)
    books = {t: [] for t in targets}
    busy_until = -1
    for i in np.where(long_sig | short_sig)[0]:
        if i <= 20 or i >= n - 2 or i < busy_until: continue
        d = 1 if long_sig[i] else -1
        E = c[i]
        stop = (l[i] - B*TICK) if d == 1 else (h[i] + B*TICK)
        risk = (E - stop) if d == 1 else (stop - E)
        if risk <= 0: continue
        busy_until = i + 1
        for tg in targets:
            T_px = next_dol(h, l, ph, pl, i, d, E, risk, n) if tg == "DOL" \
                   else (E + d*float(tg[1:])*risk)
            res, pnl, k = "FLAT", None, i
            for k in range(i+1, min(n, i+1+hold)):
                hit_s = (l[k] <= stop) if d == 1 else (h[k] >= stop)
                hit_t = (h[k] >= T_px) if d == 1 else (l[k] <= T_px)
                if hit_s: res, pnl = "STOP", -risk; break
                if hit_t: res, pnl = "TARGET", d*(T_px - E); break
            if pnl is None: pnl = d*(c[k] - E)
            books[tg].append(dict(day=str(b.index[i].date()), i=i, dir=d, entry=E,
                                  risk=risk, rr=abs(T_px-E)/risk, res=res,
                                  r=(pnl-cost)/risk, held=(k-i)*tf))
    return books

def summarise(rows, tape, tag):
    t = pd.DataFrame(rows)
    if len(t) < 10: return None
    r = t.r.values; cut = t.day.sort_values().iloc[len(t)//2]
    h1 = t[t.day < cut].r; h2 = t[t.day >= cut].r
    be = 1/(1+t.rr.median())
    return dict(tape=tape, **tag, n=len(t), R=r.mean(), netR=r.sum(),
                win=(t.res=="TARGET").mean(), be=be,
                excess=(t.res=="TARGET").mean()-be, medRR=t.rr.median(),
                medRisk=t.risk.median(),
                t=r.mean()/(r.std(ddof=1)/np.sqrt(len(r))) if len(r)>2 else np.nan,
                H1=h1.mean() if len(h1) else np.nan, H2=h2.mean() if len(h2) else np.nan,
                drop3=np.sort(r)[:-3].mean() if len(r)>4 else np.nan,
                flat=(t.res=="FLAT").mean())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cost", type=float, default=1.25)
    ap.add_argument("--maxhold", type=int, default=120)
    ap.add_argument("--tfs", default="1,2,3")
    ap.add_argument("--sessions", default="NY,LONDON,ALLDAY")
    ap.add_argument("--trends", default="SLOPE,SIDE,HHHL,NONE")
    ap.add_argument("--wicks", default="1.0,2.0")
    ap.add_argument("--upper", default="0.5")
    ap.add_argument("--buf", default="2")
    ap.add_argument("--targets", default="R1,R2,DOL")
    ap.add_argument("--tapes", default="2023-26,2020-22,2017-19")
    ap.add_argument("--out", default="data/debug/sma20_pinbar.csv")
    a = ap.parse_args()
    TFs   = [int(x) for x in a.tfs.split(",")]
    SESS  = a.sessions.split(","); TR = a.trends.split(",")
    Ws    = [float(x) for x in a.wicks.split(",")]
    Us    = [float(x) for x in a.upper.split(",")]
    Bs    = [int(x) for x in a.buf.split(",")]
    TGs   = a.targets.split(",")
    out = []
    for tape in a.tapes.split(","):
        raw = load(tape)
        for tf in TFs:
            b = resample(raw, tf)
            for sess, T, W, U, B in itertools.product(SESS, TR, Ws, Us, Bs):
                books = scan(b, tf, sess, T, W, U, B, TGs, a.cost, a.maxhold)
                for tg, rows in books.items():
                    s = summarise(rows, tape, dict(tf=tf, sess=sess, trend=T, W=W, U=U,
                                                   buf=B, tgt=tg))
                    if s: out.append(s)
        print(f"  ..{tape} done", flush=True)
    df = pd.DataFrame(out)
    df.to_csv(a.out, index=False)
    print(f"\n{len(df)} cells -> {a.out}")
    return df

if __name__ == "__main__":
    d = main()
    pd.set_option("display.width", 250, "display.max_columns", 60, "display.max_rows", 300)
    print(d.sort_values("R", ascending=False).head(25).to_string(index=False,
          float_format=lambda x: f"{x:+.3f}"))
