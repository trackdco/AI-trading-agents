"""Resampling + session context.

Right-closed, close-labelled resampling of the 1m base to entry/context TFs.
Session classification (Asia/London/NY) and running extremes. All tz-aware ET.
"""
from __future__ import annotations

from datetime import time

import pandas as pd

_AGG = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}


def resample(df1m: pd.DataFrame, minutes: int) -> pd.DataFrame:
    """1m → N-minute bars, right-closed & labelled at the bar CLOSE time.

    Label=close time means a bar timestamped 09:48 covers (09:47, 09:48] for 1m
    or the closing minute of the interval for higher TFs — signals compute on
    closed candles only (spec-1 §3 / architecture invariant 3).
    """
    if minutes == 1:
        return df1m.copy()
    out = df1m.resample(f"{minutes}min", closed="right", label="right").agg(_AGG)
    return out.dropna(subset=["open"])


def classify_session(ts) -> str:
    """ET wall-clock → session box (§2). Simplified fixed windows."""
    t = ts.time()
    if time(18, 0) <= t or t < time(2, 0):
        return "Asia"
    if time(2, 0) <= t < time(8, 0):
        return "London"
    if time(8, 0) <= t < time(17, 0):
        return "NY"
    return "off-session"


def session_extremes(df1m: pd.DataFrame, ts, session_start: time) -> tuple[float, float]:
    """High/low of the current session up to and including ``ts``."""
    day = ts.normalize()
    start = day + pd.Timedelta(hours=session_start.hour, minutes=session_start.minute)
    if ts.time() < session_start:
        start -= pd.Timedelta(days=1)
    window = df1m.loc[start:ts]
    if window.empty:
        return (float("nan"), float("nan"))
    return (float(window["high"].max()), float(window["low"].min()))


def prior_day_hl(df1m: pd.DataFrame, ts) -> tuple[float, float]:
    """Prior RTH-ish day's high/low (naive calendar-day split, ET)."""
    day = ts.normalize()
    prev = df1m.loc[day - pd.Timedelta(days=1):day - pd.Timedelta(seconds=1)]
    if prev.empty:
        return (float("nan"), float("nan"))
    return (float(prev["high"].max()), float(prev["low"].min()))
