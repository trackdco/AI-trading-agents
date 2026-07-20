#!/usr/bin/env python3
"""CDR — Cash-Open Confluence Displacement-Retest (Angus's A+ post-open setup).
Window 09:40-10:15. Per TF in {1,2,3}min, per candle:
  1. developing POC (from footprint, anchored at 09:30 cash open) aligns with a Bollinger(20,2)
     line within TOL  -> confluence level.
  2. VWAP (Globex, 18:00 anchor) is on the origin side (respected): long => VWAP <= level.
  3. displacement: the candle CLOSES THROUGH the confluence level, away from VWAP.
  4. entry on the RETEST of the level (limit), within RETEST_BARS TF-candles.
  5. stop beyond the displacement candle extreme; exit = TGT_R * risk target or stop, else flat at 10:30.

Reports per-TF: setups/day, fill%, win%, avg R, $/trade, total $ (1 NQ, $20/pt, 2-side commission).

    python -m scripts.cdr_detect
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
CASH_OPEN = dtime(9, 30)
TOL = 3.0            # confluence tolerance, points (POC vs BB line)
RETEST_BARS = 8      # how many TF bars the retest may take
TGT_R = 2.0          # target = TGT_R x risk
PV, COMM = 20.0, 2.50  # $/pt per contract, 1-side commission


def load_footprint():
    fr = [pd.read_parquet(f"data/reference/cvd/{f}.parquet", columns=["ts_minute", "price", "volume"])
          for f in CVD]
    d = pd.concat(fr, ignore_index=True)
    d["ts"] = d.ts_minute.dt.tz_convert(NY)
    d["day"] = d.ts.dt.strftime("%Y-%m-%d")
    return d[(d.ts.dt.time >= CASH_OPEN) & (d.ts.dt.time <= WIN_E)]


def dev_poc_series(fp_day):
    """Developing POC per minute: argmax cumulative volume-by-price from 09:30 to each minute."""
    out = {}
    cum = {}
    for ts, g in fp_day.groupby("ts"):
        for p, v in zip(g.price.values, g.volume.values):
            cum[p] = cum.get(p, 0) + v
        poc = max(cum, key=cum.get)
        out[ts.floor("min")] = poc
    return out


def run_tf(tf, bars1m, vwap1m, fp, tol=TOL):
    rule = f"{tf}min"
    tfd = resample_ohlcv(bars1m, rule).reset_index(drop=True)
    bb = bollinger(tfd, 20, 2.0)
    tfd = tfd.join(bb[["basis", "upper", "lower"]])
    tfd["day"] = tfd.ts_event.dt.strftime("%Y-%m-%d")
    tfd["t"] = tfd.ts_event.dt.time
    # 1m frames keyed by minute for VWAP + intrabar exit scan
    v1 = vwap1m.set_index("ts_event")["vwap"]
    trades = []
    stage = dict(bars=0, confluence=0, displacement=0)
    for day, g in tfd.groupby("day"):
        fpd = fp[fp.day == day]
        if fpd.empty:
            continue
        poc = dev_poc_series(fpd)
        g = g.reset_index(drop=True)
        for i in range(1, len(g)):
            row, prev = g.iloc[i], g.iloc[i - 1]
            if not (WIN_S <= row.t <= WIN_E):
                continue
            if pd.isna(row.basis):
                continue
            pmin = pd.Timestamp(row.ts_event).floor("min")
            if pmin not in poc:
                continue
            P = poc[pmin]
            vw = v1.get(pmin, np.nan)
            if pd.isna(vw):
                continue
            stage["bars"] += 1
            # confluence: POC aligns with a BB line
            lines = {"basis": row.basis, "upper": row.upper, "lower": row.lower}
            line_name = min(lines, key=lambda k: abs(lines[k] - P))
            if abs(lines[line_name] - P) > tol:
                continue
            stage["confluence"] += 1
            level = (lines[line_name] + P) / 2.0
            # displacement: close through the level, prev close on the other side, away from VWAP
            long_disp = prev.close < level <= row.close and vw <= level
            short_disp = prev.close > level >= row.close and vw >= level
            if not (long_disp or short_disp):
                continue
            stage["displacement"] += 1
            direction = "long" if long_disp else "short"
            stop = row.low if direction == "long" else row.high
            risk = abs(level - stop)
            if risk < 1.0:
                continue
            # retest: within RETEST_BARS TF-bars, price returns to `level`
            filled = False
            for j in range(i + 1, min(i + 1 + RETEST_BARS, len(g))):
                nb = g.iloc[j]
                if nb.t > WIN_E:
                    break
                if (direction == "long" and nb.low <= level) or (direction == "short" and nb.high >= level):
                    entry_ts = pd.Timestamp(nb.ts_event)
                    filled = True
                    break
            if not filled:
                trades.append(dict(day=day, tf=tf, direction=direction, filled=False,
                                   line=line_name, risk=risk, R=np.nan, dollars=0.0))
                continue
            # outcome: from entry bar forward on 1m, stop vs target(TGT_R), else flat 10:30
            tgt = level + TGT_R * risk if direction == "long" else level - TGT_R * risk
            scan = bars1m[(bars1m.ts_event >= entry_ts) &
                          (bars1m.ts_event.dt.time <= dtime(10, 30)) &
                          (bars1m.ts_event.dt.strftime("%Y-%m-%d") == day)]
            outcome = None
            for _, b in scan.iterrows():
                if direction == "long":
                    if b.low <= stop:
                        outcome = -risk; break
                    if b.high >= tgt:
                        outcome = TGT_R * risk; break
                else:
                    if b.high >= stop:
                        outcome = -risk; break
                    if b.low <= tgt:
                        outcome = TGT_R * risk; break
            if outcome is None:  # flat at 10:30 close
                last = scan.iloc[-1].close if len(scan) else level
                outcome = (last - level) if direction == "long" else (level - last)
            dollars = outcome * PV - 2 * COMM
            trades.append(dict(day=day, tf=tf, direction=direction, filled=True,
                               line=line_name, risk=risk, R=outcome / risk, dollars=dollars))
    return pd.DataFrame(trades), stage


def report(T, stage, tf, ndays):
    print(f"\n== TF {tf}min ==  funnel: bars={stage['bars']}  confluence={stage['confluence']}  "
          f"displacement={stage['displacement']}  setups={len(T)}")
    if not len(T) or "filled" not in T.columns:
        print("   (no setups)"); return
    f = T[T.filled]
    setups = len(T)
    print(f"   setups {setups} ({setups/ndays:.2f}/day)  filled {len(f)} ({len(f)/max(setups,1)*100:.0f}%)")
    if len(f):
        print(f"   filled: win {(f.dollars>0).mean()*100:.0f}%  avg {f.R.mean():+.2f}R  "
              f"${f.dollars.sum():+,.0f}  (${f.dollars.mean():+.0f}/t)  "
              f"| long {len(f[f.direction=='long'])} short {len(f[f.direction=='short'])}")
        print(f"   confluence line hit: {dict(f.line.value_counts())}")


def main():
    bars = pd.read_parquet(DATA)
    vwap = daily_vwap(bars, bands=[2], session_open=dtime(18, 0))  # already carries tz-aware ts_event
    fp = load_footprint()
    ndays = fp.day.nunique()
    import sys as _s
    tol = float(_s.argv[1]) if len(_s.argv) > 1 else TOL
    print(f"CDR detector — 2026 Feb-Jul, {ndays} days, window {WIN_S}-{WIN_E}, TOL={tol}pt, target={TGT_R}R")
    allT = []
    for tf in (1, 2, 3):
        T, stage = run_tf(tf, bars, vwap, fp, tol=tol)
        report(T, stage, tf, ndays)
        if len(T):
            allT.append(T)
    if allT:
        pd.concat(allT).to_csv(f"/tmp/claude-0/-home-user-AI-trading-agents/8f4cdd65-f942-532a-87f2-c9c07c27272a/scratchpad/cdr_trades.csv", index=False)


if __name__ == "__main__":
    main()
