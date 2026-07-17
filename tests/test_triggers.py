"""Tests for src/engine/triggers.py — rejection block / displacement detection (Step 6).

Hand-built candles for each trigger + MTF arbitration, plus an integration spot-check on the
committed Feb 9-11 slice (self-contained): a trigger must exist near the Feb 11 09:48
reference trade (one of the four clearest reference trades in the spec's Step-6 check).
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
DISP = {"body_range_min": 0.6, "atr_floor_enabled": False, "atr_floor_k": 1.0, "atr_length": 20}


def _candle(o, h, lo, c):
    return pd.Series({"open": o, "high": h, "low": lo, "close": c})


def _group(*lv):  # lv = (name, price, type)
    return list(lv)


# ------------------------------------------------------------------ level groups

def test_level_group_requires_two_types():
    two_types = [("bb_1m", 100.0, "bb"), ("dvwap_mid", 102.0, "vwap")]
    one_type = [("bb_1m", 100.0, "bb"), ("bb_2m", 101.0, "bb")]
    assert len(_level_groups(two_types, 10.0)) == 1
    assert len(_level_groups(one_type, 10.0)) == 0          # single type -> not a cluster
    assert len(_level_groups(two_types, 1.0)) == 0          # too far apart for tolerance


# ------------------------------------------------------------------ rejection block

def test_rejection_block_long():
    g = _group(("bb", 100.0, "bb"), ("vwap", 102.0, "vwap"))     # cluster [100,102]
    # lower wick into cluster (low 99), body above all (open/close > 102), closes above
    res = _test_candle(_candle(103.0, 104.0, 99.0, 103.5), [g], sum([g], []), DISP, 0.0)
    assert res["kind"] == "rejection_block" and res["direction"] == "long"
    assert res["stop_ref"] == 99.0                                # stop beyond the wick

def test_rejection_block_short():
    g = _group(("bb", 100.0, "bb"), ("vwap", 102.0, "vwap"))
    # upper wick into cluster (high 101), body below all, closes below
    res = _test_candle(_candle(99.0, 101.0, 96.0, 97.0), [g], sum([g], []), DISP, 0.0)
    assert res["kind"] == "rejection_block" and res["direction"] == "short"
    assert res["stop_ref"] == 101.0

def test_no_trigger_when_close_inside_cluster():
    g = _group(("bb", 100.0, "bb"), ("vwap", 102.0, "vwap"))
    # closes at 101 — not back on either side of ALL levels
    assert _test_candle(_candle(100.5, 102.5, 99.5, 101.0), [g], sum([g], []), DISP, 0.0) is None


# ------------------------------------------------------------------ displacement

def test_displacement_long_through_two_levels():
    levels = [("bb", 100.0, "bb"), ("vwap", 101.0, "vwap")]
    # body 99->102.5 engulfs up through 100 and 101; strong body; close in top quartile
    res = _test_candle(_candle(99.0, 102.6, 98.9, 102.5), [], levels, DISP, 0.0)
    assert res["kind"] == "displacement" and res["direction"] == "long"

def test_displacement_needs_two_levels():
    levels = [("bb", 100.0, "bb"), ("vwap", 101.0, "vwap")]
    # body 100.5->102.5 crosses only 101 (one level) -> not a displacement
    assert _test_candle(_candle(100.5, 102.6, 100.4, 102.5), [], levels, DISP, 0.0) is None

def test_displacement_body_ratio_floor():
    levels = [("bb", 100.0, "bb"), ("vwap", 101.0, "vwap")]
    # crosses both levels but body/range small (long upper+lower wicks) -> rejected by B_min
    assert _test_candle(_candle(99.5, 108.0, 92.0, 101.5), [], levels, DISP, 0.0) is None


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
