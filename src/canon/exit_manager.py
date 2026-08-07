"""Managed-exit decision engine for the canon (Angus RESOLVED — docs/FOR-ANGUS-managed-exit-question.md).

The canon has NO fixed bracket target — the exit is MANAGED. This reproduces the V8 management +
3-minute cut + EOD flatten that produced the signed-off book, as a deterministic per-bar decision
component: given a filled position and bar/feature updates it emits EXIT ACTIONS. Entries stay
limit-only (not this module's concern); exits are MARKETABLE where the canon exits at the market
(the 3-min cut, EOD flatten, and stop-outs — Angus B1: "those genuinely slip").

Rules, faithful to src/backtest/engine.py's V8 arm (cited inline):
  * BE MOVE     — a premarket fill moves the stop to entry at `be_time` (engine.py:684-686).
  * PARTIAL     — book `partial_pct` (50%, v8_partial_pct) at the first STRUCTURE level via
                  trade-through (engine.py:649-665).
  * TRAIL       — once the partial is booked, ratchet the runner's stop behind the prior completed
                  5-minute swing (engine.py:683-693): long trails to the swing LOW, short to the
                  swing HIGH, moving only in the favourable direction.
  * 3-MIN CUT   — `cut_after_min` into the trade, if r_3 <= cut_r3_max AND fw_3 <= cut_fw3_max,
                  exit NOW at the market (canon_mechanical.py Layer 2d).
  * EOD FLATTEN — flatten any remainder at `eod_flatten`.

STATUS — DEMOTED TO COMPARATOR (superseded). This module is NO LONGER the production exit path
and must not be armed. `src/canon/exit_driver.py` is: it drives engine.py's OWN management via
the `on_manage` hook, so its exits are engine.py's by construction rather than by re-statement
(proved in tests/test_exit_driver.py — the emitted events reconstruct every TradeRecord, and an
isolated re-run reproduces the in-context position's actions byte-for-byte).

The reason for the demotion is the risk this module always carried and could never retire: it is
a HAND-MAINTAINED COPY of engine.py's management, so every future engine edit silently forks it
(the champion-vs-canon lesson — a faithful-to-spec re-write shared 14% of its trades with the
thing it re-wrote). Its remaining job is to be the second opinion: run it alongside the driver in
shadow and journal any divergence, which is a cheap standing check on both. If it ever disagrees
with the driver, the DRIVER is right by definition and this module is the thing to fix or delete.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time as dtime


@dataclass(frozen=True)
class ExitConfig:
    partial_pct: float = 50.0                 # v8_partial_pct — % booked at first structure
    be_time: dtime = dtime(9, 29)             # premarket fill -> stop to entry at this ET time
    cut_after_min: int = 3                    # the in-trade cut is evaluated at t+this
    cut_r3_max: float = -0.1106               # 3-min cut: r_3 <= this AND ...
    cut_fw3_max: float = -13.0                # ... fw_3 <= this -> exit at market
    eod_flatten: dtime = dtime(15, 59)        # flatten the remainder at/after this ET time


@dataclass
class ManagedPosition:
    direction: str                            # "long" | "short"
    entry: float
    stop: float
    size: int
    fill_time: object                         # tz-aware ET timestamp of the fill
    first_structure: float | None = None      # partial target level (from the canon menu)
    # live-managed state
    partial_done: bool = field(default=False)
    be_done: bool = field(default=False)
    cut_checked: bool = field(default=False)
    closed: bool = field(default=False)

    @property
    def sign(self) -> int:
        return 1 if self.direction == "long" else -1


@dataclass(frozen=True)
class ExitAction:
    kind: str                                 # move_be | partial | trail_stop | cut | flatten
    price: float | None = None                # new stop (trail) / partial level; None for market
    pct: float | None = None                  # fraction for a partial
    reason: str = ""
    market: bool = False                      # True if this exit is a marketable order


class ManagedExit:
    """Per-bar managed exit. Call `on_bar` with each closed bar while the position is open; it
    returns the exit actions to take (possibly several), mutating the position's managed state."""

    def __init__(self, cfg: ExitConfig | None = None):
        self.cfg = cfg or ExitConfig()

    def on_bar(self, pos: ManagedPosition, *, high: float, low: float, now,
               r_3: float | None = None, fw_3: float | None = None,
               prior_5m_swing_low: float | None = None,
               prior_5m_swing_high: float | None = None,
               through: float = 0.0) -> list[ExitAction]:
        if pos.closed:
            return []
        c, sign, tod = self.cfg, pos.sign, _time_of(now)
        acts: list[ExitAction] = []

        # BE move: a premarket fill moves the stop to entry once `be_time` passes (engine V8).
        if (not pos.be_done and _time_of(pos.fill_time) < c.be_time and tod >= c.be_time):
            pos.be_done = True
            pos.stop = pos.entry
            acts.append(ExitAction("move_be", price=pos.entry, reason="be_at_time"))

        # 3-minute cut: at t+cut_after_min, adverse r_3 & fw_3 -> exit at market NOW.
        mins = _minutes_since(pos.fill_time, now)
        if (not pos.cut_checked and mins is not None and mins >= c.cut_after_min
                and r_3 is not None and fw_3 is not None):
            pos.cut_checked = True
            if r_3 <= c.cut_r3_max and fw_3 <= c.cut_fw3_max:
                pos.closed = True
                acts.append(ExitAction("cut", reason="3min_cut", market=True))
                return acts

        # Partial at the first structure via trade-through.
        if not pos.partial_done and pos.first_structure is not None:
            lvl = pos.first_structure
            hit = (high >= lvl + through) if sign == 1 else (low <= lvl - through)
            if hit:
                pos.partial_done = True
                acts.append(ExitAction("partial", price=lvl, pct=c.partial_pct / 100.0,
                                       reason="partial_structural"))

        # Trail the runner behind the prior completed 5m swing once the partial is booked;
        # ratchet only in the favourable direction (never loosen the stop).
        if pos.partial_done:
            cand = prior_5m_swing_low if sign == 1 else prior_5m_swing_high
            if cand is not None and ((sign == 1 and cand > pos.stop)
                                     or (sign == -1 and cand < pos.stop)):
                pos.stop = cand
                acts.append(ExitAction("trail_stop", price=cand, reason="v8_5m_swing_trail"))

        # EOD flatten the remainder.
        if not pos.closed and tod >= c.eod_flatten:
            pos.closed = True
            acts.append(ExitAction("flatten", reason="eod", market=True))
        return acts


def _time_of(ts) -> dtime:
    return ts.time() if hasattr(ts, "time") else ts


def _minutes_since(fill, now) -> float | None:
    try:
        return (now - fill).total_seconds() / 60.0
    except Exception:  # noqa: BLE001
        return None
