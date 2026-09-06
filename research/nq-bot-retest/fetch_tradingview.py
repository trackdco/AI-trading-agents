#!/usr/bin/env python3
"""
Holdout data acquisition — authorised by the user on 2026-09-06 ("Fetch") as a substitute for the
manual TradingView export named in PREREGISTRATION.md §3. Pulls CME_MINI:MNQ1! 1-minute bars from
TradingView's own chart datafeed (the `tvDatafeed` client's websocket session, anonymous), paging
backwards with `request_more_data` until the target start date is reached, and writes a
TradingView-style CSV (`time` = UNIX seconds UTC, open, high, low, close, Volume) for
prepare_holdout_data.py. Prints only counts and timestamps — no prices.

usage: fetch_tradingview.py OUT.csv TARGET_START_UTC(YYYY-MM-DD) [page_bars] [max_pages]
"""
import logging
import re
import sys
import time
from datetime import datetime, timezone

from tvDatafeed import TvDatafeed

logging.basicConfig(level=logging.ERROR)
out, target = sys.argv[1], datetime.fromisoformat(sys.argv[2]).replace(tzinfo=timezone.utc)
page = int(sys.argv[3]) if len(sys.argv) > 3 else 5000
max_pages = int(sys.argv[4]) if len(sys.argv) > 4 else 200
SYMBOL = "CME_MINI:MNQ1!"
BAR_RE = re.compile(r'\{"i":\d+,"v":\[([^\]]+)\]\}')
HB_RE = re.compile(r"~m~\d+~m~(~h~\d+)")

tv = TvDatafeed()
tv._TvDatafeed__create_connection()
tv.ws.settimeout(30)
send = tv._TvDatafeed__send_message
cs = tv.chart_session
send("set_auth_token", [tv.token])
send("chart_create_session", [cs, ""])
send("resolve_symbol", [cs, "symbol_1", '={"symbol":"' + SYMBOL + '","adjustment":"splits","session":"regular"}'])
send("create_series", [cs, "s1", "s1", "symbol_1", "1", page])
send("switch_timezone", [cs, "exchange"])

bars = {}


def recv_until_complete():
    """Collect frames until series_completed; echo heartbeats; return number of new bars."""
    new = 0
    while True:
        frame = tv.ws.recv()
        for hb in HB_RE.findall(frame):
            tv.ws.send("~m~" + str(len(hb)) + "~m~" + hb)
        for m in BAR_RE.finditer(frame):
            v = m.group(1).split(",")
            ep = int(float(v[0]))
            if ep not in bars:
                bars[ep] = (v[1], v[2], v[3], v[4], v[5] if len(v) > 5 else "0")
                new += 1
        if "series_completed" in frame:
            return new
        if '"critical_error"' in frame or "series_error" in frame:
            print("server error frame:", frame[:200])
            return new


t0 = time.time()
n = recv_until_complete()
earliest = datetime.fromtimestamp(min(bars), tz=timezone.utc)
print(f"page 0: +{n} bars, earliest {earliest:%Y-%m-%d %H:%M} UTC, total {len(bars):,}")
pages = 0
while earliest > target and pages < max_pages:
    send("request_more_data", [cs, "s1", page])
    try:
        n = recv_until_complete()
    except Exception as e:
        print("recv failed:", type(e).__name__, e)
        break
    pages += 1
    if n == 0:
        print(f"page {pages}: no new bars — server depth limit reached")
        break
    earliest = datetime.fromtimestamp(min(bars), tz=timezone.utc)
    if pages % 10 == 0 or earliest <= target:
        print(f"page {pages}: +{n} bars, earliest {earliest:%Y-%m-%d %H:%M} UTC, total {len(bars):,}  ({time.time() - t0:.0f}s)")
tv.ws.close()

with open(out, "w") as f:
    f.write("time,open,high,low,close,Volume\n")
    for ep in sorted(bars):
        o, h, l, c, v = bars[ep]
        f.write(f"{ep},{o},{h},{l},{c},{int(float(v))}\n")
latest = datetime.fromtimestamp(max(bars), tz=timezone.utc)
print(f"written {out}: {len(bars):,} bars, {earliest:%Y-%m-%d %H:%M} -> {latest:%Y-%m-%d %H:%M} UTC, {time.time() - t0:.0f}s")
