"""Unit tests for src/quant/trading_system.py (video 3 building blocks)."""
import math
from decimal import Decimal

import pytest

pytest.importorskip("torch")
import torch  # noqa: E402
from torch import nn  # noqa: E402

from src.quant.trading_system import (  # noqa: E402
    ArrayWindow, AutoRegressiveStrategy, DequeWindow, LogReturn, LogReturnLags, Order, Position,
    TestAccount, TestExchange, execute,
)


def test_deque_window_drops_oldest():
    w = DequeWindow(3)
    assert [w.on_tick(v) for v in (1, 2, 3)] == [None, None, None]
    assert w.on_tick(4) == 1
    assert list(w.to_numpy()) == [2, 3, 4]
    assert w.is_full()


def test_array_window_matches_deque():
    a, d = ArrayWindow(4), DequeWindow(4)
    for v in range(10):
        assert a.on_tick(float(v)) == d.on_tick(float(v))
    assert list(a.to_numpy()) == list(d.to_numpy())


def test_log_return_stream_is_time_additive():
    lr = LogReturn()
    out = [lr.on_tick(p) for p in (100, 120, 100)]
    assert out[0] is None
    assert math.isclose(out[1], math.log(1.2))
    assert math.isclose(out[1] + out[2], 0.0, abs_tol=1e-12)


def test_lags_are_most_recent_first():
    lags = LogReturnLags(3)
    prices = [90.0, 100.0, 120.0, 100.0, 110.0]
    xs = [lags.on_tick(p) for p in prices]
    assert xs[:3] == [None, None, None]
    expected = [math.log(prices[i] / prices[i - 1]) for i in (4, 3, 2)]
    assert torch.allclose(xs[4], torch.tensor([expected], dtype=torch.float32))
    assert xs[4].shape == (1, 3)


def test_exchange_open_close_pnl_and_flip():
    acct = TestAccount(Decimal(50))
    ex = TestExchange(acct)
    ex.market_order("X", Decimal(5), Decimal(10))
    assert ex.get_position("X") == Position("X", Decimal(5), Decimal(10), Decimal(1))
    assert ex.get_position("X").unrealised_pnl(Decimal(15)) == Decimal(25)
    t = ex.market_order("X", Decimal(-5), Decimal(15))
    assert t.pnl == Decimal(25) and ex.balance == Decimal(75) and ex.get_position("X") is None
    # flip through zero: close 2 long at 12 (+4), open 3 short at 12
    ex.market_order("X", Decimal(2), Decimal(10))
    t = ex.market_order("X", Decimal(-5), Decimal(12))
    assert t.pnl == Decimal(4)
    assert ex.get_position("X").signed_quantity == Decimal(-3)
    assert ex.get_position("X").price == Decimal(12)


def test_exchange_point_value_and_fees():
    acct = TestAccount(Decimal(10_000))
    ex = TestExchange(acct, point_value=Decimal(20), fee_per_unit_side=Decimal("7.5"))
    ex.market_order("NQ", Decimal(1), Decimal(20_000))
    ex.market_order("NQ", Decimal(-1), Decimal(20_010))
    assert ex.balance == Decimal(10_000) + Decimal(200) - Decimal(15)


class _FixedModel(nn.Module):
    def __init__(self, value: float) -> None:
        super().__init__()
        self.value = value

    def forward(self, x):
        return torch.full((x.shape[0], 1), self.value)


def test_strategy_closes_then_opens_and_sizes_from_balance():
    acct = TestAccount(Decimal(1000))
    ex = TestExchange(acct, point_value=Decimal(1))
    strat = AutoRegressiveStrategy("S", _FixedModel(-0.001), num_lags=2, scale_factor=Decimal(2))
    assert strat.on_tick(Decimal(10), ex) is None
    assert strat.on_tick(Decimal(11), ex) is None
    orders = strat.on_tick(Decimal(10), ex)
    assert orders == [Order("S", Decimal(-200))]  # 1000 * 2x / 10, short
    execute(orders, ex, Decimal(10))
    orders = strat.on_tick(Decimal(9), ex)
    assert orders[0] == Order("S", Decimal(200))  # close the short first (+200 pnl)
    assert orders[1].signed_quantity < 0
    execute(orders, ex, Decimal(9))
    assert ex.balance == Decimal(1200)


def test_strategy_rounds_to_whole_contracts():
    acct = TestAccount(Decimal(100_000))
    ex = TestExchange(acct, point_value=Decimal(20))
    strat = AutoRegressiveStrategy("NQ", _FixedModel(0.001), 1, Decimal(20), Decimal(1), quantity_step=Decimal(1))
    strat.on_tick(Decimal(20_000), ex)
    orders = strat.on_tick(Decimal(20_000), ex)
    assert orders == []  # 100k / (20k*20) = 0.25 contracts -> rounds down to 0 -> no order
    strat = AutoRegressiveStrategy("NQ", _FixedModel(0.001), 1, Decimal(20), Decimal(10), quantity_step=Decimal(1))
    strat.on_tick(Decimal(20_000), ex)
    assert strat.on_tick(Decimal(20_000), ex) == [Order("NQ", Decimal(2))]
