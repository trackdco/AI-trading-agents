"""A reclaim has to come back inside within three bars, and a vacuum needs a thin tail."""

import numpy as np
import pandas as pd

from scripts.run_of_vp_videos import failed_auction, limit_trade, lvn_far, manage_trail
from scripts.trades_profile import (
    absorption_flag,
    big_print_clusters,
    print_location,
    tick_profile,
)


def _day():
    class Day:
        pass

    day = Day()
    day.hm = np.array([9 * 60 + 30 + i for i in range(8)])
    day.o = np.array([100.0, 101.0, 102.0, 100.5, 100.0, 100.0, 100.0, 100.0])
    day.h = np.array([101.0, 106.0, 106.5, 101.0, 100.5, 100.5, 100.5, 100.5])
    day.l = np.array([99.0, 100.0, 100.0, 99.5, 99.5, 99.5, 99.5, 99.5])
    day.c = np.array([100.5, 105.5, 105.0, 100.2, 100.0, 100.0, 100.0, 100.0])
    day.i_open = 0
    day.end = 8
    day.on_va = (90.0, 104.0, 100.0)
    return day


def test_reclaim_uses_the_bar_after_the_close_back_inside():
    day = _day()
    # Bar 1 pokes above 104. Bar 2 is still outside. Bar 3 closes inside.
    setup = failed_auction(day)
    assert setup is not None
    assert setup["side"] == -1
    assert setup["reclaim"] == 3
    assert setup["bar"] == 4
    assert setup["stop"] == float(day.h[1:4].max()) + 0.5


def test_a_reclaim_four_bars_late_is_not_a_signal():
    day = _day()
    day.h[1] = 106.0
    day.c[1] = 105.5
    day.h[2:5] = 103.0
    day.c[2:5] = 105.0
    day.h[5] = 103.0
    day.c[5] = 100.0
    assert failed_auction(day) is None


def test_limit_one_point_seven_uses_the_limit_risk():
    day = _day()
    setup = {
        "side": -1, "fill": 102.75, "bar": 2, "stop": 106.5, "risk": 3.75,
        "level": 104.0, "other": 90.0, "poc": 100.0, "reclaim": 1, "poke": 1, "extreme": 106.0,
    }
    day.o[2] = 103.0
    day.h[2] = 105.0
    trades = limit_trade(day, setup, None, 1.7)
    assert len(trades) == 1
    assert abs(trades[0].risk - 2.5) < 1e-9
    assert abs(trades[0].planned - 1.7 * 2.5) < 1e-9


def test_thin_tail_points_at_the_start_of_an_up_leg():
    prices = np.array([10, 11, 12, 13, 17, 18, 19, 20])
    vols = np.array([1, 1, 1, 1, 100, 100, 100, 100], dtype=float)
    assert lvn_far(prices, vols, 1) == 10.0
    assert lvn_far(np.array([10, 11, 12]), np.array([5.0, 5.0, 5.0]), 1) is None


def test_trail_locks_after_the_target_and_only_tightens():
    class Day:
        hm = np.array([600, 601, 604, 605])
        o = np.array([100.0, 100.0, 90.0, 91.0])
        h = np.array([101.0, 100.0, 92.0, 102.0])
        l = np.array([99.0, 90.0, 89.0, 90.0])
        c = np.array([100.0, 90.0, 91.0, 95.0])
        i_open = 0
        end = 4

    # Short at 100, stop 104, target 90. Bar 1 hits 90. Bar 3 trades 96, through a trail at the prior 5m high.
    trade, _exit, reached = manage_trail(Day(), -1, 100.0, 0, 104.0, 90.0)
    assert reached is True
    assert trade is not None
    assert trade.hit is True
    assert trade.gross < 0
    assert trade.gross > -4


def test_tick_profile_and_a_print_in_the_wick():
    trades = pd.DataFrame({
        "ts": pd.to_datetime(["2026-04-01T14:30:00Z", "2026-04-01T14:30:01Z", "2026-04-01T14:30:02Z"], utc=True),
        "price": [100.0, 105.0, 110.0],
        "size": [30.0, 40.0, 80.0],
        "side": ["B", "B", "B"],
    })
    val, vah, poc = tick_profile(trades)
    assert vah >= poc >= val
    clusters = big_print_clusters(trades, min_contracts=60)
    assert len(clusters) == 1
    assert clusters[0]["price"] == 110.0
    assert print_location(110.0, 100.0, 110.0, 99.0, 101.0) == "upper_wick"
    assert print_location(100.5, 100.0, 110.0, 99.0, 101.0) == "body"
    stalled = trades.iloc[:1].copy()
    stalled["size"] = 80.0
    assert absorption_flag(stalled, "B", 100.0, n_seconds=5, min_contracts=60) is True
