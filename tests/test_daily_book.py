"""The fallback cannot fill on a bar where the overnight pull is still working."""

import numpy as np

from scripts.run_daily_book import day_trade


class Day:
    def __init__(self):
        self.hm = np.array([9 * 60 + 30, 9 * 60 + 40, 9 * 60 + 50])
        self.o = np.array([110.0, 110.0, 110.0])
        self.h = np.array([111.0, 111.0, 111.0])
        self.l = np.array([109.0, 109.0, 104.0])
        self.c = np.array([110.0, 110.0, 105.0])
        self.i_open = 0
        self.end = 3
        self.up = 1
        self.onl = 100.0
        self.onh = 120.0
        self.pdl = 105.0
        self.pdh = 130.0
        self.pdc = 108.0
        self.rth_open = 110.0
        self.vwap_prev = np.array([110.0, 110.0, 110.0])
        self.ib_i = -1
        self.ib_hi = np.nan
        self.ib_lo = np.nan
        self.va = None


def test_overnight_fill_blocks_the_fallback():
    day = Day()
    day.l = np.array([99.5, 109.0, 104.0])
    trade, source = day_trade(day, "pdhl", 9 * 60 + 40, 0.75)
    assert source == "onhl"
    assert trade is not None
    assert abs(trade.risk - 15.0) < 1e-9


def test_fallback_waits_until_the_cancel():
    day = Day()
    # Prior-day low is traded through on the first bar, before the cancel.
    day.l = np.array([104.5, 109.0, 109.0])
    trade, source = day_trade(day, "pdhl", 9 * 60 + 40, 0.75)
    assert source == "flat"
    assert trade is None
    # After the cancel the same level is taken.
    day.l = np.array([109.0, 109.0, 104.5])
    trade, source = day_trade(day, "pdhl", 9 * 60 + 40, 1.7)
    assert source == "fallback"
    assert trade is not None


def test_a_day_with_no_overnight_order_can_use_the_fallback_at_the_open():
    day = Day()
    day.up = 0
    day.onl = np.nan
    day.onh = np.nan
    day.l = np.array([104.5, 109.0, 109.0])
    _trade, source = day_trade(day, "pdhl", 9 * 60 + 40, 0.75)
    assert source == "fallback"
