"""Paper broker — the simulated account (Phase 4 Stage 3).

Consumes the Vault's TradeEvents (completed champion trades) and keeps the paper account:
an append-only trade ledger, running totals, and per-day rollups — points and dollars
kept STRICTLY separate (the units rule). No real orders, no broker API; fill quality is
the engine's own model (the same one the backtest uses), which is exactly what makes
paper P&L comparable to the backtest 1:1.

It is a Vault sink:  vault.add_sink(broker.on_trade)

Persistence: every trade appends to a CSV ledger so a crash/restart loses nothing and
each paper day can be reconciled row-for-row against the batch backtest (Stage 7/8).
`reconcile()` does that diff mechanically.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from src.live.vault import TradeEvent

LEDGER_COLS = ["trade_date", "book", "pattern", "direction", "trigger_ts", "fill_ts",
               "entry", "stop_initial", "target_level", "exit_ts", "exit_price",
               "exit_reason", "points", "dollars", "r_multiple", "size"]


@dataclass
class DaySummary:
    date: str
    trades: int = 0
    points: float = 0.0
    dollars: float = 0.0
    wins: int = 0
    losses: int = 0


@dataclass
class PaperBroker:
    ledger_path: Path | None = None          # e.g. Path("output/live/paper_ledger.csv")
    starting_equity: float = 0.0             # dollars; paper account baseline
    _trades: list[TradeEvent] = field(default_factory=list)
    _seen: set = field(default_factory=set)

    # ---- sink -----------------------------------------------------------------
    def on_trade(self, ev: TradeEvent) -> None:
        key = (ev.trade_date, ev.fill_ts)
        if key in self._seen:                # replays/restarts must not double-book
            return
        self._seen.add(key)
        self._trades.append(ev)
        if self.ledger_path is not None:
            self._append_csv(ev)

    # ---- account state --------------------------------------------------------
    @property
    def trades(self) -> list[TradeEvent]:
        return list(self._trades)

    def equity(self) -> float:
        """Dollars: starting equity + realized P&L (paper account value)."""
        return self.starting_equity + sum(t.dollars for t in self._trades)

    def total_points(self) -> float:
        return round(sum(t.points for t in self._trades), 2)

    def total_dollars(self) -> float:
        return round(sum(t.dollars for t in self._trades), 2)

    def day_summary(self, date: str) -> DaySummary:
        s = DaySummary(date=date)
        for t in self._trades:
            if t.trade_date != date:
                continue
            s.trades += 1
            s.points = round(s.points + t.points, 2)
            s.dollars = round(s.dollars + t.dollars, 2)
            if t.dollars > 0:
                s.wins += 1
            elif t.dollars < 0:
                s.losses += 1
        return s

    def daily(self) -> list[DaySummary]:
        return [self.day_summary(d) for d in
                sorted({t.trade_date for t in self._trades})]

    # ---- persistence / recovery ----------------------------------------------
    def _append_csv(self, ev: TradeEvent) -> None:
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        row = pd.DataFrame([{c: getattr(ev, c) for c in LEDGER_COLS}])
        row.to_csv(self.ledger_path, mode="a", index=False,
                   header=not self.ledger_path.exists())

    @classmethod
    def restore(cls, ledger_path: Path, starting_equity: float = 0.0) -> "PaperBroker":
        """Rebuild the account from the ledger after a restart — every persisted field
        comes back verbatim (the ledger carries the full trade, nothing is fabricated)."""
        broker = cls(ledger_path=ledger_path, starting_equity=starting_equity)
        if ledger_path.exists():
            for r in pd.read_csv(ledger_path).to_dict("records"):
                tl = r.get("target_level")
                ev = TradeEvent(
                    trade_date=str(r["trade_date"]), trigger_ts=str(r["trigger_ts"]),
                    direction=r["direction"], pattern=str(r["pattern"]),
                    fill_ts=str(r["fill_ts"]), entry=float(r["entry"]),
                    stop_initial=float(r["stop_initial"]),
                    target_level=None if pd.isna(tl) else float(tl),
                    exit_ts=str(r["exit_ts"]),
                    exit_price=float(r["exit_price"]), exit_reason=str(r["exit_reason"]),
                    points=float(r["points"]), dollars=float(r["dollars"]),
                    r_multiple=float(r["r_multiple"]), size=float(r["size"]),
                    book=str(r["book"]))
                k = (ev.trade_date, ev.fill_ts)
                if k not in broker._seen:
                    broker._seen.add(k)
                    broker._trades.append(ev)
        return broker

    # ---- reconciliation (Stage 7/8) ------------------------------------------
    def reconcile(self, expected: list[tuple]) -> dict:
        """Diff the ledger against an expected trade list of
        (trade_date, fill_ts, round(dollars)) tuples (e.g. from the batch backtest).
        Returns {'match': bool, 'missing': [...], 'unexpected': [...]}."""
        have = {(t.trade_date, t.fill_ts, round(t.dollars)) for t in self._trades}
        want = set(expected)
        return {"match": have == want,
                "missing": sorted(want - have),
                "unexpected": sorted(have - want)}
