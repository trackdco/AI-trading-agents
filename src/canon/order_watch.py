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


STRUCT_ACCEPT = 5.0    # pts traded beyond a touched level = acceptance ("broke")
STRUCT_REJECT = 8.0    # pts back off a touched level = "rejects hard"


@dataclass
class WorkingOrder:
    ref: str                     # broker ref (the bracket's entry ClientOrderID)
    side: str                    # "B" | "S"
    limit: float
    filled: bool = False
    #: session window this order belongs to; None = the watch's global window. REBUILT CANON:
    #: pre-market orders die at 09:30 and golden-window orders at 10:30, so a single global
    #: window cannot serve both — an order outliving its own session is an unmeasured trade.
    win_end: dtime | None = None
    #: away-side structural levels [(name, price, type)] and the running struct observation.
    #: Mirrors scripts/build_l1_fills.py::walk_one expression-for-expression; feeds the elite
    #: 2.0x tier, which requires struct_event == "broke".
    levels: list = field(default_factory=list)
    touched: list = field(default_factory=list)
    struct_event: str = ""       # "" | "broke" | "rejected"
    struct_level: str = ""


@dataclass
class OrderWatch:
    """Feed it every closed 1m bar; it returns the cancel decisions the engine would have
    made. The caller (route_b armed path) executes + journals them — this class decides,
    it never touches a broker."""
    #: REBUILT CANON DEFAULT: None = NO distance cancel. The engine's 22pt t_cancel measured
    #: INVERTED on the rebuilt population — it kept -0.180R of trades and killed +0.015R — so
    #: the canon replaced it with plain session-window expiry (ANGUS 2026-07-30). Set a float
    #: ONLY to reproduce the old book; arming with one set trades a book nobody measured.
    t_cancel: float | None = None
    win_start: dtime | None = None
    win_end: dtime | None = None
    eod_flatten: dtime | None = None
    _orders: dict[str, WorkingOrder] = field(default_factory=dict, init=False)

    def __post_init__(self):
        if None in (self.win_start, self.win_end, self.eod_flatten):
            from src.backtest.engine import load_backtest_config
            cfg = load_backtest_config()
            self.win_start = cfg.win_start if self.win_start is None else self.win_start
            self.win_end = cfg.win_end if self.win_end is None else self.win_end
            self.eod_flatten = (cfg.eod_flatten if self.eod_flatten is None
                                else self.eod_flatten)

    # ---- lifecycle ----------------------------------------------------------
    def register(self, ref: str, side: str, limit: float, *,
                 win_end: dtime | None = None, levels: list | None = None,
                 close: float | None = None) -> None:
        """Track a LIMIT entry now resting at the broker. Market entries never rest and must
        not be registered.

        `win_end` is this order's OWN session end (pre 09:30 / gold 10:30). `levels` is the
        trigger's level stack [(name, price, type)]; with `close` (the trigger bar's close)
        it is filtered to the away side, exactly as L1 does, and the structural event is then
        tracked bar by bar for the elite tier."""
        sign = 1 if side == "B" else -1
        away = []
        if levels and close is not None:
            away = [(n, float(p), ty) for n, p, ty in levels
                    if sign * (float(p) - float(close)) >= 0]
        self._orders[ref] = WorkingOrder(ref=ref, side=side, limit=float(limit),
                                         win_end=win_end, levels=away,
                                         touched=[False] * len(away))

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
    def _in_window(self, tod: dtime, win_end: dtime | None = None) -> bool:
        end = win_end or self.win_end
        if self.win_start <= end:
            return self.win_start <= tod < end
        return tod >= self.win_start or tod < end              # overnight wrap

    def struct_event(self, ref: str) -> str:
        """The structural observation for a resting/just-filled order: '' | 'broke' |
        'rejected'. Feeds NYScorerV2's elite tier; absent evidence never escalates size."""
        o = self._orders.get(ref)
        return o.struct_event if o is not None else ""

    def _track_struct(self, o: WorkingOrder, high: float, low: float) -> None:
        """Mirror of scripts/build_l1_fills.py::walk_one's structural block, one bar at a
        time. First event wins and is final; evaluated BEFORE the fill check on the same
        bar, exactly as the batch walk orders it."""
        if o.struct_event or not o.levels:
            return
        s = 1 if o.side == "B" else -1
        for j, (n, p, _ty) in enumerate(o.levels):
            if not o.touched[j] and low <= p <= high:
                o.touched[j] = True
            if o.touched[j]:
                beyond = (high - p) if s == 1 else (p - low)
                back = (p - low) if s == 1 else (high - p)
                if beyond >= STRUCT_ACCEPT:
                    o.struct_event, o.struct_level = "broke", n
                elif back >= STRUCT_REJECT:
                    o.struct_event, o.struct_level = "rejected", n
                if o.struct_event:
                    return

    def _past_eod(self, tod: dtime) -> bool:
        return self.eod_flatten <= tod < _SESSION_CLOSE

    def on_bar(self, ts, high: float, low: float) -> list[dict]:
        """Evaluate every watched order against one CLOSED bar. Returns cancel decisions
        [{ref, reason, detail, raced_fill}]; decided orders are dropped from the watch (the
        caller executes the broker cancel and journals). A `filled` order is skipped — but
        if its fill landed on a bar that ALSO satisfies the cancel condition, that is the
        engine-vs-live race (engine cancels, exchange filled first): reported with
        raced_fill=True so it reaches the journal as a divergence, never silently."""
        ts = pd.Timestamp(ts)
        # the engine's windows are NY WALL-CLOCK; live bars arrive UTC-stamped (.scid feed).
        tod = (ts.tz_convert(NY) if ts.tzinfo is not None else ts).time()
        out: list[dict] = []
        for ref, o in list(self._orders.items()):
            self._track_struct(o, high, low)
            sign = 1 if o.side == "B" else -1
            ran = False if self.t_cancel is None else (
                (high >= o.limit + self.t_cancel) if sign == 1
                else (low <= o.limit - self.t_cancel))
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
            elif not self._in_window(tod, o.win_end):
                decision = {"ref": ref, "reason": "cancelled_window_end",
                            "detail": f"unfilled at {o.win_end or self.win_end}",
                            "raced_fill": False}
            elif ran:
                decision = {"ref": ref, "reason": "cancelled_tcancel",
                            "detail": f"price ran {self.t_cancel} pts beyond limit unfilled",
                            "raced_fill": False}
            else:
                continue
            self._orders.pop(ref, None)
            out.append(decision)
        return out
