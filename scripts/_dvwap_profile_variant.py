#!/usr/bin/env python3
"""Brake variant (FAST): DAILY VWAP ONLY (no NY VWAP, no BB) + 18:00-anchored developing volume
profile (POC/VAH/VAL, built incrementally, matching engine math). Enter on a REJECTION candle where
a daily VWAP band coincides (<= cluster tol) with POC/VAH/VAL. Window 09:40-10:15, Feb-Jul.
Reviews band respect/rejection + daily-bias split. No BB, no NY VWAP, nothing tuned."""
import sys
from datetime import time as dtime
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.engine.indicators import daily_vwap
from src.engine.sessions import resample_ohlcv
from src.engine.data import _session_date as sess_date_maint   # 17:00; we use 18:00 explicit below

NY = "America/New_York"
DATA = "data/reference/nq_1m_feb_jul2026.parquet"
TOL, FRONT, RRFLOOR, MINSTOP = 10.0, 2.5, 1.5, 6.0
SLIP, TICK, PV, COMM, BIN, VA = 0.5, 0.25, 20.0, 1.70, 0.25, 0.70
W0, W1 = dtime(9, 40), dtime(10, 15)
IS = {"2026-02", "2026-03", "2026-04", "2026-05"}
TFR = {"5min": 4, "3min": 3, "2min": 2, "1min": 1}

bars = pd.read_parquet(DATA)
bars["ts_event"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
bars = bars.sort_values("ts_event").reset_index(drop=True)
# 18:00 CME session date
bars["sd"] = (bars.ts_event + pd.Timedelta(hours=6)).dt.tz_localize(None).dt.normalize()

# --- daily VWAP bands once (vectorized, developing) ---
dv = daily_vwap(bars, [1, 2, 3])
for col in ["vwap", "upper_1", "lower_1", "upper_2", "lower_2", "upper_3", "lower_3"]:
    bars[col] = dv[col].values
vwap_lookup = bars.set_index("ts_event")[["vwap", "upper_1", "lower_1", "upper_2", "lower_2", "upper_3", "lower_3"]]

# --- developing 18:00 profile incrementally; snapshot for each window candle-close ts ---
prof_at = {}


def snapshot(hist):
    if not hist:
        return None
    imin, imax = min(hist), max(hist)
    arr = np.array([hist.get(i, 0.0) for i in range(imin, imax + 1)])
    centers = (np.arange(imin, imax + 1) + 0.5) * BIN
    total = arr.sum(); n = len(arr)
    poc = int(arr.argmax()); lo = hi = poc; cov = arr[poc]; tgt = VA * total
    while cov < tgt - 1e-9 and (lo > 0 or hi < n - 1):
        b = arr[lo - 1] if lo > 0 else -np.inf
        a = arr[hi + 1] if hi < n - 1 else -np.inf
        if a >= b: hi += 1; cov += arr[hi]
        else: lo -= 1; cov += arr[lo]
    return dict(poc=float(centers[poc]), vah=float(centers[hi]), val=float(centers[lo]))


for sd, g in bars.groupby("sd"):
    hist = {}
    for row in g.itertuples():
        lo_i = int(np.floor(row.low / BIN + 1e-9)); hi_i = int(np.floor(row.high / BIN + 1e-9))
        share = row.volume / (hi_i - lo_i + 1)
        for bi in range(lo_i, hi_i + 1):
            hist[bi] = hist.get(bi, 0.0) + share
        t = row.ts_event.time()
        if dtime(9, 39) <= t <= dtime(10, 14):        # valid for candle closing next minute
            prof_at[row.ts_event + pd.Timedelta(minutes=1)] = snapshot(hist)

# --- detect signals over entry TFs ---
sigs = []; band_touch = {}
for tf, rank in TFR.items():
    r = resample_ohlcv(bars[["ts_event", "open", "high", "low", "close", "volume"]], tf)
    r = r[(r.ts_event.dt.time >= W0) & (r.ts_event.dt.time <= W1)]
    for row in r.itertuples():
        ts = row.ts_event
        vw = vwap_lookup.reindex([ts - pd.Timedelta(minutes=1)]).iloc[0]
        prof = prof_at.get(ts)
        if prof is None or pd.isna(vw["vwap"]):
            continue
        bands = {"mid": vw["vwap"], "+1": vw["upper_1"], "-1": vw["lower_1"],
                 "+2": vw["upper_2"], "-2": vw["lower_2"], "+3": vw["upper_3"], "-3": vw["lower_3"]}
        bands = {k: float(v) for k, v in bands.items() if pd.notna(v)}
        plv = {"POC": prof["poc"], "VAH": prof["vah"], "VAL": prof["val"]}
        o, h, l, c = row.open, row.high, row.low, row.close
        bias = "long" if c > bands["mid"] else "short"
        if tf == "1min":
            for bn, bv in bands.items():
                if l <= bv <= h:
                    rej = (c > bv and o > bv) or (c < bv and o < bv)
                    t0, r0 = band_touch.get(bn, (0, 0)); band_touch[bn] = (t0 + 1, r0 + int(rej))
        for bn, L in bands.items():
            near = [pn for pn, pv in plv.items() if abs(L - pv) <= TOL]
            if not near:
                continue
            if l < L and c > L:
                sigs.append(dict(ts=ts, rank=rank, dir="long", L=L, wick=l, band=bn,
                                 prof="/".join(near), bias=bias, bands=bands, plv=plv))
            elif h > L and c < L:
                sigs.append(dict(ts=ts, rank=rank, dir="short", L=L, wick=h, band=bn,
                                 prof="/".join(near), bias=bias, bands=bands, plv=plv))

print(f"\n[FUNNEL] raw rejection signals at a VWAP-band n profile level: {len(sigs)}")
if sigs:
    _s = pd.DataFrame(sigs)
    print("  by band:", _s.band.value_counts().to_dict())
    print("  by profile level:", _s.prof.value_counts().to_dict())
S = pd.DataFrame(sigs)
if len(S):
    S = S.sort_values(["ts", "rank"], ascending=[True, False]).drop_duplicates("ts").sort_values("ts")
print(f"  after MTF dedupe: {len(S)}")
_drop = {"minstop": 0, "notarget": 0, "nofill": 0, "cap_or_open": 0}

# --- backtest ---
idx = bars.set_index("ts_event")
trades = []; daycount = {}; open_until = pd.Timestamp.min.tz_localize(NY)
for s in (S.to_dict("records") if len(S) else []):
    ts = s["ts"]; day = ts.normalize()
    if ts <= open_until or daycount.get(day, 0) >= 2:
        _drop["cap_or_open"] += 1; continue
    d = s["dir"]
    stop = (s["wick"] - TICK) if d == "long" else (s["wick"] + TICK)
    flat = pd.Timestamp(f"{day.date()} 15:55", tz=NY)
    dayb = idx.loc[(idx.index > ts) & (idx.index.normalize() == day) & (idx.index <= flat)]
    if dayb.empty:
        _drop["nofill"] += 1; continue
    ent = float(dayb.open.iloc[0])                     # market entry on the next bar (enter on rejection)
    risk = abs(ent - stop)
    if risk < MINSTOP or (d == "long" and ent <= stop) or (d == "short" and ent >= stop):
        _drop["minstop"] += 1; continue
    opp = [v for v in list(s["bands"].values()) + list(s["plv"].values()) if (v > ent if d == "long" else v < ent)]
    tgt = None
    for lv in sorted(opp, reverse=(d == "short")):
        wk = lv - FRONT if d == "long" else lv + FRONT
        if abs(wk - ent) / risk >= RRFLOOR:
            tgt = wk; break
    if tgt is None:
        _drop["notarget"] += 1; continue
    ex = None; rs = None
    for t, b in dayb.iterrows():
        if d == "long":
            if b.low <= stop: ex = stop - SLIP; rs = "stop"; break
            if b.high >= tgt: ex = tgt; rs = "target"; break
        else:
            if b.high >= stop: ex = stop + SLIP; rs = "stop"; break
            if b.low <= tgt: ex = tgt; rs = "target"; break
    if ex is None:
        ex = float(dayb.close.iloc[-1]); rs = "eod"
    pts = ((ex - ent) if d == "long" else (ent - ex)) - COMM / PV
    trades.append(dict(date=str(day.date()), mo=str(day)[:7], tf=s["rank"], dir=d, band=s["band"],
                       prof=s["prof"], with_bias=(d == s["bias"]), r=round(pts / risk, 3),
                       dollars=round(pts * PV, 1), reason=rs))
    daycount[day] = daycount.get(day, 0) + 1
    open_until = ts + pd.Timedelta(minutes=s["rank"])

print(f"  backtest drops: {_drop}"); T = pd.DataFrame(trades)
print("=" * 70)
print("DAILY-VWAP-ONLY + 18:00 PROFILE — rejection at VWAP-band n POC/VAH/VAL, 09:40-10:15, Feb-Jul")
print("=" * 70)
print("\n[BAND RESPECT] 1m touches in window: reject=closed back on same side (level held)")
for bn in ["mid", "+1", "-1", "+2", "-2", "+3", "-3"]:
    if bn in band_touch:
        t0, r0 = band_touch[bn]
        print(f"  daily VWAP {bn:4s}: {t0:4d} touches, {r0/t0*100:4.0f}% held")
if not len(T):
    print("\nNO TRADES"); sys.exit()
print(f"\n[TRADES] {len(T)}  win {(T.r>0).mean()*100:.0f}%  ${T.dollars.sum():+,.0f}  R {T.r.sum():+.1f}  exp {T.r.mean():+.3f}")
for name, sub in [("IN-SAMPLE Feb-May", T[T.mo.isin(IS)]), ("OOS Jun-Jul", T[~T.mo.isin(IS)]),
                  ("with daily bias", T[T.with_bias]), ("against bias", T[~T.with_bias])]:
    if len(sub):
        print(f"  {name:18s} {len(sub):3d}t  win {(sub.r>0).mean()*100:3.0f}%  ${sub.dollars.sum():+7,.0f}  R {sub.r.sum():+6.1f}  exp {sub.r.mean():+.3f}")
print("\n[by VWAP band n profile level]")
print(T.groupby(["band", "prof"]).agg(n=("r", "size"), win=("r", lambda s: round((s > 0).mean()*100)), R=("r", "sum")).round(1).to_string())
T.to_csv(f"{S}/dvwap_variant.csv", index=False)
print("\nsaved")
