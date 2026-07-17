"""Tests for src/engine/triggers.py — rejection block / displacement detection (Step 6).

Hand-built candles for each trigger + MTF arbitration, plus integration checks on the
committed Feb 9-11 slice (self-contained): a trigger must exist near the Feb 11 09:48
reference trade, and the MAPPED reference bar must fire the reference direction.

Labeling convention (see triggers.py docstring): the hand log / TradingView label candles
by OPEN time, engine bars by CLOSE — hand "09:48 3M" = engine 3min bar stamped 09:51.
"""
from datetime import time
from pathlib import Path

import pandas as pd

from src.engine.indicators import IndicatorsConfig
from src.engine.triggers import (
    Trigger,
    _htf_flag,
    _level_groups,
    _mtf_arbitrate,
    _test_candle,
    detect_triggers,
)

NY = "America/New_York"
FIX = Path(__file__).parent / "fixtures"
DISP = {"min_levels_through": 2, "body_range_min": 0.6, "close_extreme_quartile": 0.25,
        "atr_floor_enabled": False, "atr_floor_k": 1.0, "atr_length": 20}
MIN_TYPES = 2


def _candle(o, h, lo, c):
    return pd.Series({"open": o, "high": h, "low": lo, "close": c})


def _group(*lv):  # lv = (name, price, type)
    return list(lv)


# ------------------------------------------------------------------ level groups

def test_level_group_requires_two_types():
    two_types = [("bb_1m", 100.0, "bb"), ("dvwap_mid", 102.0, "vwap")]
    one_type = [("bb_1m", 100.0, "bb"), ("bb_2m", 101.0, "bb")]
    assert len(_level_groups(two_types, 10.0, MIN_TYPES)) == 1
    assert len(_level_groups(one_type, 10.0, MIN_TYPES)) == 0   # single type -> not a cluster
    assert len(_level_groups(two_types, 1.0, MIN_TYPES)) == 0   # too far apart for tolerance


def test_level_group_total_span_bounded_by_tolerance():
    # single-linkage would chain 100-108-116 (adjacent gaps 8 <= tol) into a 16-pt "cluster";
    # §3 "within proximity tolerance" bounds the TOTAL span instead
    lv = [("a", 100.0, "bb"), ("b", 108.0, "vwap"), ("c", 116.0, "poc")]
    groups = _level_groups(lv, 10.0, MIN_TYPES)
    assert len(groups) == 1
    assert [n for n, _, _ in groups[0]] == ["a", "b"]           # 116 starts a new (dropped) group
    for g in groups:
        ps = [p for _, p, _ in g]
        assert max(ps) - min(ps) <= 10.0


# ------------------------------------------------------------------ rejection block

def test_rejection_block_long():
    g = _group(("bb", 100.0, "bb"), ("vwap", 102.0, "vwap"))     # cluster [100,102]
    # lower wick into cluster (low 99), body above all (open/close > 102), closes above
    res = _test_candle(_candle(103.0, 104.0, 99.0, 103.5), [g], DISP, 0.0)
    assert res["kind"] == "rejection_block" and res["direction"] == "long"
    assert res["stop_ref"] == 99.0                                # stop beyond the wick

def test_rejection_block_short():
    g = _group(("bb", 100.0, "bb"), ("vwap", 102.0, "vwap"))
    # upper wick into cluster (high 101), body below all, closes below
    res = _test_candle(_candle(99.0, 101.0, 96.0, 97.0), [g], DISP, 0.0)
    assert res["kind"] == "rejection_block" and res["direction"] == "short"
    assert res["stop_ref"] == 101.0

def test_no_trigger_when_close_inside_cluster():
    g = _group(("bb", 100.0, "bb"), ("vwap", 102.0, "vwap"))
    # closes at 101 — not back on either side of ALL levels
    assert _test_candle(_candle(100.5, 102.5, 99.5, 101.0), [g], DISP, 0.0) is None


# ------------------------------------------------------------------ displacement

def test_displacement_long_through_two_cluster_levels():
    g = _group(("bb", 100.0, "bb"), ("vwap", 101.0, "vwap"))
    # body 99->102.5 engulfs up through 100 and 101; strong body; close in top quartile
    res = _test_candle(_candle(99.0, 102.6, 98.9, 102.5), [g], DISP, 0.0)
    assert res["kind"] == "displacement" and res["direction"] == "long"
    assert res["entry_ref"] == 101.0        # penetrated level NEAREST the close (§5 E3)
    assert res["count"] == 2                # distinct types of the crossed cluster, not a constant

def test_displacement_needs_two_levels_of_one_cluster():
    g = _group(("bb", 100.0, "bb"), ("vwap", 101.0, "vwap"))
    # body 100.5->102.5 crosses only 101 (one level) -> not a displacement
    res = _test_candle(_candle(100.5, 102.6, 100.4, 102.5), [g], DISP, 0.0)
    assert res is None or res["kind"] != "displacement"

def test_displacement_ignores_levels_outside_any_cluster():
    # same-type levels 30 pts apart form NO cluster (§3) — crossing both must not fire
    lv = [("bb_1m", 100.0, "bb"), ("bb_5m", 130.0, "bb")]
    groups = _level_groups(lv, 10.0, MIN_TYPES)
    assert groups == []
    assert _test_candle(_candle(99.0, 140.5, 98.5, 140.0), groups, DISP, 0.0) is None

def test_displacement_confluence_count_counts_types():
    g = _group(("bb", 100.0, "bb"), ("vwap", 101.0, "vwap"), ("poc", 102.0, "poc"))
    res = _test_candle(_candle(99.0, 103.6, 98.9, 103.5), [g], DISP, 0.0)
    assert res["kind"] == "displacement" and res["count"] == 3

def test_displacement_body_ratio_floor():
    g = _group(("bb", 100.0, "bb"), ("vwap", 101.0, "vwap"))
    # crosses both levels but body/range small (long upper+lower wicks) -> rejected by B_min
    assert _test_candle(_candle(99.5, 108.0, 92.0, 101.5), [g], DISP, 0.0) is None

def test_displacement_nan_atr_rejected_when_floor_enabled():
    g = _group(("bb", 100.0, "bb"), ("vwap", 101.0, "vwap"))
    disp_on = dict(DISP, atr_floor_enabled=True)
    # NaN ATR = floor unevaluable -> conservative reject (never silently bypassed)
    assert _test_candle(_candle(99.0, 102.6, 98.9, 102.5), [g], disp_on, float("nan")) is None
    # with real ATR history the same candle passes the floor
    res = _test_candle(_candle(99.0, 102.6, 98.9, 102.5), [g], disp_on, 1.0)
    assert res is not None and res["kind"] == "displacement"


# ------------------------------------------------------------------ HTF flag + MTF

def test_htf_flag_mapping():
    assert _htf_flag("uptrend", "long") == "with_trend"
    assert _htf_flag("uptrend", "short") == "counter_trend"
    assert _htf_flag("range", "long") == "range"

def test_mtf_arbitration_highest_tf_wins():
    def mk(tf):
        return Trigger(ts="2026-02-11T09:48:00-05:00", tf=tf, direction="short",
                       kind="rejection_block", pattern="A", htf_flag="range", entry_ref=1.0,
                       stop_ref=2.0, wick_low=1.0, wick_high=2.0, cluster_center=1.5,
                       confluence_count=2, close=1.0)
    out = _mtf_arbitrate([mk("1min"), mk("5min"), mk("2min")])
    assert len(out) == 1 and out[0].tf == "5min"                 # highest TF wins (§1)


# ------------------------------------------------------------------ integration spot-check

def _slice():
    df = pd.read_csv(FIX / "snapshot_slice.csv")
    df["ts_event"] = pd.to_datetime(df["ts_event"], utc=True).dt.tz_convert(NY)
    return df

def _cfg():
    return IndicatorsConfig(bb_length=20, bb_mult=2.0, entry_tfs=["1min", "2min", "3min", "5min"],
                            ny_anchor=time(9, 30), ny_bands=[1, 2, 3], daily_anchor=time(18, 0),
                            daily_bands=[1, 2, 3], vwap_source="hlc3", vp_bin_points=0.25,
                            vp_value_area_pct=70, vp_weekly_enabled=False)

def test_spotcheck_trigger_exists_near_feb11_0948():
    df = _slice()
    trigs = detect_triggers(df, cfg=_cfg(),
                            start=pd.Timestamp("2026-02-11 09:30", tz=NY),
                            end=pd.Timestamp("2026-02-11 10:00", tz=NY), tol=10.0)
    ref = pd.Timestamp("2026-02-11 09:48", tz=NY)
    near = [t for t in trigs if abs((pd.Timestamp(t.ts) - ref).total_seconds()) <= 300]
    assert near, "spec Step-6 check: a trigger must exist near the Feb 11 09:48 reference trade"
    assert any(t.direction == "short" for t in near)             # reference-direction present nearby

def test_spotcheck_mapped_reference_bar_feb11_is_short():
    # hand log "Feb 11 09:48 3M short" is TV OPEN-labeled -> engine 3min bar CLOSE-labeled 09:51
    df = _slice()
    trigs = detect_triggers(df, cfg=_cfg(),
                            start=pd.Timestamp("2026-02-11 09:30", tz=NY),
                            end=pd.Timestamp("2026-02-11 10:00", tz=NY), tol=10.0)
    mapped = pd.Timestamp("2026-02-11 09:51", tz=NY)
    at = [t for t in trigs if pd.Timestamp(t.ts) == mapped]
    assert at and at[0].direction == "short", \
        "mapped reference bar (TV 09:48 3m = engine 09:51) must fire the reference SHORT"


# ------------------------------------------------------------------ no lookahead / closed bars

GATE_TS = pd.Timestamp("2026-02-11 09:48", tz=NY)

def test_no_lookahead_detect_triggers():
    # perturbing every 1m bar stamped AT/after the gate (the bar stamped GATE_TS is still
    # FORMING at GATE_TS — start-labeled) must leave triggers up to the gate unchanged
    df = _slice()
    start = pd.Timestamp("2026-02-11 09:30", tz=NY)
    base = detect_triggers(df, cfg=_cfg(), start=start, end=GATE_TS, tol=10.0)
    df2 = df.copy()
    future = df2["ts_event"] >= GATE_TS
    df2.loc[future, ["open", "high", "low", "close"]] += 500.0
    df2.loc[future, "volume"] *= 7
    got = detect_triggers(df2, cfg=_cfg(), start=start, end=GATE_TS, tol=10.0)
    assert [t.model_dump() for t in got] == [t.model_dump() for t in base]

def test_no_forming_bar_evaluated_on_truncated_data():
    # truncate mid-bin: the trailing partial resample bins must NOT be evaluated as closed
    df = _slice()
    cut = pd.Timestamp("2026-02-11 09:46", tz=NY)
    df2 = df[df["ts_event"] <= cut]
    trigs = detect_triggers(df2, cfg=_cfg(),
                            start=pd.Timestamp("2026-02-11 09:30", tz=NY),
                            end=pd.Timestamp("2026-02-11 09:55", tz=NY), tol=10.0)
    last_closed = cut + pd.Timedelta(minutes=1)  # 1m bars are start-labeled
    assert all(pd.Timestamp(t.ts) <= last_closed for t in trigs)
