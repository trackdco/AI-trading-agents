#!/usr/bin/env python3
"""Pass 23 (Angus: "run it more efficiently"): PARALLEL checkpointed OTE detection.

Days are independent, so detection shards across worker processes (one day per task,
~Ncores speedup). Each finished day writes output/ote_days/<day>.csv; resume skips days
present there OR in the sequential run's checkpoint, then everything merges into the
final cache. Kill-safe at any point: re-running redoes at most one in-flight day per
worker.

    python -m scripts._detect_parallel
"""
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

NY = "America/New_York"
DATA = Path("data/reference/nq_1m_feb_jul2026.parquet")
CKPT = Path("output/triggers_febapr_ote_checkpoint.csv")   # sequential run's progress (kept)
DAYDIR = Path("output/ote_days")
FINAL = Path("output/triggers_febapr_ote.csv")
START, END = "2026-02-02", "2026-04-30"
WORKERS = 4

_df = None


def _init():
    """Per-worker setup: force the pass-22 OTE flag ON (both binding modules) and load
    the dataset once per process."""
    global _df
    import src.engine.snapshot as _snap
    import src.engine.triggers as _trg
    _snap._include_ote = lambda: True
    _trg._include_ote = lambda: True
    _df = pd.read_parquet(DATA)


def _one_day(day: str):
    from src.engine.triggers import detect_triggers
    start = pd.Timestamp(f"{day} 07:45", tz=NY)
    end = pd.Timestamp(f"{day} 11:00", tz=NY)
    out = DAYDIR / f"{day}.csv"
    if _df[(_df["ts_event"] >= start) & (_df["ts_event"] <= end)].empty:
        out.write_text("")                       # holiday / missing session marker
        return day, 0
    trigs = detect_triggers(_df, start=start, end=end)
    pd.DataFrame([t.model_dump() for t in trigs]).to_csv(out, index=False)
    return day, len(trigs)


def main():
    DAYDIR.mkdir(parents=True, exist_ok=True)
    done: set[str] = {p.stem for p in DAYDIR.glob("*.csv")}
    if CKPT.exists():
        prev = pd.read_csv(CKPT)
        done |= set(pd.to_datetime(prev["ts"], utc=True).dt.tz_convert(NY)
                    .dt.strftime("%Y-%m-%d"))
    days = [f"{d:%Y-%m-%d}" for d in pd.date_range(START, END, freq="D")
            if d.weekday() < 5 and f"{d:%Y-%m-%d}" not in done]
    print(f"{len(days)} days pending across {WORKERS} workers", flush=True)

    with ProcessPoolExecutor(max_workers=WORKERS, initializer=_init) as ex:
        for day, n in ex.map(_one_day, days):
            print(f"  {day}: {n} triggers", flush=True)

    parts = [pd.read_csv(CKPT)] if CKPT.exists() else []
    parts += [pd.read_csv(p) for p in sorted(DAYDIR.glob("*.csv")) if p.stat().st_size > 0]
    out = (pd.concat(parts).drop_duplicates(subset=["ts", "tf"])
           .sort_values("ts").reset_index(drop=True))
    out.to_csv(FINAL, index=False)
    print(f"wrote {FINAL} ({len(out)} triggers)", flush=True)


if __name__ == "__main__":
    main()
