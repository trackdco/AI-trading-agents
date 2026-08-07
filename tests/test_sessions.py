"""Tests for src/engine/sessions.py — resampler, session boxes, levels (Spec 1, Step 3).

Hand-computed fixtures for a known day, plus a DST-boundary case (spring-forward Mar 8 2026:
America/New_York goes EST -05:00 -> EDT -04:00).
"""
from datetime import time

import pandas as pd

from src.engine.sessions import (
    SessionBox,
    data_levels,
    prior_day_levels,
    prior_week_levels,
    resample_ohlcv,
    running_session_extremes,
    session_of,
)

NY = "America/New_York"

# Standard §2 boxes (wall-clock ET); Asia wraps midnight.
BOXES = [
    SessionBox(name="asia", start=time(18, 0), end=time(3, 0)),
    SessionBox(name="london", start=time(3, 0), end=time(9, 30)),
    SessionBox(name="ny", start=time(9, 30), end=time(16, 0)),
]


def _bars(start_ny: str, ohlcv: list[tuple], freq="1min") -> pd.DataFrame:
    idx = pd.date_range(pd.Timestamp(start_ny, tz=NY), periods=len(ohlcv), freq=freq)
    o, h, low, c, v = zip(*ohlcv)
    return pd.DataFrame({"ts_event": idx, "open": o, "high": h, "low": low, "close": c, "volume": v})


# ------------------------------------------------------------------ resampling

def test_resample_5m_close_labeled_and_aggregated():
    # ten 1m bars 09:30..09:39 (start-labeled). 5m bars must be stamped 09:35 and 09:40,
    # each aggregating the five 1m bars 09:30-09:34 and 09:35-09:39.
    rows = [(100 + i, 100 + i + 3, 100 + i - 2, 100 + i + 1, 10) for i in range(10)]
    df = _bars("2026-02-02 09:30", rows)
    out = resample_ohlcv(df, "5min")
    assert list(out["ts_event"]) == [pd.Timestamp("2026-02-02 09:35", tz=NY),
                                     pd.Timestamp("2026-02-02 09:40", tz=NY)]
    b1 = out.iloc[0]
    assert b1["open"] == 100          # first of 09:30..09:34
    assert b1["close"] == 104 + 1     # last (09:34) close = 104+1
    assert b1["high"] == 104 + 3      # max high over 09:30..09:34
    assert b1["low"] == 100 - 2       # min low
    assert b1["volume"] == 50         # 5 * 10


def test_resample_no_lookahead_boundary():
    # bar stamped 09:35 must NOT include the 09:35 1m bar (that belongs to the 09:40 bar)
    rows = [(100 + i, 200, 50, 100 + i, 10) for i in range(6)]  # 09:30..09:35
    df = _bars("2026-02-02 09:30", rows)
    out = resample_ohlcv(df, "5min")
    first = out[out["ts_event"] == pd.Timestamp("2026-02-02 09:35", tz=NY)].iloc[0]
    assert first["close"] == 104      # close of 09:34, not 09:35


# ------------------------------------------------------------------ session boxes

def test_session_classification_including_wrap_and_boundaries():
    times = ["2026-02-02 20:00", "2026-02-03 02:00", "2026-02-03 05:00",
             "2026-02-03 09:30", "2026-02-03 12:00", "2026-02-03 17:00"]
    s = session_of(pd.Series(pd.to_datetime(times).tz_localize(NY)), BOXES)
    assert list(s) == ["asia", "asia", "london", "ny", "ny", ""]  # 17:00 = no box; 09:30 = ny start


def test_running_session_extremes_reset_per_instance():
    # NY session 09:30-09:33 then a later NY session next day; extremes accumulate per instance
    d1 = _bars("2026-02-02 09:30", [(100, 105, 99, 101, 1), (101, 108, 100, 102, 1),
                                    (102, 106, 95, 96, 1), (96, 97, 90, 93, 1)])
    d2 = _bars("2026-02-03 09:30", [(200, 205, 199, 201, 1), (201, 203, 195, 196, 1)])
    out = running_session_extremes(pd.concat([d1, d2], ignore_index=True), BOXES)
    day1 = out[out["ts_event"].dt.date.astype(str) == "2026-02-02"]
    assert list(day1["session_high"]) == [105, 108, 108, 108]   # running max
    assert list(day1["session_low"]) == [99, 99, 95, 90]        # running min
    day2 = out[out["ts_event"].dt.date.astype(str) == "2026-02-03"]
    assert list(day2["session_high"]) == [205, 205]             # reset for the new instance


# ------------------------------------------------------------------ prior day / week

def test_prior_day_levels_no_lookahead():
    d1 = _bars("2026-02-02 10:00", [(100, 120, 90, 110, 1)])
    d2 = _bars("2026-02-03 10:00", [(111, 130, 105, 115, 1)])
    out = prior_day_levels(pd.concat([d1, d2], ignore_index=True))
    assert pd.isna(out.iloc[0]["prior_day_high"])              # day 1 has no prior
    assert out.iloc[1]["prior_day_high"] == 120                # day 2 sees day 1's H/L
    assert out.iloc[1]["prior_day_low"] == 90


def test_prior_week_levels():
    # week A (Feb 2-6 2026) then week B (Feb 9); week B sees week A's H/L
    a = _bars("2026-02-02 10:00", [(100, 150, 80, 110, 1)])
    b = _bars("2026-02-09 10:00", [(111, 140, 100, 120, 1)])
    out = prior_week_levels(pd.concat([a, b], ignore_index=True))
    assert pd.isna(out.iloc[0]["prior_week_high"])
    assert out.iloc[1]["prior_week_high"] == 150
    assert out.iloc[1]["prior_week_low"] == 80


# ------------------------------------------------------------------ data levels

def test_data_levels_window_after_release():
    # release at 08:30; extremes taken from [08:30, 08:30+15m]
    rows = [(100, 100 + (5 if i == 3 else 1), 100 - (7 if i == 10 else 1), 100, 1) for i in range(30)]
    df = _bars("2026-02-04 08:30", rows)
    cal = pd.DataFrame({"datetime_ET": [pd.Timestamp("2026-02-04 08:30", tz=NY)],
                        "event": ["Non-Farm Employment Change"], "impact": ["high"]})
    out = data_levels(df, cal, n_minutes=15)
    assert len(out) == 1
    assert out.iloc[0]["data_high"] == 105          # spike at +3 min (within window)
    assert out.iloc[0]["data_low"] == 93            # dip at +10 min (within window)
    assert out.iloc[0]["n_bars"] == 16              # 08:30..08:45 inclusive


# ------------------------------------------------------------------ DST boundary (mandatory)

def test_dst_boundary():
    # Fri Mar 6 (EST, -05:00) and Mon Mar 9 (EDT, -04:00) straddle spring-forward (Mar 8).
    est = _bars("2026-03-06 09:30", [(100, 110, 90, 105, 1), (105, 106, 100, 101, 1)])
    edt = _bars("2026-03-09 09:30", [(200, 215, 195, 210, 1), (210, 211, 205, 206, 1)])
    df = pd.concat([est, edt], ignore_index=True)

    # tz offsets differ across the DST change
    assert df["ts_event"].iloc[0].utcoffset().total_seconds() / 3600 == -5   # EST
    assert df["ts_event"].iloc[2].utcoffset().total_seconds() / 3600 == -4   # EDT

    # 09:30 ET classifies as NY on BOTH sides of the change (wall-clock, not offset)
    s = session_of(df["ts_event"], BOXES)
    assert list(s) == ["ny", "ny", "ny", "ny"]

    # resampling works across the boundary and stays close-labeled with correct offsets
    out = resample_ohlcv(df, "2min")
    assert out["ts_event"].iloc[0] == pd.Timestamp("2026-03-06 09:32", tz=NY)
    assert out["ts_event"].iloc[-1] == pd.Timestamp("2026-03-09 09:32", tz=NY)

    # prior-day levels map correctly across the DST change (Mon sees Fri's H/L)
    pdl = prior_day_levels(df)
    assert pdl.iloc[2]["prior_day_high"] == 110    # Mon Mar 9 sees Fri Mar 6 high
    assert pdl.iloc[2]["prior_day_low"] == 90
