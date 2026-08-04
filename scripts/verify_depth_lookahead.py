#!/usr/bin/env python3
"""VERIFY the depth-snapshot look-ahead defect. Read-only. Changes nothing.

CLAIM UNDER TEST
    Condensed depth snapshots are stamped with the START of the minute but contain the
    book state from the END of that minute. Anything that reads "the book at minute t"
    and acts at or during minute t therefore sees up to ~59 seconds of the future.

WHERE IT COMES FROM
    scripts/condense_depth.py:39   df["minute"] = df["ts"].dt.floor("1min")
    scripts/condense_depth.py:46   last = g.sort_values("ts").groupby("minute").tail(1)
    scripts/condense_depth.py:54   rows.append(dict(ts=r["minute"], ...))

    tail(1) takes the LAST book message of the minute; the row is then stamped with the
    FLOORED minute. src/canon/features.py::depth_at then selects `dep.ts <= minute`,
    which is correct semantics applied to a mislabelled timestamp.

    depth_at IS NOT THE BUG. The data is mislabelled underneath it.

TWO INDEPENDENT TESTS
    1. Raw offset — only possible where ts_recv survived the condense (depth_london).
       If the snapshot is end-of-minute, ts_recv - ts_event ~ 59s.
    2. Mid-vs-bar — works on any condensed file, including those where provenance was
       stripped. A true start-of-minute snapshot tracks the bar's OPEN. An end-of-minute
       snapshot tracks its CLOSE.

Test 2 is the decisive one and is the only test available for the NY canon files.

    python -m scripts.verify_depth_lookahead
"""
from __future__ import annotations

import glob
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NY = "America/New_York"
TICK = 0.25
SAMPLE = 60


def bars() -> pd.DataFrame:
    b = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    b = b.assign(ts=pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY))
    return b.set_index("ts")[["open", "close"]]


def test_raw_offset(pattern: str) -> None:
    fs = sorted(glob.glob(str(ROOT / pattern)))[:SAMPLE]
    if not fs:
        print("  (no files)")
        return
    try:
        d = pd.concat([pd.read_csv(f, usecols=["ts_event", "ts_recv"]) for f in fs],
                      ignore_index=True)
    except ValueError:
        print("  ts_recv not present — provenance stripped, test 1 unavailable")
        return
    off = (pd.to_datetime(d.ts_recv, utc=True)
           - pd.to_datetime(d.ts_event, utc=True)).dt.total_seconds()
    print(f"  ts_recv - ts_event: median {off.median():.2f}s  "
          f"p10 {off.quantile(.1):.2f}s  p90 {off.quantile(.9):.2f}s")
    print(f"  rows more than 30s into the labelled minute: {100 * (off > 30).mean():.1f}%")


def mid_series(pattern: str) -> pd.Series:
    """Top-of-book mid per snapshot minute, for either condensed layout."""
    fs = sorted(glob.glob(str(ROOT / pattern)))[:SAMPLE]
    if not fs:
        return pd.Series(dtype=float)
    head = pd.read_csv(fs[0], nrows=1)
    if "bid_px_00" in head.columns:                       # wide MBP-10 layout
        d = pd.concat([pd.read_csv(f, usecols=["ts_event", "bid_px_00", "ask_px_00"])
                       for f in fs], ignore_index=True)
        ts = pd.to_datetime(d.ts_event, utc=True).dt.tz_convert(NY)
        return pd.Series(((d.bid_px_00 + d.ask_px_00) / 2).to_numpy(), index=ts)
    # long layout: ts, side, price, size
    d = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
    d["ts"] = pd.to_datetime(d.ts, utc=True).dt.tz_convert(NY)
    bid = d[d.side == "bid"].groupby("ts").price.max()
    ask = d[d.side == "ask"].groupby("ts").price.min()
    return ((bid + ask) / 2).dropna()


def test_mid_vs_bar(pattern: str, b: pd.DataFrame) -> None:
    mid = mid_series(pattern)
    if mid.empty:
        print("  (no files)")
        return
    j = pd.DataFrame({"mid": mid}).join(b, how="inner").dropna()
    if j.empty:
        print("  (no overlap with 1m master bars)")
        return
    eo = ((j["mid"] - j["open"]).abs() / TICK).median()
    ec = ((j["mid"] - j["close"]).abs() / TICK).median()
    print(f"  joined minutes: {len(j):,}")
    print(f"  |mid - bar OPEN |  median {eo:6.2f} ticks   <- start-of-minute would win here")
    print(f"  |mid - bar CLOSE|  median {ec:6.2f} ticks   <- end-of-minute wins here")
    verdict = ("END-OF-MINUTE STATE — look-ahead confirmed" if ec < eo
               else "consistent with start-of-minute state")
    print(f"  -> {verdict}  (open/close error ratio {eo / max(ec, 1e-9):.1f}x)")


def main() -> None:
    b = bars()
    for label, pattern in (
        ("LONDON depth  (data/reference/depth_london)",
         "data/reference/depth_london/*.csv"),
        ("NY CANON depth (data/reference/depth_2025)",
         "data/reference/depth_2025/*.csv"),
    ):
        print("=" * 78)
        print(label)
        print("=" * 78)
        print(" TEST 1 — raw receive-time offset")
        test_raw_offset(pattern)
        print(" TEST 2 — snapshot mid vs bar open/close (decisive)")
        test_mid_vs_bar(pattern, b)
        print()

    print("=" * 78)
    print("SCOPE — this is a BACKTEST/CALIBRATION bias, not a live execution bug.")
    print("=" * 78)
    print("A live feed delivers the book as it actually is; there is no future in it.")
    print("The defect is that every historical depth feature was measured, and every")
    print("threshold calibrated, on snapshots carrying ~59s of foresight. Features that")
    print("looked informative in replay have less to work with live.")
    print()
    print("src/canon/features.py:68 states the live ingestor MUST call depth_at so that")
    print("live and backtest cannot drift. The function is shared, so the intent holds —")
    print("but replay feeds it mislabelled snapshots while live feeds it true state, so")
    print("they drift anyway, through the data rather than the code.")


if __name__ == "__main__":
    main()
