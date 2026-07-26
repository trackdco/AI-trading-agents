"""Working-order lifecycle watch (gate B7) — the live twin of engine.py's T_cancel block.

The backtest cancels a resting, unfilled entry limit in three cases (engine.py, the
"working order (only when flat)" block), and the arming reference was measured WITH those
cancels active — disabling t_cancel alone moves 34 fills in a single month
(docs/FINDING-live-path-cannot-cancel-a-resting-limit.md). A live bot that leaves stale
limits resting takes EXTRA trades the edge was never measured on. This module mirrors the
engine's cancel decisions per closed bar; the caller executes them through the B7 broker
surface (`DTCBroker.cancel_order`) and journals every one.

Mirrored EXPRESSION-FOR-EXPRESSION from src/backtest/engine.py (same reason strings as the
engine's veto records, so live journals and backtest verdicts diff cleanly):

  cancelled_tcancel      ran = (h >= limit + t_cancel) if long else (lo <= limit - t_cancel)
                         — and in the engine a cancel WINS over a same-bar fill. Live, that
                         race is physical (Sierra may fill intrabar before the bar closes);
                         when a fill lands on a bar that also satisfies `ran`, on_bar reports
                         it as `raced_fill` so the divergence is journaled, never silent.
  cancelled_window_end   not (win_start <= tod < win_end)   [wrap-aware for overnight spans]
  cancelled_eod          eod_flatten <= tod < 18:00

NOT mirrored here, deliberately: `cancelled_halt` — the spine owns halting, and its kill
path already cancels every working order (`cancel_all`/`flatten`). Market entries (E4/EC
displacement) never rest, so they are never registered.

Defaults come from the SAME config the engine reads (`load_backtest_config()`), so the live
threshold cannot drift from the backtest's 22.0 by being restated.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time as dtime

import pandas as pd

NY = "America/New_York"
_SESSION_CLOSE = dtime(18, 0)


@dataclass
class WorkingOrder:
    ref: str                     # broker ref (the bracket's entry ClientOrderID)
    side: str                    # "B" | "S"
    limit: float
    filled: bool = False


@dataclass
class OrderWatch:
    """Feed it every closed 1m bar; it returns the cancel decisions the engine would have
    made. The caller (route_b armed path) executes + journals them — this class decides,
    it never touches a broker."""
    t_cancel: float | None = None
    win_start: dtime | None = None
    win_end: dtime | None = None
    eod_flatten: dtime | None = None
    _orders: dict[str, WorkingOrder] = field(default_factory=dict, init=False)

    def __post_init__(self):
        if None in (self.t_cancel, self.win_start, self.win_end, self.eod_flatten):
            from src.backtest.engine import load_backtest_config
            cfg = load_backtest_config()
            self.t_cancel = cfg.t_cancel if self.t_cancel is None else self.t_cancel
            self.win_start = cfg.win_start if self.win_start is None else self.win_start
            self.win_end = cfg.win_end if self.win_end is None else self.win_end
            self.eod_flatten = (cfg.eod_flatten if self.eod_flatten is None
                                else self.eod_flatten)

    # ---- lifecycle ----------------------------------------------------------
    def register(self, ref: str, side: str, limit: float) -> None:
        """Track a LIMIT entry that is now resting at the broker. Market entries never rest
        and must not be registered."""
        self._orders[ref] = WorkingOrder(ref=ref, side=side, limit=float(limit))

    def mark_filled(self, ref: str) -> None:
        """Broker ORDER_UPDATE said filled — stop watching (management takes over)."""
        o = self._orders.get(ref)
        if o is not None:
            o.filled = True

    def mark_gone(self, ref: str) -> None:
        """Cancelled/rejected at the broker for any reason — stop watching."""
        self._orders.pop(ref, None)

    @property
    def watching(self) -> list[str]:
        return [r for r, o in self._orders.items() if not o.filled]

    # ---- the per-bar decision (mirrors engine.py's working-order block) ------
    def _in_window(self, tod: dtime) -> bool:
        if self.win_start <= self.win_end:
            return self.win_start <= tod < self.win_end
        return tod >= self.win_start or tod < self.win_end     # overnight wrap

    def _past_eod(self, tod: dtime) -> bool:
        return self.eod_flatten <= tod < _SESSION_CLOSE

    def on_bar(self, ts, high: float, low: float) -> list[dict]:
        """Evaluate every watched order against one CLOSED bar. Returns cancel decisions
        [{ref, reason, detail, raced_fill}]; decided orders are dropped from the watch (the
        caller executes the broker cancel and journals). A `filled` order is skipped — but
        if its fill landed on a bar that ALSO satisfies the cancel condition, that is the
        engine-vs-live race (engine cancels, exchange filled first): reported with
        raced_fill=True so it reaches the journal as a divergence, never silently."""
        tod = pd.Timestamp(ts).time()
        out: list[dict] = []
        for ref, o in list(self._orders.items()):
            sign = 1 if o.side == "B" else -1
            ran = (high >= o.limit + self.t_cancel) if sign == 1 else \
                  (low <= o.limit - self.t_cancel)
            if o.filled:
                if ran:                        # the physical race: journal it, don't act
                    out.append({"ref": ref, "reason": "tcancel_raced_fill",
                                "detail": f"fill landed on a bar that ran {self.t_cancel} "
                                          f"pts beyond limit {o.limit} — engine would have "
                                          "cancelled; exchange filled first",
                                "raced_fill": True})
                self._orders.pop(ref, None)    # either way, management owns it now
                continue
            if self._past_eod(tod):
                decision = {"ref": ref, "reason": "cancelled_eod",
                            "detail": "order cancelled before fill", "raced_fill": False}
            elif not self._in_window(tod):
                decision = {"ref": ref, "reason": "cancelled_window_end",
                            "detail": f"unfilled at {self.win_end}", "raced_fill": False}
            elif ran:
                decision = {"ref": ref, "reason": "cancelled_tcancel",
                            "detail": f"price ran {self.t_cancel} pts beyond limit unfilled",
                            "raced_fill": False}
            else:
                continue
            self._orders.pop(ref, None)
            out.append(decision)
        return out
