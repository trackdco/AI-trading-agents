"""Tests for src/live/spread_guard.py — the order-time spread guard (CANON ruling Q-31).

The guard is RELATIVE (median-baselined), fail-open on thin data, and never a frozen
absolute — every case below pins one of those contract points.
"""

import pytest

from src.live.spread_guard import GuardResult, SpreadGuard


def test_passes_when_spread_is_within_relative_threshold():
    g = SpreadGuard(mult=3.0, min_obs=5)
    res = g.evaluate(4.0, [2.0, 2.0, 2.0, 2.0, 2.0])     # 4 <= 3x median(2)=6
    assert isinstance(res, GuardResult) and res.ok
    assert res.baseline == 2.0 and res.threshold == 6.0 and res.reason == "ok"


def test_trips_when_spread_exceeds_relative_threshold():
    g = SpreadGuard(mult=3.0, min_obs=5)
    res = g.evaluate(7.0, [2.0, 2.0, 2.0, 2.0, 2.0])     # 7 > 3x median(2)=6 -> TRIP
    assert not res.ok and res.observed == 7.0 and res.threshold == 6.0
    assert "7.00pt" in res.reason and "6.00pt" in res.reason


def test_threshold_is_relative_not_absolute():
    """The same 7pt fill passes in a wide-spread regime and trips in a tight one — proof
    the threshold tracks recent conditions, exactly the London-regime-shift requirement."""
    g = SpreadGuard(mult=3.0, min_obs=5)
    tight = g.evaluate(7.0, [2.0] * 5)                   # median 2 -> thr 6 -> trip
    wide = g.evaluate(7.0, [5.0] * 5)                    # median 5 -> thr 15 -> pass
    assert not tight.ok and wide.ok


def test_median_baseline_ignores_a_single_wide_outlier():
    g = SpreadGuard(mult=3.0, min_obs=5)
    # one 100pt spike must not lift the baseline (mean would; median does not)
    res = g.evaluate(7.0, [2.0, 2.0, 2.0, 2.0, 100.0])   # median 2 -> thr 6 -> trip
    assert not res.ok and res.baseline == 2.0


def test_fails_open_on_insufficient_history():
    g = SpreadGuard(mult=3.0, min_obs=5)
    res = g.evaluate(999.0, [2.0, 2.0])                  # only 2 obs < min_obs
    assert res.ok and res.reason == "pass:insufficient_history"
    assert res.baseline is None and res.threshold is None


def test_fails_open_on_missing_fill_spread():
    g = SpreadGuard()
    res = g.evaluate(None, [2.0] * 30)
    assert res.ok and res.reason == "pass:no_spread_data" and res.observed is None


def test_none_entries_in_baseline_are_dropped():
    g = SpreadGuard(mult=3.0, min_obs=3)
    res = g.evaluate(10.0, [2.0, None, 2.0, None, 2.0])  # 3 usable obs
    assert not res.ok and res.baseline == 2.0


def test_boundary_is_strictly_greater_than():
    g = SpreadGuard(mult=3.0, min_obs=5)
    res = g.evaluate(6.0, [2.0] * 5)                     # exactly at threshold -> PASS
    assert res.ok


def test_rejects_nonpositive_mult():
    with pytest.raises(ValueError):
        SpreadGuard(mult=0)
    with pytest.raises(ValueError):
        SpreadGuard(min_obs=0)
