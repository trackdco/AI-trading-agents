#!/usr/bin/env python3
"""Build HTF-bias timelines for every trading day 2023-01 -> 2026-07 (the full master set).

Per day: 08:00 INITIAL read -> event-triggered updates (15m invalidation close-through,
primary draw reached, CISD against, neutral flip-level break) -> mandatory 09:30 checkpoint
-> further event updates to 10:15. One CSV row per read: day,time,bias,tier,score,direction,
draws (up to 3, JSON'ish "px:kind|px:kind"). Appends incrementally (resumable): days already
in the cache are skipped on restart. No lookahead: every read uses only candles closed <= T.
"""
import os
import sys
from datetime import time as dtime

import pandas as pd

import importlib.util
_spec = importlib.util.spec_from_file_location("htf_bias", "/home/user/AI-trading-agents/htf_bias.py")
HB = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(HB)

NY = "America/New_York"
OUT = f"{S}/bias_timelines_3yr.csv"


def draws_str(st):
    return "|".join(f"{p:.2f}:{k}" for p, k in st.get("draws", []))


def read_row(day, tm, st):
    return dict(day=day, time=tm, bias=st["bias"], tier=st["tier"], score=st["score"],
                direction=st["direction"], draws=draws_str(st))


def main():
    bars = HB.load_bars()
    news = HB.load_news()
    all_days = sorted({str(d.date()) for d in bars.ts.dt.normalize().unique()
                       if d.weekday() < 5})
    done = set()
    if os.path.exists(OUT):
        done = set(pd.read_csv(OUT, usecols=["day"]).day.astype(str).unique())
        print(f"resume: {len(done)} days already cached", flush=True)
    todo = [d for d in all_days if d not in done]
    print(f"days total {len(all_days)}, todo {len(todo)}", flush=True)

    buf = []
    for i, dstr in enumerate(todo):
        D = pd.Timestamp(dstr, tz=NY)
        sl = bars[(bars.ts >= D - pd.Timedelta(days=60)) & (bars.ts < D + pd.Timedelta(days=1))].reset_index(drop=True)
        T0 = pd.Timestamp.combine(D.date(), dtime(8, 0)).tz_localize(NY)
        try:
            _, st = HB.read_at(sl, news, D, T0, "INITIAL premarket")
        except Exception as e:
            st = None
        if st is None:
            buf.append(dict(day=dstr, time="08:00", bias="NEUTRAL", tier="NEUTRAL", score=0,
                            direction="neutral", draws=""))
        else:
            buf.append(read_row(dstr, "08:00", st))
            fired = set()
            t = T0 + pd.Timedelta(minutes=15)
            end = pd.Timestamp.combine(D.date(), HB.WIN_END).tz_localize(NY)
            while t <= end:
                candle = sl[(sl.ts >= t - pd.Timedelta(minutes=15)) & (sl.ts < t)]
                if t.time() == dtime(9, 30):
                    _, ns = HB.read_at(sl, news, D, t, "UPDATE @ 09:30", prev_bias=st["bias"], trigger="0930")
                    if ns is not None:
                        st = ns; fired = set(); buf.append(read_row(dstr, "09:30", st))
                elif len(candle):
                    hi = float(candle.high.max()); lo = float(candle.low.min()); cl = float(candle.close.iloc[-1])
                    reasons = []
                    d = st["direction"]
                    if d in ("bullish", "bearish"):
                        ip = st["inval_px"]
                        if ip is not None and "inval" not in fired and ((d == "bullish" and cl < ip) or (d == "bearish" and cl > ip)):
                            reasons.append("inval"); fired.add("inval")
                        dp = st["draw_px"]
                        if dp is not None and "draw" not in fired and ((d == "bullish" and hi >= dp) or (d == "bearish" and lo <= dp)):
                            reasons.append("draw"); fired.add("draw")
                        if "cisd" not in fired:
                            f15 = HB.frames_asof(sl, t, D)["15m"]
                            against = "bearish" if d == "bullish" else "bullish"
                            if HB.cisd_last(f15.tail(30), against):
                                reasons.append("cisd"); fired.add("cisd")
                    else:
                        if "flip" not in fired:
                            if st["pdh"] is not None and cl > st["pdh"]:
                                reasons.append("flip"); fired.add("flip")
                            elif st["pdl"] is not None and cl < st["pdl"]:
                                reasons.append("flip"); fired.add("flip")
                    if reasons:
                        _, ns = HB.read_at(sl, news, D, t, f"UPDATE @ {t.strftime('%H:%M')}",
                                           prev_bias=st["bias"], trigger=";".join(reasons))
                        if ns is not None:
                            st = ns; buf.append(read_row(dstr, t.strftime("%H:%M"), st))
                t += pd.Timedelta(minutes=15)
        # flush every 5 days (resumable, crash-safe)
        if (i + 1) % 5 == 0 or (i + 1) == len(todo):
            df = pd.DataFrame(buf)
            df.to_csv(OUT, mode="a", header=not os.path.exists(OUT), index=False)
            buf = []
        if (i + 1) % 25 == 0:
            print(f"  {i+1}/{len(todo)} days", flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
