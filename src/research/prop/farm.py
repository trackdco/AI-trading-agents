"""The prop-farm claim, on the published rules.

This does not place orders. A "coin" here is a closed trade of +X or -X with
equal probability and no commission. That is not the same object as the
gross-zero random walk in optimise.py, which pays the MNQ commission and one
tick of slippage on both sides.

LucidFlex eval consistency is 40% unless the 50% add-on is on. Two equal days
that land exactly on the profit target are a 50% best day, so they pass the
add-on and fail the default. The add-on's dollar price is not on the help
page. Household caps used here are the ones in the notes (10 evals, 5 funded,
10 combined), cited to Lucid's general FAQ.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# 25K payout minimums follow the same help page as the 50K: $500 minimum
# request, winning day $100, cap $1,000. 100K winning day is $200, cap $2,500.
FLEX = {
    25_000: {"mll": 1_000, "target": 1_250, "trail": 26_100, "lock": 25_100, "cap": 1_000, "win_min": 100.0, "min_pay": 500.0},
    50_000: {"mll": 2_000, "target": 3_000, "trail": 52_100, "lock": 50_100, "cap": 2_000, "win_min": 150.0, "min_pay": 500.0},
    100_000: {"mll": 3_000, "target": 6_000, "trail": 103_100, "lock": 100_100, "cap": 2_500, "win_min": 200.0, "min_pay": 500.0},
}
TOPSTEP_50 = {"mll": 2_000.0, "target": 3_000.0, "consistency": 0.55, "monthly": 49.0, "activation": 149.0, "cap": 2_000.0, "win_min": 150.0, "min_pay": 125.0}


def summarise(x: np.ndarray) -> dict[str, float]:
    x = np.asarray(x, dtype=float)
    mean = float(x.mean())
    se = float(x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 1 else 0.0
    return {"mean": mean, "lo": mean - 1.96 * se, "hi": mean + 1.96 * se, "p_pos": float(np.mean(x > 0))}


def _coin(rng: np.random.Generator, n: int, win: float, loss: float, p: float = 0.5) -> np.ndarray:
    return np.where(rng.random(n) < p, win, -loss)


def _apply(balance, floor, pnl, alive):
    balance = np.where(alive, balance + pnl, balance)
    dead = alive & (balance <= floor + 1e-9)
    return balance, dead


def topstep_coin(
    rng: np.random.Generator,
    n: int = 4000,
    stake: float = 500.0,
    days: int = 252,
    payout: str = "max",
    charge_activation: bool = True,
    intraday: bool = False,
    cost: float = 0.0,
    p: float = 0.5,
    split: float = 0.9,
    winning_days: int = 5,
    monthly: float = 49.0,
    activation_fee: float = 149.0,
    xfa: bool = True,
    trail: bool = True,
    reset_floor: bool = True,
    fixed_payout: float | None = None,
    payout_floor: float | None = None,
) -> dict[str, float]:
    """One Topstep 50K attempt: ±stake once a day, then the funded account until it dies.

    `cost` is subtracted from a win and added to a loss (commission and slippage).
    `payout='min'` requests $125 whenever half the balance covers it. `max` requests
    half the balance, capped at $2,000. Intraday mode refuses the coin, and busts,
    when the stake is larger than the room under the current floor. A bracket that
    fits inside the floor has the same intraday and end-of-day outcome, because a
    winner never trades through its stop. `p` is the win probability. 0.5 is the
    slideshow coin. The floor updates from the closed balance. Intraday mode is the
    breach check on the open loss, which is how Topstep monitors the max-loss line.
    """
    win = stake - cost
    loss = stake + cost
    # eval
    balance = np.full(n, 50_000.0)
    floor = np.full(n, 48_000.0)
    high = balance.copy()
    best = np.zeros(n)
    alive = np.ones(n, dtype=bool)
    passed = np.zeros(n, dtype=bool)
    day_count = np.ones(n)
    frozen = np.zeros(n, dtype=bool)
    for d in range(days):
        trading = alive & ~passed
        if not trading.any():
            break
        room = balance - floor
        pnl = _coin(rng, n, win, loss, p)
        bust_now = trading & intraday & (loss > room + 1e-9)
        alive &= ~bust_now
        trading = alive & ~passed
        balance, dead = _apply(balance, floor, np.where(trading, pnl, 0.0), trading)
        alive &= ~dead
        trading = alive & ~passed
        day_pnl = np.where(trading, pnl, 0.0)
        best = np.where(trading, np.maximum(best, day_pnl), best)
        if trail:
            high = np.where(trading, np.maximum(high, balance), high)
            floor = np.where(trading, np.minimum(50_000.0, np.maximum(floor, high - 2_000.0)), floor)
        profit = balance - 50_000.0
        need = np.maximum(3_000.0, np.where(best > 0, best / 0.55, 3_000.0))
        now = trading & (profit + 1e-6 >= need)
        passed |= now
        active = ~frozen
        day_count = np.where(active, d + 1, day_count)
        frozen |= active & (~alive | passed)
    months = np.maximum(1, np.ceil(day_count / 21.0))
    fees = months * monthly + np.where(passed & charge_activation, activation_fee, 0.0)
    # funded. An XFA starts at $0. `xfa=False` starts it at the combine balance.
    if xfa:
        f_bal = np.zeros(n)
        f_floor = np.full(n, -2_000.0)
        f_high = np.zeros(n)
        lock_at = 0.0
    else:
        f_bal = np.full(n, 50_000.0)
        f_floor = np.full(n, 48_000.0)
        f_high = f_bal.copy()
        lock_at = 50_000.0
    f_alive = passed.copy()
    wins = np.zeros(n)
    cycle = np.zeros(n)
    cash = np.zeros(n)
    n_pay = np.zeros(n)
    ever = np.zeros(n, dtype=bool)
    for _d in range(days):
        trading = f_alive
        if not trading.any():
            break
        room = f_bal - f_floor
        pnl = _coin(rng, n, win, loss, p)
        bust_now = trading & intraday & (loss > room + 1e-9)
        f_alive &= ~bust_now
        trading = f_alive
        f_bal, dead = _apply(f_bal, f_floor, np.where(trading, pnl, 0.0), trading)
        f_alive &= ~dead
        trading = f_alive
        day_pnl = np.where(trading, pnl, 0.0)
        wins = np.where(trading & (day_pnl >= 150.0), wins + 1, wins)
        cycle = np.where(trading, cycle + day_pnl, cycle)
        if trail:
            f_high = np.where(trading, np.maximum(f_high, f_bal), f_high)
            f_floor = np.where(
                trading, np.minimum(lock_at, np.maximum(f_floor, f_high - 2_000.0)), f_floor
            )
        eligible = trading & (wins >= winning_days) & ((n_pay == 0) | (cycle > 0))
        half = 0.5 * np.maximum(f_bal, 0.0)
        if payout == "max":
            amount = np.minimum(2_000.0, half)
        elif fixed_payout is not None:
            amount = np.where(half + 1e-9 >= fixed_payout, fixed_payout, 0.0)
        else:
            amount = np.where(half >= 125.0, 125.0, 0.0)
        take = eligible & (amount >= 125.0)
        f_bal = np.where(take, f_bal - amount, f_bal)
        cash = np.where(take, cash + amount * split, cash)
        n_pay = np.where(take, n_pay + 1, n_pay)
        ever |= take
        wins = np.where(take, 0.0, wins)
        cycle = np.where(take, 0.0, cycle)
        if reset_floor:
            reset_to = lock_at if payout_floor is None else payout_floor
            f_floor = np.where(take, reset_to, f_floor)
        f_alive &= ~(take & (f_bal <= f_floor))
    net = cash - fees
    stat = summarise(net)
    passed_m = passed.astype(bool)
    stat.update({
        "pass_rate": float(passed_m.mean()),
        "payout_rate": float(ever.mean()),
        "mean_payouts": float(n_pay.mean()),
        "mean_cash": float(cash.mean()),
        "mean_fees": float(fees.mean()),
        "median_net": float(np.median(net)),
        "median_cash": float(np.median(cash)),
        "fees_per_pass": float(fees.sum() / passed_m.sum()) if passed_m.any() else float("nan"),
    })
    stat.update(_funded_stats(cash, ever, n_pay, f_alive, passed_m, finished=np.zeros(n, dtype=bool)))
    return stat


def _funded_stats(cash, ever, n_pay, alive, passed, finished) -> dict[str, float]:
    """Stats on the funded accounts only. `finished` hit the payout cap without dying."""
    if not np.any(passed):
        return {
            "median_cash_if_passed": float("nan"),
            "mean_cash_if_passed": float("nan"),
            "payout_given_pass": float("nan"),
            "dead_given_pass": float("nan"),
            "still_given_pass": float("nan"),
            "mean_payouts_if_passed": float("nan"),
        }
    return {
        "median_cash_if_passed": float(np.median(cash[passed])),
        "mean_cash_if_passed": float(cash[passed].mean()),
        "payout_given_pass": float(ever[passed].mean()),
        "dead_given_pass": float((~alive & ~finished & passed).sum() / passed.sum()),
        "still_given_pass": float((alive & passed).sum() / passed.sum()),
        "mean_payouts_if_passed": float(n_pay[passed].mean()),
    }


def _flex_trail(balance, floor, high, locked, alive, spec):
    high = np.where(alive, np.maximum(high, balance), high)
    lock_now = alive & ~locked & (high + 1e-9 >= spec["trail"])
    floor = np.where(lock_now, float(spec["lock"]), floor)
    locked = locked | lock_now
    trailed = alive & ~locked
    floor = np.where(trailed, np.maximum(floor, high - spec["mll"]), floor)
    return floor, high, locked


def lucid_coin(
    rng: np.random.Generator,
    n: int = 4000,
    stake: float = 500.0,
    days: int = 252,
    payout: str = "max",
    intraday: bool = False,
    cost: float = 0.0,
    fee: float = 100.0,
    consistency: float = 0.40,
    p: float = 0.5,
    size: int = 50_000,
) -> dict[str, float]:
    """One LucidFlex attempt at ±stake once a day.

    The fee is one-time and unconfirmed, so the caller passes it. There is no
    activation fee. Eval consistency defaults to 40%. A $500 day does not raise
    the $3,000 target, because $500 / 0.40 is below $3,000. Funded payouts are
    half of cycle profit, capped, at least the account's minimum request, 90%
    to the trader, at most 5. The floor locks at the published buffer. Intraday
    mode is a re-grade: LucidFlex's own max-loss check is end of day.
    """
    spec = FLEX[size]
    win = stake - cost
    loss = stake + cost
    mll = float(spec["mll"])
    target = float(spec["target"])
    balance = np.full(n, float(size))
    floor = np.full(n, float(size) - mll)
    high = balance.copy()
    locked = np.zeros(n, dtype=bool)
    best = np.zeros(n)
    alive = np.ones(n, dtype=bool)
    passed = np.zeros(n, dtype=bool)
    for _d in range(days):
        trading = alive & ~passed
        if not trading.any():
            break
        room = balance - floor
        pnl = _coin(rng, n, win, loss, p)
        alive &= ~(trading & intraday & (loss > room + 1e-9))
        trading = alive & ~passed
        balance, dead = _apply(balance, floor, np.where(trading, pnl, 0.0), trading)
        alive &= ~dead
        trading = alive & ~passed
        day_pnl = np.where(trading, pnl, 0.0)
        best = np.where(trading, np.maximum(best, day_pnl), best)
        floor, high, locked = _flex_trail(balance, floor, high, locked, trading, spec)
        profit = balance - size
        need = np.maximum(target, np.where(best > 0, best / consistency, target))
        passed |= trading & (profit + 1e-6 >= need)
    f_bal = np.full(n, float(size))
    f_floor = np.full(n, float(size) - mll)
    f_high = f_bal.copy()
    f_locked = np.zeros(n, dtype=bool)
    f_alive = passed.copy()
    wins = np.zeros(n)
    cycle = np.zeros(n)
    cash = np.zeros(n)
    n_pay = np.zeros(n)
    ever = np.zeros(n, dtype=bool)
    win_min = float(spec["win_min"])
    min_pay = float(spec["min_pay"])
    cap = float(spec["cap"])
    for _d in range(days):
        trading = f_alive & (n_pay < 5)
        if not trading.any():
            break
        room = f_bal - f_floor
        pnl = _coin(rng, n, win, loss, p)
        f_alive &= ~(trading & intraday & (loss > room + 1e-9))
        trading = f_alive & (n_pay < 5)
        f_bal, dead = _apply(f_bal, f_floor, np.where(trading, pnl, 0.0), trading)
        f_alive &= ~dead
        trading = f_alive & (n_pay < 5)
        day_pnl = np.where(trading, pnl, 0.0)
        wins = np.where(trading & (day_pnl >= win_min), wins + 1, wins)
        cycle = np.where(trading, cycle + day_pnl, cycle)
        f_floor, f_high, f_locked = _flex_trail(f_bal, f_floor, f_high, f_locked, trading, spec)
        half = 0.5 * np.maximum(cycle, 0.0)
        if payout == "max":
            amount = np.minimum(cap, half)
        else:
            amount = np.where(half >= min_pay, min_pay, 0.0)
        take = trading & (wins >= 5) & (cycle > 0) & (amount + 1e-9 >= min_pay)
        f_bal = np.where(take, f_bal - amount, f_bal)
        cash = np.where(take, cash + amount * 0.9, cash)
        n_pay = np.where(take, n_pay + 1, n_pay)
        ever |= take
        wins = np.where(take, 0.0, wins)
        cycle = np.where(take, 0.0, cycle)
        f_floor = np.where(take, float(spec["lock"]), f_floor)
        f_locked = f_locked | take
        f_alive &= ~(take & (f_bal <= f_floor + 1e-9))
        f_alive &= n_pay < 5
    fees = np.full(n, fee)
    net = cash - fees
    stat = summarise(net)
    passed_m = passed.astype(bool)
    finished = n_pay >= 5
    stat.update({
        "pass_rate": float(passed_m.mean()),
        "payout_rate": float(ever.mean()),
        "mean_payouts": float(n_pay.mean()),
        "mean_cash": float(cash.mean()),
        "mean_fees": float(fees.mean()),
        "median_net": float(np.median(net)),
        "median_cash": float(np.median(cash)),
        "fees_per_pass": float(fees.sum() / passed_m.sum()) if passed_m.any() else float("nan"),
    })
    stat.update(_funded_stats(cash, ever, n_pay, f_alive, passed_m, finished))
    return stat


def lucid_recipe_run(
    rng: np.random.Generator,
    n: int = 4000,
    size: int = 50_000,
    consistency: float = 0.40,
    p_eval: float = 0.60,
    p_big: float = 0.39,
    p_small: float = 0.95,
    small_fail: str = "retry",
    intraday: bool = False,
    fee: float = 100.0,
    max_eval_days: int = 15,
    samples: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    spec = FLEX[size]
    mll = float(spec["mll"])
    target = float(spec["target"])
    win_amt = target / 2.0
    big_win = 1.7 * mll
    small = float(spec["win_min"])

    def draw(risk: float, p: float, payoff: float, lose: float | None = None) -> np.ndarray:
        if samples is not None:
            return rng.choice(samples, size=n) * risk
        return _coin(rng, n, payoff, risk if lose is None else lose, p)

    balance = np.full(n, float(size))
    floor = np.full(n, float(size - mll))
    high = balance.copy()
    locked = np.zeros(n, dtype=bool)
    best = np.zeros(n)
    alive = np.ones(n, dtype=bool)
    passed = np.zeros(n, dtype=bool)
    eval_days = np.zeros(n)
    for d in range(max_eval_days):
        trading = alive & ~passed
        if not trading.any():
            break
        room = balance - floor
        pnl = draw(mll, p_eval, win_amt)
        die = trading & intraday & (mll > room + 1e-9)
        alive &= ~die
        trading = alive & ~passed
        balance, dead = _apply(balance, floor, np.where(trading, pnl, 0.0), trading)
        alive &= ~dead
        trading = alive & ~passed
        best = np.where(trading, np.maximum(best, np.where(trading, pnl, 0.0)), best)
        floor, high, locked = _flex_trail(balance, floor, high, locked, trading, spec)
        profit = balance - size
        need = np.maximum(target, np.where(best > 0, best / consistency, target))
        passed |= trading & (profit + 1e-6 >= need)
        eval_days = np.where(trading, d + 1, eval_days)
    f_bal = np.full(n, float(size))
    f_floor = np.full(n, float(size - mll))
    f_high = f_bal.copy()
    f_locked = np.zeros(n, dtype=bool)
    f_alive = passed.copy()
    cash = np.zeros(n)
    n_pay = np.zeros(n)
    ever = np.zeros(n, dtype=bool)
    for _cycle in range(5):
        trading = f_alive.copy()
        if not trading.any():
            break
        room = f_bal - f_floor
        pnl = draw(mll, p_big, big_win)
        die = trading & intraday & (mll > room + 1e-9)
        f_alive &= ~die
        trading = f_alive.copy()
        f_bal, dead = _apply(f_bal, f_floor, np.where(trading, pnl, 0.0), trading)
        f_alive &= ~dead
        trading = f_alive.copy()
        wins = (trading & (pnl >= spec["win_min"])).astype(float)
        cycle = np.where(trading, pnl, 0.0)
        f_floor, f_high, f_locked = _flex_trail(f_bal, f_floor, f_high, f_locked, trading, spec)
        small_wins = np.zeros(n)
        for _k in range(8):
            need = f_alive & (small_wins < 4)
            if not need.any():
                break
            if samples is None and small_fail == "bust":
                hit = rng.random(n) < p_small
                pnl = np.where(hit, small, -mll)
            elif samples is None:
                pnl = _coin(rng, n, small, small, p_small)
            else:
                pnl = draw(small, p_small, small)
            room = f_bal - f_floor
            die = need & intraday & (pnl < 0) & (np.abs(pnl) > room + 1e-9)
            f_alive &= ~die
            need = f_alive & (small_wins < 4)
            f_bal, dead = _apply(f_bal, f_floor, np.where(need, pnl, 0.0), need)
            f_alive &= ~dead
            need = f_alive & (small_wins < 4)
            good = need & (pnl >= spec["win_min"])
            small_wins = np.where(good, small_wins + 1, small_wins)
            wins = np.where(good, wins + 1, wins)
            cycle = np.where(need, cycle + pnl, cycle)
            f_floor, f_high, f_locked = _flex_trail(f_bal, f_floor, f_high, f_locked, need, spec)
            if small_fail == "bust":
                f_alive &= ~((pnl < spec["win_min"]) & need)
        trading = f_alive & (small_wins >= 4) & (wins >= 5) & (cycle > 0)
        amount = np.minimum(float(spec["cap"]), 0.5 * np.maximum(cycle, 0.0))
        take = trading & (amount + 1e-9 >= spec["min_pay"])
        f_bal = np.where(take, f_bal - amount, f_bal)
        cash = np.where(take, cash + amount * 0.9, cash)
        n_pay = np.where(take, n_pay + 1, n_pay)
        ever |= take
        f_floor = np.where(take, float(spec["lock"]), f_floor)
        f_locked = f_locked | take
        died = take & (f_bal <= f_floor + 1e-9)
        f_alive &= ~died
        f_alive &= take
        f_alive &= n_pay < 5
    fees = np.full(n, fee)
    return {
        "net": cash - fees,
        "cash": cash,
        "passed": passed,
        "ever": ever,
        "n_pay": n_pay,
        "eval_days": eval_days,
    }


def recipe_summary(raw: dict[str, np.ndarray], fee: float) -> dict[str, float]:
    net = raw["net"]
    stat = summarise(net)
    stat.update({
        "pass_rate": float(raw["passed"].mean()),
        "payout_rate": float(raw["ever"].mean()),
        "mean_payouts": float(raw["n_pay"].mean()),
        "mean_cash": float(raw["cash"].mean()),
        "fee": fee,
        "payouts_per_100_evals": float(raw["n_pay"].mean() * 100),
    })
    return stat


@dataclass
class BatchResult:
    month_cash: np.ndarray
    ruin: float
    mean_payouts: float
    payout_rate: float
    p_broke: float
    end_bank: np.ndarray


def household_batch(
    rng: np.random.Generator,
    n: int = 1000,
    fee: float = 100.0,
    bankroll: float = 2_000.0,
    days: int = 21,
    consistency: float = 0.50,
    p_eval: float = 0.60,
    p_big: float = 0.39,
    p_small: float = 0.95,
    intraday: bool = False,
) -> BatchResult:
    """One household for `days` trading days. Caps: 10 combined, 5 funded, 10 evals.

    Each slot runs the 50K recipe. A passed eval takes a funded slot when one
    is free. It does not trade on the day it passes: the funded account starts
    the next session. New evals start only while the bankroll covers the fee
    and a slot is free. No hedging: every account flips its own coin.
    `intraday` liquidates a funded trade whose planned loss exceeds the room.
    LucidFlex itself grades the max loss at the close, so the default is off.
    """
    spec = FLEX[50_000]
    month = np.zeros(n)
    payouts = np.zeros(n)
    # per household: up to 10 slots, encoded as arrays (n, 10)
    slots = 10
    phase = np.zeros((n, slots), dtype=np.int8)  # 0 empty, 1 eval, 2 funded
    bal = np.zeros((n, slots))
    floor = np.zeros((n, slots))
    high = np.zeros((n, slots))
    locked = np.zeros((n, slots), dtype=bool)
    best = np.zeros((n, slots))
    # funded progress
    wins = np.zeros((n, slots))
    cycle = np.zeros((n, slots))
    smalls = np.zeros((n, slots))
    pays = np.zeros((n, slots))
    stage = np.zeros((n, slots), dtype=np.int8)  # 0 need big, 1 need smalls
    cash_bank = np.full(n, bankroll)

    def start_eval(mask, j):
        phase[:, j] = np.where(mask, 1, phase[:, j])
        bal[:, j] = np.where(mask, 50_000.0, bal[:, j])
        floor[:, j] = np.where(mask, 48_000.0, floor[:, j])
        high[:, j] = np.where(mask, 50_000.0, high[:, j])
        locked[:, j] = np.where(mask, False, locked[:, j])
        best[:, j] = np.where(mask, 0.0, best[:, j])
        cash_bank[:] = np.where(mask, cash_bank - fee, cash_bank)
        month[:] = np.where(mask, month - fee, month)

    # open the first wave
    for j in range(slots):
        afford = cash_bank >= fee
        start_eval(afford, j)

    for _d in range(days):
        opened = np.zeros((n, slots), dtype=bool)
        # eval accounts
        for j in range(slots):
            on = phase[:, j] == 1
            if not on.any():
                continue
            win = rng.random(n) < p_eval
            pnl = np.where(win, 1_500.0, -2_000.0)
            bal[:, j] = np.where(on, bal[:, j] + pnl, bal[:, j])
            dead = on & (bal[:, j] <= floor[:, j] + 1e-9)
            phase[:, j] = np.where(dead, 0, phase[:, j])
            on = phase[:, j] == 1
            best[:, j] = np.where(on, np.maximum(best[:, j], pnl), best[:, j])
            high[:, j] = np.where(on, np.maximum(high[:, j], bal[:, j]), high[:, j])
            lock_now = on & ~locked[:, j] & (high[:, j] >= spec["trail"])
            floor[:, j] = np.where(lock_now, float(spec["lock"]), floor[:, j])
            locked[:, j] = locked[:, j] | lock_now
            trail = on & ~locked[:, j]
            floor[:, j] = np.where(trail, np.maximum(floor[:, j], high[:, j] - spec["mll"]), floor[:, j])
            profit = bal[:, j] - 50_000.0
            need = np.maximum(3_000.0, np.where(best[:, j] > 0, best[:, j] / consistency, 3_000.0))
            passed = on & (profit + 1e-6 >= need)
            # convert if a funded slot and a combined slot exist after this eval closes
            n_funded = (phase == 2).sum(axis=1)
            n_alive = ((phase == 1) | (phase == 2)).sum(axis=1)
            can = passed & (n_funded < 5) & (n_alive <= 10)
            # closing the eval frees a combined slot, so n_alive includes this eval.
            # converting keeps the combined count the same.
            phase[:, j] = np.where(can, 2, phase[:, j])
            phase[:, j] = np.where(passed & ~can, 0, phase[:, j])  # passed but no funded room: dropped
            opened[:, j] = opened[:, j] | can
            # reset funded state on conversion
            bal[:, j] = np.where(can, 50_000.0, bal[:, j])
            floor[:, j] = np.where(can, 48_000.0, floor[:, j])
            high[:, j] = np.where(can, 50_000.0, high[:, j])
            locked[:, j] = np.where(can, False, locked[:, j])
            wins[:, j] = np.where(can, 0.0, wins[:, j])
            cycle[:, j] = np.where(can, 0.0, cycle[:, j])
            smalls[:, j] = np.where(can, 0.0, smalls[:, j])
            pays[:, j] = np.where(can, 0.0, pays[:, j])
            stage[:, j] = np.where(can, 0, stage[:, j])
        # funded accounts. A conversion today waits until tomorrow.
        for j in range(slots):
            on = (phase[:, j] == 2) & ~opened[:, j]
            if not on.any():
                continue
            big = stage[:, j] == 0
            if big.any():
                win = rng.random(n) < p_big
                pnl = np.where(win, 3_400.0, -2_000.0)
                use = on & big
                room = bal[:, j] - floor[:, j]
                die_open = use & intraday & (float(spec["mll"]) > room + 1e-9)
                phase[:, j] = np.where(die_open, 0, phase[:, j])
                use = use & ~die_open
                bal[:, j] = np.where(use, bal[:, j] + pnl, bal[:, j])
                dead = use & (bal[:, j] <= floor[:, j] + 1e-9)
                phase[:, j] = np.where(dead, 0, phase[:, j])
                use_big = use & (phase[:, j] == 2)
                wins[:, j] = np.where(use_big & (pnl >= 150), wins[:, j] + 1, wins[:, j])
                cycle[:, j] = np.where(use_big, cycle[:, j] + pnl, cycle[:, j])
                high[:, j] = np.where(use_big, np.maximum(high[:, j], bal[:, j]), high[:, j])
                lock_now = use_big & ~locked[:, j] & (high[:, j] >= spec["trail"])
                floor[:, j] = np.where(lock_now, float(spec["lock"]), floor[:, j])
                locked[:, j] = locked[:, j] | lock_now
                trail = use_big & ~locked[:, j]
                floor[:, j] = np.where(trail, np.maximum(floor[:, j], high[:, j] - 2_000), floor[:, j])
                stage[:, j] = np.where(use_big, 1, stage[:, j])
                smalls[:, j] = np.where(use_big, 0.0, smalls[:, j])
            on = (phase[:, j] == 2) & ~opened[:, j]
            small = on & (stage[:, j] == 1) & ~big
            if small.any():
                win = rng.random(n) < p_small
                pnl = np.where(win, 150.0, -150.0)
                bal[:, j] = np.where(small, bal[:, j] + pnl, bal[:, j])
                dead = small & (bal[:, j] <= floor[:, j] + 1e-9)
                phase[:, j] = np.where(dead, 0, phase[:, j])
                small = (phase[:, j] == 2) & (stage[:, j] == 1)
                smalls[:, j] = np.where(small & win, smalls[:, j] + 1, smalls[:, j])
                wins[:, j] = np.where(small & win, wins[:, j] + 1, wins[:, j])
                cycle[:, j] = np.where(small, cycle[:, j] + pnl, cycle[:, j])
                ready = small & (smalls[:, j] >= 4) & (wins[:, j] >= 5) & (cycle[:, j] > 0)
                amount = np.minimum(2_000.0, 0.5 * np.maximum(cycle[:, j], 0.0))
                take = ready & (amount >= 500.0) & (pays[:, j] < 5)
                bal[:, j] = np.where(take, bal[:, j] - amount, bal[:, j])
                month_add = np.where(take, amount * 0.9, 0.0)
                month += month_add
                cash_bank[:] = cash_bank + month_add
                payouts += take.astype(float)
                pays[:, j] = np.where(take, pays[:, j] + 1, pays[:, j])
                floor[:, j] = np.where(take, float(spec["lock"]), floor[:, j])
                locked[:, j] = locked[:, j] | take
                dead = take & (bal[:, j] <= floor[:, j])
                phase[:, j] = np.where(dead | (take & (pays[:, j] >= 5)), 0, phase[:, j])
                still = (phase[:, j] == 2) & take
                stage[:, j] = np.where(still, 0, stage[:, j])
                wins[:, j] = np.where(still, 0.0, wins[:, j])
                cycle[:, j] = np.where(still, 0.0, cycle[:, j])
                smalls[:, j] = np.where(still, 0.0, smalls[:, j])
        # refill empty eval slots
        for j in range(slots):
            empty = phase[:, j] == 0
            n_funded = (phase == 2).sum(axis=1)
            n_alive = ((phase == 1) | (phase == 2)).sum(axis=1)
            afford = (cash_bank >= fee) & empty & (n_alive < 10) & (n_funded <= 5)
            # starting an eval: combined count increases by 1
            start_eval(afford, j)
    broke = cash_bank < fee
    return BatchResult(
        month,
        float(np.mean(month < 0)),
        float(payouts.mean()),
        float(np.mean(payouts > 0)),
        float(broke.mean()),
        cash_bank.copy(),
    )
