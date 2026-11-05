"""The YouTube rules fire on a closed minute and do not use that minute's own percentile."""

import numpy as np

from scripts.run_jake_method import (
    confluent,
    first_fade,
    long_absorption,
    manage,
    short_absorption,
    v4_direction,
)


def _day(hm, o, h, l, c, ask, bid, p80_ask=None, p80_bid=None):
    n = len(hm)
    class Day:
        pass
    day = Day()
    day.hm = np.array(hm)
    day.o = np.array(o, dtype=float)
    day.h = np.array(h, dtype=float)
    day.l = np.array(l, dtype=float)
    day.c = np.array(c, dtype=float)
    day.ask = np.array(ask, dtype=float)
    day.bid = np.array(bid, dtype=float)
    day.i_open = 0
    day.end = n
    day.p80_ask = {int(m): 10.0 for m in hm} if p80_ask is None else p80_ask
    day.p80_bid = {int(m): 10.0 for m in hm} if p80_bid is None else p80_bid
    return day


def test_short_flag_needs_no_reward_and_a_seller_refresh():
    # Bar 0 tags 100, heavy ask, down close in the lower half. Bar 1 sells off through the low.
    assert short_absorption(
        np.array([100.5]), np.array([101.0]), np.array([99.0]), np.array([99.25]),
        np.array([20.0]), np.array([5.0]), 0, 100.0, 10.0,
    )
    assert not short_absorption(
        np.array([100.0]), np.array([102.0]), np.array([100.0]), np.array([101.75]),
        np.array([20.0]), np.array([5.0]), 0, 100.0, 10.0,
    )


def test_long_flag_is_the_mirror_and_ignores_a_bar_that_does_not_reach():
    assert long_absorption(
        np.array([99.5]), np.array([101.0]), np.array([99.0]), np.array([100.75]),
        np.array([4.0]), np.array([20.0]), 0, 100.0, 10.0,
    )
    assert not long_absorption(
        np.array([110.0]), np.array([111.0]), np.array([109.0]), np.array([110.5]),
        np.array([4.0]), np.array([20.0]), 0, 100.0, 10.0,
    )


def test_wide_stop_uses_an_attempt_and_the_next_valid_flag_still_trades():
    # Bar 0 pokes 30 points through 100, refreshes, stop is about 32 points, skipped.
    # Bar 3 is a normal tag and is the trade. Entry is the bar after the refresh, one tick worse.
    hm = [9 * 60 + 30, 9 * 60 + 31, 9 * 60 + 32, 9 * 60 + 33, 9 * 60 + 34, 9 * 60 + 35]
    o = [100.0, 101.0, 100.0, 100.25, 100.0, 100.0]
    h = [130.0, 131.0, 100.5, 101.0, 100.5, 100.5]
    l = [99.0, 100.0, 99.0, 99.0, 99.5, 99.5]
    c = [129.0, 100.0, 99.25, 99.25, 100.0, 100.0]
    ask = [30.0, 1.0, 30.0, 1.0, 1.0, 1.0]
    bid = [5.0, 20.0, 5.0, 20.0, 1.0, 1.0]
    # Bar 0 close 129 is NOT in the lower half, so it is not absorption.
    # Build bar 0 properly: high 130, low 99, close near the low, open 100.
    o[0], h[0], l[0], c[0] = 100.0, 130.0, 99.0, 99.5
    # refresh bar 1: delta ask-bid = 1-20 < 0, close 100 < low 99? 100 < 99 is false.
    c[1], l[0] = 98.5, 99.0
    # So bar 0 absorption, bar 1 refresh through 99. Stop = 130+2, fill at bar 2 open 100 + ... short fill = open - tick.
    # risk ~ 32 > 20, skip. Then bar 3: high 101 tags 100, close 99.25 in lower half.
    day = _day(hm, o, h, l, c, ask, bid)
    # Make bar 3 a clean absorption and bar 4 the refresh.
    day.h[3], day.l[3], day.o[3], day.c[3] = 101.0, 99.0, 100.5, 99.25
    day.ask[3], day.bid[3] = 30.0, 5.0
    day.h[4], day.l[4], day.o[4], day.c[4] = 99.5, 97.0, 99.0, 97.5
    day.ask[4], day.bid[4] = 1.0, 20.0
    found = first_fade(day, 100.0, np.nan, 2.0, 20.0, 25.0, 2)
    assert found is not None
    assert found["absorb"] == 3
    assert found["entry"] == 5
    assert found["fill"] == day.o[5] - 0.25
    assert found["risk"] <= 20


def test_stop_is_checked_before_the_target_on_the_entry_bar():
    o = np.array([100.0, 100.0])
    h = np.array([100.0, 110.0])
    l = np.array([100.0, 89.0])
    c = np.array([100.0, 100.0])
    hm = np.array([9 * 60 + 30, 9 * 60 + 31])
    gross, _mae, hit = manage(o, h, l, c, hm, 1, 100.0, 90.0, [(1.0, 105.0)], 1, 2)
    assert hit is False
    assert gross < 0


def test_half_scale_out_keeps_the_runner_until_the_second_target():
    o = np.array([100.0, 100.0, 103.0])
    h = np.array([100.0, 104.0, 110.0])
    l = np.array([100.0, 100.0, 102.0])
    c = np.array([100.0, 103.0, 110.0])
    hm = np.array([9 * 60 + 30, 9 * 60 + 31, 9 * 60 + 32])
    gross, _mae, hit = manage(o, h, l, c, hm, 1, 100.0, 90.0, [(0.5, 103.0), (0.5, 110.0)], 1, 3)
    assert hit is True
    assert abs(gross - 6.5) < 1e-9


def test_confluence_is_five_points_and_v4_needs_a_large_overnight():
    assert confluent(100.0, [21000.0])
    assert confluent(21004.0, [])
    assert not confluent(21010.0, [100.0])
    assert v4_direction(110.0, 100.0, 101.0, 10.0, 5.0) == -1
    assert v4_direction(110.0, 100.0, 109.0, 10.0, 5.0) == 1
    assert v4_direction(110.0, 100.0, 101.0, 10.0, 8.0) == 0
