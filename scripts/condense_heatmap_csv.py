#!/usr/bin/env python3
"""Reshape the wide-format MBP-10 book snapshots (trackd-co-app condensed_GLBX-*.csv: one
per-minute row carrying 10 bid + 10 ask levels as columns) into the LONG per-minute depth
format the engine/scripts read: data/reference/depth_2026/nq_depth_YYYY-MM-DD_ny.csv with
columns ts (tz-aware America/New_York), side (bid|ask), price (0.25 tick), size. Prices are
1e-9 fixed-int; ts_event is UTC -> NY. Window as provided (08:00-10:29 ET).

    python scripts/condense_heatmap_csv.py <src_dir> <out_dir>
"""
import glob
import sys
from pathlib import Path

import pandas as pd

NY = "America/New_York"
LEVELS = range(10)


def condense_file(path):
    d = pd.read_csv(path)
    d["ts"] = pd.to_datetime(d.ts_event, utc=True).dt.tz_convert(NY)
    d["minute"] = d.ts.dt.floor("1min")
    d = d.sort_values("ts").groupby("minute", as_index=False).last()  # last book state per minute
    frames = []
    for i in LEVELS:
        for side in ("bid", "ask"):
            pxc, szc = f"{side}_px_0{i}", f"{side}_sz_0{i}"
            if pxc in d.columns and szc in d.columns:
                sub = d[["minute", pxc, szc]].rename(columns={pxc: "price", szc: "size"})
                sub["side"] = side
                frames.append(sub)
    out = pd.concat(frames, ignore_index=True).dropna(subset=["price", "size"])
    out = out[(out["size"] > 0) & (out["price"] > 0)].copy()
    out["price"] = (out["price"] / 1e9).round(2)
    out["size"] = out["size"].astype(int)
    out = out.rename(columns={"minute": "ts"})[["ts", "side", "price", "size"]]
    return out.sort_values(["ts", "side", "price"]).reset_index(drop=True)


def main():
    src, outdir = sys.argv[1], Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    files = sorted(glob.glob(f"{src}/condensed_GLBX-*.csv") + glob.glob(f"{src}/condensed_glbx-*.csv"))
    print(f"condensing {len(files)} files -> {outdir}", flush=True)
    n = 0
    for f in files:
        out = condense_file(f)
        if not len(out):
            continue
        day = out.ts.iloc[0].strftime("%Y-%m-%d")
        out.to_csv(outdir / f"nq_depth_{day}_ny.csv", index=False)
        n += 1
    print(f"wrote {n} daily depth files")


if __name__ == "__main__":
    main()
