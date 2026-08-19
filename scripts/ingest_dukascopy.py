#!/usr/bin/env python3
"""Dukascopy tick ingest -> OHLCV bars at two resolutions from ONE source.

Why this exists: the CBR autopsy could not separate "the method fails" from "1-minute
bars are too coarse to test it", because the only sub-minute data available was paid.
Dukascopy publishes tick history for free, including XAUUSD — the instrument he
actually trades, rather than the GC futures proxy every earlier finding was measured on.

Building BOTH resolutions from the same ticks is the point. Comparing 5-second XAUUSD
against the existing 1-minute GC book would move instrument, period and resolution at
once and answer nothing. Here only the resolution moves.

Honest limits of this source, which travel with every number derived from it:
  - one broker's quotes, not a consolidated tape. Volume is Dukascopy's own flow, so
    it is a liquidity proxy at best and any volume-conditioned result is suspect.
  - bars are built from the MID. The spread is carried per bar so execution can be
    costed properly instead of assumed — that is the point of keeping it.
  - the file layout is hourly and the month is ZERO-INDEXED in the URL, which is the
    classic way to silently fetch the wrong month.

    python scripts/ingest_dukascopy.py --symbol XAUUSD --start 2026-05-01 --end 2026-08-11
"""
from __future__ import annotations

import argparse
import datetime as dt
import lzma
import struct
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://datafeed.dukascopy.com/datafeed"
REC = struct.Struct(">IIIff")          # ms-into-hour, ask, bid, ask_vol, bid_vol
SCALE = {"XAUUSD": 1000.0, "XAGUSD": 1000.0}   # price divisor; 3dp on metals


def fetch_hour(symbol: str, when: dt.datetime, tries: int = 6) -> tuple[bytes | None, str]:
    """One hourly .bi5, with the two failure modes kept apart.

    A 404 means Dukascopy has no file for that hour — the market was closed. A timeout
    or connection error means the request failed and the hour may well have data. If
    both are folded into "empty", a flaky network silently deletes trading hours from
    the sample and nothing downstream can tell. Returns (payload, reason).
    """
    url = (f"{BASE}/{symbol}/{when.year}/{when.month - 1:02d}/{when.day:02d}/"
           f"{when.hour:02d}h_ticks.bi5")
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return r.read(), "ok"
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None, "closed"           # authoritative: no such hour
            if attempt == tries - 1:
                return None, f"http{e.code}"
            # 429 is the feed asking for less, not a missing hour. Back off hard —
            # the first pass at 12 workers got throttled on 27 of 120 hours and,
            # without this, those become invisible holes in the sample.
            time.sleep((5 * 3 ** attempt) if e.code == 429 else 2 ** attempt)
            continue
        except (urllib.error.URLError, TimeoutError, OSError):
            if attempt == tries - 1:
                return None, "error"
        time.sleep(2 ** attempt)
    return None, "error"


def decode(raw: bytes, when: dt.datetime, scale: float) -> pd.DataFrame | None:
    if not raw:
        return None
    try:
        d = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE).decompress(raw)
    except lzma.LZMAError:
        return None
    n = len(d) // REC.size
    if n == 0:
        return None
    a = np.frombuffer(d[: n * REC.size], dtype=">u4,>u4,>u4,>f4,>f4")
    ms = a["f0"].astype("int64")
    ask = a["f1"].astype("float64") / scale
    bid = a["f2"].astype("float64") / scale
    return pd.DataFrame({
        "ts": pd.to_datetime(when, utc=True) + pd.to_timedelta(ms, unit="ms"),
        "mid": (ask + bid) / 2.0,
        "spread": ask - bid,
        "vol": (a["f3"].astype("float64") + a["f4"].astype("float64")),
    })


def to_bars(ticks: pd.DataFrame, rule: str) -> pd.DataFrame:
    """OHLCV on the mid, plus the median spread inside each bar.

    Bars are START-labelled (``label="left"``), matching ``indicators.resample_ohlcv``
    and the repo's convention — a 04:04 bar covers 04:04:00 to 04:04:59.
    """
    g = ticks.set_index("ts").resample(rule, label="left", closed="left")
    out = pd.DataFrame({
        "open": g["mid"].first(), "high": g["mid"].max(),
        "low": g["mid"].min(), "close": g["mid"].last(),
        "volume": g["vol"].sum(), "spread": g["spread"].median(),
        "ticks": g["mid"].size(),
    })
    return out.dropna(subset=["open"]).reset_index(names="ts_event")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="XAUUSD")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--rules", default="5s,1min")
    ap.add_argument("--workers", type=int, default=1)   # 4 and 12 both get 429d
    ap.add_argument("--pace", type=float, default=0.35, help="seconds between requests")
    a = ap.parse_args()

    start = dt.datetime.fromisoformat(a.start).replace(tzinfo=dt.timezone.utc)
    end = dt.datetime.fromisoformat(a.end).replace(tzinfo=dt.timezone.utc)
    hours = []
    t = start
    while t < end:
        if t.weekday() < 5 or (t.weekday() == 6 and t.hour >= 21):   # metals week
            hours.append(t)
        t += dt.timedelta(hours=1)
    print(f"{a.symbol}: {len(hours):,} hours {start.date()} -> {end.date()}", flush=True)

    scale = SCALE.get(a.symbol, 100000.0)
    def one(h):
        # steady pacing beats bursts: the feed throttles on rate, not on volume
        time.sleep(a.pace)
        raw, why = fetch_hour(a.symbol, h)
        return decode(raw, h, scale), why

    frames, done = [], 0
    reasons: dict[str, int] = {}
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for df, why in ex.map(one, hours):
            done += 1
            reasons[why] = reasons.get(why, 0) + 1
            if df is not None and not df.empty:
                frames.append(df)
            if done % 25 == 0:
                print(f"  {done:,}/{len(hours):,} hours  {reasons}", flush=True)

    print(f"fetch outcomes: {reasons}", flush=True)
    bad = sum(v for k, v in reasons.items() if k not in ("ok", "closed"))
    if bad:
        # a failed request is not a closed market; carrying on would delete real
        # trading hours from the sample without leaving a trace in the bars
        raise SystemExit(f"{bad} hours failed to fetch after retries — refusing to "
                         f"build bars from a silently truncated sample")
    if not frames:
        raise SystemExit("no data fetched")
    ticks = pd.concat(frames, ignore_index=True).sort_values("ts").reset_index(drop=True)
    print(f"ticks: {len(ticks):,}  {ticks.ts.min()} -> {ticks.ts.max()}  "
          f"({reasons.get('closed', 0):,} closed hours)", flush=True)
    print(f"spread: median {ticks.spread.median():.3f}  p90 "
          f"{ticks.spread.quantile(0.9):.3f}  p99 {ticks.spread.quantile(0.99):.3f}",
          flush=True)

    (ROOT / "data").mkdir(exist_ok=True)
    for rule in a.rules.split(","):
        bars = to_bars(ticks, rule)
        tag = rule.replace("min", "m").replace("s", "s")
        p = ROOT / f"data/{a.symbol.lower()}_{tag}.parquet"
        bars.to_parquet(p, index=False)
        print(f"  {p.name}: {len(bars):,} bars", flush=True)


if __name__ == "__main__":
    main()
