#!/usr/bin/env python3
"""CDR v2 — confluence-REJECTION post-open detector (Angus's A+ method, 11-trade spec).
Additive-only + stand-down, graded on MONTH CONSISTENCY (green every month), not total $.

Per TF {1,2,3}min, per bar 09:40-10:15: confluence zone (>=2 of {VWAP+-1/+-2, BB basis, developing
POC, opening-leg fib 0.382/0.5/0.705} within TOL) -> REJECTION wick into/out of zone -> enter at
close, stop beyond wick+buffer, target next structural level (BE at first magnet), else stand down.
CVD confirmation toggle: absorbed flow (against) vs with-flow. All per-day data precomputed once.

    python -m scripts.cdr_v2 [TOL] [cvd: off|against|with]
"""
import sys
from datetime import time as dtime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.engine.indicators import bollinger, daily_vwap  # noqa: E402
from src.engine.sessions import resample_ohlcv  # noqa: E402

NY = "America/New_York"
DATA = Path("data/reference/nq_1m_feb_jul2026.parquet")
CVD = ["footprint_feb_mar2026", "footprint_apr2026", "footprint_may_jul2026"]
WIN_S, WIN_E = dtime(9, 40), dtime(10, 15)
OPEN_T = dtime(9, 30)
MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]
TOL, BUF, PV, COMM = 6.0, 2.0, 20.0, 2.50


def load_fp():
    fr = [pd.read_parquet(f"data/reference/cvd/{f}.parquet", columns=["ts_minute", "price", "side", "volume"])
          for f in CVD]
    d = pd.concat(fr, ignore_index=True)
    d["ts"] = d.ts_minute.dt.tz_convert(NY)
    d["day"] = d.ts.dt.strftime("%Y-%m-%d")
    d = d[(d.ts.dt.time >= OPEN_T) & (d.ts.dt.time <= WIN_E)]
    d["signed"] = np.where(d["side"] == "B", d["volume"], -d["volume"])   # B(buy)-A(sell), verified
    return d


def poc_delta_for_day(fpd):
    poc, delta, cum = {}, {}, {}
    for ts, g in fpd.groupby("ts"):
        for p, v in zip(g.price.values, g.volume.values):
            cum[p] = cum.get(p, 0) + v
        k = int(ts.floor("min").value)
        poc[k] = max(cum, key=cum.get)
        delta[k] = float(g.signed.sum())
    return poc, delta


def fibs_for_day(opening):
    """opening = 09:30-09:40 1m slice (open, high, low)."""
    if opening is None or len(opening) < 3:
        return {}
    o = opening.iloc[0].open
    hi, lo = opening.high.max(), opening.low.min()
    a, b = (lo, hi) if (hi - o) >= (o - lo) else (hi, lo)
    rng = b - a
    return {f: b - f * rng for f in (0.382, 0.5, 0.705)}


def run_tf(tf, bars1m, tol, cvd_mode, poc_by_day, delta_by_day, fibs_by_day, vwap_map, day1m):
    tfd = resample_ohlcv(bars1m, f"{tf}min").reset_index(drop=True)
    tfd = tfd.join(bollinger(tfd, 20, 2.0)[["basis", "upper", "lower"]])
    tfd["day"] = tfd.ts_event.dt.strftime("%Y-%m-%d")
    tfd["t"] = tfd.ts_event.dt.time
    tfd["k"] = tfd.ts_event.astype("int64")
    trades, stage = [], dict(bars=0, zone=0, reject=0)
    for day, g in tfd.groupby("day"):
        if day not in day1m or day not in poc_by_day:
            continue
        poc, delta, fibs = poc_by_day[day], delta_by_day[day], fibs_by_day.get(day, {})
        dts, dlo, dhi, dcl = day1m[day]
        g = g.reset_index(drop=True)
        lows, highs, closes, ks, ts_ = g.low.values, g.high.values, g.close.values, g.k.values, g.t.values
        bas, up, lo_ = g.basis.values, g.upper.values, g.lower.values
        for i in range(1, len(g)):
            if not (WIN_S <= ts_[i] <= WIN_E) or np.isnan(bas[i]):
                continue
            k = int(ks[i])
            if k not in poc or k not in vwap_map:
                continue
            stage["bars"] += 1
            vw = vwap_map[k]   # [vwap,u1,l1,u2,l2]
            levels = [vw[0], vw[1], vw[2], vw[3], vw[4], bas[i], up[i], lo_[i], poc[k]] + list(fibs.values())
            vals = sorted(levels)
            zone = None
            for x in vals:
                near = [y for y in vals if abs(y - x) <= tol]
                if len(near) >= 2:
                    zone = float(np.mean(near)); break
            if zone is None:
                continue
            stage["zone"] += 1
            long_rej = lows[i] <= zone + tol and closes[i] > zone + tol/2 and vw[0] >= zone
            short_rej = highs[i] >= zone - tol and closes[i] < zone - tol/2 and vw[0] <= zone
            if not (long_rej or short_rej):
                continue
            direction = "long" if long_rej else "short"
            stage["reject"] += 1
            cvd_dir = (delta.get(k, 0.0)) * (1 if direction == "long" else -1)
            if cvd_mode == "against" and cvd_dir >= 0:
                continue
            if cvd_mode == "with" and cvd_dir <= 0:
                continue
            entry = closes[i]
            stop = (lows[i] - BUF) if direction == "long" else (highs[i] + BUF)
            risk = abs(entry - stop)
            if risk < 2:
                continue
            opp = [vw[0], poc[k], vw[1] if direction == "long" else vw[2]]
            cands = [x for x in opp if (x > entry) == (direction == "long") and abs(x - entry) > risk]
            tgt = (min(cands) if direction == "long" else max(cands)) if cands else \
                  (entry + 2*risk if direction == "long" else entry - 2*risk)
            j0 = int(np.searchsorted(dts, k, side="right"))
            slo, shi, scl = dlo[j0:], dhi[j0:], dcl[j0:]
            hs = (slo <= stop) if direction == "long" else (shi >= stop)
            ht = (shi >= tgt) if direction == "long" else (slo <= tgt)
            si = int(np.argmax(hs)) if hs.any() else 10**9
            ti = int(np.argmax(ht)) if ht.any() else 10**9
            if si == ti == 10**9:
                last = scl[-1] if len(scl) else entry
                out = (last - entry) if direction == "long" else (entry - last)
            elif si <= ti:
                out = -risk
            else:
                out = (tgt - entry) if direction == "long" else (entry - tgt)
            trades.append(dict(day=day, month=day[:7], tf=tf, direction=direction,
                               risk=risk, R=out/risk, dollars=out*PV - 2*COMM, cvd_dir=cvd_dir))
    return pd.DataFrame(trades), stage


def main():
    tol = float(sys.argv[1]) if len(sys.argv) > 1 else TOL
    cvd_mode = sys.argv[2] if len(sys.argv) > 2 else "off"
    bars = pd.read_parquet(DATA)
    vwap = daily_vwap(bars, bands=[1, 2, 3], session_open=dtime(18, 0))
    ks = bars.ts_event.astype("int64").to_numpy()
    vw = vwap[["vwap", "upper_1", "lower_1", "upper_2", "lower_2"]].to_numpy()
    vwap_map = {int(ks[i]): vw[i] for i in range(len(ks))}
    fp = load_fp()
    poc_by_day, delta_by_day = {}, {}
    for d, g in fp.groupby("day"):
        poc_by_day[d], delta_by_day[d] = poc_delta_for_day(g)
    b = bars[(bars.ts_event.dt.time >= OPEN_T) & (bars.ts_event.dt.time <= dtime(10, 35))].copy()
    b["day"] = b.ts_event.dt.strftime("%Y-%m-%d")
    b["t"] = b.ts_event.dt.time
    day1m, fibs_by_day = {}, {}
    for d, g in b.groupby("day"):
        day1m[d] = (g.ts_event.astype("int64").to_numpy(), g.low.to_numpy(), g.high.to_numpy(), g.close.to_numpy())
        fibs_by_day[d] = fibs_for_day(g[g.t < WIN_S])
    print(f"CDR v2 — post-open 09:40-10:15, 2026 Feb-Jul, TOL={tol}, cvd={cvd_mode}", flush=True)
    allT = []
    for tf in (1, 2, 3):
        T, st = run_tf(tf, bars, tol, cvd_mode, poc_by_day, delta_by_day, fibs_by_day, vwap_map, day1m)
        allT.append(T)
        print(f"  TF{tf}: bars={st['bars']} zone={st['zone']} reject={st['reject']} -> {len(T)}t", flush=True)
    J = pd.concat(allT) if any(len(t) for t in allT) else pd.DataFrame()
    if not len(J):
        print("no trades"); return
    print(f"\nALL TF: {len(J)}t  ${J.dollars.sum():+,.0f}  win {(J.dollars>0).mean()*100:.0f}%  avg {J.R.mean():+.2f}R")
    print("MONTH CONSISTENCY:")
    by = J.groupby("month").dollars.agg(["count", "sum"])
    wins = J.groupby("month").apply(lambda x: (x.dollars > 0).mean() * 100)
    green = 0
    for m in MONTHS:
        if m in by.index:
            s = by.loc[m, "sum"]; green += s > 0
            print(f"  {m}  {int(by.loc[m,'count']):3d}t  ${s:+7,.0f}  win {wins[m]:2.0f}%  {'GREEN' if s>0 else 'red'}")
    print(f"  >>> {green}/{by.shape[0]} months green")
    J.to_csv("/tmp/claude-0/-home-user-AI-trading-agents/8f4cdd65-f942-532a-87f2-c9c07c27272a/scratchpad/cdr_v2_trades.csv", index=False)


if __name__ == "__main__":
    main()
