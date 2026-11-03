"""Resting-limit fills: trade-through, no gap fill, stop before target, no lookahead."""

import numpy as np

from src.research.strategies.limit_entry import force_fill_at_limit, try_fill


def _bars():
    # Bar 0 forms the level. Bars 1+ can fill. Flat minute is 15:55, so use morning times.
    o = np.array([100.0, 101.0, 100.5, 100.0, 103.0])
    h = np.array([101.0, 101.5, 100.75, 104.0, 104.0])
    l = np.array([99.5, 100.5, 99.75, 99.5, 102.0])
    c = np.array([100.5, 101.0, 100.0, 103.5, 103.0])
    hm = np.array([9 * 60 + 30, 9 * 60 + 31, 9 * 60 + 32, 9 * 60 + 33, 9 * 60 + 34])
    return o, h, l, c, hm


def test_trade_through_needs_a_tick_and_ignores_the_signal_bar():
    o, h, l, c, hm = _bars()
    # Buy limit at 100, stop 8 points below, target 1.7R above. Bar 0 trades
    # through 100 but is before the order exists.
    stop, target = 98.0, 100.0 + 1.7 * 2.0
    # The order starts at bar 1, so bar 0's low of 99.50 cannot fill it.
    # Bar 1's low is 100.50, which does not trade a tick through 100.
    not_yet = try_fill(o, h, l, c, hm, 1, 2, 1, 100.0, stop, target, through=True)
    assert not_yet.filled is False
    # Bar 2 low is 99.75, exactly one tick through 100. Bar 3 then prints the target.
    filled = try_fill(o, h, l, c, hm, 1, 5, 1, 100.0, stop, target, through=True)
    assert filled.filled is True
    assert filled.exit_reason == "target"
    assert abs(filled.gross_points - 1.7 * 2.0) < 1e-9


def test_touch_fills_a_bar_that_only_reaches_the_limit():
    o = np.array([101.0, 100.25])
    h = np.array([101.0, 101.0])
    l = np.array([100.25, 100.0])  # touches 100, does not trade a tick through
    c = np.array([100.5, 100.5])
    hm = np.array([9 * 60 + 31, 9 * 60 + 32])
    stop, target = 98.0, 100.0 + 1.7 * 2.0
    through = try_fill(o, h, l, c, hm, 0, 2, 1, 100.0, stop, target, through=True)
    touch = try_fill(o, h, l, c, hm, 0, 2, 1, 100.0, stop, target, through=False)
    assert through.filled is False
    assert touch.filled is True


def test_a_gap_through_the_limit_does_not_fill():
    o = np.array([99.5])
    h = np.array([100.0])
    l = np.array([99.0])
    c = np.array([99.25])
    hm = np.array([10 * 60])
    stop, target = 92.0, 100.0 + 13.6
    got = try_fill(o, h, l, c, hm, 0, 1, 1, 100.0, stop, target, through=True)
    assert got.filled is False
    assert got.exit_reason == "gap"


def test_stop_is_a_market_with_one_tick_and_beats_the_target():
    # Bar 0 trades a tick through the buy limit and does not reach the stop.
    # Bar 1 trades the stop. The stop fills one tick worse.
    o = np.array([100.5, 93.0])
    h = np.array([100.5, 93.0])
    l = np.array([99.5, 91.5])
    c = np.array([100.0, 92.0])
    hm = np.array([10 * 60, 10 * 60 + 1])
    stop, limit = 92.0, 100.0
    target = limit + 1.7 * 8.0
    got = try_fill(o, h, l, c, hm, 0, 2, 1, limit, stop, target, through=True)
    assert got.filled is True
    assert got.target_hit is False
    assert got.exit_reason == "stop"
    assert abs(got.gross_points - (-8.25)) < 1e-9


def test_a_missed_runaway_is_a_winner_in_the_counterfactual():
    # Price never trades down to the buy limit. From the first bar, a fill at
    # the limit would have reached the target.
    o = np.array([110.0, 112.0])
    h = np.array([114.0, 120.0])
    l = np.array([105.0, 111.0])
    c = np.array([112.0, 118.0])
    hm = np.array([10 * 60, 10 * 60 + 1])
    limit, stop = 100.0, 92.0
    target = limit + 1.7 * 8.0
    real = try_fill(o, h, l, c, hm, 0, 2, 1, limit, stop, target, through=True)
    ghost = force_fill_at_limit(o, h, l, c, hm, 0, 2, 1, limit, stop, target)
    assert real.filled is False
    assert ghost.target_hit is True
