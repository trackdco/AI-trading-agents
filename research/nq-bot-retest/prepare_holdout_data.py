#!/usr/bin/env python3
"""
Holdout data preparation — PREREGISTRATION.md §5-bis.2.

Builds the union 1-minute series (checked-in exports + the fresh export) in the bot's .txt format,
runs the bot's own `prepare_historical_data.py` on it (combined_1min.csv + HTF files), and reports
the bar-by-bar overlap between the fresh export and the checked-in data.

Accepted fresh-export formats (auto-detected per file):
  * bot .txt:   `YYYY-MM-DD HH:MM:SS,open,high,low,close,volume` (naive ET), title/blank lines skipped
  * TradingView CSV: header `time,open,high,low,close,Volume`, `time` = UNIX seconds or ISO-8601 (UTC)
  * Databento ohlcv-1m CSV: header with `ts_event` (ISO-8601 UTC or ns epoch), open, high, low, close, volume

usage: prepare_holdout_data.py --fresh FILE [FILE ...] --out-dir DIR
       [--checked-in-dir /home/user/prat617/ai-trading-bot/data/tradingview]
       [--reference-combined .../data/historical/combined_1min.csv]

Nothing here reads outcomes: it converts timestamps, de-duplicates, and counts discrepancies.
"""
import argparse
import csv
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
BOT_ROOT = Path(os.environ.get("NQ_BOT_ROOT", "/home/user/prat617/ai-trading-bot/nq_bot_vscode"))
DEFAULT_CHECKED_IN = BOT_ROOT.parent / "data" / "tradingview"
DEFAULT_REFERENCE = BOT_ROOT / "data" / "historical" / "combined_1min.csv"


def parse_fresh(path: Path):
    """Yield (naive-ET 'YYYY-MM-DD HH:MM:SS', o, h, l, c, v) rows from either format."""
    rows = []
    with open(path, "r", encoding="utf-8-sig") as f:
        first = f.readline()
        f.seek(0)
        if "ts_event" in first:
            # Databento ohlcv-1m CSV: ts_event (ISO-8601 UTC or ns epoch), open, high, low, close, volume
            reader = csv.DictReader(f)
            for r in reader:
                try:
                    raw = r["ts_event"].strip()
                    if raw.isdigit():
                        ts = datetime.fromtimestamp(int(raw) / 1e9, tz=timezone.utc)
                    else:
                        ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                    ts = ts.astimezone(ET)
                    rows.append((ts.strftime("%Y-%m-%d %H:%M:%S"), float(r["open"]), float(r["high"]),
                                 float(r["low"]), float(r["close"]), int(float(r["volume"] or 0))))
                except (ValueError, KeyError, TypeError):
                    continue
            fmt = "databento-ohlcv-1m"
        elif first.lower().startswith("time,"):
            reader = csv.DictReader(f)
            for r in reader:
                try:
                    raw = r["time"].strip()
                    if raw.replace(".", "", 1).isdigit():
                        ts = datetime.fromtimestamp(int(float(raw)), tz=timezone.utc)
                    else:
                        ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                    ts = ts.astimezone(ET)
                    vol_key = "Volume" if "Volume" in r else "volume"
                    rows.append((ts.strftime("%Y-%m-%d %H:%M:%S"), float(r["open"]), float(r["high"]),
                                 float(r["low"]), float(r["close"]), int(float(r[vol_key] or 0))))
                except (ValueError, KeyError, TypeError):
                    continue
            fmt = "tradingview-epoch"
        else:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) < 6:
                    continue
                try:
                    datetime.strptime(parts[0].strip(), "%Y-%m-%d %H:%M:%S")
                    rows.append((parts[0].strip(), float(parts[1]), float(parts[2]), float(parts[3]),
                                 float(parts[4]), int(float(parts[5]))))
                except ValueError:
                    continue
            fmt = "bot-txt"
    return fmt, rows


def load_reference(path: Path):
    ref = {}
    if not path.exists():
        return ref
    with open(path, "r", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            ts = datetime.fromisoformat(r["timestamp"].replace(" ", "T", 1)) if "T" not in r["timestamp"] else datetime.fromisoformat(r["timestamp"])
            key = ts.astimezone(ET).strftime("%Y-%m-%d %H:%M:%S")
            ref[key] = (float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"]), int(float(r["volume"])))
    return ref


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fresh", nargs="+", required=True)
    ap.add_argument("--out-dir", required=True, help="where combined_1min.csv + htf_*.csv are written")
    ap.add_argument("--checked-in-dir", default=str(DEFAULT_CHECKED_IN))
    ap.add_argument("--reference-combined", default=str(DEFAULT_REFERENCE))
    ap.add_argument("--min-date", default="2025-09-01", help="fresh bars before this ET date are ignored (overlap check still reports them)")
    a = ap.parse_args()

    out_dir = Path(a.out_dir).resolve()
    union_dir = out_dir / "union_txt"
    union_dir.mkdir(parents=True, exist_ok=True)

    # 1. checked-in files, as they are (the bot's parser skips its own non-data lines)
    n_ci = 0
    for p in sorted(Path(a.checked_in_dir).glob("*.txt")):
        shutil.copy(p, union_dir / p.name)
        n_ci += 1
    print(f"checked-in files copied: {n_ci}")

    # 2. fresh export(s) -> bot .txt format, with overlap check against the reference combined series
    ref = load_reference(Path(a.reference_combined))
    print(f"reference combined bars: {len(ref):,}")
    overlap = same = diff = 0
    kept = 0
    first_ts = last_ts = None
    for fp in a.fresh:
        fmt, rows = parse_fresh(Path(fp))
        print(f"fresh {fp}: format={fmt} rows={len(rows):,}")
        out = union_dir / ("FRESH_" + Path(fp).stem + ".txt")
        with open(out, "w") as w:
            w.write(f"fresh export {Path(fp).name}\n")
            for ts, o, h, l, c, v in rows:
                if ts in ref:
                    overlap += 1
                    if (o, h, l, c, v) == ref[ts]:
                        same += 1
                    else:
                        diff += 1
                    continue  # checked-in bar kept where both exist (§5-bis.2)
                if ts[:10] < a.min_date:
                    continue
                w.write(f"{ts},{o},{h},{l},{c},{v}\n")
                kept += 1
                first_ts = first_ts or ts
                last_ts = ts
    print(f"overlap with checked-in data: {overlap:,} bars — identical {same:,}, different {diff:,}")
    print(f"fresh bars kept (>= {a.min_date}, not in checked-in): {kept:,}  [{first_ts} -> {last_ts}]")
    if kept == 0:
        sys.exit("no new bars — nothing to prepare")

    # 3. the bot's own preparation script on the union
    cmd = [sys.executable, str(BOT_ROOT / "scripts" / "prepare_historical_data.py"),
           "--input-dir", str(union_dir), "--output-dir", str(out_dir)]
    print("running:", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=str(BOT_ROOT))
    for name in ("combined_1min.csv", "htf_5m.csv", "htf_15m.csv", "htf_30m.csv", "htf_1H.csv", "htf_4H.csv", "htf_1D.csv"):
        p = out_dir / name
        print(f"  {name}: {'ok' if p.exists() else 'MISSING'} ({p.stat().st_size if p.exists() else 0:,} bytes)")


if __name__ == "__main__":
    main()
