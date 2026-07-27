"""In-trade flow must be oriented to the trade, and must die with the position.

Two ways this analysis could silently invert its own conclusions:
  * sign orientation — for a SHORT, aggressive selling (negative raw delta) is flow WITH
    the position and must read positive. Get it backwards and every finding flips.
  * path correctness — a stopped-out position must not inherit later flow.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts.intrade_flow_autopsy import timelines

NY = "America/New_York"
DAY = "2025-06-02"


def _bars(prices):
    ts = pd.date_range(f"{DAY} 09:00", periods=len(prices), freq="1min", tz=NY)
    return pd.DataFrame({
        "ts": ts, "day": DAY, "mins": ts.hour * 60 + ts.minute,
        "low": [p[0] for p in prices], "high": [p[1] for p in prices],
        "open": [p[0] for p in prices], "close": [p[1] for p in prices], "volume": 100,
    })


def _delta(vals):
    ts = pd.date_range(f"{DAY} 09:00", periods=len(vals), freq="1min", tz=NY)
    return pd.Series(np.asarray(vals, dtype=float), index=ts)


def _book(entry, stop, direction, R=1.0, dollars=100.0):
    return pd.DataFrame([{
        "day": DAY, "fill": pd.Timestamp(f"{DAY} 09:00", tz=NY), "win_": "pre",
        "direction": direction, "entry": entry, "stop": stop,
        "risk": abs(entry - stop), "R": R, "dollars": dollars, "size": 1.0,
    }])


def test_long_with_buying_reads_positive_flow():
    bars = _bars([(100.0, 101.0), (100.0, 103.0), (102.0, 105.0),
                  (104.0, 107.0), (106.0, 110.0), (108.0, 112.0)])
    T = timelines(_book(100.0, 95.0, "long"), bars, _delta([500] * 6))
    assert T.iloc[0].flow_total == pytest.approx(3000.0)


def test_short_with_selling_reads_POSITIVE_flow():
    """The inversion test: raw delta is negative, but selling is WITH a short."""
    bars = _bars([(99.0, 100.0), (97.0, 100.0), (95.0, 98.0),
                  (93.0, 96.0), (90.0, 94.0), (88.0, 92.0)])
    T = timelines(_book(100.0, 105.0, "short"), bars, _delta([-500] * 6))
    assert T.iloc[0].flow_total == pytest.approx(3000.0), "short orientation inverted"


def test_short_with_buying_reads_negative_flow():
    bars = _bars([(99.0, 100.0), (97.0, 100.0), (95.0, 98.0),
                  (93.0, 96.0), (90.0, 94.0), (88.0, 92.0)])
    T = timelines(_book(100.0, 105.0, "short"), bars, _delta([500] * 6))
    assert T.iloc[0].flow_total == pytest.approx(-3000.0)


def test_flow_stops_accruing_once_the_position_is_stopped_out():
    bars = _bars([(100.0, 101.0), (100.0, 101.0), (94.0, 100.0),   # stopped on bar 2
                  (100.0, 200.0), (200.0, 300.0), (300.0, 400.0)])
    T = timelines(_book(100.0, 95.0, "long"), bars, _delta([100, 100, 100, 9999, 9999, 9999]))
    row = T.iloc[0]
    assert row.stopped
    assert row.flow_total == pytest.approx(300.0), "inherited flow after the stop-out"


def test_r1_decision_point_is_recorded_when_reached():
    bars = _bars([(100.0, 100.5), (100.0, 106.0), (105.0, 107.0),
                  (106.0, 108.0), (107.0, 109.0), (108.0, 110.0)])
    T = timelines(_book(100.0, 95.0, "long"), bars, _delta([300] * 6))
    row = T.iloc[0]
    assert row.r1_min == 1                       # +1R = 105, first reached on bar 1
    assert row.flow_at_r1 == pytest.approx(600.0)


def test_r1_is_nan_when_the_trade_never_gets_there():
    bars = _bars([(100.0, 100.5), (99.5, 100.5), (99.0, 100.5),
                  (99.0, 100.5), (99.0, 100.5), (99.0, 100.5)])
    T = timelines(_book(100.0, 95.0, "long"), bars, _delta([10] * 6))
    assert np.isnan(T.iloc[0].r1_min)
