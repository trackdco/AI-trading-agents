#!/usr/bin/env python3
"""
How close are the repo's Databento NQ bars to the bot's TradingView MNQ1! bars?
Workbench dates only (stops before the first holdout-dated bar, 2025-01-31 22:00 UTC).

Builds an NQ front-month series from the per-contract rows (outrights only; roll at the third
Friday of the contract month under two candidate rules) and compares it minute by minute with
the bot's combined_1min.csv over 2024-09-01 -> 2025-01-31. Prints aggregate agreement only.
"""
import csv
import io
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import zstandard

ET = ZoneInfo("America/New_York")
REPO = "/home/user/AI-trading-agents"
BOT = "/home/user/prat617/ai-trading-bot/nq_bot_vscode/data/historical/combined_1min.csv"
START = datetime(2024, 9, 1, tzinfo=timezone.utc)
STOP = datetime(2025, 1, 31, 22, 0, tzinfo=timezone.utc)   # end of the last workbench session
MONTH = {"H": 3, "M": 6, "U": 9, "Z": 12}
OUTRIGHT = re.compile(r"^NQ([HMUZ])(\d)$")


def third_friday(y, m):
    d = date(y, m, 15)
    while d.weekday() != 4:
        d += timedelta(days=1)
    return d


def expiry(sym):
    m = OUTRIGHT.match(sym)
    if not m:
        return None
    mon, yd = MONTH[m.group(1)], int(m.group(2))
    year = 2020 + yd if yd < 8 else 2010 + yd          # 3->2023 ... 7->2027
    return third_friday(year, mon)


def trading_day(ts_utc):
    et = ts_utc.astimezone(ET)
    return (et + timedelta(days=1)).date() if et.hour >= 18 else et.date()


# ── Databento rows, workbench window only ──
rows = defaultdict(dict)     # ts -> {sym: (o,h,l,c,v)}
p = f"{REPO}/glbx-mdp3-20230101-20250301.ohlcv-1m.csv.zst"
with open(p, "rb") as fh:
    reader = io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(fh), encoding="utf-8")
    cols = reader.readline().strip().split(",")
    ix = {c: i for i, c in enumerate(cols)}
    for line in reader:
        parts = line.rstrip("\n").split(",")
        ts = datetime.fromisoformat(parts[ix["ts_event"]].replace("Z", "+00:00"))
        if ts >= STOP:
            break
        if ts < START:
            continue
        sym = parts[ix["symbol"]]
        if not OUTRIGHT.match(sym):
            continue
        rows[ts][sym] = (float(parts[ix["open"]]), float(parts[ix["high"]]), float(parts[ix["low"]]),
                         float(parts[ix["close"]]), int(parts[ix["volume"]]))
print(f"databento NQ outright bars {START:%Y-%m-%d} -> {STOP:%Y-%m-%d %H:%M}Z: {len(rows):,} minutes")

# ── bot MNQ1! bars in the same window ──
bot = {}
with open(BOT, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        ts = datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M:%S%z").astimezone(timezone.utc)
        if START <= ts < STOP:
            bot[ts] = (float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"]), int(float(r["volume"])))
print(f"bot MNQ1! bars in window: {len(bot):,} minutes")


def front(ts, rule):
    """rule 'expiry_day': the expiring contract is dropped on its expiry date; 'day_after': dropped the day after."""
    td = trading_day(ts)
    cands = []
    for sym in rows[ts]:
        e = expiry(sym)
        alive = (td < e) if rule == "expiry_day" else (td <= e)
        if alive:
            cands.append((e, sym))
    return min(cands)[1] if cands else None


for rule in ("expiry_day", "day_after"):
    common = [ts for ts in bot if ts in rows]
    n = len(common)
    same_ohlc = same_close = 0
    dclose = []
    vratio = []
    syms = Counter()
    for ts in common:
        sym = front(ts, rule)
        if sym is None:
            continue
        syms[sym] += 1
        o, h, l, c, v = rows[ts][sym]
        bo, bh, bl, bc, bv = bot[ts]
        same_ohlc += (o, h, l, c) == (bo, bh, bl, bc)
        same_close += c == bc
        dclose.append(abs(c - bc))
        if v > 0:
            vratio.append(bv / v)
    dclose.sort()
    vratio.sort()
    q = lambda a, p: a[int(p * (len(a) - 1))] if a else None
    print(f"\nroll rule {rule}: common minutes {n:,}; front contracts {dict(syms)}")
    print(f"  identical OHLC {100*same_ohlc/n:.1f}% | identical close {100*same_close/n:.1f}% | "
          f"|dclose| median {q(dclose,0.5)} p90 {q(dclose,0.9)} p99 {q(dclose,0.99)} max {dclose[-1] if dclose else None} pts")
    print(f"  MNQ/NQ volume ratio: p10 {q(vratio,0.1):.2f} median {q(vratio,0.5):.2f} p90 {q(vratio,0.9):.2f}")
missing_in_db = sum(1 for ts in bot if ts not in rows)
missing_in_bot = sum(1 for ts in rows if ts not in bot)
print(f"\nminutes in bot but not databento: {missing_in_db:,}; in databento but not bot: {missing_in_bot:,}")

# ── per-segment price offset (bot − databento), rule expiry_day ──
import statistics
seg = defaultdict(list)
for ts in bot:
    if ts in rows:
        sym = front(ts, "expiry_day")
        if sym:
            seg[sym].append(bot[ts][3] - rows[ts][sym][3])
print("\noffset bot_close − NQ_front_close by front contract (points):")
for sym in sorted(seg, key=expiry):
    d = seg[sym]
    print(f"  {sym} (expires {expiry(sym)}): n={len(d):,} mean {statistics.mean(d):+.2f} sd {statistics.pstdev(d):.2f} min {min(d):+.2f} max {max(d):+.2f}")
