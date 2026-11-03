"""One feature row at a decision time. No column looks past that time."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime

import pandas as pd

from src.research.features.book import BookSnapshot, asof_book, book_imbalance
from src.research.features.footprint import stacked_imbalances
from src.research.features.tape import bar_vwap, cvd, session_vwap_trades


@dataclass(frozen=True)
class FeatureRow:
    decision_ts: str
    cvd: float
    trade_vwap: float
    bar_vwap_open: float
    buy_stacks: int
    sell_stacks: int
    book_imbalance: float
    book_ts: str | None

    def as_dict(self) -> dict:
        return asdict(self)


def features_at(
    trades: pd.DataFrame,
    decision_ts: datetime,
    *,
    bars: pd.DataFrame | None = None,
    book: list[BookSnapshot] | None = None,
    book_convention: str = "event_time",
) -> FeatureRow:
    stacks = stacked_imbalances(trades, decision_ts)
    snap = asof_book(book or [], decision_ts, convention=book_convention)
    bar_value = float("nan")
    if bars is not None and len(bars):
        bar_value = bar_vwap(bars, decision_ts)
    return FeatureRow(
        decision_ts=pd.Timestamp(decision_ts).tz_convert("UTC").isoformat(),
        cvd=cvd(trades, decision_ts),
        trade_vwap=session_vwap_trades(trades, decision_ts),
        bar_vwap_open=bar_value,
        buy_stacks=sum(1 for stack in stacks if stack.side == "B"),
        sell_stacks=sum(1 for stack in stacks if stack.side == "A"),
        book_imbalance=book_imbalance(snap),
        book_ts=None if snap is None else snap.effective_ts(book_convention).tz_convert("UTC").isoformat(),
    )
