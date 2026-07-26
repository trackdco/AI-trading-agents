"""Promotion-gate evidence primitives (docs/PROMOTION-GATE.md sections A/B/C).

The gate must be a SCRIPT's output, not a human's recollection (Angus). Before a report can
assert PASS/FAIL it needs the underlying evidence captured. This module supplies the pieces
the journal did not already cover, audited against the gate's demands:

  * RejectLedger        — ONE normalized, append-only ledger of every rejection, from all
                          sources (spine rule rejects, DTC market-data/order rejects, the
                          order-time spread guard). Today those live in three unrelated sinks;
                          a gate can't tally reason codes across them. (gap: rejection codes)
  * expected_micros /   — recompute the sizing schedule (SAFETY-SPINE dollar-risk) and assert
    check_sizing          the size that actually went out matches it, per trade. The verdict
                          drop already carries conviction/risk_pts/micros; this is the missing
                          ASSERTION over them. (gap: per-trade micros-vs-schedule)

The other two audited gaps live at the execution boundary and are added to src/canon/spine.py:
`SpineExecutor.guard_report` (all-guards fired/not-fired, not just the first trip) and
`SpineExecutor.reconcile` (timer-based naked-position detection, any duration).

`scripts/gate_report.py` (the A/B/C/D PASS/FAIL emitter) is DEFERRED until PROMOTION-GATE.md
lands and pins the exact table shape — these primitives are what it will read.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------- sizing assertion
# SAFETY-SPINE dollar-risk schedule. Floor (available_dd <= $3k): base $200/1.0 tier; past
# +$3k, +$75 per additional $1k of available DD. risk_$ = base × min(2.0, conviction); the
# 2.25 tier caps at 2× base. micros = round(risk_$ / (stop_pts × $2)), clamped to 40.
BASE_DOLLAR_FLOOR = 200.0
DD_FLOOR = 3000.0
DD_STEP_DOLLARS = 75.0
CONVICTION_CAP = 2.0
MNQ_DOLLARS_PER_PT = 2.0
MICRO_CLAMP = 40


def base_dollar(available_dd: float | None) -> float:
    """The 1.0-tier dollar risk for the current available drawdown. None => floor schedule."""
    if available_dd is None or available_dd <= DD_FLOOR:
        return BASE_DOLLAR_FLOOR
    steps = int((available_dd - DD_FLOOR) // 1000)
    return BASE_DOLLAR_FLOOR + DD_STEP_DOLLARS * steps


def expected_micros(conviction: float, stop_pts: float,
                    available_dd: float | None = None) -> int:
    """The size the sizer SHOULD have produced for this trade under the frozen schedule."""
    if stop_pts <= 0:
        raise ValueError(f"stop_pts must be positive, got {stop_pts}")
    risk_d = base_dollar(available_dd) * min(CONVICTION_CAP, float(conviction))
    return min(MICRO_CLAMP, int(round(risk_d / (stop_pts * MNQ_DOLLARS_PER_PT))))


def check_sizing(conviction: float, stop_pts: float, actual_micros: int,
                 available_dd: float | None = None) -> dict:
    """Assert an executed trade's size matches the schedule. Returns a gate-ready row:
    {ok, expected, actual, delta, conviction, stop_pts, available_dd}. `ok=False` means the
    order that went out was NOT the schedule size — a sizer bug, stale available_dd, or a
    misapplied clamp — which is a promotion-gate FAIL, not a rounding nicety."""
    exp = expected_micros(conviction, stop_pts, available_dd)
    return {"ok": int(actual_micros) == exp, "expected": exp, "actual": int(actual_micros),
            "delta": int(actual_micros) - exp, "conviction": float(conviction),
            "stop_pts": float(stop_pts), "available_dd": available_dd}


# --------------------------------------------------------------------------- unified rejects
# Source tags for the ledger.
SRC_SPINE = "spine"
SRC_DTC = "dtc"
SRC_SPREAD_GUARD = "spread_guard"

# DTC message Type -> normalized reject code (the two the desk cares about; see dtc_client).
_DTC_CODE = {103: "market_data_reject", 301: "order_rejected"}


def normalize_spine_reject(decision: dict) -> dict:
    """A spine decision dict (event=='decision', action in reject/halt/flatten) -> ledger row.
    The rule name IS the reject code (feed_stale, spread, duplicate, dd_proximity, ...)."""
    return {"source": SRC_SPINE, "code": decision.get("rule", "unknown"),
            "reason": decision.get("detail", ""),
            "ctx": {"action": decision.get("action"), "setup": decision.get("setup")}}


def normalize_dtc_reject(msg: dict) -> dict:
    """A raw DTC message dict -> ledger row. Tolerant of field naming: DTC MARKET_DATA_REJECT
    carries RejectText; an ORDER_UPDATE rejection carries InfoText + OrderStatus."""
    t = msg.get("Type")
    reason = (msg.get("RejectText") or msg.get("InfoText") or msg.get("text") or "")
    return {"source": SRC_DTC, "code": _DTC_CODE.get(t, f"dtc_type_{t}"),
            "reason": reason,
            "ctx": {k: msg.get(k) for k in ("Symbol", "OrderStatus", "ServerOrderID")
                    if k in msg}}


def normalize_spread_trip(res, ctx: dict | None = None) -> dict:
    """A spread-guard GuardResult (observed/baseline/threshold) -> ledger row."""
    return {"source": SRC_SPREAD_GUARD, "code": getattr(res, "reason", "spread"),
            "reason": (f"observed {getattr(res, 'observed', None)} vs threshold "
                       f"{getattr(res, 'threshold', None)} (baseline {getattr(res, 'baseline', None)})"),
            "ctx": ctx or {}}


@dataclass
class RejectLedger:
    """Append-only JSONL of normalized rejections from every source, so the gate can tally
    reason codes in one place. Fail-soft: a write error never raises into the trade loop."""
    path: str | Path = Path("output/live/rejects.jsonl")
    failures: int = field(default=0)

    def __post_init__(self):
        self.path = Path(self.path)

    def record(self, row: dict, ts: str | None = None) -> bool:
        """Append one normalized reject row (from a normalize_* helper). `ts` is the caller's
        timestamp (kept injectable — no wall-clock call here, so it stays deterministic)."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a") as f:
                f.write(json.dumps({"ts": ts, **row}) + "\n")
            return True
        except Exception:  # noqa: BLE001 — the ledger never breaks trading
            self.failures += 1
            return False

    def rows(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(x) for x in self.path.read_text().splitlines() if x.strip()]

    def code_counts(self) -> dict[str, int]:
        """{code: count} across all sources — the gate's reason-code tally."""
        out: dict[str, int] = {}
        for r in self.rows():
            out[r.get("code", "unknown")] = out.get(r.get("code", "unknown"), 0) + 1
        return out
