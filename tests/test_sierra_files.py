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
import pytest

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


def test_depth_command_enum_is_pinned_to_the_real_sierra_numbering(tmp_path):
    """PINNED ON THE BOX 2026-07-26 (SC build 2930, real NQU6.CME .depth + Sierra's file-
    format doc): 1 clear, 2/3 add, 4/5 MODIFY, 6/7 DELETE. The original offline guess had
    deletes at 4/5 — a real file FAILED the pin check on Command 6, and modifies would have
    silently decoded as deletes. This test freezes the corrected mapping."""
    from src.canon.sierra_files import (
        DCMD_ADD_ASK,
        DCMD_ADD_BID,
        DCMD_DEL_ASK,
        DCMD_DEL_BID,
        DCMD_MOD_ASK,
        DCMD_MOD_BID,
    )
    assert (DCMD_CLEAR, DCMD_ADD_BID, DCMD_ADD_ASK) == (1, 2, 3)
    assert (DCMD_MOD_BID, DCMD_MOD_ASK, DCMD_DEL_BID, DCMD_DEL_ASK) == (4, 5, 6, 7)
    p = tmp_path / "nq.depth"
    write_depth(p, [
        {"ts": _ts("2026-03-17", "08:00"), "command": DCMD_ADD_BID, "price": 100.0,
         "qty": 50, "num_orders": 4},
        {"ts": _ts("2026-03-17", "08:00"), "command": DCMD_MOD_BID, "price": 100.0,
         "qty": 75, "num_orders": 5},
        {"ts": _ts("2026-03-17", "08:00"), "command": DCMD_DEL_BID, "price": 100.0},
        {"ts": _ts("2026-03-17", "08:00"), "command": DCMD_MOD_ASK, "price": 100.25,
         "qty": 20, "num_orders": 2},
        {"ts": _ts("2026-03-17", "08:00"), "command": DCMD_DEL_ASK, "price": 100.25},
    ])
    out = list(DepthReader(p).records())
    assert [e.action for e in out] == ["B", "B", "b", "A", "a"]   # modify SETS, never deletes
    assert (out[1].size, out[1].ct) == (75, 5)
    b = DepthBook()
    for e in out:
        b.apply({"action": e.action, "price": e.price, "size": e.size, "ct": e.ct})
    assert b.best_bid() is None and b.best_ask() is None          # add+mod+del leaves empty


def _feed_files(tmp_path, *, depth_scale=1.0, close=28480.75):
    """A tiny scid (two records) + depth (clear, one bid, one ask) pair; depth prices
    written at `depth_scale` x the true price, as Pat's box does at 100x."""
    sp, dp = tmp_path / "nq.scid", tmp_path / "nq.depth"
    ts = _ts("2026-03-17", "08:00")
    write_scid(sp, [
        {"ts": ts, "close": close, "total_volume": 5, "bid_volume": 2, "ask_volume": 3},
        {"ts": _ts("2026-03-17", "08:02"), "close": close + 0.25, "total_volume": 5,
         "bid_volume": 2, "ask_volume": 3},
    ])
    write_depth(dp, [
        {"ts": ts, "command": DCMD_CLEAR},
        {"ts": ts, "command": DCMD_SET_BID, "price": (close - 0.25) * depth_scale,
         "qty": 50, "num_orders": 4},
        {"ts": ts, "command": DCMD_SET_ASK, "price": (close + 0.25) * depth_scale,
         "qty": 60, "num_orders": 6},
    ])
    return sp, dp


def test_depth_price_scale_100x_is_detected_and_divided_out(tmp_path):
    """Pat's VPS (2026-07-26): .scid prices in points, .depth prices 100x. The feed must
    detect the factor from the files themselves and emit UNSCALED depth prices, or every
    wall-distance feature is silently wrong by 100x."""
    from src.canon.ingestor import CanonIngestor
    sp, dp = _feed_files(tmp_path, depth_scale=100.0)
    feed = SierraFileFeed(sp, dp)
    ing = CanonIngestor(book=DepthBook())
    feed.drive_batch(ing)
    assert feed.depth_price_scale == 100.0
    assert ing.book.best_bid() == pytest.approx(28480.50)
    assert ing.book.best_ask() == pytest.approx(28481.00)


def test_depth_price_scale_1x_stays_untouched(tmp_path):
    from src.canon.ingestor import CanonIngestor
    sp, dp = _feed_files(tmp_path, depth_scale=1.0)
    feed = SierraFileFeed(sp, dp)
    ing = CanonIngestor(book=DepthBook())
    feed.drive_batch(ing)
    assert feed.depth_price_scale == 1.0
    assert ing.book.best_bid() == pytest.approx(28480.50)


def test_depth_price_scale_not_a_power_of_ten_refuses(tmp_path):
    from src.canon.ingestor import CanonIngestor
    sp, dp = _feed_files(tmp_path, depth_scale=37.0)
    feed = SierraFileFeed(sp, dp)
    with pytest.raises(ValueError, match="not a power of ten"):
        feed.drive_batch(CanonIngestor(book=DepthBook()))


def test_depth_events_are_held_until_a_trade_reference_exists(tmp_path):
    """Depth before any .scid record: no reference to judge the scale against, so events
    are HELD (never emitted unscaled) and released once the first trade price arrives."""
    from src.canon.ingestor import CanonIngestor
    sp, dp = tmp_path / "nq.scid", tmp_path / "nq.depth"
    write_scid(sp, [])                                   # header only, no trades yet
    ts = _ts("2026-03-17", "08:00")
    write_depth(dp, [
        {"ts": ts, "command": DCMD_SET_BID, "price": 2848050.0, "qty": 50, "num_orders": 4},
    ])
    feed = SierraFileFeed(sp, dp)
    ing = CanonIngestor(book=DepthBook())
    feed.poll(ing)
    assert feed.depth_price_scale is None and ing.book.best_bid() is None   # held
    write_scid(sp, [{"ts": ts, "close": 28480.75, "total_volume": 5,
                     "bid_volume": 2, "ask_volume": 3}])
    feed.poll(ing)
    assert feed.depth_price_scale == 100.0
    assert ing.book.best_bid() == pytest.approx(28480.50)                   # released


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


# --------------------------------------------------------------------------- feed lag (Route B)
def test_feed_lag_measured_per_bar_on_poll(tmp_path):
    """poll() records wall-clock file-append latency per closed bar (FEED-LAG directive):
    lag = readable-at (injected clock) − bar close (minute + 1min). Reported, not corrected."""
    p = tmp_path / "nq.scid"
    write_scid(p, [
        {"ts": _ts("2026-03-17", "08:00:05"), "close": 100.0, "total_volume": 10, "ask_volume": 10},
        {"ts": _ts("2026-03-17", "08:01:05"), "close": 100.5, "total_volume": 10, "ask_volume": 10},
        {"ts": _ts("2026-03-17", "08:02:05"), "close": 101.0, "total_volume": 10, "ask_volume": 10},
    ])
    journaled: list[dict] = []
    # clock returns a fixed "now" at the poll: 08:02:05 UTC (the same day/tz as the bars).
    now = _ts("2026-03-17", "08:02:05")
    feed = SierraFileFeed(p, clock=lambda: now, on_lag=journaled.append, flush_ms=1000)
    ing = CanonIngestor(book=DepthBook())
    feed.poll(ing)                                     # closes 08:00 and 08:01 (08:02 forming)

    # 08:00 bar closes at 08:01:00 -> lag 65s;  08:01 bar closes at 08:02:00 -> lag 5s.
    assert feed.lag.samples == [65.0, 5.0]
    assert [r["lag_s"] for r in journaled] == [65.0, 5.0]
    s = feed.lag_summary()
    assert s["n"] == 2 and s["flush_ms"] == 1000
    assert s["min_s"] == 5.0 and s["max_s"] == 65.0 and s["median_s"] in (5.0, 65.0)


def test_feed_lag_absent_in_batch_mode(tmp_path):
    """drive_batch (historical replay / parity) does NOT record lag — the wall clock is
    unrelated to historical bar times, so a lag number there would be meaningless."""
    p = tmp_path / "nq.scid"
    write_scid(p, [{"ts": _ts("2026-03-17", "08:00:05"), "close": 100.0, "total_volume": 10},
                   {"ts": _ts("2026-03-17", "08:01:05"), "close": 100.5, "total_volume": 10}])
    feed = SierraFileFeed(p, flush_ms=1000)
    feed.drive_batch(CanonIngestor(book=DepthBook()))
    assert feed.lag_summary() == {"n": 0, "flush_ms": 1000}


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
    Silent + expensive, so the pin check treats it as a hard stop. (check_scid RAISES
    OrderFlowFail on the blind case — the unified contract, see test_sierra_pin_check.py.)
    """
    import pytest

    from scripts.sierra_pin_check import OrderFlowFail, check_scid

    base = dict(open=100.0, high=100.0, low=100.0, close=100.0, num_trades=1, total_volume=5)
    ts = _ts("2026-07-24", "09:30:00")

    ok = tmp_path / "ok.scid"
    write_scid(ok, [dict(ts=ts, bid_volume=2, ask_volume=3, **base)])
    assert check_scid(ok) is True

    dead = tmp_path / "dead.scid"
    write_scid(dead, [dict(ts=ts, bid_volume=0, ask_volume=0, **base)])
    with pytest.raises(OrderFlowFail):
        check_scid(dead)


# --------------------------------------------------------------------------- bar price scale
# Pat's VPS (2026-08-01, R13 practice-day cert): the Rithmic-named NQU6.CME.scid writes
# BAR prices 100x (2857526.00) — same box whose NQU26-CME.scid writes points. Both runs
# over 2026-07-31 produced ZERO triggers: level clustering and every point-based
# tolerance in detect_triggers breaks at 100x, silently. Bars are normalized at the
# source, anchored to a known-good reference price, refusing when no clean decade fits.

def _feed_100x_files(tmp_path, *, bar_scale=100.0, depth_scale=100.0, close=28480.75):
    """scid AND depth both written scaled — the NQU6.CME.* state found on the box."""
    sp, dp = tmp_path / "nq6.scid", tmp_path / "nq6.depth"
    ts = _ts("2026-03-17", "08:00")
    write_scid(sp, [
        {"ts": ts, "close": close * bar_scale, "total_volume": 5,
         "bid_volume": 2, "ask_volume": 3},
        {"ts": _ts("2026-03-17", "08:02"), "close": (close + 0.25) * bar_scale,
         "total_volume": 5, "bid_volume": 2, "ask_volume": 3},
    ])
    write_depth(dp, [
        {"ts": ts, "command": DCMD_CLEAR},
        {"ts": ts, "command": DCMD_SET_BID, "price": (close - 0.25) * depth_scale,
         "qty": 50, "num_orders": 4},
        {"ts": ts, "command": DCMD_SET_ASK, "price": (close + 0.25) * depth_scale,
         "qty": 60, "num_orders": 6},
    ])
    return sp, dp


def test_bar_price_scale_100x_detected_bars_and_depth_end_in_points(tmp_path):
    from src.canon.ingestor import CanonIngestor
    sp, dp = _feed_100x_files(tmp_path)
    feed = SierraFileFeed(sp, dp, reference_px=23_364.0)   # repo reference last close
    ing = CanonIngestor(book=DepthBook())
    feed.drive_batch(ing)
    assert feed.bar_price_scale == 100.0
    # bars in points at the ingestor…
    assert ing.bars_frame()["close"].iloc[0] == pytest.approx(28480.75)
    # …and the depth detection COMPOSES: raw 100x depth vs the now-scaled trade price
    assert feed.depth_price_scale == 100.0
    assert ing.book.best_bid() == pytest.approx(28480.50)
    assert ing.book.best_ask() == pytest.approx(28481.00)


def test_bar_price_scale_without_anchor_is_todays_behavior(tmp_path):
    """No reference_px -> scale 1.0, untouched — consumers that never see scaled files
    (parity replays over known-good captures, tests) keep their exact behavior."""
    from src.canon.ingestor import CanonIngestor
    sp, dp = _feed_100x_files(tmp_path)
    feed = SierraFileFeed(sp, dp)
    ing = CanonIngestor(book=DepthBook())
    feed.drive_batch(ing)
    assert feed.bar_price_scale == 1.0
    assert ing.bars_frame()["close"].iloc[0] == pytest.approx(2_848_075.0)


def test_bar_price_scale_points_file_with_anchor_stays_1x(tmp_path):
    from src.canon.ingestor import CanonIngestor
    sp, dp = _feed_files(tmp_path, depth_scale=100.0)      # scid already in points
    feed = SierraFileFeed(sp, dp, reference_px=23_364.0)
    ing = CanonIngestor(book=DepthBook())
    feed.drive_batch(ing)
    assert feed.bar_price_scale == 1.0
    assert feed.depth_price_scale == 100.0
    assert ing.bars_frame()["close"].iloc[0] == pytest.approx(28480.75)


def test_bar_price_scale_no_clean_decade_refuses(tmp_path):
    """37x off the anchor: nothing lands within sqrt(10) of a power of ten — RAISE,
    never trade on implausible prices (the zero-triggers-forever failure mode)."""
    from src.canon.ingestor import CanonIngestor
    sp, dp = _feed_100x_files(tmp_path, bar_scale=37.0, depth_scale=1.0)
    feed = SierraFileFeed(sp, dp, reference_px=23_364.0)
    with pytest.raises(ValueError, match="refusing to guess"):
        feed.drive_batch(CanonIngestor(book=DepthBook()))


def test_bar_price_scale_explicit_pin_wins_without_anchor(tmp_path):
    from src.canon.ingestor import CanonIngestor
    sp, dp = _feed_100x_files(tmp_path)
    feed = SierraFileFeed(sp, dp, bar_price_scale=100.0)   # PIN-ON-BOX config
    ing = CanonIngestor(book=DepthBook())
    feed.drive_batch(ing)
    assert ing.bars_frame()["close"].iloc[0] == pytest.approx(28480.75)


def test_retarget_scid_redetects_both_scales(tmp_path):
    """A contract roll can swap naming variants (NQU26-CME points <-> NQU6.CME 100x) —
    the new file's evidence decides, not the old file's."""
    from src.canon.ingestor import CanonIngestor
    sp1, dp1 = _feed_files(tmp_path, depth_scale=1.0)          # points file
    feed = SierraFileFeed(sp1, dp1, reference_px=23_364.0)
    ing = CanonIngestor(book=DepthBook())
    feed.drive_batch(ing)
    assert feed.bar_price_scale == 1.0
    sp2, dp2 = _feed_100x_files(tmp_path)                      # roll onto the 100x variant
    feed.retarget_scid(sp2, depth_path=dp2)
    assert feed.bar_price_scale is None                        # re-detect from new evidence
    ing2 = CanonIngestor(book=DepthBook())
    feed.drive_batch(ing2)
    assert feed.bar_price_scale == 100.0
    assert ing2.bars_frame()["close"].iloc[0] == pytest.approx(28480.75)


# --------------------------------------------------------------------------- tick records
def test_tick_records_zero_open_aggregate_from_trades_not_quotes(tmp_path):
    """Sierra TICK files (the box's NQU6.CME.scid): record Open is a FLAG (0.0), High/Low
    are the ASK/BID quotes, Close is the trade. The minute bar must come from TRADES —
    open = first trade, high/low = trade extremes (quote extremes would widen every bar
    by the spread). A zero open leaking through reads as 'displacement through every
    level below the close' and manufactures wrong-side long brackets (practice day 2)."""
    from src.canon.ingestor import CanonIngestor
    sp = tmp_path / "tick.scid"
    ts = _ts("2026-03-17", "08:00")
    recs = []
    for sec, px in ((0, 28480.75), (10, 28482.00), (20, 28479.50), (30, 28481.25)):
        recs.append({"ts": ts + pd.Timedelta(seconds=sec), "open": 0.0,
                     "high": px + 0.50,            # ask quote — must NOT become bar high
                     "low": px - 0.50,             # bid quote — must NOT become bar low
                     "close": px, "num_trades": 1, "total_volume": 2,
                     "bid_volume": 1, "ask_volume": 1})
    recs.append({"ts": _ts("2026-03-17", "08:01"), "open": 0.0, "high": 28481.0,
                 "low": 28480.0, "close": 28480.5, "num_trades": 1, "total_volume": 1,
                 "bid_volume": 1, "ask_volume": 0})
    write_scid(sp, recs)
    feed = SierraFileFeed(sp, None)
    ing = CanonIngestor(book=DepthBook())
    feed.drive_batch(ing)
    bars = ing.bars_frame()
    b = bars.iloc[0]
    assert b["open"] == pytest.approx(28480.75)     # first TRADE, not 0.0
    assert b["high"] == pytest.approx(28482.00)     # trade extreme, not ask 28482.50
    assert b["low"] == pytest.approx(28479.50)      # trade extreme, not bid 28479.00
    assert b["close"] == pytest.approx(28481.25)
    assert (bars["open"] > 0).all()


def test_summary_records_keep_their_real_ohlc(tmp_path):
    """Records with a real Open (historical summary section of the same file) keep their
    own OHLC — the tick rule is per-record, not per-file."""
    from src.canon.ingestor import CanonIngestor
    sp = tmp_path / "mix.scid"
    write_scid(sp, [
        {"ts": _ts("2026-03-17", "08:00"), "open": 28480.0, "high": 28485.0,
         "low": 28478.0, "close": 28481.0, "num_trades": 9, "total_volume": 40,
         "bid_volume": 18, "ask_volume": 22},
        {"ts": _ts("2026-03-17", "08:01"), "open": 28481.0, "high": 28482.0,
         "low": 28480.0, "close": 28481.5, "num_trades": 3, "total_volume": 10,
         "bid_volume": 5, "ask_volume": 5},
    ])
    feed = SierraFileFeed(sp, None)
    ing = CanonIngestor(book=DepthBook())
    feed.drive_batch(ing)
    b = ing.bars_frame().iloc[0]
    assert (b["open"], b["high"], b["low"]) == (28480.0, 28485.0, 28478.0)


def test_priceless_records_are_skipped(tmp_path):
    from src.canon.ingestor import CanonIngestor
    sp = tmp_path / "flag.scid"
    write_scid(sp, [
        {"ts": _ts("2026-03-17", "08:00"), "open": 0.0, "high": 0.0, "low": 0.0,
         "close": 0.0, "num_trades": 0, "total_volume": 0},   # heartbeat/flag record
        {"ts": _ts("2026-03-17", "08:00:30"), "open": 0.0, "high": 28481.0,
         "low": 28480.0, "close": 28480.5, "num_trades": 1, "total_volume": 1,
         "bid_volume": 0, "ask_volume": 1},
        {"ts": _ts("2026-03-17", "08:01"), "open": 0.0, "high": 28482.0,
         "low": 28480.0, "close": 28481.0, "num_trades": 1, "total_volume": 1,
         "bid_volume": 0, "ask_volume": 1},
    ])
    feed = SierraFileFeed(sp, None)
    ing = CanonIngestor(book=DepthBook())
    feed.drive_batch(ing)
    b = ing.bars_frame().iloc[0]
    assert b["low"] == pytest.approx(28480.5) and b["open"] == pytest.approx(28480.5)
