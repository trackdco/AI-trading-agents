"""Tests for src/engine/indicators.py — BB, anchored VWAPs, volume profile (Spec 1, Step 4).

Hand-computed small fixtures throughout (code-standards: unit tests against
hand-computed fixtures). Includes the mandatory ``test_ny_vwap_absent_premarket``
and a no-lookahead test mirroring the spirit of ``test_no_lookahead``.
"""
import math

import numpy as np
import pandas as pd
import pytest

from src.engine.indicators import (
    IndicatorsConfig,
    bollinger,
    daily_vwap,
    indicators_asof,
    load_indicators_config,
    ny_vwap,
    profile_asof,
    volume_profile,
    weekly_profile_asof,
)

NY = "America/New_York"


def _bars(start_ny: str, ohlcv: list[tuple], freq: str = "1min") -> pd.DataFrame:
    idx = pd.date_range(pd.Timestamp(start_ny, tz=NY), periods=len(ohlcv), freq=freq)
    o, h, low, c, v = zip(*ohlcv)
    return pd.DataFrame({"ts_event": idx, "open": o, "high": h, "low": low,
                         "close": c, "volume": v})


def _flat_bars(start_ny: str, prices_volumes: list[tuple]) -> pd.DataFrame:
    """1m bars with open=high=low=close=p (zero range) — volume lands in one bin."""
    return _bars(start_ny, [(p, p, p, p, v) for p, v in prices_volumes])


CFG = IndicatorsConfig(
    bb_length=20, bb_mult=2.0, entry_tfs=["1min", "2min", "3min", "5min"],
    ny_anchor=pd.Timestamp("2026-01-01 09:30").time(), ny_bands=[1, 2, 3],
    daily_anchor=pd.Timestamp("2026-01-01 18:00").time(), daily_bands=[1, 2, 3],
    vwap_source="hlc3", vp_bin_points=0.25, vp_value_area_pct=70.0,
    vp_weekly_enabled=False,
)


# ------------------------------------------------------------------ Bollinger

def test_bollinger_hand_computed_population_stdev():
    # closes 10, 20, 30, 40 with length=3, mult=2:
    #   bar 3: SMA = (10+20+30)/3 = 20; population stdev = sqrt(((10-20)^2 + 0 + (30-20)^2)/3)
    #          = sqrt(200/3) = 8.16497 (sample stdev ddof=1 would be 10 — must NOT match)
    #   bar 4: SMA = 30, same stdev
    closes = [10, 20, 30, 40]
    df = _bars("2026-02-02 09:30", [(c, c + 1, c - 1, c, 5) for c in closes])
    bb = bollinger(df, length=3, mult=2.0)
    sd = math.sqrt(200 / 3)
    assert bb["basis"].iloc[0:2].isna().all()          # warm-up rows NaN
    assert bb["basis"].iloc[2] == pytest.approx(20.0)
    assert bb["upper"].iloc[2] == pytest.approx(20.0 + 2 * sd)
    assert bb["lower"].iloc[2] == pytest.approx(20.0 - 2 * sd)
    assert bb["basis"].iloc[3] == pytest.approx(30.0)
    assert bb["upper"].iloc[3] == pytest.approx(30.0 + 2 * sd)
    assert bb["upper"].iloc[3] != pytest.approx(30.0 + 2 * 10.0)   # ddof=1 would give this


def test_bollinger_validation_raises():
    df = _bars("2026-02-02 09:30", [(100, 101, 99, 100, 1)])
    with pytest.raises(ValueError):
        bollinger(df, length=0, mult=2.0)
    with pytest.raises(ValueError):
        bollinger(df, length=20, mult=-1.0)


# ------------------------------------------------------------------ anchored VWAP formula

def test_daily_vwap_hand_computed_volume_weighted_bands():
    # Three bars in one CME session (all after 18:00 anchor). hlc3 sources:
    #   bar1: (102+98+100)/3  = 100, vol 10
    #   bar2: (105+101+103)/3 = 103, vol 20
    #   bar3: (108+104+106)/3 = 106, vol 30
    # Running TradingView VWAP and VOLUME-WEIGHTED variance:
    #   after bar1: vwap = 1000/10 = 100;      var = 10*100^2/10 - 100^2 = 0
    #   after bar2: vwap = (1000+2060)/30 = 102
    #               var  = (10*10000 + 20*10609)/30 - 102^2 = 10406 - 10404 = 2
    #   after bar3: vwap = (3060+3180)/60 = 104
    #               var  = (312180 + 30*11236)/60 - 104^2 = 10821 - 10816 = 5
    df = _bars("2026-02-02 18:00", [(100, 102, 98, 100, 10),
                                    (103, 105, 101, 103, 20),
                                    (106, 108, 104, 106, 30)])
    dv = daily_vwap(df, bands=[1, 2, 3])
    assert list(dv["vwap"]) == pytest.approx([100.0, 102.0, 104.0])
    assert dv["upper_1"].iloc[0] == pytest.approx(100.0)              # zero variance
    assert dv["upper_1"].iloc[1] == pytest.approx(102.0 + math.sqrt(2))
    assert dv["lower_2"].iloc[1] == pytest.approx(102.0 - 2 * math.sqrt(2))
    assert dv["upper_1"].iloc[2] == pytest.approx(104.0 + math.sqrt(5))
    assert dv["upper_3"].iloc[2] == pytest.approx(104.0 + 3 * math.sqrt(5))
    # NOT a simple stdev of the three source prices around their mean:
    simple_sd = np.std([100, 103, 106])
    assert dv["upper_1"].iloc[2] != pytest.approx(104.0 + simple_sd)


def test_daily_vwap_resets_at_1800_anchor():
    # 16:58/16:59 close the old session; 18:00 starts the new one (data._session_date).
    old = _bars("2026-02-02 16:58", [(100, 100, 100, 100, 10), (200, 200, 200, 200, 10)])
    new = _bars("2026-02-02 18:00", [(300, 300, 300, 300, 10), (310, 310, 310, 310, 10)])
    dv = daily_vwap(pd.concat([old, new], ignore_index=True))
    assert dv["vwap"].iloc[0] == pytest.approx(100.0)
    assert dv["vwap"].iloc[1] == pytest.approx(150.0)   # (100*10+200*10)/20 — same session
    assert dv["vwap"].iloc[2] == pytest.approx(300.0)   # RESET: 18:00 bar starts fresh
    assert dv["vwap"].iloc[3] == pytest.approx(305.0)   # accumulates within the new session


# ------------------------------------------------------------------ NY VWAP (mandatory test)

def test_ny_vwap_absent_premarket():
    # MANDATORY (code-standards): NY VWAP is NaN for every bar before 09:30 ET and
    # non-NaN at/after 09:30. Bars 09:25..09:34, plus one at 16:59 (in) / 17:10 (out).
    rows = [(100 + i, 101 + i, 99 + i, 100 + i, 10) for i in range(10)]  # 09:25..09:34
    df = _bars("2026-02-02 09:25", rows)
    late = _bars("2026-02-02 16:59", [(100, 101, 99, 100, 5)])
    after = _bars("2026-02-02 17:10", [(100, 101, 99, 100, 5)])          # maintenance break
    df = pd.concat([df, late, after], ignore_index=True)
    nv = ny_vwap(df)
    t = df["ts_event"].dt.time
    pre = nv[(t < pd.Timestamp("2026-01-01 09:30").time()).to_numpy()]
    assert len(pre) == 5
    assert pre[["vwap", "upper_1", "lower_1", "upper_2", "lower_2",
                "upper_3", "lower_3"]].isna().all().all()
    ny_window = nv[((t >= pd.Timestamp("2026-01-01 09:30").time())
                    & (t < pd.Timestamp("2026-01-01 17:00").time())).to_numpy()]
    assert len(ny_window) == 6                                # 09:30..09:34 + 16:59
    assert ny_window["vwap"].notna().all()
    assert pd.isna(nv["vwap"].iloc[-1])                       # 17:10 bar: outside -> NaN
    # anchor excludes pre-market volume: first NY value = hlc3 of the 09:30 bar alone
    hlc3_0930 = (106 + 104 + 105) / 3
    assert nv["vwap"].iloc[5] == pytest.approx(hlc3_0930)


# ------------------------------------------------------------------ volume profile

def test_volume_profile_concentrated_poc_and_value_area_exact_70():
    # All range-less bars -> volume lands in exactly one 0.25-pt bin each.
    # 100.0 -> 70 vol, 101.0 -> 20, 102.0 -> 10. Total 100; POC = 100.0's bin.
    # Value area target = 70% of 100 = 70, covered by the POC bin alone -> VAH = VAL = POC.
    df = _flat_bars("2026-02-02 09:30", [(100.0, 70), (101.0, 20), (102.0, 10)])
    vp = volume_profile(df, bin_points=0.25, value_area_pct=70.0)
    poc_center = (math.floor(100.0 / 0.25) + 0.5) * 0.25       # = 100.125
    assert vp.poc == pytest.approx(poc_center)
    assert vp.vah == pytest.approx(poc_center)
    assert vp.val == pytest.approx(poc_center)
    assert vp.total_volume == pytest.approx(100.0)
    # HVN: 101.0's bin (20 > both zero neighbours). Edge bins (100.0, 102.0) excluded.
    assert vp.hvn == pytest.approx([(math.floor(101.0 / 0.25) + 0.5) * 0.25])


def test_volume_profile_uniform_distribution_across_bar_range():
    # One bar low=100.0 high=100.5 touches bins [100.0,100.25), [100.25,100.5), [100.5,100.75)
    # (inclusive of the bin containing the high) -> 30 volume spread as 10/10/10.
    df = _bars("2026-02-02 09:30", [(100.2, 100.5, 100.0, 100.4, 30)])
    vp = volume_profile(df, bin_points=0.25, value_area_pct=70.0)
    assert vp.bin_volumes == pytest.approx([10.0, 10.0, 10.0])
    assert vp.bin_centers == pytest.approx([100.125, 100.375, 100.625])
    assert vp.poc == pytest.approx(100.125)                    # tie -> lowest-price bin


def test_volume_profile_value_area_greedy_covers_70pct():
    # Bins: 99.75->10, 100.0->50 (POC), 100.25->30, 100.5->10. Total 100, target 70.
    # Greedy from POC: above (30) > below (10) -> add 100.25 bin; covered 80 >= 70. Stop.
    # VAH = 100.25's center, VAL = POC bin center.
    df = _flat_bars("2026-02-02 09:30",
                    [(99.75, 10), (100.0, 50), (100.25, 30), (100.5, 10)])
    vp = volume_profile(df, bin_points=0.25, value_area_pct=70.0)
    assert vp.poc == pytest.approx(100.125)
    assert vp.vah == pytest.approx(100.375)
    assert vp.val == pytest.approx(100.125)
    covered = sum(v for c, v in zip(vp.bin_centers, vp.bin_volumes)
                  if vp.val <= c <= vp.vah)
    assert covered >= 0.70 * vp.total_volume                   # >= 70% covered
    # LVN example: none strictly lower than both neighbours here (monotone slopes)
    assert vp.lvn == []


def test_volume_profile_validation_raises():
    df = _flat_bars("2026-02-02 09:30", [(100.0, 10)])
    with pytest.raises(ValueError):
        volume_profile(df.iloc[0:0], 0.25, 70.0)               # empty slice
    with pytest.raises(ValueError):
        volume_profile(df, 0.0, 70.0)                          # bad bin size
    with pytest.raises(ValueError):
        volume_profile(df, 0.25, 0.0)                          # bad value-area pct


def test_profile_asof_uses_only_closed_bars_and_scopes():
    # Session bars: 09:30 (vol 100 @ 100.0), 09:31 (vol 50 @ 101.0), 09:32 (forming at
    # ts=09:32? No — closed. Add 09:32 bar that must be EXCLUDED at ts=09:32).
    df = _flat_bars("2026-02-02 09:30", [(100.0, 100), (101.0, 50), (999.0, 999)])
    ts = pd.Timestamp("2026-02-02 09:32", tz=NY)
    vp = profile_asof(df, ts, "daily", 0.25, 70.0)
    # bar stamped 09:31 closes at 09:32 -> included; bar stamped 09:32 still forming -> excluded
    assert vp.total_volume == pytest.approx(150.0)
    assert 999.0 not in [round(c) for c in vp.bin_centers]
    ny = profile_asof(df, ts, "ny", 0.25, 70.0)
    assert ny.total_volume == pytest.approx(150.0)
    # NY scope excludes pre-9:30 bars that the daily scope includes
    pre = _flat_bars("2026-02-02 09:00", [(90.0, 40)])
    df2 = pd.concat([pre, df], ignore_index=True)
    assert profile_asof(df2, ts, "daily", 0.25, 70.0).total_volume == pytest.approx(190.0)
    assert profile_asof(df2, ts, "ny", 0.25, 70.0).total_volume == pytest.approx(150.0)
    with pytest.raises(ValueError):
        profile_asof(df, ts, "weekly", 0.25, 70.0)             # not a profile_asof scope


def test_weekly_profile_gated_behind_config_flag():
    df = _flat_bars("2026-02-02 09:30", [(100.0, 10), (100.0, 20)])
    ts = pd.Timestamp("2026-02-02 09:32", tz=NY)
    with pytest.raises(ValueError):                            # disabled (config default)
        weekly_profile_asof(df, ts, 0.25, 70.0, weekly_enabled=False)
    vp = weekly_profile_asof(df, ts, 0.25, 70.0, weekly_enabled=True)
    assert vp.total_volume == pytest.approx(30.0)


# ------------------------------------------------------------------ indicators_asof

def _asof_fixture() -> pd.DataFrame:
    # 08:00..10:29 on Wed 2026-02-04 (one CME session), deterministic wiggly series.
    rows = []
    for i in range(150):
        c = 100.0 + 5 * math.sin(i / 7) + (i % 5) * 0.25
        rows.append((c - 0.25, c + 0.75, c - 0.75, c, 100 + (i % 7) * 10))
    return _bars("2026-02-04 08:00", rows)


def test_indicators_asof_last_closed_bar_semantics():
    df = _asof_fixture()
    ts = pd.Timestamp("2026-02-04 09:48", tz=NY)
    snap = indicators_asof(df, ts, CFG)
    # 1m base frame is START-labeled: bar stamped 09:48 is still forming at 09:48,
    # so the last closed 1m bar is stamped 09:47 (closes at 09:48).
    assert snap["tfs"]["1min"]["bar_ts"] == pd.Timestamp("2026-02-04 09:47", tz=NY)
    # Resampled frames are CLOSE-labeled: 2m/3m bars stamped 09:48 are fully closed at 09:48.
    assert snap["tfs"]["2min"]["bar_ts"] == pd.Timestamp("2026-02-04 09:48", tz=NY)
    assert snap["tfs"]["3min"]["bar_ts"] == pd.Timestamp("2026-02-04 09:48", tz=NY)
    assert snap["tfs"]["5min"]["bar_ts"] == pd.Timestamp("2026-02-04 09:45", tz=NY)
    for tf in CFG.entry_tfs:                                   # >= 20 bars everywhere
        assert snap["tfs"][tf]["bb_basis"] is not None
        assert snap["tfs"][tf]["bb_upper"] > snap["tfs"][tf]["bb_basis"]
    # BB basis of the 1m TF == SMA(20) of the 20 closes ending at the 09:47 bar
    closed = df[df["ts_event"] <= ts - pd.Timedelta(minutes=1)]
    assert snap["tfs"]["1min"]["bb_basis"] == pytest.approx(
        closed["close"].iloc[-20:].mean())
    assert snap["daily_vwap"]["mid"] is not None
    assert snap["ny_vwap"]["mid"] is not None                  # post-9:30
    assert snap["daily_profile"]["poc"] is not None


def test_indicators_asof_ny_vwap_none_premarket():
    df = _asof_fixture()
    snap = indicators_asof(df, pd.Timestamp("2026-02-04 09:00", tz=NY), CFG)
    assert snap["ny_vwap"]["mid"] is None                      # pre-9:30: no NY VWAP
    assert all(v is None for v in snap["ny_vwap"].values())
    assert snap["daily_vwap"]["mid"] is not None               # daily VWAP always exists (§3)


def test_no_lookahead_indicators_asof():
    # Perturbing/appending bars strictly AFTER the last closed bar at T must not change
    # anything indicators_asof reports at T (mirrors tests/test_data no-lookahead spirit).
    df = _asof_fixture()
    ts = pd.Timestamp("2026-02-04 10:00", tz=NY)
    base = indicators_asof(df, ts, CFG)
    perturbed = df.copy()
    future = perturbed["ts_event"] >= ts                       # 10:00 bar is still forming
    for col in ("open", "high", "low", "close"):
        perturbed.loc[future, col] = 55555.0
    perturbed.loc[future, "volume"] = 1
    extra = _bars("2026-02-04 10:30", [(200.0, 300.0, 100.0, 250.0, 99999)] * 30)
    perturbed = pd.concat([perturbed, extra], ignore_index=True)
    assert indicators_asof(perturbed, ts, CFG) == base


def test_indicators_asof_rejects_naive_timestamp():
    with pytest.raises(ValueError):
        indicators_asof(_asof_fixture(), pd.Timestamp("2026-02-04 09:48"), CFG)


def test_load_indicators_config_matches_yaml():
    cfg = load_indicators_config()
    assert cfg.bb_length == 20 and cfg.bb_mult == 2.0
    assert cfg.entry_tfs == ["1min", "2min", "3min", "5min"]
    assert cfg.vwap_source == "hlc3"
    assert cfg.vp_bin_points == 0.25 and cfg.vp_value_area_pct == 70
    assert cfg.vp_weekly_enabled is False
    assert str(cfg.ny_anchor) == "09:30:00" and str(cfg.daily_anchor) == "18:00:00"
