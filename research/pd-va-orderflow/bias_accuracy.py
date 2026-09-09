#!/usr/bin/env python3
"""
Daily-bias rule from the video, measured on NQ 1-minute bars 2018-08 → 2026-09.

Bias at the 09:30 open vs the PREVIOUS cash session's (09:30–16:00 ET) 70% value area, volume
profile from 1-minute bars with each bar's volume spread uniformly over its range at 0.25:
  open > VAH → bullish; open < VAL → bearish; else neutral.
Correct: bullish → cash close > cash open; bearish → close < open;
         neutral → close inside [VAL, VAH] (reading A) / day range below the median (reading B).
Baselines: unconditional up-day rate; gap rule (open > previous cash close → up) on the same days.
Contract-roll weeks (Mon..Fri of the quarterly third Friday) in the unadjusted segments are excluded.
"""
import csv
import statistics as st
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np

ET = ZoneInfo("America/New_York")
TICK = 0.25
SERIES = [("/home/user/AI-trading-agents/research/nq-bot-retest/data/holdout2_input/prepared/combined_1min.csv", "2018-08-01", "2021-08-31"),
          ("/home/user/AI-trading-agents/research/nq-bot-retest/data/holdout_input/prepared/combined_1min.csv", "2021-09-01", "2026-09-03")]


def value_area(bars):
    lo = int(round(min(b[2] for b in bars) / TICK)); hi = int(round(max(b[1] for b in bars) / TICK))
    prof = np.zeros(hi - lo + 1)
    for _, h, l, _, v in bars:
        a = int(round(l / TICK)) - lo; b = int(round(h / TICK)) - lo
        prof[a:b + 1] += v / (b - a + 1)
    if prof.sum() <= 0:
        return None
    poc = int(np.argmax(prof)); target = 0.7 * prof.sum(); acc = prof[poc]; up = poc + 1; dn = poc - 1
    while acc < target and (up < len(prof) or dn >= 0):
        vu = prof[up] if up < len(prof) else -1; vd = prof[dn] if dn >= 0 else -1
        if vu >= vd: acc += vu; up += 1
        else: acc += vd; dn -= 1
    return (poc + lo) * TICK, (dn + 1 + lo) * TICK, (up - 1 + lo) * TICK


days = {}   # date -> list of (o,h,l,c,v) for 09:30–15:59 bars, in order
for path, a, b in SERIES:
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            d = r["timestamp"][:10]
            if d < a or d > b: continue
            t = datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M:%S%z").astimezone(ET)
            hm = t.hour * 60 + t.minute
            if 570 <= hm < 960:
                days.setdefault(t.date(), []).append((float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"]), float(r["volume"])))
dates = sorted(d for d in days if len(days[d]) >= 300)
rows = []
prev = None
for d in dates:
    bars = days[d]
    if prev is not None:
        va = value_area(days[prev])
        o = bars[0][0]; c = bars[-1][3]; hi = max(b[1] for b in bars); lo = min(b[2] for b in bars); pc = days[prev][-1][3]
        # exclude only contract-roll sessions in the unadjusted segments: the expiry week (Mon..Fri of the third Friday)
        from datetime import timedelta as _td
        def _third_friday(y, m):
            x = d.replace(year=y, month=m, day=15)
            while x.weekday() != 4: x += _td(days=1)
            return x
        raw_segment = d.year < 2021 or (d.year == 2021 and d.month < 9) or d >= d.replace(year=2025, month=9, day=1)
        tf = _third_friday(d.year, ((d.month - 1) // 3 + 1) * 3) if d.month % 3 == 0 else None
        in_roll_week = raw_segment and tf is not None and (tf - _td(days=4)) <= d <= tf
        if va and not in_roll_week:
            poc, val, vah = va
            bias = "bullish" if o > vah else ("bearish" if o < val else "neutral")
            rows.append({"date": d, "bias": bias, "o": o, "c": c, "hi": hi, "lo": lo, "pc": pc, "poc": poc, "val": val, "vah": vah,
                         "range": hi - lo, "up": c > o, "gap_up": o > pc, "close_in_va": val <= c <= vah,
                         "touched_vah": lo <= vah <= hi, "touched_val": lo <= val <= hi})
        else:
            rows.append(None)
    prev = d
rows = [r for r in rows if r]
excluded = len(dates) - 1 - len(rows)
med_range = st.median(r["range"] for r in rows)
for r in rows: r["small_range"] = r["range"] < med_range

def pct(xs): return f"{100*sum(xs)/len(xs):.1f}%" if xs else "n/a"
def show(rs, label):
    bull = [r for r in rs if r["bias"] == "bullish"]; bear = [r for r in rs if r["bias"] == "bearish"]; neu = [r for r in rs if r["bias"] == "neutral"]
    print(f"\n{label}: {len(rs)} sessions | bullish {len(bull)} ({100*len(bull)/len(rs):.0f}%), bearish {len(bear)} ({100*len(bear)/len(rs):.0f}%), neutral {len(neu)} ({100*len(neu)/len(rs):.0f}%)")
    print(f"  unconditional up-day rate {pct([r['up'] for r in rs])}; gap rule (open>prev close → up, open<prev close → down) accuracy {pct([r['up']==r['gap_up'] for r in rs if r['o']!=r['pc']])}")
    print(f"  bullish bias → close>open: {pct([r['up'] for r in bull])}   | gap rule on the same days: {pct([r['up']==r['gap_up'] for r in bull])} | day extends more up than down (hi−o > o−lo): {pct([r['hi']-r['o'] > r['o']-r['lo'] for r in bull])} | pulled back to VAH intraday: {pct([r['touched_vah'] for r in bull])}")
    print(f"  bearish bias → close<open: {pct([not r['up'] for r in bear])} | gap rule on the same days: {pct([r['up']==r['gap_up'] for r in bear])} | day extends more down than up: {pct([r['o']-r['lo'] > r['hi']-r['o'] for r in bear])} | rallied to VAL intraday: {pct([r['touched_val'] for r in bear])}")
    print(f"  neutral bias → close inside PD value area: {pct([r['close_in_va'] for r in neu])} | range below median: {pct([r['small_range'] for r in neu])} | (all days: close inside PD VA {pct([r['close_in_va'] for r in rs])}, range below median {pct([r['small_range'] for r in rs])})")
    directional = bull + bear
    print(f"  directional days combined (bull→up, bear→down): {pct([r['up']==(r['bias']=='bullish') for r in directional])} on {len(directional)} days vs gap rule on the same days {pct([r['up']==r['gap_up'] for r in directional])}")

print(f"cash sessions 2018-08 → 2026-09 with a prior session: {len(rows)} (excluded {excluded}: roll weeks in unadjusted segments or missing profile); median cash range {med_range:.0f} pt")
show(rows, "ALL YEARS")
for y in range(2018, 2027):
    ys = [r for r in rows if r["date"].year == y]
    if len(ys) > 50: show(ys, str(y))
