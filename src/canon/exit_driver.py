"""Live exit driver — REUSES engine.py's simulate() management for the canon exit (no re-impl).

The canon's exits ARE `simulate()` run with the E3/E4 V8 config: `_regen_build_substrate_v2.py`
runs `simulate(seg, trigs, books(base))` → substrate → `trade_matrix` → the signed-off book. So
the live exit must drive that SAME code — the way `Vault` reuses `simulate()` for entries — not a
re-implementation (the champion-vs-canon lesson: a faithful-to-spec re-write shared 14% of trades
with the thing it re-wrote). Correctness is BY CONSTRUCTION: the exit decisions are engine.py's,
surfaced verbatim through the `on_manage` callback and translated into broker orders.

  drive()            run simulate() with on_manage; return the FILL + ordered exit actions.
  entry pinned       the FILL event's entry/stop MUST match the canon's to the tick before ANY
                     exit is trusted (verified in scripts/exit_driver_verify.py).
  3-min cut          canon_mechanical Layer 2d overlay (NOT in simulate): reuse the frozen
                     condition, applied at t+3min as an early MARKET exit, precedence over simulate.
  to_broker_actions  stop_move → modify the resting stop; partial → partial-close; exit → the
                     resting stop fires or a marketable order (B2 is entries-only; exits may slip).

`src/canon/exit_manager.py` is retained ONLY as a comparator (run both, journal divergence), never
the production path.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time as dtime

from src.backtest.engine import load_backtest_config, simulate

# 3-min cut (canon_mechanical.py Layer 2d) — frozen condition, reused not re-derived.
CUT_AFTER_MIN = 3
CUT_R3_MAX = -0.1106
CUT_FW3_MAX = -13.0


def exit_cfgs():
    """The exact (E3, E4) configs that produced the canon exits — the substrate recipe
    (`_regen_build_substrate_v2.main`): base + win 08:00–10:15, max 2 trades/day, via books()."""
    from scripts.grade_window_cap import books
    base = load_backtest_config().model_copy(
        update={"win_start": dtime(8, 0), "win_end": dtime(10, 15), "max_trades_per_day": 2})
    return books(base)


@dataclass
class DriveResult:
    fill: dict | None = None                  # the fill event {entry, stop, fill_ts, risk_pts, ...}
    actions: list[dict] = field(default_factory=list)   # stop_move / partial / exit, in order
    entry_ok: bool = False                    # fill matched the canon entry+stop to the tick
    detail: str = ""


class ExitDriver:
    """Drives engine.py's management for a canon position and surfaces its exit actions."""

    def __init__(self, tick: float = 0.25):
        self.tick = tick

    def drive(self, bars, trigger, cfg, *, canon_entry: float, canon_stop: float) -> DriveResult:
        """Run simulate() over `bars` for `trigger` with the on_manage hook. VERIFY the resulting
        fill matches the canon's entry+stop to the tick; only then are the exit actions trustworthy
        (a mismatch means simulate entered a different position — do NOT trust its exit)."""
        events: list[dict] = []
        simulate(bars, [trigger], cfg, on_manage=events.append)
        fill = next((e for e in events if e["kind"] == "fill"), None)
        actions = [e for e in events if e["kind"] in ("stop_move", "partial", "exit")]
        if fill is None:
            return DriveResult(fill=None, actions=actions, entry_ok=False,
                               detail="simulate produced no fill for this trigger")
        half = self.tick / 2.0
        entry_ok = (abs(fill["entry"] - canon_entry) <= half
                    and abs(fill["stop"] - canon_stop) <= half)
        detail = "" if entry_ok else (
            f"ENTRY MISMATCH: sim fill entry={fill['entry']} stop={fill['stop']} vs canon "
            f"entry={canon_entry} stop={canon_stop} — exit NOT trustworthy")
        return DriveResult(fill=fill, actions=actions, entry_ok=entry_ok, detail=detail)


def three_min_cut(r_3: float | None, fw_3: float | None) -> bool:
    """The canon 3-min cut (Layer 2d), reused: True → exit at market NOW. Overlay on top of
    simulate's management, taking precedence when it fires at t+CUT_AFTER_MIN."""
    return (r_3 is not None and fw_3 is not None
            and r_3 <= CUT_R3_MAX and fw_3 <= CUT_FW3_MAX)


def to_broker_actions(result: DriveResult) -> list[dict]:
    """Translate engine.py's management events into broker order actions. REFUSES if the entry
    was not pinned (never manage an exit for a position we didn't reproduce)."""
    if not result.entry_ok:
        raise ValueError(f"entry not pinned — refusing to translate exits: {result.detail}")
    out = []
    for e in result.actions:
        if e["kind"] == "stop_move":
            out.append({"action": "modify_stop", "price": e["price"], "market": False})
        elif e["kind"] == "partial":
            out.append({"action": "partial_close", "frac": e["frac"], "price": e["price"],
                        "reason": e["reason"], "market": e["reason"] not in ("target",)})
        elif e["kind"] == "exit":
            # stop-outs / cut / eod are marketable; a target exit rests as a limit.
            out.append({"action": "close", "price": e["price"], "reason": e["reason"],
                        "market": e["reason"] != "target"})
    return out
