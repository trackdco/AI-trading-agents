#!/usr/bin/env python3
"""ESCALATION GATE — orchestrator-side enforcement of the 0.3.5 escalation rule.

The tv-trigger contract *asks* the agent to escalate `thesis_stale` instead of
passing on a thesis-derived gate, and *asks* it not to escalate on a mechanical
gate. Prompt text is not enforcement: a model that ignores the instruction, or
reads its own gate as thesis-derived when it is not, would drive an unbounded
number of Tier-1 re-fires. This module is the orchestrator's answer. Every
`thesis_stale: true` verdict passes through `EscalationGate.request()`, and only
a GRANTED request causes a Tier-1 re-fire.

THE THREE SAFEGUARDS (his instruction, 2026-08-12):

  1. PER-WINDOW BUDGET — at most `budget` escalations per window (default 2).
     Past that, a request is refused and the verdict is downgraded to a pass.
     Without this, a thesis the tape has genuinely outrun produces one escalation
     per candidate for the rest of the window.

  2. SAME-LEVEL RATCHET — a level that has already been escalated in this window
     cannot be escalated again, matched on normalised level NAME or on price
     within `price_tol`. Without this, the trigger re-litigates one rejection
     across every candidate that touches it, and the budget is spent on a single
     disagreement.

  3. MECHANICAL GATES NEVER RE-FIRE — window closed, cap exhausted, news
     blackout, the 09:35 open buffer, or an open position are facts about the
     book and the clock, not about the thesis. Tier 1 cannot fix any of them, so
     an escalation carrying one is refused outright and the mechanical pass
     stands.

Two further conditions fall out of the contract itself and are enforced here
rather than trusted to the prompt:

  4. ONCE PER CANDIDATE — the contract says "at most once per candidate".
  5. A REJECTION MUST BE NAMED — the contract licenses escalation only when the
     trigger "can NAME the level that was rejected". A `thesis_stale` with an
     empty `rejected_level` does not qualify.

Refusals are not silent. Every request returns a record, granted or not, and the
orchestrator logs it — the refusals are as interesting as the grants, because a
refused escalation is a place the trigger wanted Tier 1 to move and was not
allowed to ask.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Reasons that are facts about the book or the clock. Tier 1 cannot resolve any
# of them, so they can never justify a re-fire.
MECHANICAL_GATES = frozenset({
    "window_cap",
    "window_cap_exhausted",
    "window_closed",
    "outside_window",
    "news_blackout",
    "cash_open_buffer",
    "cash_open_bar",
    "position_already_open",
})

_NORM = re.compile(r"[^a-z0-9]+")


def normalise_level(name: str) -> str:
    """'prior_day_VAH + bb_2m_upper' -> 'bb2mupper|priordayvah' (order-free)."""
    if not name:
        return ""
    parts = [p for p in _NORM.sub(" ", str(name).lower()).split() if p]
    return "|".join(sorted(set(parts)))


@dataclass
class EscalationRecord:
    candidate_id: str
    window: str
    granted: bool
    reason: str
    level_name: str = ""
    level_price: float | None = None
    outcome: str = ""          # accommodated | reaffirmed — set after Tier 1 answers
    downgraded_to: str | None = None


@dataclass
class EscalationGate:
    """One instance per session-day. Call `open_window` at each window open."""

    budget: int = 2
    price_tol: float = 5.0
    _window: str = ""
    _used: int = 0
    _levels: list[tuple[str, float | None]] = field(default_factory=list)
    _candidates: set[str] = field(default_factory=set)
    log: list[EscalationRecord] = field(default_factory=list)

    def open_window(self, window: str) -> None:
        """Reset the per-window budget, ratchet and candidate set."""
        self._window = window
        self._used = 0
        self._levels = []
        self._candidates = set()

    # -- the ratchet -------------------------------------------------------
    def _level_seen(self, name: str, price: float | None) -> bool:
        norm = normalise_level(name)
        for seen_name, seen_price in self._levels:
            if norm and norm == seen_name:
                return True
            if (price is not None and seen_price is not None
                    and abs(price - seen_price) <= self.price_tol):
                return True
        return False

    # -- the gate ----------------------------------------------------------
    def request(self, candidate_id: str, verdict: dict,
                mechanical_gate: str | None = None) -> EscalationRecord:
        """Decide whether a `thesis_stale: true` verdict earns a Tier-1 re-fire.

        `mechanical_gate` is the orchestrator's own reading of the candidate —
        pass the gate name if the candidate would be refused for a book/clock
        reason regardless of the thesis. It is checked before anything else.
        """
        rl = verdict.get("rejected_level") or {}
        name = rl.get("level", "") if isinstance(rl, dict) else str(rl)
        price = rl.get("price") if isinstance(rl, dict) else None

        def deny(reason: str) -> EscalationRecord:
            rec = EscalationRecord(candidate_id, self._window, False, reason,
                                   name, price, downgraded_to="pass")
            self.log.append(rec)
            return rec

        # 3 — mechanical gates never re-fire, checked first and unconditionally
        if mechanical_gate:
            g = str(mechanical_gate)
            tag = g if g in MECHANICAL_GATES else f"{g} (unrecognised, treated as mechanical)"
            return deny(f"mechanical_gate:{tag}")
        for c in verdict.get("constraints_failed", []) or []:
            if str(c) in MECHANICAL_GATES:
                return deny(f"mechanical_gate:{c}")

        # 5 — the contract licenses escalation only with a named rejection
        if not name:
            return deny("no_rejection_named")

        # T25 QUALIFICATION — only a candidate it would OTHERWISE TAKE may
        # escalate: a same-candle two-level break behind a named rejection.
        # Sequential pairs never qualify; they already default toward pass under
        # T1, so escalating one asks Tier 1 to re-read on evidence the trigger
        # would not have traded anyway.
        shape = str(verdict.get("pair_shape", "")).lower()
        if shape and "same_candle" not in shape:
            return deny(f"T25_not_same_candle:{shape}")

        # 4 — once per candidate
        if candidate_id in self._candidates:
            return deny("already_escalated_this_candidate")

        # 2 — same-level ratchet
        if self._level_seen(name, price):
            return deny("same_level_ratchet")

        # 1 — per-window budget
        if self._used >= self.budget:
            return deny(f"escalation_budget_exhausted ({self.budget} per window)")

        self._used += 1
        self._candidates.add(candidate_id)
        self._levels.append((normalise_level(name), price))
        rec = EscalationRecord(candidate_id, self._window, True, "granted", name, price)
        self.log.append(rec)
        return rec

    # -- the other direction: an escalation the trigger SHOULD have raised ----
    @staticmethod
    def should_have_escalated(verdict: dict) -> tuple[bool, str]:
        """Detect the combination the 0.3.5 contract forbids.

        The gate above can only REFUSE. It cannot manufacture an escalation the
        agent never requested — and the expensive failure is the missing one, not
        the excess one, because a silent pass is precisely what the escalation
        rule was written to abolish. So the orchestrator also checks the inverse:
        a verdict that passes on a THESIS-derived gate while naming a rejected
        level has met the contract's own test ("can I NAME the level that was
        rejected, and did a two-level break prove it?") and should have escalated.

        The candidate existing at all means a two-level break occurred — that is
        the definition of a candidate — so naming the rejection is the only open
        question, and the verdict answers it.

        Returns (True, why) when the verdict should have escalated and did not.
        """
        if verdict.get("thesis_stale"):
            return False, "already escalated"
        if str(verdict.get("decision", "")).startswith("take"):
            return False, "not a pass"
        thesis_gates = {"direction_mismatch", "waiting_for_unmet",
                        "waiting_for", "waiting_for_not_satisfied", "thesis_gate"}
        failed = {str(c) for c in (verdict.get("constraints_failed") or [])}
        if failed & MECHANICAL_GATES:
            return False, "mechanical gate present — escalation correctly withheld"
        hit = failed & thesis_gates
        if not hit:
            return False, "no thesis-derived gate"
        rl = verdict.get("rejected_level") or {}
        name = rl.get("level", "") if isinstance(rl, dict) else str(rl)
        if not name:
            return False, "no rejection named — pass is correct"
        # T25 qualification applies to the inverse detector too: a sequential
        # pair is not an escalation the trigger owed us, so its pass stands.
        shape = str(verdict.get("pair_shape", "")).lower()
        if shape and "same_candle" not in shape:
            return False, f"T25: pair_shape {shape!r} is not same_candle — pass is correct"
        return True, (f"passed on {sorted(hit)} while naming rejected_level "
                      f"{name!r} behind a same-candle break: the contract forbids "
                      f"this combination")

    def record_outcome(self, candidate_id: str, outcome: str) -> None:
        """Tag the most recent granted escalation with accommodated|reaffirmed."""
        if outcome not in ("accommodated", "reaffirmed"):
            raise ValueError(f"outcome must be accommodated|reaffirmed, got {outcome!r}")
        for rec in reversed(self.log):
            if rec.candidate_id == candidate_id and rec.granted:
                rec.outcome = outcome
                return
        raise KeyError(f"no granted escalation for {candidate_id}")

    # -- reporting ---------------------------------------------------------
    def report(self) -> dict:
        granted = [r for r in self.log if r.granted]
        refused = [r for r in self.log if not r.granted]
        by_reason: dict[str, int] = {}
        for r in refused:
            key = r.reason.split(" (")[0]
            by_reason[key] = by_reason.get(key, 0) + 1
        acc = sum(1 for r in granted if r.outcome == "accommodated")
        rea = sum(1 for r in granted if r.outcome == "reaffirmed")
        return {
            "requested": len(self.log),
            "granted": len(granted),
            "refused": len(refused),
            "refused_by_reason": by_reason,
            "accommodated": acc,
            "reaffirmed": rea,
            "reaffirm_rate": (round(rea / len(granted), 3) if granted else None),
            "rows": [vars(r) for r in self.log],
        }


# -- entry-order sanity, orchestrator-side ---------------------------------
def validate_entry_geometry(verdict: dict, price: float) -> list[str]:
    """Catch limit/cancel placements that are void before the order exists.

    Four distinct T12 failures have now been recorded in replay, and the fourth
    was pure arithmetic rather than judgement: a LONG whose `cancel_if_reaches`
    sat BELOW the current price, so the cancel condition was already true at
    placement and the order died on its first bar. The counterfactual filled two
    minutes later and ran 304 points.

    That is checkable, so it is checked here rather than trusted to the agent.
    Returns a list of problems; empty means the geometry is coherent.

    `price` is the close of the last completed bar at the decision minute.
    """
    problems: list[str] = []
    if not str(verdict.get("decision", "")).startswith("take"):
        return problems

    entry = verdict.get("entry")
    stop = verdict.get("stop")
    if entry is None or stop is None:
        return ["take without an entry or a stop"]

    long_side = stop < entry
    cancel = verdict.get("cancel_if_reaches") or {}
    cancel_px = cancel.get("price") if isinstance(cancel, dict) else None

    # T20: the limit must sit between price and where the move came FROM, i.e.
    # price must come BACK to fill it, never go further.
    if long_side and entry > price:
        problems.append(
            f"T20: long limit {entry} is ABOVE price {price} - it needs further "
            f"upward displacement to fill, which is a breakout bet")
    if not long_side and entry < price:
        problems.append(
            f"T20: short limit {entry} is BELOW price {price} - it needs further "
            f"downward displacement to fill, which is a breakout bet")

    # The cancel level is 'the move went without me'. For a long that is UP,
    # for a short DOWN — and it must not already be violated at placement.
    if cancel_px is not None:
        if long_side and cancel_px <= price:
            problems.append(
                f"cancel_if_reaches {cancel_px} is at or below price {price} on a "
                f"LONG - already true at placement, so the order is void on its "
                f"first bar")
        if not long_side and cancel_px >= price:
            problems.append(
                f"cancel_if_reaches {cancel_px} is at or above price {price} on a "
                f"SHORT - already true at placement, so the order is void on its "
                f"first bar")
        if long_side and cancel_px < entry:
            problems.append(
                f"cancel_if_reaches {cancel_px} sits below the long limit {entry} - "
                f"it can never fire before the fill, so it is inoperative")
        if not long_side and cancel_px > entry:
            problems.append(
                f"cancel_if_reaches {cancel_px} sits above the short limit {entry} - "
                f"it can never fire before the fill, so it is inoperative")
    return problems
