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
