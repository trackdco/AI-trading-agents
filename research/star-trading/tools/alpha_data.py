#!/usr/bin/env python3
"""Build the front-month NQ bar store for the cluster-alpha feasibility test.

Handles, per the Stage 0 audit:
  * calendar spreads excluded (any symbol containing '-')
  * front month chosen per UTC day by traded volume
  * overlapping source archives deduped on (symbol, ts)
  * rolls detected; the session after a roll is skipped by the caller
  * bars are OPEN-LABELLED at source: the bar stamped 00:00 covers 00:00:00-00:00:59,
    so its `open` IS the price at 00:00:00 — which is the alpha entry reference.

Writes a compact cache so the feasibility steps do not re-parse 1.65M rows.
"""
from __future__ import annotations

import csv
import io
import json
import pickle
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CACHE = Path(__file__).resolve().parent / "_nq_frontmonth.pkl"

ARCHIVES = [
    "glbx-mdp3-20230101-20250301.ohlcv-1m.csv.zst",
    "glbx-mdp3-20250101-20250501.ohlcv-1m.csv.zst",
    "glbx-mdp3-20250502-20251001.ohlcv-1m.csv.zst",
    "glbx-mdp3-20251002-20260131.ohlcv-1m.csv.zst",
]


def stream(path: Path):
    p = subprocess.Popen(["zstd", "-dc", str(path)], stdout=subprocess.PIPE)
    for row in csv.DictReader(io.TextIOWrapper(p.stdout, encoding="utf-8")):
        yield row
    p.wait()


def build():
    # ---- pass 1: daily volume per symbol, to pick the front month ----------
    day_sym_vol: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    seen_files = []
    for name in ARCHIVES:
        f = REPO / name
        if not f.exists():
            print(f"  MISSING {name}", file=sys.stderr)
            continue
        seen_files.append(name)
        n = 0
        for r in stream(f):
            sym = r["symbol"]
            if "-" in sym:                      # calendar spread — never trade these
                continue
            day_sym_vol[r["ts_event"][:10]][sym] += int(float(r["volume"]))
            n += 1
        print(f"  pass1 {name}: {n:,} outright rows")

    front = {d: max(v.items(), key=lambda kv: kv[1])[0] for d, v in day_sym_vol.items()}

    # ---- pass 2: keep only front-month bars, deduped -----------------------
    bars: dict[str, dict[int, tuple]] = defaultdict(dict)   # date -> {minute_of_day: (o,h,l,c,v)}
    for name in seen_files:
        for r in stream(REPO / name):
            sym = r["symbol"]
            if "-" in sym:
                continue
            d = r["ts_event"][:10]
            if front.get(d) != sym:
                continue
            hh, mm = int(r["ts_event"][11:13]), int(r["ts_event"][14:16])
            key = hh * 60 + mm
            if key in bars[d]:                  # archive overlap — first wins
                continue
            bars[d][key] = (float(r["open"]), float(r["high"]),
                            float(r["low"]), float(r["close"]), int(float(r["volume"])))
        print(f"  pass2 {name}: cumulative {len(bars):,} UTC days")

    out = {"front": front, "bars": {d: dict(v) for d, v in bars.items()}}
    CACHE.write_bytes(pickle.dumps(out, protocol=4))
    print(f"\ncached {len(bars):,} UTC days -> {CACHE}")
    return out


def load():
    if CACHE.exists():
        return pickle.loads(CACHE.read_bytes())
    return build()


if __name__ == "__main__":
    d = build()
    days = sorted(d["bars"])
    print(f"date range {days[0]} -> {days[-1]}")
    rolls = [days[i] for i in range(1, len(days)) if d["front"][days[i]] != d["front"][days[i - 1]]]
    print(f"rolls detected: {len(rolls)} -> {rolls}")
