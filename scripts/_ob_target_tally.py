#!/usr/bin/env python3
"""Brake OB variant: strong level = DAILY VWAP band OR BB band aligning with POC/VAH/VAL (18:00
profile). Rejection candle = the ORDER BLOCK. Limit at OB 50%, fill on retest to 50%, stop at the
far edge of the OB. Tally how often 30/50/80/100/150 pts get hit (MFE before stop). CVD confirm
overlay (Feb-Jul footprint). Window 09:40-10:15, Feb-Jul."""
import sys, glob
from datetime import time as dtime
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.engine.indicators import daily_vwap
from src.engine.sessions import resample_ohlcv

NY = "America/New_York"
DATA = "data/reference/nq_1m_feb_jul2026.parquet"
TOL, TICK, BIN, VA, MINSTOP, MAXSTOP = 10.0, 0.25, 0.25, 0.70, 2.0, 45.0   # 45pt HARD CAP
W0, W1 = dtime(9, 40), dtime(10, 15)
TARGETS = [30, 50, 80, 100, 150]
IS = {"2026-02", "2026-03", "2026-04", "2026-05"}
TFR = {"5min": 4, "3min": 3, "2min": 2, "1min": 1}

bars = pd.read_parquet(DATA)
bars["ts_event"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
bars = bars.sort_values("ts_event").reset_index(drop=True)
bars["sd"] = (bars.ts_event + pd.Timedelta(hours=6)).dt.tz_localize(None).dt.normalize()
dv = daily_vwap(bars, [1, 2, 3])
for col in ["vwap", "upper_1", "lower_1", "upper_2", "lower_2", "upper_3", "lower_3"]:
    bars[col] = dv[col].values
vwl = bars.set_index("ts_event")[["vwap", "upper_1", "lower_1", "upper_2", "lower_2", "upper_3", "lower_3"]]

# CVD per-minute delta (B=buy, A=sell), NY tz
fp = pd.concat([pd.read_parquet(f, columns=["ts_minute", "side", "volume"])
                for f in glob.glob("data/reference/cvd/footprint_*2026.parquet")])
fp["ts"] = pd.to_datetime(fp.ts_minute, utc=True).dt.tz_convert(NY)
delta = fp.assign(sg=np.where(fp.side == "B", fp.volume, -fp.volume)).groupby("ts").sg.sum().sort_index()
print(f"CVD coverage: {delta.index.min()} -> {delta.index.max()}")


def cvd_confirm(t, direction, mins=3):
    w = delta.loc[t - pd.Timedelta(minutes=mins): t - pd.Timedelta(minutes=1)]
    if not len(w):
        return None
    s = float(w.sum())
    return (s > 0) if direction == "long" else (s < 0)


# developing 18:00 profile snapshots at window candle-close ts
prof_at = {}


def snap(hist):
    imin, imax = min(hist), max(hist)
    arr = np.array([hist.get(i, 0.0) for i in range(imin, imax + 1)])
    centers = (np.arange(imin, imax + 1) + 0.5) * BIN
    total = arr.sum(); n = len(arr); poc = int(arr.argmax()); lo = hi = poc; cov = arr[poc]; tgt = VA * total
    while cov < tgt - 1e-9 and (lo > 0 or hi < n - 1):
        b = arr[lo - 1] if lo > 0 else -np.inf
        a = arr[hi + 1] if hi < n - 1 else -np.inf
        if a >= b: hi += 1; cov += arr[hi]
        else: lo -= 1; cov += arr[lo]
    return dict(POC=float(centers[poc]), VAH=float(centers[hi]), VAL=float(centers[lo]))


for _, g in bars.groupby("sd"):
    hist = {}
    for row in g.itertuples():
        lo_i = int(np.floor(row.low / BIN + 1e-9)); hi_i = int(np.floor(row.high / BIN + 1e-9))
        share = row.volume / (hi_i - lo_i + 1)
        for bi in range(lo_i, hi_i + 1):
            hist[bi] = hist.get(bi, 0.0) + share
        if dtime(9, 39) <= row.ts_event.time() <= dtime(10, 14):
            prof_at[row.ts_event + pd.Timedelta(minutes=1)] = snap(hist)

# detect signals: rejection (OB) at a VWAP-band OR BB-band aligning with a profile level
sigs = []
for tf, rank in TFR.items():
    r = resample_ohlcv(bars[["ts_event", "open", "high", "low", "close", "volume"]], tf)
    basis = r.close.rolling(20).mean(); sd = r.close.rolling(20).std(ddof=0)
    r = r.assign(bb_basis=basis, bb_up=basis + 2 * sd, bb_lo=basis - 2 * sd)
    r = r[(r.ts_event.dt.time >= W0) & (r.ts_event.dt.time <= W1)]
    for row in r.itertuples():
        ts = row.ts_event
        vw = vwl.reindex([ts - pd.Timedelta(minutes=1)]).iloc[0]
        prof = prof_at.get(ts)
        if prof is None or pd.isna(vw["vwap"]):
            continue
        levels = {"VWAPmid": vw["vwap"], "VWAP+1": vw["upper_1"], "VWAP-1": vw["lower_1"],
                  "VWAP+2": vw["upper_2"], "VWAP-2": vw["lower_2"], "VWAP+3": vw["upper_3"], "VWAP-3": vw["lower_3"],
                  "BBbasis": row.bb_basis, "BBupper": row.bb_up, "BBlower": row.bb_lo}
        levels = {k: float(v) for k, v in levels.items() if pd.notna(v)}
        plv = prof
        o, h, l, c = row.open, row.high, row.low, row.close
        for ln, L in levels.items():
            near = [pn for pn, pv in plv.items() if abs(L - pv) <= TOL]
            if not near:
                continue
            d = "long" if (l < L and c > L) else "short" if (h > L and c < L) else None
            if d is None:
                continue
            ob_hi, ob_lo = h, l; ob_mid = (h + l) / 2
            sigs.append(dict(ts=ts, rank=rank, dir=d, ob_hi=ob_hi, ob_lo=ob_lo, ob_mid=ob_mid,
                             level="%s^%s" % (ln, "/".join(near)), lvltype=("BB" if ln.startswith("BB") else "VWAP")))

S = pd.DataFrame(sigs).sort_values(["ts", "rank"], ascending=[True, False]).drop_duplicates("ts").sort_values("ts")
print(f"raw OB signals: {len(sigs)}  after MTF dedupe: {len(S)}")

# backtest: limit at ob_mid, fill on retest, stop at far OB edge, tally MFE targets
idx = bars.set_index("ts_event")
rows = []; open_until = pd.Timestamp.min.tz_localize(NY); nofill = 0; capped = 0
for s in S.to_dict("records"):
    ts = s["ts"]; day = ts.normalize()
    if ts <= open_until:
        continue
    d = s["dir"]; mid = s["ob_mid"]
    stop = (s["ob_hi"] + TICK) if d == "short" else (s["ob_lo"] - TICK)
    risk = abs(mid - stop)
    if risk > MAXSTOP:                                # enforce the 45pt HARD CAP
        capped += 1; continue
    if risk < MINSTOP:
        continue
    flat = pd.Timestamp(f"{day.date()} 15:55", tz=NY)
    dayb = idx.loc[(idx.index > ts) & (idx.index.normalize() == day) & (idx.index <= flat)]
    filled = False; maxfav = 0.0; stopped = False; ent = mid
    for t, b in dayb.iterrows():
        if not filled:                                   # retest to OB 50%
            if (d == "short" and b.high >= mid) or (d == "long" and b.low <= mid):
                filled = True
            else:
                continue
        sh = (b.high >= stop) if d == "short" else (b.low <= stop)
        if sh:
            stopped = True; break
        fav = (ent - b.low) if d == "short" else (b.high - ent)
        maxfav = max(maxfav, fav)
    if not filled:
        nofill += 1; continue
    open_until = ts + pd.Timedelta(minutes=s["rank"])
    rows.append(dict(mo=str(day)[:7], lvltype=s["lvltype"], level=s["level"], dir=d, risk=round(risk, 2),
                     maxfav=round(maxfav, 1), stopped=stopped, cvd=cvd_confirm(ts, d),
                     **{f"hit{X}": maxfav >= X for X in TARGETS}))
T = pd.DataFrame(rows)
print(f"filled trades: {len(T)}  (no-fill retests: {nofill};  rejected by 45pt cap: {capped})\n")


def tally(sub, label):
    if not len(sub):
        print(f"  {label:22s} 0t"); return
    line = f"  {label:22s} {len(sub):3d}t | median MFE {sub.maxfav.median():4.0f}pt |"
    for X in TARGETS:
        line += f"  {X}:{sub[f'hit{X}'].mean()*100:3.0f}%"
    print(line)


print("TARGET-HIT TALLY (% of filled trades whose MFE reached each level before stop):")
print(f"  {'':22s} {'':3s}   {'':13s}    " + "  ".join(f"{X}pt" for X in TARGETS))
tally(T, "ALL")
tally(T[T.lvltype == "VWAP"], "VWAP-aligned")
tally(T[T.lvltype == "BB"], "BB-aligned")
tally(T[T.cvd == True], "CVD-confirmed")
tally(T[T.cvd == False], "CVD-against")
tally(T[T.mo.isin(IS)], "IN-SAMPLE Feb-May")
tally(T[~T.mo.isin(IS)], "OOS Jun-Jul")

print("\nEXPECTED POINTS if you FIXED each target (win=+X, else stop=-risk or EOD):")
for X in TARGETS:
    pnl = np.where(T[f"hit{X}"], X, np.where(T.stopped, -T.risk, 0.0))
    print(f"  target {X:3d}pt: hit {T[f'hit{X}'].mean()*100:3.0f}%  avg {pnl.mean():+6.1f} pts/trade  total {pnl.sum():+7.0f} pts")
print("\n  same, CVD-confirmed only:")
Tc = T[T.cvd == True]
for X in TARGETS:
    pnl = np.where(Tc[f"hit{X}"], X, np.where(Tc.stopped, -Tc.risk, 0.0))
    print(f"  target {X:3d}pt: hit {Tc[f'hit{X}'].mean()*100:3.0f}%  avg {pnl.mean():+6.1f} pts/trade ({len(Tc)}t)")
T.to_csv(f"{S}/ob_target_tally.csv", index=False)
print("\nsaved")
