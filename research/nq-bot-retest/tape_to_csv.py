#!/usr/bin/env python3
"""
Assemble the repository's canonical NQ 1-minute tape (unadjusted front month, Databento-built,
`data/reference/nq_1m_*.parquet`) into the Databento-style CSV that prepare_holdout_data.py accepts,
for a trading-day range. Files are given in precedence order and de-duplicated on ts_event keeping
the first occurrence — the same rule as the repository's own `load_bars()` (BARFILES order).

Also reports the junction with the bot's own series: over the overlap window the mean close
offset (bot − tape), the share of identical OHLC bars and the volume ratio. Counts only.

usage: tape_to_csv.py OUT.csv START END BOT_COMBINED.csv PARQUET [PARQUET ...]
"""
import csv
import statistics
import sys
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd

ET = ZoneInfo("America/New_York")
out, start, end, botcsv = sys.argv[1], date.fromisoformat(sys.argv[2]), date.fromisoformat(sys.argv[3]), sys.argv[4]
files = sys.argv[5:]

parts = []
for f in files:
    d = pd.read_parquet(f).drop(columns=["roll"], errors="ignore")
    print(f"  {f.split('/')[-1]}: {len(d):,} rows")
    parts.append(d)
b = pd.concat(parts, ignore_index=True).drop_duplicates("ts_event")
b["ts_utc"] = pd.to_datetime(b["ts_event"], utc=True)
b = b.sort_values("ts_utc").reset_index(drop=True)
et = b["ts_utc"].dt.tz_convert(ET)
tday = (et + pd.to_timedelta((et.dt.hour >= 18).astype(int), unit="D")).dt.date
b = b[(tday >= start) & (tday <= end)]
print(f"tape bars for trading days {start}..{end}: {len(b):,} | {b['ts_utc'].iloc[0]} -> {b['ts_utc'].iloc[-1]}")

with open(out, "w") as f:
    f.write("ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume,symbol\n")
    for ts, o, h, l, c, v in zip(b["ts_utc"], b["open"], b["high"], b["low"], b["close"], b["volume"]):
        f.write(f"{ts.strftime('%Y-%m-%dT%H:%M:%S.000000000Z')},33,1,0,{o},{h},{l},{c},{int(v)},NQ\n")
print("written", out)

# junction check against the bot's series (overlap = whatever both hold)
bot = {}
with open(botcsv, encoding="utf-8-sig") as fh:
    for r in csv.DictReader(fh):
        ts = datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M:%S%z").astimezone(timezone.utc)
        if ts.date() >= start - timedelta(days=1):
            bot[ts] = (float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"]), int(float(r["volume"])))
tape = {ts.to_pydatetime(): (o, h, l, c, int(v)) for ts, o, h, l, c, v in zip(b["ts_utc"], b["open"], b["high"], b["low"], b["close"], b["volume"])}
common = sorted(ts for ts in bot if ts in tape)
if common:
    off = [bot[ts][3] - tape[ts][3] for ts in common]
    same = sum(bot[ts][:4] == tape[ts][:4] for ts in common)
    vr = [bot[ts][4] / tape[ts][4] for ts in common if tape[ts][4]]
    by_month = {}
    for ts in common:
        by_month.setdefault(ts.strftime("%Y-%m"), []).append(bot[ts][3] - tape[ts][3])
    print(f"overlap with bot series: {len(common):,} minutes ({common[0]:%Y-%m-%d} -> {common[-1]:%Y-%m-%d})")
    print(f"  close offset bot−tape: mean {statistics.mean(off):+.3f} sd {statistics.pstdev(off):.3f} | identical OHLC {100*same/len(common):.1f}% | volume ratio median {statistics.median(vr):.3f}")
    for m_, v_ in sorted(by_month.items()):
        print(f"    {m_}: n={len(v_):,} offset mean {statistics.mean(v_):+.2f} sd {statistics.pstdev(v_):.2f}")
else:
    print("no overlap with the bot series")
