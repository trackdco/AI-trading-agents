"""The Desk Verdict — pinned schema + independent arithmetic re-check (Phase 5).

Hermes (third-party, per docs/desk-skills/hermes-coordinator.md) is not trusted with
load-bearing arithmetic — this module is the Python trust boundary the design doc
requires: "the Python runner independently recomputes size/grade; any mismatch or
invalid Hermes output -> the runner synthesizes a VETOED verdict." No LLM output ever
reaches the paper account without passing through here first.

Rules enforced here are strategy-definition-v1.2.md (the LOCKED, current strategy —
NOT the older v1.0 the original Desk blueprint design was drafted against; the skill
docs and this module were corrected to v1.2 on discovery, see docs/desk-skills/):

  * §5.4 minimum stop: a structural stop narrower than `min_stop_points` (10) should
    never have been proposed — Hephaestus must SKIP, not widen. Enforced here as a
    hard rejection, computed directly from entry/stop (never trusted from Hermes).
  * §6.5 RR floor: the SELECTED TARGET LEVEL (not the front-run-adjusted working
    price) must be >= `rr_floor` (2.0) R from entry/stop. The front-run adjustment is
    execution mechanics only and does not enter this calculation (Angus, 17 Jul).
  * §9 sizing (v1.2 — Angus calibration ruling, 17 Jul 2026): full size is the
    DEFAULT for every trade that clears the gates, counter-trend included. There is
    NO confluence-count or with-trend/A-at-extension size reduction anymore (that
    v1.1 ladder was deleted). Half applies ONLY if either: the stop is wider than
    `oversized_stop_points` (42), or the trigger fills after `late_window_after_et`
    (10:30 ET) in a session-scoped window (W2 has no time-based sizing at all). Both
    conditions are recomputed directly here from entry/stop/trigger_ts — never taken
    on Hermes's word.

    from src.desk.verdict import validate_verdict
    result = validate_verdict(raw_json_text, cfg)   # ValidationResult
    if result.ok:
        ...  # result.verdict is a trustworthy DeskVerdict
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import time as dtime
from typing import Literal

import pandas as pd
from pydantic import BaseModel, Field, ValidationError

Gate = Literal["pass", "fail"]

NY = "America/New_York"


class GateReason(BaseModel, extra="forbid"):
    code: str
    detail: str = ""


class Facts(BaseModel, extra="forbid"):
    """Verbatim, informational context echoed by Hermes from the specialists' own
    outputs. NOT trusted for size/grade arithmetic (that's recomputed directly from
    entry/stop/trigger_ts below) — kept for audit/journal readability only."""
    confluence_count: int | None = None
    with_trend: bool | None = None
    a_at_extension: bool | None = None
    target_r_multiple: float | None = None
    half_trigger_count: int | None = None
    half_trigger_reasons: list[str] = Field(default_factory=list)


class DeskVerdict(BaseModel, extra="forbid"):
    """Pinned schema per docs/agent-blueprint.md §4.4, corrected for v1.2 sizing.
    Strict: an unrecognized field from Hermes is a schema violation, not a warning.

    target_level: the RAW selected menu level (§6.1-6.2) — the RR-floor and sizing
        checks below use THIS, never the front-run-adjusted price (§6.4's F is
        execution-only per the v1.2 ruling).
    target: the front-run-adjusted working price actually used for fills (§6.4).
    """
    trade: bool
    pattern: Literal["A", "B", "B2"]
    direction: Literal["long", "short"]
    entry: float | None = None
    stop: float | None = None
    target_level: float | None = None
    target: float | None = None
    size: Literal["full", "half"] | None = None
    grade: Literal["A", "B"] | None = None
    thesis: str
    gates: dict[str, Gate]
    gate_reasons: dict[str, GateReason] = Field(default_factory=dict)
    trigger_ts: str
    snapshot_ts: str
    facts: Facts = Field(default_factory=Facts)


REQUIRED_GATES = {"atlas", "helios", "apollo", "hephaestus"}


@dataclass(frozen=True)
class SizingConfig:
    """strategy-definition-v1.2.md §5.4/§6.5/§9, config/strategy.yaml `sizing:`."""
    min_stop_points: float = 10.0          # §5.4 v1.2 — narrower than this = should skip
    rr_floor: float = 2.0                  # §6.5 v1.2 — hard, not CALIBRATE
    oversized_stop_points: float = 42.0    # §9 — config: sizing.oversized_stop_points
    late_window_after_et: str = "10:30"    # §9 — config: sizing.late_window_after
    window_session_scoped: bool = True     # W1 etc. = True; W2 (full-day) = False,
                                           # no time-based sizing at all (Angus, 17 Jul)


@dataclass
class ValidationResult:
    ok: bool
    verdict: DeskVerdict | None
    veto_reason: str | None = None      # populated iff not ok


def _stop_points(v: DeskVerdict) -> float:
    return abs(v.entry - v.stop)


def _is_late_window(trigger_ts: str, cfg: SizingConfig) -> bool:
    if not cfg.window_session_scoped:
        return False                    # W2: no time-based sizing at all (Angus ruling)
    t = pd.Timestamp(trigger_ts).tz_convert(NY) if pd.Timestamp(trigger_ts).tzinfo \
        else pd.Timestamp(trigger_ts, tz=NY)
    h, m = (int(x) for x in cfg.late_window_after_et.split(":"))
    return t.time() > dtime(h, m)


def _recompute_size_grade(v: DeskVerdict, cfg: SizingConfig) -> tuple[str, str]:
    """§9 v1.2: full is the default; half ONLY on stop-width or late-window, computed
    directly from entry/stop/trigger_ts — never taken on Hermes's word. The two
    triggers "do not stack below half" (per the doc) — there is no lower tier."""
    oversized = _stop_points(v) > cfg.oversized_stop_points
    late = _is_late_window(v.trigger_ts, cfg)
    size = "half" if (oversized or late) else "full"
    grade = "A" if size == "full" else "B"
    return size, grade


def validate_verdict(raw: str | bytes, cfg: SizingConfig) -> ValidationResult:
    """Fail-closed at every step: bad JSON, schema violation, gate/trade arithmetic
    mismatch, an undersized stop, a target that misses the RR floor, or a size/grade
    recompute mismatch all veto. Nothing here ever raises into a caller."""
    try:
        obj = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as e:
        return ValidationResult(False, None, f"invalid_json: {e}")

    try:
        v = DeskVerdict(**obj)
    except ValidationError as e:
        return ValidationResult(False, None, f"schema_violation: {e}")

    if set(v.gates) != REQUIRED_GATES:
        return ValidationResult(False, None,
                                "schema_violation: gates must be exactly "
                                f"{sorted(REQUIRED_GATES)}, got {sorted(v.gates)}")

    expected_trade = all(v.gates[g] == "pass" for g in REQUIRED_GATES)
    if v.trade != expected_trade:
        return ValidationResult(False, None,
                                "hermes_arithmetic_mismatch: trade != AND(gates) "
                                f"(trade={v.trade}, gates={v.gates})")

    if not v.trade:
        return ValidationResult(True, v)          # a well-formed veto is a valid result

    if v.entry is None or v.stop is None or v.target_level is None or \
            v.target is None or v.size is None:
        return ValidationResult(False, None,
                                "schema_violation: trade=true requires entry/stop/"
                                "target_level/target/size populated")

    stop_pts = _stop_points(v)
    if stop_pts < cfg.min_stop_points:
        return ValidationResult(False, None,
                                f"min_stop_violation: stop is {stop_pts:.2f} pts, "
                                f"below the {cfg.min_stop_points}pt v1.2 floor "
                                "(strategy-definition-v1.2.md §5.4) — should have "
                                "been a skip, never proposed")

    r_multiple = abs(v.target_level - v.entry) / stop_pts
    if r_multiple < cfg.rr_floor:
        return ValidationResult(False, None,
                                f"rr_floor_violation: {r_multiple:.2f}R to the raw "
                                f"target level, below the {cfg.rr_floor}R v1.2 floor "
                                "(§6.5 — measured to target_level, never the "
                                "front-run-adjusted target)")

    exp_size, exp_grade = _recompute_size_grade(v, cfg)
    if v.size != exp_size or v.grade != exp_grade:
        return ValidationResult(False, None,
                                "hermes_arithmetic_mismatch: size/grade recompute "
                                f"disagrees (hermes size={v.size} grade={v.grade}, "
                                f"recomputed size={exp_size} grade={exp_grade}, "
                                f"stop_pts={stop_pts:.2f}, "
                                f"late_window={_is_late_window(v.trigger_ts, cfg)})")

    if v.direction == "long" and not (v.stop < v.entry < v.target):
        return ValidationResult(False, None,
                                f"incoherent_construction: long requires "
                                f"stop<entry<target (got {v.stop},{v.entry},{v.target})")
    if v.direction == "short" and not (v.target < v.entry < v.stop):
        return ValidationResult(False, None,
                                f"incoherent_construction: short requires "
                                f"target<entry<stop (got {v.target},{v.entry},{v.stop})")

    return ValidationResult(True, v)
