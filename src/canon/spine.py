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
from pathlib import Path
from typing import Protocol

from src.canon.gate_evidence import MICRO_CLAMP, base_dollar


# --------------------------------------------------------------------------- config/state
@dataclass(frozen=True)
class SpineConfig:
    dd_halt_buffer: float = 250.0          # halt when equity within this of the trailing floor
    # Day P&L halt as an R MULTIPLE of the day's own base_dollar, never a fixed dollar figure
    # (PROMOTION-GATE §D2 blocker 1). The sizer is drawdown-scaled: base_dollar is $200 at the
    # eval floor and steps +$75 per $1k of available DD past $3k, so a constant -$800 tightens
    # as the account grows — at $6k available DD it is tighter than ONE max-conviction trade,
    # priced by the payout-cycle MC at -$6,000/account/year for zero bust reduction. As an R
    # multiple the halt tracks the risk unit instead: -4R = -$800 at the floor, -$1,700 at $6k.
    # The VALUE (-4R) awaits Angus's sign-off; the UNITS are not a preference.
    daily_loss_halt_r: float = -4.0
    # Hard size clamp, in MICROS — the unit `OrderIntent.size` actually carries (canon_lane.py
    # and route_b.py both build it via `int(micros)`). Imported from the sizing schedule rather
    # than restated, because the previous local literal `2` (commented "minis") silently
    # clamped every live order to 2 micros — gate B5 fails on trade one (§D2 blocker 2).
    max_contracts: int = MICRO_CLAMP
    max_spread_rel: float = 2.5            # spread ceiling as a multiple of the trailing baseline
    feed_stale_ms: int = 3000              # no order if last tick older than this
    max_orders_per_min: int = 10           # order-rate cap


def daily_loss_halt_dollars(cfg: SpineConfig, acct: "AccountState") -> float:
    """The day's loss-halt threshold in DOLLARS: the configured R multiple times the day's own
    base_dollar, where available drawdown = equity - trailing_floor. Recomputed per check, so
    the halt re-indexes as the account's available DD moves."""
    return cfg.daily_loss_halt_r * base_dollar(acct.equity - acct.trailing_floor)


# ------------------------------------------------------------------- Tier-1 pin (§D2 blocker 3)
# The signed-off Tier-1 values. These are duplicated ON PURPOSE: config/live.yaml carries the
# operator-visible copy, this carries the reviewed copy, and `assert_tier1_pinned` refuses to
# start when they disagree. A single source would let one silent edit change live risk; two
# sources plus a boot assertion make any change a deliberate, reviewable act — which is what
# PROMOTION-GATE §E ("any code change to canon, sizer, spine, or relay -> stop and review")
# requires. Changing a limit means editing both and re-running the gate, never one file.
TIER1_PINNED: dict[str, float | int] = {
    "dd_halt_buffer": 250.0,
    "daily_loss_halt_r": -4.0,
    "max_contracts": MICRO_CLAMP,
    "max_spread_rel": 2.5,
    "feed_stale_ms": 3000,
    "max_orders_per_min": 10,
}


class SpinePinError(RuntimeError):
    """Raised at boot when the live spine config does not match the signed-off Tier-1 set."""


def spine_config_from_mapping(m: dict | None) -> SpineConfig:
    """Build a SpineConfig from a config mapping (the `spine:` block of config/live.yaml).
    Unknown keys are an ERROR, not a warning — a typo'd limit that silently falls back to a
    default is exactly the failure this exists to stop."""
    m = dict(m or {})
    known = set(TIER1_PINNED)
    unknown = sorted(set(m) - known)
    if unknown:
        raise SpinePinError(f"unknown spine config key(s): {unknown}; expected {sorted(known)}")
    return SpineConfig(**m)


def assert_tier1_pinned(cfg: SpineConfig, *, pinned: dict | None = None) -> None:
    """Boot assertion: every Tier-1 constant must equal its signed-off value. Fails CLOSED —
    a mismatch raises rather than warning, so a drifted limit cannot reach a live order."""
    exp = dict(TIER1_PINNED if pinned is None else pinned)
    drift = {k: (getattr(cfg, k), v) for k, v in exp.items() if getattr(cfg, k) != v}
    if drift:
        detail = ", ".join(f"{k}: config={got!r} pinned={want!r}" for k, (got, want) in drift.items())
        raise SpinePinError(f"Tier-1 spine constants drifted from the signed-off set — {detail}")


def load_spine_config(path: str | Path = "config/live.yaml", *,
                      assert_pinned: bool = True) -> SpineConfig:
    """Load the Tier-1 spine constants from the live config and (by default) assert they match
    the signed-off set. An ABSENT `spine:` block is an error, not a silent fall-back to the
    dataclass defaults — 'the limits ride on defaults' is the defect being fixed."""
    import yaml
    raw = yaml.safe_load(Path(path).read_text()) or {}
    if "spine" not in raw:
        raise SpinePinError(f"{path} has no `spine:` block — Tier-1 limits must be explicit")
    cfg = spine_config_from_mapping(raw["spine"])
    if assert_pinned:
        assert_tier1_pinned(cfg)
    return cfg


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
    ref: str | None = None                 # broker order ref, ONLY on an armed placement

    @property
    def allowed(self) -> bool:
        return self.action == "place"


class Broker(Protocol):
    """Minimal broker surface the executor drives. A real DTC client and the test
    MockBroker both implement it. The executor NEVER assumes success — it reads back.

    The B7/B8 additions (cancel_order / modify_stop / close_partial) are RISK-REDUCING
    ONLY: cancel pulls a working entry (the cancel-if-runs rule), modify_stop moves the
    resting protective stop in place (BE move / V8 trail — never cancel+resubmit, that
    gap would leave the position unprotected), close_partial reduces an open position
    (V8 partial, 3-min cut, EOD flatten). None of them can open or increase risk."""
    def submit_bracket(self, intent: OrderIntent) -> str: ...
    def order_status(self, ref: str) -> dict: ...        # {entry, stop, size, side, account, stop_resting}
    def position(self, account: str) -> int: ...
    def flatten(self, account: str) -> None: ...
    def cancel_all(self, account: str) -> None: ...
    def cancel_order(self, ref: str) -> None: ...        # B7: pull ONE working order (+ its children)
    def modify_stop(self, ref: str, price: float) -> None: ...   # B8: move the resting stop in place
    def close_partial(self, account: str, qty: int, *,
                      price: float | None = None) -> str: ...    # B8: reduce; market iff price None


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
            ("daily_loss", acct.day_pnl <= daily_loss_halt_dollars(c, acct),
             f"day P&L {acct.day_pnl} <= {daily_loss_halt_dollars(c, acct)} "
             f"({c.daily_loss_halt_r}R)"),
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
            # Tier 1 (2): daily-loss halt — threshold re-indexed to the day's own risk unit
            halt_at = daily_loss_halt_dollars(self.cfg, acct)
            if acct.day_pnl <= halt_at:
                return SpineDecision("halt", "daily_loss",
                                     f"day P&L {acct.day_pnl} <= {halt_at} "
                                     f"({self.cfg.daily_loss_halt_r}R)")

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
        return SpineDecision("place", d.rule, f"ref={ref}", clamped_size=d.clamped_size,
                             ref=ref)

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
