"""The LIVE NY canon lane — candidate fill in, verdict out, computed at fill time.

This is the cut-over path for the rebuilt canon. The old lane
(`src/desk/canon_lane.py::ScriptVerdictSource`) shells out to the old canon's batch scripts
and hands back a whole day's book; that shape cannot carry the new canon, because the new
canon's decisions depend on state that only exists at the moment of the fill:

  * the daily risk BUDGET consumes realized P&L and in-flight risk as the session runs, so a
    verdict computed at 08:00 for a 10:15 fill would be sized against a budget that no longer
    exists;
  * the elite 2.0x slot is spent by whichever qualifying trade fills FIRST;
  * `struct_event` is an observation of what price did while the order rested.

So this lane is event-driven: `CanonIngestor` keeps rolling state, and on each candidate fill
we assemble that trade's feature row with backtest-identical definitions
(`src/canon/features.py`) and score it with `NYScorerV2` — the same class the conformance
suite proves reproduces `scripts/funded_book.py` exactly.

FAIL-CLOSED BY CONSTRUCTION: a missing feature yields a MISSING KEY from the ingestor, which
reads as NaN here, which stands the corresponding check down. W and D are NaN-guarded, so an
absent depth book means the gate cannot be satisfied and the trade is refused. Nothing is
fabricated to let a trade through.

THE `on_extreme_age` TRAP: the ingestor deliberately emits TWO keys, because gold and London
were fit against different features that share that column name upstream. Gold's AGE is
`on_extreme_age_day` (the completed 18:00-08:00 overnight tape); `on_extreme_age_trade` is
London's per-trade wall-clock form. This lane maps the DAY form and nothing else — see
scripts/score_canon_span.py:164. Mapping the wrong one silently changes a score component.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import time as dtime

import pandas as pd

from src.canon.scorer_ny import LUCID, NYScorerV2, Profile, session_of
from src.engine.data import _session_date

NY_TZ = "America/New_York"
_BOUNDARY = dtime(18, 0)

#: session window ends, for the order watch (no distance cancel — window expiry only)
WINDOW_END = {"pre": dtime(9, 30), "gold": dtime(10, 30)}


def normalize_trigger_times(trigger_times):
    """Trigger stamps as `badpa_features` needs them: NAIVE numpy datetime64 in UTC.

    The batch feeds it `pd.to_datetime(..., utc=True).tz_localize(None).to_numpy()`
    (scripts/score_canon_span.py:323) and `badpa_features` compares against
    `fill.to_datetime64()`, which is also naive-UTC. A live caller handing over tz-aware
    stamps either raises or — far worse — miscounts silently, and trigdens_30 is a score
    component. So the conversion lives here rather than in every call site.

    Returns None for an empty input, which leaves `trigdens_30` ABSENT so the TRIG component
    stands down instead of scoring a fabricated zero density."""
    if trigger_times is None:
        return None
    arr = pd.DatetimeIndex(pd.to_datetime(list(trigger_times), utc=True))
    if len(arr) == 0:
        return None
    return arr.tz_localize(None).to_numpy()


def session_day(fill_ts) -> str:
    """The canon's session date for a fill (18:00 boundary), as the batch computes it."""
    return str(_session_date(pd.Series([pd.Timestamp(fill_ts)]), _BOUNDARY).iloc[0])


def scorer_row(features: dict, *, fill_ts, entry: float, stop: float, direction: str,
               struct_event: str = "", risk_pts: float | None = None) -> dict:
    """Map an ingestor feature row onto the scorer's input row.

    Everything the ingestor produces passes through untouched; this adds only what the
    ingestor does not own (the trade's own geometry and clock) and resolves the two
    `on_extreme_age` forms to gold's.

    `risk_pts` — THE STOP DISTANCE THE TRADE IS ACTUALLY SIZED ON. Pass it explicitly from
    the bracket as placed. It is NOT reliably `|entry - stop|`: in the validated dataset those
    two disagree on 28% of trades (up to tens of points), because `entry`/`stop` are the
    trigger's REFERENCE levels while the canon sized on the engine's realized bracket
    (limit_price vs stop_initial). Risk feeds both the 7-60pt Layer-0 gate and the micros
    calculation, so getting it from the wrong place changes which trades are taken AND how
    big they are. When omitted it falls back to `|entry - stop|` and the verdict records
    `risk_source="bracket"` so the journal shows an inferred value was used."""
    fill = pd.Timestamp(fill_ts)
    et = fill.tz_convert(NY_TZ) if fill.tzinfo is not None else fill.tz_localize(NY_TZ)
    row = dict(features)
    row["day"] = session_day(fill)
    row["fill"] = fill
    row["fill_hm"] = et.hour * 60 + et.minute
    row["direction"] = direction
    row["risk"] = (abs(float(entry) - float(stop)) if risk_pts is None
                   else abs(float(risk_pts)))
    row["struct_event"] = struct_event or ""
    # gold's AGE input, explicitly. Absent -> NaN -> the AGE component scores 0, never a guess.
    row["on_extreme_age"] = features.get("on_extreme_age_day", math.nan)
    return row


@dataclass
class NYLane:
    """Event-driven live canon lane. One instance per trading account.

    Wiring, per session day:
        lane.start_day(day, buffer=equity - trailing_line)
    Per candidate fill (the entry limit just filled, or is about to):
        v = lane.on_candidate(fill_ts=..., entry=..., stop=..., direction=...,
                              trigger_times=<the day's trigger stamps>,
                              struct_event=<order_watch.struct_event(ref)>)
        if v["take"]: route v to the agents / spine; then lane.confirm(v)
    On exit:
        lane.on_exit(v, pl=<realized dollars>)
    """
    ingestor: object
    profile: Profile = LUCID
    news_gate: object | None = None
    account: str = "FUNDED"
    scorer: NYScorerV2 = field(init=False)
    _verdicts: dict = field(default_factory=dict, init=False)
    _next_id: int = field(default=0, init=False)

    def __post_init__(self):
        self.scorer = NYScorerV2(profile=self.profile, news_gate=self.news_gate)

    def start_day(self, day: str, *, buffer: float) -> None:
        self.scorer.start_day(str(day), buffer=float(buffer))

    def on_candidate(self, *, fill_ts, entry: float, stop: float, direction: str,
                     trigger_times=None, struct_event: str = "",
                     risk_pts: float | None = None) -> dict:
        """Assemble features, score, and return a VERDICT dict in the shape the relay and the
        spine already consume (`src/desk/canon_lane.py`), plus the audit fields.

        `take=False` verdicts are returned too, never swallowed: a refusal with its reason is
        the evidence that the lane saw the signal and declined it."""
        feats = self.ingestor.feature_row(fill_ts, float(entry), direction,
                                          trigger_times=normalize_trigger_times(trigger_times))
        row = scorer_row(feats, fill_ts=fill_ts, entry=entry, stop=stop,
                         direction=direction, struct_event=struct_event, risk_pts=risk_pts)
        v = self.scorer.evaluate(row)
        out = {
            "session": "NY", "window": v.session, "day": v.day,
            "fill": pd.Timestamp(fill_ts).isoformat(),
            "direction": direction, "entry": float(entry), "stop": float(stop),
            "target": None,                       # managed exit — no fixed bracket target
            "conviction": v.tier, "risk_pts": v.risk_pts, "micros": v.micros,
            "risk_source": "explicit" if risk_pts is not None else "bracket",
            "risk_dollars": v.risk_dollars, "elite": v.elite, "score": v.score,
            "take": bool(v.taken), "reasons": list(v.reasons),
            "window_end": WINDOW_END.get(v.session).isoformat() if v.session in WINDOW_END
            else None,
            "base": v.base, "budget": v.budget, "pl": None,
        }
        # A monotonic handle, NOT (fill, direction): sibling triggers off one cluster share a
        # fill minute AND a direction routinely, and keying on those silently dropped the
        # first verdict of a colliding pair — its risk then never left the budget.
        self._next_id += 1
        out["vid"] = self._next_id
        if v.taken:
            self._verdicts[out["vid"]] = v
        return out

    def confirm(self, verdict: dict) -> None:
        """The entry FILLED — register its risk as in-flight so it consumes budget room."""
        v = self._verdicts.get(verdict.get("vid"))
        if v is None:
            raise RuntimeError("confirm() for a verdict this lane did not take")
        self.scorer.commit(v)

    def on_exit(self, verdict: dict, *, pl: float) -> None:
        """The position CLOSED — realize its P&L and free its budget room."""
        v = self._verdicts.pop(verdict.get("vid"), None)
        if v is None:
            raise RuntimeError("on_exit() for an unknown verdict")
        self.scorer.on_exit(v, pl=float(pl))
        verdict["pl"] = float(pl)

    def status(self) -> dict:
        return {"account": self.account, **self.scorer.status()}


def in_canon_window(fill_ts) -> bool:
    """True when a candidate fill lands in a canon session window at all. Cheap pre-filter so
    the lane is not asked to build features for out-of-window candidates."""
    fill = pd.Timestamp(fill_ts)
    et = fill.tz_convert(NY_TZ) if fill.tzinfo is not None else fill.tz_localize(NY_TZ)
    return session_of(et.hour * 60 + et.minute) in ("pre", "gold")
