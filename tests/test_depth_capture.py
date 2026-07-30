"""The capture step (Sierra .depth -> depth_parity JSONL) round-trips the box's format.

Verified end-to-end on 2026-04-20 (180 archive minutes synthesized to a 100x-scaled .depth
with the full command enum, captured, then run through scripts.depth_parity): 100% gate
agreement, every feature delta 0.0000. These tests pin the pieces of that chain that can
regress silently: scale detection/refusal, snapshot-per-minute semantics (fresh-book
reconstruction from each JSONL group), modify/delete folding, and carry-forward across
event-less minutes.
"""
import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.depth_capture import capture, detect_scale
from src.canon.book import DepthBook
from src.canon.sierra_files import (
    DCMD_ADD_ASK, DCMD_ADD_BID, DCMD_CLEAR, DCMD_DEL_BID, DCMD_MOD_ASK,
    write_depth, write_scid,
)

NY = "America/New_York"
DAY = "2026-04-20"


def _ts(hms: str) -> pd.Timestamp:
    return pd.Timestamp(f"{DAY} {hms}", tz=NY)


@pytest.fixture()
def synth(tmp_path: Path) -> dict:
    """Three active minutes + one event-less gap minute, depth prices 100x the .scid."""
    scale = 100.0
    scid = tmp_path / "SYNTH.CME.scid"
    depth = tmp_path / f"SYNTH.CME.{DAY}.depth"
    write_scid(scid, [{"ts": _ts("07:50:00"), "close": 20000.0, "total_volume": 3}])
    recs = [
        # 08:00 — clear, two bids, two asks
        {"ts": _ts("08:00:05"), "command": DCMD_CLEAR},
        {"ts": _ts("08:00:05"), "command": DCMD_ADD_BID, "price": 19999.0 * scale, "qty": 5},
        {"ts": _ts("08:00:05"), "command": DCMD_ADD_BID, "price": 19998.0 * scale, "qty": 8},
        {"ts": _ts("08:00:05"), "command": DCMD_ADD_ASK, "price": 20001.0 * scale, "qty": 4},
        {"ts": _ts("08:00:05"), "command": DCMD_ADD_ASK, "price": 20002.0 * scale, "qty": 9},
        # 08:01 — modify an ask, delete a bid: last-state-in-minute is what must land
        {"ts": _ts("08:01:20"), "command": DCMD_MOD_ASK, "price": 20001.0 * scale, "qty": 7},
        {"ts": _ts("08:01:40"), "command": DCMD_DEL_BID, "price": 19998.0 * scale},
        # 08:02 — silent (no events): the 08:01 state must carry forward
        # 08:03 — one more bid
        {"ts": _ts("08:03:10"), "command": DCMD_ADD_BID, "price": 19997.5 * scale, "qty": 2},
    ]
    write_depth(depth, recs)
    return {"scid": scid, "depth": depth, "out": tmp_path / "cap.jsonl"}


def _books_from_jsonl(path: Path) -> dict[str, list[dict]]:
    """Reconstruct a fresh book per minute group exactly as depth_parity.read_events +
    its per-minute loop do, and return each minute's long_form."""
    by_min: dict[str, list[dict]] = {}
    for line in path.read_text().splitlines():
        e = json.loads(line)
        by_min.setdefault(e.pop("ts"), []).append(e)
    out = {}
    for ts, evs in by_min.items():
        b = DepthBook()
        for e in evs:
            b.apply(e)
        out[ts] = b.long_form()
    return out


def test_roundtrip_snapshots(synth):
    n = capture(synth["depth"], synth["scid"], DAY, synth["out"])
    books = _books_from_jsonl(synth["out"])
    assert n == 4 and len(books) == 4

    m0 = books[_ts("08:00:00").isoformat()]
    assert {(r["side"], r["price"], r["size"]) for r in m0} == {
        ("bid", 19999.0, 5), ("bid", 19998.0, 8), ("ask", 20001.0, 4), ("ask", 20002.0, 9)}

    # 08:01: the modify landed (ask 20001 -> 7) and the deleted bid is GONE
    m1 = books[_ts("08:01:00").isoformat()]
    assert {(r["side"], r["price"], r["size"]) for r in m1} == {
        ("bid", 19999.0, 5), ("ask", 20001.0, 7), ("ask", 20002.0, 9)}

    # 08:02 had no events: byte-identical carry-forward of the 08:01 state
    assert books[_ts("08:02:00").isoformat()] == m1

    m3 = books[_ts("08:03:00").isoformat()]
    assert ("bid", 19997.5, 2) in {(r["side"], r["price"], r["size"]) for r in m3}


def test_scale_detected_and_prices_in_points(synth):
    capture(synth["depth"], synth["scid"], DAY, synth["out"])
    prices = [json.loads(x)["price"] for x in synth["out"].read_text().splitlines()
              if json.loads(x)["action"] != "R"]
    assert prices and all(19000 < p < 21000 for p in prices)   # points, not the 100x raw


def test_scale_refusal_is_loud():
    with pytest.raises(SystemExit, match="not a power of ten"):
        detect_scale([20000.0 * 3.0] * 10, 20000.0)


def test_unscaled_depth_passes_through(tmp_path):
    """A box whose .depth is already in points must detect scale 1 and change nothing."""
    scid = tmp_path / "S.scid"
    depth = tmp_path / f"S.{DAY}.depth"
    write_scid(scid, [{"ts": _ts("07:50:00"), "close": 20000.0, "total_volume": 1}])
    write_depth(depth, [
        {"ts": _ts("08:00:05"), "command": DCMD_CLEAR},
        {"ts": _ts("08:00:05"), "command": DCMD_ADD_BID, "price": 19999.0, "qty": 5},
        {"ts": _ts("08:00:05"), "command": DCMD_ADD_ASK, "price": 20001.0, "qty": 4},
    ])
    out = tmp_path / "cap.jsonl"
    capture(depth, scid, DAY, out)
    rows = [json.loads(x) for x in out.read_text().splitlines()]
    assert {(r["action"], r["price"]) for r in rows} == {
        ("R", 0.0), ("B", 19999.0), ("A", 20001.0)}
