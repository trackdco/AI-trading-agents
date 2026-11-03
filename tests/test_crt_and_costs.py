"""Costs, a hand-built CRT, and a no-skill lifecycle that should not print money."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from src.research.prop.optimise import Policy, run_topstep, summarise
from src.research.strategies.catalog import crt
from src.research.strategies.costs import (
    COST_POINTS,
    breakeven_win_rate,
    random_walk_win_rate,
)

NY = ZoneInfo("America/New_York")


def test_quarter_r_breakeven_is_above_the_random_walk():
    be = breakeven_win_rate(0.25, 16)
    rw = random_walk_win_rate(0.25, 16)
    assert 0.84 < be < 0.88
    assert rw < be
    win = 0.25 * 16 - COST_POINTS
    loss = 16 + COST_POINTS
    assert rw * win - (1 - rw) * loss < 0


def test_crt_waits_for_the_sweep_candle_to_close():
    start = datetime(2024, 1, 3, 10, 0, tzinfo=NY)
    rows = []
    # 15 minutes inside 100-110, then 15 minutes that sweep 112 and close at 105.
    for i in range(15):
        rows.append(_bar(start + timedelta(minutes=i), 104, 106, 103, 105))
    for i in range(14):
        rows.append(_bar(start + timedelta(minutes=15 + i), 108, 112, 107, 111))
    rows.append(_bar(start + timedelta(minutes=29), 108, 112, 104, 105))
    rows.append(_bar(start + timedelta(minutes=30), 105, 106, 104, 105))
    df = pd.DataFrame(rows)
    df["sess"] = 1
    df["hm"] = df["ts_event"].dt.hour * 60 + df["ts_event"].dt.minute
    sig = crt(df, 15, "close", 0.25, "crt_test")
    assert len(sig["i"]) == 1
    # signal is the last bar of the sweep candle, index 29, not earlier
    assert int(sig["i"][0]) == 29
    assert int(sig["side"][0]) == -1


def test_gross_zero_topstep_does_not_have_a_positive_lower_bound():
    policy = Policy(200.0, 0.25, 2, None, None, None, 1)
    net = run_topstep(50_000, policy, "gross0", 0.0, 400, np.random.default_rng(1), eval_days=40, funded_days=40)
    stat = summarise(net)
    assert stat["hi"] < 50  # not a free-money machine on this short horizon


def _bar(ts, o, h, l, c):
    return {"ts_event": pd.Timestamp(ts), "open": o, "high": h, "low": l, "close": c, "volume": 10}
