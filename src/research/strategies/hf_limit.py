"""High-frequency resting limits on 1-minute bars. No order routing.

A buy limit is live only on a bar after its price was known. It fills at the
limit only if the low trades at least one tick through and the bar did not
open already through. The stop is a market, one tick worse, and is checked
before the target. Commission is applied by the caller.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.research.strategies.costs import FLAT_MINUTE, TICK

OPEN = 9 * 60 + 30


@dataclass
class Trade:
    gross: float
    risk: float
    mae: float
    hit: bool


def _flat_end(hm: np.ndarray) -> int:
    hit = np.flatnonzero((hm >= FLAT_MINUTE) & (hm < 18 * 60))
    return int(hit[0]) if len(hit) else len(hm)


def _manage(side, limit, stop_px, target, o, h, l, c, hm, j, end):
    mae = 0.0
    for k in range(j, end):
        if hm[k] >= FLAT_MINUTE:
            if k == j:
                return k, 0.0, mae, False
            px = float(c[k - 1]) - side * TICK
            return k, side * (px - limit), mae, False
        if side == 1:
            adv = limit - float(l[k])
            mae = max(mae, adv)
            if float(o[k]) <= stop_px or float(l[k]) <= stop_px:
                fill = min(float(o[k]), stop_px - TICK) if float(o[k]) <= stop_px else stop_px - TICK
                return k, fill - limit, max(mae, limit - fill), False
            if float(h[k]) >= target:
                return k, target - limit, mae, True
        else:
            adv = float(h[k]) - limit
            mae = max(mae, adv)
            if float(o[k]) >= stop_px or float(h[k]) >= stop_px:
                fill = max(float(o[k]), stop_px + TICK) if float(o[k]) >= stop_px else stop_px + TICK
                return k, limit - fill, max(mae, fill - limit), False
            if float(l[k]) <= target:
                return k, limit - target, mae, True
    last = end - 1
    if last < j:
        return j, 0.0, mae, False
    px = float(c[last]) - side * TICK
    return last, side * (px - limit), mae, False


def scan_limits(o, h, l, c, hm, buy, sell, stop, reward, start, end, through=1, first_only=False):
    """`buy[i]` / `sell[i]` are limits known before bar i. NaN means no order.

    One position at a time. Two passes through on the same bar is no trade.
    """
    extra = TICK * through
    out = []
    i = start
    while i < end:
        b = buy[i]
        s = sell[i]
        b_hit = np.isfinite(b) and float(o[i]) > b - TICK and float(l[i]) <= b - extra
        s_hit = np.isfinite(s) and float(o[i]) < s + TICK and float(h[i]) >= s + extra
        if b_hit and s_hit:
            i += 1
            continue
        if not b_hit and not s_hit:
            i += 1
            continue
        side = 1 if b_hit else -1
        limit = float(b if side == 1 else s)
        stop_px = limit - side * stop
        target = limit + side * reward * stop
        k, gross, mae, hit = _manage(side, limit, stop_px, target, o, h, l, c, hm, i, end)
        out.append(Trade(gross, stop, mae, hit))
        if first_only:
            break
        i = k + 1
    return out


def eod_update(balance, floor, locked, mll, lock_trigger, lock_at):
    """Trail from the closing balance only. An intraday high does not move the floor."""
    if locked:
        return floor, True
    if balance + 1e-9 >= lock_trigger:
        return lock_at, True
    return max(floor, balance - mll), False


def path_blow(equity, floor, mae_dollars) -> bool:
    """A dip to the floor, open or closed, ends the account. A dip that stays above it does not."""
    return equity - mae_dollars <= floor + 1e-9
