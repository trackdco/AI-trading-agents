"""High-impact news blackout. Reads the existing Forex Factory archive.

LucidDaily: flat from 1 minute before through 1 minute after a high-impact
USD release. Other plans in config/prop_rules.yaml do not use this as a breach.
The archive itself is data/reference/news_archive.csv (already in the repo).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

NY = ZoneInfo("America/New_York")
DEFAULT_ARCHIVE = Path("data/reference/news_archive.csv")


def load_high_impact_usd(path: Path | None = None) -> pd.DatetimeIndex:
    """Timezone-aware UTC timestamps of high-impact USD releases.

    The archive stores ET wall-clock strings with no offset. They are
    localized to America/New_York, which is how Forex Factory prints them.
    """
    src = path or DEFAULT_ARCHIVE
    frame = pd.read_csv(src)
    if "impact" in frame.columns:
        frame = frame[frame["impact"].astype(str).str.lower() == "high"]
    if "currency" in frame.columns:
        frame = frame[frame["currency"].astype(str).str.upper() == "USD"]
    stamps = pd.to_datetime(frame["datetime_ET"])
    localized = stamps.dt.tz_localize(NY, ambiguous="infer", nonexistent="shift_forward")
    return pd.DatetimeIndex(localized.dt.tz_convert("UTC"))


def in_news_blackout(
    ts: datetime,
    events: pd.DatetimeIndex,
    minutes: int = 1,
) -> bool:
    """True when ts is inside ±minutes of any event. ts must be timezone-aware."""
    if events.empty:
        return False
    moment = pd.Timestamp(ts).tz_convert("UTC")
    delta = pd.Timedelta(minutes=minutes)
    # searchsorted window, no full scan of the archive on the hot path
    start = moment - delta
    end = moment + delta
    left = events.searchsorted(start, side="left")
    right = events.searchsorted(end, side="right")
    return int(right) > int(left)


def blackout_window(event: datetime, minutes: int = 1) -> tuple[datetime, datetime]:
    return (event - timedelta(minutes=minutes), event + timedelta(minutes=minutes))
