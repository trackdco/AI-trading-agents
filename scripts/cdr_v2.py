#!/usr/bin/env python3
"""CDR v2 — confluence-REJECTION post-open detector (Angus's A+ method, 11-trade spec).
Additive-only + stand-down, graded on MONTH CONSISTENCY (green every month), not total $.

Per TF {1,2,3}min, per bar in 09:40-10:15:
  1. Build the confluence zone: >=2 of {VWAP+-1/+-2, BB basis, developing POC, opening-leg fib
     0.382/0.5/0.705} within TOL of each other.
  2. REJECTION trigger: bar wicks INTO the zone and closes back OUT (rejection wick), with VWAP on
     the origin side. long = reject support (wick down, close up); short = reject resistance.
  3. CVD confirmation (toggle): aggressive delta in the rejection bar is ABSORBED (flow against the
     trade = the fade signal). Recorded always; optionally required.
  4. Entry at rejection close. Stop beyond the wick extreme + buffer. Target = next structural level
     (nearest opposite: VWAP-mid / opposite band / POC), leg-scaled fallback 2R. BE at first magnet.
  5. STAND-DOWN: no confluence rejection -> no trade.

    python -m scripts.cdr_v2 [TOL] [cvd_mode: off|against|with]
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
TOL = 6.0
BUF = 2.0            # stop buffer beyond wick (points)
PV, COMM = 20.0, 2.50


def load_fp():
    fr = [pd.read_parquet(f"data/reference/cvd/{f}.parquet", columns=["ts_minute", "price", "side", "volume"])
          for f in CVD]
    d = pd.concat(fr, ignore_index=True)
    d["ts"] = d.ts_minute.dt.tz_convert(NY)
    d["day"] = d.ts.dt.strftime("%Y-%m-%d")
    d = d[(d.ts.dt.time >= OPEN_T) & (d.ts.dt.time <= WIN_E)]
    d["signed"] = np.where(d["side"] == "B", d["volume"], -d["volume"])   # B=buy - A=sell (verified)
    return d


def dev_poc_and_delta(fpd):
    poc, delta, cum = {}, {}, {}
    for ts, g in fpd.groupby("ts"):
        for p, v in zip(g.price.values, g.volume.values):
            cum[p] = cum.get(p, 0) + v
        poc[ts.floor("min")] = max(cum, key=cum.get)
        delta[ts.floor("min")] = float(g.signed.sum())
    return poc, delta


def opening_leg_fibs(bars1m, day):
    """Fib the 9:30 opening leg: 9:30 open -> extreme by 09:40. Returns dict of level->price."""
    d = bars1m[(bars1m.ts_event.dt.strftime("%Y-%m-%d") == day) &
               (bars1m.ts_event.dt.time >= OPEN_T) & (bars1m.ts_event.dt.time < WIN_S)]
    if len(d) < 3:
        return {}
    o = d.iloc[0].open
    hi, lo = d.high.max(), d.low.min()
    up = (hi - o) >= (o - lo)
    a, b = (lo, hi) if up else (hi, lo)      # leg from a->b
    rng = b - a
    return {f: b - f * rng for f in (0.382, 0.5, 0.705)}   # retracement levels


def run_tf(tf, bars1m, vwap1m, fp, tol, cvd_mode):
    tfd = resample_ohlcv(bars1m, f"{tf}min").reset_index(drop=True)
    bb = bollinger(tfd, 20, 2.0)
    tfd = tfd.join(bb[["basis", "upper", "lower"]])
    tfd["day"] = tfd.ts_event.dt.strftime("%Y-%m-%d")
    tfd["t"] = tfd.ts_event.dt.time
    vb = vwap1m.set_index("ts_event")
    trades, stage = [], dict(bars=0, zone=0, reject=0)
    for day, g in tfd.groupby("day"):
        fpd = fp[fp.day == day]
        if fpd.empty:
            continue
        poc, delta = dev_poc_and_delta(fpd)
        fibs = opening_leg_fibs(bars1m, day)
        g = g.reset_index(drop=True)
        for i in range(1, len(g)):
            row = g.iloc[i]
            if not (WIN_S <= row.t <= WIN_E) or pd.isna(row.basis):
                continue
            pmin = pd.Timestamp(row.ts_event).floor("min")
            if pmin not in poc or pmin not in vb.index:
                continue
            stage["bars"] += 1
            vw = vb.loc[pmin]
            # candidate confluence levels
            levels = {"vwap": vw["vwap"], "v+1": vw["upper_1"], "v-1": vw["lower_1"],
                      "v+2": vw["upper_2"], "v-2": vw["lower_2"], "bb": row.basis,
                      "bbU": row.upper, "bbL": row.lower, "poc": poc[pmin]}
            for k, v in fibs.items():
                levels[f"fib{k}"] = v
            # find a zone: a price where >=2 levels cluster
            vals = sorted(levels.values())
            zone = None
            for x in vals:
                near = [y for y in vals if abs(y - x) <= tol]
                if len(near) >= 2:
                    zone = float(np.mean(near)); break
            if zone is None:
                continue
            stage["zone"] += 1
            # rejection: wick into zone, close back out
            long_rej = row.low <= zone + tol and row.close > zone + tol/2 and vw["vwap"] >= zone
            short_rej = row.high >= zone - tol and row.close < zone - tol/2 and vw["vwap"] <= zone
            if not (long_rej or short_rej):
                continue
            direction = "long" if long_rej else "short"
            stage["reject"] += 1
            d_bar = delta.get(pmin, 0.0)
            cvd_dir = d_bar if direction == "long" else -d_bar   # +ve = flow WITH trade
            if cvd_mode == "against" and cvd_dir >= 0:   # require absorbed (flow against)
                continue
            if cvd_mode == "with" and cvd_dir <= 0:
                continue
            entry = row.close
            stop = (row.low - BUF) if direction == "long" else (row.high + BUF)
            risk = abs(entry - stop)
            if risk < 2:
                continue
            # target = nearest opposite structural level; fallback 2R
            opp = [levels["vwap"], levels["poc"], levels["v+1"] if direction == "long" else levels["v-1"]]
            cands = [x for x in opp if (x > entry) == (direction == "long") and abs(x - entry) > risk]
            tgt = (min(cands) if direction == "long" else max(cands)) if cands else \
                  (entry + 2*risk if direction == "long" else entry - 2*risk)
            # outcome scan on 1m to 10:30
            scan = bars1m[(bars1m.ts_event > pd.Timestamp(row.ts_event)) &
                          (bars1m.ts_event.dt.time <= dtime(10, 30)) &
                          (bars1m.ts_event.dt.strftime("%Y-%m-%d") == day)]
            out = None
            for _, b in scan.iterrows():
                if direction == "long":
                    if b.low <= stop: out = -risk; break
                    if b.high >= tgt: out = tgt - entry; break
                else:
                    if b.high >= stop: out = -risk; break
                    if b.low <= tgt: out = entry - tgt; break
            if out is None:
                last = scan.iloc[-1].close if len(scan) else entry
                out = (last - entry) if direction == "long" else (entry - last)
            trades.append(dict(day=day, month=day[:7], tf=tf, direction=direction,
                               risk=risk, R=out/risk, dollars=out*PV - 2*COMM, cvd_dir=cvd_dir))
    return pd.DataFrame(trades), stage


def main():
    tol = float(sys.argv[1]) if len(sys.argv) > 1 else TOL
    cvd_mode = sys.argv[2] if len(sys.argv) > 2 else "off"
    bars = pd.read_parquet(DATA)
    vwap = daily_vwap(bars, bands=[1, 2, 3], session_open=dtime(18, 0))
    fp = load_fp()
    print(f"CDR v2 — post-open 09:40-10:15, 2026 Feb-Jul, TOL={tol}, cvd={cvd_mode}\n", flush=True)
    allT = []
    for tf in (1, 2, 3):
        T, st = run_tf(tf, bars, vwap, fp, tol, cvd_mode)
        allT.append(T)
        print(f"  TF{tf}: funnel bars={st['bars']} zone={st['zone']} reject={st['reject']} -> {len(T)} trades", flush=True)
    J = pd.concat(allT) if any(len(t) for t in allT) else pd.DataFrame()
    if not len(J):
        print("no trades"); return
    print(f"\nALL TF: {len(J)}t  ${J.dollars.sum():+,.0f}  win {(J.dollars>0).mean()*100:.0f}%  avg {J.R.mean():+.2f}R")
    print("\nMONTH CONSISTENCY (the scorecard):")
    by = J.groupby("month").dollars.agg(["count", "sum"]); by["win"] = J.groupby("month").apply(lambda x: (x.dollars>0).mean()*100)
    green = 0
    for m in MONTHS:
        if m in by.index:
            r = by.loc[m]; g = "GREEN" if r["sum"] > 0 else "red"
            green += r["sum"] > 0
            print(f"  {m}  {int(r['count']):3d}t  ${r['sum']:+7,.0f}  win {r['win']:2.0f}%  {g}")
    print(f"\n  >>> {green}/{len([m for m in MONTHS if m in by.index])} months green")
    J.to_csv("/tmp/claude-0/-home-user-AI-trading-agents/8f4cdd65-f942-532a-87f2-c9c07c27272a/scratchpad/cdr_v2_trades.csv", index=False)


if __name__ == "__main__":
    main()
