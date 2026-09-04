"""Quant series video 3: the trading system (streaming, data classes, mock exchange, strategy API).

Building blocks, in the video's order:
  Tick            generic "handle one new data point" interface
  DequeWindow     fixed-size sliding window on a deque (O(1) push/pop at both ends)
  ArrayWindow     same thing on a numpy array (for the benchmark)
  LastValue       remembers the last tick
  LogReturn       turns a price stream into a log-return stream
  LogReturnLags   turns a price stream into the model's feature tensor [lag_1, lag_2, ..., lag_n]
  Order/Trade/Position, Account/Exchange (+ test doubles), Strategy/AutoRegressiveStrategy

Money is Decimal. Quantity is signed: + long, - short. For NQ a "unit" is one contract and
P&L = contracts * price change * point_value (20 for NQ, 2 for MNQ, 1 for spot-like assets).
"""
from __future__ import annotations

import math
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Generic, Optional, TypeVar

import numpy as np
import torch
from torch import nn

T = TypeVar("T")
U = TypeVar("U")


# ----------------------------------------------------------------------------- streaming
class Tick(ABC, Generic[T, U]):
    @abstractmethod
    def on_tick(self, value: T) -> Optional[U]: ...


class DequeWindow(Tick[T, Optional[T]]):
    """Keeps the last `capacity` values. on_tick returns the value that fell out, if any."""

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self._buf: deque[T] = deque()

    def on_tick(self, value: T) -> Optional[T]:
        dropped = self._buf.popleft() if len(self._buf) == self.capacity else None
        self._buf.append(value)
        return dropped

    def append_left(self, value: T) -> Optional[T]:
        dropped = self._buf.pop() if len(self._buf) == self.capacity else None
        self._buf.appendleft(value)
        return dropped

    def is_full(self) -> bool:
        return len(self._buf) == self.capacity

    def __len__(self) -> int:
        return len(self._buf)

    def __getitem__(self, i: int) -> T:
        return self._buf[i]

    def to_numpy(self, dtype=np.float32) -> np.ndarray:
        return np.fromiter(self._buf, dtype=dtype, count=len(self._buf))

    def __repr__(self) -> str:
        return f"DequeWindow(capacity={self.capacity}, size={len(self._buf)}, values={list(self._buf)})"


class ArrayWindow(Tick[float, Optional[float]]):
    """Same contract on a numpy array: every push shifts the whole buffer (O(n))."""

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self._buf = np.empty(capacity, dtype=np.float64)
        self._size = 0

    def on_tick(self, value: float) -> Optional[float]:
        dropped = None
        if self._size == self.capacity:
            dropped = float(self._buf[0])
            self._buf[:-1] = self._buf[1:]
            self._buf[-1] = value
        else:
            self._buf[self._size] = value
            self._size += 1
        return dropped

    def is_full(self) -> bool:
        return self._size == self.capacity

    def to_numpy(self, dtype=np.float32) -> np.ndarray:
        return self._buf[: self._size].astype(dtype)


class LastValue(Tick[T, T]):
    def __init__(self) -> None:
        self.value: Optional[T] = None

    def on_tick(self, value: T) -> T:
        self.value = value
        return value


class LogReturn(Tick[float, Optional[float]]):
    """Window of two prices -> log(p_t / p_{t-1}) once both are present."""

    def __init__(self) -> None:
        self.window: DequeWindow[float] = DequeWindow(2)

    def on_tick(self, price: float) -> Optional[float]:
        self.window.on_tick(price)
        if not self.window.is_full():
            return None
        return math.log(self.window[1] / self.window[0])


class LogReturnLags(Tick[float, Optional[torch.Tensor]]):
    """Streams prices -> [lag_1, lag_2, ..., lag_n] (most recent first) as a (1, n) float32 tensor."""

    def __init__(self, num_lags: int) -> None:
        self.num_lags = num_lags
        self.log_return = LogReturn()
        self.lags: DequeWindow[float] = DequeWindow(num_lags)

    def on_tick(self, price: float) -> Optional[torch.Tensor]:
        r = self.log_return.on_tick(price)
        if r is None:
            return None
        self.lags.append_left(r)
        if not self.lags.is_full():
            return None
        return torch.from_numpy(self.lags.to_numpy()).reshape(1, -1)  # zero-copy from numpy


# ----------------------------------------------------------------------------- data classes
def sign(x: Decimal) -> Decimal:
    return Decimal(1) if x > 0 else Decimal(-1) if x < 0 else Decimal(0)


@dataclass(frozen=True)
class Order:
    symbol: str
    signed_quantity: Decimal  # + buy/long, - sell/short


@dataclass(frozen=True)
class Trade:
    symbol: str
    signed_quantity: Decimal
    price: Decimal
    pnl: Decimal = Decimal(0)  # realised P&L released by this trade (0 when opening/increasing)
    fee: Decimal = Decimal(0)


@dataclass
class Position:
    symbol: str
    signed_quantity: Decimal
    price: Decimal          # average entry price
    point_value: Decimal = Decimal(1)

    def unrealised_pnl(self, mark_price: Decimal) -> Decimal:
        """Mark to market: what closing at `mark_price` right now would realise."""
        return self.signed_quantity * (mark_price - self.price) * self.point_value


# ----------------------------------------------------------------------------- account / exchange
class Account(ABC):
    @property
    @abstractmethod
    def balance(self) -> Decimal: ...

    @abstractmethod
    def get_position(self, symbol: str) -> Optional[Position]: ...


@dataclass
class TestAccount(Account):
    _balance: Decimal
    positions: dict[str, Position] = field(default_factory=dict)
    trades: list[Trade] = field(default_factory=list)

    @property
    def balance(self) -> Decimal:
        return self._balance

    def get_position(self, symbol: str) -> Optional[Position]:
        return self.positions.get(symbol)


class Exchange(Account):
    @abstractmethod
    def market_order(self, symbol: str, signed_quantity: Decimal, price: Decimal) -> Trade: ...


class TestExchange(Exchange):
    """Mock exchange: fills every market order at the given price (composition over inheritance).

    fee_per_unit_side: flat fee charged per unit traded, per side (NQ: commission + slippage ticks * $5).
    """

    def __init__(self, account: TestAccount, point_value: Decimal = Decimal(1), fee_per_unit_side: Decimal = Decimal(0)) -> None:
        self.account = account
        self.point_value = point_value
        self.fee_per_unit_side = fee_per_unit_side

    @property
    def balance(self) -> Decimal:
        return self.account.balance

    def get_position(self, symbol: str) -> Optional[Position]:
        return self.account.get_position(symbol)

    def market_order(self, symbol: str, signed_quantity: Decimal, price: Decimal) -> Trade:
        if signed_quantity == 0:
            raise ValueError("zero-quantity order")
        pos = self.account.positions.get(symbol)
        pnl = Decimal(0)
        fee = abs(signed_quantity) * self.fee_per_unit_side
        if pos is None or sign(pos.signed_quantity) == sign(signed_quantity):
            # open or increase: new average price
            if pos is None:
                self.account.positions[symbol] = Position(symbol, signed_quantity, price, self.point_value)
            else:
                total = pos.signed_quantity + signed_quantity
                pos.price = (pos.price * pos.signed_quantity + price * signed_quantity) / total
                pos.signed_quantity = total
        else:
            # reduce, close, or flip
            closed = min(abs(signed_quantity), abs(pos.signed_quantity)) * sign(pos.signed_quantity)
            pnl = closed * (price - pos.price) * self.point_value
            remaining = pos.signed_quantity + signed_quantity
            if remaining == 0:
                del self.account.positions[symbol]
            elif sign(remaining) == sign(pos.signed_quantity):
                pos.signed_quantity = remaining
            else:  # flipped through zero: leftover opens at this price
                self.account.positions[symbol] = Position(symbol, remaining, price, self.point_value)
        self.account._balance += pnl - fee
        trade = Trade(symbol, signed_quantity, price, pnl, fee)
        self.account.trades.append(trade)
        return trade


# ----------------------------------------------------------------------------- strategy API
class Strategy(ABC):
    """Like Tick, but also sees the account (needed for compounding sizing). Never sees the exchange."""

    @abstractmethod
    def on_tick(self, price: Decimal, account: Account) -> Optional[list[Order]]: ...


class AutoRegressiveStrategy(Strategy):
    """Each bar close: build lags -> model -> sign(y_hat) -> [close old position?, open new position]."""

    def __init__(
        self,
        symbol: str,
        model: nn.Module,
        num_lags: int,
        point_value: Decimal = Decimal(1),
        scale_factor: Optional[Decimal] = None,
        quantity_step: Optional[Decimal] = None,
    ) -> None:
        self.symbol = symbol
        self.model = model.eval()
        self.lags = LogReturnLags(num_lags)
        self.point_value = point_value
        self.scale_factor = scale_factor if scale_factor is not None else Decimal(1)  # leverage (>1) or fraction (<1)
        self.quantity_step = quantity_step  # e.g. Decimal(1) to round to whole contracts; None = fractional
        self.last_y_hat: Optional[float] = None

    def predict(self, x: torch.Tensor) -> float:
        with torch.no_grad():
            return float(self.model(x)[0].detach())

    def on_tick(self, price: Decimal, account: Account) -> Optional[list[Order]]:
        x = self.lags.on_tick(float(price))
        if x is None:
            return None
        self.last_y_hat = self.predict(x)
        return self.create_orders(self.last_y_hat, account, price)

    def create_orders(self, y_hat: float, account: Account, price: Decimal) -> list[Order]:
        direction = sign(Decimal(y_hat))
        notional = account.balance * self.scale_factor  # compounding: size from the live balance
        quantity = notional / (price * self.point_value)
        if self.quantity_step is not None:
            quantity = (quantity / self.quantity_step).to_integral_value(rounding="ROUND_DOWN") * self.quantity_step
        orders: list[Order] = []
        pos = account.get_position(self.symbol)
        if pos is not None:
            orders.append(Order(self.symbol, -pos.signed_quantity))  # close what we hold
        if quantity > 0 and direction != 0:
            orders.append(Order(self.symbol, direction * quantity))
        return orders


def execute(orders: Optional[list[Order]], exchange: Exchange, price: Decimal) -> list[Trade]:
    return [exchange.market_order(o.symbol, o.signed_quantity, price) for o in (orders or [])]
