"""The live canon decision lane (shape i) — the AUTHORITATIVE trade path.

Pat ruling (this session): the canon-scripts lane is the sole live decision-maker — the lane
that produced the signed-off `baseline_book.parquet` (400/400, +$56,065.18). NO champion in
the trade path, NO LLM proposing verdicts. The chain is exactly:

    hermes-router (clock lookup) -> SHELL OUT canon_mechanical.py + london_canon.py (frozen,
    never re-implemented) -> Python dollar-risk sizer (baseline_dollar_risk.size_book) ->
    atomic file-drop (canon_runtime.drop_verdicts) -> canon-relay byte passthrough
    (canon_runtime.relay) -> the relayed verdict drives the verdict journal + the spine intent.

A VERDICT is an ENTRY decision (direction/entry/stop/target/size), captured at decision time.
In a SHADOW run (zero orders — the pre-arming stage) there are no fills or exits, so the lane
emits VERDICT RECORDS (the §D shadow evidence at ~3.8/week), not completed trades; the
completed-trade JournalRecord is an ARMED-run artifact (needs real fills) and is out of scope
here.

P1 = the loop SKELETON. `ScriptVerdictSource` shells out the frozen scripts over the batch
matrices (the covered feature families); P2 swaps the matrix inputs from batch to a live
assembly behind the SAME `VerdictSource` interface. Until then the verdict source is a seam.

FLAGGED, not papered over:
  * The canon scripts emit NO bracket target — the canon exit is MANAGED (V8 etc.), not a fixed
    target. The spine's OrderIntent needs one, so `target_rr` derives a PROVISIONAL R-multiple
    target purely so the disarmed spine can evaluate. The fixed-bracket-vs-managed-exit
    execution model must be resolved before arming.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Protocol

import pandas as pd

from scripts.baseline_dollar_risk import size_book
from src.canon.spine import OrderIntent
from src.desk.canon_runtime import drop_verdicts, relay, run_canon_engine

PROVISIONAL_TARGET_RR = 2.0        # §6.5 RR floor — provisional bracket target (see module doc)


class VerdictSource(Protocol):
    """Yields the canon verdicts for a session day (already sized, with execution levels).
    P1: ScriptVerdictSource (shell-out over batch matrices). P2: a live-assembly source behind
    this same interface."""
    def session_verdicts(self, day: str) -> list[dict]: ...


class ScriptVerdictSource:
    """Shell out the frozen canon scripts, size, attach execution levels, drop, and relay —
    the full shape-i chain — returning the RELAYED verdicts for a session day. The engine is
    run once and cached; `session_verdicts` filters it. `engine_fn` is injectable for tests."""

    def __init__(self, engine_fn=run_canon_engine, target_rr: float = PROVISIONAL_TARGET_RR):
        self._engine = engine_fn
        self._target_rr = target_rr
        self._book: pd.DataFrame | None = None

    @staticmethod
    def _leveled(book: pd.DataFrame, session: str) -> pd.DataFrame:
        """size_book() drops entry/stop — join them back on (day, fill, direction) so the
        verdict carries the execution levels the spine intent needs."""
        sized = size_book(book, session)
        if sized.empty:
            return sized.assign(entry=[], stop=[])
        sized["_d"] = sized["day"].astype(str)
        lvl = book[book["size"] > 0].copy()
        lvl["fill"] = pd.to_datetime(lvl["fill"], utc=True)
        lvl["_d"] = lvl["day"].astype(str)
        lvl = lvl[["_d", "fill", "direction", "entry", "stop"]].drop_duplicates(
            ["_d", "fill", "direction"])
        return sized.merge(lvl, on=["_d", "fill", "direction"], how="left").drop(columns=["_d"])

    def _load(self) -> pd.DataFrame:
        if self._book is None:
            ny, lon = self._engine()
            parts = [self._leveled(ny, "NY"), self._leveled(lon, "LONDON")]
            b = pd.concat([p for p in parts if not p.empty], ignore_index=True) \
                if any(not p.empty for p in parts) else parts[0]
            if not b.empty:
                b = b.sort_values("fill").reset_index(drop=True)
                sign = b["direction"].map({"long": 1.0, "short": -1.0}).fillna(0.0)
                b["target"] = b["entry"] + sign * self._target_rr * b["risk_pts"]
            self._book = b
        return self._book

    def session_verdicts(self, day: str) -> list[dict]:
        b = self._load()
        if b.empty:
            return []
        sub = b[b["day"].astype(str) == str(day)]
        if sub.empty:
            return []
        drop_dir = Path(tempfile.mkdtemp(prefix="canon_verdict_"))
        drop_verdicts(sub, drop_dir)          # atomic file-drop (with entry/stop/target)
        return relay(drop_dir)                # canon-relay byte passthrough -> verdicts


# --------------------------------------------------------------------------- verdict mappers
def verdict_record(v: dict, roll_ctx: dict | None = None) -> dict:
    """The shadow verdict-journal row — the §D decision evidence (an ENTRY, not a completed
    trade). Compact and gate-readable. `pl` is carried through only when the source is a replay
    that already knows the outcome; a live shadow leaves it as the source provided."""
    rc = roll_ctx or {}
    out = {"type": "verdict", "session": v.get("session"), "day": v.get("day"),
           "fill": v.get("fill"), "direction": v.get("direction"),
           "entry": v.get("entry"), "stop": v.get("stop"), "target": v.get("target"),
           "conviction": v.get("conviction"), "risk_pts": v.get("risk_pts"),
           "micros": v.get("micros"), "pl": v.get("pl"),
           "roll": rc.get("roll"), "contract": rc.get("contract")}
    return out


def verdict_to_intent(v: dict, account: str = "FUNDED") -> OrderIntent:
    """Build the disarmed spine OrderIntent from a relayed verdict. size = the verdict's own
    micros (the PRODUCTION dollar-risk sizer already sized the canon book — not recomputed)."""
    return OrderIntent(
        side="B" if v.get("direction") == "long" else "S",
        order_type="limit",
        entry_ref=float(v["entry"]), stop=float(v["stop"]), target=float(v["target"]),
        size=max(1, int(v.get("micros", 0) or 0)),
        setup_id=f"{v.get('day')}:{v.get('fill')}", account=account)
