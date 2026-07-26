"""The Safety Spine executor (docs/SAFETY-SPINE.md) — deterministic, order-time.

This is the hard guardrail layer between the canon's `size` decision and the DTC order.
It NEVER opens or increases risk; every rule is a HALT, a CLAMP, or a REJECT, and on any
doubt it does nothing or flattens (the one invariant). No LLM, no discretion, no in-the-
moment tuning — every threshold is a frozen constant on SpineConfig.

Implements the deterministic order-time rules of SAFETY-SPINE.md:
  Tier 1  (1) trailing-drawdown proximity halt  (2) daily-loss halt  (3) contract clamp
  Tier 2  (5) feed-health/staleness  (6) spread guard  (7) order-rate/duplicate
          (8) limit-not-market
  Tier 3  (9) fail-closed on any error/NaN/ambiguity   (12) spine-event journaling

Seams (infrastructural, wired elsewhere — this module exposes the hooks):
  (4) startup parity gate — the ingestor asserts it on boot; `parity_ok=False` keeps the
      executor read-only. (10) heartbeat/watchdog and (11) manual kill switch — a tripped
      kill (output/live/KILL, the champion's file) or lost heartbeat calls `flatten()`.

YES-ONLY + ARMED GATE: the executor only ever emits a fully-formed LIMIT bracket that
passed every rule; it can only reject / clamp / halt / flatten. It is DISARMED by default
and will not send a single order to the broker until `arm(token)` is called with the
sign-off token — Angus's written yes on the GAP/spine doc (Pat ruling 2026-07-24: build
now, arm later). Disarmed, it evaluates and journals every decision (shadow mode).

BROKER READ-BACK (Pat-approved primitive; NOT yet a numbered rule in SAFETY-SPINE.md —
flagged for doc update): after a submit, the placed order + resulting position are read
back from the broker and verified against intent; any mismatch → flatten + halt. The
submit ack is never trusted alone.
"""
from __future__ import annotations

import math
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol


# --------------------------------------------------------------------------- config/state
@dataclass(frozen=True)
class SpineConfig:
    dd_halt_buffer: float = 250.0          # halt when equity within this of the trailing floor
    daily_loss_halt: float = -800.0        # account-wide day P&L halt (<=)
    max_contracts: int = 2                 # hard clamp (Lucid 50k tier; minis)
    max_spread_rel: float = 2.5            # spread ceiling as a multiple of the trailing baseline
    feed_stale_ms: int = 3000              # no order if last tick older than this
    max_orders_per_min: int = 10           # order-rate cap


@dataclass(frozen=True)
class AccountState:
    equity: float
    trailing_floor: float
    day_pnl: float
    open_positions: int


@dataclass(frozen=True)
class FeedHealth:
    last_tick_age_ms: float
    crossed_or_locked: bool
    context_complete: bool                 # required session context present (e.g. overnight)
    spread_rel: float                      # observed spread / trailing baseline


@dataclass(frozen=True)
class OrderIntent:
    side: str                              # "B" | "S"
    order_type: str                        # must be "limit"
    entry_ref: float
    stop: float
    target: float | None                   # no fixed target in the canon (managed exit); may be None
    size: int
    setup_id: str                          # unique per candidate — duplicate guard key
    account: str


@dataclass
class SpineDecision:
    action: str                            # "place" | "reject" | "halt" | "flatten"
    rule: str                              # which rule fired ("ok" when placing)
    detail: str = ""
    clamped_size: int | None = None        # set when a clamp changed the size

    @property
    def allowed(self) -> bool:
        return self.action == "place"


class Broker(Protocol):
    """Minimal broker surface the executor drives. A real DTC client and the test
    MockBroker both implement it. The executor NEVER assumes success — it reads back."""
    def submit_bracket(self, intent: OrderIntent) -> str: ...
    def order_status(self, ref: str) -> dict: ...        # {entry, stop, size, side, account, stop_resting}
    def position(self, account: str) -> int: ...
    def flatten(self, account: str) -> None: ...
    def cancel_all(self, account: str) -> None: ...


# --------------------------------------------------------------------------- the executor
class SpineExecutor:
    def __init__(self, cfg: SpineConfig, broker: Broker,
                 kill_file_present: Callable[[], bool] = lambda: False,
                 journal: Callable[[dict], None] | None = None,
                 arm_token: str = "ANGUS-SIGNOFF") -> None:
        self.cfg = cfg
        self.broker = broker
        self._kill_present = kill_file_present
        self._journal = journal
        self._arm_token = arm_token
        self._armed = False
        self._halted = False
        self._order_times: deque[float] = deque()      # epoch-seconds of recent submits
        self._seen_setups: set[str] = set()
        self._resting: dict[str, str] = {}             # account -> last placed order ref
                                                       # (naked-position reconcile, rule 8b)

    # ---- arming (deliberate; represents Angus's written yes) ----------------
    def arm(self, token: str) -> bool:
        """Arm live order submission. Refuses unless the exact sign-off token is given."""
        self._armed = token == self._arm_token
        self._emit({"event": "arm", "armed": self._armed})
        return self._armed

    def disarm(self) -> None:
        self._armed = False
        self._emit({"event": "disarm"})

    @property
    def armed(self) -> bool:
        return self._armed and not self._halted

    # ---- the halt / flatten path (Tier 3 + manual kill) --------------------
    def flatten_and_halt(self, account: str, rule: str, detail: str = "") -> SpineDecision:
        self._halted = True
        self._resting.pop(account, None)               # position is being flattened
        try:
            self.broker.cancel_all(account)
            self.broker.flatten(account)
        finally:
            self._emit({"event": "flatten_halt", "rule": rule, "detail": detail,
                        "account": account})
        return SpineDecision("flatten", rule, detail)

    # ---- naked-position reconcile (SAFETY-SPINE 8b: reconcile on a TIMER, any duration) ---
    def reconcile(self, account: str, now: float) -> SpineDecision | None:
        """Timer-driven position-vs-bracket check — the periodic twin of the submit-time
        read-back. An open position whose bracket legs are NOT resting is NAKED (an unbounded
        loss): flatten + halt immediately, at any duration. Returns the flatten decision when
        naked, else None. Call on a timer from the run loop; fail-closed on any broker error."""
        try:
            pos = self.broker.position(account)
            if pos == 0:
                self._resting.pop(account, None)       # flat: nothing to protect
                return None
            ref = self._resting.get(account)
            naked = ref is None
            if not naked:
                st = self.broker.order_status(ref)
                naked = not st.get("stop_resting", False)     # protective stop must still rest
            if naked:
                self._emit({"event": "naked_position", "account": account, "position": pos,
                            "ref": ref})
                detail = (f"open position {pos} on {account} with no resting protective stop "
                          f"(ref={ref})")
                return self.flatten_and_halt(account, "naked_position", detail)
            return None
        except Exception as e:  # noqa: BLE001 — a failed reconcile fails closed (rule 9)
            return self.flatten_and_halt(account, "fail_closed", f"reconcile: {type(e).__name__}: {e}")

    # ---- all-guards evidence (PROMOTION-GATE: per-guard fired/not-fired, not just the trip) ---
    def guard_report(self, intent: OrderIntent, acct: AccountState, feed: FeedHealth,
                     now: float, parity_ok: bool = True) -> dict:
        """Evaluate EVERY guard independently (read-only — no rate/dup state mutation) and
        return each one's fired/not-fired outcome, plus the terminal decision `check()` would
        reach. `check()` short-circuits on the first failure, so the journal alone can't show
        that guards 2..N were evaluated; this is the evidence the promotion gate's per-guard
        table needs. Kept adjacent to `check()` so the two stay in lockstep."""
        c = self.cfg
        bad = self._malformed(intent)
        recent_orders = sum(1 for t in self._order_times if now - t <= 60.0)
        guards = [
            ("halted", self._halted, "spine already halted"),
            ("manual_kill", self._kill_present(), "KILL file present"),
            ("startup_parity", not parity_ok, "parity gate not green"),
            ("fail_closed", bool(bad), bad),
            ("limit_only", intent.order_type != "limit", f"order_type={intent.order_type!r}"),
            ("dd_proximity", acct.equity - acct.trailing_floor <= c.dd_halt_buffer,
             f"equity {acct.equity} within {c.dd_halt_buffer} of floor {acct.trailing_floor}"),
            ("daily_loss", acct.day_pnl <= c.daily_loss_halt,
             f"day P&L {acct.day_pnl} <= {c.daily_loss_halt}"),
            ("feed_stale", feed.last_tick_age_ms > c.feed_stale_ms,
             f"tick age {feed.last_tick_age_ms}ms > {c.feed_stale_ms}ms"),
            ("book_crossed", feed.crossed_or_locked, "book crossed/locked"),
            ("context_incomplete", not feed.context_complete, "required context missing"),
            ("spread", feed.spread_rel > c.max_spread_rel,
             f"spread_rel {feed.spread_rel} > {c.max_spread_rel}"),
            ("duplicate", intent.setup_id in self._seen_setups,
             f"setup {intent.setup_id} already sent"),
            ("order_rate", recent_orders >= c.max_orders_per_min,
             f"{recent_orders} orders in the last 60s >= {c.max_orders_per_min}"),
            ("contract_clamp", intent.size > c.max_contracts,
             f"size {intent.size} -> {c.max_contracts}"),
        ]
        report = [{"rule": name, "fired": bool(fired), "detail": (detail if fired else "")}
                  for name, fired, detail in guards]
        # terminal decision mirrors check(): first firing HALT/REJECT rule; clamp is not fatal.
        fatal = next((g for g in report if g["fired"] and g["rule"] != "contract_clamp"), None)
        decision = fatal["rule"] if fatal else "ok"
        return {"decision": decision, "setup": intent.setup_id, "guards": report,
                "n_fired": sum(1 for g in report if g["fired"])}

    # ---- the deterministic order-time check (pure; no side effects) --------
    def check(self, intent: OrderIntent, acct: AccountState, feed: FeedHealth,
              now: float, parity_ok: bool = True) -> SpineDecision:
        """Evaluate every deterministic rule. Returns the FIRST failing rule as a
        reject/halt, a clamp if only the size was out of bounds, else 'place'. Never
        raises — an internal error is itself a fail-closed HALT (rule 9)."""
        try:
            if self._halted:
                return SpineDecision("halt", "halted", "spine already halted")
            if self._kill_present():
                return SpineDecision("halt", "manual_kill", "KILL file present")   # rule 11
            if not parity_ok:
                return SpineDecision("halt", "startup_parity", "parity gate not green")  # rule 4

            # rule 9: fail-closed on NaN / malformed intent (also enforces yes-only shape)
            bad = self._malformed(intent)
            if bad:
                return SpineDecision("halt", "fail_closed", bad)

            # rule 8: limit-not-market
            if intent.order_type != "limit":
                return SpineDecision("reject", "limit_only",
                                     f"order_type={intent.order_type!r}, only 'limit' allowed")

            # Tier 1 (1): trailing-drawdown proximity halt
            if acct.equity - acct.trailing_floor <= self.cfg.dd_halt_buffer:
                return SpineDecision("halt", "dd_proximity",
                                     f"equity {acct.equity} within {self.cfg.dd_halt_buffer} "
                                     f"of floor {acct.trailing_floor}")
            # Tier 1 (2): daily-loss halt
            if acct.day_pnl <= self.cfg.daily_loss_halt:
                return SpineDecision("halt", "daily_loss",
                                     f"day P&L {acct.day_pnl} <= {self.cfg.daily_loss_halt}")

            # Tier 2 (5): feed health / staleness
            if feed.last_tick_age_ms > self.cfg.feed_stale_ms:
                return SpineDecision("reject", "feed_stale",
                                     f"tick age {feed.last_tick_age_ms}ms")
            if feed.crossed_or_locked:
                return SpineDecision("reject", "book_crossed", "book crossed/locked")
            if not feed.context_complete:
                return SpineDecision("reject", "context_incomplete", "required context missing")

            # Tier 2 (6): relative spread guard
            if feed.spread_rel > self.cfg.max_spread_rel:
                return SpineDecision("reject", "spread",
                                     f"spread_rel {feed.spread_rel} > {self.cfg.max_spread_rel}")

            # Tier 2 (7): order-rate + duplicate
            if intent.setup_id in self._seen_setups:
                return SpineDecision("reject", "duplicate", f"setup {intent.setup_id} already sent")
            self._trim_rate(now)
            if len(self._order_times) >= self.cfg.max_orders_per_min:
                return SpineDecision("reject", "order_rate",
                                     f"{len(self._order_times)} orders in the last 60s")

            # Tier 1 (3): contract clamp — never a reject, always shrink to the limit
            if intent.size > self.cfg.max_contracts:
                return SpineDecision("place", "contract_clamp",
                                     f"size {intent.size} -> {self.cfg.max_contracts}",
                                     clamped_size=self.cfg.max_contracts)
            return SpineDecision("place", "ok")
        except Exception as e:  # noqa: BLE001 — ANY error in the guard fails closed (rule 9)
            return SpineDecision("halt", "fail_closed", f"{type(e).__name__}: {e}")

    # ---- place: check -> (armed) submit -> READ-BACK verify ---------------
    def place(self, intent: OrderIntent, acct: AccountState, feed: FeedHealth,
              now: float, parity_ok: bool = True) -> SpineDecision:
        d = self.check(intent, acct, feed, now, parity_ok)
        self._emit({"event": "decision", "action": d.action, "rule": d.rule,
                    "detail": d.detail, "setup": intent.setup_id,
                    "clamped_size": d.clamped_size})
        if d.action in ("halt", "flatten"):
            return self.flatten_and_halt(intent.account, d.rule, d.detail)
        if d.action == "reject":
            return d
        # d.action == "place"
        size = d.clamped_size if d.clamped_size is not None else intent.size
        placed = OrderIntent(**{**intent.__dict__, "size": size})
        if not self.armed:
            self._emit({"event": "shadow_place", "setup": intent.setup_id, "size": size})
            return SpineDecision("place", "shadow", "disarmed — not sent to broker",
                                 clamped_size=d.clamped_size)
        # armed: submit, then read back and verify against intent
        self._order_times.append(now)
        self._seen_setups.add(intent.setup_id)
        ref = self.broker.submit_bracket(placed)
        mismatch = self._verify_readback(placed, ref)
        if mismatch:
            return self.flatten_and_halt(intent.account, "readback_mismatch", mismatch)
        self._resting[intent.account] = ref            # track for the naked-position reconcile
        self._emit({"event": "placed", "setup": intent.setup_id, "ref": ref, "size": size})
        return SpineDecision("place", d.rule, f"ref={ref}", clamped_size=d.clamped_size)

    # ---- internals ---------------------------------------------------------
    def _verify_readback(self, intent: OrderIntent, ref: str) -> str:
        """Read the order + position back from the broker and confirm they match intent.
        Returns '' on match, or a mismatch description (which triggers flatten+halt).

        THE INVARIANT (Angus B4): the RESTING PROTECTIVE STOP must exist at the broker. The
        canon has no fixed target (managed exit), so the target is NOT verified here — but the
        stop is checked to actually rest, not merely that the submit call returned. A silent
        Stop-field drop (the naked-entry bug) is exactly what this catches now."""
        st = self.broker.order_status(ref)
        for field_name, want in (("side", intent.side), ("size", intent.size),
                                 ("account", intent.account)):
            if st.get(field_name) != want:
                return f"{field_name}: broker {st.get(field_name)!r} != intent {want!r}"
        for field_name, want in (("entry", intent.entry_ref), ("stop", intent.stop)):
            got = st.get(field_name)
            if got is None or not math.isclose(float(got), want, rel_tol=1e-9, abs_tol=1e-9):
                return f"{field_name}: broker {got!r} != intent {want!r}"
        # the protective stop must be RESTING at the broker (a child order, read back), else NAKED.
        if not st.get("stop_resting", False):
            return "protective stop not resting at broker after submit — NAKED ENTRY"
        pos = self.broker.position(intent.account)
        if abs(pos) > intent.size:
            return f"position {pos} exceeds intended size {intent.size}"
        return ""

    @staticmethod
    def _malformed(i: OrderIntent) -> str:
        # entry_ref + stop are load-bearing (stop is the invariant); target is optional (the
        # canon has no fixed target — managed exit), but if present it must be finite.
        for name in ("entry_ref", "stop"):
            v = getattr(i, name)
            if v is None or (isinstance(v, float) and math.isnan(v)):
                return f"{name} is NaN/None"
        if i.target is not None and isinstance(i.target, float) and math.isnan(i.target):
            return "target is NaN"
        if i.size is None or i.size <= 0:
            return f"size {i.size} not positive"
        if i.side not in ("B", "S"):
            return f"side {i.side!r} invalid"
        if not i.setup_id:
            return "empty setup_id"
        return ""

    def _trim_rate(self, now: float) -> None:
        while self._order_times and now - self._order_times[0] > 60.0:
            self._order_times.popleft()

    def _emit(self, rec: dict) -> None:
        if self._journal is not None:
            self._journal(rec)
