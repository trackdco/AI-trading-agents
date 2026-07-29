"""Bar feeds for the live bot (Phase 4 Stage 1).

The Vault consumes ONE closed 1-minute bar at a time through a small feed interface, so
the same loop runs against a historical replay (for building/testing) or a real-time
source (Stage 8) with no change to the Vault — the swap is the feed, nothing else.

A "bar" here is a completed 1-minute candle in the exact schema the engine already uses
(`ts_event` tz-aware, open/high/low/close/volume). The feed never emits a forming bar —
only closed ones — so live decisions can never peek at an incomplete candle.

    from src.live.feed import ReplayFeed
    for bar in ReplayFeed("data/reference/nq_1m_feb_jul2026.parquet",
                          start="2026-02-10", end="2026-02-13").stream():
        vault.on_bar(bar)          # one closed bar, in chronological order
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Protocol

import pandas as pd

NY = "America/New_York"
BAR_COLS = ("ts_event", "open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class Bar:
    """One closed 1-minute candle. Frozen — a delivered bar can never be mutated."""
    ts_event: pd.Timestamp        # tz-aware bar timestamp (the engine's convention)
    open: float
    high: float
    low: float
    close: float
    volume: float

    @classmethod
    def from_row(cls, row) -> "Bar":
        return cls(ts_event=row["ts_event"], open=float(row["open"]), high=float(row["high"]),
                   low=float(row["low"]), close=float(row["close"]),
                   volume=float(row["volume"]))


class BarFeed(Protocol):
    """The one method the Vault depends on. LiveFeed (Stage 8) implements the same."""
    def stream(self) -> Iterator[Bar]: ...


class ReplayFeed:
    """Stream historical bars as if live: chronological, one closed bar at a time.

    Source may be a parquet path or an in-memory DataFrame carrying the BAR_COLS. An
    optional [start, end] date window (NY calendar dates, inclusive) slices the stream;
    a `warmup_days` lead-in is prepended so the Vault has history to compute indicators
    before the window of interest begins.
    """

    def __init__(self, source: str | Path | pd.DataFrame, start: str | None = None,
                 end: str | None = None, warmup_days: int = 0):
        df = source if isinstance(source, pd.DataFrame) else pd.read_parquet(source)
        missing = [c for c in BAR_COLS if c not in df.columns]
        if missing:
            raise ValueError(f"feed source missing columns {missing}")
        df = df[list(BAR_COLS)].sort_values("ts_event").reset_index(drop=True)
        if start is not None:
            lo = pd.Timestamp(start, tz=NY) - pd.Timedelta(days=warmup_days)
            df = df[df["ts_event"] >= lo]
        if end is not None:
            hi = pd.Timestamp(end, tz=NY) + pd.Timedelta(days=1)   # inclusive of the end day
            df = df[df["ts_event"] < hi]
        self._df = df.reset_index(drop=True)

    def __len__(self) -> int:
        return len(self._df)

    def bars_df(self) -> pd.DataFrame:
        """The underlying frame (for parity checks against the batch backtest)."""
        return self._df.copy()

    def stream(self) -> Iterator[Bar]:
        prev = None
        for row in self._df.itertuples(index=False):
            r = {c: getattr(row, c) for c in BAR_COLS}
            if prev is not None and r["ts_event"] <= prev:
                raise ValueError(f"non-monotonic bar {r['ts_event']} after {prev} — "
                                 "feed must be strictly time-ordered")
            prev = r["ts_event"]
            yield Bar.from_row(r)
