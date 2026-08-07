#!/usr/bin/env python3
"""CAPTURE STEP for the depth parity gate — Sierra `.depth` -> `depth_parity` JSONL.

`docs/HANDOVER-pat-arming.md` §4.1 requires one real captured session normalised to the
JSONL schema `scripts/depth_parity.py::read_events` consumes; its docstring says that
normalisation "is the capture step's job". This is that step for the box's native format:
Sierra's per-level `.depth` file (the SAME file the live `SierraFileFeed` tails), decoded by
the SAME pinned reader (`DepthReader` — the Command enum and record layout were pinned on
Pat's VPS 2026-07-26), scaled by the SAME evidence rule the feed uses (median depth price vs
a same-day `.scid` trade must sit within 5% of a power of ten, else refuse — the box writes
`.scid` in points but `.depth` 100x).

The parity harness rebuilds a FRESH book from each minute's event group, so the capture must
emit per-minute SNAPSHOTS, not raw increments: the full event stream is folded through
`DepthBook` (the production book) and, for every minute in the archive's NY window, the
book's own `long_form()` — MBP-10, exactly what `feature_row` reads live — is written as one
`R` + level-set group stamped at that minute. Snapshot convention matches the archive
builder (`condense_depth.py`): last book state within the minute, stamped at the minute;
event-less minutes carry the standing book forward.

    # on the box, against a day that ALSO exists in data/reference/depth_*/
    python -m scripts.depth_capture --scid NQU6.CME.scid --depth NQU6.CME.2026-07-08.depth \
        --day 2026-07-08 --out capture_2026-07-08.jsonl
    python -m scripts.depth_parity --day 2026-07-08 --events capture_2026-07-08.jsonl --book depth

Use `--book depth` on the parity run: Sierra's `.depth` is per-price-level (MBP), not MBO.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterator

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.canon.book import DepthBook                                # noqa: E402
from src.canon.sierra_files import DepthEvent, DepthReader, ScidReader  # noqa: E402

NY = "America/New_York"
BAND = ("08:00", "11:00")            # the archive's NY window (condense_depth.py)
SCALE_CANDIDATES = (0.01, 0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0)
_SCALE_SAMPLE = 500                  # depth prices buffered before deciding the scale


def trade_reference(scid: Path, day_end: pd.Timestamp) -> float | None:
    """Last trade close at or before the capture day's end — the price the depth scale is
    judged against. Stops reading at the first record past `day_end` (records are
    chronological), so a multi-week `.scid` is not scanned past the day it needs."""
    ref = None
    for rec in ScidReader(scid).records():
        if rec.ts > day_end:
            break
        if rec.close > 0:
            ref = float(rec.close)
    return ref


def detect_scale(prices: list[float], trade_px: float) -> float:
    """The feed's own rule (`SierraFileFeed._detect_depth_scale`), standalone: median depth
    price over the trade price must land within 5% of a power of ten — else refuse. Scoring
    on mis-scaled depth is the silent-poison case; never guess."""
    px = sorted(p for p in prices if p > 0)
    if not px or trade_px <= 0:
        raise SystemExit("no usable prices to detect the depth scale — is the .scid empty?")
    ratio = px[len(px) // 2] / trade_px
    for s in SCALE_CANDIDATES:
        if abs(ratio / s - 1.0) <= 0.05:
            return s
    raise SystemExit(f".depth/.scid price ratio {ratio:.6g} is not a power of ten — refusing "
                     f"to guess a divisor (depth px {px[len(px) // 2]:.6g} vs trade px "
                     f"{trade_px:.6g})")


def scaled_events(depth: Path, trade_px: float | None,
                  scale: float | None) -> Iterator[DepthEvent]:
    """The `.depth` stream with prices already divided by the (detected or given) scale.
    Detection buffers the first _SCALE_SAMPLE events, decides once, then replays them in
    order — downstream sees one clean chronological stream either way."""
    buf: list[DepthEvent] = []

    def rescaled(de: DepthEvent, s: float) -> DepthEvent:
        return DepthEvent(de.ts, de.action, de.price / s, de.size, de.ct)

    for de in DepthReader(depth).records():
        if scale is None:
            buf.append(de)
            if len(buf) < _SCALE_SAMPLE:
                continue
            scale = detect_scale([b.price for b in buf if b.action in "BAba"], trade_px)
            print(f"depth price scale detected: {scale:g}", flush=True)
            for b in buf:
                yield rescaled(b, scale)
            buf.clear()
            continue
        yield rescaled(de, scale)
    if scale is None and buf:            # short file: decide on what there is
        scale = detect_scale([b.price for b in buf if b.action in "BAba"], trade_px)
        print(f"depth price scale detected: {scale:g}", flush=True)
        for b in buf:
            yield rescaled(b, scale)


def snapshot_lines(book: DepthBook, minute: pd.Timestamp) -> list[str]:
    """One minute's group in read_events' `--book depth` schema: clear, then every level of
    the book's own MBP-10 view — the exact rows the live feature path consumes."""
    ts = minute.isoformat()
    lines = [json.dumps({"ts": ts, "action": "R", "price": 0.0, "size": 0, "ct": 0})]
    for r in book.long_form():
        lines.append(json.dumps({"ts": ts, "action": "B" if r["side"] == "bid" else "A",
                                 "price": r["price"], "size": r["size"], "ct": r["ct"]}))
    return lines


def capture(depth: Path, scid: Path, day: str, out: Path,
            scale: float | None = None, band: tuple[str, str] = BAND) -> int:
    lo = pd.Timestamp(f"{day} {band[0]}", tz=NY)
    hi = pd.Timestamp(f"{day} {band[1]}", tz=NY)
    trade_px = None
    if scale is None:
        trade_px = trade_reference(scid, hi.tz_convert("UTC"))
        if trade_px is None:
            raise SystemExit(f"no trade at or before {day} {band[1]} in {scid} — cannot "
                             "detect the depth price scale (or pass --scale explicitly)")

    book = DepthBook()
    events = n_lines = n_minutes = 0
    cur_min: pd.Timestamp | None = None

    with out.open("w") as f:

        def emit(upto: pd.Timestamp) -> None:
            """Band minutes cur_min..upto get the CURRENT book — the state at cur_min's
            close, unchanged across the event-less minutes between them."""
            nonlocal n_lines, n_minutes
            m = max(cur_min, lo)
            while m <= min(upto, hi):
                for line in snapshot_lines(book, m):
                    f.write(line + "\n")
                    n_lines += 1
                n_minutes += 1
                m += pd.Timedelta(minutes=1)

        for de in scaled_events(depth, trade_px, scale):
            m = de.ts.tz_convert(NY).floor("1min")
            if cur_min is None:
                cur_min = m
            elif m > cur_min:
                emit(m - pd.Timedelta(minutes=1))
                cur_min = m
                if cur_min > hi:
                    break                # past the band — nothing further can be emitted
            book.apply({"action": de.action, "price": de.price,
                        "size": de.size, "ct": de.ct})
            events += 1
            if events % 5_000_000 == 0:
                print(f"  ... {events / 1e6:.0f}M events, at {m}", flush=True)
        else:
            if cur_min is not None:      # stream ended inside the band: close the last minute
                emit(cur_min)

    bb, ba = book.best_bid(), book.best_ask()
    print(f"\nwrote {out} — {n_minutes} minute snapshots ({n_lines} lines) from {events:,} "
          f"depth events | band {day} {band[0]}-{band[1]} ET")
    if bb and ba:
        print(f"final book: best bid/ask {bb:.2f}/{ba:.2f} (sanity: should look like NQ)")
    print(f"\nnext:\n  python -m scripts.depth_parity --day {day} --events {out} --book depth")
    if n_minutes == 0:
        raise SystemExit("no snapshots emitted — is --day right for this .depth file?")
    return n_minutes


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--depth", type=Path, required=True, help="Sierra .depth file for the day")
    ap.add_argument("--scid", type=Path, required=True,
                    help=".scid for the same contract (trade-price reference for the scale)")
    ap.add_argument("--day", required=True, help="session date, YYYY-MM-DD (NY)")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--scale", type=float, default=None,
                    help="override the depth price divisor (skips detection — use only if "
                         "detection refuses and you KNOW the ratio)")
    a = ap.parse_args()
    out = a.out or Path(f"capture_{a.day}.jsonl")
    capture(a.depth, a.scid, a.day, out, scale=a.scale)


if __name__ == "__main__":
    main()
