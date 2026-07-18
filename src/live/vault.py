"""The Vault — the live decision loop (Phase 4 Stage 2).

The Vault is the ONLY thing that turns streaming bars into trade decisions, applies the
risk gate, and drives the outputs (paper broker / Telegram / journal). It reuses the
champion's EXACT decision code by driving `simulate()` incrementally instead of
re-implementing it: on each closed bar it re-runs the champion over the session-so-far and
emits any trade that has newly completed. Because it literally calls `simulate()`, live is
identical to the backtest by construction — Stage 7's parity check confirms the streaming
diff surfaces every trade exactly once.

`simulate()` runs ~0.7 s over a session, so re-running per closed bar sits inside the live
1-minute budget with room to spare. Trigger detection is kept OUT of this hot loop (it is
slow on large windows); triggers are supplied to the Vault (pre-detected for replay/paper,
or fed incrementally by a live detector later).

The `day_gate` argument is the swap seam: None = pure champion (byte-identical); Angus's
refined strategy / the desk agent plugs in here later with no other change to the Vault.

    vault = Vault(cfg, triggers=day_triggers, book="E4")
    vault.add_sink(paper_broker.on_trade).add_sink(telegram.on_trade)
    for bar in ReplayFeed(...).stream():
        vault.on_bar(bar)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time as dtime
from typing import Callable

import pandas as pd

from src.backtest.engine import _session_date, simulate
from src.live.feed import BAR_COLS, Bar

_SESSION_BOUNDARY = dtime(18, 0)


@dataclass(frozen=True)
class TradeEvent:
    """One completed champion trade, surfaced live the bar it closes. Points = NQ price
    movement; dollars = P&L — kept distinct (the units rule)."""
    trade_date: str
    trigger_ts: str
    direction: str
    pattern: str
    fill_ts: str
    entry: float
    stop_initial: float
    target_level: float | None
    exit_ts: str
    exit_price: float
    exit_reason: str
    points: float
    dollars: float
    r_multiple: float
    size: float
    book: str

    @classmethod
    def from_record(cls, tr, book: str) -> "TradeEvent":
        return cls(
            trade_date=str(tr.trade_date), trigger_ts=str(tr.trigger_ts),
            direction=tr.direction, pattern=tr.pattern, fill_ts=str(tr.fill_ts),
            entry=float(tr.entry), stop_initial=float(tr.stop_initial),
            target_level=None if tr.target_level is None else float(tr.target_level),
            exit_ts=str(tr.exit_ts), exit_price=float(tr.exit_price),
            exit_reason=tr.exit_reason, points=float(tr.points), dollars=float(tr.dollars),
            r_multiple=float(tr.r_multiple), size=float(tr.size), book=book)


class Vault:
    def __init__(self, cfg, triggers=(), day_gate: Callable[[str], dict | None] | None = None,
                 book: str = "champion", warmup_sessions: int = 2,
                 sim_fn=simulate):
        self.cfg = cfg
        self._triggers = sorted(triggers, key=lambda t: pd.Timestamp(t.ts))
        self.day_gate = day_gate                 # the swap seam (None = pure champion)
        self.book = book
        self.warmup_sessions = warmup_sessions
        self._sim = sim_fn
        self._bars: list[Bar] = []
        self._emitted: set[tuple] = set()        # (trade_date, fill_ts) — emit each trade once
        self._sinks: list[Callable[[TradeEvent], None]] = []

    # ---- wiring
    def add_sink(self, fn: Callable[[TradeEvent], None]) -> "Vault":
        self._sinks.append(fn)
        return self

    def add_triggers(self, triggers) -> None:
        """Feed newly-detected triggers (live path). Kept sorted; causal filtering happens
        at decision time, so future-dated triggers can be added safely."""
        self._triggers = sorted([*self._triggers, *triggers], key=lambda t: pd.Timestamp(t.ts))

    # ---- the loop
    def on_bar(self, bar: Bar) -> list[TradeEvent]:
        """Ingest one closed bar; return any trades that newly completed on it."""
        self._bars.append(bar)
        self._trim()
        cutoff = pd.Timestamp(bar.ts_event)
        trigs = [t for t in self._triggers if pd.Timestamp(t.ts) <= cutoff]
        if not trigs:
            return []                            # no causal trigger yet → no trade possible
        trades, _, _ = self._sim(self._df(), trigs, self.cfg, day_gate=self.day_gate)
        fresh = []
        for tr in trades:
            key = (str(tr.trade_date), str(tr.fill_ts))
            if key not in self._emitted:
                self._emitted.add(key)
                ev = TradeEvent.from_record(tr, self.book)
                fresh.append(ev)
                for s in self._sinks:
                    s(ev)
        return fresh

    # ---- internals
    def _df(self) -> pd.DataFrame:
        return pd.DataFrame([{c: getattr(b, c) for c in BAR_COLS} for b in self._bars])

    def _trim(self) -> None:
        """Bound the buffer to the last `warmup_sessions` session-days so each re-sim stays
        cheap. Older sessions' trades are already emitted; the warmup tail only feeds
        indicators (it is pre-window, so it produces no new trades)."""
        if len(self._bars) < 2:
            return
        ts = pd.Series([b.ts_event for b in self._bars])
        sd = _session_date(ts, _SESSION_BOUNDARY)
        keep_days = sorted(sd.unique())[-(self.warmup_sessions + 1):]
        if len(keep_days) <= self.warmup_sessions + 1 and len(sd.unique()) <= self.warmup_sessions + 1:
            return
        mask = sd.isin(keep_days).to_numpy()
        self._bars = [b for b, m in zip(self._bars, mask) if m]
