"""Combined daily de-risk gate — merge the regime + HTF verdicts into one decision.

The two agents each produce a per-day gate; the engine needs ONE. This module
does the merge with a conservative AND posture (a trade type is allowed only if
BOTH agents permit it — the fail-safe stance the whole system uses) and records
WHY, so the walk-forward replay can attribute a blocked trade to the right agent.

Mapping between the two vocabularies:
  - a REVERSION trade fades the move  -> allowed iff regime permits "reversion"
    AND the HTF agent permits fades (fade_permitted).
  - a CONTINUATION trade rides the move -> allowed iff regime permits
    "continuation" (the HTF agent never vetoes continuation; `continuation_only`
    actually favors it).
  - size = the regime agent's size_multiplier (the HTF agent gates permission,
    not size); forced to 0 when nothing is permitted.
  - either agent standing everything down forces a full stand-down.

Engine integration (flagged for the engine lane): `simulate()` needs a per-day
de-risk hook that consumes `CombinedGate` exactly like the existing day/time
condition de-risks. This module produces the schedule; wiring it into the fill
loop is the one engine-lane touch the replay needs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pandas as pd
from pydantic import BaseModel

from src.desk.htf_agent import HTFGate
from src.desk.regime_agent import RegimeGate


class CombinedGate(BaseModel, extra="forbid"):
    date: str
    allow_reversion: bool
    allow_continuation: bool
    size_multiplier: float
    directional_bias: str
    stand_down: bool
    reasons: list[str]              # human-auditable: which agent drove each restriction
    conflict: bool                  # true when the agents disagree on a structure


def combine(regime: RegimeGate, htf: HTFGate) -> CombinedGate:
    if regime.date != htf.date:
        raise ValueError(f"date mismatch: regime {regime.date} vs htf {htf.date}")

    reasons: list[str] = []
    conflict = False

    # reversion = fade: needs regime permission AND htf fade permission
    allow_reversion = regime.allow_reversion and htf.fade_permitted
    if regime.allow_reversion and not htf.fade_permitted:
        reasons.append("reversion blocked: HTF agent forbids fades (trend segment / unclear)")
        conflict = True
    elif not regime.allow_reversion and htf.fade_permitted:
        reasons.append("reversion blocked: regime agent excludes reversion")
        conflict = True

    # continuation = with the move: regime permission governs; htf never vetoes it
    allow_continuation = regime.allow_continuation
    if not regime.allow_continuation:
        reasons.append("continuation blocked: regime agent excludes continuation")

    size = regime.size_multiplier
    stand_down = not (allow_reversion or allow_continuation) or size == 0.0

    if stand_down and not reasons:
        reasons.append("stand down: no structure permitted by either agent")
    if htf.continuation_only and allow_reversion:
        # HTF said continuation-only yet fade slipped through — shouldn't happen given the
        # schema, but assert the invariant loudly rather than trade on a contradiction
        raise ValueError("invariant: continuation_only gate permitted a reversion")

    return CombinedGate(
        date=regime.date,
        allow_reversion=allow_reversion,
        allow_continuation=allow_continuation,
        size_multiplier=0.0 if stand_down else size,
        directional_bias=regime.directional_bias,
        stand_down=stand_down,
        reasons=reasons or ["both agents permit the day's structures"],
        conflict=conflict,
    )


# ------------------------------------------------------------------ engine seam

# keys the engine's simulate(day_gate=...) reads (docs/replay-integration-contract.md)
_GATE_KEYS = ("stand_down", "allow_reversion", "allow_continuation", "size_multiplier")


def day_gate_from_schedule(
    schedule_csv: Path = Path("output/combined_gate_schedule.csv"),
) -> Callable[[str], dict | None]:
    """Load output/combined_gate_schedule.csv into the `day_gate` callable the engine's
    simulate() consumes: date 'YYYY-MM-DD' -> {stand_down, allow_reversion,
    allow_continuation, size_multiplier} or None for a day with no verdict (arm A).

    Returns a plain dict (not a pydantic model) so the engine imports no desk module —
    the architecture boundary holds from both sides."""
    df = pd.read_csv(schedule_csv)
    table = {
        str(row["date"]): {k: row[k] for k in _GATE_KEYS}
        for _, row in df.iterrows()
    }
    return lambda date: table.get(date)
