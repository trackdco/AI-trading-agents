"""Tests for src/backtest/event_timing.py — the v0.6 R1/R2 event-day timing floor."""

from types import SimpleNamespace

import pandas as pd

from src.backtest.event_timing import apply_timing_floor, event_entry_floor

NY = "America/New_York"


def _cal(rows):
    return pd.DataFrame([{"datetime_ET": pd.Timestamp(ts, tz=NY), "impact": imp}
                         for ts, imp in rows])


def _trig(ts):
    return SimpleNamespace(ts=ts)


def test_r1_momentum_delays_early_release_by_10min():
    cal = _cal([("2026-03-06 08:30", "high")])          # NFP-class 08:30
    floor = event_entry_floor(cal, "momentum", delay_min=10)
    assert floor["2026-03-06"] == pd.Timestamp("2026-03-06 08:40", tz=NY)
    # rotation book is NOT gated by an early release (R1 is momentum-only)
    assert event_entry_floor(cal, "rotation") == {}


def test_r2_rotation_blocks_prerelease_on_late_release():
    cal = _cal([("2026-03-24 10:00", "high")])          # 10:00 flash PMI-class
    floor = event_entry_floor(cal, "rotation")
    assert floor["2026-03-24"] == pd.Timestamp("2026-03-24 10:00", tz=NY)   # no delay, block pre
    # momentum book is NOT gated by a late release (R2 is rotation-only)
    assert event_entry_floor(cal, "momentum") == {}


def test_buckets_do_not_overlap_0931_to_0959_ungated():
    cal = _cal([("2026-05-01 09:45", "high")])          # falls in neither bucket
    assert event_entry_floor(cal, "momentum") == {}
    assert event_entry_floor(cal, "rotation") == {}


def test_afternoon_release_never_gates_the_morning():
    cal = _cal([("2026-03-17 14:00", "high")])          # FOMC 14:00, after the window
    assert event_entry_floor(cal, "momentum") == {}
    assert event_entry_floor(cal, "rotation") == {}


def test_latest_gating_release_wins_same_day():
    cal = _cal([("2026-03-06 08:30", "high"), ("2026-03-06 09:15", "high")])
    floor = event_entry_floor(cal, "momentum", delay_min=10)
    assert floor["2026-03-06"] == pd.Timestamp("2026-03-06 09:25", tz=NY)   # max(08:40, 09:25)


def test_low_impact_release_does_not_gate():
    cal = _cal([("2026-03-06 08:30", "medium")])
    assert event_entry_floor(cal, "momentum") == {}


def test_apply_floor_drops_pre_release_triggers_only():
    floor = {"2026-03-06": pd.Timestamp("2026-03-06 08:40", tz=NY)}
    trigs = [_trig("2026-03-06T08:35:00-05:00"),    # pre-floor -> dropped
             _trig("2026-03-06T08:45:00-05:00"),    # post-floor -> kept
             _trig("2026-03-09T09:00:00-04:00")]    # ungated day -> kept
    kept = apply_timing_floor(trigs, floor)
    assert [t.ts for t in kept] == ["2026-03-06T08:45:00-05:00", "2026-03-09T09:00:00-04:00"]


def test_empty_floor_is_byte_identical_passthrough():
    trigs = [_trig("2026-03-06T08:35:00-05:00"), _trig("2026-03-06T08:45:00-05:00")]
    kept = apply_timing_floor(trigs, {})
    assert kept == trigs and kept is not trigs        # unchanged content, fresh list


def test_book_arg_validated():
    import pytest
    with pytest.raises(ValueError):
        event_entry_floor(_cal([]), "both")
