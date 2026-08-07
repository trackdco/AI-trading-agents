#!/usr/bin/env python3
"""FOR BRAKE — condense raw Databento `trades` ticks into the committable footprint parquet.

DO NOT upload the raw export to GitHub (100 MB file cap; 18 GB will never fit and we don't
need it). Run THIS locally next to the raw file(s); commit ONLY the output parquet.

    pip install pandas pyarrow            # (+ `pip install databento` if you have .dbn files)
    python scripts/condense_trades.py /path/to/raw_trades.csv output/footprint_apr2026.parquet

Accepts .csv/.csv.gz/.csv.zst (Databento trades CSV) or .dbn/.dbn.zst (needs databento pkg).
Multiple inputs allowed: pass each raw file, then the output path LAST.

Output: one row per (1-minute bar x price level x aggressor side):
    ts_minute (UTC), price, side ('B' buyer-aggressor / 'A' seller-aggressor),
    volume (contracts), trades (tick count)
~50-100x smaller than raw ticks. The engine derives footprints, delta, absorption grading,
and level memory from this file alone.
"""
import sys
from pathlib import Path

import pandas as pd

CHUNK = 5_000_000


def _frames(path: Path):
    if ".dbn" in path.suffixes or path.suffix == ".dbn":
        import databento as db
        store = db.DBNStore.from_file(str(path))
        df = store.to_df()
        df = df.reset_index()
        tscol = "ts_event" if "ts_event" in df.columns else "ts_recv"
        yield df[[tscol, "price", "size", "side"]].rename(columns={tscol: "ts"})
        return
    for chunk in pd.read_csv(path, chunksize=CHUNK):
        tscol = "ts_event" if "ts_event" in chunk.columns else "ts_recv"
        df = chunk[[tscol, "price", "size", "side"]].rename(columns={tscol: "ts"})
        yield df


def condense(inputs: list[Path], out: Path):
    parts = []
    for path in inputs:
        print(f"reading {path} ...", flush=True)
        for df in _frames(path):
            df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
            df = df.dropna(subset=["ts"])
            # Databento prices may be fixed-point 1e-9 ints; detect and rescale
            if df["price"].dtype.kind in "iu" and df["price"].abs().max() > 1e7:
                df["price"] = df["price"] / 1e9
            df = df[df["side"].isin(["A", "B"])]          # keep aggressor-tagged ticks only
            g = (df.assign(ts_minute=df["ts"].dt.floor("1min"))
                   .groupby(["ts_minute", "price", "side"], observed=True)
                   .agg(volume=("size", "sum"), trades=("size", "count"))
                   .reset_index())
            parts.append(g)
            print(f"  +{len(g):,} footprint rows", flush=True)
    full = (pd.concat(parts)
              .groupby(["ts_minute", "price", "side"], observed=True)
              .sum().reset_index()
              .sort_values(["ts_minute", "price"]))
    out.parent.mkdir(parents=True, exist_ok=True)
    full.to_parquet(out, index=False)
    mb = out.stat().st_size / 1e6
    print(f"wrote {out}: {len(full):,} rows, {mb:.0f} MB "
          f"({full.ts_minute.min()} -> {full.ts_minute.max()})", flush=True)
    if mb > 95:
        print("WARNING: >95 MB — split by month (one output per month) before committing.",
              flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    condense([Path(p) for p in sys.argv[1:-1]], Path(sys.argv[-1]))
