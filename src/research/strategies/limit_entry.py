"""Resting-limit fills on 1-minute bars. No order routing.

A buy limit at L is eligible only on a bar after the level was known. The
trade-through rule fills at L only if the bar's low is at least one tick
below L and the bar did not open already through L. A touch fill uses the
same gap rule and fills if the low merely reaches L. The stop is a market
order, one tick worse, and is checked before the target. The target is a
limit, filled at its price with no extra slippage. A flat exit is a market
order with one tick of slippage. Commission is applied by the caller.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.research.strategies.costs import FLAT_MINUTE, TICK

REWARD_R = 1.7
MIN_RISK = 8.0
MAX_RISK = 80.0


@dataclass
class Fill:
    filled: bool
    target_hit: bool
    gross_points: float
    risk_points: float
    exit_reason: str


def _stop_price(side: int, op: float, stop: float) -> float:
    slipped = stop - side * TICK
    if side == 1 and op <= stop:
        return min(op, slipped)
    if side == -1 and op >= stop:
        return max(op, slipped)
    return slipped


def _manage(
    o: np.ndarray,
    h: np.ndarray,
    l: np.ndarray,
    c: np.ndarray,
    hm: np.ndarray,
    j0: int,
    end: int,
    side: int,
    limit: float,
    stop: float,
    target: float,
) -> Fill:
    """Stop before target from the fill bar. Entry is the limit. Risk is the stop distance."""
    risk = abs(limit - stop)
    for j in range(j0, end):
        if hm[j] >= FLAT_MINUTE:
            if j == j0:
                return Fill(True, False, 0.0, risk, "flat")
            px = float(c[j - 1]) - side * TICK
            return Fill(True, False, side * (px - limit), risk, "flat")
        op, hi, lo = float(o[j]), float(h[j]), float(l[j])
        if side == 1:
            if op <= stop or lo <= stop:
                return Fill(True, False, _stop_price(1, op, stop) - limit, risk, "stop")
            if hi >= target:
                return Fill(True, True, target - limit, risk, "target")
        else:
            if op >= stop or hi >= stop:
                return Fill(True, False, limit - _stop_price(-1, op, stop), risk, "stop")
            if lo <= target:
                return Fill(True, True, limit - target, risk, "target")
    last = end - 1
    if last < j0:
        return Fill(False, False, 0.0, risk, "none")
    px = float(c[last]) - side * TICK
    return Fill(True, False, side * (px - limit), risk, "eod")


def try_fill(
    o: np.ndarray,
    h: np.ndarray,
    l: np.ndarray,
    c: np.ndarray,
    hm: np.ndarray,
    start: int,
    end: int,
    side: int,
    limit: float,
    stop: float,
    target: float,
    through: bool,
) -> Fill:
    """Scan for a resting limit. Gap-through does not fill. `through` requires one extra tick."""
    extra = TICK if through else 0.0
    for j in range(start, end):
        if hm[j] >= FLAT_MINUTE:
            return Fill(False, False, 0.0, abs(limit - stop), "cancel")
        op = float(o[j])
        if side == 1:
            if op <= limit - TICK:
                return Fill(False, False, 0.0, abs(limit - stop), "gap")
            if float(l[j]) <= limit - extra:
                return _manage(o, h, l, c, hm, j, end, side, limit, stop, target)
        else:
            if op >= limit + TICK:
                return Fill(False, False, 0.0, abs(limit - stop), "gap")
            if float(h[j]) >= limit + extra:
                return _manage(o, h, l, c, hm, j, end, side, limit, stop, target)
    return Fill(False, False, 0.0, abs(limit - stop), "cancel")


def force_fill_at_limit(
    o: np.ndarray,
    h: np.ndarray,
    l: np.ndarray,
    c: np.ndarray,
    hm: np.ndarray,
    start: int,
    end: int,
    side: int,
    limit: float,
    stop: float,
    target: float,
) -> Fill:
    """Counterfactual: filled at the limit at the first eligible bar, even if price never traded there."""
    if start >= end:
        return Fill(False, False, 0.0, 0.0, "none")
    return _manage(o, h, l, c, hm, start, end, side, limit, stop, target)
