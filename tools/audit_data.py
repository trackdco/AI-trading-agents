#!/usr/bin/env python3
"""Audit every market-data file in the repo and print what actually exists.

Regenerates the tables in context/data-inventory.md. Run it after every data
purchase. A stale inventory is worse than none: it is how a backtest silently
runs on a window with no data and reports a flat equity curve as "no signals".

    python tools/audit_data.py
    python tools/audit_data.py --json

Only dependency for the bar audit is `zstandard`; the book audit is stdlib.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import itertools
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

BOOK_SETS = {
    "london": ("glbx-mdp3-2*.mbp-10_condensed.csv",),
    "new_york": ("condensed_glbx-mdp3-2*.mbp-10.csv", "condensed_GLBX-*.csv"),
}
BAR_GLOB = "*.ohlcv-1m.csv.zst"

# Rows sampled per book file. The files are ~150 rows, so this reads them whole
# while staying bounded if someone drops in an unfiltered day.
SAMPLE_ROWS = 5000


def _iter_book_files(patterns: tuple[str, ...]) -> list[Path]:
    found: list[Path] = []
    for pattern in patterns:
        found.extend(REPO_ROOT.glob(pattern))
    return sorted(set(found))


def audit_books() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for session, patterns in BOOK_SETS.items():
        files = _iter_book_files(patterns)
        days: dict[str, dict[str, Any]] = {}
        actions: collections.Counter = collections.Counter()
        symbols: collections.Counter = collections.Counter()
        scalings: collections.Counter = collections.Counter()

        for path in files:
            with path.open() as handle:
                handle.readline()  # header
                first = handle.readline()
                if not first:
                    continue
                rows = 1
                last = first
                for line in handle:
                    if rows >= SAMPLE_ROWS:
                        break
                    parts = line.split(",")
                    actions[parts[5]] += 1
                    rows += 1
                    last = line

            head = first.split(",")
            date = head[0][:10]
            symbols[head[-1].strip()] += 1
            price_int = head[8].split(".")[0]
            scaling = "fixed_point_1e9" if len(price_int) > 10 else "decimal"
            scalings[scaling] += 1
            actions[head[5]] += 1

            days[date] = {
                "file": path.name,
                "start_utc": head[0][11:16],
                "end_utc": last.split(",")[0][11:16],
                "rows": rows,
                "symbol": head[-1].strip(),
                "price_format": scaling,
            }

        dates = sorted(dt.date.fromisoformat(d) for d in days)
        out[session] = {
            "files": len(files),
            "unique_days": len(dates),
            "first": dates[0].isoformat() if dates else None,
            "last": dates[-1].isoformat() if dates else None,
            "symbols": dict(symbols),
            "price_formats": dict(scalings),
            "actions": dict(actions),
            "trades_in_sample": actions.get("T", 0),
            "gaps": _weekday_gaps(dates),
            "days_per_month": dict(
                sorted(collections.Counter(d.strftime("%Y-%m") for d in dates).items())
            ),
        }
    return out


def _weekday_gaps(dates: list[dt.date], min_missing: int = 3) -> list[dict[str, Any]]:
    gaps = []
    for start, end in itertools.pairwise(dates):
        missing = 0
        cursor = start + dt.timedelta(days=1)
        while cursor < end:
            if cursor.weekday() < 5:
                missing += 1
            cursor += dt.timedelta(days=1)
        if missing >= min_missing:
            gaps.append(
                {
                    "after": start.isoformat(),
                    "until": end.isoformat(),
                    "weekdays_missing": missing,
                }
            )
    return gaps


def audit_bars() -> list[dict[str, Any]]:
    try:
        import zstandard
    except ImportError:
        print(
            "zstandard not installed — skipping bar audit. `pip install zstandard`",
            file=sys.stderr,
        )
        return []

    results = []
    for path in sorted(REPO_ROOT.glob(BAR_GLOB)):
        decompressor = zstandard.ZstdDecompressor()
        symbols: collections.Counter = collections.Counter()
        rows = 0
        first = last = ""
        with path.open("rb") as raw:
            import io

            stream = io.TextIOWrapper(decompressor.stream_reader(raw), encoding="utf-8")
            header = stream.readline().strip().split(",")
            symbol_idx = header.index("symbol") if "symbol" in header else -1
            for line in stream:
                rows += 1
                if not first:
                    first = line
                last = line
                if symbol_idx >= 0 and rows % 500 == 0:
                    symbols[line.rstrip().split(",")[symbol_idx]] += 1
        results.append(
            {
                "file": path.name,
                "rows": rows,
                "columns": header,
                "first_ts": first.split(",")[0] if first else None,
                "last_ts": last.split(",")[0] if last else None,
                "symbols_sampled": sorted(symbols),
                # CVD needs a per-trade aggressor side. Depth columns are not
                # a substitute — resting size is not executed size.
                "has_aggressor_side": "side" in header,
            }
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    report = {
        "generated_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "repo_root": str(REPO_ROOT),
        "bars": audit_bars(),
        "books": audit_books(),
    }

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print(f"DATA AUDIT — {report['generated_at']}\n")

    print("=" * 78)
    print("MINUTE BARS (ohlcv-1m)")
    print("=" * 78)
    if not report["bars"]:
        print("  none found")
    for bar in report["bars"]:
        print(f"\n  {bar['file']}")
        print(f"    rows      : {bar['rows']:,}")
        print(f"    range     : {bar['first_ts'][:19]}  ->  {bar['last_ts'][:19]}")
        print(f"    contracts : {', '.join(bar['symbols_sampled'][:8])}")
        print(f"    CVD-capable: {'yes' if bar['has_aggressor_side'] else 'NO (no aggressor side)'}")

    print("\n" + "=" * 78)
    print("ORDER BOOK SNAPSHOTS (mbp-10)")
    print("=" * 78)
    for session, info in report["books"].items():
        print(f"\n  {session.upper()}")
        print(f"    files/days : {info['files']} files, {info['unique_days']} unique days")
        print(f"    range      : {info['first']}  ->  {info['last']}")
        print(f"    symbols    : {info['symbols']}")
        print(f"    price fmt  : {info['price_formats']}")
        print(f"    actions    : {info['actions']}")
        trades = info["trades_in_sample"]
        print(
            f"    trades     : {trades} "
            f"{'<- depth only, NO CVD derivable' if trades < 100 else ''}"
        )
        if info["gaps"]:
            print("    GAPS:")
            for gap in info["gaps"]:
                print(
                    f"      after {gap['after']} until {gap['until']} "
                    f"({gap['weekdays_missing']} weekdays missing)"
                )
        else:
            print("    gaps       : none longer than a long weekend")
        print("    days/month :")
        for month, count in info["days_per_month"].items():
            print(f"      {month}  {count:>3}")

    print("\n" + "=" * 78)
    print("Compare against context/data-inventory.md and update it if this differs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
