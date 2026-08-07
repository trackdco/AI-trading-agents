"""The trail simulator must be pessimistic and must arm correctly.

If ADVERSE-FIRST is not honoured, every trailing policy is flattered — a bar that could
both stop us out and make a new high would be counted as the high. That single choice
decides whether these policies look like they beat the canon.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts.trail_policies import simulate

NY = "America/New_York"
DAY = "2025-06-02"


def _bars(prices):
    ts = pd.date_range(f"{DAY} 09:00", periods=len(prices), freq="1min", tz=NY)
    return pd.DataFrame({
        "ts": ts, "day": DAY, "mins": ts.hour * 60 + ts.minute,
        "low": [p[0] for p in prices], "high": [p[1] for p in prices],
        "open": [p[0] for p in prices], "close": [p[2] if len(p) > 2 else p[1] for p in prices],
        "volume": 100,
    })


FILL = pd.Timestamp(f"{DAY} 09:00", tz=NY)


def test_adverse_first_takes_the_stop_not_the_high():
    """A bar that both stops us and makes a new high MUST count as the stop."""
    bars = _bars([(100.0, 101.0), (95.0, 130.0)])      # bar 1: stops at 95 AND prints 130
    r = simulate(bars, FILL, entry=100.0, stop=95.0, sign=1.0, risk=5.0, trail_R=1.0)
    assert r == pytest.approx(-1.0), f"flattered by intrabar ordering: {r}R"


def test_trail_does_not_arm_below_1R():
    """Before +1R the structural stop stands — a shallow pullback must not scratch us."""
    bars = _bars([(100.0, 104.0), (99.0, 103.0), (98.0, 102.0), (97.0, 101.0)])
    r = simulate(bars, FILL, entry=100.0, stop=95.0, sign=1.0, risk=5.0, trail_R=0.5)
    assert r > -1.0                      # never hit 95
    assert r == pytest.approx((101.0 - 100.0) / 5.0, abs=0.3)


def test_trail_locks_in_profit_once_armed():
    # runs to +4R (120) then collapses; a 1R trail should exit near 115 = +3R
    bars = _bars([(100.0, 106.0), (105.0, 120.0), (95.0, 110.0)])
    r = simulate(bars, FILL, entry=100.0, stop=95.0, sign=1.0, risk=5.0, trail_R=1.0)
    assert r == pytest.approx(3.0, abs=0.01)


def test_breakeven_stop_scratches_rather_than_losing():
    bars = _bars([(100.0, 106.0), (99.0, 104.0), (90.0, 99.0)])
    r = simulate(bars, FILL, entry=100.0, stop=95.0, sign=1.0, risk=5.0,
                 trail_R=None, be_at=1.0)
    assert r == pytest.approx(0.0, abs=0.01), "BE stop did not hold"


def test_short_side_mirrors():
    # short from 100, stop 105; runs to 80 (+4R) then rallies to 90 -> 1R trail exits +3R
    bars = _bars([(94.0, 100.0), (80.0, 95.0), (90.0, 100.0)])
    r = simulate(bars, FILL, entry=100.0, stop=105.0, sign=-1.0, risk=5.0, trail_R=1.0)
    assert r == pytest.approx(3.0, abs=0.01)


def test_flat_at_the_belt_when_never_stopped():
    bars = _bars([(100.0, 101.0, 100.5), (100.0, 102.0, 101.0), (101.0, 103.0, 102.5)])
    r = simulate(bars, FILL, entry=100.0, stop=95.0, sign=1.0, risk=5.0, trail_R=None)
    assert r == pytest.approx((102.5 - 100.0) / 5.0)


def test_returns_nan_when_no_bars_follow_the_fill():
    bars = _bars([(100.0, 101.0)])
    r = simulate(bars, pd.Timestamp(f"{DAY} 15:00", tz=NY), 100.0, 95.0, 1.0, 5.0, 1.0)
    assert np.isnan(r)
