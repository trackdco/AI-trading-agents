"""The Vault — the live decision loop (Phase 4 Stage 2, hardened per the Stage-2 review).

The Vault turns streaming closed bars into champion trade decisions by driving the REAL
`simulate()` incrementally — never a re-implementation — so live is identical to the
backtest by construction. Design points, each forced by a review finding:

* SESSION POLICY (review #1): the champion is a daily BLEND, not one book. At each
  session roll the policy picks the day's (book, cfg, trigger filter) — see
  src/live/champion.champion_policy. A static cfg (no policy) is still supported for
  single-book runs and tests.
* SESSION-SCOPED TRIGGERS (review #3): each re-sim sees ONLY the current session's
  triggers. Warmup bars from prior sessions feed indicators/levels but can never mint
  trades, so a config change at a session roll cannot retroactively "discover" phantom
  trades in already-emitted days.
* WARMUP = 10 SESSIONS (review #2): the target menu uses prior-WEEK high/low
  (src/engine/snapshot.py), so the buffer must hold ~2 trading weeks or re-sims would
  compute different targets than the batch backtest. 10 sessions + the live one covers it.
* SINK ISOLATION (review #4): a crashing sink (e.g. Telegram hiccup) must never kill the
  trading loop — sink errors are caught and reported via on_sink_error.
* TRIGGER DEDUP (review #5): re-delivered triggers (live detector overlap/restart) are
  dropped by identity key.

Emission semantics: a TradeEvent is emitted once, on the bar its trade COMPLETES (entry
and exit together). Entry-time visibility for alerts is a known limitation deferred to
Stage 5 (needs an engine kwarg to expose the open position; flagged in the build plan).

`day_gate` is the strategy swap seam: None = pure champion; Angus's refined layer plugs
in with no other Vault change.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import time as dtime
from typing import Callable

import pandas as pd

from src.backtest.engine import (
    _session_date,
    default_target_resolver,
    load_news_calendar,
    simulate,
)
from src.live.feed import BAR_COLS, Bar

_SESSION_BOUNDARY = dtime(18, 0)
DEFAULT_WARMUP_SESSIONS = 10     # >= 2 trading weeks: prior-week levels stay correct
SIM_PAD_SESSIONS = 0             # fill-loop frame: the current session (18:00 -> now) —
                                 # every champion trade sits >= 14h after session open, so
                                 # intra-session structures (V8 5m swings) are covered;
                                 # multi-day levels come from the full-buffer resolver


def _sess_of(ts) -> str:
    return str(_session_date(pd.Series([pd.Timestamp(ts)]), _SESSION_BOUNDARY).iloc[0])


def _trig_key(t) -> tuple:
    return (str(t.ts), getattr(t, "tf", None), getattr(t, "direction", None),
            getattr(t, "pattern", None))


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
    def __init__(self, cfg=None, triggers=(), day_gate: Callable[[str], dict | None] | None = None,
                 book: str = "champion", warmup_sessions: int = DEFAULT_WARMUP_SESSIONS,
                 sim_fn=simulate,
                 session_policy: Callable[[str], tuple | None] | None = None,
                 on_sink_error: Callable[[Exception, TradeEvent], None] | None = None):
        """session_policy: date 'YYYY-MM-DD' -> (book_name, cfg, trigger_predicate) or
        None to sit the session out entirely. When omitted, `cfg`/`book` apply to every
        session (single-book mode)."""
        if cfg is None and session_policy is None:
            raise ValueError("Vault needs a cfg or a session_policy")
        self.cfg = cfg
        self.book = book
        self.day_gate = day_gate                       # the strategy swap seam
        self.warmup_sessions = warmup_sessions
        self._sim = sim_fn
        self._policy = session_policy
        self._on_sink_error = on_sink_error or self._default_sink_error
        self._triggers: dict[tuple, object] = {}       # identity key -> trigger (deduped)
        for t in triggers:
            self._triggers[_trig_key(t)] = t
        self._bars: list[Bar] = []
        self._emitted: set[tuple] = set()              # (trade_date, fill_ts): emit once
        self._sinks: list[Callable[[TradeEvent], None]] = []
        self._cur_sess: str | None = None
        self._sess_active = True
        self._sess_triggers: list = []
        self._sess_done = False                        # all causal triggers disposed, window over
        try:
            self._calendar = load_news_calendar()
        except Exception:
            self._calendar = None

    # ---- wiring -------------------------------------------------------------
    def add_sink(self, fn: Callable[[TradeEvent], None]) -> "Vault":
        self._sinks.append(fn)
        return self

    def add_triggers(self, triggers) -> None:
        """Feed newly-detected triggers (live path). Deduped by identity; a re-delivered
        trigger is a no-op. Refreshes the current session's working set."""
        for t in triggers:
            self._triggers[_trig_key(t)] = t
        self._sess_done = False                        # new triggers re-arm the loop
        if self._cur_sess is not None:
            self._load_session_triggers(self._cur_sess)

    # ---- the loop -----------------------------------------------------------
    def on_bar(self, bar: Bar) -> list[TradeEvent]:
        """Ingest one closed bar; return any trades that newly completed on it."""
        sess = _sess_of(bar.ts_event)
        if sess != self._cur_sess:
            self._roll_session(sess)
            self._trim()                               # per ROLL, not per bar (perf)
        self._bars.append(bar)
        if not self._sess_active or self._sess_done:
            return []
        cutoff = pd.Timestamp(bar.ts_event)
        trigs = [t for t in self._sess_triggers if pd.Timestamp(t.ts) <= cutoff]
        if not trigs:
            return []                                  # nothing causal yet this session
        trades, verdicts, _ = self._run_sim(trigs)
        self._update_done(bar, trigs, trades, verdicts)
        fresh: list[TradeEvent] = []
        for tr in trades:
            key = (str(tr.trade_date), str(tr.fill_ts))
            if key in self._emitted:
                continue
            self._emitted.add(key)
            ev = TradeEvent.from_record(tr, self.book)
            fresh.append(ev)
            for s in self._sinks:
                try:
                    s(ev)
                except Exception as e:                 # a sink must never kill the loop
                    self._on_sink_error(e, ev)
        return fresh

    def _run_sim(self, trigs):
        """Run the champion over a SLICED frame (current + SIM_PAD_SESSIONS sessions) for
        speed, while the target resolver sees the FULL warmup buffer so multi-week levels
        (prior-week H/L) match the batch backtest. Falls back to the plain call when cfg
        is not a real engine config (unit-test stubs)."""
        full = self._df()
        if not hasattr(self.cfg, "target_model"):
            return self._sim(full, trigs, self.cfg, day_gate=self.day_gate)
        ts = pd.Series([b.ts_event for b in self._bars])
        sd = _session_date(ts, _SESSION_BOUNDARY)
        keep = set(sorted(sd.unique())[-(SIM_PAD_SESSIONS + 1):])
        sim_df = full[sd.isin(keep).to_numpy()].reset_index(drop=True)
        cal = self._calendar
        resolver = default_target_resolver(
            full, cal if cal is not None else pd.DataFrame(columns=["datetime_ET", "event", "impact"]),
            self.cfg.target_model, self.cfg.rr_floor, self.cfg.front_run,
            walkout=self.cfg.walkout_under_floor, named_high=self.cfg.named_high_impact)
        return self._sim(sim_df, trigs, self.cfg, day_gate=self.day_gate,
                         target_resolver=resolver)

    def _update_done(self, bar: Bar, trigs, trades, verdicts) -> None:
        """Stop re-simming once nothing can change this session: the entry window is over
        AND every causal trigger is TERMINALLY disposed — a completed trade, or a
        vetoed/cancelled/skipped verdict. A "taken" verdict is NOT terminal (the position
        is open; its exit must still be observed), so an open position keeps the loop
        simming until it closes. After eod_flatten the engine has force-flattened
        everything, so the sim that saw a post-flatten bar is always the last one.
        add_triggers / the session roll re-arm the loop."""
        win_end = getattr(self.cfg, "win_end", None)
        if win_end is None:
            return
        tod = bar.ts_event.time()
        if tod < win_end:
            return                                     # entries still possible
        flat = getattr(self.cfg, "eod_flatten", None)
        if flat is not None and flat <= tod < _SESSION_BOUNDARY:
            self._sess_done = True                     # backstop: everything force-flat now
            return
        disposed = {str(t.trigger_ts) for t in trades}
        disposed |= {str(v.ts) for v in verdicts or [] if v.status != "taken"}
        if all(str(t.ts) in disposed for t in trigs):
            self._sess_done = True

    # ---- internals ----------------------------------------------------------
    def _roll_session(self, sess: str) -> None:
        self._cur_sess = sess
        self._sess_done = False
        if self._policy is not None:
            picked = self._policy(sess)
            if picked is None:                         # policy sits this session out
                self._sess_active = False
                self._sess_triggers = []
                return
            self.book, self.cfg, self._sess_pred = picked
        else:
            self._sess_pred = None
        self._sess_active = True
        self._load_session_triggers(sess)

    def _load_session_triggers(self, sess: str) -> None:
        pred = getattr(self, "_sess_pred", None) or (lambda t: True)
        self._sess_triggers = sorted(
            (t for t in self._triggers.values()
             if _sess_of(t.ts) == sess and pred(t)),
            key=lambda t: pd.Timestamp(t.ts))

    def _df(self) -> pd.DataFrame:
        return pd.DataFrame([{c: getattr(b, c) for c in BAR_COLS} for b in self._bars])

    def _trim(self) -> None:
        """Called at each session ROLL (before the new session's first bar lands): keep
        the last `warmup_sessions` prior session-days, so buffer = warmup + the live
        session. The warmup tail feeds indicators and the level menu (incl. prior-WEEK
        levels) only — its sessions' triggers are out of scope, so it can't create trades."""
        if not self._bars:
            return
        ts = pd.Series([b.ts_event for b in self._bars])
        sd = _session_date(ts, _SESSION_BOUNDARY)
        uniq = sorted(sd.unique())
        if len(uniq) <= self.warmup_sessions:
            return
        keep = set(uniq[-self.warmup_sessions:])
        mask = sd.isin(keep).to_numpy()
        self._bars = [b for b, m in zip(self._bars, mask) if m]

    @staticmethod
    def _default_sink_error(e: Exception, ev: TradeEvent) -> None:
        print(f"[vault] sink error on {ev.trade_date} {ev.fill_ts}: "
              f"{type(e).__name__}: {e}", file=sys.stderr)
