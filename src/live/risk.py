"""Risk guards — the Vault's safety rails (Phase 4 Stage 4).

Defense in depth: the engine already enforces the champion's own limits (entry window,
max 2 trades/day, the -2R damage halt, EOD flatten). This layer adds the ACCOUNT-level
backstops that must exist before anything runs unattended, and enforces them through the
same `day_gate` seam the engine already honors — a tripped guard means new trades are
never admitted by simulate() itself, not filtered after the fact:

  * KILL SWITCH — a file on disk (`output/live/KILL`). Present -> no new trades, every
    session, until a human deletes it. Works even if the bot is wedged: no code path is
    needed to honor it beyond the gate read, and `trip()`/`reset()` manage it for the
    Telegram /kill command later.
  * DAILY LOSS LIMIT — realized day P&L <= -limit (dollars) -> no new entries for the
    rest of that session. Open-position exits still run their normal rules (stops/
    targets/flatten); the guard stops NEW risk, it does not manage positions.
    Enforcement granularity is BETWEEN BARS: a trade's loss is booked when it
    completes, so a second admission inside the same one-minute bar cannot be stopped
    by this guard — the engine's own -2R damage halt (halt_r) covers the intra-bar
    case. This layer is the account-level dollar backstop on top of it.
  * MAX TRADES/DAY — hard backstop above the engine's own cap.
  * EQUITY FLOOR — cumulative realized P&L below the floor -> permanent stand-down
    (every session) until a human calls `reset_floor()`. The "walk away" brake.

Wiring (both hooks on the same Vault):
    guard = RiskGuard(limits)
    vault = Vault(..., day_gate=guard.wrap(strategy_gate_or_None))
    vault.add_sink(guard.on_trade)        # BEFORE the broker sink, so state is fresh

`wrap()` composes conservatively with any inner (strategy) gate: the guard can only
REMOVE risk on top of it, never add any. Halt transitions fire `on_halt` exactly once
per (date, reason) — the Telegram hook for Stage 5.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from src.live.vault import TradeEvent

KILL_FILE = Path("output/live/KILL")


def fanout(*fns: Callable[[str, str], None]) -> Callable[[str, str], None]:
    """Combine halt hooks (Telegram + journal + ...) into one on_halt callable.
    Each hook is isolated: one raising hook can never stop the others (Stage-6
    review F4)."""
    def call(date: str, reason: str) -> None:
        for fn in fns:
            try:
                fn(date, reason)
            except Exception as e:
                print(f"[risk] halt hook failed: {type(e).__name__}: {e}",
                      file=sys.stderr)
    return call


@dataclass(frozen=True)
class RiskLimits:
    """Account-level backstops that sit ABOVE the canon's own daily risk budget.

    REBUILT CANON (2026-07-29): entries are UNCAPPED — capacity is bounded by the scorer's
    daily budget (realized losses + in-flight risk + new risk <= budget), not by a trade
    count. Two consequences, both load-bearing:

      * `max_trades_per_day` now defaults to None (no count cap). The old default of 3 was a
        backstop above a 2/day engine cap that NO LONGER EXISTS; against a book that averages
        ~4 trades/day and legitimately runs into double digits, it would have announced a
        halt on most days and stood the account down mid-session. Leaving it at 3 is the
        single most dangerous stale default in this file.
      * `daily_loss_dollars` must be set ABOVE the canon budget, never below it. Below, this
        guard front-runs the budget and truncates the measured book; the shipped numbers
        assume the budget is what stops the day. Use `for_budget()` rather than a literal.
    """
    daily_loss_dollars: float = 1_200.0        # realized day P&L at/below -this -> day halt
    max_trades_per_day: int | None = None      # None = no count cap (uncapped canon)
    equity_floor_dollars: float | None = None  # cumulative P&L at/below this -> full stop
    kill_file: Path = KILL_FILE

    @classmethod
    def for_budget(cls, budget: float, *, headroom: float = 1.5, **kw) -> "RiskLimits":
        """Backstop derived from the canon's own daily budget, so it can only ever fire
        AFTER the budget has failed to hold. `headroom` is how far above the budget the
        account-level halt sits — 1.5x means the guard is silent in every day the scorer
        handles correctly, and catches the case where the scorer itself is wrong."""
        if budget <= 0:
            raise ValueError(f"budget must be positive, got {budget}")
        return cls(daily_loss_dollars=float(budget) * float(headroom), **kw)


@dataclass
class _DayState:
    dollars: float = 0.0
    trades: int = 0


class RiskGuard:
    def __init__(self, limits: RiskLimits = RiskLimits(),
                 on_halt: Callable[[str, str], None] | None = None):
        """on_halt(date, reason) fires once per (date, reason) transition — alert hook."""
        self.limits = limits
        self._days: dict[str, _DayState] = {}
        self._cum_dollars = 0.0
        self._floor_tripped = False
        self._announced: set[tuple[str, str]] = set()
        self._on_halt = on_halt

    # ---- restart recovery -----------------------------------------------------
    def seed(self, trades) -> None:
        """Rebuild guard state from persisted trades (PaperBroker.restore().trades)
        after a restart — WITHOUT re-announcing halts that already fired. Without this
        a crash-looping bot would forget its daily loss / equity floor and re-trade
        straight through them. Call before wiring the guard into a new Vault."""
        saved, self._on_halt = self._on_halt, None
        try:
            for ev in trades:
                self.on_trade(ev)
        finally:
            self._on_halt = saved

    # ---- accounting sink (add BEFORE the broker so gates see fresh state) ----
    def on_trade(self, ev: TradeEvent) -> None:
        st = self._days.setdefault(ev.trade_date, _DayState())
        st.dollars += ev.dollars
        st.trades += 1
        self._cum_dollars += ev.dollars
        fl = self.limits.equity_floor_dollars
        if fl is not None and self._cum_dollars <= fl:
            self._floor_tripped = True
        # evaluate now so halts are announced the moment they trip, not on next admission
        self.gate(ev.trade_date)

    # ---- the day_gate ---------------------------------------------------------
    def gate(self, date: str) -> dict | None:
        """day_gate signature: date -> engine gate dict or None (no restriction)."""
        reason = self._halt_reason(date)
        if reason is None:
            return None
        if (date, reason) not in self._announced:
            self._announced.add((date, reason))
            if self._on_halt is not None:
                try:                                   # gate() runs INSIDE the engine's
                    self._on_halt(date, reason)        # day_gate path — a raising alert
                except Exception as e:                 # hook must never kill the loop
                    print(f"[risk] on_halt failed: {type(e).__name__}: {e}",
                          file=sys.stderr)
        return {"stand_down": True, "allow_reversion": False,
                "allow_continuation": False, "size_multiplier": 0.0,
                "risk_reason": reason}

    def _halt_reason(self, date: str) -> str | None:
        if self.limits.kill_file.exists():
            return "kill_switch"
        if self._floor_tripped:
            return "equity_floor"
        st = self._days.get(date)
        if st is not None:
            if st.dollars <= -self.limits.daily_loss_dollars:
                return "daily_loss_limit"
            cap = self.limits.max_trades_per_day
            if cap is not None and st.trades >= cap:
                return "max_trades"
        return None

    def wrap(self, inner: Callable[[str], dict | None] | None = None,
             ) -> Callable[[str], dict | None]:
        """Compose: risk guard first (it can only REMOVE risk), else the strategy gate."""
        def gate(date: str) -> dict | None:
            g = self.gate(date)
            if g is not None:
                return g
            return inner(date) if inner is not None else None
        return gate

    # ---- controls (Telegram /status /kill later) ------------------------------
    def trip(self) -> None:
        """Arm the kill switch (idempotent)."""
        self.limits.kill_file.parent.mkdir(parents=True, exist_ok=True)
        self.limits.kill_file.write_text("armed\n")

    def reset(self) -> None:
        """Disarm the kill switch (a deliberate human act)."""
        self.limits.kill_file.unlink(missing_ok=True)

    def reset_floor(self) -> None:
        """Clear an equity-floor stop (a deliberate human act)."""
        self._floor_tripped = False

    def status(self) -> dict:
        return {"killed": self.limits.kill_file.exists(),
                "floor_tripped": self._floor_tripped,
                "cum_dollars": round(self._cum_dollars, 2),
                "days": {d: {"dollars": round(s.dollars, 2), "trades": s.trades}
                         for d, s in sorted(self._days.items())}}
