"""Step 3 checks: resampling convention, session boxes, extremes, prior/data levels.

All fixtures are hand-computed; the DST test uses the March 8 2026
spring-forward weekend (mandatory named test, code-standards).
"""

from __future__ import annotations

from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from src.engine import sessions as s

NY = ZoneInfo("America/New_York")
BOXES = {
    "asia": ("18:00", "03:00"),
    "london": ("03:00", "09:30"),
    "ny": ("09:30", "16:00"),
    "premarket": ("08:00", "09:30"),
}


def mk_bars(start_ny: str, rows: list[tuple[float, float, float, float, int]]) -> pd.DataFrame:
    """1m bars starting at start_ny, one per minute: (open, high, low, close, volume)."""
    start = pd.Timestamp(start_ny, tz=NY)
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"])
    df.insert(0, "ts_event", [start + pd.Timedelta(minutes=i) for i in range(len(rows))])
    df["symbol"] = "NQH6"
    return df


def test_resample_5m_hand_computed() -> None:
    bars = mk_bars(
        "2026-02-10 09:30",
        [
            (100.0, 105.0, 99.0, 104.0, 10),
            (104.0, 106.0, 103.0, 105.0, 20),
            (105.0, 105.5, 101.0, 102.0, 30),
            (102.0, 103.0, 100.5, 101.0, 40),
            (101.0, 102.0, 98.0, 99.0, 50),   # last bar of first 5m bin
            (99.0, 99.5, 97.0, 98.0, 60),      # first bar of second bin
        ],
    )
    out = s.resample(bars, 5)
    assert len(out) == 2
    first = out.iloc[0]
    # right-closed, labeled by close: 09:30-09:34 opens -> ts_close 09:35
    assert first["ts_open"] == pd.Timestamp("2026-02-10 09:30", tz=NY)
    assert first["ts_close"] == pd.Timestamp("2026-02-10 09:35", tz=NY)
    assert first["open"] == 100.0    # first bar's open
    assert first["high"] == 106.0    # max of bars 0-4
    assert first["low"] == 98.0      # min of bars 0-4 (NOT bar 5's 97.0)
    assert first["close"] == 99.0    # bar 4's close
    assert first["volume"] == 150    # 10+20+30+40+50
    assert out.iloc[1]["ts_close"] == pd.Timestamp("2026-02-10 09:40", tz=NY)


def test_resample_drops_empty_bins_and_keeps_session_date() -> None:
    a = mk_bars("2026-02-10 09:30", [(1, 2, 0.5, 1.5, 5)] * 4)
    b = mk_bars("2026-02-10 18:00", [(1, 2, 0.5, 1.5, 5)] * 4)  # evening -> Feb 11 session
    out = s.resample(pd.concat([a, b], ignore_index=True), 2)
    assert len(out) == 4  # no NaN rows for the 8.5h halt between chunks
    assert out.iloc[0]["session_date"] == pd.Timestamp("2026-02-10").date()
    assert out.iloc[-1]["session_date"] == pd.Timestamp("2026-02-11").date()


@pytest.mark.parametrize("tf", [2, 3, 15])
def test_resample_bins_align_to_wall_clock(tf: int) -> None:
    bars = mk_bars("2026-02-10 09:31", [(1, 2, 0.5, 1.5, 5)] * (2 * tf))
    out = s.resample(bars, tf)
    # 09:31 falls inside the bin that started at the wall-clock multiple of tf
    assert out.iloc[0]["ts_open"].minute % tf == 0


def test_resample_rejects_tf_not_dividing_60() -> None:
    with pytest.raises(ValueError, match="divide 60"):
        s.resample(mk_bars("2026-02-10 09:30", [(1, 2, 0.5, 1.5, 5)]), 7)


def test_classify_session_boxes_including_midnight_wrap() -> None:
    times = ["18:30", "02:59", "03:00", "08:15", "09:29", "09:30", "15:59", "16:30", "17:15"]
    ts = pd.Series([pd.Timestamp(f"2026-02-10 {t}", tz=NY) for t in times])
    got = list(s.classify_session(ts, {k: BOXES[k] for k in ("asia", "london", "ny")}))
    assert got == ["asia", "asia", "london", "london", "london", "ny", "ny", "other", "other"]


def test_session_extremes_run_then_freeze() -> None:
    bars = mk_bars(
        "2026-02-10 03:00",  # two London bars...
        [(100, 110, 95, 105, 1), (105, 120, 100, 115, 1)],
    )
    ny = mk_bars("2026-02-10 09:30", [(115, 118, 111, 112, 1), (112, 130, 110, 129, 1)])
    df = s.session_extremes(pd.concat([bars, ny], ignore_index=True), BOXES)
    # running during London: bar0 sees only itself, bar1 sees both
    assert df.loc[0, "london_high"] == 110 and df.loc[1, "london_high"] == 120
    assert df.loc[1, "london_low"] == 95
    # frozen after London ends, still visible during NY
    assert df.loc[2, "london_high"] == 120 and df.loc[3, "london_high"] == 120
    # NY extremes run independently
    assert df.loc[2, "ny_high"] == 118 and df.loc[3, "ny_high"] == 130
    # Asia never printed -> NaN
    assert pd.isna(df.loc[0, "asia_high"])


def test_prior_day_and_prior_week_levels() -> None:
    d1 = mk_bars("2026-02-10 09:30", [(100, 111, 90, 105, 1)])   # Tue, week of Feb 9
    d2 = mk_bars("2026-02-11 09:30", [(105, 108, 99, 101, 1)])   # Wed, same week
    d3 = mk_bars("2026-02-16 09:30", [(101, 104, 100, 103, 1)])  # Mon, next week
    df = s.prior_levels(pd.concat([d1, d2, d3], ignore_index=True))
    assert pd.isna(df.loc[0, "prior_day_high"])                  # first session has no prior
    assert df.loc[1, "prior_day_high"] == 111 and df.loc[1, "prior_day_low"] == 90
    assert df.loc[2, "prior_day_high"] == 108                    # Mon's prior day is Wed
    assert df.loc[2, "prior_week_high"] == 111                   # max over Feb 9 week
    assert df.loc[2, "prior_week_low"] == 90
    assert pd.isna(df.loc[1, "prior_week_high"])                 # still inside first week


def test_dst_boundary() -> None:
    """Mandatory (code-standards): March 8 2026 spring-forward weekend.

    09:30 ET is 14:30 UTC on Friday (EST) but 13:30 UTC on Monday (EDT).
    Session labels, wall-clock times, and resample labels must all hold on
    both sides of the transition.
    """
    utc = [
        pd.Timestamp("2026-03-06 14:30", tz="UTC"),  # Fri 09:30 EST
        pd.Timestamp("2026-03-06 14:31", tz="UTC"),
        pd.Timestamp("2026-03-09 13:30", tz="UTC"),  # Mon 09:30 EDT
        pd.Timestamp("2026-03-09 13:31", tz="UTC"),
    ]
    df = pd.DataFrame(
        {
            "ts_event": pd.Series(utc).dt.tz_convert(NY),
            "open": [1.0] * 4, "high": [2.0] * 4, "low": [0.5] * 4, "close": [1.5] * 4,
            "volume": [5] * 4, "symbol": ["NQH6"] * 4,
        }
    )
    assert [t.strftime("%H:%M") for t in df["ts_event"]] == ["09:30", "09:31", "09:30", "09:31"]
    labels = s.classify_session(df["ts_event"], {k: BOXES[k] for k in ("asia", "london", "ny")})
    assert list(labels) == ["ny", "ny", "ny", "ny"]
    out = s.resample(df, 5)
    assert [t.strftime("%H:%M") for t in out["ts_close"]] == ["09:35", "09:35"]
    assert str(out["ts_close"].iloc[0].tz) == "America/New_York"


def test_data_levels_post_release_window_only() -> None:
    # pre-release bar has the biggest high; it must NOT become the data level
    bars = mk_bars(
        "2026-02-11 08:28",
        [
            (100, 999, 99, 100, 1),   # 08:28 pre-release, huge high — excluded
            (100, 101, 99, 100, 1),   # 08:29 pre-release — excluded
            (100, 105, 98, 104, 1),   # 08:30 release bar
            (104, 112, 103, 111, 1),  # 08:31 spike high
            (111, 111, 96, 97, 1),    # 08:32 spike low
        ]
        + [(97, 98, 96.5, 97, 1)] * 12,  # through 08:44
    )
    cal = pd.DataFrame(
        {
            "date": ["2026-02-11", "2026-02-11"],
            "time_et": ["08:30", "14:00"],  # 14:00 event has no bars -> skipped
            "event": ["CPI", "FOMC Minutes"],
            "impact": ["high", "high"],
        }
    )
    cal["ts_event"] = pd.to_datetime(cal["date"] + " " + cal["time_et"]).dt.tz_localize(NY)
    out = s.data_levels(bars, cal, window_minutes=15)
    assert len(out) == 1
    row = out.iloc[0]
    assert row["event"] == "CPI"
    assert row["data_high"] == 112 and row["data_low"] == 96
    assert row["ts_available"] == pd.Timestamp("2026-02-11 08:45", tz=NY)


def test_load_session_config_reads_strategy_yaml() -> None:
    cfg = s.load_session_config(Path(__file__).parents[1] / "config" / "strategy.yaml")
    assert cfg["boxes"]["ny"] == ("09:30", "16:00")
    assert cfg["boxes"]["asia"] == ("18:00", "03:00")
    assert cfg["data_window_minutes"] == 15
