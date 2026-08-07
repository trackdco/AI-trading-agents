#!/usr/bin/env python3
"""Stage-8 detector gate: streamed per-bar detection must reproduce the frozen caches.

Streams real sessions one closed 1m bar at a time (the live loop's view), runs
LiveDetector per bar over the accumulated history (16-day warmup like parity_check),
and diffs the UNION of detections against the frozen trigger caches for those days on
every decision-relevant field. Any difference fails the gate.

    python -m scripts.detector_parity --start 2026-03-16 --end 2026-03-18
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.live.detector import LiveDetector  # noqa: E402
from src.live.feed import ReplayFeed  # noqa: E402
from scripts.parity_check import PARQUET, load_triggers  # noqa: E402

NY = "America/New_York"

# fields that drive engine decisions (identity + prices + classification)
FIELDS = ["ts", "tf", "direction", "kind", "pattern", "htf_flag", "entry_ref",
          "stop_ref", "wick_low", "wick_high", "cluster_center", "confluence_count",
          "vwap_touched", "close"]


def sig(t) -> tuple:
    return tuple(getattr(t, f) for f in FIELDS)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", default="2026-03-16")
    ap.add_argument("--end", default="2026-03-18")
    args = ap.parse_args(argv)

    df = pd.read_parquet(PARQUET)
    lo = pd.Timestamp(args.start, tz=NY)
    hi = pd.Timestamp(args.end, tz=NY) + pd.Timedelta(days=1)
    cache = load_triggers(lo, hi)

    det = LiveDetector()
    feed = ReplayFeed(df, start=args.start, end=args.end, warmup_days=16)
    bars: list[dict] = []
    streamed: dict[tuple, object] = {}
    n_window = 0
    for bar in feed.stream():
        bars.append({c: getattr(bar, c) for c in
                     ("ts_event", "open", "high", "low", "close", "volume")})
        ts = pd.Timestamp(bar.ts_event)
        if not (args.start <= ts.strftime("%Y-%m-%d") <= args.end):
            continue                                   # warmup days feed history only
        if not det.wants(ts):
            continue
        n_window += 1
        frame = pd.DataFrame(bars)
        for t in det.on_bar(frame, bar):
            streamed.setdefault(sig(t), t)

    cache_sigs = {sig(t) for t in cache}
    stream_sigs = set(streamed)
    missing = sorted(cache_sigs - stream_sigs)
    extra = sorted(stream_sigs - cache_sigs)
    print(f"detector parity {args.start}..{args.end}: cache {len(cache_sigs)}, "
          f"streamed {len(stream_sigs)} ({det.calls} detect calls over "
          f"{n_window} in-band bars)")
    for m in missing:
        print(f"  MISSING from stream: {m[:5]}")
    for e in extra:
        print(f"  EXTRA in stream:     {e[:5]}")
    ok = not missing and not extra
    print(f"\nDETECTOR: {'MATCH — gate PASSED' if ok else 'MISMATCH — gate FAILED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
