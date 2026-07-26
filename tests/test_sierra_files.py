"""Route-B file-tail data path tests (src/canon/sierra_files.py, DepthBook).

All offline against SYNTHETIC .scid/.depth written by this module's own writers. These prove
(a) the readers invert the writers, (b) tick->minute aggregation is correct, (c) live-tail
resumption never re-emits or delivers a forming minute, and (d) the headline PARITY claim:
the file-tail path produces byte-identical ingestor feature rows to the trusted ReplaySource.

They do NOT prove the byte layout matches a real Sierra build — that is the PIN-ON-BOX gate
documented in sierra_files.py (arch §2.2/§3), closed only against a captured sample day.
"""
from __future__ import annotations

import math

import pandas as pd

from src.canon.book import DepthBook
from src.canon.ingestor import CanonIngestor, ReplaySource
from src.canon.sierra_files import (
    DCMD_CLEAR,
    DCMD_SET_ASK,
    DCMD_SET_BID,
    DepthReader,
    MinuteAggregator,
    ScidReader,
    SierraFileFeed,
    scdt_to_ts,
    ts_to_scdt,
    write_depth,
    write_scid,
)

NY = "America/New_York"


def _ts(day, hm):
    return pd.Timestamp(f"{day} {hm}", tz=NY).tz_convert("UTC")


def _eq(a: dict, b: dict) -> bool:
    """Dict equality treating NaN == NaN (feature rows carry NaNs)."""
    if a.keys() != b.keys():
        return False
    for k, x in a.items():
        y = b[k]
        if isinstance(x, float) and isinstance(y, float) and math.isnan(x) and math.isnan(y):
            continue
        if x != y:
            return False
    return True


# --------------------------------------------------------------------------- SCDateTime
def test_scdatetime_round_trip():
    t = _ts("2026-03-17", "09:30")
    assert scdt_to_ts(ts_to_scdt(t)) == t
    # epoch anchor
    assert ts_to_scdt(pd.Timestamp("1899-12-30", tz="UTC")) == 0


# --------------------------------------------------------------------------- .scid round-trip
def test_scid_reader_inverts_writer(tmp_path):
    recs = [
        {"ts": _ts("2026-03-17", "08:00"), "open": 100.0, "high": 101.0, "low": 99.5,
         "close": 100.5, "num_trades": 12, "total_volume": 300, "bid_volume": 120,
         "ask_volume": 180},
        {"ts": _ts("2026-03-17", "08:01"), "open": 100.5, "high": 100.75, "low": 100.0,
         "close": 100.25, "num_trades": 8, "total_volume": 200, "bid_volume": 150,
         "ask_volume": 50},
    ]
    p = tmp_path / "nq.scid"
    write_scid(p, recs)
    out = list(ScidReader(p).records())
    assert len(out) == 2
    assert out[0].ts == recs[0]["ts"]
    assert (out[0].open, out[0].high, out[0].low, out[0].close) == (100.0, 101.0, 99.5, 100.5)
    assert (out[0].total_volume, out[0].bid_volume, out[0].ask_volume) == (300, 120, 180)
    assert out[1].close == 100.25 and out[1].num_trades == 8


def test_scid_ignores_partial_trailing_record(tmp_path):
    p = tmp_path / "nq.scid"
    write_scid(p, [{"ts": _ts("2026-03-17", "08:00"), "close": 100.0, "total_volume": 10}])
    # append 12 stray bytes (a half-written record mid-flush) — must be ignored, not crash.
    with p.open("ab") as f:
        f.write(b"\x00" * 12)
    assert len(list(ScidReader(p).records())) == 1


def test_scid_bad_magic_rejected(tmp_path):
    p = tmp_path / "bad.scid"
    p.write_bytes(b"XXXX" + b"\x00" * 60)
    try:
        list(ScidReader(p).records())
        raise AssertionError("expected ValueError on bad magic")
    except ValueError as e:
        assert "magic" in str(e)


# --------------------------------------------------------------------------- .depth round-trip
def test_depth_reader_inverts_writer(tmp_path):
    recs = [
        {"ts": _ts("2026-03-17", "08:00"), "command": DCMD_CLEAR},
        {"ts": _ts("2026-03-17", "08:00"), "command": DCMD_SET_BID, "price": 100.0,
         "qty": 50, "num_orders": 4},
        {"ts": _ts("2026-03-17", "08:00"), "command": DCMD_SET_ASK, "price": 100.25,
         "qty": 60, "num_orders": 6},
    ]
    p = tmp_path / "nq.depth"
    write_depth(p, recs)
    out = list(DepthReader(p).records())
    assert [e.action for e in out] == ["R", "B", "A"]
    assert (out[1].price, out[1].size, out[1].ct) == (100.0, 50, 4)
    assert (out[2].price, out[2].size, out[2].ct) == (100.25, 60, 6)


# --------------------------------------------------------------------------- DepthBook (level)
def test_depth_book_levels_and_delete():
    b = DepthBook()
    b.apply({"action": "R"})
    b.apply({"action": "B", "price": 100.0, "size": 50, "ct": 4})
    b.apply({"action": "B", "price": 99.75, "size": 30, "ct": 2})
    b.apply({"action": "A", "price": 100.25, "size": 60, "ct": 6})
    b.apply({"action": "A", "price": 100.50, "size": 20, "ct": 1})
    assert b.best_bid() == 100.0 and b.best_ask() == 100.25
    lf = b.long_form()
    bid0 = next(r for r in lf if r["side"] == "bid" and r["price"] == 100.0)
    assert bid0["size"] == 50 and bid0["ct"] == 4
    # update-in-place replaces the level (level data is already aggregate)
    b.apply({"action": "B", "price": 100.0, "size": 80, "ct": 5})
    assert next(r for r in b.long_form() if r["price"] == 100.0)["size"] == 80
    # explicit delete + set-to-zero delete
    b.apply({"action": "b", "price": 99.75})
    b.apply({"action": "A", "price": 100.25, "size": 0, "ct": 0})
    prices = {r["price"] for r in b.long_form()}
    assert 99.75 not in prices and 100.25 not in prices
    assert b.best_ask() == 100.50


# --------------------------------------------------------------------------- minute aggregation
def test_minute_aggregator_closes_on_new_minute():
    agg = MinuteAggregator()
    recs = [
        # minute 08:00 — two ticks
        _rec("08:00:10", close=100.0, vol=10, ask=8, bid=2, hi=100.0, lo=100.0),
        _rec("08:00:40", close=100.5, vol=20, ask=5, bid=15, hi=100.5, lo=99.9),
        # minute 08:01 — one tick (triggers 08:00 close)
        _rec("08:01:05", close=101.0, vol=5, ask=5, bid=0, hi=101.0, lo=101.0),
    ]
    closed = []
    for r in recs:
        closed += agg.push(r)
    assert len(closed) == 1
    m = closed[0]
    assert m["ts"] == _ts("2026-03-17", "08:00")
    assert m["bar"] == {"ts_event": _ts("2026-03-17", "08:00"), "open": 100.0,
                        "high": 100.5, "low": 99.9, "close": 100.5, "volume": 30.0}
    assert m["tape"]["delta"] == (8 - 2) + (5 - 15)        # = -4
    assert m["tape"]["vol"] == 30.0
    # vwp = (100.0*10 + 100.5*20)/30
    assert abs(m["tape"]["vwp"] - (100.0 * 10 + 100.5 * 20) / 30) < 1e-9
    # flush closes the forming 08:01 minute
    tail = agg.flush()
    assert len(tail) == 1 and tail[0]["ts"] == _ts("2026-03-17", "08:01")


def _rec(hms, *, close, vol, ask, bid, hi, lo):
    from src.canon.sierra_files import ScidRecord
    return ScidRecord(_ts("2026-03-17", hms), open=close, high=hi, low=lo, close=close,
                      num_trades=1, total_volume=vol, bid_volume=bid, ask_volume=ask)


# --------------------------------------------------------------------------- live tail
def test_live_tail_resumes_and_never_emits_forming_minute(tmp_path):
    p = tmp_path / "nq.scid"
    # three minutes present; minute 2 is the forming (last) minute.
    write_scid(p, [
        {"ts": _ts("2026-03-17", "08:00:05"), "close": 100.0, "total_volume": 10, "ask_volume": 10},
        {"ts": _ts("2026-03-17", "08:01:05"), "close": 100.5, "total_volume": 10, "ask_volume": 10},
        {"ts": _ts("2026-03-17", "08:02:05"), "close": 101.0, "total_volume": 10, "ask_volume": 10},
    ])
    feed = SierraFileFeed(p)
    ing = CanonIngestor(book=DepthBook())
    n1 = feed.poll(ing)
    # minutes 08:00 and 08:01 close; 08:02 stays buffered (forming) -> 2 bars, not 3.
    assert n1 == 2 and len(ing._bars) == 2
    # append a record in a later minute -> 08:02 now closes; no re-emit of 08:00/08:01.
    with p.open("ab") as f:
        from src.canon.sierra_files import SCID_REC
        f.write(SCID_REC.pack(ts_to_scdt(_ts("2026-03-17", "08:03:05")),
                              101.5, 101.5, 101.5, 101.5, 1, 10, 0, 10))
    n2 = feed.poll(ing)
    assert n2 == 1 and len(ing._bars) == 3
    assert [b["ts_event"] for b in ing._bars] == [_ts("2026-03-17", f"08:0{i}") for i in (0, 1, 2)]


# --------------------------------------------------------------------------- PARITY vs ReplaySource
def _synth_day():
    """One session's worth of 1-minute bars (08:00–09:59 ET, 2026-03-17), each minute a single
    .scid record so aggregation is identity — the same numbers fed to ReplaySource."""
    bars, scid_recs, fp_rows = [], [], []
    px = 18000.0
    for i in range(120):
        ts = _ts("2026-03-17", "08:00") + pd.Timedelta(minutes=i)
        o = px
        px = px + (1.5 if i % 3 == 0 else -1.0)
        c = px
        hi, lo = max(o, c) + 2.0, min(o, c) - 2.0
        vol = 100 + (i % 7) * 10
        ask = 60 + (i % 5) * 5
        bid = vol - ask
        bars.append({"ts_event": ts, "open": o, "high": hi, "low": lo, "close": c,
                     "volume": float(vol)})
        scid_recs.append({"ts": ts, "open": o, "high": hi, "low": lo, "close": c,
                          "num_trades": 1, "total_volume": vol, "bid_volume": bid,
                          "ask_volume": ask})
        fp_rows.append({"ts_event": ts, "delta": float(ask - bid), "vol": float(vol),
                        "vwp": float(c)})     # single-record minute -> vwp == close
    return (pd.DataFrame(bars),
            pd.DataFrame(fp_rows).set_index("ts_event"),
            scid_recs)


def test_filetail_matches_replaysource_feature_row(tmp_path):
    bars, footprint, scid_recs = _synth_day()

    # Path A — the trusted offline path.
    ing_replay = CanonIngestor()
    ReplaySource(bars, footprint).drive(ing_replay)

    # Path B — the new file-tail path (no depth: ReplaySource carries none, so book is empty
    # in both, isolating the tape/CVD + VWAP-geometry families for an exact comparison).
    p = tmp_path / "nq.scid"
    write_scid(p, scid_recs)
    ing_file = CanonIngestor(book=DepthBook())
    applied = SierraFileFeed(p).drive_batch(ing_file)
    assert applied == 120

    fill = _ts("2026-03-17", "09:50")
    entry = float(bars.loc[bars.ts_event == fill, "open"].iloc[0]) if (bars.ts_event == fill).any() \
        else 18000.0
    for direction in ("long", "short"):
        row_replay = ing_replay.feature_row(fill, entry, direction)
        row_file = ing_file.feature_row(fill, entry, direction)
        assert _eq(row_file, row_replay), (
            f"[{direction}] file-tail feature row diverges from ReplaySource:\n"
            f"  file={row_file}\n  replay={row_replay}")
    # sanity: the parity row actually carries the tape + VWAP families (not an empty dict).
    r = ing_file.feature_row(fill, entry, "long")
    assert "pm_sofar_cvd" in r and "ent_vs_vwap_sd" in r


def test_filetail_with_depth_populates_depth_family(tmp_path):
    _, _, scid_recs = _synth_day()
    sp = tmp_path / "nq.scid"
    dp = tmp_path / "nq.depth"
    write_scid(sp, scid_recs)
    # a book snapshot just before the fill, with a clear wall above and below the entry
    entry = 18000.0
    dt = _ts("2026-03-17", "09:49:30")
    write_depth(dp, [
        {"ts": dt, "command": DCMD_CLEAR},
        {"ts": dt, "command": DCMD_SET_BID, "price": entry - 2.0, "qty": 400, "num_orders": 20},
        {"ts": dt, "command": DCMD_SET_BID, "price": entry - 5.0, "qty": 90, "num_orders": 5},
        {"ts": dt, "command": DCMD_SET_ASK, "price": entry + 3.0, "qty": 500, "num_orders": 25},
        {"ts": dt, "command": DCMD_SET_ASK, "price": entry + 8.0, "qty": 70, "num_orders": 4},
    ])
    ing = CanonIngestor(book=DepthBook())
    SierraFileFeed(sp, dp).drive_batch(ing)
    row = ing.feature_row(_ts("2026-03-17", "09:50"), entry, "long")
    assert "dep_thick" in row and row["dep_thick"] == 400 + 90 + 500 + 70
    # nearest/biggest wall below = the 400-lot bid at entry-2; above = the 500-lot ask at entry+3
    assert row["dep_wall_below_sz"] == 400 and row["dep_wall_below_d"] == 2.0
    assert row["dep_wall_above_sz"] == 500 and row["dep_wall_above_d"] == 3.0


# --------------------------------------------------------------------------- pin-check gate
def test_pin_check_fails_when_order_flow_missing(tmp_path):
    """A .scid whose BidVolume/AskVolume are all zero must FAIL the pin check.

    The bytes decode fine, so nothing else catches it — but the whole CVD family
    (cvd_*, fill_delta, absorption, delta_div, stacked_imb, d5/d15/d30) has no source.
    Silent + expensive, so the pin check treats it as a hard stop.
    """
    from scripts.sierra_pin_check import check_scid

    base = dict(open=100.0, high=100.0, low=100.0, close=100.0, num_trades=1, total_volume=5)
    ts = _ts("2026-07-24", "09:30:00")

    ok = tmp_path / "ok.scid"
    write_scid(ok, [dict(ts=ts, bid_volume=2, ask_volume=3, **base)])
    assert check_scid(ok) is True

    dead = tmp_path / "dead.scid"
    write_scid(dead, [dict(ts=ts, bid_volume=0, ask_volume=0, **base)])
    assert check_scid(dead) is False
