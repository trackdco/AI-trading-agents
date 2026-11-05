"""A bubble is one print. Several small prints at the same price are not one."""

import numpy as np
import pandas as pd

from scripts.run_footprint_absorption import (
    bubbles_at,
    is_bubble,
    rest_limit,
    wick_cluster,
)


def test_one_print_of_sixty_is_a_bubble_and_five_prints_are_not():
    assert is_bubble(100.0, "B", 60, 1, 60) is True
    assert is_bubble(100.0, "B", 60, 5, 60) is False
    assert is_bubble(100.0, "B", 15, 1, 15) is True
    assert is_bubble(100.0, "B", 15, 1, 60) is False


def test_bubble_has_to_sit_on_the_extreme():
    book = [(100.0, "B", 20.0), (90.0, "A", 40.0)]
    assert bubbles_at(book, 15, -1, 100.0) == [(100.0, 20.0)]
    assert bubbles_at(book, 15, -1, 101.0) == []
    assert bubbles_at(book, 15, 1, 90.0) == [(90.0, 40.0)]


def test_wick_print_is_outside_the_body():
    class Day:
        o = np.array([100.0, 100.0])
        h = np.array([110.0, 101.0])
        l = np.array([99.0, 99.0])
        c = np.array([101.0, 100.0])

    setup = {"poke": 0, "side": -1}
    stamp = pd.Timestamp("2024-10-01 09:31", tz="America/New_York")
    bubbles = {stamp: [(110.0, "B", 20.0), (100.5, "B", 15.0)]}
    day = Day()
    day.hm = np.array([9 * 60 + 31, 9 * 60 + 32])
    day.ts = pd.Timestamp("2024-10-01 09:30", tz="America/New_York")
    assert wick_cluster(day, setup, bubbles, 15) == 110.0
    bubbles[stamp] = [(100.5, "B", 40.0), (110.0, "B", 20.0)]
    assert wick_cluster(day, setup, bubbles, 15) is None


def test_limit_does_not_fill_on_the_signal_bar():
    class Day:
        hm = np.array([9 * 60 + 30 + i for i in range(4)])
        o = np.array([100.0, 103.0, 103.0, 100.0])
        h = np.array([106.0, 105.0, 104.5, 101.0])
        l = np.array([99.0, 102.0, 99.0, 99.0])
        c = np.array([105.0, 104.0, 100.0, 100.0])
        i_open = 0
        end = 4

    setup = {"side": -1, "level": 104.0, "stop": 106.5, "start": 2}
    trades = rest_limit(Day(), setup, 1.7, None, 80)
    assert len(trades) == 1
    assert abs(trades[0].risk - 2.5) < 1e-9
