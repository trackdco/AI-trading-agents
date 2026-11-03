"""The farm recipe against the consistency rule. No market data."""

import numpy as np

from src.research.prop.farm import (
    household_batch,
    lucid_coin,
    lucid_recipe_run,
    topstep_coin,
)


def test_two_equal_days_pass_only_with_the_50_percent_addon():
    rng = np.random.default_rng(1)
    # p_eval=1 means every day is +target/2 and the loss branch never happens.
    at_40 = lucid_recipe_run(rng, n=200, consistency=0.40, p_eval=1.0, max_eval_days=2, fee=100)
    at_50 = lucid_recipe_run(np.random.default_rng(1), n=200, consistency=0.50, p_eval=1.0, max_eval_days=2, fee=100)
    assert at_40["passed"].mean() == 0.0
    assert at_50["passed"].mean() == 1.0


def test_a_third_winning_day_clears_the_40_percent_rule():
    raw = lucid_recipe_run(np.random.default_rng(2), n=100, consistency=0.40, p_eval=1.0, max_eval_days=3, fee=100)
    assert raw["passed"].mean() == 1.0


def test_household_respects_the_funded_cap():
    # Smoke: the batch runs and does not require hedging.
    batch = household_batch(np.random.default_rng(3), n=30, fee=100, bankroll=2_000, days=5, p_eval=1.0)
    assert batch.month_cash.shape == (30,)
    assert np.isfinite(batch.month_cash).all()


def test_intraday_grading_blocks_the_second_full_size_loss():
    # Every scripted day wins. End-of-day grading banks five payouts. Intraday
    # grading liquidates the next $2,000 risk once a $2,000 withdrawal has left
    # about $1,900 of room above the lock.
    kw = {
        "n": 30,
        "consistency": 0.50,
        "p_eval": 1.0,
        "p_big": 1.0,
        "p_small": 1.0,
        "max_eval_days": 2,
        "fee": 100,
    }
    eod = lucid_recipe_run(np.random.default_rng(5), intraday=False, **kw)
    intra = lucid_recipe_run(np.random.default_rng(5), intraday=True, **kw)
    assert eod["passed"].all()
    assert intra["passed"].all()
    assert eod["n_pay"].min() == 5
    assert intra["n_pay"].max() == 1


def test_lucid_coin_charges_the_unconfirmed_fee_up_front():
    stat = lucid_coin(
        np.random.default_rng(6), n=40, stake=2_000, days=4, p=0.0, fee=80, cost=0
    )
    assert stat["pass_rate"] == 0.0
    assert stat["mean_fees"] == 80
    assert stat["mean"] == -80
    assert stat["payout_rate"] == 0.0


def test_symmetric_coin_is_not_the_cost_dragged_walk():
    # A fair ±$500 coin has zero trade expectancy. The function must run both
    # payout styles without crashing; the sign of EV is an output, not a fixture.
    raw = topstep_coin(np.random.default_rng(4), n=300, stake=500, days=40, payout="min", cost=0)
    dragged = topstep_coin(np.random.default_rng(4), n=300, stake=500, days=40, payout="min", cost=40)
    assert raw["mean_fees"] > 0
    assert dragged["mean"] < raw["mean"]
