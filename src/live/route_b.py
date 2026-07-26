"""Route-B live loop — SierraFileFeed → the AUTHORITATIVE canon lane (shape i) + disarmed spine.

The operational entry point is `scripts/canon_run.py`. It drives the desk off the files Sierra
writes to disk (Route B — Sierra won't serve data over DTC under the non-pro licence). A SINGLE
poll of `SierraFileFeed` fans each closed minute to the CanonIngestor (on_bar/on_minute_tape/
on_depth) so live canon features/book are maintained; each session's canon verdicts (a
`VerdictSource`) drive the verdict journal + the disarmed spine, emitted at their fill time.

The champion (`comparator`, a LiveRunner) is OPTIONAL and NON-AUTHORITATIVE — structurally OUT
of the journal/spine/trade path; if wired (with an isolated journal dir) its trades go only to
the champion-vs-canon divergence canary.

Per canon verdict, a SHADOW spine step emits the promotion-gate evidence: per-trade sizing
(sizing.jsonl), the spine's per-guard evaluation + decision (spine.jsonl via SpineJournalSink),
and every rejection normalized into one ledger (rejects.jsonl via RejectLedger). Roll events go
to decisions.jsonl.

NOTHING TOUCHES A BROKER, ARMING STAYS GATED. The spine runs DISARMED — `place()` returns a
`shadow` decision before any `submit_bracket`, and the injected `_NoBroker` raises if called at
all, so a coding error can never route an order. There is no DTC order path here.

Robustness (feed_guard): dedup / strict ordering / gap record / stall halt. Warm start preloads
recent history so day-one levels are right. The CommandListener (/status, /kill) is polled
between reads. Contract rollover + the per-day .depth swap are handled via RollWatcher +
resolve_*_path (src/canon/sierra_symbol): the .scid is per-contract (swaps only at a roll), the
.depth is per-day (swaps every session).
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import time as dtime
from pathlib import Path

import pandas as pd

from src.canon.book import DepthBook
from src.canon.feed_guard import FeedGuard, warm_start
from src.canon.gate_evidence import RejectLedger, normalize_spine_reject
from src.canon.infra import SpineJournalSink
from src.canon.ingestor import CanonIngestor
from src.canon.sierra_files import SierraFileFeed
from src.canon.sierra_symbol import (
    RollTagger,
    RollWatcher,
    format_roll_alert,
    resolve_depth_path,
    resolve_scid_path,
)
from src.engine.data import _session_date
from src.canon.spine import (
    AccountState,
    FeedHealth,
    OrderIntent,
    SpineConfig,
    SpineExecutor,
)
from src.desk.canon_lane import verdict_record
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
    cancel_order = modify_stop = close_partial = _forbid          # B7/B8 surface: also forbidden


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


# --------------------------------------------------------------------------- roll state
@dataclass
class RollState:
    """Live roll-tag state (the loop-side wrapper around RollTagger). Tracks the active
    front-month contract and the SET of session-dates that saw a roll — the live twin of the
    backtest's roll-day partition (diagnostics.py). Buffers are NOT trimmed at a roll: the
    backtest SPANS the gap on the unspliced continuous series, so live must span too or diverge.
    This state only TAGS (for the journal/gate partition) and lets §E reset the clock."""
    root: str = "NQ"
    tagger: RollTagger = None
    contract: str | None = None
    roll_sessions: set = field(default_factory=set)
    rolls: list = field(default_factory=list)

    def __post_init__(self):
        if self.tagger is None:
            self.tagger = RollTagger(root=self.root)

    def on_bar(self, ts) -> dict:
        """Tag a bar; update state; return {contract, roll, session}. `roll` is True once, on
        the first bar of the new contract (matches engine.data.tag_rolls)."""
        t = self.tagger.tag(ts)
        prev, self.contract = self.contract, t["contract"]
        session = str(_session_date(pd.Series([pd.Timestamp(ts)]), dtime(18, 0)).iloc[0])
        bar_ts = str(pd.Timestamp(ts))
        if t["roll"]:
            self.roll_sessions.add(session)
            self.rolls.append({"session": session, "from": prev, "to": t["contract"],
                               "bar_ts": bar_ts})
        return {**t, "session": session, "from": prev, "bar_ts": bar_ts}

    def context(self, tr) -> dict:
        """Per-trade roll context for the journal ambient (roll = did this trade's session see
        a roll; contract = the front month in force)."""
        return self.context_for_day(str(getattr(tr, "trade_date", "")))

    def context_for_day(self, day: str) -> dict:
        return {"roll": str(day) in self.roll_sessions, "contract": self.contract}


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

    def observe(self, tr, acct: AccountState, feed: FeedHealth, now_epoch: float,
                roll_ctx: dict | None = None) -> dict:
        conv = float(getattr(tr, "size", 1.0))            # champion conviction (§9 size)
        entry = float(tr.entry)
        stop = float(tr.stop_initial)
        stop_pts = abs(entry - stop)
        micros = dollar_risk_micros(conv, stop_pts) if stop_pts > 0 else 0
        available_dd = acct.equity - acct.trailing_floor
        setup_id = f"{tr.trade_date}:{tr.fill_ts}"
        rc = roll_ctx or {}

        self.sizing_sink({"trade_date": str(tr.trade_date), "fill_ts": str(tr.fill_ts),
                          "direction": tr.direction, "conviction": conv, "stop_pts": stop_pts,
                          "micros": int(micros), "available_dd": None,  # floor schedule = anchor
                          "available_dd_live": round(available_dd, 2),
                          "roll": rc.get("roll"), "contract": rc.get("contract")})

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

    def observe_verdict(self, v: dict, acct: AccountState, feed: FeedHealth, now_epoch: float,
                        roll_ctx: dict | None = None) -> dict:
        """The AUTHORITATIVE canon-lane path: drive the disarmed spine from a relayed canon
        verdict. Unlike observe(), micros come from the verdict (the PRODUCTION dollar-risk
        sizer already sized the canon book) — not recomputed. Emits sizing/spine/rejects."""
        from src.desk.canon_lane import verdict_to_intent
        rc = roll_ctx or {}
        stop_pts = abs(float(v["entry"]) - float(v["stop"]))
        micros = int(v.get("micros", 0) or 0)
        setup_id = f"{v.get('day')}:{v.get('fill')}"
        available_dd = acct.equity - acct.trailing_floor
        self.sizing_sink({"trade_date": str(v.get("day")), "fill_ts": str(v.get("fill")),
                          "direction": v.get("direction"),
                          "conviction": float(v.get("conviction", 0) or 0), "stop_pts": stop_pts,
                          "micros": micros, "available_dd": None,   # floor schedule = anchor
                          "available_dd_live": round(available_dd, 2),
                          "roll": rc.get("roll"), "contract": rc.get("contract")})
        intent = verdict_to_intent(v, self.account)
        rep = self.spine.guard_report(intent, acct, feed, now_epoch)
        if self.guard_report_sink is not None:
            self.guard_report_sink({"event": "guard_report", "setup": setup_id, **rep})
        decision = self.spine.place(intent, acct, feed, now_epoch)   # -> shadow (disarmed)
        if decision.action in ("reject", "halt", "flatten"):
            self.rejects.record(normalize_spine_reject(
                {"action": decision.action, "rule": decision.rule,
                 "detail": decision.detail, "setup": setup_id}), ts=str(v.get("fill")))
        return {"sizing_micros": micros, "decision": decision.rule,
                "action": decision.action, "ref": decision.ref, "intent": intent}


# --------------------------------------------------------------------------- default providers
def constant_account_fn(equity: float = 50_000.0,
                        trailing_floor: float = 0.0) -> Callable[[pd.Timestamp], AccountState]:
    """AccountState from a fixed equity — a P1 placeholder. The funded account's real state
    (equity/EOD line) comes from the broker read-back (DTC account probe) once wired; until then
    the disarmed spine evaluates against this constant. available_dd = equity − trailing_floor."""
    def acct(_now) -> AccountState:
        return AccountState(equity=equity, trailing_floor=trailing_floor,
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
    """The AUTHORITATIVE canon-lane live loop (shape i). Canon verdicts (from a VerdictSource)
    drive the verdict journal + the disarmed spine. The champion (`comparator`, a LiveRunner) is
    OPTIONAL and NON-AUTHORITATIVE — it is structurally OUT of the journal/spine/trade path; if
    wired, its trades go only to `comparator_sink` (the champion-vs-canon divergence canary)."""
    feed: SierraFileFeed
    data_dir: str | Path
    verdict_source: object = None                    # VerdictSource (canon lane) — authoritative
    verdict_sink: Callable[[dict], None] | None = None   # verdicts.jsonl (§D shadow evidence)
    decision_sink: Callable[[dict], None] | None = None  # roll / note decisions
    ingestor: CanonIngestor = None                   # canon features (built if None)
    guard: FeedGuard = None
    watcher: RollWatcher = None
    roll_state: RollState = None                      # live roll tag (span-preserving)
    instrument: ShadowSpineInstrument | None = None
    lifecycle: object | None = None                  # TradeLifecycle (watch/fill/exit assembly)
    premarket_guard: object | None = None            # PremarketGuard (corrections 2+3, live)
    comparator: object = None                        # optional champion LiveRunner (diagnostic)
    comparator_sink: Callable[[dict], None] | None = None
    listener: object | None = None                   # Telegram CommandListener
    alerts: object | None = None                     # LaunchAlerts / TelegramAlerts (.say)
    acct_fn: Callable[[pd.Timestamp], AccountState] | None = None
    feed_fn: Callable[[pd.Timestamp], FeedHealth] | None = None
    clock: Callable[[], pd.Timestamp] | None = None
    account_equity: float = 50_000.0
    root: str = "NQ"
    suffix: str = "-CME"
    _cur_depth_day: object = field(default=None, init=False)
    _last_bar_ts: pd.Timestamp | None = field(default=None, init=False)
    _cur_sess: str | None = field(default=None, init=False)
    _pending: list = field(default_factory=list, init=False)   # session verdicts, fill-sorted

    def __post_init__(self):
        if self.ingestor is None:
            self.ingestor = CanonIngestor(book=DepthBook())
        if self.guard is None:
            self.guard = FeedGuard()
        if self.watcher is None:
            self.watcher = RollWatcher(root=self.root)
        if self.roll_state is None:
            self.roll_state = RollState(root=self.root)
        if self.clock is None:
            self.clock = lambda: pd.Timestamp.now(tz="UTC")
        if self.acct_fn is None:
            self.acct_fn = constant_account_fn(self.account_equity)
        if self.feed_fn is None:
            self.feed_fn = default_feed_fn(self.ingestor, lambda: self._last_bar_ts)

    # ---- warm start -------------------------------------------------------------------
    def warm(self, bars_df: pd.DataFrame, footprint_df: pd.DataFrame | None = None) -> None:
        """Preload recent history into the canon ingestor (and the comparator, if wired) without
        trading it, so day-one levels/tape are correct. Footprint optional: with it tape/CVD is
        warmed too; without, bars-only."""
        if self.comparator is not None and hasattr(self.comparator, "prime"):
            self.comparator.prime(bars_df[list(BAR_COLS)])
        if footprint_df is not None and not footprint_df.empty:
            warm_start(self.ingestor, bars_df, footprint_df)
        else:
            for r in bars_df[list(BAR_COLS)].itertuples(index=False):
                self.ingestor.on_bar({c: getattr(r, c) for c in BAR_COLS})

    # ---- per-poll dispatch ------------------------------------------------------------
    def dispatch(self, events: list[dict], now: pd.Timestamp) -> list:
        """Fan bars to the canon ingestor + roll tag; load each session's canon verdicts and
        emit them at their fill time into the verdict journal + disarmed spine. The champion
        comparator (if any) is driven in parallel but only writes the divergence canary."""
        emitted: list = []
        for e in events:
            if e["kind"] == "minute":
                for gbar in self.guard.accept(e["bar"]):     # dedup / order / gap
                    bts = pd.Timestamp(gbar["ts_event"])
                    # roll tag first (buffers are NOT trimmed — the backtest spans the gap).
                    ri = self.roll_state.on_bar(bts)
                    if ri["roll"]:
                        self._on_roll_bar(ri)
                    self.ingestor.on_bar(gbar)
                    t = e["tape"]
                    self.ingestor.on_minute_tape(e["ts"], t["delta"], t["vol"], t["vwp"])
                    self._last_bar_ts = bts
                    if ri["session"] != self._cur_sess:       # session roll -> load verdicts
                        self._cur_sess = ri["session"]
                        self._load_verdicts(ri["session"])
                    emitted += self._emit_due(bts, now)       # verdicts whose fill has passed
                    if self.lifecycle is not None:            # watch/fill/exit, per closed bar
                        self.lifecycle.on_bar(
                            gbar, bars_df=self.ingestor.bars_frame(),
                            tape_df=self.ingestor.tape.frame())
                    self._run_comparator(gbar)                # non-authoritative canary
            else:                                             # depth
                self.ingestor.on_depth(e["event"])
        return emitted

    def _load_verdicts(self, session: str) -> None:
        if self.verdict_source is None:
            self._pending = []
            return
        vs = list(self.verdict_source.session_verdicts(session) or [])
        self._pending = sorted(vs, key=lambda v: pd.Timestamp(v["fill"]))

    def _emit_due(self, bts: pd.Timestamp, now: pd.Timestamp) -> list:
        """Emit every pending verdict whose fill time is at/ before this bar — journal it (§D
        evidence) and drive the disarmed spine. Removes them from the pending queue."""
        out: list = []
        acct = feed = None
        while self._pending and pd.Timestamp(self._pending[0]["fill"]) <= bts:
            v = self._pending.pop(0)
            rc = self.roll_state.context_for_day(str(v.get("day")))
            # corrections 2+3 live (news blackout / dead zone / sentinel fail-closed):
            # a vetoed verdict is journaled as a veto and NEVER reaches the verdict
            # journal, the spine, or the lifecycle — same as batch size->0 (the day's
            # trade slot is not consumed; the shell-out books never saw these vetoes).
            if self.premarket_guard is not None:
                reason = self.premarket_guard.veto(v)
                if reason is not None:
                    if self.decision_sink is not None:
                        self.decision_sink({"type": "verdict_veto", "reason": reason,
                                            "day": v.get("day"), "fill": str(v.get("fill")),
                                            "session": v.get("session")})
                    continue
            if self.verdict_sink is not None:
                self.verdict_sink(verdict_record(v, roll_ctx=rc))
            if self.instrument is not None:
                if acct is None:
                    acct, feed = self.acct_fn(now), self.feed_fn(now)
                res = self.instrument.observe_verdict(v, acct, feed,
                                                      pd.Timestamp(now).timestamp(),
                                                      roll_ctx=rc)
                # hand every placement to the lifecycle: armed -> the broker ref; shadow ->
                # a synthetic ref so the watch's would-be cancels become §D evidence.
                if self.lifecycle is not None and res.get("action") == "place":
                    intent = res["intent"]
                    ref = res.get("ref") or f"shadow:{intent.setup_id}"
                    self.lifecycle.on_placed(ref, side=intent.side,
                                             entry=float(intent.entry_ref),
                                             stop=float(intent.stop),
                                             size=int(intent.size))
            out.append(v)
        return out

    def _run_comparator(self, gbar: dict) -> None:
        """Drive the champion in parallel (if wired) and record its trades to the divergence
        canary ONLY — never the authoritative journal or the spine."""
        if self.comparator is None:
            return
        for tr in self.comparator.on_bar(Bar.from_row(gbar)):
            if self.comparator_sink is not None:
                self.comparator_sink({"lane": "champion", "trade_date": str(tr.trade_date),
                                      "fill_ts": str(tr.fill_ts), "direction": tr.direction,
                                      "entry": float(tr.entry), "dollars": float(tr.dollars)})

    def _on_roll_bar(self, ri: dict) -> None:
        """A roll bar arrived intraday (tag_rolls twin). Journal the roll decision (so the gate
        can partition roll-day verdicts and §E can reset the clock) and alert."""
        if self.decision_sink is not None:
            self.decision_sink({"type": "roll", "date": ri["session"], "from": ri.get("from"),
                                "to": ri["contract"], "bar_ts": ri.get("bar_ts")})
        if self.alerts is not None:
            self.alerts.say(f"🔁 ROLL TAG {ri['session']}: now {ri['contract']} — §E resets "
                            f"the promotion clock for this session (buffers span the gap, "
                            f"matching the backtest).")

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
        if self.comparator is not None and hasattr(self.comparator, "finalize"):
            self.comparator.finalize()


# --------------------------------------------------------------------------- builder
def build_shadow_instrument(out_dir: str | Path, account: str = "FUNDED",
                            cfg: SpineConfig | None = None,
                            kill_file: str | Path | None = None) -> ShadowSpineInstrument:
    """Assemble the shadow spine instrument with all three evidence sinks under out_dir. When
    `kill_file` is given, the spine halts while that file is present (the manual /kill switch —
    it still halts even a DISARMED spine, so the wiring is verified before arming)."""
    out = Path(out_dir)
    spine_sink = SpineJournalSink(out / "spine.jsonl")
    kfp = (lambda: Path(kill_file).exists()) if kill_file is not None else (lambda: False)
    spine = SpineExecutor(cfg or SpineConfig(), _NoBroker(), journal=spine_sink,
                          kill_file_present=kfp)
    return ShadowSpineInstrument(
        spine=spine, sizing_sink=JsonlSink(out / "sizing.jsonl"),
        rejects=RejectLedger(path=out / "rejects.jsonl"), account=account,
        guard_report_sink=spine_sink)
