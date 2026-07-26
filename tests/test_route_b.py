"""Route-B live loop tests (src/live/route_b.py) — fan-out, shadow-spine evidence, roll
re-point, stall/stop. Offline against synthetic .scid/.depth; the champion runner and clock
are faked so nothing blocks and no broker is ever reachable."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from src.canon.book import DepthBook
from src.canon.ingestor import CanonIngestor
from src.canon.sierra_files import (
    DCMD_CLEAR,
    DCMD_SET_ASK,
    DCMD_SET_BID,
    SierraFileFeed,
    write_depth,
    write_scid,
)
from src.canon.sierra_symbol import RollWatcher, resolve_scid_path
from src.canon.spine import AccountState, FeedHealth
from src.live.route_b import (
    RouteBLive,
    _NoBroker,
    build_shadow_instrument,
)

NY = "America/New_York"


def _ts(hms, day="2026-03-17"):
    return pd.Timestamp(f"{day} {hms}", tz=NY).tz_convert("UTC")


def _scid(path, day="2026-03-17"):
    write_scid(path, [
        {"ts": _ts("08:00:05", day), "close": 100.0, "total_volume": 10, "bid_volume": 4,
         "ask_volume": 6},
        {"ts": _ts("08:01:05", day), "close": 100.5, "total_volume": 10, "bid_volume": 3,
         "ask_volume": 7},
        {"ts": _ts("08:02:05", day), "close": 101.0, "total_volume": 10, "bid_volume": 5,
         "ask_volume": 5},
    ])


def _cand(**kw):
    base = {"size": 1.0, "entry": 18000.0, "stop_initial": 17990.0, "target_level": 18050.0,
            "direction": "long", "trade_date": "2026-03-17",
            "fill_ts": "2026-03-17T08:20:00-04:00"}
    base.update(kw)
    return SimpleNamespace(**base)


class FakeRunner:
    def __init__(self, journal_dir, trades_on=None):
        self.primed = None
        self.finalized = False
        self.alerts = None
        self.broker = SimpleNamespace(equity=lambda: 52_000.0)
        self.journal = SimpleNamespace(dir=Path(journal_dir))
        self._trades_on = trades_on or {}
        self.bars_seen = []

    def prime(self, df):
        self.primed = df

    def finalize(self):
        self.finalized = True

    def on_bar(self, bar):
        self.bars_seen.append(str(bar.ts_event))
        return list(self._trades_on.get(str(bar.ts_event), []))


# --------------------------------------------------------------------------- poll_events / retarget
def test_poll_events_returns_merged_and_records_lag(tmp_path):
    sp = tmp_path / "nq.scid"
    _scid(sp)
    feed = SierraFileFeed(sp, clock=lambda: _ts("08:02:05"), flush_ms=1000)
    events = feed.poll_events()
    kinds = [e["kind"] for e in events]
    assert kinds == ["minute", "minute"]              # 08:00, 08:01 close; 08:02 forming
    assert feed.lag_summary()["n"] == 2               # per-bar lag recorded on the poll


def test_retarget_depth_and_scid(tmp_path):
    sp1, sp2 = tmp_path / "u.scid", tmp_path / "z.scid"
    _scid(sp1)
    _scid(sp2, day="2026-09-14")
    feed = SierraFileFeed(sp1)
    feed.retarget_scid(sp2)
    assert Path(feed.scid_path) == sp2 and feed._depth is None
    dp = tmp_path / "d.depth"
    write_depth(dp, [{"ts": _ts("08:00"), "command": DCMD_CLEAR}])
    feed.retarget_depth(dp)
    assert feed._depth is not None


# --------------------------------------------------------------------------- _NoBroker
def test_no_broker_forbids_every_call():
    nb = _NoBroker()
    for m in ("submit_bracket", "order_status", "position", "flatten", "cancel_all"):
        with pytest.raises(AssertionError):
            getattr(nb, m)("x")


# --------------------------------------------------------------------------- shadow instrument
def _good_acct():
    return AccountState(equity=52_000, trailing_floor=50_000, day_pnl=-100, open_positions=0)


def _good_feed():
    return FeedHealth(last_tick_age_ms=100, crossed_or_locked=False, context_complete=True,
                      spread_rel=1.0)


def test_shadow_instrument_emits_all_three_artifacts(tmp_path):
    inst = build_shadow_instrument(tmp_path)
    out = inst.observe(_cand(), _good_acct(), _good_feed(), now_epoch=0.0)
    # sizing.jsonl: micros = dollar_risk_micros(1.0, 10.0) = 200/(10*2) = 10
    sizing = [json.loads(x) for x in (tmp_path / "sizing.jsonl").read_text().splitlines()]
    assert sizing[0]["micros"] == 10 and sizing[0]["conviction"] == 1.0
    assert out["sizing_micros"] == 10
    # spine.jsonl carries the all-guards report AND a shadow decision (disarmed)
    spine = [json.loads(x) for x in (tmp_path / "spine.jsonl").read_text().splitlines()]
    assert any(e.get("event") == "guard_report" for e in spine)
    assert any(e.get("event") == "shadow_place" for e in spine)   # disarmed -> not sent
    # good state -> no rejection recorded
    assert not (tmp_path / "rejects.jsonl").exists() or \
        (tmp_path / "rejects.jsonl").read_text().strip() == ""


def test_shadow_instrument_records_reject_on_bad_feed(tmp_path):
    inst = build_shadow_instrument(tmp_path)
    stale = FeedHealth(last_tick_age_ms=9_000, crossed_or_locked=False,
                       context_complete=True, spread_rel=1.0)
    inst.observe(_cand(), _good_acct(), stale, now_epoch=0.0)
    rej = [json.loads(x) for x in (tmp_path / "rejects.jsonl").read_text().splitlines()]
    assert rej and rej[0]["code"] == "feed_stale" and rej[0]["source"] == "spine"


# --------------------------------------------------------------------------- dispatch fan-out
def test_dispatch_fans_out_to_runner_ingestor_and_instrument(tmp_path):
    sp = tmp_path / "nq.scid"
    _scid(sp)
    feed = SierraFileFeed(sp, clock=lambda: _ts("08:02:05"))
    # champion completes a trade on the 08:01 bar
    runner = FakeRunner(tmp_path, trades_on={str(_ts("08:01")): [_cand()]})
    inst = build_shadow_instrument(tmp_path)
    live = RouteBLive(runner=runner, feed=feed, data_dir=tmp_path, instrument=inst,
                      ingestor=CanonIngestor(book=DepthBook()))
    completed = live.dispatch(feed.poll_events(), now=_ts("08:02:05"))
    assert len(completed) == 1                         # champion trade surfaced
    assert runner.bars_seen == [str(_ts("08:00")), str(_ts("08:01"))]   # bars fanned to champion
    assert len(live.ingestor._bars) == 2               # AND to the canon ingestor
    assert (tmp_path / "sizing.jsonl").exists()         # shadow evidence emitted for the trade


# --------------------------------------------------------------------------- roll re-point
def test_maybe_retarget_repoints_scid_and_alerts_on_roll(tmp_path):
    sp = tmp_path / "start.scid"
    _scid(sp)
    feed = SierraFileFeed(sp)
    said = []
    runner = FakeRunner(tmp_path)
    live = RouteBLive(runner=runner, feed=feed, data_dir=tmp_path,
                      watcher=RollWatcher(start=date(2026, 9, 13)),
                      alerts=SimpleNamespace(say=said.append))
    # step to the roll day (Sep 14) -> depth re-points (new day) AND scid re-points (roll)
    live._maybe_retarget(_ts("08:00", day="2026-09-14"))
    assert Path(feed.scid_path) == resolve_scid_path(tmp_path, date(2026, 9, 14))
    assert Path(feed.scid_path).name == "NQZ26-CME.scid"
    assert said and "CONTRACT ROLL" in said[0]


def test_maybe_retarget_swaps_depth_daily_without_roll(tmp_path):
    sp = tmp_path / "nq.scid"
    _scid(sp)
    feed = SierraFileFeed(sp)
    runner = FakeRunner(tmp_path)
    live = RouteBLive(runner=runner, feed=feed, data_dir=tmp_path,
                      watcher=RollWatcher(start=date(2026, 3, 17)))
    live._maybe_retarget(_ts("09:00", day="2026-03-17"))
    d1 = str(feed.depth_path)
    live._maybe_retarget(_ts("09:00", day="2026-03-18"))    # next day, same contract
    d2 = str(feed.depth_path)
    assert d1 != d2 and Path(feed.scid_path) == sp          # depth swapped, scid unchanged


# --------------------------------------------------------------------------- serve stop/stall
def test_serve_stops_on_stop_fn(tmp_path):
    sp = tmp_path / "nq.scid"
    _scid(sp)
    runner = FakeRunner(tmp_path)
    live = RouteBLive(runner=runner, feed=SierraFileFeed(sp, clock=lambda: _ts("08:02:05")),
                      data_dir=tmp_path, ingestor=CanonIngestor(book=DepthBook()))
    live.serve(sleep_fn=lambda s: None, stop_fn=lambda: True)   # stop immediately
    assert runner.finalized is True


def test_serve_halts_on_stall(tmp_path):
    sp = tmp_path / "nq.scid"
    _scid(sp)
    # clock jumps far past the last bar so the feed guard reports a stall on the first check.
    live = RouteBLive(runner=FakeRunner(tmp_path),
                      feed=SierraFileFeed(sp, clock=lambda: _ts("10:00")),
                      data_dir=tmp_path, ingestor=CanonIngestor(book=DepthBook()),
                      clock=lambda: _ts("10:00"))
    live.serve(sleep_fn=lambda s: None, max_polls=5)
    # stalled -> loop broke before exhausting max_polls; runner finalized
    assert live.runner.finalized is True
