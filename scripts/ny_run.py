#!/usr/bin/env python3
"""Live NY-canon runner — the operational entrypoint for the REBUILT canon (R11/R13 wiring).

This is the per-bar lane: Sierra file tail -> CanonIngestor -> LiveDetector triggers ->
NYRunner (resting rule, budget-gates-fills, struct-event join) -> actions, decided per
closed 1m bar. It replaces canon_run's day-batch ScriptVerdictSource path for the rebuilt
canon; canon_run remains the OLD canon's entrypoint and must not carry this one
(HANDOVER-pat-arming §5.2).

DISARMED BY DEFAULT. Without --arm the spine holds a _NoBroker and every placement is a
journaled shadow decision — structurally orderless. The arm gate is byte-identical to
canon_run's: verify_for_arming (two-party token vs config/arming.yaml, HEAD == certified
commit) -> build_armed_broker (MNQ check, DTC logon) -> spine.arm(token), every failure a
hard exit. A refused arm never falls back to a shadow run.

CAPTURE NIGHT PURPOSE (2026-07-31): run disarmed against the live .scid/.depth tail. It
journals every verdict and action the rebuilt canon would have taken, and records the
phase-2 fixture streams (minute tape + MBP-10 snapshots) the agent layer's wiring is built
against. Sierra's own .depth file is tonight's R10b capture input (scripts/depth_capture.py
converts it after the close).

THE THREE-RULE EXECUTION SEMANTICS (handover rows J/K/L) live HERE, not inside NYRunner:
  L  one-per-level — enforced AT THE FILL, the measured predicate: apply_close_reverse
     prunes exited positions BEFORE the check, so a sibling that fills after its blocker
     exits is legitimate. A fill that lands while an open same-direction position sits
     within 3pt of its entry or shares its stop is closed immediately (rule_l_scratch) —
     the same fills-not-resting-orders semantics as the runner's budget race. Placement
     while a conflict holds is journaled as an advisory (rule_l_conflict_at_place).
  J  close-and-reverse — an opposing canon fill flattens the open position at the fill
     price and the reversal runs as its own trade; while a position is open, an opposing
     resting order's size is padded to close + open in one ticket.
  K  two sessions — every position filled before 09:30 is market-flattened on the first
     bar at/after 09:30.
J and K act on FILLS, so in a disarmed run they journal their intent and touch nothing.

ARMED USE IS BLOCKED ON (R13, certified on the box before any arm):
  * broker fill events wired into on_fill / on_position_closed (four-call contract,
    HANDOVER-pat-arming §4.3) — this loop only journals what it WOULD do until then;
  * the exit manager (V8) bound to filled positions and reporting realized $ back;
  * rows J/K exercised against real fills in a dry run.
The catch-up guard (2026-07-27 ghost-order class): a bar older than STALE_BAR_S against
the wall clock still feeds the ingestor but never emits triggers or actions.

Config: config/live.yaml, same keys as canon_run (feed.sierra.*, paths.*, account.equity,
telegram.*, spine.*) plus the `ny:` block — ny.profile (lucid|scaled600, default lucid),
ny.journal_subdir (default "ny": journals land under paths.journal_dir/ny so a parallel
canon_run never interleaves evidence; the KILL FILE is shared deliberately — one kill
halts both loops), ny.buffer (day-one budget buffer $; else account.equity minus
account.trailing_line; REQUIRED one way or the other — refuses to guess).

    python -m scripts.ny_run                      # disarmed shadow (tonight)
    python -m scripts.ny_run --telegram off       # log only
    python -m scripts.ny_run --arm                # two-party arm (Monday, after R10b/R13)

Clean shutdown: SIGINT/SIGTERM finishes the current poll, STOP alert, exit 0.
"""
from __future__ import annotations

import argparse
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import time as dtime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.canon_run import (
    LaunchAlerts,
    _collect_arm_token,
    _git_sha,
    build_alerts,
    build_armed_broker,
    load_config,
    setup_logging,
)
from src.canon.book import DepthBook
from src.canon.feed_guard import FeedGuard
from src.canon.ingestor import CanonIngestor
from src.canon.news_gate import NewsGate
from src.canon.ny_lane import NYLane, session_day
from src.canon.scorer_ny import LUCID, SCALED600
from src.canon.sierra_files import SierraFileFeed
from src.canon.sierra_symbol import RollWatcher, resolve_depth_path, resolve_scid_path
from src.canon.spine import OrderIntent, load_spine_config
from src.live.arming import ArmingError, verify_for_arming
from src.live.detector import LiveDetector
from src.live.feed import Bar
from src.live.ny_execution import DryRunBroker, NYExecution
from src.live.ny_runner import NYRunner
from src.live.route_b import (
    JsonlSink,
    RollState,
    build_shadow_instrument,
    constant_account_fn,
    default_feed_fn,
)

NY = "America/New_York"
PRE_FLATTEN = dtime(9, 30)             # rule K: two sessions, pre flat at the open
RULE_L_PTS = 3.0                       # rule L: same-level band (apply_close_reverse.py)
STALE_BAR_S = 300.0                    # catch-up guard. 120s clipped 17 REAL session
                                       # minutes on 2026-07-31 (loop lag spikes 120-132s);
                                       # 300s still kills restart ghost-order replays cold.
FRAME_WARMUP = pd.Timedelta(days=14)   # per-bar frame horizon: covers detect_triggers'
                                       # 10-day OTE lookback with slack (parity pinned)
# 2026-08-02/03 incident: two armed sessions found the order socket dead on the first
# real order because nothing touched it during a quiet market. DTC_KEEPALIVE_S drives
# an idle-independent ensure_connected() every ~10s (matches the negotiated heartbeat
# interval); DTC_ALERT_REPEAT_S caps how often a sustained outage re-alerts so a dead
# socket pages once loudly, then reminds every 5 minutes, not every 10 seconds.
DTC_KEEPALIVE_S = 10.0
DTC_ALERT_REPEAT_S = 300.0
# 2026-08-03 review finding: reconciliation originally ran ONLY right after a
# reconnect — a session with zero disconnects never checked for drift at all, from
# ANY cause (not just a reconnect-caused one), and a mismatch flagged by a one-off
# transient query hiccup had no path to ever clear itself if the connection then
# stayed healthy. Now genuinely periodic, always, whenever the connection is up.
RECONCILE_INTERVAL_S = 60.0
# 2026-08-05 review: a position query taken the instant after a fresh fill can catch
# Sierra's own internal state before it has caught up to the fill it just sent us --
# reproduced live tonight (a mismatch 8s after a real fill). One retry after a brief
# pause absorbs that without weakening the check: a GENUINE mismatch reproduces on the
# retry too, since nothing about a real drift resolves itself in two seconds.
RECONCILE_RETRY_DELAY_S = 2.0


def _profile(name: str):
    if name == "lucid":
        return LUCID
    if name == "scaled600":
        return SCALED600
    raise SystemExit(f"ny.profile must be lucid or scaled600, got {name!r}")


def _market_should_be_open(now: pd.Timestamp) -> bool:
    """CME equity-index session calendar (reuses the same closed-session mask the gap
    reporter trusts, src.engine.data._is_closed): False during the daily 17:00-18:00 ET
    maintenance break and the weekend. For 24/7 unattended operation (2026-08-03 audit):
    the feed-staleness guard cannot tell 'the market is closed, this silence is normal'
    from 'the feed broke' without this — and without the distinction, the loop fail-halts
    at 17:00 ET EVERY SINGLE DAY, which is the entire reason a human had to manually
    restart it before every session. Holidays are NOT modeled (matches the gap reporter's
    own documented limitation) — an exchange holiday still reads as 'should be open' and
    a quiet feed on one will still halt for a human to eyeball, which is the safe default
    for an unmodeled case, not a regression."""
    from src.engine.data import _is_closed
    ts = pd.Timestamp(now)
    if ts.tzinfo is None:
        # never guess a wall clock — the same convention FeedGuard.accept already
        # enforces on bars. Silently treating a naive value AS NY time could misjudge
        # market hours by several hours if the real caller meant UTC (self.clock()'s
        # actual contract) — a wrong answer here means either a false halt or, worse,
        # a false "expected closure" masking a genuine feed failure.
        raise ValueError("_market_should_be_open needs a tz-aware timestamp")
    ts = ts.tz_convert(NY)
    return not bool(_is_closed(pd.DatetimeIndex([ts])).iloc[0])


def _trigger_key(t) -> tuple:
    """Identity for detector dedup — LiveDetector re-emits overlapping tail detections."""
    return (str(t.ts), str(getattr(t, "tf", "")), t.direction, str(getattr(t, "kind", "")),
            str(getattr(t, "pattern", "")), round(float(t.entry_ref), 2),
            round(float(t.stop_ref), 2))


@dataclass
class _Position:
    ref: str
    direction: str                     # "long" | "short"
    entry: float
    stop: float
    size: int
    fill_ts: pd.Timestamp              # tz-aware
    pre: bool                          # filled before 09:30 ET (rule K applies)


@dataclass
class NYLive:
    """The rebuilt canon's per-bar loop. Feed/guard/roll machinery mirrors RouteBLive;
    the verdict pipeline is NYRunner instead of the day-batch relay."""

    feed: SierraFileFeed
    data_dir: str | Path
    runner: NYRunner
    detector: LiveDetector
    ingestor: CanonIngestor
    instrument: object                          # ShadowSpineInstrument
    account: str = "FUNDED"
    buffer: float = 2_000.0                     # day-one budget buffer (equity - trailing)
    equity: float = 50_000.0
    root: str = "NQ"
    suffix: str = "-CME"
    alerts: LaunchAlerts | None = None
    decision_sink: object | None = None         # decisions.jsonl
    action_sink: object | None = None           # ny_actions.jsonl
    verdict_sink: object | None = None          # ny_verdicts.jsonl
    fixture_sink: object | None = None          # fixtures.jsonl (phase-2 agent streams)
    armed: bool = False
    execution: NYExecution = None               # R13 layer; shadow-mode default
    replay_day: str | None = None               # practice day: act on this historical day
    kill_file: str | Path | None = None         # shared with canon_run: one kill, both loops
    clock: object = None                        # Callable[[], pd.Timestamp], injectable
    reconcile_sleep: object = None              # Callable[[float], None], injectable

    guard: FeedGuard = None
    watcher: RollWatcher = None
    roll_state: RollState = None
    _day: str | None = field(default=None, init=False)
    _seen: set = field(default_factory=set, init=False)
    _positions: dict = field(default_factory=dict, init=False)   # ref -> _Position
    _last_bar_ts: pd.Timestamp | None = field(default=None, init=False)
    _acct_fn: object = field(default=None, init=False)
    _feed_fn: object = field(default=None, init=False)
    _bar_scale_journaled: bool = field(default=False, init=False)
    _depth_scale_journaled: bool = field(default=False, init=False)
    desk: object | None = None                  # R15 AgentDesk (None = mech-only)
    _last_flip_by: str | None = field(default=None, init=False)
    _last_keepalive: pd.Timestamp | None = field(default=None, init=False)
    _dtc_down_since: pd.Timestamp | None = field(default=None, init=False)
    _last_dtc_alert: pd.Timestamp | None = field(default=None, init=False)
    _announced_closure: bool = field(default=False, init=False)
    _position_mismatch: bool = field(default=False, init=False)
    _last_reconcile: pd.Timestamp | None = field(default=None, init=False)

    def __post_init__(self):
        if self.execution is None:
            self.execution = NYExecution(mode="shadow")
        self.execution.journal = self._journal
        self.execution.on_closed = self._on_execution_closed
        if self.guard is None:
            self.guard = FeedGuard()
        if self.watcher is None:
            self.watcher = RollWatcher(root=self.root)
        if self.roll_state is None:
            self.roll_state = RollState(root=self.root)
        if self.clock is None:
            self.clock = lambda: pd.Timestamp.now(tz="UTC")
        if self.reconcile_sleep is None:
            self.reconcile_sleep = time.sleep
        self._acct_fn = constant_account_fn(self.equity)
        self._feed_fn = default_feed_fn(self.ingestor, lambda: self._last_bar_ts)

    # ---------------------------------------------------------------- journaling
    def _say(self, text: str) -> None:
        if self.alerts is not None:
            self.alerts.say(text)

    def _journal(self, row: dict) -> None:
        if self.decision_sink is not None:
            self.decision_sink(row)

    # ---------------------------------------------------------------- rules J/K/L
    def _rule_l_conflict(self, direction: str, limit: float, stop: float) -> str | None:
        """Row L predicate, verbatim from apply_close_reverse: same-direction, within 3pt
        of an OPEN position's entry or sharing its stop. Returns the blocking ref."""
        for p in self._positions.values():
            if p.direction == direction and (
                    abs(p.entry - limit) <= RULE_L_PTS or p.stop == stop):
                return p.ref
        return None

    def _on_execution_closed(self, ref: str, pl: float) -> None:
        self._close_position(ref, pl=pl, reason="execution")

    def _close_position(self, ref: str, *, pl: float, reason: str) -> None:
        p = self._positions.pop(ref, None)
        if self.armed:
            side = f"{p.direction.upper()} " if p is not None else ""
            self._say(f"CLOSED {side}{ref} ({reason}): ${pl:+,.2f}")
        try:
            self.runner.on_position_closed(ref, pl=pl)
        except RuntimeError as e:
            # unknown to the runner (restart residue, injected state): journal loudly,
            # keep the loop alive — the operator has the kill file if this is wrong.
            self._journal({"type": "position_close_unknown_ref", "ref": ref,
                           "reason": reason, "error": str(e)})
            self._say(f"WARN position close for unknown ref {ref} ({reason})")

    def _opposing_open_size(self, direction: str) -> int:
        return sum(p.size for p in self._positions.values() if p.direction != direction)

    def _rule_k_flatten(self, ts: pd.Timestamp, bar_open: float | None = None) -> None:
        """Row K: every pre-session position goes flat AT the open. Bars are open-stamped,
        so the bar whose CLOSE is 09:30:00 (stamp 09:29) is the first moment the flatten
        can go out — test the close time, not the stamp, or the flatten is a minute late
        and eats opening volatility the measured book never held."""
        et = (ts + pd.Timedelta(minutes=1)).tz_convert(NY)
        if et.time() < PRE_FLATTEN:
            return
        for ref, p in list(self._positions.items()):
            if p.pre:
                sgn = 1.0 if p.direction == "long" else -1.0
                pl = (sgn * (float(bar_open) - p.entry) * 2.0 * p.size
                      if bar_open is not None else 0.0)
                self._journal({"type": "rule_k_flatten", "ref": ref, "ts": str(ts),
                               "pl_estimated": round(pl, 2), "executed": False})
                self._say(f"RULE K: pre position {ref} flat at the open")
                if self.execution.live:
                    self.execution.close_now(ref, "rule_k_flatten")
                else:
                    self._close_position(ref, pl=pl, reason="rule_k_flatten")
                if self.desk is not None and bar_open is not None:
                    self.desk.on_position_closed_externally(
                        ref, "rule_k_flatten", ts.tz_convert(NY), float(bar_open),
                        self.desk.tape_frame())

    # ---------------------------------------------------------------- action execution
    def _execute(self, actions: list[dict], now: pd.Timestamp) -> None:
        for a in actions:
            kind = a.get("action")
            if self.action_sink is not None:
                self.action_sink({**a, "ts": str(now), "armed": self.armed,
                                  "verdict": None,  # full verdict rides ny_verdicts.jsonl
                                  "vid": (a.get("verdict") or {}).get("vid")})
            v = a.get("verdict")
            if v is not None and self.verdict_sink is not None:
                self.verdict_sink(v)
            if kind == "cancel":
                self.execution.cancel(a["ref"], a.get("why", ""))
                continue
            if kind == "modify_size":
                v = a.get("verdict") or {}
                c = self.runner._cands.get(a["ref"])
                if c is not None:
                    intent = OrderIntent(side=c.side, order_type="limit",
                                         entry_ref=float(c.limit), stop=float(c.stop),
                                         target=None, size=int(a["size"]),
                                         setup_id=f"{a['ref']}:r{int(a['size'])}",
                                         account=self.account)
                    self.execution.modify_size(a["ref"], intent, c.trigger)
                continue
            if kind != "place":
                continue                       # scratch results ride on_fill, not here
            if self._position_mismatch:
                # 2026-08-03 audit: a broker/tracking disagreement blocks NEW risk only —
                # cancels above and existing positions' resting stops are untouched.
                self._journal({"type": "place_blocked_position_mismatch", "ref": a["ref"],
                               "ts": str(now)})
                c = self.runner._cands.get(a["ref"])
                if c is not None:
                    c.resting, c.size = False, 0
                    self.runner.watch.mark_gone(a["ref"])
                continue
            block = self._rule_l_conflict(
                "long" if a["side"] == "B" else "short", a["limit"], a["stop"])
            if block is not None:
                # advisory only: rule L gates FILLS (the measured predicate) — the order
                # rests; if it fills while the conflict still holds, on_fill scratches it.
                self._journal({"type": "rule_l_conflict_at_place", "ref": a["ref"],
                               "blocking": block, "ts": str(now)})
            size = int(a["size"])
            pad = self._opposing_open_size("long" if a["side"] == "B" else "short")
            if pad:                            # rule J: close + open in one ticket
                self._journal({"type": "rule_j_padded", "ref": a["ref"],
                               "open_size": size, "close_pad": pad, "ts": str(now)})
            intent = OrderIntent(side=a["side"], order_type="limit",
                                 entry_ref=float(a["limit"]), stop=float(a["stop"]),
                                 target=None, size=size + pad, setup_id=a["ref"],
                                 account=self.account)
            acct = self._acct_fn(now)
            feed = self._feed_fn(now)
            now_epoch = float(self.clock().timestamp())
            try:
                self.instrument.spine.guard_report(intent, acct, feed, now_epoch)
                self.instrument.spine.place(intent, acct, feed, now_epoch)
            except Exception as e:             # noqa: BLE001 — capture night: journal, live on
                self._journal({"type": "spine_error", "ref": a["ref"], "error": str(e),
                               "ts": str(now)})
                self._say(f"WARN spine error on {a['ref']}: {e}")
                continue
            trig = self.runner._cands[a["ref"]].trigger \
                if a["ref"] in self.runner._cands else None
            if not self.execution.place(a["ref"], intent, trig):
                # submission failed: un-rest the candidate so a later bar re-places it.
                # 2026-08-02/03 audit: this is EXACTLY the event that went unnoticed for
                # 9 hours overnight and again mid-session — a failed placement now pages
                # immediately, armed or not, instead of waiting to be discovered in a
                # journal nobody was tailing.
                self._say(f"WARN order FAILED to place: {a['ref']} {a['side']} "
                          f"{size + pad}@{a['limit']:.2f} — see decisions.jsonl for the "
                          "broker error; the candidate will re-place on a later bar")
                c = self.runner._cands.get(a["ref"])
                if c is not None:
                    c.resting, c.size = False, 0
                    self.runner.watch.mark_gone(a["ref"])
                self._journal({"type": "placement_failed_unrested", "ref": a["ref"]})
            elif self.armed:
                self._say(f"PLACED {a['side']} {a['ref']} x{size + pad}@{a['limit']:.2f} "
                          f"stop {a['stop']:.2f}")

    # ---------------------------------------------------------------- fills (armed loop)
    def on_fill(self, ref: str, fill_ts, filled_size: int) -> dict:
        """Broker fill event -> the runner's fill-minute contract. Rules L and J are
        re-checked HERE because the book's predicates act at the fill."""
        ts = pd.Timestamp(fill_ts)
        if ts.tzinfo is None:                  # DTC fills are epoch-UTC; guessing a zone
            raise ValueError(f"on_fill needs a tz-aware stamp, got naive {ts}")
        res = self.runner.on_fill(ref, ts, filled_size)
        if res.get("action") == "scratch":
            self._journal({"type": "scratch", **{k: res[k] for k in ("ref", "why")},
                           "ts": str(ts)})
            self.execution.scratch_unconfirmed(ref, int(filled_size),
                                               f"gate:{res.get('why', '')[:40]}")
            return res
        v = res["verdict"]
        direction = v["direction"]
        block = self._rule_l_conflict(direction, float(v["entry"]), float(v["stop"]))
        if block is not None:                  # fill landed inside the conflict window
            self._journal({"type": "rule_l_scratch", "ref": ref, "blocking": block,
                           "ts": str(ts)})
            self.execution.scratch_unconfirmed(ref, int(filled_size),
                                               f"one_per_level:{block}")
            # the runner already committed this fill (budget + possibly the elite slot).
            # Release the risk immediately — a scratched trade "never existed" and must
            # not hold budget room all session. KNOWN CONSERVATIVE DEVIATION: an elite
            # slot spent by a rule-L-scratched fill stays spent (the lane has no unspend
            # API) — sizes down, never up; flagged for the R13 dry-run.
            self._close_position(ref, pl=0.0, reason="rule_l_scratch")
            return {"action": "scratch", "ref": ref, "why": f"one_per_level:{block}"}
        for pref, p in list(self._positions.items()):   # rule J: flatten opposing at fill
            if p.direction != direction:
                sgn = 1.0 if p.direction == "long" else -1.0
                pl = sgn * (float(v["entry"]) - p.entry) * 2.0 * p.size
                self._journal({"type": "rule_j_flip", "closed": pref, "by": ref,
                               "at": float(v["entry"]), "pl_estimated": round(pl, 2),
                               "ts": str(ts)})
                self._last_flip_by = ref
                if self.desk is not None:
                    self.desk.on_position_closed_externally(
                        pref, "rule_j_flip", ts, float(v["entry"]),
                        getattr(self.desk, "_tape", None))
                if self.execution.live:
                    self.execution.close_now(pref, "rule_j_flip")
                else:
                    self._close_position(pref, pl=pl, reason="rule_j_flip")
        et = ts.tz_convert(NY)
        pre = et.time() < PRE_FLATTEN
        self._positions[ref] = _Position(ref=ref, direction=direction,
                                         entry=float(v["entry"]), stop=float(v["stop"]),
                                         size=int(filled_size), fill_ts=ts, pre=pre)
        self.execution.confirm_fill(ref, v, int(filled_size), pre)
        if self.armed:
            self._say(f"FILLED {direction.upper()} {ref} x{int(filled_size)} @ "
                      f"{float(v['entry']):.2f} (stop {float(v['stop']):.2f})")
        if self.desk is not None:
            # R15: the agent inherits the mechanical plan at commit. is_reversal =
            # this fill flattened an opposing position via rule J this same minute
            # (the book's strongest signal — reference NEW-POSITION context line).
            self.desk.on_committed_fill(
                ref, v, int(filled_size), ts,
                trigger=self.runner.trigger_for(ref), pre=pre,
                is_reversal=bool(self._last_flip_by == ref))
        return res

    def on_position_closed(self, ref: str, *, pl: float) -> None:
        self._close_position(ref, pl=pl, reason="exit_manager")

    # ---------------------------------------------------------------- per-bar dispatch
    def _start_day_if_new(self, ts: pd.Timestamp) -> None:
        # session_day's 17:00 maintenance boundary reads the timestamp's OWN wall time.
        # Sierra bars are UTC — fed raw, the "day" rolled at 17:00 UTC = 1pm ET, clearing
        # position state mid-session (seen live on 07-31 and in the R13 replay). Convert
        # to ET here so the roll lands at the real CME boundary (17:00 ET).
        day = session_day(ts.tz_convert(NY))
        if day != self._day:
            # Sierra writes settlement/close records with future stamps; session_day on
            # one of those rolled the live day to 2026-08-01 mid-afternoon on 07-31. A
            # spurious roll CLEARS position/candidate state — refuse any roll driven by
            # a bar stamped in the future relative to the wall clock.
            if (self._day is not None
                    and (ts - self.clock()).total_seconds() > 3600):
                self._journal({"type": "day_roll_refused_future_bar", "bar_ts": str(ts),
                               "would_be_day": day, "current_day": self._day})
                return
            self._day = day
            self._seen.clear()
            self._positions.clear()
            # R13: armed multi-day use must replace this with the broker account
            # read-back (equity - trailing_line per session), not the boot-time value.
            self.runner.start_day(day, buffer=float(self.buffer))
            self._journal({"type": "ny_day_start", "day": day, "buffer": self.buffer,
                           "bar_ts": str(ts)})
            self._say(f"NY canon day {day} — buffer ${self.buffer:,.0f}")

    def dispatch(self, events: list[dict], now: pd.Timestamp) -> None:
        for ev in events:
            if ev["kind"] == "depth":
                self.ingestor.on_depth(ev["event"])
                continue
            if ev["kind"] != "minute":
                continue
            for gbar in self.guard.accept(dict(ev["bar"])):
                bts = pd.Timestamp(gbar["ts_event"])
                rs = self.roll_state.on_bar(bts)
                if rs.get("roll"):
                    self._journal({"type": "roll", **{k: str(v) for k, v in rs.items()}})
                self.ingestor.on_bar(gbar)
                t = ev["tape"]
                self.ingestor.on_minute_tape(bts, t["delta"], t["vol"], t["vwp"])
                if self.desk is not None:
                    self.desk.push_tape(bts.tz_convert(NY), float(t["delta"]),
                                        float(t["vol"]))
                self._last_bar_ts = bts
                if self.execution.live and hasattr(self.execution.broker, "on_bar"):
                    self.execution.broker.on_bar(bts, float(gbar["high"]),
                                                 float(gbar["low"]),
                                                 float(gbar["close"]))
                self._start_day_if_new(bts)
                # catch-up guard: an old bar builds state but must never act — and
                # fixture rows for a boot backlog are noise, so they wait too. In
                # PRACTICE-DAY replay the guard is the day match instead: the certified
                # rehearsal must act on historical bars, but only the chosen day's.
                if self.replay_day is not None:
                    if session_day(bts.tz_convert(NY)) != self.replay_day:
                        continue
                else:
                    age = (self.clock() - (bts + pd.Timedelta(minutes=1))).total_seconds()
                    if age > STALE_BAR_S:
                        self._journal({"type": "catchup_bar_skipped", "ts": str(bts),
                                       "age_s": round(age, 1)})
                        continue
                if self.fixture_sink is not None:
                    self.fixture_sink({"type": "tape", "ts": str(bts), **t})
                    self.fixture_sink({"type": "book", "ts": str(bts),
                                       "levels": self.ingestor.book.long_form(10)})
                try:
                    # FILLS FIRST (R13 practice day 3, ny:20): the broker saw this bar
                    # before any of the decisions below. Processing fills before the
                    # runner's per-bar cancels/resizes means a cancel can never race a
                    # fill the broker has already made — the fill commits (or scratches)
                    # here, the runner marks the candidate filled, and its re-evaluation
                    # below skips it. The execution-layer graveyard covers the residual
                    # armed-path race (broker fills between our poll and our cancel).
                    for f in self.execution.poll_fills():
                        self.on_fill(f["ref"], f["ts"], int(f["size"]))
                    self._rule_k_flatten(bts, bar_open=float(gbar["open"]))
                    # LiveDetector's 07:45-11:00 band is ET WALL TIME (proven against
                    # NY-tz reference frames); Sierra bars arrive UTC. Convert at this
                    # boundary or wants() never passes during the session.
                    bts_ny = bts.tz_convert(NY)
                    bar = Bar(ts_event=bts_ny, open=float(gbar["open"]),
                              high=float(gbar["high"]), low=float(gbar["low"]),
                              close=float(gbar["close"]), volume=float(gbar["volume"]))
                    # ONE frame per bar, trimmed to the detector's warmup horizon.
                    # The full-history rebuild (x2, plus a full tz-convert) cost ~1 real
                    # minute per in-band bar on the box — the R13 replay took 3.5h and a
                    # live bar would flirt with the 60s budget. detect_triggers' deepest
                    # lookback is the 10-day OTE window; 14 days keeps it whole
                    # (trim parity pinned in tests/test_ny_run.py).
                    df = self.ingestor.bars_frame()
                    if len(df):
                        ts_col = pd.to_datetime(df.ts_event)
                        df = (df[ts_col >= bts - FRAME_WARMUP]
                              .assign(ts_event=lambda d: pd.to_datetime(d.ts_event)
                                      .dt.tz_convert(NY)))
                    for trig in self.detector.on_bar(df, bar):
                        key = _trigger_key(trig)
                        if key in self._seen:
                            continue
                        self._seen.add(key)
                        acts = self.runner.on_trigger(trig)
                        self._journal({"type": "trigger_seen", "ts": str(trig.ts),
                                       "direction": trig.direction,
                                       "entry_ref": float(trig.entry_ref),
                                       "placed": bool(acts)})
                        self._execute(acts, bts)
                    self._execute(self.runner.on_bar(bts, float(gbar["high"]),
                                                     float(gbar["low"])), bts)
                    if self.execution.live:
                        self.execution.on_bar(df, bts_ny)   # same trimmed NY frame
                    if self.desk is not None:
                        self.desk.on_bar(bts_ny, bar, df,
                                         self.desk.tape_frame(),
                                         self.ingestor.book.long_form(10))
                except Exception as e:         # noqa: BLE001 — capture night: a crashed
                    # loop at 09:00 loses the session's evidence; journal loudly, keep
                    # ingesting. Runner state may be inconsistent for THIS candidate —
                    # the journal row is the flag to investigate before certifying.
                    self._journal({"type": "dispatch_error", "ts": str(bts),
                                   "error": repr(e)})
                    self._say(f"WARN dispatch error at {bts}: {e}")

    # ---------------------------------------------------------------- loop
    def _maybe_retarget(self, now: pd.Timestamp) -> None:
        if self.replay_day is not None:
            return                             # the feed was pinned to the replay day
        today = now.tz_convert(NY).strftime("%Y-%m-%d")
        # Latch _depth_day only once today's file was FOUND: a 07:00 boot predates
        # Sierra creating the day's .depth, and a latch-on-miss would leave the whole
        # session depthless (W/D never satisfiable, zero verdicts — silently).
        if getattr(self, "_depth_day", None) != today:
            p = resolve_depth_path(self.data_dir, now, day=today,
                                   root=self.root, suffix=self.suffix)
            if p is not None and Path(p).exists():
                self.feed.retarget_depth(p)
                self._depth_day = today
                self._journal({"type": "depth_retarget", "path": str(p), "day": today})
        ev = self.watcher.check(now)
        if ev is not None:
            self.feed.retarget_scid(
                resolve_scid_path(self.data_dir, now, self.root, self.suffix),
                depth_path=resolve_depth_path(self.data_dir, now,
                                              root=self.root, suffix=self.suffix))
            # a new file re-detects both price scales — journal the fresh decisions too
            self._bar_scale_journaled = self._depth_scale_journaled = False
            self._say(f"contract ROLL: {ev}")

    def warm(self, bars_df: pd.DataFrame, footprint_df: pd.DataFrame | None = None):
        from src.canon.feed_guard import warm_start
        if footprint_df is not None:
            warm_start(self.ingestor, bars_df, footprint_df)
        else:
            for _, row in bars_df.iterrows():
                self.ingestor.on_bar(dict(row))

    def _journal_scales(self) -> None:
        """One loud row per detected divisor — the R13 practice day ran an entire session
        on 100x prices with zero console evidence; the scale decision is never silent again."""
        bar_s = getattr(self.feed, "bar_price_scale", None)
        depth_s = getattr(self.feed, "depth_price_scale", None)
        if not self._bar_scale_journaled and bar_s is not None:
            self._bar_scale_journaled = True
            self._journal({"type": "price_scale", "which": "bars", "scale": float(bar_s)})
            self._say(f"price scale: .scid bars / {bar_s:g}")
        if not self._depth_scale_journaled and depth_s is not None:
            self._depth_scale_journaled = True
            self._journal({"type": "price_scale", "which": "depth",
                           "scale": float(depth_s)})
            self._say(f"price scale: .depth levels / {depth_s:g}")

    def _reconcile_position(self, now: pd.Timestamp) -> bool:
        """Compare in-process position bookkeeping against the broker's own live
        read-back. Called after every DTC reconnect recovery (the exact moment state may
        have silently drifted while the socket was dead — a resting order could have
        filled, or a stop fired, with nobody watching). Soft: blocks NEW entries only —
        an existing position's protection is the real resting stop AT THE BROKER, which
        needs no cooperation from this process to keep working. Never guesses a fix.

        2026-08-05 review: one retry, after RECONCILE_RETRY_DELAY_S, before treating a
        mismatch (or a query error) as real — Sierra's own position state can lag a query
        taken right after a fresh fill by a couple of seconds, and this was reproduced
        live. A genuine drift reproduces on the retry too; a transient one does not."""
        broker = getattr(self.execution, "broker", None)
        if broker is None or not hasattr(broker, "position"):
            return True                            # dry-run/shadow: nothing to reconcile
        expected = sum(p.size if p.direction == "long" else -p.size
                       for p in self._positions.values())
        actual, err = None, None
        for attempt in (1, 2):
            try:
                actual = int(broker.position(self.account))
                err = None
            except Exception as e:                 # noqa: BLE001 — can't verify = not ok
                err = e
            if err is None and actual == expected:
                break                              # clean match — no need for a retry query
            if attempt == 1:
                self.reconcile_sleep(RECONCILE_RETRY_DELAY_S)
        if err is not None:
            self._journal({"type": "position_reconcile_error", "error": repr(err),
                           "ts": str(now)})
            self._position_mismatch = True
            return False
        ok = actual == expected
        if not ok and not self._position_mismatch:
            self._say(f"WARN position mismatch: tracking {expected}, broker reports "
                      f"{actual} — blocking new entries until reconciled (existing "
                      "stops are still live at the broker)")
            self._journal({"type": "position_mismatch", "expected": expected,
                           "actual": actual, "ts": str(now)})
        elif ok and self._position_mismatch:
            self._say(f"position reconciled: {actual} matches tracking — new entries resume")
            self._journal({"type": "position_reconciled", "actual": actual, "ts": str(now)})
        self._position_mismatch = not ok
        return ok

    def _maybe_reconcile(self, now: pd.Timestamp) -> None:
        """Position reconciliation on a flat periodic cadence whenever the DTC
        connection is up — independent of whether it JUST reconnected. Called from
        the keepalive's throttled cadence; self-throttles again to
        RECONCILE_INTERVAL_S so it does not query the broker every single poll."""
        if (self._last_reconcile is not None
                and (now - self._last_reconcile).total_seconds() < RECONCILE_INTERVAL_S):
            return
        self._last_reconcile = now
        self._reconcile_position(now)

    def _dtc_keepalive(self, now: pd.Timestamp) -> None:
        """Idle-independent liveness check on the ORDER connection (2026-08-02/03 fix).
        Runs every poll but self-throttles to DTC_KEEPALIVE_S — a dead socket is caught
        and either healed or loudly alerted within ~10s of going stale, never discovered
        only when the next real order needs it."""
        broker = getattr(self.execution, "broker", None)
        if broker is None or not hasattr(broker, "ensure_connected"):
            return                                  # dry-run / shadow: nothing to keep alive
        if (self._last_keepalive is not None
                and (now - self._last_keepalive).total_seconds() < DTC_KEEPALIVE_S):
            return
        self._last_keepalive = now
        ok = broker.ensure_connected()
        if ok:
            if self._dtc_down_since is not None:
                downtime = (now - self._dtc_down_since).total_seconds()
                self._say(f"DTC order route RECOVERED after {downtime:.0f}s downtime")
                self._journal({"type": "dtc_reconnected", "ts": str(now),
                               "downtime_s": round(downtime, 1)})
                self._dtc_down_since = self._last_dtc_alert = None
                self._last_reconcile = None    # force an IMMEDIATE reconcile below —
                                               # state most likely drifted while blind
            self._maybe_reconcile(now)
            return
        first = self._dtc_down_since is None
        if first:
            self._dtc_down_since = now
        self._journal({"type": "dtc_keepalive_failed", "ts": str(now)})
        if first or (self._last_dtc_alert is not None
                     and (now - self._last_dtc_alert).total_seconds() >= DTC_ALERT_REPEAT_S):
            self._last_dtc_alert = now
            downtime = (now - self._dtc_down_since).total_seconds()
            self._say(f"WARN DTC order route DOWN {downtime:.0f}s — orders cannot reach "
                      f"the broker; retrying every {DTC_KEEPALIVE_S:.0f}s")

    def poll_once(self, now: pd.Timestamp | None = None) -> bool:
        now = self.clock() if now is None else now
        self._dtc_keepalive(now)
        self._maybe_retarget(now)
        self.dispatch(self.feed.poll_events(), now)
        self._journal_scales()
        return self.guard.check_stale(now)

    def serve(self, sleep_fn, poll_interval_s: float = 1.0, max_polls=None, stop_fn=None):
        mode = ("ARMED" if self.armed else
                f"DRYRUN practice day {self.replay_day}" if self.replay_day
                else "DISARMED (shadow)")
        self._say(f"NY canon loop {mode} — git {_git_sha()}")
        polls, boot, warned_no_bars = 0, self.clock(), False
        while max_polls is None or polls < max_polls:
            if stop_fn is not None and stop_fn():
                break
            if self.kill_file is not None and Path(self.kill_file).exists():
                self._say("KILL file present — stopping the NY loop")
                self._journal({"type": "kill_file_stop"})
                break
            now = self.clock()
            if self.poll_once(now):
                if _market_should_be_open(now):
                    self._say("feed STALLED — halting (fail closed)")
                    self._journal({"type": "feed_stall_halt", "ts": str(now)})
                    break
                # 2026-08-03 audit: an expected closure (daily 17:00-18:00 ET break,
                # weekend) is NOT a fault — idle through it instead of halting. The DTC
                # keepalive above keeps running every poll regardless, so the order
                # connection is proven alive (or healed) well before bars resume, not
                # discovered dead at the worst possible moment: the reopen.
                if not self._announced_closure:
                    self._announced_closure = True
                    self._say("feed quiet during an expected market closure — idling, "
                              "not halting (resumes automatically when bars return)")
                    self._journal({"type": "expected_closure_idle", "ts": str(now)})
            else:
                self._announced_closure = False
            # a feed that never produced a single bar never trips the stall guard —
            # a wrong .scid naming variant would otherwise run silently all day.
            if (not warned_no_bars and self.guard._last is None
                    and (self.clock() - boot).total_seconds() > 180):
                warned_no_bars = True
                self._say("WARN no bars 3 minutes after boot — check the .scid path "
                          "and naming variant")
            polls += 1
            sleep_fn(poll_interval_s)


# -------------------------------------------------------------------- assembly

def build_ny_live(cfg: dict, alerts: LaunchAlerts, log, arm: bool = False,
                  config_path: str | Path = "config/live.yaml",
                  dryrun: bool = False, replay_day: str | None = None,
                  agents: bool | None = None,
                  agent_kill_test: bool = False) -> NYLive:
    # R13 CERTIFIED 2026-08-01 (this commit): four practice-day replays of 2026-07-31 on
    # the box surfaced and closed — 100x bar scale, 1pm-ET day roll, tick records
    # aggregated as bars, and the cancel/fill same-bar race (ny:2026-07-31:20, whose
    # day-4 journal shows the fill surfaced and scratched flat). The arm path below
    # remains two-party fail-closed: no config/arming.yaml -> no token verify -> no arm.
    ny = cfg.get("ny", {}) or {}
    sc = (cfg.get("feed", {}) or {}).get("sierra", {}) or {}
    paths = cfg.get("paths", {}) or {}
    acct = cfg.get("account", {}) or {}
    data_dir = sc.get("data_dir")
    if not data_dir:
        raise SystemExit("feed.sierra.data_dir required")
    root, suffix = sc.get("root", "NQ"), sc.get("suffix", "-CME")

    equity = float(acct.get("equity", 50_000.0))
    if "buffer" in ny:
        buffer = float(ny["buffer"])
    elif "trailing_line" in acct:
        buffer = equity - float(acct["trailing_line"])
    else:
        raise SystemExit("set ny.buffer or account.trailing_line — the budget buffer "
                         "is a risk input and will not be guessed")

    out = Path(paths.get("journal_dir", "runs/journal")) / ny.get("journal_subdir", "ny")
    out.mkdir(parents=True, exist_ok=True)
    kill_file = paths.get("kill_file", "KILL")     # SHARED with canon_run deliberately

    now = pd.Timestamp.now(tz="UTC")
    today = now.tz_convert(NY).strftime("%Y-%m-%d")
    # a practice-day replay reads the REPLAY day's depth file — today's may not exist
    # (Saturday) and would leave the depth gates blind for the whole rehearsal
    depth_day = replay_day or today
    depth_ref = pd.Timestamp(depth_day, tz=NY) if replay_day else now
    scid = Path(sc["scid"]) if sc.get("scid") else resolve_scid_path(
        data_dir, now, root, suffix)
    depth = resolve_depth_path(data_dir, depth_ref, day=depth_day,
                               root=root, suffix=suffix)
    depth_ok = depth is not None and Path(depth).exists()
    # --- bar price scale (R13 practice-day finding 2026-08-01): the box's Rithmic-named
    # NQU6.CME.scid writes prices 100x (2857526.00 for 28575.26). An explicit
    # feed.sierra.price_scale pin wins; otherwise the feed detects the divisor against
    # the repo reference data's last close and REFUSES to run if no clean power of ten
    # fits. The NY loop never runs unanchored — mis-scaled bars mean zero triggers, silently.
    scale_pin = sc.get("price_scale")
    ref_px = None
    if scale_pin is None:
        ref_pq = Path(sc.get("reference_parquet", "data/reference/nq_1m_master.parquet"))
        if not ref_pq.exists():
            raise SystemExit(f"{ref_pq} missing — the bar price-scale check needs the "
                             "reference anchor (or pin feed.sierra.price_scale)")
        ref_px = float(pd.read_parquet(ref_pq, columns=["close"])["close"].iloc[-1])
    feed = SierraFileFeed(scid, depth if depth_ok else None,
                          flush_ms=int(sc.get("flush_ms", 1000)),
                          bar_price_scale=(float(scale_pin) if scale_pin is not None
                                           else None),
                          reference_px=ref_px)
    if not depth_ok:
        alerts.say(f"no .depth file for {depth_day} yet — depth features stand down "
                   "until it appears (retargeted automatically each poll)")

    ingestor = CanonIngestor(book=DepthBook())
    lane = NYLane(ingestor=ingestor, profile=_profile(ny.get("profile", "lucid")),
                  news_gate=NewsGate.load(), account=sc.get("account", "FUNDED"))
    runner = NYRunner(lane=lane)

    broker, token = None, None
    if arm:
        token = _collect_arm_token()
        try:
            auth = verify_for_arming(token, entrypoint="scripts.ny_run")
        except ArmingError as e:
            raise SystemExit(f"ARM REFUSED: {e}")
        broker, _client = build_armed_broker(cfg, auth, log)
        # 2026-08-03 audit: a fresh process starts believing it is flat (empty
        # _positions) — if it crashed mid-trade, or a prior session's process died
        # without a clean flatten, the BROKER may disagree. Continuing to run in that
        # state is dangerous: the mechanical laws (09:30/15:55 flatten, rule J/K) are
        # blind to a position they don't know exists. This process never GUESSES a
        # recovery (rebuilding entry/stop/direction from partial broker data is worse
        # than refusing) — it refuses to arm and tells the operator to look, the same
        # fail-closed posture as every other refusal in this file.
        acct_label = sc.get("account", "FUNDED")
        try:
            existing = int(broker.position(acct_label))
        except Exception as e:                     # noqa: BLE001 — can't verify = refuse
            raise SystemExit(
                f"ARM REFUSED: could not verify the broker is flat before arming "
                f"({type(e).__name__}: {e}) — a fresh process must never start managing "
                "a position it cannot first confirm is zero.")
        if existing != 0:
            raise SystemExit(
                f"ARM REFUSED: broker reports an existing {acct_label} position of "
                f"{existing} that this fresh process has no record of (crash-restart "
                "while in a trade, or a stale prior session). This process does not "
                "auto-adopt unknown positions — flatten it manually (Sierra Trade "
                "Positions Window), confirm flat, then arm.")
    # 2026-08-05 incident: instrument.spine used to be wired to the REAL broker and
    # armed with the same token as the live loop -- both SpineExecutor.place() (here,
    # via guard_report/place below, for promotion-gate evidence) AND NYExecution.place()
    # (the actual certified execution path) independently called broker.submit_bracket()
    # for the SAME trigger. Every armed trade went out as two real, separate bracket
    # orders. This spine exists ONLY for promotion-gate evidence (guard_report/place
    # calls below) -- exactly like canon_run.py's own instrument, which is documented as
    # "NOTHING TOUCHES A BROKER... no DTC order path here". It must NEVER be armed here.
    # broker=None (not `broker`) wires _NoBroker structurally -- even a future bug that
    # re-adds an .arm() call cannot route a real order through this instrument again.
    spine_cfg = load_spine_config(config_path)     # pinned Tier-1 (F6: honour --config)
    instrument = build_shadow_instrument(out, account=sc.get("account", "FUNDED"),
                                         cfg=spine_cfg, kill_file=kill_file,
                                         broker=None, arm_token=token)

    # R15: agents on by config (ny.agents) or the --agents flag. In agent mode the
    # execution layer does NOT bind the live V8 exit engine — the AgentDesk owns the
    # standing plan and runs V8 in shadow for the counterfactual (HANDOVER §7 row 7).
    agents_on = bool(agents if agents is not None else ny.get("agents", False))
    execution = None
    if dryrun:
        from scripts.build_l2_outcomes import l2_cfg    # the canon exit config (V8)
        execution = NYExecution(mode="dryrun", broker=DryRunBroker(),
                                account=sc.get("account", "FUNDED"),
                                exit_cfg=l2_cfg(), agent_managed=agents_on)
    elif arm:
        # ARMED: the same execution layer the practice days certified, pointed at the
        # real DTC route. Without this branch an "armed" run would silently fall back
        # to shadow execution (journal-only placements) — the operator believing money
        # is routing while nothing is. Wired in the certified commit, never before it.
        from scripts.build_l2_outcomes import l2_cfg
        execution = NYExecution(mode="armed", broker=broker,
                                account=sc.get("account", "FUNDED"),
                                exit_cfg=l2_cfg(), agent_managed=agents_on)
    live = NYLive(
        feed=feed, data_dir=data_dir, runner=runner, detector=LiveDetector(),
        ingestor=ingestor, instrument=instrument, account=sc.get("account", "FUNDED"),
        buffer=buffer, equity=equity, root=root, suffix=suffix, alerts=alerts,
        kill_file=kill_file,
        execution=execution, replay_day=replay_day,
        decision_sink=JsonlSink(out / "decisions.jsonl"),
        action_sink=JsonlSink(out / "ny_actions.jsonl"),
        verdict_sink=JsonlSink(out / "ny_verdicts.jsonl"),
        fixture_sink=JsonlSink(out / "fixtures.jsonl"),
        armed=arm)

    if agents_on and execution is not None:
        from src.live.agent_desk import AgentDesk, call_claude
        runs_live = Path("runs/live")
        runs_live.mkdir(parents=True, exist_ok=True)
        # LIVE appends to the real journal (the seed grows — that IS the learning
        # loop). A REPLAY must never pollute the seed: it journals to the cert
        # evidence dir, primed with a copy of the seed so the digest context is real.
        jpath, tdir = runs_live / "journal.jsonl", runs_live / "transcripts"
        if replay_day is not None:
            jpath, tdir = out / "agent_journal.jsonl", out / "agent_transcripts"
            seed = runs_live / "journal.jsonl"
            if not jpath.exists() and seed.exists():
                import shutil
                jpath.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(seed, jpath)
        call_fn = call_claude
        if agent_kill_test:
            # R15 kill-test (§7 row 8): from the SECOND agent call on, the CLI process
            # is killed ~1s after launch — a genuinely dead brain mid-trade. The trade
            # must complete mechanically; the parse degrades to hold by construction.
            import subprocess as _sp
            calls = {"n": 0}

            def call_fn(prompt, session, *, cwd, spec=None, timeout=None):
                calls["n"] += 1
                if calls["n"] <= 1:
                    return call_claude(prompt, session, cwd=cwd)
                cmd = ["claude", "-p", "--disallowedTools", "*",
                       "--output-format", "json", prompt]
                try:
                    pr = _sp.Popen(cmd, stdout=_sp.PIPE, stderr=_sp.PIPE, cwd=str(cwd))
                    import time as _t
                    _t.sleep(1.0)
                    pr.kill()                       # the agent process DIES mid-call
                except Exception:                   # noqa: BLE001
                    pass
                return "__ERROR__ agent process killed (kill-test)", session
        live.desk = AgentDesk(
            execution=execution, exit_cfg=execution.exit_cfg,
            journal_path=jpath, transcripts_dir=tdir,
            runs_cwd=runs_live, journal_sink=live.decision_sink,
            sync=(replay_day is not None), call_fn=call_fn,
            # trade-level alerts only for a REAL armed session — a practice-day cert
            # replay shouldn't page anyone's phone for a simulated trade
            alert_sink=(alerts.say if arm else None))
        log.info("R15 agent desk ON (sync=%s, kill_test=%s)",
                 replay_day is not None, agent_kill_test)

    wu = sc.get("warmup", {}) or {}
    if wu.get("parquet"):
        hist = pd.read_parquet(wu["parquet"])
        # reference parquet is NY-tz; live bars are UTC. Mixed zones make ts_event
        # object-dtype and the first feature_row raises — normalize on the way in.
        hist = hist.assign(ts_event=pd.to_datetime(hist.ts_event, utc=True))
        sess = pd.Timestamp(wu.get("session", today), tz=NY)
        lo = sess - pd.Timedelta(days=int(wu.get("warmup_days", 20)))
        hist = hist[(hist.ts_event >= lo.tz_convert("UTC"))
                    & (hist.ts_event < sess.tz_convert("UTC"))]
        fp = pd.read_parquet(wu["footprint"]) if wu.get("footprint") else None
        live.warm(hist, fp)
        log.info("warm start: %d bars", len(hist))
    return live


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/live.yaml")
    ap.add_argument("--telegram", choices=("on", "off"), default="on")
    ap.add_argument("--arm", action="store_true")
    ap.add_argument("--dryrun", action="store_true",
                    help="R13 practice mode: real feed, simulated fills (DryRunBroker)")
    ap.add_argument("--agents", action="store_true",
                    help="R15: agent trade management ON (also via ny.agents in config)")
    ap.add_argument("--agent-kill-test", action="store_true",
                    help="R15 cert: kill the agent process mid-trade; the trade must "
                         "complete mechanically (with --dryrun --agents)")
    ap.add_argument("--replay-day", default=None,
                    help="with --dryrun: act on this historical day (YYYY-MM-DD) from "
                         "the box's own .scid — the certification practice day")
    a = ap.parse_args(argv)
    if a.replay_day and not a.dryrun:
        raise SystemExit("--replay-day requires --dryrun")
    if a.arm and a.dryrun:
        raise SystemExit("--arm and --dryrun are mutually exclusive")

    cfg = load_config(Path(a.config))
    paths = cfg.get("paths", {}) or {}
    log = setup_logging(Path(paths.get("run_log", "runs/ny_run.log")))
    alerts = build_alerts(cfg, log, force_off=(a.telegram == "off"))

    live = build_ny_live(cfg, alerts, log, arm=a.arm, config_path=a.config,
                         dryrun=a.dryrun, replay_day=a.replay_day,
                         agents=(True if a.agents else None),
                         agent_kill_test=a.agent_kill_test)
    live.decision_sink({"type": "boot", "git_sha": _git_sha(), "armed": a.arm,
                        "entry": "ny_run"})

    state = {"stop": False}
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: state.update(stop=True))
    alerts.say(f"ny_run START ({'ARMED' if a.arm else 'DISARMED shadow'})")
    live.serve(sleep_fn=time.sleep,
               poll_interval_s=float((cfg.get("feed", {}).get("sierra", {})
                                      or {}).get("poll_interval_s", 1.0)),
               stop_fn=lambda: state["stop"])
    if live.desk is not None:
        live.desk.finalize()                  # flush pending agent journal rows
    alerts.say("ny_run STOP")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
