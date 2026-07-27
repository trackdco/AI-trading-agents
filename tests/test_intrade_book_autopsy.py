"""The separation statistic and the decision-point construction must be trustworthy.

If `auc` is wrong every ranking in the report is wrong, and if the book is referenced to
the ENTRY rather than the trade's CURRENT price then "wall ahead" measures the wrong thing
once the trade has moved — which is the whole point of an in-trade read.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts.intrade_book_autopsy import auc, build

NY = "America/New_York"
DAY = "2025-06-02"


def test_auc_is_half_when_populations_are_identical():
    s = pd.Series(np.arange(50, dtype=float))
    assert auc(s, s.copy()) == pytest.approx(0.5, abs=0.02)


def test_auc_is_one_when_perfectly_separated():
    assert auc(pd.Series(np.arange(100.0, 120.0)),
               pd.Series(np.arange(0.0, 20.0))) == pytest.approx(1.0)


def test_auc_is_zero_when_perfectly_inverted():
    assert auc(pd.Series(np.arange(0.0, 20.0)),
               pd.Series(np.arange(100.0, 120.0))) == pytest.approx(0.0)


def test_auc_returns_nan_on_thin_samples():
    """Better no number than a number built on five points."""
    assert np.isnan(auc(pd.Series([1.0, 2.0]), pd.Series([3.0, 4.0])))


def _bars(prices):
    ts = pd.date_range(f"{DAY} 09:00", periods=len(prices), freq="1min", tz=NY)
    return pd.DataFrame({
        "ts": ts, "day": DAY, "mins": ts.hour * 60 + ts.minute,
        "low": [p[0] for p in prices], "high": [p[1] for p in prices],
        "open": [p[0] for p in prices], "close": [p[1] for p in prices], "volume": 100,
    })


def _book_row(entry, stop, direction, dollars=100.0):
    return pd.DataFrame([{
        "day": DAY, "fill": pd.Timestamp(f"{DAY} 09:00", tz=NY), "win_": "pre",
        "direction": direction, "entry": entry, "stop": stop,
        "risk": abs(entry - stop), "R": 1.0, "dollars": dollars, "size": 1.0,
    }])


def _delta(vals):
    ts = pd.date_range(f"{DAY} 09:00", periods=len(vals), freq="1min", tz=NY)
    return pd.Series(np.asarray(vals, dtype=float), index=ts)


def test_trade_that_never_reaches_1R_is_excluded():
    """The decision point must exist for the row to mean anything."""
    bars = _bars([(100.0, 101.0)] * 6)
    T = build(_book_row(100.0, 95.0, "long"), bars, _delta([50] * 6), {})
    assert T.empty


def test_label_marks_a_runner_as_hold_was_right():
    # +1R = 105 on bar 1; then runs to 115 = +3R => ran_further = 2.0
    bars = _bars([(100.0, 100.5), (100.0, 106.0), (105.0, 110.0),
                  (108.0, 112.0), (110.0, 115.0), (112.0, 115.0)])
    T = build(_book_row(100.0, 95.0, "long"), bars, _delta([200] * 6), {})
    assert len(T) == 1
    assert T.iloc[0].ran_further >= 1.0


def test_label_marks_a_giveback_as_cut_was_right():
    # tags +1R then rolls straight over without extending
    bars = _bars([(100.0, 100.5), (100.0, 105.2), (99.0, 103.0),
                  (97.0, 100.0), (96.0, 98.0), (95.5, 97.0)])
    T = build(_book_row(100.0, 95.0, "long", dollars=-100.0), bars, _delta([-200] * 6), {})
    assert len(T) == 1
    assert T.iloc[0].ran_further < 1.0
