"""One account path under a loaded rule set.

The path accepts or rejects a fill. It never sends an order. Max-loss is
checked on the fill (the firm's real-time equity rule, with each fill treated
as immediately realized). The trailing line moves on the schedule the firm
published: end of day, or intraday when that is the rule.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.research.news import in_news_blackout
from src.research.prop.rules import AccountRules, session_open


@dataclass
class ApplyResult:
    action: str
    reason: str


@dataclass
class PropAccount:
    rules: AccountRules
    balance: float = field(init=False)
    floor: float = field(init=False)
    peak: float = field(init=False)
    high_close: float = field(init=False)
    locked: bool = False
    failed: bool = False
    fail_reason: str | None = None
    passed: bool = False
    blocked: bool = False
    day_pnl: float = 0.0
    had_fill: bool = False
    best_day: float = 0.0
    cycle_profit: float = 0.0
    cycle_best: float = 0.0
    winning_days: int = 0
    traded_days: int = 0
    days: int = 0
    payout_count: int = 0
    trader_cash: float = 0.0
    gross_payouts: float = 0.0
    news_events: Any = None

    def __post_init__(self) -> None:
        self.balance = float(self.rules.start_balance)
        self.peak = self.balance
        self.high_close = self.balance
        self.floor = self.balance - float(self.rules.mll_amount)
        if self.rules.mll_mode == "eod_trail_lock_at_zero":
            self.floor = -float(self.rules.mll_amount)
            self.peak = 0.0
            self.high_close = 0.0

    def apply(
        self,
        pnl: float,
        ts=None,
        minis: int = 0,
        micros: int = 1,
    ) -> ApplyResult:
        if self.failed:
            return ApplyResult("rejected", "failed")
        if self.passed and self.rules.stage != "funded":
            return ApplyResult("rejected", "passed")
        if self.blocked:
            return ApplyResult("rejected", "dll")
        if ts is not None and not session_open(ts, self.rules):
            return ApplyResult("rejected", "hours")
        if (
            ts is not None
            and self.rules.news_blackout
            and self.news_events is not None
            and in_news_blackout(ts, self.news_events, self.rules.news_blackout_minutes)
        ):
            return ApplyResult("rejected", "news")
        equivalent = minis + micros / 10.0
        if equivalent > self.rules.max_minis + 1e-9:
            return ApplyResult("rejected", "contracts")

        new_balance = self.balance + float(pnl)
        if self.rules.mll_mode == "intraday_trail" and not self.locked:
            self.peak = max(self.peak, new_balance)
            self.floor = max(self.floor, self.peak - self.rules.mll_amount)
            if self.rules.lock_floor is not None:
                self.floor = min(self.floor, self.rules.lock_floor)

        self.balance = new_balance
        self.day_pnl += float(pnl)
        self.had_fill = True
        if self.balance <= self.floor + 1e-9:
            self.failed = True
            self.fail_reason = "mll"
            return ApplyResult("bust", "mll")
        if self.rules.dll is not None and self.day_pnl <= -self.rules.dll + 1e-9:
            self.blocked = True
            if self.rules.dll_is_breach:
                self.failed = True
                self.fail_reason = "dll"
                return ApplyResult("bust", "dll")
            return ApplyResult("dll", "dll")
        return ApplyResult("accepted", "ok")

    def end_day(self) -> None:
        if self.had_fill:
            self.traded_days += 1
            payout = self.rules.payout or {}
            minimum = payout.get("winning_day_min")
            if self.rules.payout is not None and (
                minimum is None or self.day_pnl + 1e-9 >= float(minimum)
            ):
                self.winning_days += 1
        self.best_day = max(self.best_day, self.day_pnl)
        self.cycle_best = max(self.cycle_best, self.day_pnl)
        self.cycle_profit += self.day_pnl
        self.days += 1
        if not self.failed:
            self._trail()
            self._check_pass()
            self._try_payout()
        self.day_pnl = 0.0
        self.had_fill = False
        self.blocked = False

    def _trail(self) -> None:
        mode = self.rules.mll_mode
        if mode == "intraday_trail" or self.locked:
            self.high_close = max(self.high_close, self.balance)
            return
        self.high_close = max(self.high_close, self.balance)
        if mode == "eod_trail_lock_at_buffer":
            trigger = self.rules.trail_trigger
            if trigger is not None and self.high_close + 1e-9 >= trigger:
                self.floor = float(self.rules.lock_floor)
                self.locked = True
                return
            self.floor = max(self.floor, self.high_close - self.rules.mll_amount)
            return
        if mode == "eod_trail_lock_at_start":
            proposed = self.high_close - self.rules.mll_amount
            cap = float(self.rules.lock_floor)
            self.floor = min(cap, max(self.floor, proposed))
            if self.floor >= cap - 1e-9:
                self.locked = True
            return
        if mode == "eod_trail_lock_at_zero":
            proposed = self.high_close - self.rules.mll_amount
            self.floor = min(0.0, max(self.floor, proposed))
            if self.floor >= -1e-9:
                self.floor = 0.0
                self.locked = True
            return
        raise ValueError(f"unknown mll_mode {mode}")

    def _check_pass(self) -> None:
        target = self.rules.profit_target
        if self.rules.stage == "funded" or target is None:
            return
        profit = self.balance - self.rules.start_balance
        need = float(target)
        if self.rules.consistency:
            need = max(need, self.best_day / float(self.rules.consistency))
        if profit + 1e-6 >= need:
            self.passed = True

    def _try_payout(self) -> None:
        payout = self.rules.payout
        if not payout or self.failed or self.passed and self.rules.stage != "funded":
            return
        limit = payout.get("max_payouts")
        if limit is not None and self.payout_count >= int(limit):
            return
        if payout.get("winning_days") is not None and self.winning_days < int(payout["winning_days"]):
            return
        goal = payout.get("min_cycle_profit")
        later = payout.get("min_cycle_profit_later")
        if self.payout_count >= 1 and later is not None:
            goal = later
        exempt = bool(payout.get("first_cycle_exempt")) and self.payout_count == 0
        if goal is not None and not exempt and self.cycle_profit + 1e-9 < float(goal):
            return
        ratio = payout.get("consistency")
        if ratio is not None:
            if self.cycle_profit <= 1e-9:
                return
            if self.cycle_best / self.cycle_profit > float(ratio) + 1e-9:
                return
        base = self.balance if payout.get("fraction_of") == "balance" else self.cycle_profit
        cap = _cap_for(payout, self.payout_count)
        amount = min(float(cap), float(payout["fraction"]) * max(float(base), 0.0))
        amount = round(amount + 1e-9, 2)
        if amount + 1e-9 < float(payout["min_request"]):
            return
        buffer = payout.get("buffer_floor")
        if buffer is not None and self.balance - amount < float(buffer) - 1e-9:
            return
        self.balance = round(self.balance - amount, 2)
        self.gross_payouts = round(self.gross_payouts + amount, 2)
        self.trader_cash = round(self.trader_cash + amount * float(payout["split"]), 2)
        self.payout_count += 1
        self.cycle_profit = 0.0
        self.cycle_best = 0.0
        self.winning_days = 0
        if payout.get("mll_resets_to_zero_on_first_payout"):
            self.floor = 0.0
            self.locked = True
        if payout.get("mll_resets_to_lock_on_payout") and self.rules.lock_floor is not None:
            self.floor = float(self.rules.lock_floor)
            self.locked = True
        if self.balance <= self.floor + 1e-9:
            self.failed = True
            self.fail_reason = "mll_after_payout"

    def required_profit(self) -> float | None:
        target = self.rules.profit_target
        if target is None:
            return None
        need = float(target)
        if self.rules.consistency:
            need = max(need, self.best_day / float(self.rules.consistency))
        return need


def _cap_for(payout: dict[str, Any], already: int) -> float:
    switch = payout.get("cap_switch_after")
    if switch is not None and already >= int(switch) and payout.get("cap_later_cycles") is not None:
        return float(payout["cap_later_cycles"])
    if payout.get("cap_first_cycles") is not None and (switch is None or already < int(switch)):
        return float(payout["cap_first_cycles"])
    if payout.get("cap_first_cycles") is not None and switch is None:
        return float(payout["cap_first_cycles"])
    return float(payout["cap"])
