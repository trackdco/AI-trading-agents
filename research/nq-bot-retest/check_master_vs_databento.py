#!/usr/bin/env python3
"""Provenance check: is the repository's nq_1m_master.parquet an UNADJUSTED NQ front-month series?
Compares it with the raw per-contract Databento front-month build (build_nq_series.py) on
workbench dates 2024-12-01 .. 2025-01-31. Prints aggregates only.
usage: check_master_vs_databento.py MASTER.parquet RAW_FRONT.csv"""
import csv
import statistics
import sys
from datetime import datetime

import pyarrow.parquet as pq

master, rawcsv = sys.argv[1], sys.argv[2]
t = pq.read_table(master).to_pandas()
t = t[(t["ts_event"] >= "2024-12-01") & (t["ts_event"] < "2025-02-01")]
m = {ts.tz_convert("UTC").to_pydatetime(): (o, h, l, c, v)
     for ts, o, h, l, c, v in zip(t["ts_event"], t["open"], t["high"], t["low"], t["close"], t["volume"])}
raw = {}
for r in csv.DictReader(open(rawcsv)):
    ts = datetime.fromisoformat(r["ts_event"].replace("Z", "+00:00"))
    raw[ts] = (float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"]), int(r["volume"]), r["symbol"])
common = [ts for ts in m if ts in raw]
print(f"master rows in window: {len(m):,}; raw front-month rows: {len(raw):,}; common: {len(common):,}")
by = {}
for ts in common:
    sym = raw[ts][5]
    by.setdefault(sym, []).append((m[ts][3] - raw[ts][3], (m[ts][4] / raw[ts][4]) if raw[ts][4] else None, m[ts][:4] == raw[ts][:4]))
for sym, rows in by.items():
    off = [r[0] for r in rows]
    vr = [r[1] for r in rows if r[1] is not None]
    same = sum(r[2] for r in rows)
    print(f"  {sym}: n={len(rows):,}  close offset mean {statistics.mean(off):+.3f} sd {statistics.pstdev(off):.3f}  "
          f"identical OHLC {100 * same / len(rows):.1f}%  volume ratio median {statistics.median(vr):.3f}")
diff_days = sorted({ts.date() for ts in common if m[ts][:4] != raw[ts][:4]})
print(f"days with any differing bar: {len(diff_days)} -> {[d.isoformat() for d in diff_days[:10]]}")
