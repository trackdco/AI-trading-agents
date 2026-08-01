"""ny_run.NYLive — the rebuilt canon's live loop, driven synthetically.

What this file pins is the ENTRYPOINT's own obligations (the runner/lane/scorer are proven
elsewhere): shadow placements flow through the spine disarmed (structurally orderless),
rule L withholds same-level same-direction placements while a position is open and
scratches a fill that lands inside the conflict window, rule J pads an opposing placement
to close + open and flattens at the flip, rule K flattens pre positions on the first bar
at/after 09:30, the catch-up guard feeds state but never acts on stale bars, and the
detector dedup never registers the same trigger twice.
"""
from __future__ import annotations

import json
from datetime import time as dtime
from types import SimpleNamespace

from pathlib import Path

import pandas as pd
import pytest

from scripts.ny_run import NYLive, _trigger_key
from src.canon.book import DepthBook
from src.canon.ingestor import CanonIngestor
from src.canon.ny_lane import NYLane
from src.canon.scorer_ny import LUCID
from src.canon.spine import SpineConfig
from src.live.ny_runner import NYRunner
from src.live.route_b import build_shadow_instrument

NY = "America/New_York"
DAY = "2026-04-20"


def _ts(hm: str) -> pd.Timestamp:
    return pd.Timestamp(f"{DAY} {hm}", tz=NY)


def _feats(**over) -> dict:
    f = {"dep_thick": 5.0, "dep_wall_below_d": 8.0, "dep_wall_above_d": 6.0,
         "dep_wall_below_sz": 9.0, "dep_wall_above_sz": 9.0,
         "ent_vs_vwap_sd_dir": 0.5, "fill_delta_conf": 1, "d15_conf": 1,
         "trigdens_30": 20.0, "bp5opp": 0, "lon_slope_d": 0.0,
         "on_extreme_age_day": 500.0}
    f.update(over)
    return f


class FakeIngestor:
    """feature_row-only ingestor (the lane's duck type) plus the loop's push surface."""
    def __init__(self, feats=None):
        self.feats = feats if feats is not None else _feats()
        self.book = DepthBook()
        self.bars = []

    def feature_row(self, fill_ts, entry, direction, trigger_times=None):
        return dict(self.feats)

    def on_bar(self, bar):
        self.bars.append(bar)

    def on_minute_tape(self, ts, delta, vol, vwp):
        pass

    def on_depth(self, event):
        self.book.apply(event)

    def bars_frame(self):
        return pd.DataFrame(self.bars)


class StubDetector:
    """Emits a scripted list of triggers at given bar minutes."""
    def __init__(self):
        self.script = {}                     # hm str -> list[trigger]

    def on_bar(self, df_1m, bar):
        return self.script.get(bar.ts_event.tz_convert(NY).strftime("%H:%M"), [])


class FakeFeed:
    def __init__(self):
        self.queue = []

    def poll_events(self):
        evs, self.queue = self.queue, []
        return evs

    def retarget_depth(self, p):
        pass

    def retarget_scid(self, p, depth_path=None):
        pass


class Sink(list):
    def __call__(self, row):
        self.append(row)


def _trigger(hm="09:45", direction="long", entry=18_000.10, stop=17_989.90, tf="1m"):
    return SimpleNamespace(ts=str(_ts(hm)), tf=tf, direction=direction, kind="rejection",
                           pattern="A", entry_ref=entry, stop_ref=stop,
                           close=entry + (5 if direction == "long" else -5),
                           level_stack="")


def _minute_event(hm, o=18_000.0, h=18_005.0, low=17_995.0, c=18_000.0, vol=100.0):
    ts = _ts(hm)
    return {"kind": "minute", "ts": ts,
            "bar": {"ts_event": ts, "open": o, "high": h, "low": low, "close": c,
                    "volume": vol},
            "tape": {"delta": 10.0, "vol": vol, "vwp": c}}


@pytest.fixture()
def live(tmp_path):
    ing = FakeIngestor()
    lane = NYLane(ingestor=ing, profile=LUCID)
    runner = NYRunner(lane=lane)
    instrument = build_shadow_instrument(tmp_path, account="FUNDED", cfg=SpineConfig(),
                                         kill_file=tmp_path / "KILL", broker=None)
    det = StubDetector()
    lv = NYLive(feed=FakeFeed(), data_dir=tmp_path, runner=runner, detector=det,
                ingestor=ing, instrument=instrument, buffer=5_000.0,
                decision_sink=Sink(), action_sink=Sink(), verdict_sink=Sink(),
                fixture_sink=Sink(),
                clock=lambda: lv._wall)          # controllable wall clock
    lv._wall = _ts("09:45") + pd.Timedelta(minutes=1)
    return lv, det


def _drive(lv, hm, events=None):
    """Advance the wall clock to the bar close and dispatch one minute."""
    lv._wall = _ts(hm) + pd.Timedelta(minutes=1, seconds=5)
    lv.dispatch(events if events is not None else [_minute_event(hm)], lv._wall)


# ---------------------------------------------------------------- shadow placement
def test_admissible_trigger_places_in_shadow_through_the_spine(live):
    lv, det = live
    det.script["09:45"] = [_trigger()]
    _drive(lv, "09:45")
    places = [a for a in lv.action_sink if a["action"] == "place"]
    assert len(places) == 1 and places[0]["armed"] is False
    assert lv.verdict_sink and lv.verdict_sink[-1]["take"] is True
    # the spine journaled a shadow decision, and no broker exists to touch
    assert lv.runner.status()["resting"] == 1


def test_fixture_streams_record_every_minute(live):
    lv, det = live
    _drive(lv, "09:45")
    kinds = {r["type"] for r in lv.fixture_sink}
    assert kinds == {"tape", "book"}


# ---------------------------------------------------------------- rule L
def test_rule_l_scratches_a_sibling_fill_and_advises_at_place(live):
    lv, det = live
    det.script["09:45"] = [_trigger()]
    _drive(lv, "09:45")
    ref = lv.action_sink[-1]["ref"]
    res = lv.on_fill(ref, _ts("09:46"), 11)
    assert res["action"] == "commit"
    assert len(lv._positions) == 1
    # sibling: same direction, entry within 3pt -> rests with an advisory, and its FILL
    # inside the conflict window is scratched (the measured fill-time predicate)
    det.script["09:47"] = [_trigger(hm="09:47", entry=18_001.60, stop=17_991.40)]
    _drive(lv, "09:47")
    assert any(r["type"] == "rule_l_conflict_at_place" for r in lv.decision_sink)
    ref2 = [a["ref"] for a in lv.action_sink if a["action"] == "place"][-1]
    assert ref2 != ref
    res2 = lv.on_fill(ref2, _ts("09:48"), 11)
    assert res2["action"] == "scratch" and "one_per_level" in res2["why"]
    assert any(r["type"] == "rule_l_scratch" for r in lv.decision_sink)
    assert len(lv._positions) == 1               # the sibling never became a position


def test_rule_l_same_stop_form_scratches_at_fill(live):
    lv, det = live
    det.script["09:45"] = [_trigger()]
    _drive(lv, "09:45")
    ref1 = lv.action_sink[-1]["ref"]
    # second candidate at a DIFFERENT level places fine...
    det.script["09:47"] = [_trigger(hm="09:47", entry=18_010.10, stop=18_000.10)]
    _drive(lv, "09:47")
    ref2 = [a["ref"] for a in lv.action_sink if a["action"] == "place"][-1]
    assert ref2 != ref1
    # ...but if the FIRST fills and then the second's level converges via the open
    # position (same stop), the second's fill is scratched
    lv.on_fill(ref1, _ts("09:48"), 11)
    lv._positions[ref1].stop = 18_000.00        # force the same-stop conflict form
    # (18_000.00 is ref2's tick-rounded bracket stop: 18_000.10 -> 18_000.00)
    res = lv.on_fill(ref2, _ts("09:49"), 11)
    assert res["action"] == "scratch" and "one_per_level" in res["why"]
    assert any(r["type"] == "rule_l_scratch" for r in lv.decision_sink)


# ---------------------------------------------------------------- rule J
def test_rule_j_pads_opposing_placement_and_flattens_at_flip(live):
    lv, det = live
    det.script["09:45"] = [_trigger()]
    _drive(lv, "09:45")
    ref1 = lv.action_sink[-1]["ref"]
    lv.on_fill(ref1, _ts("09:46"), 11)
    # opposing trigger: placement is padded close+open
    det.script["09:50"] = [_trigger(hm="09:50", direction="short",
                                    entry=18_020.10, stop=18_030.30)]
    _drive(lv, "09:50")
    assert any(r["type"] == "rule_j_padded" and r["close_pad"] == 11
               for r in lv.decision_sink)
    ref2 = [a["ref"] for a in lv.action_sink if a["action"] == "place"][-1]
    # the opposing FILL flattens the long and the short runs as its own trade
    res = lv.on_fill(ref2, _ts("09:51"), 22)
    assert res["action"] == "commit"
    assert any(r["type"] == "rule_j_flip" and r["closed"] == ref1
               for r in lv.decision_sink)
    assert ref1 not in lv._positions and ref2 in lv._positions


# ---------------------------------------------------------------- rule K
def test_rule_k_flattens_pre_positions_on_the_first_open_bar(live):
    from scripts.ny_run import _Position
    lv, det = live
    lv._wall = _ts("09:28") + pd.Timedelta(minutes=1)
    _drive(lv, "09:28")                          # establishes the session day
    ref = "ny:2026-04-20:1"
    lv._positions[ref] = _Position(ref=ref, direction="long", entry=18_000.0,
                                   stop=17_990.0, size=11, fill_ts=_ts("08:31"),
                                   pre=True)
    lv.runner._cands = getattr(lv.runner, "_cands", {})   # runner knows nothing of it;
    assert lv._positions[ref].pre is True
    _drive(lv, "09:28")
    assert ref in lv._positions                  # open through the 09:28 bar (closes 09:29)
    _drive(lv, "09:29")                          # this bar CLOSES at 09:30:00 — flatten now
    assert ref not in lv._positions
    assert any(r["type"] == "rule_k_flatten" and r["ref"] == ref
               for r in lv.decision_sink)


# ---------------------------------------------------------------- catch-up guard
def test_stale_bar_feeds_state_but_never_acts(live):
    lv, det = live
    det.script["09:45"] = [_trigger()]
    lv._wall = _ts("09:45") + pd.Timedelta(minutes=30)      # bar is 30 minutes old
    lv.dispatch([_minute_event("09:45")], lv._wall)
    assert any(r["type"] == "catchup_bar_skipped" for r in lv.decision_sink)
    assert not [a for a in lv.action_sink if a["action"] == "place"]
    assert len(lv.ingestor.bars) == 1            # state still built


# ---------------------------------------------------------------- dedup
def test_detector_dedup_registers_a_trigger_exactly_once(live):
    lv, det = live
    t = _trigger()
    det.script["09:45"] = [t]
    det.script["09:46"] = [t]                    # tail overlap re-emission
    _drive(lv, "09:45")
    _drive(lv, "09:46")
    places = [a for a in lv.action_sink if a["action"] == "place"]
    assert len(places) == 1
    assert lv.runner.status()["candidates"] == 1 if "candidates" in lv.runner.status() \
        else True


def test_trigger_key_distinguishes_tf_and_level():
    a, b = _trigger(tf="1m"), _trigger(tf="5m")
    assert _trigger_key(a) != _trigger_key(b)
    c = _trigger(entry=18_010.10)
    assert _trigger_key(_trigger()) != _trigger_key(c)


# ---------------------------------------------------------------- depth retarget retry
def test_depth_retarget_retries_until_the_days_file_appears(live, tmp_path):
    """A 07:00 boot predates Sierra creating the day's .depth — the retarget must keep
    retrying, not latch on the first miss (a latch leaves the session depthless)."""
    lv, det = live
    lv.data_dir = tmp_path
    calls = []
    lv.feed.retarget_depth = lambda p: calls.append(p)
    now = _ts("07:00")
    lv._maybe_retarget(now)                      # file absent -> no latch
    assert calls == [] and getattr(lv, "_depth_day", None) != "2026-04-20"
    # Sierra creates the file mid-session; the box's naming convention is discovered
    # by resolve_depth_path from siblings — write the default-pattern name for the day
    from src.canon.sierra_symbol import resolve_depth_path
    p = resolve_depth_path(tmp_path, now, day="2026-04-20")
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_bytes(b"")
    lv._maybe_retarget(now)
    assert calls and getattr(lv, "_depth_day") == "2026-04-20"
    assert any(r["type"] == "depth_retarget" for r in lv.decision_sink)


# ---------------------------------------------------------------- review fixes
def test_utc_bars_reach_the_detector_as_new_york_time(live):
    """Sierra stamps bars UTC; the detector band is ET wall time. The boundary must
    convert or the detector never fires in the session (review F2)."""
    lv, det = live
    seen = []
    det.on_bar = lambda df, bar: seen.append(bar.ts_event) or []
    ts_utc = _ts("09:45").tz_convert("UTC")
    ev = _minute_event("09:45")
    ev["ts"] = ts_utc
    ev["bar"]["ts_event"] = ts_utc
    _drive(lv, "09:45", events=[ev])
    assert seen and str(seen[0].tz) == "America/New_York"
    assert seen[0] == _ts("09:45")


def test_rule_l_scratch_releases_the_committed_risk(live):
    """A rule-L-scratched fill must not hold budget room all session (review D3)."""
    lv, det = live
    det.script["09:45"] = [_trigger()]
    _drive(lv, "09:45")
    ref1 = lv.action_sink[-1]["ref"]
    lv.on_fill(ref1, _ts("09:46"), 11)
    room_after_first = lv.runner.status()["room"]
    det.script["09:47"] = [_trigger(hm="09:47", entry=18_001.60, stop=17_991.40)]
    _drive(lv, "09:47")
    ref2 = [a["ref"] for a in lv.action_sink if a["action"] == "place"][-1]
    res = lv.on_fill(ref2, _ts("09:48"), 11)
    assert res["action"] == "scratch"
    assert lv.runner.status()["room"] == room_after_first


def test_kill_file_stops_the_serve_loop(live, tmp_path):
    lv, det = live
    kf = tmp_path / "KILL"
    kf.write_text("")
    lv.kill_file = kf
    lv.serve(sleep_fn=lambda s: None, max_polls=5)
    assert any(r["type"] == "kill_file_stop" for r in lv.decision_sink)


def test_backlog_bars_write_no_fixture_rows(live):
    """Boot replays the whole .scid tail; those bars build state but must not spam
    fixtures.jsonl (review F9)."""
    lv, det = live
    lv._wall = _ts("09:45") + pd.Timedelta(minutes=30)      # bar 30 minutes stale
    lv.dispatch([_minute_event("09:45")], lv._wall)
    assert lv.fixture_sink == []
    assert len(lv.ingestor.bars) == 1


def test_naive_fill_timestamp_is_refused(live):
    lv, det = live
    det.script["09:45"] = [_trigger()]
    _drive(lv, "09:45")
    ref = lv.action_sink[-1]["ref"]
    with pytest.raises(ValueError, match="tz-aware"):
        lv.on_fill(ref, pd.Timestamp("2026-04-20 09:46:00"), 11)


def test_arm_is_refused_until_r13_is_certified(tmp_path):
    """--arm must hard-exit BY CONSTRUCTION while the execution wiring is incomplete
    (review D1/D2/D5). A refused arm never falls back to a shadow run."""
    from scripts.ny_run import build_ny_live
    import logging
    with pytest.raises(SystemExit, match="R13"):
        build_ny_live({"feed": {"sierra": {"data_dir": str(tmp_path)}},
                       "paths": {}, "account": {"equity": 50_000.0},
                       "ny": {"buffer": 2_000.0}},
                      alerts=None, log=logging.getLogger("t"), arm=True)


# ---------------------------------------------------------------- dry-run end to end
def test_dryrun_place_fill_and_rule_k_flatten_reach_the_broker(live):
    """The practice-day loop: a placement reaches the DryRunBroker, its fill comes back
    through poll_fills into the runner's fill-minute gate, and the 09:30 flatten
    actually closes the position at the broker (R13's whole point)."""
    from src.live.ny_execution import DryRunBroker, NYExecution
    lv, det = live
    bk = DryRunBroker()
    lv.execution = NYExecution(mode="dryrun", broker=bk, journal=lv.decision_sink)
    lv.execution.on_closed = lv._on_execution_closed
    lv._wall = _ts("08:30") + pd.Timedelta(minutes=1)
    lv.ingestor.feats = _feats(dep_wall_below_d=float("nan"))   # pre window: W==1
    det.script["08:30"] = [_trigger(hm="08:30")]
    _drive(lv, "08:30", events=[_minute_event("08:30", low=18_002.0)])  # rests, no fill
    assert len(bk._orders) == 1 and bk.position("FUNDED") == 0
    # next bar trades through the limit -> broker fill -> poll -> runner commit
    _drive(lv, "08:31", events=[_minute_event("08:31", low=17_999.0)])
    placed_size = list(bk._orders.values())[0]["size"]
    assert bk.position("FUNDED") == placed_size > 0
    assert len(lv._positions) == 1 and len(lv.execution._positions) == 1
    ref = next(iter(lv._positions))
    assert lv._positions[ref].pre is True
    # the bar whose close is 09:30 flattens the pre position AT THE BROKER
    _drive(lv, "09:29", events=[_minute_event("09:29", low=18_003.0)])
    assert bk.position("FUNDED") == 0
    assert ref not in lv._positions and ref not in lv.execution._positions
    assert any(r.get("type") == "closed_now" and r.get("why") == "rule_k_flatten"
               for r in lv.decision_sink)


# ---------------------------------------------------------------- session findings 08-01
def test_future_stamped_bar_never_rolls_the_day(live):
    """A settlement record stamped hours ahead must not clear live day state
    (found in the 2026-07-31 shadow session: day rolled to 08-01 mid-afternoon)."""
    lv, det = live
    _drive(lv, "09:45")
    assert lv._day == "2026-04-20"
    future = _minute_event("09:46")
    fts = _ts("09:46") + pd.Timedelta(hours=9)          # stamped way in the future
    future["ts"] = fts
    future["bar"]["ts_event"] = fts
    lv._wall = _ts("09:46") + pd.Timedelta(minutes=1)
    lv.dispatch([future], lv._wall)
    assert lv._day == "2026-04-20"                       # day did NOT roll
    assert any(r["type"] == "day_roll_refused_future_bar" for r in lv.decision_sink)


def test_two_minute_late_bar_still_acts(live):
    """120-132s lag spikes clipped 17 real session minutes on 07-31 — the widened
    threshold must let a 2.5-minute-old bar act."""
    lv, det = live
    det.script["09:45"] = [_trigger()]
    lv._wall = _ts("09:45") + pd.Timedelta(seconds=150 + 60)
    lv.dispatch([_minute_event("09:45")], lv._wall)
    assert any(a["action"] == "place" for a in lv.action_sink)
    assert any(r["type"] == "trigger_seen" and r["placed"] for r in lv.decision_sink)


# ---------------------------------------------------------------- session-day boundary
def test_session_day_rolls_at_17_et_not_13_et(live):
    """R13 practice-day finding (2026-08-01): session_day fed raw UTC stamps rolled the
    trading day at 17:00 UTC = 1pm ET — Friday's live shadow started 'day 2026-08-01'
    mid-Friday-afternoon, clearing position state while the session was still trading.
    The boundary must be 17:00 ET (the real CME maintenance break)."""
    lv, det = live
    _drive(lv, "09:45")
    assert lv._day == DAY
    _drive(lv, "13:30")                     # 17:30 UTC — the OLD bug's roll instant
    assert lv._day == DAY                   # same session: NO roll at 1pm ET
    _drive(lv, "16:59")
    assert lv._day == DAY
    _drive(lv, "17:05")                     # past the maintenance break: real roll
    assert lv._day == "2026-04-21"


# ---------------------------------------------------------------- per-bar frame trim
def test_detector_frame_is_trimmed_to_warmup_horizon(live):
    """The full-history rebuild cost ~1 real minute per in-band bar on the box (3.5h
    replay). The frame handed to the detector starts at bar_ts - FRAME_WARMUP; trim
    parity vs the full frame is pinned empirically in scripts/check_trim_parity.py."""
    from scripts.ny_run import FRAME_WARMUP
    lv, det = live
    seen = {}
    orig = det.on_bar
    det.on_bar = lambda df, bar: seen.update(df=df, bar=bar) or orig(df, bar)
    old = _ts("09:00") - pd.Timedelta(days=30)
    lv.ingestor.bars.append({"ts_event": old, "open": 1.0, "high": 1.0,
                             "low": 1.0, "close": 1.0, "volume": 1.0})
    _drive(lv, "09:45")
    df = seen["df"]
    assert len(df)                                          # the fresh bar is present
    assert pd.to_datetime(df.ts_event).min() >= _ts("09:45") - FRAME_WARMUP
