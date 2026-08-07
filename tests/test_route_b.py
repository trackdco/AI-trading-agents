"""Route-B canon-lane loop tests (src/live/route_b.py).

The AUTHORITATIVE path is canon verdicts (a VerdictSource) driving the verdict journal + the
disarmed spine. The champion is demoted to a non-authoritative comparator. Offline against
synthetic .scid + a fixture verdict source; the clock is faked so nothing blocks, and _NoBroker
makes any order route impossible."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from src.canon.book import DepthBook
from src.canon.ingestor import CanonIngestor
from src.canon.sierra_files import SierraFileFeed, write_scid
from src.canon.spine import AccountState, FeedHealth
from src.live.route_b import (
    JsonlSink,
    RollState,
    RouteBLive,
    _NoBroker,
    build_shadow_instrument,
    constant_account_fn,
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


def _bar(ts, close=100.0):
    return {"ts_event": ts, "open": close, "high": close, "low": close, "close": close,
            "volume": 10.0}


def _tape():
    return {"delta": 1.0, "vol": 10.0, "vwp": 100.0}


def _verdict(fill_ts, day="2026-03-17", direction="long", micros=10):
    return {"session": "NY", "day": day, "fill": pd.Timestamp(fill_ts).isoformat(),
            "direction": direction, "entry": 18000.0, "stop": 17990.0, "target": 18020.0,
            "conviction": 1.0, "risk_pts": 10.0, "micros": micros, "pl": 100.0}


class FixtureVerdictSource:
    def __init__(self, by_day):
        self.by_day = by_day
        self.asked = []

    def session_verdicts(self, day):
        self.asked.append(str(day))
        return list(self.by_day.get(str(day), []))


class FakeComparator:
    """Stand-in champion LiveRunner: on_bar returns trades on given ts; prime/finalize noop."""
    def __init__(self, trades_on=None):
        self.primed = None
        self.finalized = False
        self._trades_on = trades_on or {}

    def prime(self, df):
        self.primed = df

    def finalize(self):
        self.finalized = True

    def on_bar(self, bar):
        return list(self._trades_on.get(str(bar.ts_event), []))


def _good_acct():
    return AccountState(equity=52_000, trailing_floor=50_000, day_pnl=-100, open_positions=0)


def _good_feed():
    return FeedHealth(last_tick_age_ms=100, crossed_or_locked=False, context_complete=True,
                      spread_rel=1.0)


# --------------------------------------------------------------------------- feed primitives
def test_poll_events_returns_merged_and_records_lag(tmp_path):
    sp = tmp_path / "nq.scid"
    _scid(sp)
    feed = SierraFileFeed(sp, clock=lambda: _ts("08:02:05"), flush_ms=1000)
    events = feed.poll_events()
    assert [e["kind"] for e in events] == ["minute", "minute"]
    assert feed.lag_summary()["n"] == 2


def test_retarget_depth_and_scid(tmp_path):
    sp1, sp2 = tmp_path / "u.scid", tmp_path / "z.scid"
    _scid(sp1)
    _scid(sp2, day="2026-09-16")
    feed = SierraFileFeed(sp1)
    feed.retarget_scid(sp2)
    assert Path(feed.scid_path) == sp2 and feed._depth is None


def test_no_broker_forbids_every_call():
    nb = _NoBroker()
    for m in ("submit_bracket", "order_status", "position", "flatten", "cancel_all"):
        with pytest.raises(AssertionError):
            getattr(nb, m)("x")


# --------------------------------------------------------------------------- shadow instrument
def test_observe_verdict_emits_sizing_and_spine(tmp_path):
    inst = build_shadow_instrument(tmp_path)
    v = _verdict(_ts("08:20"))
    out = inst.observe_verdict(v, _good_acct(), _good_feed(), now_epoch=0.0)
    # The verdict's anchor (10) is merged remove-risk-only with the canon schedule, which at
    # the $150 lucid base and a 10pt stop is 8 micros. Live, the verdict's own micros ARE the
    # canon's, so this min() is a no-op; the fixture's arbitrary anchor makes it visible.
    assert out["sizing_micros"] == 8
    sizing = [json.loads(x) for x in (tmp_path / "sizing.jsonl").read_text().splitlines()]
    assert sizing[0]["micros"] == 8 and sizing[0]["conviction"] == 1.0
    spine = [json.loads(x) for x in (tmp_path / "spine.jsonl").read_text().splitlines()]
    assert any(e.get("event") == "guard_report" for e in spine)
    assert any(e.get("event") == "shadow_place" for e in spine)   # disarmed


def test_dd_ramp_halves_size_below_1k_of_room(tmp_path):
    """REBUILT CANON ramp: below $1,000 of available DD the base HALVES (remove-risk-only).
    It no longer tapers linearly to zero at $100 — that was the old canon's rule, measured on
    the broken book. The floor beneath this ramp is now the spine's $100 hard DD halt."""
    inst = build_shadow_instrument(tmp_path)
    # $800 of room: base halves ($150 -> $75) -> 75/(10*2) = 3.75 -> 4 micros
    in_ramp = AccountState(equity=50_800, trailing_floor=50_000, day_pnl=0, open_positions=0)
    out = inst.observe_verdict(_verdict(_ts("08:20")), in_ramp, _good_feed(), now_epoch=0.0)
    assert out["sizing_micros"] == 4
    sizing = [json.loads(x) for x in (tmp_path / "sizing.jsonl").read_text().splitlines()]
    assert sizing[-1]["micros"] == 4 and sizing[-1]["micros_anchor"] == 10

    # at/above $1,000 the ramp is inert; the schedule (not the ramp) sets the size
    healthy = AccountState(equity=52_000, trailing_floor=50_000, day_pnl=0, open_positions=0)
    out2 = inst.observe_verdict(_verdict(_ts("08:30")), healthy, _good_feed(), now_epoch=0.0)
    assert out2["sizing_micros"] == 8          # $150 / (10 * $2) = 7.5 -> 8


def test_schedule_never_sizes_a_trade_to_zero(tmp_path):
    """Canon micros floor at 1: a trade is taken at >=1 micro or not at all. The dd_ramp_zero
    path stays as a defensive floor but the schedule can no longer reach it."""
    inst = build_shadow_instrument(tmp_path)
    deep = AccountState(equity=50_150, trailing_floor=50_000, day_pnl=0, open_positions=0)
    out = inst.observe_verdict(_verdict(_ts("08:25")), deep, _good_feed(), now_epoch=0.0)
    assert out["sizing_micros"] >= 1 and out["decision"] != "dd_ramp_zero"


def test_observe_verdict_records_reject_on_bad_feed(tmp_path):
    inst = build_shadow_instrument(tmp_path)
    stale = FeedHealth(last_tick_age_ms=9_000, crossed_or_locked=False,
                       context_complete=True, spread_rel=1.0)
    inst.observe_verdict(_verdict(_ts("08:20")), _good_acct(), stale, now_epoch=0.0)
    rej = [json.loads(x) for x in (tmp_path / "rejects.jsonl").read_text().splitlines()]
    assert rej and rej[0]["code"] == "feed_stale"


# --------------------------------------------------------------------------- verdict-driven loop
def _live(tmp_path, source, comparator=None, comp_sink=None):
    return RouteBLive(
        feed=SierraFileFeed(tmp_path / "none.scid"), data_dir=tmp_path,
        verdict_source=source, verdict_sink=JsonlSink(tmp_path / "verdicts.jsonl"),
        decision_sink=JsonlSink(tmp_path / "decisions.jsonl"),
        instrument=build_shadow_instrument(tmp_path), ingestor=CanonIngestor(book=DepthBook()),
        acct_fn=constant_account_fn(52_000, 50_000),
        comparator=comparator, comparator_sink=comp_sink)


def test_dispatch_emits_verdict_at_fill_time(tmp_path):
    fill = _ts("08:01")
    src = FixtureVerdictSource({"2026-03-17": [_verdict(fill)]})
    live = _live(tmp_path, src)
    events = [
        {"kind": "minute", "ts": _ts("08:00"), "bar": _bar(_ts("08:00")), "tape": _tape()},
        {"kind": "minute", "ts": _ts("08:01"), "bar": _bar(_ts("08:01")), "tape": _tape()},
    ]
    emitted = live.dispatch(events, now=_ts("08:01"))
    assert src.asked == ["2026-03-17"]                # verdicts loaded once on the session roll
    assert len(emitted) == 1                          # emitted when its fill bar (08:01) passed
    verdicts = [json.loads(x) for x in (tmp_path / "verdicts.jsonl").read_text().splitlines()]
    assert verdicts[0]["type"] == "verdict" and verdicts[0]["micros"] == 10
    assert (tmp_path / "sizing.jsonl").exists()        # spine driven by the verdict


def test_verdict_not_emitted_before_its_fill(tmp_path):
    src = FixtureVerdictSource({"2026-03-17": [_verdict(_ts("08:05"))]})   # fill after the bars
    live = _live(tmp_path, src)
    events = [{"kind": "minute", "ts": _ts("08:00"), "bar": _bar(_ts("08:00")), "tape": _tape()}]
    assert live.dispatch(events, now=_ts("08:00")) == []
    assert not (tmp_path / "verdicts.jsonl").exists()


def test_comparator_writes_only_canary_never_journal_or_spine(tmp_path):
    # champion completes a trade on 08:00; it must reach the canary, NOT verdicts/sizing/spine.
    champ_trade = SimpleNamespace(trade_date="2026-03-17", fill_ts="2026-03-17T08:00:00-04:00",
                                  direction="long", entry=18000.0, dollars=42.0)
    comp = FakeComparator(trades_on={str(_ts("08:00")): [champ_trade]})
    canary = []
    src = FixtureVerdictSource({})                     # no canon verdicts
    live = _live(tmp_path, src, comparator=comp, comp_sink=canary.append)
    live.dispatch([{"kind": "minute", "ts": _ts("08:00"), "bar": _bar(_ts("08:00")),
                    "tape": _tape()}], now=_ts("08:00"))
    assert canary and canary[0]["lane"] == "champion" and canary[0]["dollars"] == 42.0
    assert not (tmp_path / "verdicts.jsonl").exists()  # champion never touches the verdict journal
    assert not (tmp_path / "sizing.jsonl").exists()    # nor the spine


def test_shadow_placement_reaches_the_lifecycle_with_a_synthetic_ref(tmp_path):
    """The armed-path assembly seam: a verdict the disarmed spine would PLACE is handed to
    the TradeLifecycle under a synthetic shadow ref, so the order-watch's would-be cancels
    become §D evidence — with the broker still a _NoBroker (zero calls possible)."""
    from src.live.trade_lifecycle import TradeLifecycle
    rows = []
    lc = TradeLifecycle(armed=False, account="FUNDED", journal=rows.append)
    fill = _ts("08:01")
    src = FixtureVerdictSource({"2026-03-17": [_verdict(fill)]})
    live = _live(tmp_path, src)
    live.lifecycle = lc
    live.dispatch([
        {"kind": "minute", "ts": _ts("08:00"), "bar": _bar(_ts("08:00")), "tape": _tape()},
        {"kind": "minute", "ts": _ts("08:01"), "bar": _bar(_ts("08:01")), "tape": _tape()},
    ], now=_ts("08:01"))
    resting = [r for r in rows if r["event"] == "entry_resting"]
    assert len(resting) == 1
    assert resting[0]["ref"].startswith("shadow:") and resting[0]["executed"] is False
    assert resting[0]["entry"] == 18000.0 and resting[0]["side"] == "B"
    # 08:01 NY is in-window and the bar (high 100) never ran above the long limit, so the
    # watch keeps watching — this also pins that UTC-stamped live bars evaluate as NY
    # wall-clock (the naive read made 12:01Z look past the window's end).
    assert [r for r in rows if r["event"] == "order_watch"] == []
    assert lc.watch.watching == [resting[0]["ref"]] and not lc.halted


# --------------------------------------------------------------------------- roll tag
def test_roll_bar_writes_decision(tmp_path):
    src = FixtureVerdictSource({})
    live = RouteBLive(feed=SierraFileFeed(tmp_path / "none.scid"), data_dir=tmp_path,
                      verdict_source=src, decision_sink=JsonlSink(tmp_path / "decisions.jsonl"),
                      ingestor=CanonIngestor(book=DepthBook()),
                      roll_state=RollState(), alerts=SimpleNamespace(say=lambda s: None))
    live.dispatch([
        {"kind": "minute", "ts": _ts("12:00", "2026-09-15"), "bar": _bar(_ts("12:00", "2026-09-15")),
         "tape": _tape()},
        {"kind": "minute", "ts": _ts("12:00", "2026-09-16"), "bar": _bar(_ts("12:00", "2026-09-16")),
         "tape": _tape()},
    ], now=_ts("12:00", "2026-09-16"))
    decs = [json.loads(x) for x in (tmp_path / "decisions.jsonl").read_text().splitlines()]
    roll = next(d for d in decs if d.get("type") == "roll")
    assert roll["to"] == "NQZ26" and roll["from"] == "NQU26"


# --------------------------------------------------------------------------- roll state
def test_roll_state_tracks_sessions_and_context():
    rs = RollState()
    assert rs.on_bar(_ts("12:00", "2026-09-15"))["roll"] is False
    b = rs.on_bar(_ts("12:00", "2026-09-16"))
    assert b["roll"] is True and b["from"] == "NQU26"
    assert rs.roll_sessions == {"2026-09-16"}
    assert rs.context_for_day("2026-09-16") == {"roll": True, "contract": "NQZ26"}


# --------------------------------------------------------------------------- serve stop/stall
def test_serve_stops_on_stop_fn(tmp_path):
    sp = tmp_path / "nq.scid"
    _scid(sp)
    comp = FakeComparator()
    live = RouteBLive(feed=SierraFileFeed(sp, clock=lambda: _ts("08:02:05")), data_dir=tmp_path,
                      verdict_source=FixtureVerdictSource({}), ingestor=CanonIngestor(book=DepthBook()),
                      comparator=comp)
    live.serve(sleep_fn=lambda s: None, stop_fn=lambda: True)
    assert comp.finalized is True


def test_serve_halts_on_stall(tmp_path):
    sp = tmp_path / "nq.scid"
    _scid(sp)
    live = RouteBLive(feed=SierraFileFeed(sp, clock=lambda: _ts("10:00")), data_dir=tmp_path,
                      verdict_source=FixtureVerdictSource({}), ingestor=CanonIngestor(book=DepthBook()),
                      clock=lambda: _ts("10:00"))
    live.serve(sleep_fn=lambda s: None, max_polls=5)   # stalled -> breaks before max_polls


def test_stale_verdicts_skipped_on_catchup_never_reach_the_spine(tmp_path):
    """THE ARMING-SAFETY GUARD (found live 2026-07-27): a boot catch-up over a backlog file
    replays months of bars through dispatch; every historical session's verdicts would
    re-emit as if fresh — armed, stale intents reach the broker. A verdict whose fill is
    older than STALE_VERDICT_S vs the WALL CLOCK is journaled as a skip and acts on nothing."""
    fill = _ts("08:01")
    src = FixtureVerdictSource({"2026-03-17": [_verdict(fill)]})
    live = _live(tmp_path, src)
    events = [
        {"kind": "minute", "ts": _ts("08:00"), "bar": _bar(_ts("08:00")), "tape": _tape()},
        {"kind": "minute", "ts": _ts("08:01"), "bar": _bar(_ts("08:01")), "tape": _tape()},
    ]
    months_later = pd.Timestamp("2026-07-27 06:00", tz=NY).tz_convert("UTC")
    emitted = live.dispatch(events, now=months_later)
    assert emitted == []                                # nothing acted on
    assert not (tmp_path / "verdicts.jsonl").exists()   # never reached the verdict journal
    assert not (tmp_path / "sizing.jsonl").exists()     # never reached the spine
    dec = [json.loads(x) for x in (tmp_path / "decisions.jsonl").read_text().splitlines()]
    skips = [d for d in dec if d.get("type") == "verdict_stale_skipped"]
    assert len(skips) == 1 and skips[0]["age_s"] > RouteBLive.STALE_VERDICT_S


def test_historical_roll_bars_journal_but_do_not_alert(tmp_path):
    """Catch-up ingest announced MARCH's contract roll at boot as if live (on-box
    2026-07-27). Historical roll bars journal for the gate partition; only a roll in the
    CURRENT session alerts."""
    class _Say:
        def __init__(self):
            self.msgs = []

        def say(self, text):
            self.msgs.append(text)

    say = _Say()
    live = _live(tmp_path, FixtureVerdictSource({}))
    live.alerts = say
    # March roll day bars replayed at a July wall clock: journal yes, alert no
    d1 = _ts("08:00", day="2026-03-17")
    d2 = _ts("08:00", day="2026-03-18")
    events = [{"kind": "minute", "ts": t, "bar": _bar(t), "tape": _tape()} for t in (d1, d2)]
    live.dispatch(events, now=pd.Timestamp("2026-07-27 06:00", tz=NY).tz_convert("UTC"))
    dec = [json.loads(x) for x in (tmp_path / "decisions.jsonl").read_text().splitlines()]
    assert any(d.get("type") == "roll" for d in dec)    # journaled for the partition
    assert say.msgs == []                               # but not announced as live
