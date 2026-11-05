"""High-frequency limits: no fill before the level exists, and the floor follows the close."""

import numpy as np

from src.research.strategies.costs import TICK
from src.research.strategies.hf_limit import eod_update, path_blow, scan_limits


def test_limit_uses_only_a_price_known_before_the_bar():
    # Bar 0 trades through 100. The buy limit is not live until bar 1, and bar 1 does not reach it.
    o = np.array([101.0, 101.0, 100.5])
    h = np.array([101.5, 101.5, 101.0])
    l = np.array([99.5, 100.5, 100.4])
    c = np.array([100.0, 101.0, 100.6])
    hm = np.array([9 * 60 + 30, 9 * 60 + 31, 9 * 60 + 32])
    buy = np.array([np.nan, np.nan, 100.0])
    sell = np.array([np.nan, np.nan, np.nan])
    assert scan_limits(o, h, l, c, hm, buy, sell, 4.0, 1.0, 0, 3) == []
    # Bar 2 trades a tick through 100 and then the target 104 is not there, so it is a trade.
    buy2 = np.array([np.nan, 100.0, 100.0])
    l2 = np.array([100.5, 99.75, 100.4])
    h2 = np.array([101.0, 104.0, 101.0])
    o2 = np.array([101.0, 100.5, 101.0])
    c2 = np.array([100.8, 103.5, 100.6])
    got = scan_limits(o2, h2, l2, c2, hm, buy2, sell, 4.0, 1.0, 0, 3)
    assert len(got) == 1
    assert got[0].hit
    assert abs(got[0].gross - 4.0) < 1e-9
    assert got[0].mae >= TICK


def test_floor_follows_the_close_and_a_dip_to_it_ends_the_account():
    floor, locked = eod_update(51_500.0, 48_000.0, False, 2_000.0, 52_000.0, 50_000.0)
    assert floor == 49_500.0 and locked is False
    # An intraday print of 53_000 is not passed in. The close is what moves the floor.
    same, _ = eod_update(50_000.0, 48_000.0, False, 2_000.0, 52_000.0, 50_000.0)
    assert same == 48_000.0
    assert path_blow(50_000.0, 48_000.0, 2_000.0)
    assert path_blow(50_000.0, 48_000.0, 1_999.0) is False
