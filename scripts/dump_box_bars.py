"""Dump the EXACT bars the live loop's detector saw — R13 practice-day-2 forensics.

Practice day 2 (2026-08-01) placed LONG candidates whose stops sit ABOVE their limit
entries (e.g. B limit 28500.5 stop 28508.25). `detect_triggers` cannot produce that
geometry on well-formed bars (long stop_ref = the candle's own low, always at/below any
penetrated level), and the repo reference days emit 0 wrong-side stops in 173 triggers —
so the suspect is the BOX's bar stream itself (settlement records, aggregator edge,
duplicate/out-of-order records). This script rebuilds the feed exactly like
`scripts.ny_run` (same resolver, same scale anchor) and writes the ingestor's bar frame
for the practice window to a small CSV for offline reproduction.

Run on the box (repo root), then commit the dump:

    python -m scripts.dump_box_bars
    git add data/debug
    git commit -m "R13 forensics - box bars 2026-07-27..08-01"
    git push
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.ny_run import load_config
from src.canon.book import DepthBook
from src.canon.ingestor import CanonIngestor
from src.canon.sierra_files import SierraFileFeed
from src.canon.sierra_symbol import resolve_scid_path

OUT = Path("data/debug/box_bars_2026-07-27_08-01.csv")
LO, HI = "2026-07-27", "2026-08-02"          # UTC day span covering the practice session


def main() -> int:
    cfg = load_config(Path("config/live.yaml"))
    sc = (cfg.get("feed", {}) or {}).get("sierra", {}) or {}
    data_dir = sc["data_dir"]
    now = pd.Timestamp.now(tz="UTC")
    scid = Path(sc["scid"]) if sc.get("scid") else resolve_scid_path(
        data_dir, now, sc.get("root", "NQ"), sc.get("suffix", "-CME"))
    ref_pq = Path(sc.get("reference_parquet", "data/reference/nq_1m_master.parquet"))
    ref_px = float(pd.read_parquet(ref_pq, columns=["close"])["close"].iloc[-1])
    print(f"scid: {scid}\nreference px: {ref_px}")

    feed = SierraFileFeed(scid, None, reference_px=ref_px)
    ing = CanonIngestor(book=DepthBook())
    feed.drive_batch(ing)
    print(f"bar price scale detected: {feed.bar_price_scale}")

    df = ing.bars_frame()
    ts = pd.to_datetime(df["ts_event"], utc=True)
    win = df[(ts >= pd.Timestamp(LO, tz="UTC")) & (ts < pd.Timestamp(HI, tz="UTC"))]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    win.to_csv(OUT, index=False)
    bad = win[(win["low"] > win[["open", "close"]].min(axis=1))
              | (win["high"] < win[["open", "close"]].max(axis=1))]
    print(f"wrote {len(win)} bars -> {OUT}")
    print(f"malformed bars (low>min(o,c) or high<max(o,c)): {len(bad)}")
    if len(bad):
        print(bad.head(10).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
