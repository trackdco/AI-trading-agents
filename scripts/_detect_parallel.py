#!/usr/bin/env python3
"""Parallel day-sharded trigger detection (pass 23; generalized pass 24 for the full-dataset
mandate). Days are independent -> shard across worker processes. Kill-safe: each finished day
writes <out-stem>_days/<day>.csv; re-running skips finished days; everything merges into --out.

    python -m scripts._detect_parallel --start 2026-06-01 --end 2026-07-15 \
        --out output/triggers_junjul.csv
    python -m scripts._detect_parallel --start 2026-02-02 --end 2026-04-30 \
        --out output/triggers_febapr_ote.csv --ote \
        --merge output/triggers_febapr_ote_checkpoint.csv
"""
import argparse
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

NY = "America/New_York"
DATA = Path("data/reference/nq_1m_feb_jul2026.parquet")
WORKERS = 4

_df = None
_OTE = False


def _init(ote: bool):
    """Per-worker setup: optionally force the pass-22 OTE flag ON (both binding modules)
    and load the dataset once per process."""
    global _df
    if ote:
        import src.engine.snapshot as _snap
        import src.engine.triggers as _trg
        _snap._include_ote = lambda: True
        _trg._include_ote = lambda: True
    _df = pd.read_parquet(DATA)


def _one_day(task):
    day, daydir = task
    from src.engine.triggers import detect_triggers
    start = pd.Timestamp(f"{day} 07:45", tz=NY)
    end = pd.Timestamp(f"{day} 11:00", tz=NY)
    out = Path(daydir) / f"{day}.csv"
    if _df[(_df["ts_event"] >= start) & (_df["ts_event"] <= end)].empty:
        out.write_text("")                       # holiday / missing session marker
        return day, 0
    trigs = detect_triggers(_df, start=start, end=end)
    pd.DataFrame([t.model_dump() for t in trigs]).to_csv(out, index=False)
    return day, len(trigs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ote", action="store_true", help="force OTE fib cluster levels ON")
    ap.add_argument("--merge", default=None, help="extra csv (e.g. legacy checkpoint) to merge")
    a = ap.parse_args()

    final = Path(a.out)
    daydir = final.parent / (final.stem + "_days")
    daydir.mkdir(parents=True, exist_ok=True)
    done: set[str] = {p.stem for p in daydir.glob("*.csv")}
    if a.merge and Path(a.merge).exists():
        prev = pd.read_csv(a.merge)
        done |= set(pd.to_datetime(prev["ts"], utc=True).dt.tz_convert(NY)
                    .dt.strftime("%Y-%m-%d"))
    days = [f"{d:%Y-%m-%d}" for d in pd.date_range(a.start, a.end, freq="D")
            if d.weekday() < 5 and f"{d:%Y-%m-%d}" not in done]
    print(f"{len(days)} days pending across {WORKERS} workers (ote={a.ote})", flush=True)

    with ProcessPoolExecutor(max_workers=WORKERS, initializer=_init,
                             initargs=(a.ote,)) as ex:
        for day, n in ex.map(_one_day, [(d, str(daydir)) for d in days]):
            print(f"  {day}: {n} triggers", flush=True)

    parts = [pd.read_csv(a.merge)] if a.merge and Path(a.merge).exists() else []
    parts += [pd.read_csv(p) for p in sorted(daydir.glob("*.csv")) if p.stat().st_size > 0]
    out = (pd.concat(parts).drop_duplicates(subset=["ts", "tf"])
           .sort_values("ts").reset_index(drop=True))
    out.to_csv(final, index=False)
    print(f"wrote {final} ({len(out)} triggers)", flush=True)


if __name__ == "__main__":
    main()
