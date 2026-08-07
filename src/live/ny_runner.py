"""NYRunner — the live orchestrator that joins detector -> orders -> lane -> verdicts.

This is the module that makes the rebuilt canon TRADEABLE: it connects the production
trigger detector, the order watch (struct events, cancels), and the NY lane (features ->
scorer) into one per-bar decision stream. It DECIDES and never touches a broker — every
output is an ACTION the caller executes and journals, the same contract as OrderWatch.

THE RESTING RULE (read this before changing anything): an entry limit rests exactly while a
fill RIGHT NOW would be admissible — in a canon window AND the lane's current evaluation says
take. This is the faithful live mapping of how the book was measured:

  * L1 walked every trigger's limit to its fill with NO cancel; the verdict then gated by
    the FILL minute. A pre-window trigger whose limit filled at 09:50 is a GOLD trade in the
    book — so orders must NOT die at their birth-window's end; they go dormant through the
    09:30-09:40 gap and come back if the gold evaluation admits them (ANGUS: replace-with-
    freshest, both directions).
  * The budget is fill-time state. A resting order whose room was consumed by an earlier
    fill MUST come down before it can fill — `evaluate` is pure precisely so it can be
    re-asked every closed bar.
  * Nothing is admissible at/after 10:30, so every candidate is dropped there for good.

Evaluation timing: at each closed bar the lane is asked about a fill at bar_close + 1min —
the EARLIEST minute a fill could land — with features as-of now. `feature_row` windows end at
fill-1min, so this uses exactly the state through the just-closed bar: causally identical to
the batch.

Sizing while resting: the resting size tracks the CURRENT evaluation's micros
(replace-with-freshest). At the fill, the runner re-evaluates AT the actual fill minute with
the order's observed `struct_event`; that verdict is the one committed. If the filled size
differs from the final verdict's micros (a one-bar race), the fill stands at its size and the
drift is reported for the journal — sizes are never silently rewritten after the fact.

THE SCRATCH RACE: if the final fill-minute evaluation REFUSES a fill that landed anyway
(state moved inside the last bar — budget consumed, news window opened), the runner returns
a `scratch` action: the position must be closed immediately and journaled. The book never
paid for these because it gated at fill with zero cost; live, the scratch is the honest
price of that idealisation, and it must be VISIBLE, never absorbed.

Wiring (Pat):

    runner = NYRunner(lane=NYLane(ingestor=ing, profile=LUCID, news_gate=gate))
    runner.start_day(day, buffer=equity - trailing_line)
    acts = runner.on_trigger(trigger)                  # from LiveDetector.on_bar
    acts = runner.on_bar(ts, high, low)                # every closed 1m bar
    res  = runner.on_fill(ref, fill_ts, filled_size)   # broker fill (or shadow fill)
    runner.on_position_closed(ref, pl=realized)        # exit manager's realized dollars

Every action dict carries {"action": place|cancel|modify_size|scratch, "ref": ..., ...}.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time as dtime

import pandas as pd

from src.canon.ny_lane import NYLane, session_day
from src.canon.order_watch import OrderWatch
from src.canon.scorer_ny import GOLD_WIN

NY_TZ = "America/New_York"
TICK = 0.25
#: no candidate survives past the gold window's end — nothing is admissible after it
FINAL_END = GOLD_WIN[1]


def _round_tick(x: float, tick: float = TICK) -> float:
    return round(round(float(x) / tick) * tick, 10)


def bracket_for(trigger) -> tuple[float, float]:
    """The E3 bracket exactly as the engine places it (src/backtest/engine.py): limit =
    tick-rounded entry_ref, stop = tick-rounded stop_ref. The book's `risk` column IS
    |limit - stop| in this form — this is the derivation that closes the 28% reference-level
    trap, so the ARMED path must place THIS bracket, not the raw refs."""
    return (_round_tick(trigger.entry_ref), _round_tick(trigger.stop_ref))


@dataclass
class _Cand:
    ref: str
    trigger: object
    side: str                    # "B" | "S"
    limit: float
    stop: float
    risk_pts: float
    resting: bool = False
    filled: bool = False         # a filled candidate is a POSITION — never reconciled again
    size: int = 0
    verdict: dict | None = None  # last evaluation (for the journal)


@dataclass
class NYRunner:
    lane: NYLane
    watch: OrderWatch = None
    _cands: dict = field(default_factory=dict, init=False)
    _trig_times: list = field(default_factory=list, init=False)
    _seq: int = field(default=0, init=False)
    _day: str | None = field(default=None, init=False)

    def __post_init__(self):
        if self.watch is None:
            # no distance cancel; the runner itself pulls inadmissible orders, so the
            # watch's own window is the final end for everything it still holds.
            self.watch = OrderWatch(t_cancel=None, win_start=dtime(7, 45),
                                    win_end=dtime(FINAL_END // 60, FINAL_END % 60),
                                    eod_flatten=dtime(15, 55))

    # ---- day boundary ---------------------------------------------------------------
    def start_day(self, day: str, *, buffer: float) -> None:
        self.lane.start_day(day, buffer=buffer)
        self._cands.clear()
        self._trig_times.clear()
        self._day = str(day)

    # ---- trigger -> candidate -------------------------------------------------------
    def on_trigger(self, trigger) -> list[dict]:
        """Register a detector trigger as a candidate. Its timestamp feeds trigdens_30 —
        the live census IS the detector's own output, the same stamps the batch counted.
        Returns the immediate actions (usually a place, if the first evaluation admits)."""
        ts = pd.Timestamp(trigger.ts)
        ts = ts.tz_localize(NY_TZ) if ts.tzinfo is None else ts.tz_convert(NY_TZ)
        if self._day is None:
            raise RuntimeError("start_day() before on_trigger()")
        if session_day(ts) != self._day:
            raise RuntimeError(f"trigger day {session_day(ts)} != runner day {self._day}")
        self._trig_times.append(ts.tz_convert("UTC"))
        limit, stop = bracket_for(trigger)
        side = "B" if trigger.direction == "long" else "S"
        risk = (limit - stop) if side == "B" else (stop - limit)
        self._seq += 1
        ref = f"ny:{self._day}:{self._seq}"
        cand = _Cand(ref=ref, trigger=trigger, side=side, limit=limit, stop=stop,
                     risk_pts=risk)
        self._cands[ref] = cand
        return self._reconcile(cand, ts)

    # ---- the per-bar decision -------------------------------------------------------
    def on_bar(self, ts, high: float, low: float) -> list[dict]:
        """Drive the watch (struct events + terminal cancels) and reconcile every candidate
        against a fresh evaluation. Call on every CLOSED 1m bar, after the ingestor has
        consumed it."""
        ts = pd.Timestamp(ts)
        ts = ts.tz_localize(NY_TZ) if ts.tzinfo is None else ts.tz_convert(NY_TZ)
        acts: list[dict] = []
        for d in self.watch.on_bar(ts, high, low):     # struct tracking + terminal cancels
            c = self._cands.pop(d["ref"], None)
            if c is not None and c.resting:
                acts.append({"action": "cancel", "ref": d["ref"], "why": d["reason"]})
        for c in list(self._cands.values()):
            if not c.filled:                           # positions are the exit manager's
                acts += self._reconcile(c, ts)
        return acts

    def _hm(self, ts: pd.Timestamp) -> int:
        et = ts.tz_convert(NY_TZ)
        return et.hour * 60 + et.minute

    def _reconcile(self, c: _Cand, now: pd.Timestamp) -> list[dict]:
        """Make the order state match the CURRENT evaluation: place / cancel / resize."""
        nxt = now + pd.Timedelta(minutes=1)            # earliest possible fill minute
        if self._hm(nxt) >= FINAL_END:                 # nothing ahead is admissible: done
            self._cands.pop(c.ref, None)
            self.watch.mark_gone(c.ref)
            return ([{"action": "cancel", "ref": c.ref, "why": "no_window_ahead"}]
                    if c.resting else [])
        v = self.lane.on_candidate(
            fill_ts=nxt.tz_convert("UTC"), entry=c.limit, stop=c.stop,
            direction="long" if c.side == "B" else "short",
            trigger_times=list(self._trig_times),
            struct_event=self.watch.struct_event(c.ref), risk_pts=c.risk_pts)
        c.verdict = v
        if v["take"] and not c.resting:
            c.resting, c.size = True, v["micros"]
            self.watch.register(c.ref, c.side, c.limit,
                                levels=self._levels(c.trigger), close=c.trigger.close)
            return [{"action": "place", "ref": c.ref, "side": c.side, "limit": c.limit,
                     "stop": c.stop, "size": v["micros"], "verdict": v}]
        if not v["take"] and c.resting:
            c.resting, c.size = False, 0
            # dormant, not dead: mark_gone stops the watch cancelling it, but the candidate
            # stays for re-placement if a later evaluation re-admits it (freshest wins).
            self.watch.mark_gone(c.ref)
            return [{"action": "cancel", "ref": c.ref,
                     "why": ",".join(v["reasons"]) or "refused"}]
        if v["take"] and c.resting and v["micros"] != c.size:
            old, c.size = c.size, v["micros"]
            return [{"action": "modify_size", "ref": c.ref, "size": v["micros"],
                     "was": old, "verdict": v}]
        return []

    @staticmethod
    def _levels(trigger) -> list:
        import json
        raw = getattr(trigger, "level_stack", "") or ""
        try:
            return json.loads(raw) if raw else []
        except (ValueError, TypeError):
            return []

    # ---- fills and exits ------------------------------------------------------------
    def on_fill(self, ref: str, fill_ts, filled_size: int) -> dict:
        """The entry FILLED. The verdict of record is the evaluation AT the fill minute,
        with the struct event observed while the order rested. Returns either
        {"action": "commit", "verdict": ..., "size_drift": int} or
        {"action": "scratch", "why": ...} — a scratch means close the position NOW."""
        c = self._cands.get(ref)
        if c is None or not c.resting:
            return {"action": "scratch", "ref": ref,
                    "why": "fill_for_unknown_or_pulled_order"}
        self.watch.mark_filled(ref)
        fill = pd.Timestamp(fill_ts)
        fill = fill.tz_localize(NY_TZ) if fill.tzinfo is None else fill
        v = self.lane.on_candidate(
            fill_ts=fill.tz_convert("UTC"), entry=c.limit, stop=c.stop,
            direction="long" if c.side == "B" else "short",
            trigger_times=list(self._trig_times),
            struct_event=self.watch.struct_event(ref), risk_pts=c.risk_pts)
        if not v["take"]:
            self._cands.pop(ref, None)
            self.watch.mark_gone(ref)
            return {"action": "scratch", "ref": ref,
                    "why": ",".join(v["reasons"]) or "refused_at_fill"}
        self.lane.confirm(v)
        c.verdict, c.resting, c.filled = v, False, True
        return {"action": "commit", "ref": ref, "verdict": v,
                "size_drift": int(filled_size) - int(v["micros"])}

    def on_position_closed(self, ref: str, *, pl: float) -> None:
        c = self._cands.pop(ref, None)
        if c is None or c.verdict is None or not c.verdict.get("take"):
            raise RuntimeError(f"position close for unknown/uncommitted candidate {ref}")
        self.lane.on_exit(c.verdict, pl=pl)
        self.watch.mark_gone(ref)

    # ---- introspection --------------------------------------------------------------
    def trigger_for(self, ref: str):
        """The committed candidate's originating detector trigger (R15: the agent's
        NEW-POSITION briefing carries its pattern). None if the candidate is gone."""
        c = self._cands.get(ref)
        return c.trigger if c is not None else None

    def status(self) -> dict:
        return {**self.lane.status(),
                "candidates": len(self._cands),
                "resting": sum(1 for c in self._cands.values() if c.resting),
                "triggers_today": len(self._trig_times)}
