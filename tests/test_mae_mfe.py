"""Excursions are measured after the fill, and a same-bar extreme counts as adverse first."""

import numpy as np

from scripts.run_mae_mfe import horizon_end, path_stats


def test_mfe_before_mae_uses_the_first_time_each_extreme_prints():
    h = np.array([105.0, 104.0, 112.0])
    l = np.array([100.0, 90.0, 100.0])
    hm = np.array([600, 601, 602])
    early = path_stats(1, 100.0, h, l, hm, 0, 2)
    assert early["mfe"] == 5.0
    assert early["mae"] == 10.0
    assert early["mfe_first"] is True
    assert early["t_mfe"] == 0
    assert early["t_mae"] == 1
    later = path_stats(1, 100.0, h, l, hm, 0, 3)
    assert later["mfe"] == 12.0
    assert later["mfe_first"] is False


def test_same_bar_extreme_is_not_mfe_first():
    h = np.array([110.0])
    l = np.array([90.0])
    hm = np.array([600])
    stats = path_stats(-1, 100.0, h, l, hm, 0, 1)
    assert stats["mfe"] == 10.0
    assert stats["mae"] == 10.0
    assert stats["mfe_first"] is False


def test_horizon_stops_at_fifteen_minutes_and_at_eleven_thirty():
    class Day:
        hm = np.array([10 * 60, 10 * 60 + 10, 10 * 60 + 14, 10 * 60 + 20, 11 * 60 + 40])
        end = 5

    assert horizon_end(Day(), 0, "15m") == 3
    assert horizon_end(Day(), 0, "1130") == 4
    assert horizon_end(Day(), 4, "1130") == 4
