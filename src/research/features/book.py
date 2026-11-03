"""MBP-10 snapshots, read as-of the decision.

The old canon stored the last book state of minute M under a timestamp of
M:00. A fill stamped M:00 then selected `ts <= fill` and received the state
from M:59. That is future data. Snapshots here carry the time the book was
actually observed.

Convention `event_time`: ts is when the book looked like this.
Convention `minute_label_end_state`: ts is the minute label, and the state
is the end of that minute (the archive bug). The reader shifts the label
to the minute close before the as-of cut, so a decision at the label does
not see it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

EVENT_TIME = "event_time"
MINUTE_LABEL_END_STATE = "minute_label_end_state"


@dataclass(frozen=True)
class BookSnapshot:
    ts: pd.Timestamp
    bids: tuple[tuple[float, float], ...]
    asks: tuple[tuple[float, float], ...]

    def effective_ts(self, convention: str) -> pd.Timestamp:
        if convention == EVENT_TIME:
            return self.ts
        if convention == MINUTE_LABEL_END_STATE:
            # the state belongs to the close of the labelled minute
            return self.ts + pd.Timedelta(minutes=1) - pd.Timedelta(nanoseconds=1)
        raise ValueError(f"unknown book convention {convention}")


def asof_book(
    snapshots: list[BookSnapshot],
    decision_ts: datetime,
    *,
    convention: str = EVENT_TIME,
) -> BookSnapshot | None:
    """Last snapshot whose information time is <= the decision. None if none."""
    decision = pd.Timestamp(decision_ts).tz_convert("UTC")
    chosen: BookSnapshot | None = None
    chosen_at: pd.Timestamp | None = None
    for snap in snapshots:
        stamp = snap.ts
        if stamp.tzinfo is None:
            raise ValueError("book snapshots must be timezone-aware")
        seen = snap.effective_ts(convention).tz_convert("UTC")
        if seen <= decision and (chosen_at is None or seen > chosen_at):
            chosen = snap
            chosen_at = seen
    return chosen


def naive_label_asof(snapshots: list[BookSnapshot], decision_ts: datetime) -> BookSnapshot | None:
    """The old, wrong selector: label timestamp <= decision. Used only by tests."""
    decision = pd.Timestamp(decision_ts).tz_convert("UTC")
    chosen = None
    chosen_at = None
    for snap in snapshots:
        seen = snap.ts.tz_convert("UTC")
        if seen <= decision and (chosen_at is None or seen > chosen_at):
            chosen = snap
            chosen_at = seen
    return chosen


def book_imbalance(snap: BookSnapshot | None) -> float:
    """(bid size - ask size) / (bid size + ask size) across the visible levels.

    Levels that are not in the snapshot do not exist. Nothing is invented
    past the deepest published price. Returns NaN when the book is empty.
    """
    if snap is None:
        return float("nan")
    bid = sum(size for _, size in snap.bids)
    ask = sum(size for _, size in snap.asks)
    total = bid + ask
    if total <= 0:
        return float("nan")
    return (bid - ask) / total


def depth_span_points(snap: BookSnapshot | None) -> float | None:
    """How many points the visible book covers on the wider side. None if empty."""
    if snap is None or not snap.bids or not snap.asks:
        return None
    best_bid = max(price for price, _ in snap.bids)
    best_ask = min(price for price, _ in snap.asks)
    bid_span = best_bid - min(price for price, _ in snap.bids)
    ask_span = max(price for price, _ in snap.asks) - best_ask
    return float(max(bid_span, ask_span))
