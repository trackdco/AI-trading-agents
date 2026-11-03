"""Lifecycle search. Losses, fees, activation and payouts until the account stops.

The search half and the confirmation half use different random seeds. A
policy's published interval comes from the confirmation half only.

Edge is net R after costs unless mode is "gross0". Gross zero is a random
walk in the intended payoff (win probability 1/(1+k)) with MNQ commission
and one tick of slippage each side taken out of the dollars. That is the
no-skill case.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.research.strategies.costs import COMMISSION_RT_USD, MNQ_DOLLARS_PER_POINT

# Confirmed rule constants. Pro funded caps are not here on purpose.
TOPSTEP = {
    50_000: {"mll": 2_000, "target": 3_000, "consistency": 0.55, "monthly": 49.0, "activation": 149.0, "cap": 2_000, "win_min": 150.0},
    100_000: {"mll": 3_000, "target": 6_000, "consistency": 0.55, "monthly": 99.0, "activation": 149.0, "cap": 3_000, "win_min": 150.0},
    150_000: {"mll": 4_500, "target": 9_000, "consistency": 0.55, "monthly": 199.0, "activation": 149.0, "cap": 5_000, "win_min": 150.0},
}
LUCIDFLEX = {
    50_000: {"mll": 2_000, "target": 3_000, "consistency": 0.40, "trail": 52_100, "lock": 50_100, "cap": 2_000, "win_min": 150.0},
    100_000: {"mll": 3_000, "target": 6_000, "consistency": 0.40, "trail": 103_100, "lock": 100_100, "cap": 2_500, "win_min": 200.0},
    150_000: {"mll": 4_500, "target": 9_000, "consistency": 0.40, "trail": 154_600, "lock": 150_100, "cap": 3_000, "win_min": 250.0},
}


@dataclass(frozen=True)
class Policy:
    risk: float
    reward_r: float
    trades_per_day: int
    daily_loss_r: float | None
    daily_win_r: float | None
    retire_after_payouts: int | None
    attempts: int
    stop_points: float = 16.0

    def label(self) -> str:
        dl = "none" if self.daily_loss_r is None else f"{self.daily_loss_r:g}R"
        dw = "none" if self.daily_win_r is None else f"{self.daily_win_r:g}R"
        ret = "bust" if self.retire_after_payouts is None else str(self.retire_after_payouts)
        return (
            f"risk ${self.risk:g} / {self.reward_r:g}R / {self.trades_per_day}/day / "
            f"day-stop {dl} / day-bank {dw} / retire {ret} / attempts {self.attempts} / "
            f"stop {self.stop_points:g}pt"
        )


def grid() -> list[Policy]:
    out = []
    for risk in (150.0, 400.0, 1000.0):
        for reward in (0.25, 0.5, 1.0, 2.0):
            for tpd in (1, 2, 4):
                for dloss in (None, 2.0):
                    for dwin in (None, 2.0):
                        for retire in (1, None):
                            for attempts in (1, 3):
                                out.append(Policy(risk, reward, tpd, dloss, dwin, retire, attempts))
    return out


def payout_dollars(policy: Policy, mode: str, edge: float) -> tuple[float, float, float]:
    """Return win dollars, loss dollars, win probability."""
    k = policy.reward_r
    if mode == "gross0":
        contracts = policy.risk / (policy.stop_points * MNQ_DOLLARS_PER_POINT)
        slip_pts = 0.5  # one tick each side
        cost = (COMMISSION_RT_USD + slip_pts * MNQ_DOLLARS_PER_POINT) * contracts
        win = k * policy.risk - cost
        loss = policy.risk + cost
        return win, loss, 1.0 / (1.0 + k)
    if mode != "net":
        raise ValueError(mode)
    p = (edge + 1.0) / (k + 1.0)
    if not 0.0 < p < 1.0:
        raise ValueError(f"edge {edge} is not feasible at {k}R")
    return k * policy.risk, policy.risk, p


def _day_pnls(
    rng: np.random.Generator,
    n: int,
    days: int,
    policy: Policy,
    win: float,
    loss: float,
    p: float,
    samples: np.ndarray | None = None,
) -> np.ndarray:
    if samples is not None and len(samples):
        raw = rng.choice(samples, size=(n, days, policy.trades_per_day)) * policy.risk
    else:
        raw = np.where(rng.random((n, days, policy.trades_per_day)) < p, win, -loss)
    if policy.daily_loss_r is None and policy.daily_win_r is None:
        return raw
    taken = np.zeros_like(raw)
    cum = np.zeros((n, days))
    for t in range(policy.trades_per_day):
        allow = np.ones((n, days), dtype=bool)
        if policy.daily_loss_r is not None:
            allow &= cum > -policy.daily_loss_r * policy.risk
        if policy.daily_win_r is not None:
            allow &= cum < policy.daily_win_r * policy.risk
        shock = np.where(allow, raw[:, :, t], 0.0)
        taken[:, :, t] = shock
        cum = cum + shock
    return taken


def _fees(days: np.ndarray, passed: np.ndarray, monthly: float, activation: float) -> np.ndarray:
    months = np.maximum(1, np.ceil(np.maximum(days, 1) / 21.0))
    return months * monthly + np.where(passed, activation, 0.0)


def run_topstep(
    size: int,
    policy: Policy,
    mode: str,
    edge: float,
    n: int,
    rng: np.random.Generator,
    eval_days: int = 100,
    funded_days: int = 120,
    samples: np.ndarray | None = None,
) -> np.ndarray:
    """Net dollars per sim: trader payouts minus fees, over `attempts` tries."""
    spec = TOPSTEP[size]
    win, loss, p = payout_dollars(policy, mode, edge)
    cash = np.zeros(n)
    fees = np.zeros(n)
    still = np.ones(n, dtype=bool)
    for _attempt in range(policy.attempts):
        if not still.any():
            break
        pnl = _day_pnls(rng, n, eval_days, policy, win, loss, p, samples)
        balance = np.full(n, float(size))
        floor = np.full(n, float(size - spec["mll"]))
        high = balance.copy()
        best = np.zeros(n)
        alive = still.copy()
        passed = np.zeros(n, dtype=bool)
        days_used = np.ones(n)
        frozen = ~still
        for d in range(eval_days):
            if not (alive & ~passed).any():
                break
            day = np.zeros(n)
            for t in range(policy.trades_per_day):
                shock = pnl[:, d, t]
                tradable = alive & ~passed & (shock != 0.0)
                balance = np.where(tradable, balance + shock, balance)
                day = np.where(tradable, day + shock, day)
                dead = tradable & (balance <= floor)
                alive &= ~dead
            finished = alive & ~passed & ~frozen
            best = np.where(finished, np.maximum(best, day), best)
            high = np.where(finished, np.maximum(high, balance), high)
            proposed = high - spec["mll"]
            floor = np.where(finished, np.minimum(float(size), np.maximum(floor, proposed)), floor)
            profit = balance - size
            need = np.maximum(spec["target"], np.where(best > 0, best / spec["consistency"], spec["target"]))
            now = finished & (profit + 1e-6 >= need)
            passed |= now
            active_now = ~frozen
            days_used = np.where(active_now, d + 1, days_used)
            frozen |= active_now & (~alive | passed)
            alive &= ~now
        fees = fees + np.where(still, _fees(days_used, passed, spec["monthly"], spec["activation"]), 0.0)
        # funded
        f_pnl = _day_pnls(rng, n, funded_days, policy, win, loss, p, samples)
        f_bal = np.zeros(n)
        f_floor = np.full(n, -float(spec["mll"]))
        f_high = np.zeros(n)
        f_alive = still & passed
        wins = np.zeros(n)
        cycle = np.zeros(n)
        pays = np.zeros(n)
        got = np.zeros(n)
        for d in range(funded_days):
            if not f_alive.any():
                break
            day = np.zeros(n)
            for t in range(policy.trades_per_day):
                shock = f_pnl[:, d, t]
                tradable = f_alive & (shock != 0.0)
                f_bal = np.where(tradable, f_bal + shock, f_bal)
                day = np.where(tradable, day + shock, day)
                dead = tradable & (f_bal <= f_floor)
                f_alive &= ~dead
            active = f_alive
            wins = np.where(active & (day >= spec["win_min"]), wins + 1, wins)
            cycle = np.where(active, cycle + day, cycle)
            f_high = np.where(active, np.maximum(f_high, f_bal), f_high)
            proposed = f_high - spec["mll"]
            f_floor = np.where(active, np.minimum(0.0, np.maximum(f_floor, proposed)), f_floor)
            eligible = active & (wins >= 5) & ((pays == 0) | (cycle > 0))
            amount = np.minimum(spec["cap"], 0.5 * np.maximum(f_bal, 0.0))
            take = eligible & (amount >= 125.0)
            if policy.retire_after_payouts is not None:
                take &= pays < policy.retire_after_payouts
            f_bal = np.where(take, f_bal - amount, f_bal)
            got = np.where(take, got + amount * 0.9, got)
            pays = np.where(take, pays + 1, pays)
            wins = np.where(take, 0.0, wins)
            cycle = np.where(take, 0.0, cycle)
            f_floor = np.where(take, 0.0, f_floor)
            f_alive &= ~((pays >= (policy.retire_after_payouts or 10**9)) & take)
            dead_after = take & (f_bal <= f_floor)
            f_alive &= ~dead_after
        cash = cash + np.where(still & passed, got, 0.0)
        still &= ~passed
    return cash - fees


def run_lucidflex(
    size: int,
    policy: Policy,
    mode: str,
    edge: float,
    n: int,
    rng: np.random.Generator,
    fee: float,
    eval_days: int = 100,
    funded_days: int = 120,
    samples: np.ndarray | None = None,
) -> np.ndarray:
    spec = LUCIDFLEX[size]
    win, loss, p = payout_dollars(policy, mode, edge)
    cash = np.zeros(n)
    fees = np.zeros(n)
    still = np.ones(n, dtype=bool)
    for _attempt in range(policy.attempts):
        if not still.any():
            break
        pnl = _day_pnls(rng, n, eval_days, policy, win, loss, p, samples)
        balance = np.full(n, float(size))
        floor = np.full(n, float(size - spec["mll"]))
        high = balance.copy()
        best = np.zeros(n)
        alive = still.copy()
        passed = np.zeros(n, dtype=bool)
        locked = np.zeros(n, dtype=bool)
        for d in range(eval_days):
            if not alive.any():
                break
            day = np.zeros(n)
            for t in range(policy.trades_per_day):
                shock = pnl[:, d, t]
                tradable = alive & ~passed & (shock != 0.0)
                balance = np.where(tradable, balance + shock, balance)
                day = np.where(tradable, day + shock, day)
                dead = tradable & (balance <= floor)
                alive &= ~dead
            finished = alive & ~passed
            best = np.where(finished, np.maximum(best, day), best)
            high = np.where(finished, np.maximum(high, balance), high)
            lock_now = finished & ~locked & (high + 1e-9 >= spec["trail"])
            floor = np.where(lock_now, float(spec["lock"]), floor)
            locked |= lock_now
            trailed = finished & ~locked
            floor = np.where(trailed, np.maximum(floor, high - spec["mll"]), floor)
            profit = balance - size
            need = np.maximum(spec["target"], np.where(best > 0, best / spec["consistency"], spec["target"]))
            now = finished & (profit + 1e-6 >= need)
            passed |= now
            alive &= ~now
        fees = fees + np.where(still, fee, 0.0)  # one-time fee per attempt; dollar amount is an assumption
        f_pnl = _day_pnls(rng, n, funded_days, policy, win, loss, p, samples)
        f_bal = np.full(n, float(size))
        f_floor = np.full(n, float(size - spec["mll"]))
        f_high = f_bal.copy()
        f_alive = still & passed
        f_locked = np.zeros(n, dtype=bool)
        wins = np.zeros(n)
        cycle = np.zeros(n)
        pays = np.zeros(n)
        got = np.zeros(n)
        for d in range(funded_days):
            if not f_alive.any():
                break
            day = np.zeros(n)
            for t in range(policy.trades_per_day):
                shock = f_pnl[:, d, t]
                tradable = f_alive & (shock != 0.0)
                f_bal = np.where(tradable, f_bal + shock, f_bal)
                day = np.where(tradable, day + shock, day)
                dead = tradable & (f_bal <= f_floor)
                f_alive &= ~dead
            active = f_alive
            wins = np.where(active & (day >= spec["win_min"]), wins + 1, wins)
            cycle = np.where(active, cycle + day, cycle)
            f_high = np.where(active, np.maximum(f_high, f_bal), f_high)
            lock_now = active & ~f_locked & (f_high + 1e-9 >= spec["trail"])
            f_floor = np.where(lock_now, float(spec["lock"]), f_floor)
            f_locked |= lock_now
            trailed = active & ~f_locked
            f_floor = np.where(trailed, np.maximum(f_floor, f_high - spec["mll"]), f_floor)
            amount = np.minimum(spec["cap"], 0.5 * np.maximum(cycle, 0.0))
            eligible = active & (wins >= 5) & (cycle > 0) & (amount >= 500.0)
            if policy.retire_after_payouts is not None:
                eligible &= pays < policy.retire_after_payouts
            eligible &= pays < 5
            f_bal = np.where(eligible, f_bal - amount, f_bal)
            got = np.where(eligible, got + amount * 0.9, got)
            pays = np.where(eligible, pays + 1, pays)
            wins = np.where(eligible, 0.0, wins)
            cycle = np.where(eligible, 0.0, cycle)
            f_floor = np.where(eligible, float(spec["lock"]), f_floor)
            f_locked = np.where(eligible, True, f_locked)
            if policy.retire_after_payouts is None:
                stop = eligible & (pays >= 5)
            else:
                stop = eligible & ((pays >= policy.retire_after_payouts) | (pays >= 5))
            f_alive &= ~stop
            f_alive &= ~(eligible & (f_bal <= f_floor))
        cash = cash + np.where(still & passed, got, 0.0)
        still &= ~passed
    return cash - fees


def summarise(net: np.ndarray) -> dict[str, float]:
    mean = float(net.mean())
    se = float(net.std(ddof=1) / np.sqrt(len(net)))
    return {"ev": mean, "lo": mean - 1.96 * se, "hi": mean + 1.96 * se, "n": float(len(net))}


PREDECLARED = Policy(200.0, 1.0, 2, None, None, None, 1)
ANGUS_POLICY = Policy(200.0, 0.25, 4, 2.0, 2.0, 1, 3)
