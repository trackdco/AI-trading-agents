"""Footprint, stacked diagonal imbalance, and absorption.

These are detectors with fixed definitions. They are not a setup. Thresholds
below are the definition of the word, written down so a later setup card can
point at them. They were not fitted.

Stacked imbalance
    On one closed minute, at each price P:
    buy imbalance when buy[P] / sell[P - 1 tick] >= ratio (default 3),
    sell imbalance when sell[P] / buy[P + 1 tick] >= ratio.
    A zero on the denominator counts only when the numerator is at least
    `min_volume` (default 1). A stack is `stack` (default 3) consecutive
    prices with the same side. The minute is visible only after it closes.

Absorption
    Over a window ending at the decision (default 30 seconds), using only
    trades and book states at or before that time:
    the trade range is at most `max_range` points (default 0.50, two NQ ticks),
    aggressive volume at the level (within one tick) is at least `min_volume`
    (default 50) on the attacking side, and the defending side of the book
    is still there: its displayed size at the decision is at least half of
    its size at the start of the window, or at least `min_resting` (default
    20) when the window opened empty.
    Attacking the bid means sell aggressors. Attacking the ask means buy
    aggressors.
    Without a book snapshot the function returns a proxy flag and
    confirmed=False. A proxy is not absorption.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from src.research.features.book import BookSnapshot, asof_book
from src.research.features.tape import BUY, SELL, TICK, visible

RATIO = 3.0
STACK = 3
MIN_PRINT = 1.0
ABSORB_WINDOW_S = 30
ABSORB_MIN_VOLUME = 50.0
ABSORB_MAX_RANGE = 0.50
ABSORB_MIN_RESTING = 20.0


@dataclass(frozen=True)
class Stack:
    side: str
    prices: tuple[float, ...]


@dataclass(frozen=True)
class Absorption:
    confirmed: bool
    proxy: bool
    reason: str
    aggressive_volume: float
    range_points: float


def minute_footprint(trades: pd.DataFrame, decision_ts: datetime) -> dict[pd.Timestamp, pd.DataFrame]:
    """Closed minutes only, keyed by the minute close in UTC."""
    frame = visible(trades, decision_ts)
    if frame.empty:
        return {}
    frame = frame.copy()
    frame["minute_start"] = frame["ts"].dt.floor("min")
    frame["minute_close"] = frame["minute_start"] + pd.Timedelta(minutes=1)
    decision = pd.Timestamp(decision_ts).tz_convert("UTC")
    closed = frame[frame["minute_close"] <= decision]
    out: dict[pd.Timestamp, pd.DataFrame] = {}
    for close_ts, group in closed.groupby("minute_close"):
        out[pd.Timestamp(close_ts)] = group
    return out


def _price_side(group: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for price, part in group.groupby("price"):
        buy = float(part.loc[part["side"] == BUY, "size"].sum())
        sell = float(part.loc[part["side"] == SELL, "size"].sum())
        rows.append((float(price), buy, sell))
    table = pd.DataFrame(rows, columns=["price", "buy", "sell"]).sort_values("price")
    return table


def _imbalance(numerator: float, denominator: float) -> bool:
    if numerator < MIN_PRINT:
        return False
    if denominator <= 0:
        return True
    return numerator / denominator >= RATIO


def stacked_imbalances(trades: pd.DataFrame, decision_ts: datetime) -> list[Stack]:
    found: list[Stack] = []
    for group in minute_footprint(trades, decision_ts).values():
        table = _price_side(group)
        found.extend(_stacks_from_table(table))
    return found


def _stacks_from_table(table: pd.DataFrame) -> list[Stack]:
    if table.empty:
        return []
    buy_at = dict(zip(table["price"], table["buy"]))
    sell_at = dict(zip(table["price"], table["sell"]))
    prices = list(table["price"])
    buy_flags = []
    sell_flags = []
    for price in prices:
        below = round(price - TICK, 10)
        above = round(price + TICK, 10)
        buy_flags.append(_imbalance(buy_at.get(price, 0.0), sell_at.get(below, 0.0)))
        sell_flags.append(_imbalance(sell_at.get(price, 0.0), buy_at.get(above, 0.0)))
    return _runs(prices, buy_flags, BUY) + _runs(prices, sell_flags, SELL)


def _runs(prices: list[float], flags: list[bool], side: str) -> list[Stack]:
    stacks: list[Stack] = []
    run: list[float] = []
    for price, flag in zip(prices, flags):
        if flag and (not run or abs(price - run[-1] - TICK) < 1e-9):
            run.append(price)
        else:
            if len(run) >= STACK:
                stacks.append(Stack(side, tuple(run)))
            run = [price] if flag else []
    if len(run) >= STACK:
        stacks.append(Stack(side, tuple(run)))
    return stacks


def _resting(snap: BookSnapshot | None, level: float, defending: str) -> float:
    if snap is None:
        return 0.0
    levels = snap.bids if defending == "bid" else snap.asks
    total = 0.0
    for price, size in levels:
        if abs(price - level) <= TICK + 1e-9:
            total += size
    return total


def absorption_at(
    trades: pd.DataFrame,
    decision_ts: datetime,
    level: float,
    *,
    attacking: str,
    book: list[BookSnapshot] | None = None,
    window_seconds: int = ABSORB_WINDOW_S,
    min_volume: float = ABSORB_MIN_VOLUME,
    max_range: float = ABSORB_MAX_RANGE,
    min_resting: float = ABSORB_MIN_RESTING,
) -> Absorption:
    """`attacking` is 'bid' (sellers hitting) or 'ask' (buyers lifting)."""
    if attacking not in {"bid", "ask"}:
        raise ValueError("attacking must be 'bid' or 'ask'")
    frame = visible(trades, decision_ts)
    decision = pd.Timestamp(decision_ts).tz_convert("UTC")
    start = decision - pd.Timedelta(seconds=window_seconds)
    window = frame[(frame["ts"] > start) & (frame["ts"] <= decision)]
    if window.empty:
        return Absorption(False, False, "no_trades", 0.0, 0.0)
    span = float(window["price"].max() - window["price"].min())
    near = window[(window["price"] - level).abs() <= TICK + 1e-9]
    aggressor = SELL if attacking == "bid" else BUY
    aggressive = float(near.loc[near["side"] == aggressor, "size"].sum())
    if span > max_range + 1e-9:
        return Absorption(False, False, "range", aggressive, span)
    if aggressive + 1e-9 < min_volume:
        return Absorption(False, False, "volume", aggressive, span)
    if not book:
        return Absorption(False, True, "no_book", aggressive, span)
    opening = asof_book(book, start.to_pydatetime())
    closing = asof_book(book, decision.to_pydatetime())
    if closing is None:
        return Absorption(False, True, "no_book", aggressive, span)
    defending = "bid" if attacking == "bid" else "ask"
    start_size = _resting(opening, level, defending)
    end_size = _resting(closing, level, defending)
    held = end_size + 1e-9 >= min_resting or (
        start_size > 0 and end_size + 1e-9 >= 0.5 * start_size
    )
    if not held:
        return Absorption(False, False, "book_pulled", aggressive, span)
    return Absorption(True, False, "confirmed", aggressive, span)
