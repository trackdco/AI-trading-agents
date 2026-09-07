#!/usr/bin/env python3
"""
Build an UNADJUSTED NQ front-month 1-minute series from the repository's Databento files
(glbx-mdp3-*.ohlcv-1m.csv.zst: per-contract rows, GLBX.MDP3 ohlcv-1m) for prepare_holdout_data.py.

Front month = the outright NQ contract with the nearest third-Friday expiry that has not expired
as of the bar's CME trading day (roll at the start of the expiry date's session). Prices are the
contract's own — no back-adjustment — so round numbers are real round numbers and each quarterly
roll shows the true basis gap, as a live `NQ1!`/`MNQ1!` chart does.

Output: Databento-style CSV (ts_event ISO UTC, rtype, publisher_id, instrument_id, open, high, low,
close, volume, symbol). Prints counts and timestamps only.

The repository's config/data_split.yaml seals sessions 2025-02-01 .. 2026-01-30. Any request that
overlaps them is refused unless --acknowledge-seal is given; passing it records that the user
ruled the bot re-test may read those sessions, and the exposure is disclosed in RESULT.md.

usage: build_nq_series.py OUT.csv START END [--acknowledge-seal] [--roll expiry_day|monday_of_expiry_week]
       (--input-glob GLOB to read files other than the repository's; PREREGISTRATION-2 uses monday_of_expiry_week)
"""
import glob
import io
import re
import sys
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import zstandard

ET = ZoneInfo("America/New_York")
REPO = "/home/user/AI-trading-agents"
SEAL_START, SEAL_END = date(2025, 2, 1), date(2026, 1, 30)
MONTH = {"H": 3, "M": 6, "U": 9, "Z": 12}
OUTRIGHT = re.compile(r"^NQ([HMUZ])(\d)$")


def third_friday(y, m):
    d = date(y, m, 15)
    while d.weekday() != 4:
        d += timedelta(days=1)
    return d


def expiry(sym, bar_year):
    """Contract expiry from the one-digit year code, resolved relative to the bar's year: a row for
    a contract can only exist before that contract expires, so the code names the first year >= the
    bar's year with that last digit (NQH9 seen in 2018 -> 2019; NQZ8 seen in 2018 -> 2018)."""
    m = OUTRIGHT.match(sym)
    if not m:
        return None
    yd = int(m.group(2))
    year = bar_year + ((yd - bar_year % 10) % 10)
    return third_friday(year, MONTH[m.group(1)])


def trading_day(ts_utc):
    et = ts_utc.astimezone(ET)
    return (et + timedelta(days=1)).date() if et.hour >= 18 else et.date()


def roll_monday(exp):
    """Start of the expiry week's Monday session: the repository tape's convention."""
    return exp - timedelta(days=exp.weekday())          # third Friday -> that week's Monday


def main():
    out, start, end = sys.argv[1], date.fromisoformat(sys.argv[2]), date.fromisoformat(sys.argv[3])
    ack = "--acknowledge-seal" in sys.argv
    rule = "monday_of_expiry_week" if "--roll" in sys.argv and sys.argv[sys.argv.index("--roll") + 1] == "monday_of_expiry_week" else "expiry_day"
    if "--roll" in sys.argv:
        rule = sys.argv[sys.argv.index("--roll") + 1]
    assert rule in ("expiry_day", "monday_of_expiry_week"), rule
    print("roll rule:", rule)
    if start <= SEAL_END and end >= SEAL_START and not ack:
        sys.exit(f"requested {start}..{end} overlaps the sealed holdout {SEAL_START}..{SEAL_END}; "
                 f"refusing without --acknowledge-seal (see docstring)")
    pattern = sys.argv[sys.argv.index("--input-glob") + 1] if "--input-glob" in sys.argv else f"{REPO}/glbx-mdp3-*.ohlcv-1m.csv.zst"
    files = sorted(glob.glob(pattern))
    bars = {}          # ts -> dict(sym -> row)
    for p in files:
        with open(p, "rb") as fh:
            reader = (io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(fh), encoding="utf-8")
                      if p.endswith(".zst") else io.TextIOWrapper(fh, encoding="utf-8"))
            cols = reader.readline().strip().split(",")
            ix = {c: i for i, c in enumerate(cols)}
            for line in reader:
                parts = line.rstrip("\n").split(",")
                ts = datetime.fromisoformat(parts[ix["ts_event"]].replace("Z", "+00:00"))
                td = trading_day(ts)
                if td < start:
                    continue
                if td > end:
                    break
                sym = parts[ix["symbol"]]
                if not OUTRIGHT.match(sym):
                    continue
                bars.setdefault(ts, {})[sym] = parts
    n = 0
    fronts = {}
    with open(out, "w") as f:
        f.write("ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume,symbol\n")
        for ts in sorted(bars):
            td = trading_day(ts)
            exps = {s: expiry(s, td.year) for s in bars[ts]}
            if rule == "expiry_day":
                cands = [(e, s) for s, e in exps.items() if e and td < e]
            else:
                cands = [(e, s) for s, e in exps.items() if e and td < roll_monday(e)]
            if not cands:
                continue
            sym = min(cands)[1]
            parts = bars[ts][sym]
            f.write(",".join([ts.strftime("%Y-%m-%dT%H:%M:%S.000000000Z"), parts[ix["rtype"]], parts[ix["publisher_id"]],
                              parts[ix["instrument_id"]], parts[ix["open"]], parts[ix["high"]], parts[ix["low"]],
                              parts[ix["close"]], parts[ix["volume"]], sym]) + "\n")
            fronts[sym] = fronts.get(sym, 0) + 1
            n += 1
    tss = sorted(bars)
    print(f"files: {len(files)} | trading days {start}..{end} | minutes with any outright: {len(tss):,} | written {n:,} front-month bars")
    print(f"first {tss[0] if tss else None} last {tss[-1] if tss else None} | front contracts {fronts}")
    print("written", out)


if __name__ == "__main__":
    main()
