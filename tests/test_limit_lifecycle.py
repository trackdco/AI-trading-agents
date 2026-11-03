"""Lifecycle, month, and grid for the two-phase limit research. No orders."""

import numpy as np

from scripts.run_limit_research import (
    _first_bar,
    _idx,
    _session_end,
    eval_stats,
    firms,
    grid_value,
    month_at_cap,
    month_plan,
)


def _firm(name: str) -> dict:
    for spec in firms():
        if spec["firm"] == name:
            return spec
    raise AssertionError(name)


def test_morning_index_skips_the_evening_open():
    hm = np.array([18 * 60, 18 * 60 + 1, 9 * 60 + 30, 9 * 60 + 31, 15 * 60 + 55, 16 * 60])
    assert _idx(hm, 9 * 60 + 30) == 2
    assert _session_end(hm) == 4


def test_first_bar_ignores_a_gap_and_requires_a_tick():
    # Buy limit at 100. Bar 0 opens through it. That is not a fill.
    o = np.array([99.5, 101.0, 100.5])
    h = np.array([100.0, 101.0, 101.0])
    l = np.array([99.0, 100.5, 99.75])
    assert _first_bar(1, 100.0, o, h, l, True) is None
    # No gap. Bar 2 trades a tick through 100.
    o2 = np.array([101.0, 100.5, 100.25])
    h2 = np.array([101.5, 101.0, 101.0])
    l2 = np.array([100.5, 100.0, 99.75])
    assert _first_bar(1, 100.0, o2, h2, l2, True) == 2
    # Touch-fill accepts the bar that only reaches 100.
    assert _first_bar(1, 100.0, o2, h2, l2, False) == 1


def test_grid_is_exact_for_a_certain_pass_and_hit():
    lucid = _firm("LucidFlex")
    contracts = 2000.0 / 32.0
    big = 1.7 * 2000.0 - 1.00 * contracts
    cycle = big + 4.0 * 150.0
    payout = min(0.50 * cycle, 2000.0)
    cash = payout * 0.90
    assert abs(grid_value(lucid, 1.0, 1.0) - (cash - 100.0)) < 1e-6
    assert abs(grid_value(lucid, 0.0, 1.0) - (-100.0)) < 1e-6
    # A higher hit rate is worth more, and a miss is not worth more than the fee.
    assert grid_value(lucid, 0.40, 0.50) > grid_value(lucid, 0.40, 0.37)
    assert grid_value(lucid, 0.40, 0.0) == -100.0

    topstep = _firm("Topstep")
    comm = 1.22 * contracts
    big_t = 1.7 * 2000.0 - comm
    cycle_t = big_t + 600.0
    payout_t = min(0.50 * cycle_t, 2000.0)
    cash_t = payout_t * 0.90
    assert abs(grid_value(topstep, 1.0, 1.0) - (cash_t - 49.0 - 149.0)) < 1e-6


def test_eval_pass_respects_the_40_percent_rule():
    lucid = _firm("LucidFlex")
    day = np.full(100, 1000.0)
    stat = eval_stats(day, lucid, seed=1, n=200, horizon=10)
    assert stat["pass"] == 1.0
    assert stat["days"] == 3.0


def test_month_charges_the_cap_and_can_pay():
    lucid = _firm("LucidFlex")
    slots, _note = month_plan(lucid)
    assert slots == 10
    fn_slots, _fn = month_plan(_firm("FundedNext Futures Flex"))
    assert fn_slots == 10
    bust = np.full(50, -2000.0)
    dead = month_at_cap(bust, bust, 0.0, lucid, np.random.default_rng(1), n=30, days=21)
    assert abs(float(dead.mean()) - (-100.0 * slots)) < 1e-6
    win_eval = np.full(50, 1000.0)
    win_funded = np.full(50, 4000.0)
    paid = month_at_cap(win_eval, win_funded, 1.0, lucid, np.random.default_rng(2), n=20, days=21)
    assert float(paid.min()) > 0.0
