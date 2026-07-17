"""Resampler + session context: TF resampling, session boxes, extremes, levels.

Spec: spec-1-market-engine-backtester.md, Step 3.

Consumes the step-2 1m table (ts_event tz-aware America/New_York, bar OPEN
labels, plus session_date) and provides:
  - resample():        1m -> 2m/3m/5m/15m bars, right-closed, labeled by CLOSE
                       time (ts_close = when the bar's information exists;
                       no-lookahead depends on this convention)
  - classify_session(): Asia / London / NY box labels (strategy §2)
  - session_extremes(): running (causal) session-box highs/lows per trading day
  - prior_levels():     prior-day and prior-week H/L (strategy §6 target menu)
  - data_levels():      extremes printed in the window after scheduled
                        releases (strategy §2, N: CALIBRATE), with the
                        timestamp at which each level becomes known

DST is handled by flooring bar bins in UTC: the ET offset is always a whole
number of hours and every entry TF divides 60, so UTC flooring equals ET
wall-clock flooring on both sides of a transition (architecture invariant 2:
tz library only, never offset arithmetic).
"""

from __future__ import annotations

from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import yaml

from src.engine.data import session_date

NY_TZ = ZoneInfo("America/New_York")
OHLCV_AGG = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
SESSION_OTHER = "other"  # 16:00-18:00 ET sits outside the §2 boxes


def load_session_config(path: Path = Path("config/strategy.yaml")) -> dict:
    """Session boxes + data-level window from strategy.yaml (§2). No magic numbers."""
    with open(path) as f:
        cfg = yaml.safe_load(f)
    return {
        "boxes": {name: (box["start"], box["end"]) for name, box in cfg["session"]["boxes"].items()},
        "data_window_minutes": int(cfg["indicators"]["data_levels"]["window_minutes"]),
    }


def _minute_of_day(ts: pd.Series) -> pd.Series:
    return ts.dt.hour * 60 + ts.dt.minute


def _hhmm_to_minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def resample(df_1m: pd.DataFrame, tf_minutes: int) -> pd.DataFrame:
    """1m bars (open-labeled) -> tf bars labeled by close time (right-closed).

    A 5m bar built from 1m opens 09:30..09:34 gets ts_open=09:30 and
    ts_close=09:35 — its OHLC is only knowable at 09:35. Empty bins (halts,
    weekends) are dropped, not NaN-filled. tf must divide 60.
    """
    if 60 % tf_minutes:
        raise ValueError(f"tf_minutes={tf_minutes} must divide 60")
    utc_idx = pd.DatetimeIndex(df_1m["ts_event"].dt.tz_convert("UTC"))
    out = (
        df_1m.set_index(utc_idx)[list(OHLCV_AGG)]
        .resample(f"{tf_minutes}min", closed="left", label="left")
        .agg(OHLCV_AGG)
        .dropna(subset=["open"])
        .reset_index(names="ts_open")
    )
    out["ts_open"] = out["ts_open"].dt.tz_convert(NY_TZ)
    out["ts_close"] = out["ts_open"] + pd.Timedelta(minutes=tf_minutes)
    out["volume"] = out["volume"].astype("int64")
    out["session_date"] = session_date(out["ts_open"])
    return out[["ts_open", "ts_close", "open", "high", "low", "close", "volume", "session_date"]]


def classify_session(ts: pd.Series, boxes: dict[str, tuple[str, str]]) -> pd.Series:
    """Label each timestamp with its §2 session box; outside all boxes -> 'other'.

    Boxes may wrap midnight (Asia 18:00->03:00). Interval is [start, end):
    03:00 exactly belongs to London, 09:30 exactly to NY.
    """
    mins = _minute_of_day(ts)
    labels = pd.Series(SESSION_OTHER, index=ts.index, dtype="object")
    for name, (start, end) in boxes.items():
        s, e = _hhmm_to_minutes(start), _hhmm_to_minutes(end)
        mask = ((mins >= s) | (mins < e)) if s > e else ((mins >= s) & (mins < e))
        labels[mask] = name
    return labels


def session_extremes(df_1m: pd.DataFrame, boxes: dict[str, tuple[str, str]]) -> pd.DataFrame:
    """Running high/low per session box, causal at every bar.

    While a box is active its high/low expand bar by bar (cummax/cummin over
    closed bars); after it ends the final values persist for the rest of the
    trading day (§6: session extremes are targets/liquidity). Before a box has
    printed any bar its columns are NaN.
    """
    df = df_1m.copy()
    if "session_date" not in df.columns:
        df["session_date"] = session_date(df["ts_event"])
    df["session_box"] = classify_session(df["ts_event"], boxes)
    for name in boxes:
        in_box = df["session_box"] == name
        grp = df[in_box].groupby("session_date")
        df.loc[in_box, f"{name}_high"] = grp["high"].cummax()
        df.loc[in_box, f"{name}_low"] = grp["low"].cummin()
        day = df.groupby("session_date")
        df[f"{name}_high"] = day[f"{name}_high"].ffill()
        df[f"{name}_low"] = day[f"{name}_low"].ffill()
    return df


def prior_levels(df_1m: pd.DataFrame) -> pd.DataFrame:
    """Prior-day and prior-week H/L stamped on every bar (§6 target menu).

    Prior day = previous trading session present in the data. Weeks run
    Monday-Sunday over session_date, so Sunday-evening bars (which belong to
    Monday's session) fall in the correct new week. First day/week is NaN.
    """
    df = df_1m.copy()
    if "session_date" not in df.columns:
        df["session_date"] = session_date(df["ts_event"])

    daily = df.groupby("session_date").agg(high=("high", "max"), low=("low", "min"))
    df["prior_day_high"] = df["session_date"].map(daily["high"].shift(1))
    df["prior_day_low"] = df["session_date"].map(daily["low"].shift(1))

    sess = pd.to_datetime(df["session_date"])
    df["week_start"] = (sess - pd.to_timedelta(sess.dt.weekday, unit="D")).dt.date
    weekly = df.groupby("week_start").agg(high=("high", "max"), low=("low", "min"))
    df["prior_week_high"] = df["week_start"].map(weekly["high"].shift(1))
    df["prior_week_low"] = df["week_start"].map(weekly["low"].shift(1))
    return df.drop(columns="week_start")


def load_news_calendar(path: Path = Path("config/news_calendar.csv")) -> pd.DataFrame:
    cal = pd.read_csv(path)
    cal["ts_event"] = pd.to_datetime(
        cal["date"] + " " + cal["time_et"], format="%Y-%m-%d %H:%M"
    ).dt.tz_localize(NY_TZ)
    return cal


def data_levels(
    df_1m: pd.DataFrame, calendar: pd.DataFrame, window_minutes: int
) -> pd.DataFrame:
    """Extremes printed within N minutes AFTER each scheduled release (§2).

    N: CALIBRATE (start 15, config indicators.data_levels.window_minutes).
    Window is [release, release + N): the post-release spike is the level.
    NOTE — parked for Angus: §2 says "within N min of" which could also be
    read as symmetric ±N; post-release only is implemented pending his call.

    ts_available = window end: the level may only be used by snapshots at or
    after this time (no-lookahead).
    """
    rows = []
    ts = df_1m["ts_event"]
    for ev in calendar.itertuples():
        t0 = ev.ts_event
        t1 = t0 + pd.Timedelta(minutes=window_minutes)
        window = df_1m[(ts >= t0) & (ts < t1)]
        if window.empty:
            continue
        rows.append(
            {
                "event": ev.event,
                "impact": ev.impact,
                "ts_event": t0,
                "data_high": window["high"].max(),
                "data_low": window["low"].min(),
                "ts_available": t1,
            }
        )
    return pd.DataFrame(
        rows, columns=["event", "impact", "ts_event", "data_high", "data_low", "ts_available"]
    )
