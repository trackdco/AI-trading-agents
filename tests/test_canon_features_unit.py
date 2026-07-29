"""Unit tests for the shared canon feature functions (LIVE-STACK #2), with hand-computed
synthetic frames. These validate the tape/CVD + VWAP-geometry definitions independently
of the (currently absent) research parquets, so the live ingestor has a tested foundation
now; the backtest-parity check against output/trade_matrix.parquet activates when
output/fp_minutes.parquet is restored.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from src.canon.features import crosses, path_eff, tape_features, vwap_geometry

NY = "America/New_York"


def _mins(day: str, hms, delta, vol, vwp):
    """Build a minute-tape frame like output/fp_minutes.parquet for one session day."""
    idx = pd.DatetimeIndex([pd.Timestamp(f"{day} {h // 60:02d}:{h % 60:02d}", tz=NY) for h in hms])
    df = pd.DataFrame({"sday": day, "hm": hms, "delta": delta, "vol": vol, "vwp": vwp},
                      index=idx)
    df["cum"] = df.delta.cumsum()
    df["runmin"] = df.cum.cummin()
    df["runmax"] = df.cum.cummax()
    return df


def test_path_eff_and_crosses():
    # straight line up over 5 points: net move == sum of steps -> efficiency 1.0
    assert path_eff(pd.Series([1.0, 2, 3, 4, 5])) == 1.0
    # fewer than 5 non-null -> NaN guard
    assert math.isnan(path_eff(pd.Series([1.0, 2, 3])))
    assert math.isnan(crosses(pd.Series([1.0, 2, 3])))
    # oscillating series crosses its mean several times
    assert crosses(pd.Series([0.0, 2, 0, 2, 0, 2])) > 0


def test_tape_features_long():
    # three 08:xx minutes before a 08:33 fill; hand-computed expectations
    day = "2026-03-17"
    upto = _mins(day, [480, 481, 482], delta=[10, -4, 6], vol=[100, 50, 60],
                 vwp=[10.0, 11.0, 12.0])
    fill = pd.Timestamp(f"{day} 08:03", tz=NY)      # right after the minutes, so d5/d15/d30 see them
    f = tape_features(upto, "long", fill, day_med_vol=60.0)

    assert f["pm_sofar_cvd"] == 12                    # 10 - 4 + 6
    assert f["pm_sofar_abscvd"] == 12
    assert math.isclose(f["pm_sofar_eff"], 12 / 210)  # cvd / total vol (210)
    assert f["pm_sofar_conf"] == 1                    # cvd>0 and long
    assert "op_sofar_cvd" not in f                    # no 09:30+ rows
    # all three minutes are within 5 of the fill -> d5==d15==d30==12
    assert f["d5"] == 12 and f["d15"] == 12 and f["d30"] == 12
    assert f["d5_conf"] == 1
    # last row: cum=12, runmin=6, runmax=12 -> pathpos=(12-6)/(12-6)=1.0
    assert f["pathpos"] == 1.0
    assert f["fill_vol_rel"] == 1.0                   # 60 / max(60,1)
    assert f["fill_delta"] == 6
    assert f["fill_delta_conf"] == 1


def test_tape_features_short_conf_flips():
    day = "2026-03-17"
    upto = _mins(day, [480, 481], delta=[10, 6], vol=[100, 60], vwp=[10.0, 11.0])
    f = tape_features(upto, "short", pd.Timestamp(f"{day} 08:33", tz=NY), day_med_vol=80.0)
    assert f["pm_sofar_cvd"] == 16
    assert f["pm_sofar_conf"] == 0                    # cvd>0 but short -> not confirming
    assert f["fill_delta_conf"] == 0


def test_tape_features_empty():
    # empty tape: no pm/op/pathpos keys, but the d5/d15/d30 loop still emits nan keys
    # (faithful to trade_matrix.py). Needs a DatetimeIndex for the index comparison.
    empty = pd.DataFrame(columns=["sday", "hm", "delta", "vol", "vwp", "cum",
                                  "runmin", "runmax"], index=pd.DatetimeIndex([], tz=NY))
    f = tape_features(empty, "long", pd.Timestamp("2026-03-17 08:33", tz=NY), 50.0)
    assert set(f) == {"d5", "d5_conf", "d15", "d15_conf", "d30", "d30_conf"}
    assert all(math.isnan(v) for v in f.values())   # all NaN


def _bars(day, hms, high, low, vw, up1):
    return pd.DataFrame({
        "mi": [pd.Timestamp(f"{day} {h // 60:02d}:{h % 60:02d}", tz=NY) for h in hms],
        "hm": hms, "high": high, "low": low, "vw": vw, "up1": up1,
    })


def test_vwap_geometry_long_with_sweep():
    day = "2026-03-17"
    # overnight (hm>=1080 or <480), London (120<=hm<480), then a post-08:00 bar
    # NOTE the definition quirk: "post" = hm>=480 ALSO includes the 18:00+ evening bars
    # (minute-of-day filter), so keep the evening bar inside the London hi/lo to isolate
    # the sweep to the 08:01 bar.
    pre = _bars(
        day,
        hms=[1140, 200, 300, 481],                  # 19:00 (ON), 03:20 & 05:00 (London), 08:01
        high=[100.0, 105.0, 106.0, 110.0],          # 08:01 high 110 > London high 106 -> hi swept
        low=[98.0, 95.0, 96.0, 96.0],               # nothing dips below London low 95 -> lo NOT swept
        vw=[np.nan, np.nan, np.nan, 100.0],
        up1=[np.nan, np.nan, np.nan, 102.0],
    )
    f = vwap_geometry(pre, entry=101.0, direction="long")
    assert math.isclose(f["ent_vs_vwap_sd"], 0.5)        # (101-100)/(102-100)
    assert math.isclose(f["ent_vs_vwap_sd_dir"], 0.5)    # long -> same sign
    # ON range = hm>=1080 OR hm<480 -> 19:00 + both London bars: hi=106, lo=95, range=11
    assert math.isclose(f["ent_on_pos"], 6 / 11)         # (101-95)/11
    assert f["lon_hi_swept"] == 1
    assert f["lon_lo_swept"] == 0


def test_vwap_geometry_short_sign_and_nan_guard():
    day = "2026-03-17"
    pre = _bars(day, [481], [110.0], [97.0], [100.0], [102.0])
    f = vwap_geometry(pre, entry=101.0, direction="short")
    assert math.isclose(f["ent_vs_vwap_sd"], 0.5)
    assert math.isclose(f["ent_vs_vwap_sd_dir"], -0.5)   # short flips the sign
    # VWAP not yet anchored -> empty geometry
    nan_bar = _bars(day, [400], [110.0], [97.0], [float("nan")], [float("nan")])
    assert vwap_geometry(nan_bar, 101.0, "long") == {}
    assert vwap_geometry(pre.iloc[0:0], 101.0, "long") == {}
