"""Trade tape and session clock.

CVD sign, fixed: side "B" is the buyer aggressor (lifted the offer) and
side "A" is the seller aggressor (hit the bid). Delta and CVD are
buy volume minus sell volume. This matches data/reference/cvd/README.md.
scripts/build_cvd_minute.py documented the opposite sign and is not used here.

A feature may only see trades with timestamp <= the decision time.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

NY = ZoneInfo("America/New_York")
BUY = "B"
SELL = "A"
TICK = 0.25


def session_start(ts: datetime) -> pd.Timestamp:
    """CME session open: 18:00 America/New_York, including the previous evening."""
    local = pd.Timestamp(ts).tz_convert(NY)
    anchor = local.normalize() + pd.Timedelta(hours=18)
    if local < anchor:
        anchor = anchor - pd.Timedelta(days=1)
    return anchor


def _prepare(trades: pd.DataFrame) -> pd.DataFrame:
    frame = trades.copy()
    if "ts" not in frame.columns:
        raise ValueError("trades need a tz-aware ts column")
    frame["ts"] = pd.to_datetime(frame["ts"], utc=True)
    if frame["ts"].dt.tz is None:
        raise ValueError("trade timestamps must be timezone-aware")
    side = frame["side"].astype(str)
    unknown = set(side.unique()) - {BUY, SELL}
    if unknown:
        raise ValueError(f"side must be {BUY!r} (buy aggressor) or {SELL!r} (sell aggressor), got {unknown}")
    frame["size"] = frame["size"].astype(float)
    frame["price"] = frame["price"].astype(float)
    return frame.sort_values("ts")


def visible(trades: pd.DataFrame, decision_ts: datetime) -> pd.DataFrame:
    frame = _prepare(trades)
    decision = pd.Timestamp(decision_ts).tz_convert("UTC")
    return frame[frame["ts"] <= decision]


def signed_size(frame: pd.DataFrame) -> pd.Series:
    sign = frame["side"].map({BUY: 1.0, SELL: -1.0})
    return frame["size"] * sign


def cvd(trades: pd.DataFrame, decision_ts: datetime) -> float:
    """Session CVD at the decision, from the 18:00 New York anchor, buys minus sells."""
    frame = visible(trades, decision_ts)
    if frame.empty:
        return 0.0
    start = session_start(decision_ts).tz_convert("UTC")
    session = frame[frame["ts"] >= start]
    if session.empty:
        return 0.0
    return float(signed_size(session).sum())


def session_vwap_trades(trades: pd.DataFrame, decision_ts: datetime) -> float:
    """Volume-weighted average of trade prices since 18:00 New York.

    This is the tape VWAP. The chart VWAP Angus reads is bar_vwap() with
    source = open, anchored at the same 18:00. They are different objects.
    """
    frame = visible(trades, decision_ts)
    start = session_start(decision_ts).tz_convert("UTC")
    session = frame[frame["ts"] >= start]
    volume = float(session["size"].sum()) if len(session) else 0.0
    if volume <= 0:
        return float("nan")
    return float((session["price"] * session["size"]).sum() / volume)


def footprint_minutes_to_trades(minutes: pd.DataFrame) -> pd.DataFrame:
    """Turn a per-minute footprint into trades visible only at the minute close.

    The archive labels `ts_minute` as the start of the minute and stores the
    whole minute's volume on that label. Emitting the trade at the close
    (start + 1 minute) stops a decision inside the minute from seeing it.
    """
    if "ts_minute" not in minutes.columns:
        raise ValueError("footprint minutes need ts_minute")
    start = pd.to_datetime(minutes["ts_minute"], utc=True)
    close = start + pd.Timedelta(minutes=1)
    return pd.DataFrame(
        {
            "ts": close,
            "price": minutes["price"].astype(float),
            "size": minutes["volume"].astype(float),
            "side": minutes["side"].astype(str),
        }
    )


def bar_vwap(bars: pd.DataFrame, decision_ts: datetime, *, bar_seconds: int = 60) -> float:
    """Session VWAP of bar source = open, anchored at 18:00 New York.

    A bar is usable only after it has closed. Source is the open, not hlc3.
    """
    frame = bars.copy()
    frame["ts"] = pd.to_datetime(frame["ts"], utc=True)
    close_ts = frame["ts"] + pd.Timedelta(seconds=bar_seconds)
    decision = pd.Timestamp(decision_ts).tz_convert("UTC")
    closed = frame[close_ts <= decision]
    if closed.empty:
        return float("nan")
    start = session_start(decision_ts).tz_convert("UTC")
    session = closed[closed["ts"] >= start]
    # a bar that opened before the anchor and closed after it is the first
    # bar of the new session only when its open timestamp is at the anchor.
    session = session[session["ts"] >= start]
    volume = float(session["volume"].sum()) if len(session) else 0.0
    if volume <= 0:
        return float("nan")
    return float((session["open"] * session["volume"]).sum() / volume)
