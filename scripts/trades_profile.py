"""Build tick profiles and print flags from a Databento `trades` tape.

This module does not call Databento and does not buy data. It reads a table
that already has `ts`, `price`, `size`, and `side` (`B` buy aggressor, `A`
sell aggressor). A 60-lot threshold is contracts of the named root: 60 MNQ
is 6 NQ.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.research.strategies.costs import TICK
from src.research.strategies.jake_rules import value_area

NQ_PER_MNQ = 10.0


def nq_equivalent(size: float, root: str) -> float:
    if root.lower() == "mnq":
        return float(size) / NQ_PER_MNQ
    return float(size)


def tick_profile(trades: pd.DataFrame, frac: float = 0.70):
    """70% value area on 1-tick rows. Volume is the print size, not a 1-minute close."""
    if trades.empty:
        return None
    ticks = np.rint(trades["price"].to_numpy(dtype=float) / TICK).astype(np.int64)
    vols = trades["size"].to_numpy(dtype=float)
    area = value_area(ticks, vols, frac)
    if area is None or area[1] <= area[0]:
        return None
    return tuple(float(x) * TICK for x in area)


def big_print_clusters(
    trades: pd.DataFrame,
    min_contracts: float = 60.0,
    root: str = "nq",
    price_ticks: int = 4,
    window_seconds: float = 2.0,
) -> list[dict]:
    """Clusters of aggressive prints at or above `min_contracts` of this root."""
    if trades.empty:
        return []
    frame = trades.copy()
    frame["ts"] = pd.to_datetime(frame["ts"], utc=True)
    frame = frame.sort_values("ts")
    frame = frame[frame["size"].to_numpy(dtype=float) >= min_contracts]
    clusters: list[dict] = []
    for side, part in frame.groupby("side", sort=False):
        rows = part.to_dict("records")
        current: list[dict] = []
        for row in rows:
            if not current:
                current = [row]
                continue
            same_price = abs(float(row["price"]) - float(current[-1]["price"])) <= price_ticks * TICK + 1e-9
            close_time = (row["ts"] - current[-1]["ts"]).total_seconds() <= window_seconds
            if same_price and close_time:
                current.append(row)
                continue
            clusters.append(_cluster(current, str(side), root))
            current = [row]
        if current:
            clusters.append(_cluster(current, str(side), root))
    return clusters


def _cluster(rows: list[dict], side: str, root: str) -> dict:
    sizes = np.array([float(row["size"]) for row in rows])
    prices = np.array([float(row["price"]) for row in rows])
    total = float(sizes.sum())
    return {
        "side": side,
        "price": float(np.average(prices, weights=sizes)),
        "contracts": total,
        "nq_equivalent": nq_equivalent(total, root),
        "prints": len(rows),
        "start": rows[0]["ts"],
        "end": rows[-1]["ts"],
    }


def print_location(price: float, open_: float, high: float, low: float, close: float) -> str:
    """Where a print sits in the finished 1-minute bar. Wick versus body needs the bar."""
    body_lo = min(open_, close)
    body_hi = max(open_, close)
    if price > body_hi + 1e-9:
        return "upper_wick" if high + 1e-9 >= price else "outside"
    if price < body_lo - 1e-9:
        return "lower_wick" if low - 1e-9 <= price else "outside"
    return "body"


def absorption_flag(
    trades: pd.DataFrame,
    side: str,
    extreme: float,
    n_seconds: float = 5.0,
    min_contracts: float = 60.0,
) -> bool:
    """Large aggressive size at the extreme, and no further progress inside the window.

    `side` is the aggressor being absorbed: `B` at a high, `A` at a low.
    Progress is another tick beyond `extreme` after the first large print.
    """
    if trades.empty:
        return False
    frame = trades.copy()
    frame["ts"] = pd.to_datetime(frame["ts"], utc=True)
    frame = frame.sort_values("ts")
    near = frame[(frame["price"] - extreme).abs() <= TICK + 1e-9]
    near = near[near["side"] == side]
    near = near[near["size"].to_numpy(dtype=float) >= min_contracts]
    if near.empty:
        return False
    start = near.iloc[0]["ts"]
    window = frame[(frame["ts"] >= start) & (frame["ts"] <= start + pd.Timedelta(seconds=n_seconds))]
    if window.empty:
        return False
    if side == "B":
        return float(window["price"].max()) <= extreme + TICK + 1e-9
    return float(window["price"].min()) >= extreme - TICK - 1e-9
