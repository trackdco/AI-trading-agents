"""Route-B live loop — SierraFileFeed → the champion paper stack + shadow canon/spine.

This is the real body of `paper_run.stream_live`: it drives the paper desk off the files
Sierra writes to disk (Route B — Sierra won't serve data over DTC under the non-pro licence).
A SINGLE poll of `SierraFileFeed` fans each closed minute out to two consumers:

  1. champion path  — the closed bar → LiveRunner.on_bar → the validated Vault/champion sim,
                      which journals completed trades (output/live/journal.jsonl), alerts, and
                      the paper ledger. Unchanged; it just gets live Sierra bars now.
  2. canon path     — the same bar + footprint → CanonIngestor (on_bar/on_minute_tape) and
                      depth events → on_depth, so live canon features/book are maintained.

Per completed champion trade, a SHADOW spine step emits the promotion-gate evidence the
journal alone could not (docs/PROMOTION-GATE.md B/C): per-trade sizing (sizing.jsonl), the
spine's per-guard evaluation + decision (spine.jsonl via SpineJournalSink), and every
rejection normalized into one ledger (rejects.jsonl via RejectLedger).

NOTHING TOUCHES A BROKER, ARMING STAYS GATED. The spine runs DISARMED — `place()` returns a
`shadow` decision before any `submit_bracket`, and the injected broker raises if called at all,
so a coding error can never route an order. The champion uses the PaperBroker. There is no DTC
order path here.

Robustness (feed_guard): dedup / strict ordering / gap record / stall halt. Warm start preloads
recent history so day-one levels are right. The CommandListener (/status, /kill) is polled
between reads. Contract rollover + the per-day .depth swap are handled via RollWatcher +
resolve_*_path (src/canon/sierra_symbol): the .scid is per-contract (swaps only at a roll), the
.depth is per-day (swaps every session).
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from src.canon.book import DepthBook
from src.canon.feed_guard import FeedGuard, warm_start
from src.canon.gate_evidence import RejectLedger, normalize_spine_reject
from src.canon.infra import SpineJournalSink
from src.canon.ingestor import CanonIngestor
from src.canon.sierra_files import SierraFileFeed
from src.canon.sierra_symbol import (
    RollWatcher,
    format_roll_alert,
    resolve_depth_path,
    resolve_scid_path,
)
from src.canon.spine import (
    AccountState,
    FeedHealth,
    OrderIntent,
    SpineConfig,
    SpineExecutor,
)
from src.live.feed import BAR_COLS, Bar

# frozen dollar-risk sizer (the parity anchor — floor schedule; the DD overlay is applied
# identically by baseline and agents from the same account feed, so floor is the check anchor).
from scripts.baseline_dollar_risk import dollar_risk_micros

NY = "America/New_York"


# --------------------------------------------------------------------------- no-broker guard
class _NoBroker:
    """Spine Broker that raises on ANY call. In shadow the spine never reaches it; wiring it
    proves — structurally — that this loop cannot route an order."""
    def _forbid(self, *_a, **_k):
        raise AssertionError("Route-B live loop is disarmed — no broker call is permitted")
    submit_bracket = order_status = position = flatten = cancel_all = _forbid


# --------------------------------------------------------------------------- jsonl sink
class JsonlSink:
    """Append-only JSONL sink, fail-soft (a write error never raises into the loop)."""
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.failures = 0

    def __call__(self, row: dict) -> None:
        import json
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a") as f:
                f.write(json.dumps(row) + "\n")
        except Exception:  # noqa: BLE001
            self.failures += 1


# --------------------------------------------------------------------------- shadow spine
@dataclass
class ShadowSpineInstrument:
    """Turns each completed champion trade into promotion-gate evidence, DISARMED.

    Emits, per trade:
      * sizing.jsonl  — {conviction, stop_pts, micros, available_dd, ...} for check_sizing (B5)
      * spine.jsonl   — the all-guards report (guard_report) + the shadow decision (C5, B4)
      * rejects.jsonl — every reject/halt decision, normalized into the unified ledger (B3)
    """
    spine: SpineExecutor
    sizing_sink: Callable[[dict], None]
    rejects: RejectLedger
    account: str = "PAPER"
    guard_report_sink: Callable[[dict], None] | None = None

    def observe(self, tr, acct: AccountState, feed: FeedHealth, now_epoch: float) -> dict:
        conv = float(getattr(tr, "size", 1.0))            # champion conviction (§9 size)
        entry = float(tr.entry)
        stop = float(tr.stop_initial)
        stop_pts = abs(entry - stop)
        micros = dollar_risk_micros(conv, stop_pts) if stop_pts > 0 else 0
        available_dd = acct.equity - acct.trailing_floor
        setup_id = f"{tr.trade_date}:{tr.fill_ts}"

        self.sizing_sink({"trade_date": str(tr.trade_date), "fill_ts": str(tr.fill_ts),
                          "direction": tr.direction, "conviction": conv, "stop_pts": stop_pts,
                          "micros": int(micros), "available_dd": None,  # floor schedule = anchor
                          "available_dd_live": round(available_dd, 2)})

        intent = OrderIntent(
            side="B" if tr.direction == "long" else "S", order_type="limit",
            entry_ref=entry, stop=stop, target=(None if tr.target_level is None
                                                else float(tr.target_level)),
            size=max(1, int(micros)), setup_id=setup_id, account=self.account)

        # all-guards evidence (fired/not-fired), then the shadow decision (spine journal
        # auto-emits it). guard_report/check/place(disarmed) never touch the broker.
        rep = self.spine.guard_report(intent, acct, feed, now_epoch)
        if self.guard_report_sink is not None:
            self.guard_report_sink({"event": "guard_report", "setup": setup_id, **rep})
        decision = self.spine.place(intent, acct, feed, now_epoch)   # -> shadow (disarmed)
        if decision.action in ("reject", "halt", "flatten"):
            self.rejects.record(normalize_spine_reject(
                {"action": decision.action, "rule": decision.rule,
                 "detail": decision.detail, "setup": setup_id}),
                ts=str(tr.fill_ts))
        return {"sizing_micros": int(micros), "decision": decision.rule, "guards": rep}


# --------------------------------------------------------------------------- default providers
def default_account_fn(runner, trailing_floor: float) -> Callable[[pd.Timestamp], AccountState]:
    """AccountState from the paper broker's live equity. trailing_floor is the EOD line the
    50k tier fixes intraday (SAFETY-SPINE); available_dd = equity − floor."""
    def acct(_now) -> AccountState:
        eq = float(runner.broker.equity())
        return AccountState(equity=eq, trailing_floor=trailing_floor,
                            day_pnl=0.0, open_positions=0)
    return acct


def default_feed_fn(ingestor: CanonIngestor, get_last_bar_ts,
                    spread_baseline_pts: float = 1.0) -> Callable[[pd.Timestamp], FeedHealth]:
    """FeedHealth derived from the live book + last-bar age. Approximate (shadow), but real:
    feed_stale fires on a late bar, book_crossed on a crossed book, spread from the live book."""
    def feed(now) -> FeedHealth:
        bb, ba = ingestor.book.best_bid(), ingestor.book.best_ask()
        crossed = bb is not None and ba is not None and bb >= ba
        spread_rel = (((ba - bb) / spread_baseline_pts) if (bb is not None and ba is not None
                      and not crossed and spread_baseline_pts > 0) else 1.0)
        last = get_last_bar_ts()
        age_ms = 0.0 if last is None else max(0.0, (pd.Timestamp(now) - last).total_seconds() * 1000)
        return FeedHealth(last_tick_age_ms=age_ms, crossed_or_locked=crossed,
                          context_complete=True, spread_rel=spread_rel)
    return feed


# --------------------------------------------------------------------------- the loop
@dataclass
class RouteBLive:
    runner: object                                   # LiveRunner (champion paper stack)
    feed: SierraFileFeed
    data_dir: str | Path
    ingestor: CanonIngestor = None                   # canon features (built if None)
    guard: FeedGuard = None
    watcher: RollWatcher = None
    instrument: ShadowSpineInstrument | None = None
    listener: object | None = None                   # Telegram CommandListener
    alerts: object | None = None                     # LaunchAlerts / TelegramAlerts (.say)
    acct_fn: Callable[[pd.Timestamp], AccountState] | None = None
    feed_fn: Callable[[pd.Timestamp], FeedHealth] | None = None
    clock: Callable[[], pd.Timestamp] | None = None
    root: str = "NQ"
    suffix: str = "-CME"
    _cur_depth_day: object = field(default=None, init=False)
    _last_bar_ts: pd.Timestamp | None = field(default=None, init=False)

    def __post_init__(self):
        if self.ingestor is None:
            self.ingestor = CanonIngestor(book=DepthBook())
        if self.guard is None:
            self.guard = FeedGuard()
        if self.watcher is None:
            self.watcher = RollWatcher(root=self.root)
        if self.clock is None:
            self.clock = lambda: pd.Timestamp.now(tz="UTC")
        if self.acct_fn is None:
            self.acct_fn = default_account_fn(self.runner, trailing_floor=0.0)
        if self.feed_fn is None:
            self.feed_fn = default_feed_fn(self.ingestor, lambda: self._last_bar_ts)

    # ---- warm start -------------------------------------------------------------------
    def warm(self, bars_df: pd.DataFrame, footprint_df: pd.DataFrame | None = None) -> None:
        """Preload recent history into BOTH stacks (champion Vault buffer + canon ingestor)
        without trading it, so day-one levels/tape are correct (the live prime()). Footprint is
        optional: with it, tape/CVD is warmed too; without, bars-only (a thinner but valid warm)."""
        if hasattr(self.runner, "prime"):
            self.runner.prime(bars_df[list(BAR_COLS)])
        if footprint_df is not None and not footprint_df.empty:
            warm_start(self.ingestor, bars_df, footprint_df)
        else:
            for r in bars_df[list(BAR_COLS)].itertuples(index=False):
                self.ingestor.on_bar({c: getattr(r, c) for c in BAR_COLS})

    # ---- per-poll dispatch ------------------------------------------------------------
    def dispatch(self, events: list[dict], now: pd.Timestamp) -> list:
        completed: list = []
        for e in events:
            if e["kind"] == "minute":
                for gbar in self.guard.accept(e["bar"]):     # dedup / order / gap
                    self.ingestor.on_bar(gbar)
                    t = e["tape"]
                    self.ingestor.on_minute_tape(e["ts"], t["delta"], t["vol"], t["vwp"])
                    self._last_bar_ts = pd.Timestamp(gbar["ts_event"])
                    completed += self.runner.on_bar(Bar.from_row(gbar))
            else:                                            # depth
                self.ingestor.on_depth(e["event"])
        if completed and self.instrument is not None:
            now_epoch = pd.Timestamp(now).timestamp()
            acct, feed = self.acct_fn(now), self.feed_fn(now)
            for tr in completed:
                self.instrument.observe(tr, acct, feed, now_epoch)
        return completed

    # ---- roll / per-day depth swap ----------------------------------------------------
    def _maybe_retarget(self, now: pd.Timestamp) -> None:
        day = pd.Timestamp(now).tz_convert(NY).date()
        if day == self._cur_depth_day:
            return
        self._cur_depth_day = day
        # .depth is per-day → always re-point at the new day's file.
        self.feed.retarget_depth(resolve_depth_path(self.data_dir, now, day=str(day),
                                                    root=self.root, suffix=self.suffix))
        # .scid is per-contract → re-point (and reset the aggregator) only on a real roll.
        ev = self.watcher.check(now)
        if ev is not None:
            self.feed.retarget_scid(
                resolve_scid_path(self.data_dir, now, root=self.root, suffix=self.suffix),
                depth_path=resolve_depth_path(self.data_dir, now, day=str(day),
                                              root=self.root, suffix=self.suffix))
            if self.alerts is not None:
                self.alerts.say(format_roll_alert(ev))

    # ---- one poll ---------------------------------------------------------------------
    def poll_once(self, now: pd.Timestamp | None = None) -> bool:
        """One live-tail poll. Returns True if the feed is STALLED (caller should halt)."""
        now = now if now is not None else self.clock()
        self._maybe_retarget(now)
        self.dispatch(self.feed.poll_events(), now)
        if self.listener is not None:
            self.listener.poll_once(timeout=0)
        return self.guard.check_stale(now)

    # ---- serve ------------------------------------------------------------------------
    def serve(self, sleep_fn: Callable[[float], None], poll_interval_s: float = 1.0,
              max_polls: int | None = None, stop_fn: Callable[[], bool] | None = None) -> None:
        """Live loop: poll → dispatch → command-poll → stall-check, on a fixed cadence. A
        stalled feed (feed_guard) ends the loop fail-closed; `stop_fn` (SIGINT/SIGTERM) ends it
        cleanly. `sleep_fn`/`max_polls`/`stop_fn` are injectable so tests never block on a clock."""
        if self.alerts is not None:
            self.alerts.say(f"▶️ Route-B live tail up — feed={self.feed.scid_path}")
        n = 0
        while max_polls is None or n < max_polls:
            if stop_fn is not None and stop_fn():
                break
            stalled = self.poll_once()
            n += 1
            if stalled:
                if self.alerts is not None:
                    self.alerts.say("⛔ Route-B feed STALLED — halting the live tail.")
                break
            sleep_fn(poll_interval_s)
        if hasattr(self.runner, "finalize"):
            self.runner.finalize()


# --------------------------------------------------------------------------- builder
def build_shadow_instrument(out_dir: str | Path, account: str = "PAPER",
                            cfg: SpineConfig | None = None) -> ShadowSpineInstrument:
    """Assemble the shadow spine instrument with all three evidence sinks under out_dir."""
    out = Path(out_dir)
    spine_sink = SpineJournalSink(out / "spine.jsonl")
    spine = SpineExecutor(cfg or SpineConfig(), _NoBroker(), journal=spine_sink)
    return ShadowSpineInstrument(
        spine=spine, sizing_sink=JsonlSink(out / "sizing.jsonl"),
        rejects=RejectLedger(path=out / "rejects.jsonl"), account=account,
        guard_report_sink=spine_sink)
