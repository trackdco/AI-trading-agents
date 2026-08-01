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
STALE_BAR_S = 120.0                    # catch-up guard, same constant as route_b's verdict wall


def _profile(name: str):
    if name == "lucid":
        return LUCID
    if name == "scaled600":
        return SCALED600
    raise SystemExit(f"ny.profile must be lucid or scaled600, got {name!r}")


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

    guard: FeedGuard = None
    watcher: RollWatcher = None
    roll_state: RollState = None
    _day: str | None = field(default=None, init=False)
    _seen: set = field(default_factory=set, init=False)
    _positions: dict = field(default_factory=dict, init=False)   # ref -> _Position
    _last_bar_ts: pd.Timestamp | None = field(default=None, init=False)
    _acct_fn: object = field(default=None, init=False)
    _feed_fn: object = field(default=None, init=False)

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
        self._positions.pop(ref, None)
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
                # submission failed: un-rest the candidate so a later bar re-places it
                c = self.runner._cands.get(a["ref"])
                if c is not None:
                    c.resting, c.size = False, 0
                    self.runner.watch.mark_gone(a["ref"])
                self._journal({"type": "placement_failed_unrested", "ref": a["ref"]})

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
        return res

    def on_position_closed(self, ref: str, *, pl: float) -> None:
        self._close_position(ref, pl=pl, reason="exit_manager")

    # ---------------------------------------------------------------- per-bar dispatch
    def _start_day_if_new(self, ts: pd.Timestamp) -> None:
        day = session_day(ts)
        if day != self._day:
            self._day = day
            self._seen.clear()
            self._positions.clear()
            # R13: armed multi-day use must replace this with the broker account
            # read-back (equity - trailing_line per session), not the boot-time value.
            self.runner.start_day(day, buffer=float(self.buffer))
            self._journal({"type": "ny_day_start", "day": day, "buffer": self.buffer})
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
                    if session_day(bts) != self.replay_day:
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
                    self._rule_k_flatten(bts, bar_open=float(gbar["open"]))
                    # LiveDetector's 07:45-11:00 band is ET WALL TIME (proven against
                    # NY-tz reference frames); Sierra bars arrive UTC. Convert at this
                    # boundary or wants() never passes during the session.
                    bts_ny = bts.tz_convert(NY)
                    bar = Bar(ts_event=bts_ny, open=float(gbar["open"]),
                              high=float(gbar["high"]), low=float(gbar["low"]),
                              close=float(gbar["close"]), volume=float(gbar["volume"]))
                    df = self.ingestor.bars_frame()
                    if len(df):
                        df = df.assign(
                            ts_event=pd.to_datetime(df.ts_event).dt.tz_convert(NY))
                    for trig in self.detector.on_bar(df, bar):
                        key = _trigger_key(trig)
                        if key in self._seen:
                            continue
                        self._seen.add(key)
                        self._execute(self.runner.on_trigger(trig), bts)
                    self._execute(self.runner.on_bar(bts, float(gbar["high"]),
                                                     float(gbar["low"])), bts)
                    for f in self.execution.poll_fills():
                        self.on_fill(f["ref"], f["ts"], int(f["size"]))
                    if self.execution.live:
                        df_all = self.ingestor.bars_frame()
                        if len(df_all):
                            df_all = df_all.assign(ts_event=pd.to_datetime(
                                df_all.ts_event).dt.tz_convert(NY))
                        self.execution.on_bar(df_all, bts_ny)
                except Exception as e:         # noqa: BLE001 — capture night: a crashed
                    # loop at 09:00 loses the session's evidence; journal loudly, keep
                    # ingesting. Runner state may be inconsistent for THIS candidate —
                    # the journal row is the flag to investigate before certifying.
                    self._journal({"type": "dispatch_error", "ts": str(bts),
                                   "error": repr(e)})
                    self._say(f"WARN dispatch error at {bts}: {e}")

    # ---------------------------------------------------------------- loop
    def _maybe_retarget(self, now: pd.Timestamp) -> None:
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
            self._say(f"contract ROLL: {ev}")

    def warm(self, bars_df: pd.DataFrame, footprint_df: pd.DataFrame | None = None):
        from src.canon.feed_guard import warm_start
        if footprint_df is not None:
            warm_start(self.ingestor, bars_df, footprint_df)
        else:
            for _, row in bars_df.iterrows():
                self.ingestor.on_bar(dict(row))

    def poll_once(self, now: pd.Timestamp | None = None) -> bool:
        now = self.clock() if now is None else now
        self._maybe_retarget(now)
        self.dispatch(self.feed.poll_events(), now)
        return self.guard.check_stale(now)

    def serve(self, sleep_fn, poll_interval_s: float = 1.0, max_polls=None, stop_fn=None):
        self._say(f"NY canon loop {'ARMED' if self.armed else 'DISARMED (shadow)'} — "
                  f"git {_git_sha()}")
        polls, boot, warned_no_bars = 0, self.clock(), False
        while max_polls is None or polls < max_polls:
            if stop_fn is not None and stop_fn():
                break
            if self.kill_file is not None and Path(self.kill_file).exists():
                self._say("KILL file present — stopping the NY loop")
                self._journal({"type": "kill_file_stop"})
                break
            if self.poll_once():
                self._say("feed STALLED — halting (fail closed)")
                break
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
                  dryrun: bool = False, replay_day: str | None = None) -> NYLive:
    if arm:
        # R13 WIRING IS BUILT (src/live/ny_execution.py: cancel routing, scratch
        # close, rule J/K order submission, canon exit engine binding, dry-run broker)
        # but NOT YET CERTIFIED on the box. The gate comes off in the certified commit,
        # after the practice day (`--dryrun --replay-day <d>`) and the DTC fill-detection
        # pin (`_entry_working`) pass on real Sierra order updates. Refused BY
        # CONSTRUCTION until then.
        raise SystemExit(
            "ARM REFUSED: R13 wiring built but not certified on the box. Run the "
            "practice day (--dryrun --replay-day <day>) per docs/ARMING-REFERENCE.md "
            "R13; the refusal comes off in the certified commit.")

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
    scid = Path(sc["scid"]) if sc.get("scid") else resolve_scid_path(
        data_dir, now, root, suffix)
    depth = resolve_depth_path(data_dir, now, day=today, root=root, suffix=suffix)
    depth_ok = depth is not None and Path(depth).exists()
    feed = SierraFileFeed(scid, depth if depth_ok else None,
                          flush_ms=int(sc.get("flush_ms", 1000)))
    if not depth_ok:
        alerts.say(f"no .depth file for {today} yet — depth features stand down until "
                   "it appears (retargeted automatically each poll)")

    ingestor = CanonIngestor(book=DepthBook())
    lane = NYLane(ingestor=ingestor, profile=_profile(ny.get("profile", "lucid")),
                  news_gate=NewsGate.load(), account=sc.get("account", "FUNDED"))
    runner = NYRunner(lane=lane)

    broker, token = None, None
    if arm:
        token = _collect_arm_token()
        try:
            auth = verify_for_arming(token)
        except ArmingError as e:
            raise SystemExit(f"ARM REFUSED: {e}")
        broker, _client = build_armed_broker(cfg, auth, log)
    spine_cfg = load_spine_config(config_path)     # pinned Tier-1 (F6: honour --config)
    instrument = build_shadow_instrument(out, account=sc.get("account", "FUNDED"),
                                         cfg=spine_cfg, kill_file=kill_file,
                                         broker=broker, arm_token=token)
    if arm and not instrument.spine.arm(token):
        raise SystemExit("ARM REFUSED: spine token mismatch")

    execution = None
    if dryrun:
        from scripts.build_l2_outcomes import l2_cfg    # the canon exit config (V8)
        execution = NYExecution(mode="dryrun", broker=DryRunBroker(),
                                account=sc.get("account", "FUNDED"),
                                exit_cfg=l2_cfg())
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
                         dryrun=a.dryrun, replay_day=a.replay_day)
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
    alerts.say("ny_run STOP")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
