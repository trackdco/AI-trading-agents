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


def test_arm_without_angus_file_is_refused_never_shadow(tmp_path, monkeypatch):
    """R13 is certified (practice day 4) so the wiring gate is gone — but --arm remains
    two-party fail-closed: without config/arming.yaml (Angus's commit) the token can
    never verify and the build hard-exits. A refused arm never falls back to shadow."""
    from scripts.ny_run import build_ny_live
    import logging
    monkeypatch.setenv("ARM_TOKEN", "not-the-phrase")

    class _Alerts:
        def say(self, text):
            pass

    with pytest.raises(SystemExit, match="ARM REFUSED"):
        build_ny_live({"feed": {"sierra": {"data_dir": str(tmp_path),
                                           "scid": str(tmp_path / "x.scid")}},
                       "paths": {}, "account": {"equity": 50_000.0},
                       "ny": {"buffer": 2_000.0}},
                      alerts=_Alerts(), log=logging.getLogger("t"), arm=True)


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


# ------------------------------------------------------- cancel/fill same-bar race (ny:20)
def test_same_bar_fill_beats_gate_cancel_and_scratches_flat(tmp_path):
    """Practice day 3, ny:2026-07-31:20 done right: the bar that touches the resting
    limit is the same bar whose re-evaluation withdraws the candidate. Fills are
    processed FIRST in dispatch, so the fill routes to the runner's fill-minute gate,
    which refuses -> scratch -> broker flat. Nothing is orphaned, everything journaled."""
    from src.live.ny_execution import DryRunBroker, NYExecution
    ing = FakeIngestor()
    lane = NYLane(ingestor=ing, profile=LUCID)
    runner = NYRunner(lane=lane)
    instrument = build_shadow_instrument(tmp_path, account="FUNDED", cfg=SpineConfig(),
                                         kill_file=tmp_path / "KILL", broker=None)
    det = StubDetector()
    bk = DryRunBroker()
    exe = NYExecution(mode="dryrun", broker=bk)
    lv = NYLive(feed=FakeFeed(), data_dir=tmp_path, runner=runner, detector=det,
                ingestor=ing, instrument=instrument, buffer=5_000.0,
                execution=exe,
                decision_sink=Sink(), action_sink=Sink(), verdict_sink=Sink(),
                fixture_sink=Sink(), clock=lambda: lv._wall)
    lv._wall = _ts("09:45") + pd.Timedelta(minutes=1)

    det.script["09:45"] = [_trigger()]                 # long, limit 18000.10 -> 18000.0
    _drive(lv, "09:45", [_minute_event("09:45", low=18_002.0)])   # rests, no touch
    assert len(bk._orders) == 1 and bk.position("FUNDED") == 0

    # next bar: price trades through the limit AND the evaluation flips to refuse
    ing.feats = _feats(dep_wall_below_sz=0.1, dep_wall_above_sz=0.1,
                       dep_wall_below_d=0.1)
    _drive(lv, "09:46", [_minute_event("09:46", low=17_999.0)])

    types = [r.get("type") for r in lv.decision_sink]
    assert "scratch" in types or "rule_l_scratch" in types or "scratched" in types
    assert bk.position("FUNDED") == 0                  # flat, never naked
    assert not any(t == "dispatch_error" for t in types)
    # the fill was SEEN (routed), not silently dropped
    assert any(r.get("type") == "scratched" for r in lv.decision_sink)


# ---------------------------------------------------------------- R15: agents in the loop
def test_agent_desk_manages_a_dryrun_fill_end_to_end(tmp_path):
    """Full wiring: trigger -> place -> fill -> commit -> desk opens the trade ->
    scripted agent exits -> broker flat -> journal row written. The certified
    mechanical laws (fills-first, scratch, flatten) are untouched around it."""
    from src.live.agent_desk import AgentDesk
    from src.live.ny_execution import DryRunBroker, NYExecution
    ing = FakeIngestor()
    lane = NYLane(ingestor=ing, profile=LUCID)
    runner = NYRunner(lane=lane)
    instrument = build_shadow_instrument(tmp_path, account="FUNDED", cfg=SpineConfig(),
                                         kill_file=tmp_path / "KILL", broker=None)
    det = StubDetector()
    bk = DryRunBroker()
    exe = NYExecution(mode="dryrun", broker=bk, agent_managed=True)
    lv = NYLive(feed=FakeFeed(), data_dir=tmp_path, runner=runner, detector=det,
                ingestor=ing, instrument=instrument, buffer=5_000.0,
                execution=exe,
                decision_sink=Sink(), action_sink=Sink(), verdict_sink=Sink(),
                fixture_sink=Sink(), clock=lambda: lv._wall)
    lv._wall = _ts("09:45") + pd.Timedelta(minutes=1)

    def call_fn(prompt, session, *, cwd, spec=None, timeout=None):
        return '{"action":"exit_now","note":"scripted"}', "s1"

    lv.desk = AgentDesk(execution=exe, exit_cfg=None,
                        journal_path=tmp_path / "journal.jsonl",
                        transcripts_dir=tmp_path / "tr", runs_cwd=tmp_path,
                        journal_sink=lv.decision_sink, sync=True, call_fn=call_fn)

    det.script["09:45"] = [_trigger()]
    _drive(lv, "09:45", [_minute_event("09:45", low=18_002.0)])   # places, no touch
    _drive(lv, "09:46", [_minute_event("09:46", low=17_999.0)])   # fills -> commit
    assert "ny:2026-04-20:1" in lv.desk.trades                    # desk took the trade
    _drive(lv, "09:47", [_minute_event("09:47", low=18_001.0)])   # turn 0 -> exit pends
    _drive(lv, "09:48", [_minute_event("09:48", low=18_001.0)])   # executes
    t = lv.desk.trades.get("ny:2026-04-20:1")
    assert t is not None and t.done
    assert bk.position("FUNDED") == 0                             # broker flat
    lv.desk.finalize()
    import json as _json
    rows = [_json.loads(x) for x in (tmp_path / "journal.jsonl").read_text().splitlines()]
    assert rows and rows[0]["exit_reason"] == "agent_exit"
    types = [r.get("type") for r in lv.decision_sink]
    assert "agent_trade_open" in types and "agent_trade_settled" in types
    assert "dispatch_error" not in types


# ---------------------------------------------------------------- DTC idle keepalive
class _FakeDTCBroker:
    """A minimal live broker double that models the dead-socket incident: ensure_connected
    returns whatever the test script says, independent of any order call."""
    def __init__(self, script):
        self.script = list(script)          # list of bool results, consumed in order
        self.calls = 0

    def ensure_connected(self):
        self.calls += 1
        return self.script.pop(0) if self.script else self.script and self.script[-1]


def test_dtc_keepalive_fires_on_a_quiet_market_and_alerts_once_then_recovers(live):
    """The exact incident: the market is quiet (no dispatch calls the broker at all), the
    socket dies, and NOTHING before this fix would have noticed. Now poll_once's own
    cadence catches it, alerts once (not spammed), and alerts again on recovery."""
    lv, det = live
    lv.execution = SimpleNamespace(live=True, broker=_FakeDTCBroker([True, False, False, True]))
    said = []
    lv._say = said.append

    t0 = _ts("09:00")
    lv.poll_once(t0)                                    # connected: silent
    assert lv.execution.broker.calls == 1 and said == []

    t1 = t0 + pd.Timedelta(seconds=11)                   # past DTC_KEEPALIVE_S: checks again
    lv.poll_once(t1)                                     # -> False: goes down
    assert lv.execution.broker.calls == 2
    assert any("DOWN" in s for s in said)
    down_alerts = len(said)

    t2 = t1 + pd.Timedelta(seconds=11)                    # still down, but well under the
    lv.poll_once(t2)                                      # 5-minute repeat window -> no spam
    assert lv.execution.broker.calls == 3
    assert len(said) == down_alerts                       # no new alert

    t3 = t2 + pd.Timedelta(seconds=11)                     # recovers
    lv.poll_once(t3)
    assert lv.execution.broker.calls == 4
    assert any("RECOVERED" in s for s in said)
    assert any(r.get("type") == "dtc_reconnected" for r in lv.decision_sink)


def test_dtc_keepalive_throttles_to_its_own_cadence(live):
    """Two polls inside the same second must not double-hit the socket — the keepalive
    self-throttles to DTC_KEEPALIVE_S regardless of how often poll_once is called."""
    lv, det = live
    lv.execution = SimpleNamespace(live=True, broker=_FakeDTCBroker([True] * 10))
    lv.poll_once(_ts("09:00"))
    lv.poll_once(_ts("09:00") + pd.Timedelta(seconds=1))
    assert lv.execution.broker.calls == 1


def test_dtc_keepalive_is_a_noop_for_dryrun_and_shadow(live):
    """DryRunBroker/no-broker execution has no socket to keep alive — the check must not
    error or do anything when the object has no ensure_connected."""
    lv, det = live
    lv.poll_once(_ts("09:00"))          # default fixture execution: shadow, no broker attr
    lv.poll_once(_ts("09:00") + pd.Timedelta(seconds=20))   # nothing raises


# ---------------------------------------------------------------- market-calendar guard
def test_market_should_be_open_refuses_a_naive_timestamp():
    """2026-08-03 review: never GUESS a wall clock — matches FeedGuard.accept's own
    convention. A wrong guess here means a false halt or, worse, a false "expected
    closure" masking a genuine feed failure."""
    from scripts.ny_run import _market_should_be_open
    with pytest.raises(ValueError, match="tz-aware"):
        _market_should_be_open(pd.Timestamp("2026-04-20 09:30"))


def test_market_should_be_open_matches_real_cme_hours():
    from scripts.ny_run import _market_should_be_open
    NY_ = "America/New_York"
    cases = [
        ("2026-04-20 16:59", True), ("2026-04-20 17:05", False),
        ("2026-04-20 18:05", True), ("2026-04-24 17:30", False),
        ("2026-04-25 12:00", False), ("2026-04-26 17:00", False),
        ("2026-04-26 18:30", True), ("2026-04-20 09:30", True),
    ]
    for ts, expect in cases:
        assert _market_should_be_open(pd.Timestamp(ts, tz=NY_)) is expect, ts


def test_serve_idles_through_expected_closure_instead_of_halting(live):
    """The 24/7 audit finding: without the calendar check, ANY stale feed halts the loop
    — including the guaranteed-daily 17:00 ET maintenance break, which is why a human had
    to restart it every single session. Now: idle through it, one announcement, no halt."""
    lv, det = live
    lv.feed = FakeFeed()
    lv.guard.accept({"ts_event": _ts("16:55")})       # a bar just before the break
    said = []
    lv._say = said.append
    # 17:05 ET Monday: 10 min past that bar, inside the daily maintenance break -> expected
    lv.clock = lambda: _ts("17:05")
    stops = {"n": 0}

    def stop_fn():
        stops["n"] += 1
        return stops["n"] > 3
    lv.serve(sleep_fn=lambda s: None, stop_fn=stop_fn)
    assert not any("halting (fail closed)" in s for s in said)
    assert any("expected market closure" in s for s in said)
    assert sum("expected market closure" in s for s in said) == 1   # announced once, not spammed


def test_serve_still_halts_on_a_real_stall_during_market_hours(live):
    """The other half of the same fix: a stale feed WHILE the market should be open is
    still fatal — the calendar check narrows the exception, it does not remove the guard."""
    lv, det = live
    lv.feed = FakeFeed()
    lv.guard.accept({"ts_event": _ts("09:30")})       # a bar, then silence
    said = []
    lv._say = said.append
    lv.clock = lambda: _ts("09:35")     # 5 min later, well past stale_after, market open
    lv.serve(sleep_fn=lambda s: None, stop_fn=lambda: False)
    assert any("halting (fail closed)" in s for s in said)
    assert any(r.get("type") == "feed_stall_halt" for r in lv.decision_sink)


# ---------------------------------------------------------------- position reconciliation
class _FakeBrokerWithPosition:
    def __init__(self, position, ensure_ok=True):
        self._position = position
        self._ensure_ok = ensure_ok

    def position(self, account):
        if isinstance(self._position, Exception):
            raise self._position
        return self._position

    def ensure_connected(self):
        return self._ensure_ok


def test_reconcile_position_matches_is_silent(live):
    lv, det = live
    lv.execution = SimpleNamespace(live=True, account="FUNDED",
                                   broker=_FakeBrokerWithPosition(0))
    said = []
    lv._say = said.append
    assert lv._reconcile_position(_ts("09:00")) is True
    assert said == [] and lv._position_mismatch is False


def test_reconcile_position_mismatch_blocks_new_entries_not_existing_ones(live):
    from scripts.ny_run import _Position
    lv, det = live
    lv._positions["ny:1"] = _Position(ref="ny:1", direction="long", entry=18_000.0,
                                      stop=17_990.0, size=10, fill_ts=_ts("09:00"), pre=False)
    lv.execution = SimpleNamespace(live=True, account="FUNDED",
                                   broker=_FakeBrokerWithPosition(15))  # tracked 10, broker 15
    said = []
    lv._say = said.append
    ok = lv._reconcile_position(_ts("09:05"))
    assert ok is False and lv._position_mismatch is True
    assert any("mismatch" in s for s in said)
    types = [r.get("type") for r in lv.decision_sink]
    assert "position_mismatch" in types

    # a NEW placement is blocked...
    lv._execute([{"action": "place", "ref": "ny:new", "side": "B", "limit": 18_010.0,
                 "stop": 18_000.0, "size": 5}], _ts("09:06"))
    assert any(r.get("type") == "place_blocked_position_mismatch" for r in lv.decision_sink)

    # ...but a cancel still goes through (risk-reducing actions are never blocked)
    lv.execution.cancel = lambda ref, why: said.append(f"cancelled:{ref}")
    lv._execute([{"action": "cancel", "ref": "ny:1", "why": "test"}], _ts("09:07"))
    assert "cancelled:ny:1" in said


def test_reconcile_position_query_error_fails_closed(live):
    lv, det = live
    lv.execution = SimpleNamespace(live=True, account="FUNDED",
                                   broker=_FakeBrokerWithPosition(RuntimeError("DTC down")))
    ok = lv._reconcile_position(_ts("09:00"))
    assert ok is False and lv._position_mismatch is True
    assert any(r.get("type") == "position_reconcile_error" for r in lv.decision_sink)


def test_reconnect_recovery_triggers_reconciliation(live):
    """The exact incident-adjacent risk: the socket dies, something fills or stops while
    we're blind, it reconnects — reconciliation must run automatically at that moment."""
    lv, det = live
    from scripts.ny_run import _Position
    lv._positions["ny:1"] = _Position(ref="ny:1", direction="long", entry=18_000.0,
                                      stop=17_990.0, size=10, fill_ts=_ts("09:00"), pre=False)

    class _Flaky:
        def __init__(self):
            self.calls = 0

        def ensure_connected(self):
            self.calls += 1
            return self.calls > 1              # down once, then recovers

        def position(self, account):
            return 0                           # broker now shows FLAT (the stop fired blind)

    lv.execution = SimpleNamespace(live=True, account="FUNDED", broker=_Flaky())
    said = []
    lv._say = said.append
    lv.poll_once(_ts("09:00"))                                          # down
    lv.poll_once(_ts("09:00") + pd.Timedelta(seconds=11))               # recovers -> reconcile
    assert lv._position_mismatch is True        # tracked 10, broker 0 -> caught immediately
    assert any("RECOVERED" in s for s in said)
    assert any("mismatch" in s for s in said)


def test_arm_refused_when_broker_shows_an_untracked_position(tmp_path, monkeypatch):
    """2026-08-03 audit: a fresh process must never start managing money it can't first
    prove is flat. A crash-restart-while-in-a-trade (or a stale prior session) leaves an
    orphaned position at the broker; this process refuses rather than guessing at its
    entry/stop/direction from partial data."""
    import logging

    import scripts.ny_run as nr

    monkeypatch.setattr(nr, "verify_for_arming", lambda token, entrypoint=None: object())
    monkeypatch.setattr(nr, "build_armed_broker",
                        lambda cfg, auth, log: (_FakeBrokerWithPosition(3), None))
    monkeypatch.setenv("ARM_TOKEN", "whatever")

    class _Alerts:
        def say(self, text):
            pass

    with pytest.raises(SystemExit, match="existing FUNDED position"):
        nr.build_ny_live({"feed": {"sierra": {"data_dir": str(tmp_path),
                                              "scid": str(tmp_path / "x.scid")}},
                          "paths": {}, "account": {"equity": 50_000.0},
                          "ny": {"buffer": 2_000.0}},
                         alerts=_Alerts(), log=logging.getLogger("t"), arm=True)


def test_arm_proceeds_when_broker_confirms_flat(tmp_path, monkeypatch):
    """The non-error path: position() reports 0, arming continues past the check."""
    import logging

    import scripts.ny_run as nr

    monkeypatch.setattr(nr, "verify_for_arming", lambda token, entrypoint=None: object())
    monkeypatch.setattr(nr, "build_armed_broker",
                        lambda cfg, auth, log: (_FakeBrokerWithPosition(0), None))
    monkeypatch.setenv("ARM_TOKEN", "whatever")

    class _Alerts:
        def say(self, text):
            pass

    live = nr.build_ny_live(
        {"feed": {"sierra": {"data_dir": str(tmp_path), "scid": str(tmp_path / "x.scid")}},
         "paths": {}, "account": {"equity": 50_000.0}, "ny": {"buffer": 2_000.0}},
        alerts=_Alerts(), log=logging.getLogger("t"), arm=True)
    assert live.armed is True


# ---------------------------------------------------------------- trade-level alerts
def test_disarmed_run_stays_silent_on_placements_and_fills(live):
    """Shadow/practice runs must not page anyone's phone — only a placement FAILURE is
    loud unconditionally (that's the exact thing that went unnoticed for 9 hours)."""
    lv, det = live
    assert lv.armed is False
    said = []
    lv._say = said.append
    det.script["09:45"] = [_trigger()]
    _drive(lv, "09:45")
    ref = lv.action_sink[-1]["ref"]
    assert not any(s.startswith("PLACED") for s in said)
    lv.on_fill(ref, _ts("09:46"), 11)
    assert not any(s.startswith("FILLED") for s in said)
    lv._close_position(ref, pl=42.0, reason="test")
    assert not any(s.startswith("CLOSED") for s in said)


def test_armed_run_alerts_on_placed_filled_and_closed(live):
    lv, det = live
    lv.armed = True
    said = []
    lv._say = said.append
    det.script["09:45"] = [_trigger()]
    _drive(lv, "09:45")
    assert any(s.startswith("PLACED") for s in said)
    ref = lv.action_sink[-1]["ref"]
    lv.on_fill(ref, _ts("09:46"), 11)
    assert any(s.startswith("FILLED") and "LONG" in s for s in said)
    lv._close_position(ref, pl=137.5, reason="test")
    assert any(s.startswith("CLOSED") and "+137.50" in s for s in said)


def test_placement_failure_alerts_regardless_of_armed_state(live):
    """The exact incident: a failed order must page immediately, armed or not — it was
    silently journaled for 9 hours overnight and again mid-session before this fix."""
    lv, det = live
    said = []
    lv._say = said.append

    class _FailingExecution:
        live = False

        def place(self, ref, intent, trig):
            return False

        def poll_fills(self):
            return []

    lv.execution = _FailingExecution()
    det.script["09:45"] = [_trigger()]
    _drive(lv, "09:45")
    assert any("FAILED to place" in s for s in said)


def test_position_reconciliation_is_genuinely_periodic_not_reconnect_only(live):
    """2026-08-03 review finding: reconciliation originally ran ONLY right after a
    reconnect — a session with a perfectly stable connection never checked for drift at
    all. Now it must run on its own periodic cadence regardless of connection history."""
    lv, det = live
    checks = []

    class _StableButChecked:
        def ensure_connected(self):
            return True                     # never once drops the whole session

        def position(self, account):
            checks.append(1)
            return 0

    lv.execution = SimpleNamespace(live=True, account="FUNDED", broker=_StableButChecked())
    lv.poll_once(_ts("09:00"))
    assert len(checks) == 1, "must reconcile even with zero disconnects, ever"
    lv.poll_once(_ts("09:00") + pd.Timedelta(seconds=11))    # inside RECONCILE_INTERVAL_S
    assert len(checks) == 1, "must throttle to RECONCILE_INTERVAL_S, not every keepalive"
    lv.poll_once(_ts("09:00") + pd.Timedelta(seconds=61))    # past RECONCILE_INTERVAL_S
    assert len(checks) == 2


def test_transient_mismatch_self_heals_on_the_next_periodic_check(live):
    """A mismatch flagged by a ONE-OFF query hiccup must clear itself once the periodic
    recheck sees the broker actually agrees — no new disconnect required."""
    lv, det = live

    class _FlakyThenFine:
        def __init__(self):
            self.calls = 0

        def ensure_connected(self):
            return True                     # connection itself is fine throughout

        def position(self, account):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("transient blip")   # one-off, not a real drift
            return 0                                    # every call after: genuinely flat

    lv.execution = SimpleNamespace(live=True, account="FUNDED", broker=_FlakyThenFine())
    said = []
    lv._say = said.append
    lv.poll_once(_ts("09:00"))
    assert lv._position_mismatch is True                # the transient blip flags it
    lv.poll_once(_ts("09:00") + pd.Timedelta(seconds=61))   # next periodic recheck
    assert lv._position_mismatch is False                # self-healed, no new disconnect needed
    assert any("reconciled" in s for s in said)


def test_genuine_mismatch_keeps_reconfirming_and_stays_blocked(live):
    """The other half: a REAL, persistent mismatch must never auto-clear just because
    time passes — it stays blocked until the broker actually agrees again."""
    from scripts.ny_run import _Position
    lv, det = live
    lv._positions["ny:1"] = _Position(ref="ny:1", direction="long", entry=18_000.0,
                                      stop=17_990.0, size=10, fill_ts=_ts("09:00"), pre=False)
    lv.execution = SimpleNamespace(live=True, account="FUNDED",
                                   broker=_FakeBrokerWithPosition(0))  # persistently wrong
    said = []
    lv._say = said.append
    lv.poll_once(_ts("09:00"))
    assert lv._position_mismatch is True
    lv.poll_once(_ts("09:00") + pd.Timedelta(seconds=61))
    lv.poll_once(_ts("09:00") + pd.Timedelta(seconds=122))
    assert lv._position_mismatch is True                # never self-clears without agreement
    assert sum("mismatch" in s for s in said) == 1       # but doesn't spam a new alert each retry
