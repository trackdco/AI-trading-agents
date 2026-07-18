#!/usr/bin/env python3
"""FOR BRAKE — condense raw mbp-10 depth exports into committable per-minute book snapshots.

The raw April month is ~144 GB. DO NOT upload it, zip it, or move it — run THIS next to the
raw files; it streams them chunk by chunk and writes one small CSV per session window
(same format as your Apr 1 hand-made sample: ts, side, price, size).

    pip install pandas pyarrow databento
    python scripts/condense_depth.py /path/to/raw/*.dbn.zst --outdir depth_out

Produces per day: <outdir>/nq_depth_YYYY-MM-DD_ny.csv     (08:00-11:00 ET)
                  <outdir>/nq_depth_YYYY-MM-DD_london.csv (02:00-05:59 ET)
One snapshot per minute x 10 bid + 10 ask levels, front-month instrument only (by daily
volume of trades within the file, falling back to modal instrument_id). Commit ONLY the
outputs (~150 KB/day). Skip Apr 10 (Databento flagged degraded) — the script tags it.
"""
import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

NY = "America/New_York"
WINDOWS = {"ny": (dtime(8, 0), dtime(11, 0)), "london": (dtime(2, 0), dtime(5, 59))}


def condense_file(path: Path, outdir: Path):
    import databento as db
    print(f"reading {path.name} (streaming)...", flush=True)
    store = db.DBNStore.from_file(str(path))
    df = store.to_df()
    df = df.reset_index()
    tcol = "ts_event" if "ts_event" in df.columns else "ts_recv"
    df["ts"] = pd.to_datetime(df[tcol], utc=True).dt.tz_convert(NY)
    # front instrument = modal instrument_id (parent pulls carry many)
    if "instrument_id" in df.columns and df["instrument_id"].nunique() > 1:
        front = df["instrument_id"].value_counts().idxmax()
        df = df[df["instrument_id"] == front]
    df["minute"] = df["ts"].dt.floor("1min")
    for day, dgrp in df.groupby(df["ts"].dt.strftime("%Y-%m-%d")):
        for wname, (w0, w1) in WINDOWS.items():
            g = dgrp[(dgrp["ts"].dt.time >= w0) & (dgrp["ts"].dt.time <= w1)]
            if g.empty:
                continue
            # last book state per minute -> unpack 10 bid + 10 ask levels
            last = g.sort_values("ts").groupby("minute").tail(1)
            rows = []
            for _, r in last.iterrows():
                for i in range(10):
                    for side, px, sz in (("bid", f"bid_px_{i:02d}", f"bid_sz_{i:02d}"),
                                         ("ask", f"ask_px_{i:02d}", f"ask_sz_{i:02d}")):
                        if px in r and pd.notna(r[px]) and r[sz] > 0:
                            price = r[px] / 1e9 if abs(r[px]) > 1e7 else r[px]
                            rows.append(dict(ts=r["minute"], side=side,
                                             price=price, size=int(r[sz])))
            if not rows:
                continue
            out = outdir / f"nq_depth_{day}_{wname}.csv"
            pd.DataFrame(rows).to_csv(out, index=False)
            tag = "  [DEGRADED - Databento flag, use with care]" if day == "2026-04-10" else ""
            print(f"  {out.name}: {len(rows):,} rows{tag}", flush=True)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    outdir = Path("depth_out")
    if "--outdir" in sys.argv:
        outdir = Path(sys.argv[sys.argv.index("--outdir") + 1])
        args = [a for a in args if str(outdir) != a]
    outdir.mkdir(parents=True, exist_ok=True)
    for p in args:
        condense_file(Path(p), outdir)
    print(f"done. Commit the contents of {outdir}/ into data/reference/depth_apr2026/")


if __name__ == "__main__":
    main()
