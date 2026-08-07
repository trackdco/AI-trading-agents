"""Step 9 diagnostics: time-bucket boundaries + slice sum-consistency (spec-1 Step 9 check)."""
from datetime import time

import pandas as pd

from src.backtest.diagnostics import DIMENSIONS, _slice_rows, _time_bucket


def test_time_bucket_boundaries():
    assert _time_bucket(time(8, 6)) == "premarket"
    assert _time_bucket(time(9, 29)) == "premarket"
    assert _time_bucket(time(9, 30)) == "open_0930_0945"
    assert _time_bucket(time(9, 45)) == "prime_0945_1015"
    assert _time_bucket(time(10, 14)) == "prime_0945_1015"
    assert _time_bucket(time(10, 15)) == "mid_1015_1030"
    assert _time_bucket(time(10, 30)) == "late_after_1030"
    assert _time_bucket(time(10, 59)) == "late_after_1030"


def _synthetic_trades() -> pd.DataFrame:
    return pd.DataFrame({
        "pattern": ["A", "B", "B2", "A", "unclassified"],
        "tf": ["1min", "2min", "3min", "5min", "2min"],
        "confluence": [2, 3, 3, 2, 3],
        "htf_flag": ["with_trend", "counter_trend", "range", "with_trend", "range"],
        "time_bucket": ["premarket", "prime_0945_1015", "late_after_1030",
                        "open_0930_0945", "prime_0945_1015"],
        "news_day": [True, False, True, False, True],
        "roll_day": [False, False, False, False, False],
        "gap_day": [True, True, False, True, False],
        "r_multiple": [2.0, -1.0, 3.5, -1.0, -0.5],
        "dollars": [400.0, -200.0, 700.0, -200.0, -100.0],
    })


def test_slices_sum_to_headline_totals():
    # spec-1 Step 9 check: every dimension is a full partition -> its rows sum to the headline.
    t = _synthetic_trades()
    rows = _slice_rows(t)
    total_n, total_r, total_d = len(t), t["r_multiple"].sum(), t["dollars"].sum()
    for dim in DIMENSIONS:
        sub = rows[rows["dimension"] == dim]
        assert sub["n_trades"].sum() == total_n, f"{dim} n mismatch"
        assert round(sub["sum_r"].sum(), 4) == round(total_r, 4), f"{dim} R mismatch"
        assert round(sub["sum_dollars"].sum(), 2) == round(total_d, 2), f"{dim} $ mismatch"


def test_win_loss_counts_are_consistent():
    t = _synthetic_trades()
    rows = _slice_rows(t)
    pat = rows[rows["dimension"] == "pattern"]
    assert pat["wins"].sum() == int((t["r_multiple"] > 0).sum())
    assert pat["losses"].sum() == int((t["r_multiple"] < 0).sum())
