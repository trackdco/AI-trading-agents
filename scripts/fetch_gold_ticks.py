#!/usr/bin/env python3
"""Download XAUUSD tick history and write 5-second and 1-minute bars. Stdlib only.

RUN THIS ON A HOME CONNECTION, NOT IN A CLOUD CONTAINER. Dukascopy rate-limits
datacenter IPs hard — the same pull took ~2.2 minutes per hour of data from a cloud
box and should take a second or two per hour from a laptop.

No pip install, no virtualenv, nothing to set up: urllib, lzma, struct, gzip and csv
are all in the standard library. Output is two gzipped CSVs, a few MB each.

    python3 scripts/fetch_gold_ticks.py                      # last 3 months
    python3 scripts/fetch_gold_ticks.py --start 2026-02-01 --end 2026-08-11

Both resolutions come from the SAME ticks on purpose. The open question is whether a
5-second entry gets a better reward:risk than a 1-minute one; comparing against bars
from a different source or a different instrument would move two things at once and
answer nothing.

Bars are START-labelled: an 04:04:00 bar covers 04:04:00 through 04:04:04.999.
Prices are the MID. The median spread inside each bar is carried as a column, because
execution has to be costed from measured quotes rather than a guessed tick size.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import struct
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    import lzma
except ImportError:                                  # pragma: no cover
    sys.exit("This Python has no lzma module. On macOS install the Command Line "
             "Tools (xcode-select --install) or use python.org's build.")

BASE = "https://datafeed.dukascopy.com/datafeed"
REC = struct.Struct(">IIIff")        # ms-into-hour, ask, bid, ask_vol, bid_vol
SCALE = 1000.0                       # XAUUSD quotes carry 3 decimals
COLS = ["ts_event", "open", "high", "low", "close", "volume", "spread", "ticks"]


def fetch(symbol: str, when: dt.datetime, tries: int = 5) -> tuple[bytes | None, str]:
    """One hourly file. A 404 means the market was closed; anything else means the
    request failed and the hour may well hold data. Conflating them silently deletes
    trading hours from the sample, so they are kept apart and counted separately."""
    url = (f"{BASE}/{symbol}/{when.year}/{when.month - 1:02d}/{when.day:02d}/"
           f"{when.hour:02d}h_ticks.bi5")            # NB: month is ZERO-indexed
    import time
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return r.read(), "ok"
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None, "closed"
            if attempt == tries - 1:
                return None, f"http{e.code}"
            time.sleep(min(30, 3 * 2 ** attempt))
        except (urllib.error.URLError, TimeoutError, OSError):
            if attempt == tries - 1:
                return None, "error"
            time.sleep(min(30, 2 ** attempt))
    return None, "error"


def ticks_of(raw: bytes | None) -> list[tuple[int, float, float]]:
    """(ms into the hour, mid, spread) for every tick in one hourly file."""
    if not raw:
        return []
    try:
        d = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE).decompress(raw)
    except lzma.LZMAError:
        return []
    out = []
    for i in range(len(d) // REC.size):
        ms, ask, bid, av, bv = REC.unpack_from(d, i * REC.size)
        out.append((ms, (ask + bid) / 2.0 / SCALE, (ask - bid) / SCALE, av + bv))
    return out


def bars_of(ticks, hour: dt.datetime, seconds: int) -> list[list]:
    """Bucket one hour of ticks into fixed-width bars. Empty buckets are skipped."""
    buckets: dict[int, list] = {}
    for ms, mid, spread, vol in ticks:
        k = ms // (seconds * 1000)
        b = buckets.get(k)
        if b is None:
            buckets[k] = [mid, mid, mid, mid, vol, [spread], 1]
        else:
            b[1] = max(b[1], mid)
            b[2] = min(b[2], mid)
            b[3] = mid
            b[4] += vol
            b[5].append(spread)
            b[6] += 1
    rows = []
    for k in sorted(buckets):
        o, hi, lo, c, vol, sp, n = buckets[k]
        sp.sort()
        ts = hour + dt.timedelta(seconds=k * seconds)
        rows.append([ts.strftime("%Y-%m-%dT%H:%M:%S+00:00"), f"{o:.3f}", f"{hi:.3f}",
                     f"{lo:.3f}", f"{c:.3f}", f"{vol:.4f}",
                     f"{sp[len(sp) // 2]:.3f}", n])
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="XAUUSD")
    ap.add_argument("--start", default="")
    ap.add_argument("--end", default="2026-08-11")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default=".")
    a = ap.parse_args()

    end = dt.datetime.fromisoformat(a.end).replace(tzinfo=dt.timezone.utc)
    start = (dt.datetime.fromisoformat(a.start).replace(tzinfo=dt.timezone.utc)
             if a.start else end - dt.timedelta(days=92))

    hours, t = [], start
    while t < end:
        if t.weekday() < 5 or (t.weekday() == 6 and t.hour >= 21):
            hours.append(t)
        t += dt.timedelta(hours=1)
    print(f"{a.symbol}: {len(hours):,} hours, {start.date()} -> {end.date()}", flush=True)

    outdir = Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    p5 = outdir / f"{a.symbol.lower()}_5s.csv.gz"
    p1 = outdir / f"{a.symbol.lower()}_1m.csv.gz"

    reasons: dict[str, int] = {}
    n5 = n1 = 0
    with (gzip.open(p5, "wt", newline="") as f5, gzip.open(p1, "wt", newline="") as f1):
        w5, w1 = csv.writer(f5), csv.writer(f1)
        w5.writerow(COLS)
        w1.writerow(COLS)
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            results = ex.map(lambda h: (h, *fetch(a.symbol, h)), hours)
            for i, (hour, raw, why) in enumerate(results, 1):
                reasons[why] = reasons.get(why, 0) + 1
                tk = ticks_of(raw)
                if tk:
                    r5 = bars_of(tk, hour, 5)
                    r1 = bars_of(tk, hour, 60)
                    w5.writerows(r5)
                    w1.writerows(r1)
                    n5 += len(r5)
                    n1 += len(r1)
                if i % 50 == 0 or i == len(hours):
                    print(f"  {i:,}/{len(hours):,} hours · {n5:,} 5s bars · {reasons}",
                          flush=True)

    bad = sum(v for k, v in reasons.items() if k not in ("ok", "closed"))
    print(f"\noutcomes: {reasons}")
    print(f"{p5}  {n5:,} bars  {p5.stat().st_size / 1e6:.1f} MB")
    print(f"{p1}  {n1:,} bars  {p1.stat().st_size / 1e6:.1f} MB")
    if bad:
        print(f"\nWARNING: {bad} hours failed to fetch (not 'closed' — actually failed).")
        print("Those hours are MISSING from the files. Re-run to fill them, or say so")
        print("when you hand the data over so the gap is on the record.")
    else:
        print("\nNo failed hours — every gap is a genuinely closed market.")


if __name__ == "__main__":
    main()
