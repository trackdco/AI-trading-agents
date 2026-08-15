#!/usr/bin/env python3
"""Accept/reject test for a rebuilt data/gc_1m.parquet.

The gold-track parquets are gitignored and die with their container. When one is rebuilt
from the Databento CSV (see docs/DATA-PROVENANCE-gold.md) the question is whether it is
the *same* file the published findings were measured on. Eyeballing a bar count does not
answer that; this does.

Checks the invariants recorded in the provenance doc, plus the validation the ingest
already enforces, plus the two data-quality facts that condition.json either states or
misses. Exits non-zero on any failure so it can gate a re-run.

    python scripts/verify_gold_data.py [path]
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# The 18:00-anchored session day has one definition in this repo and this is it. Counting
# session-days by calendar date instead gives 1,124 rather than 936 — a 20% overstatement,
# and the kind of quiet divergence that makes two docs disagree about the same sample.
from src.research.gold.htf_census import NY, _session_day

EXPECTED = {
    "bars": 1_276_717,
    "first": "2023-01-02 18:00:00-05:00",
    "last": "2026-08-11 19:59:00-04:00",
    "rolls": 19,
    "contracts": 20,
    "session_days": 936,
}
# Query boundary, not a market day: ~2h of bars because the export ends 2026-08-12T00:00Z
# and the NY session opens 18:00 the evening before. condition.json does not flag it.
STUB_SESSION_DAY = "2026-08-11"


def check(label: str, got, want) -> bool:
    ok = got == want
    print(f"  {'ok  ' if ok else 'FAIL'} {label:<22} {got!r}" + ("" if ok else f"  want {want!r}"))
    return ok


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/gc_1m.parquet")
    if not path.exists():
        print(f"{path} is missing — rebuild it, see docs/DATA-PROVENANCE-gold.md")
        return 2

    df = pd.read_parquet(path)
    df["ts_event"] = pd.to_datetime(df["ts_event"], utc=True).dt.tz_convert(NY)
    sday = pd.Series(_session_day(pd.DatetimeIndex(df["ts_event"])), index=df.index)

    print(f"{path}")
    results = [
        check("bars", len(df), EXPECTED["bars"]),
        check("first bar", str(df["ts_event"].min()), EXPECTED["first"]),
        check("last bar", str(df["ts_event"].max()), EXPECTED["last"]),
        check("rolls", int(df["roll"].sum()), EXPECTED["rolls"]),
        check("contracts", int(df["symbol"].nunique()), EXPECTED["contracts"]),
        check("session-days", int(sday.nunique()), EXPECTED["session_days"]),
        check("nulls", int(df.isna().sum().sum()), 0),
        check("high < low", int((df["high"] < df["low"]).sum()), 0),
        check("duplicate ts", int(df["ts_event"].duplicated().sum()), 0),
        check("non-positive px", int((df[["open", "high", "low", "close"]] <= 0).any(axis=1).sum()), 0),
        check("monotonic ts", bool(df["ts_event"].is_monotonic_increasing), True),
    ]

    counts = sday.groupby(sday).size()
    stub = int(counts.get(pd.Timestamp(STUB_SESSION_DAY).date(), 0))
    print(f"\n  note  truncated tail session {STUB_SESSION_DAY}: {stub} bars "
          f"({stub / counts.median() * 100:.0f}% of median) — drop it in session-window work")

    failed = results.count(False)
    print(f"\n{'PASS' if not failed else f'FAIL ({failed} checks)'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
