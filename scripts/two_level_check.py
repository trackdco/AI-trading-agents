#!/usr/bin/env python3
"""TWO-LEVEL CHECK — codifies his R1 minimum and tests it on any window.

His stated entry minimum (2026-06-23): "My entry always needs to be closure
through two levels. That's usually what I stick by."  This walks every 2m and
3m candle in a window and reports which of his levels each one closed through,
so a narrated claim like "there were no good entries, no closure through two
levels at once" can be checked rather than taken on trust.

Levels are exactly the ones he names across the narrated days: the candle's
own BB(20) MA, the 15m and 1h BB MAs, the VWAP bands, and the developing
daily POC / VAH / VAL.

A "closure through" is open one side, close the other. A "rejection" is a wick
beyond the level closing back — day 2 established that rejection counts toward
the pair, so both are reported, closures first.

THE OWN BB MA IS REQUIRED. Confirmed by him 2026-08-10: "usually I want it to
break the BB MA and another structural level in the same candle, but it's up
to my discretion... I need a break through of 2 structural levels."

So there are TWO shapes, and both are reported:
  same-candle  - the norm: MA and a second level in one candle
  sequential   - MA closes first, the second level completes on a later
                 candle within SEQ_CANDLES. He calls this the exception
                 ("usually I wouldn't"), and did it on 2026-06-26 London:
                 the 04:00 2m closed the MA, the 04:04 2m closed VWAP, and
                 he entered on the retest only then.
Pass --any-pair to also surface pairs that exclude the MA.

    python -m scripts.two_level_check 2026-06-24 LONDON
    python -m scripts.two_level_check 2026-06-24 LONDON --min 1
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from src.htf_ma.levels import (NY, bb_ma_asof, profile_at_minutes,  # noqa: E402
                               vwap_bands)

WINDOWS = {"LONDON": (180, 299), "NY_PRE": (480, 569),
           "NY_AM": (570, 645), "ALL": (0, 1439)}
BANDS = ["vwap", "vwap_p1", "vwap_m1", "vwap_p2", "vwap_m2"]
SEQ_CANDLES = 3          # how long an MA-only closure stays live


def analyse(sess_day: str, window: str, tfs=(2, 3), min_levels: int = 2,
            require_own_ma: bool = True):
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low",
                                              "close", "volume"]]
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30))
                & (bars.index < t0 + pd.Timedelta(hours=23))]
    seg = hist[hist.index >= t0]
    if seg.empty:
        print(f"no bars for session-day {sess_day}")
        return
    idx = seg.index
    vw = vwap_bands(hist)
    prof = profile_at_minutes(hist, list(idx + pd.Timedelta(minutes=1)))
    lv = {b: vw[b].reindex(idx) for b in BANDS}
    for k in ("poc", "vah", "val"):
        lv[k.upper()] = pd.Series(prof[k].to_numpy(), index=idx)
    for htf in (15, 60):
        m, _ = bb_ma_asof(hist, htf)
        lv[f"ma{htf}"] = m.reindex(idx)

    a, b = WINDOWS[window]
    print(f"session-day {sess_day}  window {window} "
          f"({a//60:02d}:{a%60:02d}-{b//60:02d}:{b%60:02d} NY)\n")
    rows, pend = [], []
    for tf in tfs:
        ma_tf, _ = bb_ma_asof(hist, tf)
        f = hist.resample(f"{tf}min", label="left", closed="left").agg(
            {"open": "first", "high": "max", "low": "min",
             "close": "last"}).dropna()
        f = f[(f.index >= t0) & (f.index < t0 + pd.Timedelta(hours=23))]
        f = f[[(t.hour * 60 + t.minute) >= a and (t.hour * 60 + t.minute) <= b
               for t in f.index]]
        for ts, r in f.iterrows():
            # levels are read as-of the candle's CLOSE minute
            cl_min = ts + pd.Timedelta(minutes=tf - 1)
            if cl_min not in idx:
                continue
            own = ma_tf.reindex(idx).get(cl_min, np.nan)
            here = {"own_ma": own}
            here.update({k: v.get(cl_min, np.nan) for k, v in lv.items()})
            closed, rejected = [], []
            for name, val in here.items():
                if not np.isfinite(val):
                    continue
                if r.open > val >= r.close or r.open < val <= r.close:
                    closed.append(name)
                elif (r.high > val > r.open and r.close < val) or \
                     (r.low < val < r.open and r.close > val):
                    rejected.append(name)
            others = [c for c in closed if c != "own_ma"]
            if "own_ma" in closed and others:
                rows.append((ts, tf, r, closed, rejected, "same-candle"))
            elif "own_ma" in closed:
                # MA only. His discretion allows WAITING for the second level
                # on a later candle - verified 2026-06-26 London, where the
                # 04:00 2m closed the MA and the 04:04 2m closed VWAP.
                pend.append((ts, tf, r, 1 if r.close > r.open else -1))
            elif others and pend:
                for p_ts, p_tf, p_r, p_d in list(pend):
                    if p_tf != tf or ts <= p_ts:
                        continue
                    if (ts - p_ts) > pd.Timedelta(minutes=tf * SEQ_CANDLES):
                        pend.remove((p_ts, p_tf, p_r, p_d))
                        continue
                    if p_d == (1 if r.close > r.open else -1):
                        rows.append((ts, tf, r, ["own_ma@" +
                                                 p_ts.strftime("%H:%M")]
                                     + others, rejected,
                                     f"sequential (+{int((ts-p_ts).total_seconds()//60)}m)"))
                        pend.remove((p_ts, p_tf, p_r, p_d))
                        break
            if len(closed) >= min_levels and not require_own_ma \
                    and "own_ma" not in closed:
                rows.append((ts, tf, r, closed, rejected, "no-own-MA"))
    if not rows:
        print(f"  NO candle closed through {min_levels}+ levels"
              + (" including its own BB MA" if require_own_ma else "")
              + ". His claim holds mechanically.")
    for ts, tf, r, closed, rejected, kind in sorted(rows, key=lambda x: x[0]):
        d = "UP  " if r.close > r.open else "DOWN"
        print(f"  {ts:%H:%M} {tf}m {d}  O{r.open:9.2f} C{r.close:9.2f}  "
              f"{kind:18s} [{', '.join(closed)}]"
              + (f"   rejected [{', '.join(rejected)}]" if rejected else ""))
    print(f"\n  {len(rows)} candle(s) with {min_levels}+ closures")

    # how often did a candle close through EXACTLY ONE level?
    return rows


def main() -> None:
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    sess_day = args[0] if args else "2026-06-24"
    window = args[1] if len(args) > 1 else "LONDON"
    mn = 2
    for x in sys.argv[1:]:
        if x.startswith("--min"):
            mn = int(x.split("=")[1]) if "=" in x else 1
    analyse(sess_day, window, min_levels=mn,
            require_own_ma="--any-pair" not in sys.argv)


if __name__ == "__main__":
    main()
