#!/usr/bin/env python3
"""Depth-wall extractor — per-minute MBP-10 book metrics for wall-at-entry reads.

Consumes the extracted depth archive (data/depth/, both file families) and
writes one row per snapshot minute: total and max resting size per side, the
wall ratio (max level vs the side's median level), the wall's distance from
best, and the book imbalance. HONORS THE PRIOR FINDING (canon program,
commit 2a9c221): MBP-10 sees ~±5 NQ points around price, so these metrics
are valid ONLY as at-price reads at entry time — never as distant-level
structure. Prices decode from fixed-point 1e-9.

Wall definitions (frozen; thresholds are declared per-prereg, not here):
  side_total   sum of the 10 visible level sizes
  side_max     largest single level size
  wall_ratio   side_max / median(level sizes) — canon-WALLSZ-style
  wall_dist    points from best price to the max level
  imb          bid_total / (bid_total + ask_total)

    python -m scripts.depth_walls   # writes output/depth_minutes.parquet
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SRC = ROOT / "data/depth"


def main() -> None:
    frames = []
    for f in sorted(SRC.glob("*.csv")):
        try:
            df = pd.read_csv(f)
        except Exception:
            continue
        if "bid_px_00" not in df.columns:
            continue
        ts = pd.to_datetime(df["ts_event"], utc=True, errors="coerce")
        bpx = df[[f"bid_px_0{i}" for i in range(10)]].to_numpy(float) * 1e-9
        apx = df[[f"ask_px_0{i}" for i in range(10)]].to_numpy(float) * 1e-9
        bsz = df[[f"bid_sz_0{i}" for i in range(10)]].to_numpy(float)
        asz = df[[f"ask_sz_0{i}" for i in range(10)]].to_numpy(float)
        with np.errstate(invalid="ignore"):
            b_med = np.nanmedian(np.where(bsz > 0, bsz, np.nan), axis=1)
            a_med = np.nanmedian(np.where(asz > 0, asz, np.nan), axis=1)
        bi, ai = np.nanargmax(bsz, axis=1), np.nanargmax(asz, axis=1)
        rows = pd.DataFrame({
            "mi": ts.dt.tz_convert("America/New_York").dt.floor("min"),
            "best_bid": bpx[:, 0], "best_ask": apx[:, 0],
            "bid_total": bsz.sum(1), "ask_total": asz.sum(1),
            "bid_max": bsz.max(1), "ask_max": asz.max(1),
            "bid_wall_ratio": bsz.max(1) / np.clip(b_med, 1, None),
            "ask_wall_ratio": asz.max(1) / np.clip(a_med, 1, None),
            "bid_wall_dist": bpx[:, 0] - bpx[np.arange(len(df)), bi],
            "ask_wall_dist": apx[np.arange(len(df)), ai] - apx[:, 0],
        })
        rows["imb"] = rows.bid_total / (rows.bid_total + rows.ask_total).clip(lower=1)
        frames.append(rows)
    D = pd.concat(frames, ignore_index=True).dropna(subset=["mi"])
    D = D.sort_values("mi").drop_duplicates("mi", keep="last").set_index("mi")
    D.to_parquet(ROOT / "output/depth_minutes.parquet")
    days = pd.Series(D.index.date).nunique()
    ny = D.between_time("08:00", "10:29")
    print(f"{len(D)} snapshot minutes, {days} days | NY-morning minutes {len(ny)} "
          f"({pd.Series(ny.index.date).nunique()} days)")
    print(f"wall_ratio medians bid {D.bid_wall_ratio.median():.1f} ask {D.ask_wall_ratio.median():.1f} | "
          f"p90 bid {D.bid_wall_ratio.quantile(.9):.1f}")


if __name__ == "__main__":
    main()
