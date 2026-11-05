"""MNQ costs used by every research result.

TopstepX published round-turn for MNQ is $1.22 (exchange $0.70, NFA $0.02,
commission $0.50), retrieved 2026-11-03 from
https://help.topstep.com/en/articles/8284213-topstepx-commissions-and-fees
(page dated 2026-09-30). MNQ is $2 per point, so commission is 0.61 points.

Slippage is one NQ tick (0.25 points) against the fill on entry and one tick
against the fill on exit. Lucid's own commission card was not in the pages
read for the rule file, so the same CME-like MNQ cost is used there and
flagged in the report.
"""

from __future__ import annotations

TICK = 0.25
MNQ_DOLLARS_PER_POINT = 2.0
COMMISSION_RT_USD = 1.22
COMMISSION_POINTS = COMMISSION_RT_USD / MNQ_DOLLARS_PER_POINT
SLIPPAGE_POINTS = TICK * 2  # one tick each side
COST_POINTS = COMMISSION_POINTS + SLIPPAGE_POINTS
MIN_STOP = 2.0
MAX_STOP = 200.0
FLAT_MINUTE = 15 * 60 + 55  # 15:55 ET, inside Topstep and Lucid


def breakeven_win_rate(reward_r: float, stop_points: float, cost_points: float = COST_POINTS) -> float:
    """Win rate that nets zero after costs. Reward and stop are the intended prices, before slippage."""
    win = reward_r * stop_points - cost_points
    loss = stop_points + cost_points
    if win <= 0:
        return 1.0
    return loss / (win + loss)


def random_walk_win_rate(reward_r: float, stop_points: float, tick: float = TICK) -> float:
    """P(target trigger before stop trigger) from the slipped entry, no drift."""
    dist_stop = stop_points + tick
    dist_target = reward_r * stop_points - tick
    if dist_target <= 0:
        return 0.0
    return dist_stop / (dist_stop + dist_target)
