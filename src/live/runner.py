"""The live runner (Phase 4 Stage 8) — one process that IS the paper-trading bot.

Assembles every stage into a single loop, feed-agnostic (replay for drills, live for
paper). Per closed 1-minute bar:

    1. append to a bounded bar history (indicators/levels warmup + prior-day overnight)
    2. LiveDetector -> new triggers -> Vault.add_triggers        (Stage 8 detector)
    3. Vault.on_bar -> champion sim under the risk gate, book chosen by the live
       vector policy at the first >=08:00 bar (Stage 8 vector; PENDING before that)
    4. completed trades fan out to: guard (risk accounting) -> broker (paper ledger)
       -> journal (audit) -> Telegram (alert). Session rolls emit a daily summary.

Wiring order matters and is fixed here so callers cannot get it wrong:

    restore broker from ledger  ->  seed guard from restored trades (no re-announce)
    ->  build Vault (vector policy wrapped by journal, risk gate as day_gate)
    ->  sinks: guard.on_trade (first, fresh state) -> broker -> Telegram
    ->  record sink: journal.on_record
    ->  seed_emitted from restored trades (a restart re-fires nothing)

STRATEGY SWAP SEAM (Stage 9): pass `strategy_gate` and it composes UNDER the risk guard
(`guard.wrap(strategy_gate)`) — the champion stays byte-identical when it is None, and
Angus's refined layer plugs in with no other runner change.

The real-time entrypoint (`serve`) additionally polls the Telegram CommandListener
between bars so /status and /kill work while the bot runs; `run_replay` is the same loop
over a historical feed, used by the full-stack drill (scripts/runner_drill.py) that
proves the assembled runner — computing its OWN triggers and book picks — reproduces the
batch backtest.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pandas as pd

from src.live.ambient import vault_ambient
from src.live.detector import LiveDetector
from src.live.feed import BAR_COLS, Bar
from src.live.journal import LiveJournal
from src.live.paper_broker import PaperBroker
from src.live.risk import RiskGuard, RiskLimits, fanout
from src.live.vault import Vault, _sess_of
from src.live.vector import LiveVectorPolicy

DEFAULT_HISTORY_DAYS = 20        # >= the 16-day warmup proven sufficient for the detector
                                 # (scripts/detector_parity.py) plus prior-day overnight


class LiveRunner:
    def __init__(self, *, ledger_path: Path, journal_dir: Path,
                 starting_equity: float = 25_000.0,
                 limits: RiskLimits | None = None,
                 alerts=None, daytypes_csv: Path | None = None,
                 strategy_gate: Callable[[str], dict | None] | None = None,
                 history_days: int = DEFAULT_HISTORY_DAYS,
                 detector: LiveDetector | None = None,
                 sim_fn=None, session_policy=None,
                 ambient: bool = True, spread_guard=None):
        self.alerts = alerts
        self.history_days = history_days
        self.detect_enabled = True                   # off while feeding known-historical
                                                     # warmup bars (they carry no
                                                     # in-scope triggers; skipping the
                                                     # re-detect is a big speedup and
                                                     # changes no trade — see runner_drill)
        self._history: list[dict] = []
        self._frame_cache: pd.DataFrame | None = None
        self._cur_sess: str | None = None

        # --- account: restore, then seed the guard from the restored trades ---------
        ledger_path = Path(ledger_path)
        self.broker = (PaperBroker.restore(ledger_path, starting_equity)
                       if ledger_path.exists()
                       else PaperBroker(ledger_path=ledger_path,
                                        starting_equity=starting_equity))
        self.journal = LiveJournal(journal_dir)
        halt_hook = fanout(*( ([self.alerts.on_halt] if self.alerts else [])
                             + [self.journal.on_halt]))
        self.guard = RiskGuard(limits or RiskLimits(), on_halt=halt_hook)
        self.guard.seed(self.broker.trades)          # restart: remember today's halts

        # --- the live decision loop -------------------------------------------------
        self.detector = detector or LiveDetector()
        # session_policy defaults to the live vector policy; injectable for tests and
        # for a future non-champion book selector.
        self.vector = session_policy or LiveVectorPolicy(
            self._frame, **({"daytypes_csv": daytypes_csv} if daytypes_csv else {}))
        policy = self.journal.wrap_policy(self.vector)
        vkw = {"sim_fn": sim_fn} if sim_fn is not None else {}
        # CANON ruling (24 Jul): journal ambient context on EVERY trade ("journal
        # EVERYTHING"). The order-time spread guard stays OPT-IN (spread_guard=None) — it
        # drops orders, so arming it by default would diverge live from the validated
        # backtest; an operator enables it deliberately.
        self.vault = Vault(session_policy=policy,
                           day_gate=self.guard.wrap(strategy_gate),
                           ambient_fn=(vault_ambient if ambient else None),
                           spread_guard=spread_guard,
                           on_guard_trip=self.journal.on_guard_trip, **vkw)
        self.vault.add_sink(self.guard.on_trade)     # BEFORE broker: fresh gate state
        self.vault.add_sink(self.broker.on_trade)
        if self.alerts is not None:
            self.vault.add_sink(self.alerts.on_trade)
        self.vault.add_record_sink(self.journal.on_record)
        self.vault.seed_emitted(self.broker.trades)  # restart re-fires nothing

    # ---- bar history (shared by detector + vector policy) ----------------------
    def _frame(self) -> pd.DataFrame:
        if self._frame_cache is None:
            self._frame_cache = pd.DataFrame(self._history, columns=list(BAR_COLS))
        return self._frame_cache

    def _trim_history(self, latest: pd.Timestamp) -> None:
        cutoff = latest - pd.Timedelta(days=self.history_days)
        if self._history and self._history[0]["ts_event"] < cutoff:
            self._history = [b for b in self._history if b["ts_event"] >= cutoff]

    # ---- warmup ----------------------------------------------------------------
    def prime(self, bars_df: pd.DataFrame) -> None:
        """Preload prior bars into the history buffer WITHOUT trading them, so day-one
        detection and the book switch have their ~16-day warmup. Required before
        `serve` on a live feed that starts at 'now' (a replay feed supplies its own
        warmup via `warmup_days`). Leaves `_cur_sess` None so the first live bar starts
        a session cleanly — no bogus 0-trade summary for a day we never actually traded."""
        for r in bars_df[list(BAR_COLS)].sort_values("ts_event").itertuples(index=False):
            self._history.append({c: getattr(r, c) for c in BAR_COLS})
        if self._history:
            self._trim_history(self._history[-1]["ts_event"])
        self._frame_cache = None

    # ---- the loop --------------------------------------------------------------
    def on_bar(self, bar: Bar) -> list:
        ts = pd.Timestamp(bar.ts_event)
        sess = _sess_of(ts)
        if self._cur_sess is not None and sess != self._cur_sess:
            self._end_of_session(self._cur_sess)      # summarize the day that just ended
        self._cur_sess = sess

        self._history.append({c: getattr(bar, c) for c in BAR_COLS})
        self._trim_history(ts)
        self._frame_cache = None                      # invalidate: history changed

        if hasattr(self.vector, "note_bar"):           # O(1) readiness hook (perf
            self.vector.note_bar(ts)                   # review): keeps the Vault's
                                                        # PENDING retry loop cheap
        if self.detect_enabled and self.detector.wants(ts):
            new = self.detector.on_bar(self._frame(), bar)
            if new:
                self.vault.add_triggers(new)
        return self.vault.on_bar(bar)

    def _end_of_session(self, date: str) -> None:
        # Always emit — a daily heartbeat, including 0-trade days: silence is ambiguous
        # (crashed vs quietly flat), a "0 trades" line is not. Guard-style noise control
        # applies to REPEATED alerts, not the once-a-day rollup.
        if self.alerts is not None:
            self.alerts.daily_summary(self.broker, date)
        self.journal.note(f"session_end {date} "
                          f"equity={self.broker.equity():.2f}")

    def finalize(self) -> None:
        """Flush the final session's summary (a replay ends without a trailing roll)."""
        if self._cur_sess is not None:
            self._end_of_session(self._cur_sess)
            self._cur_sess = None

    # ---- entrypoints -----------------------------------------------------------
    def run_replay(self, feed) -> None:
        """Drive the whole loop over a (historical) feed to completion. Used by the
        full-stack drill and by an operator replaying a day."""
        if self.alerts is not None:
            self.alerts.say(f"▶️ NQ paper bot up (replay) — equity "
                            f"${self.broker.equity():,.0f}, "
                            f"{len(self.broker.trades)} trades restored")
        for bar in feed.stream():
            self.on_bar(bar)
        self.finalize()

    def serve(self, feed, listener=None, poll_every: int = 1) -> None:
        """Real-time entrypoint: same loop, plus non-blocking Telegram command polls
        between bars so /status and /kill respond while the bot runs. A live feed's
        `stream()` blocks until the next closed bar; `listener` is the Stage-5
        CommandListener (locked to allowed user ids)."""
        if self.alerts is not None:
            self.alerts.say(f"▶️ NQ paper bot LIVE — equity "
                            f"${self.broker.equity():,.0f}, "
                            f"{len(self.broker.trades)} trades restored")
        n = 0
        for bar in feed.stream():
            self.on_bar(bar)
            n += 1
            if listener is not None and n % poll_every == 0:
                listener.poll_once(timeout=0)         # non-blocking: never stalls a bar
        self.finalize()
