"""Pass / payout Monte Carlo on a two-point trade distribution.

Each trade is a win of `avg_win` with probability `win_rate`, otherwise a
loss of `avg_loss`. Trades are independent. That is the distribution the
caller asked for. It is not a claim about NQ.

Zero edge means win_rate * avg_win == (1 - win_rate) * avg_loss.
The research brief's closed form P = drawdown / (drawdown + target) = 40%
is the infinite-horizon static-floor case with no consistency rule and no
costs. Trailing floors, a consistency rule, and a day cap all push a
zero-edge pass rate lower. This module measures that. It does not trust
the brief's table.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.research.prop.account import PropAccount
from src.research.prop.rules import AccountRules


@dataclass(frozen=True)
class TradeDistribution:
    win_rate: float
    avg_win: float
    avg_loss: float
    trades_per_day: int = 2

    def __post_init__(self) -> None:
        if not 0.0 < self.win_rate < 1.0:
            raise ValueError("win_rate must be between 0 and 1")
        if self.avg_win <= 0 or self.avg_loss <= 0:
            raise ValueError("avg_win and avg_loss are positive dollar amounts")
        if self.trades_per_day < 1:
            raise ValueError("trades_per_day must be at least 1")

    @property
    def expectancy(self) -> float:
        p = self.win_rate
        return p * self.avg_win - (1.0 - p) * self.avg_loss

    @classmethod
    def no_edge(cls, risk: float, trades_per_day: int = 2) -> TradeDistribution:
        return cls(win_rate=0.5, avg_win=risk, avg_loss=risk, trades_per_day=trades_per_day)


@dataclass
class SimResult:
    key: str
    n_sims: int
    max_days: int
    pass_rate: float
    bust_rate: float
    mean_days_if_pass: float
    expected_fees: float
    fee_unconfirmed: bool
    expected_payout_count: float
    expected_trader_cash: float
    expected_cost_per_payout: float
    ev_per_eval: float
    assumptions: tuple[str, ...]


def _draw(dist: TradeDistribution, rng: np.random.Generator) -> float:
    if rng.random() < dist.win_rate:
        return dist.avg_win
    return -dist.avg_loss


def _eval_fees(rules: AccountRules, days_used: int, passed: bool) -> tuple[float, bool]:
    fees = rules.fees or {}
    unconfirmed = bool(fees.get("fee_status") == "unconfirmed" or fees.get("onetime") is None and "monthly" not in fees)
    if fees.get("monthly") is not None:
        months = max(1, int(np.ceil(max(days_used, 1) / 21.0)))
        cost = months * float(fees["monthly"])
        if passed:
            cost += float(fees.get("activation_if_pass") or 0.0)
        return cost, False
    if fees.get("onetime") is None:
        return 0.0, True
    return float(fees["onetime"]), unconfirmed


def run_paths(
    rules: AccountRules,
    dist: TradeDistribution,
    *,
    n_sims: int = 2000,
    max_days: int = 60,
    seed: int = 20261103,
    funded: AccountRules | None = None,
    funded_days: int = 60,
    micros: int = 1,
) -> SimResult:
    """Simulate `n_sims` independent accounts.

    `funded`, when given, starts a fresh funded account after an eval pass.
    Eval profit does not carry. Fees are the eval's fees only.
    """
    rng = np.random.default_rng(seed)
    passes = 0
    busts = 0
    pass_days = []
    fees = []
    fee_flags = []
    payouts = []
    cash = []
    for _ in range(n_sims):
        account = PropAccount(rules)
        for _day in range(max_days):
            if account.failed or account.passed:
                break
            for _trade in range(dist.trades_per_day):
                if account.failed or account.blocked or account.passed:
                    break
                account.apply(_draw(dist, rng), micros=micros)
            account.end_day()
        if account.passed:
            passes += 1
            pass_days.append(account.days)
        if account.failed:
            busts += 1
        cost, unknown = _eval_fees(rules, account.days, account.passed)
        fee_flags.append(unknown)
        trader = 0.0
        n_pay = 0
        if account.passed and funded is not None:
            live = PropAccount(funded)
            for _day in range(funded_days):
                if live.failed:
                    break
                for _trade in range(dist.trades_per_day):
                    if live.failed or live.blocked:
                        break
                    live.apply(_draw(dist, rng), micros=micros)
                live.end_day()
            trader = live.trader_cash
            n_pay = live.payout_count
        elif rules.stage == "funded":
            trader = account.trader_cash
            n_pay = account.payout_count
        fees.append(cost)
        payouts.append(n_pay)
        cash.append(trader)

    n = float(n_sims)
    expected_fees = float(np.mean(fees))
    expected_payouts = float(np.mean(payouts))
    expected_cash = float(np.mean(cash))
    if expected_payouts > 0:
        cost_per = expected_fees / expected_payouts
    else:
        cost_per = float("inf")
    return SimResult(
        key=rules.key,
        n_sims=n_sims,
        max_days=max_days,
        pass_rate=passes / n,
        bust_rate=busts / n,
        mean_days_if_pass=float(np.mean(pass_days)) if pass_days else float("nan"),
        expected_fees=expected_fees,
        fee_unconfirmed=any(fee_flags),
        expected_payout_count=expected_payouts,
        expected_trader_cash=expected_cash,
        expected_cost_per_payout=cost_per,
        ev_per_eval=expected_cash - expected_fees,
        assumptions=(
            "independent two-point trades, no slippage, no commission",
            "each fill is realized immediately, so intraday open heat is the fill itself",
            "a pass is marked at the session close, a max-loss breach on the fill",
            "eval profit does not carry into a funded account",
            "21 trading days per billed month when the firm charges monthly",
            "Topstep payout cap is the standard cap, not the limited-time DLL cap",
            "LucidFlex payout uses 50% of cycle profit, which is one of the two wordings on the page",
        ),
    )


def static_floor_pass_rate(
    drawdown: float,
    target: float,
    dist: TradeDistribution,
    *,
    n_sims: int = 2000,
    max_days: int = 400,
    seed: int = 7,
) -> float:
    """Zero-rule coin: fail at -drawdown, pass at +target, floor never moves.

    With no edge and a long horizon this approaches drawdown / (drawdown + target).
    """
    rng = np.random.default_rng(seed)
    passes = 0
    for _ in range(n_sims):
        equity = 0.0
        done = False
        for _day in range(max_days):
            for _trade in range(dist.trades_per_day):
                equity += _draw(dist, rng)
                if equity <= -drawdown:
                    done = True
                    break
                if equity >= target:
                    passes += 1
                    done = True
                    break
            if done:
                break
    return passes / n_sims
