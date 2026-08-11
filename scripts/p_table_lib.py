"""P-TABLE build library — SPEC-pxl-p-table.md Part B.

Pure, deterministic functions: the gate harness re-runs `run_session` on perturbed
minute inputs, so nothing in here may read the wall clock, global state, or any bar
later than the value it claims to be as-of.

Every declared parameter lives in CONFIG. Declared conventions that the SPEC left to
implementation are marked "# DECLARED:" and are echoed in the build report.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import date as Date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
LONDON = ZoneInfo("Europe/London")
UTC = timezone.utc
TICK = 0.25

CONFIG = {
    "MIN_LEG_RETRACE": 0.382,           # A2.1 placeholder, pending ruling
    "MIN_LEG_RETRACE_SENSITIVITY": [0.236, 0.382, 0.5],
    "STRUCT_N": 2,                       # A3
    "STOP_BUFFER_PTS": 2.0,              # A6 base
    "STOP_BUFFER_ATR_FRACS": {"atr015": 0.15, "atr025": 0.25, "atr033": 0.33},
    "STOP_BUFFER_ATR_FLOOR_PTS": 1.0,    # A6: 4 ticks
    "TRADE_THROUGH_TICKS": 1,            # A5 base fill rule
    "STRESS_TRADE_THROUGH_TICKS": 2,     # A5 stress
    "COST_RT_PTS": 0.5,                  # A9, inside the R numerator
    "TFS_MIN": [1, 2, 3, 5],             # A1.1
    "RESOLUTION_TF_MIN": 5,              # mode (b): resolve at the 5m boundary
    "WICK_TOP_MODE": "body",             # DA-3, ruled
    "ATR_PERIOD": 14,
    "SESSIONS": {
        # session -> (warmup_start, session_start, session_end, tz)
        "ny_am": (time(8, 0), time(9, 30), time(11, 30), "America/New_York"),
        # DA-4 (declarations file): london implemented as 08:00-12:00 Europe/London
        "london": (time(7, 0), time(8, 0), time(12, 0), "Europe/London"),
    },
    "MIN_REAL_MINUTE_FRAC": 0.90,        # exclusion criterion: session processed only if
                                         # >=90% of nominal minutes are real bars
    "FIT_END_DATE": "2025-05-31",        # DECLARATIONS entry 1
    "FILL_RULE_VERSION": "v1_tt1",
    "RESOLUTION_MODE": "wait_5m_close",
}


def tick_round(x: float) -> float:
    return round(round(x * 4) / 4, 2)


# --------------------------------------------------------------------------- bars

@dataclass
class Bar:
    open_ts: datetime
    close_ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    real: bool = True          # False for flat filler minutes


def session_window_utc(d: Date, session: str) -> tuple[datetime, datetime, datetime]:
    w, s, e, tzname = CONFIG["SESSIONS"][session]
    tz = ZoneInfo(tzname)
    return (
        datetime.combine(d, w, tz).astimezone(UTC),
        datetime.combine(d, s, tz).astimezone(UTC),
        datetime.combine(d, e, tz).astimezone(UTC),
    )


def build_session_minutes(minute_map: dict[datetime, tuple], d: Date, session: str):
    """Minute grid from warm-up start to session end; missing minutes become flat
    filler bars at the previous close (the same convention the perturbation gates
    use). Returns (bars, n_real, n_total) or None if there is no leading real bar
    or the real fraction is below the exclusion criterion."""
    w_utc, s_utc, e_utc = session_window_utc(d, session)
    n_total = int((e_utc - w_utc).total_seconds() // 60)
    bars: list[Bar] = []
    prev_close = None
    n_real = 0
    t = w_utc
    for _ in range(n_total):
        row = minute_map.get(t)
        if row is not None:
            o, h, l, c, v = row
            bars.append(Bar(t, t + timedelta(minutes=1), o, h, l, c, v, True))
            prev_close = c
            n_real += 1
        elif prev_close is not None:
            bars.append(Bar(t, t + timedelta(minutes=1), prev_close, prev_close,
                            prev_close, prev_close, 0.0, False))
        else:
            bars = []  # skip leading gap; grid starts at first real minute
        t += timedelta(minutes=1)
    if not bars or n_real < CONFIG["MIN_REAL_MINUTE_FRAC"] * n_total:
        return None
    return bars, n_real, n_total


def aggregate_tf(minutes: list[Bar], k: int) -> list[Bar]:
    """k-minute bars anchored on the warm-up grid; only complete groups."""
    out = []
    # anchor on the grid position, not on list index, so a trimmed leading gap
    # cannot shift bar boundaries
    if not minutes:
        return out
    for i in range(0, len(minutes) - k + 1):
        b0 = minutes[i]
        if (b0.open_ts.minute % k) if k <= 60 else 0:
            continue
        grp = minutes[i:i + k]
        if len(grp) < k or grp[-1].close_ts != b0.open_ts + timedelta(minutes=k):
            continue
        out.append(Bar(
            b0.open_ts, grp[-1].close_ts, b0.open,
            max(g.high for g in grp), min(g.low for g in grp),
            grp[-1].close, sum(g.volume for g in grp),
            any(g.real for g in grp)))
    return out


def true_ranges(bars: list[Bar]) -> list[float]:
    trs = []
    for i, b in enumerate(bars):
        if i == 0:
            trs.append(b.high - b.low)
        else:
            pc = bars[i - 1].close
            trs.append(max(b.high - b.low, abs(b.high - pc), abs(b.low - pc)))
    return trs


# ------------------------------------------------------------------- leg tracking

@dataclass
class Pivot:
    kind: str                  # 'H' or 'L'
    px: float
    ts: datetime               # close_ts of the bar printing the extreme
    bar: Bar
    start_px: float            # origin of the leg this pivot terminates
    start_ts: datetime
    leg_height: float
    confirm_ts: datetime       # close_ts of the bar on which the retrace confirmed


@dataclass
class Candidate:
    """A PXL (direction=-1, swing low) or PXH (direction=+1, swing high)."""
    direction: int
    tf: int
    pivot: Pivot
    level_0: float             # wick outer edge (low for PXL, high for PXH)
    level_1: float             # wick inner edge = body boundary (DA-3)
    born_ts: datetime          # confirm_ts
    alive: bool = True
    fate: str = ""             # triggered_* | broken_multibar | broken_not_active |
                               # penetrated | invalidated | session_end
    fate_ts: datetime | None = None
    n_penetrations: int = 0
    born_penetrated: bool = False
    liquidity_intact: bool = True   # no trade beyond level_0 since the pivot bar
    retrace_max: float = 0.0        # max retrace fraction of the leg achieved
    retrace_extreme: float = 0.0    # extreme of the retrace (high for PXL)
    invalidated: bool = False
    invalidation_ts: datetime | None = None
    invalidation_reason: str = ""

    @property
    def wick_width(self) -> float:
        return abs(self.level_1 - self.level_0)

    @property
    def fifty(self) -> float:
        return tick_round((self.level_0 + self.level_1) / 2)


class LegTracker:
    """Alternating-leg swing tracker (SPEC A2). One instance per (session, TF).

    DECLARED conventions:
    - Cold start: the first bar's open is a virtual origin; initial direction is the
      sign of the first bar's body (down if close < open).
    - Within a bar that extends the leg extreme, only (close - extreme) counts toward
      the retrace, because the close is the one print known to come after the
      extreme. Highs/lows of later bars count in full.
    - At most one leg flip per bar (intrabar double-flips are unresolvable).
    - Equal extremes: the FIRST bar printing the extreme is the pivot bar.
    """

    def __init__(self, frac: float, min_height_atr_frac: float = 0.0):
        self.frac = frac
        # ADDITIVE, default-off (0.0 == old behaviour exactly, byte-identical to
        # every previously-built table). Gates PIVOT CONFIRMATION, not just
        # candidate creation: below the floor, the leg keeps extending (does not
        # flip) rather than terminating into an undersized PXL/PXH candidate.
        # Requires atr_val passed into on_bar; NaN (warm-up) never gates.
        self.min_height_atr_frac = min_height_atr_frac
        self.dir = 0
        self.start_px = self.ext_px = self.counter_px = None
        self.start_ts = self.ext_ts = None
        self.ext_bar: Bar | None = None
        self.pivots: list[Pivot] = []

    def on_bar(self, bar: Bar, atr_val: float = float("nan")) -> list[Pivot]:
        if self.dir == 0:
            self.dir = -1 if bar.close < bar.open else 1
            self.start_px, self.start_ts = bar.open, bar.open_ts
            if self.dir == -1:
                self.ext_px, self.counter_px = bar.low, bar.close
            else:
                self.ext_px, self.counter_px = bar.high, bar.close
            self.ext_ts, self.ext_bar = bar.close_ts, bar
            return []
        new: list[Pivot] = []
        if self.dir == -1:
            if bar.low < self.ext_px:
                self.ext_px, self.ext_ts, self.ext_bar = bar.low, bar.close_ts, bar
                self.counter_px = bar.close
            else:
                self.counter_px = max(self.counter_px, bar.high)
            height = self.start_px - self.ext_px
            floor_ok = (self.min_height_atr_frac <= 0 or math.isnan(atr_val)
                       or height >= self.min_height_atr_frac * atr_val)
            if height > 0 and floor_ok and \
                    (self.counter_px - self.ext_px) >= self.frac * height:
                piv = Pivot("L", self.ext_px, self.ext_ts, self.ext_bar,
                            self.start_px, self.start_ts, height, bar.close_ts)
                self.pivots.append(piv)
                new.append(piv)
                self.dir = 1
                self.start_px, self.start_ts = self.ext_px, self.ext_ts
                self.ext_px, self.ext_ts, self.ext_bar = self.counter_px, bar.close_ts, bar
                self.counter_px = bar.close
        else:
            if bar.high > self.ext_px:
                self.ext_px, self.ext_ts, self.ext_bar = bar.high, bar.close_ts, bar
                self.counter_px = bar.close
            else:
                self.counter_px = min(self.counter_px, bar.low)
            height = self.ext_px - self.start_px
            floor_ok = (self.min_height_atr_frac <= 0 or math.isnan(atr_val)
                       or height >= self.min_height_atr_frac * atr_val)
            if height > 0 and floor_ok and \
                    (self.ext_px - self.counter_px) >= self.frac * height:
                piv = Pivot("H", self.ext_px, self.ext_ts, self.ext_bar,
                            self.start_px, self.start_ts, height, bar.close_ts)
                self.pivots.append(piv)
                new.append(piv)
                self.dir = -1
                self.start_px, self.start_ts = self.ext_px, self.ext_ts
                self.ext_px, self.ext_ts, self.ext_bar = self.counter_px, bar.close_ts, bar
                self.counter_px = bar.close
        return new


# --------------------------------------------------------------- per-TF pipeline

@dataclass
class TfEvent:
    """One (candidate, trigger-TF bar) break event on a single timeframe."""
    tf: int
    direction: int
    qualified: bool
    reason: str                # '' | 'multi_bar_break' | 'structure_unaligned'
    cand: Candidate
    bar: Bar                   # the breaking bar (decision bar on this TF)
    close_ts: datetime
    structure_state: str
    n_desc_highs: int
    n_desc_lows: int
    break_bars: int
    atr14: float
    target_price: float        # NaN when no draw exists
    pxl_age_bars: int
    pivots_at_decision: list[Pivot]


def _structure_state(pivots: list[Pivot], direction: int, n: int):
    """Bias gate (A3): last n completed swing highs AND lows aligned with
    `direction` (descending for shorts, ascending for longs). Also returns the
    consecutive aligned-step counts (n_desc_highs / n_desc_lows semantics: counts
    of terminals in the aligned run, so >= n means gate-aligned)."""
    highs = [p for p in pivots if p.kind == "H"]
    lows = [p for p in pivots if p.kind == "L"]
    if len(highs) < n or len(lows) < n:
        return "neutral", _aligned_run(highs, direction), _aligned_run(lows, direction)
    rh, rl = _aligned_run(highs, direction), _aligned_run(lows, direction)
    return ("aligned" if (rh >= n and rl >= n) else "unaligned"), rh, rl


def _aligned_run(piv: list[Pivot], direction: int) -> int:
    """Length of the run of consecutive terminals stepping in `direction`
    (direction=-1: strictly descending), counted from the most recent backward.
    A single terminal is a run of 1."""
    if not piv:
        return 0
    run = 1
    for a, b in zip(reversed(piv[:-1]), reversed(piv[1:])):
        step_ok = (b.px < a.px) if direction == -1 else (b.px > a.px)
        if step_ok:
            run += 1
        else:
            break
    return run


def run_tf_pipeline(tf_bars: list[Bar], tf: int, frac: float,
                    session_start: datetime, session_end: datetime,
                    min_height_atr_frac: float = 0.0):
    """Run legs + candidates + triggers for ONE timeframe.
    Returns (events, candidates). Everything is as-of bar close: a row's existence
    and every pre-decision field depend only on bars up to and including the
    decision bar (Gate 1's property, by construction).

    min_height_atr_frac: ADDITIVE param (default 0.0 preserves prior behaviour
    byte-for-byte). Gates leg-pivot confirmation on height >= frac * ATR14(tf)."""
    tracker = LegTracker(frac, min_height_atr_frac)
    trs = true_ranges(tf_bars)
    atr = [float("nan")] * len(tf_bars)
    atr_x = [float("nan")] * len(tf_bars)   # expanding-window fallback: total by
    P = CONFIG["ATR_PERIOD"]                # construction, feeds rangex (B5 item 2)
    for i in range(len(tf_bars)):
        if i + 1 >= P:
            atr[i] = sum(trs[i - P + 1:i + 1]) / P
            atr_x[i] = atr[i]
        else:
            atr_x[i] = sum(trs[:i + 1]) / (i + 1)

    cands: list[Candidate] = []          # both directions
    events: list[TfEvent] = []

    def alive(direction):
        return [c for c in cands if c.direction == direction and c.alive]

    for i, bar in enumerate(tf_bars):
        # 1) candidate lifecycle on candidates that existed BEFORE this bar.
        # The ACTIVE candidate (DA-1: most recent unbroken) is fixed at bar open —
        # deaths inside this bar must not promote another candidate mid-bar.
        active_at_open = {d: (alive(d)[-1] if alive(d) else None) for d in (-1, 1)}
        for c in cands:
            if not c.alive:
                # liquidity tracking continues after death for target purposes
                if c.liquidity_intact:
                    if (c.direction == -1 and bar.low < c.level_0) or \
                       (c.direction == 1 and bar.high > c.level_0):
                        c.liquidity_intact = False
                continue
            is_active = c is active_at_open[c.direction]
            if c.direction == -1:
                span = bar.open > c.level_1 and bar.close < c.level_0
                broke = bar.close < c.level_0
                pen = min(bar.open, bar.close) < c.level_1
                c.retrace_extreme = max(c.retrace_extreme, bar.high)
                # A2: invalidated THE MOMENT the leg-start high is taken — the
                # ACCUMULATED retrace extreme decides, and it precedes any
                # same-bar trigger (the premise died intrabar before the close)
                inval = c.retrace_extreme >= c.pivot.start_px + TICK
            else:
                span = bar.open < c.level_1 and bar.close > c.level_0
                broke = bar.close > c.level_0
                pen = max(bar.open, bar.close) > c.level_1
                c.retrace_extreme = min(c.retrace_extreme, bar.low)
                inval = c.retrace_extreme <= c.pivot.start_px - TICK
            if c.pivot.leg_height > 0:
                c.retrace_max = abs(c.retrace_extreme - c.level_0) / c.pivot.leg_height
            if c.liquidity_intact:
                if (c.direction == -1 and bar.low < c.level_0) or \
                   (c.direction == 1 and bar.high > c.level_0):
                    c.liquidity_intact = False

            if inval:
                c.invalidated, c.invalidation_ts = True, bar.close_ts
                c.invalidation_reason = "high_taken"
                c.fate, c.fate_ts, c.alive = "invalidated", bar.close_ts, False
            elif span and is_active:
                # trigger evaluation happens below (needs post-tracker pivots for
                # the bias gate); mark for evaluation
                c.fate, c.fate_ts, c.alive = "_trigger_pending", bar.close_ts, False
                c._trigger_bar = bar          # type: ignore[attr-defined]
                c._trigger_i = i              # type: ignore[attr-defined]
            elif broke:
                c.fate = "broken_multibar" if is_active else "broken_not_active"
                c.fate_ts, c.alive = bar.close_ts, False
                c._break_bar = bar            # type: ignore[attr-defined]
                c._break_i = i                # type: ignore[attr-defined]
            elif pen:
                c.n_penetrations += 1
                c.fate, c.fate_ts, c.alive = "penetrated", bar.close_ts, False

        # 2) leg tracker update — pivots confirmed at this close
        for piv in tracker.on_bar(bar, atr[i]):
            direction = -1 if piv.kind == "L" else 1
            c = Candidate(direction, tf, piv,
                          level_0=piv.px,
                          level_1=(min(piv.bar.open, piv.bar.close) if direction == -1
                                   else max(piv.bar.open, piv.bar.close)),
                          born_ts=piv.confirm_ts)
            c.retrace_extreme = piv.px
            # birth scan over bars strictly after the pivot bar up to and including
            # the confirm bar: (a) penetration ("approached from fully outside"),
            # (b) the retrace extreme achieved before birth
            for j in range(len(tf_bars)):
                b2 = tf_bars[j]
                if b2.close_ts <= piv.ts or b2.close_ts > bar.close_ts:
                    continue
                if direction == -1:
                    c.retrace_extreme = max(c.retrace_extreme, b2.high)
                    if min(b2.open, b2.close) < c.level_1:
                        c.n_penetrations += 1
                else:
                    c.retrace_extreme = min(c.retrace_extreme, b2.low)
                    if max(b2.open, b2.close) > c.level_1:
                        c.n_penetrations += 1
            if c.pivot.leg_height > 0:
                c.retrace_max = abs(c.retrace_extreme - c.level_0) / c.pivot.leg_height
            born_inval = (c.retrace_extreme >= piv.start_px + TICK) if direction == -1 \
                else (c.retrace_extreme <= piv.start_px - TICK)
            if born_inval:
                # the confirming retrace itself took the leg-start extreme:
                # structure premise failed before the candidate ever armed (A2)
                c.invalidated, c.invalidation_ts = True, bar.close_ts
                c.invalidation_reason = "high_taken"
                c.alive, c.fate, c.fate_ts = False, "invalidated", bar.close_ts
            elif c.n_penetrations:
                c.born_penetrated = True
                c.alive, c.fate, c.fate_ts = False, "penetrated", bar.close_ts
            cands.append(c)

        # 3) resolve pending triggers with pivots as-of this close
        for c in cands:
            if c.fate != "_trigger_pending" or c.fate_ts != bar.close_ts:
                continue
            tb: Bar = c._trigger_bar                     # type: ignore[attr-defined]
            in_session = session_start < bar.close_ts <= session_end
            piv_now = list(tracker.pivots)
            state, rh, rl = _structure_state(
                [p for p in piv_now if p.confirm_ts <= bar.close_ts],
                c.direction, CONFIG["STRUCT_N"])
            qualified = state == "aligned"
            c.fate = "triggered_qualified" if qualified else "triggered_unaligned"
            if not in_session:
                c.fate += "_warmup"
                continue
            events.append(_make_event(
                tf, c, tb, bar.close_ts, qualified,
                "" if qualified else "structure_unaligned",
                state, rh, rl, 1, atr[c._trigger_i],    # type: ignore[attr-defined]
                atr_x[c._trigger_i],                    # type: ignore[attr-defined]
                cands, tf_bars, piv_now))

        # 4) multi-bar break events (active candidate broken without a span)
        for c in cands:
            if c.fate != "broken_multibar" or c.fate_ts != bar.close_ts:
                continue
            bb: Bar = c._break_bar                       # type: ignore[attr-defined]
            in_session = session_start < bar.close_ts <= session_end
            if not in_session:
                c.fate += "_warmup"
                continue
            piv_now = list(tracker.pivots)
            state, rh, rl = _structure_state(
                [p for p in piv_now if p.confirm_ts <= bar.close_ts],
                c.direction, CONFIG["STRUCT_N"])
            # break accumulation count: consecutive bars from first body entry
            # into the zone through the breaking bar
            k = c._break_i                               # type: ignore[attr-defined]
            nb = 1
            for j in range(k - 1, -1, -1):
                b2 = tf_bars[j]
                if b2.close_ts <= c.pivot.ts:
                    break
                inside = (min(b2.open, b2.close) < c.level_1) if c.direction == -1 \
                    else (max(b2.open, b2.close) > c.level_1)
                if inside:
                    nb += 1
                else:
                    break
            events.append(_make_event(
                tf, c, bb, bar.close_ts, False, "multi_bar_break",
                state, rh, rl, nb, atr[k], atr_x[k], cands, tf_bars, piv_now))

        # session end: close out remaining lifecycle state
        if i == len(tf_bars) - 1:
            for c in cands:
                if c.alive:
                    c.alive, c.fate, c.fate_ts = False, "session_end", bar.close_ts
    return events, cands


def _make_event(tf, cand, bar, close_ts, qualified, reason, state, rh, rl,
                break_bars, atr14, atr_total, cands, tf_bars, pivots_now) -> TfEvent:
    limit = cand.fifty
    if cand.direction == -1:
        pool = [c.level_0 for c in cands
                if c.direction == -1 and c is not cand
                and c.liquidity_intact and c.level_0 < limit
                and c.born_ts <= close_ts]
        target = max(pool) if pool else float("nan")
    else:
        pool = [c.level_0 for c in cands
                if c.direction == 1 and c is not cand
                and c.liquidity_intact and c.level_0 > limit
                and c.born_ts <= close_ts]
        target = min(pool) if pool else float("nan")
    age = sum(1 for b in tf_bars
              if cand.pivot.ts < b.close_ts <= close_ts)
    ev = TfEvent(tf, cand.direction, qualified, reason, cand, bar, close_ts,
                 state, rh, rl, break_bars, atr14, target, age, pivots_now)
    ev.atr_total = atr_total                    # type: ignore[attr-defined]
    return ev


# ------------------------------------------------------------- fight resolution

def resolve_fights(events_by_tf: dict[int, list[TfEvent]],
                   warmup_start: datetime, session_end: datetime):
    """Mode (b): resolve at each 5m boundary; the highest TF that qualified within
    the window governs and its geometry executes. Returns a list of fight dicts.

    CAUSALITY (Gate 1 finding, kept deliberately): under mode (b) the DECISION
    completes at the boundary — within a window, a later-closing higher-TF bar
    can supersede an earlier trigger, so governance is only fixed once the window
    ends. The row's ts_decision is therefore the BOUNDARY (B3's "trigger bar
    close" parenthetical is satisfied by tf_trigger_ts instead; under mode (a)
    the two coincide). Row existence and every row column are functions of bars
    up to the boundary only; the governing EVENT's own facts (geometry,
    qualification) are functions of bars up to tf_trigger_ts only. Both are
    asserted under perturbation."""
    res_min = CONFIG["RESOLUTION_TF_MIN"]
    all_events = sorted((e for evs in events_by_tf.values() for e in evs),
                        key=lambda e: (e.close_ts, -e.tf))

    def boundary(ts: datetime) -> datetime:
        # epoch-anchored so the boundary grid always coincides with the 5m bar
        # grid, independent of any trimmed leading minutes
        sec = res_min * 60
        return datetime.fromtimestamp(math.ceil(ts.timestamp() / sec) * sec, UTC)

    groups: dict[tuple, list[TfEvent]] = {}
    for e in all_events:
        key = (boundary(e.close_ts), e.direction, round(e.cand.level_0 * 4))
        groups.setdefault(key, []).append(e)

    spent: dict[tuple, datetime] = {}
    fights = []
    for (bts, direction, l0t), evs in sorted(groups.items(), key=lambda kv: kv[0][0]):
        skey = (direction, l0t)
        if skey in spent and min(e.cand.pivot.ts for e in evs) <= spent[skey]:
            for e in evs:
                e.subsumed_late = True          # type: ignore[attr-defined]
            continue
        spent[skey] = bts
        qual = [e for e in evs if e.qualified]
        exe = max(qual, key=lambda e: e.tf) if qual else max(evs, key=lambda e: e.tf)
        reason = "" if exe.qualified else exe.reason
        fights.append(dict(
            boundary_ts=min(bts, session_end), direction=direction,
            events=evs, exe=exe, qualified=exe.qualified, reason=reason,
            tf_qualifying=sorted(e.tf for e in qual),
            tf_first_ts=min(e.close_ts for e in evs),
        ))
    return fights


# --------------------------------------------------------------- fill & outcomes

def _cross(direction, px_a, px_b):
    """True if px_a is beyond px_b in the trade direction."""
    return px_a <= px_b if direction == -1 else px_a >= px_b


def simulate_fill_and_outcomes(direction: int, limit: float, stop: float,
                               target: float, leg_start: float,
                               minutes: list[Bar], eligible_ts: datetime,
                               decision_ts: datetime, session_end: datetime,
                               stop_dist: float, minute_atr: dict[datetime, float]):
    """Resting-limit lifecycle per A5 + outcome battery per A8. Returns dict.

    DECLARED conventions:
    - Entry fill: >=1 tick trade-through beyond the limit; fill price = limit.
    - Cancellation on target: touch (the draw got tapped), not trade-through.
    - Exit fills at targets: 1 tick trade-through; stops: touch, filled at stop px.
    - Same-bar ambiguity: on any bar that could both fill and stop, the stop wins
      (conservative); flagged in fill_bar_ambiguous.
    - Costs: 0.5 pt round trip subtracted in the R numerator; *_pts stay gross.
    """
    tt = CONFIG["TRADE_THROUGH_TICKS"] * TICK
    out: dict = {k: float("nan") for k in (
        "bars_to_fill", "trade_through_ticks", "unfilled_mfe_pts",
        "unfilled_mae_pts", "mfe_pts", "mae_pts", "mfe_R", "mae_R", "bars_held")}
    out["ts_fill"] = None
    out.update(filled=False, expired_target_taken=False, expired_invalidated=False,
               expired_session_end=False, gap_limit_traded_through=False,
               gap_target_taken=False, gap_invalidated=False, order_never_live=False,
               fill_bar_ambiguous=False, filled_stress_2tick=False,
               filled_stress_partial=0.0)

    def hi(b):  # favorable extreme for the trade
        return b.low if direction == -1 else b.high

    def adverse(b):
        return b.high if direction == -1 else b.low

    sim = [b for b in minutes if b.close_ts > decision_ts and b.open_ts < session_end]
    gap = [b for b in sim if b.open_ts < eligible_ts]
    live = [b for b in sim if b.open_ts >= eligible_ts]

    fill_cond = (lambda b: b.high >= limit + tt) if direction == -1 else \
                (lambda b: b.low <= limit - tt)
    inval_cond = (lambda b: b.high >= leg_start + TICK) if direction == -1 else \
                 (lambda b: b.low <= leg_start - TICK)
    tgt_touch = (lambda b: (not math.isnan(target)) and
                 (b.low <= target if direction == -1 else b.high >= target))

    for b in gap:
        if fill_cond(b):
            out["gap_limit_traded_through"] = True
        if tgt_touch(b):
            out["gap_target_taken"] = True
        if inval_cond(b):
            out["gap_invalidated"] = True
    # gap events cancel before the order goes live (mode-b cost, recorded)
    if out["gap_target_taken"] or out["gap_invalidated"]:
        out["order_never_live"] = True
        out["expired_target_taken"] = bool(out["gap_target_taken"])
        out["expired_invalidated"] = bool(out["gap_invalidated"]
                                          and not out["gap_target_taken"])
        _unfilled_travel(out, direction, limit, sim, session_end)
        return out

    fill_i = None
    for i, b in enumerate(live):
        if fill_cond(b):
            fill_i = i
            out["filled"] = True
            out["ts_fill"] = b.close_ts
            out["bars_to_fill"] = float(i + 1)
            through = (b.high - limit) if direction == -1 else (limit - b.low)
            out["trade_through_ticks"] = round(through / TICK)
            st2 = CONFIG["STRESS_TRADE_THROUGH_TICKS"] * TICK
            out["filled_stress_2tick"] = (b.high >= limit + st2) if direction == -1 \
                else (b.low <= limit - st2)
            if out["filled_stress_2tick"]:
                a = minute_atr.get(b.close_ts, float("nan"))
                wide = (not math.isnan(a)) and (b.high - b.low) > 2 * a
                out["filled_stress_partial"] = 0.5 if wide else 1.0
            break
        if tgt_touch(b):
            out["expired_target_taken"] = True
            break
        if inval_cond(b):
            out["expired_invalidated"] = True
            break
    if not out["filled"]:
        if not (out["expired_target_taken"] or out["expired_invalidated"]):
            out["expired_session_end"] = True
        _unfilled_travel(out, direction, limit, live, session_end)
        return out

    hold = live[fill_i:]
    entry = limit
    stopped_i = None
    stop_touch = (lambda b: b.high >= stop) if direction == -1 else \
                 (lambda b: b.low <= stop)
    if stop_touch(hold[0]):
        out["fill_bar_ambiguous"] = True
    mfe = mae = 0.0
    for b in hold:
        mfe = max(mfe, (entry - b.low) if direction == -1 else (b.high - entry))
        mae = max(mae, (b.high - entry) if direction == -1 else (entry - b.low))
    out["mfe_pts"], out["mae_pts"] = mfe, mae
    out["mfe_R"], out["mae_R"] = mfe / stop_dist, mae / stop_dist

    cost = CONFIG["COST_RT_PTS"]

    def run_exit(tgt_px: float | None, be_after: float | None = None,
                 partial_frac: float | None = None, partial_r: float | None = None):
        """Generic exit runner. Returns (gross_pts, exit_i)."""
        stop_now = stop
        remaining = 1.0
        banked = 0.0
        for i, b in enumerate(hold):
            s_hit = (b.high >= stop_now) if direction == -1 else (b.low <= stop_now)
            t_hit = False
            if partial_frac is not None and remaining == 1.0:
                p_tgt = entry - partial_r * stop_dist if direction == -1 \
                    else entry + partial_r * stop_dist
                p_hit = (b.low <= p_tgt - tt) if direction == -1 else \
                        (b.high >= p_tgt + tt)
                if s_hit:  # conservative: stop first
                    pts = (entry - stop_now) if direction == -1 else (stop_now - entry)
                    return banked + remaining * pts, i
                if p_hit:
                    banked += partial_frac * partial_r * stop_dist
                    remaining -= partial_frac
                    stop_now = entry          # runner to break-even
                    continue
            elif tgt_px is not None and not math.isnan(tgt_px):
                t_hit = (b.low <= tgt_px - tt) if direction == -1 else \
                        (b.high >= tgt_px + tt)
            if s_hit:
                pts = (entry - stop_now) if direction == -1 else (stop_now - entry)
                return banked + remaining * pts, i
            if t_hit:
                pts = (entry - tgt_px) if direction == -1 else (tgt_px - entry)
                return banked + remaining * pts, i
        last = hold[-1].close
        pts = (entry - last) if direction == -1 else (last - entry)
        return banked + remaining * pts, len(hold) - 1

    battery = {}
    g, ei = run_exit(target)
    battery["out_nearest_draw_pts"], battery["out_nearest_draw_R"] = g, (g - cost) / stop_dist
    out["bars_held"] = float(ei + 1)
    for name, k in (("1R", 1.0), ("1_5R", 1.5), ("2R", 2.0), ("3R", 3.0)):
        tp = entry - k * stop_dist if direction == -1 else entry + k * stop_dist
        g, _ = run_exit(tp)
        battery[f"out_fixed_{name}_pts"] = g
        battery[f"out_fixed_{name}_R"] = (g - cost) / stop_dist
    g, _ = run_exit(None)
    battery["out_hold_stop_pts"], battery["out_hold_stop_R"] = g, (g - cost) / stop_dist
    for name, pr in (("1R", 1.0), ("2R", 2.0)):
        g, _ = run_exit(None, partial_frac=0.75, partial_r=pr)
        battery[f"out_partial75_{name}_trail_pts"] = g
        battery[f"out_partial75_{name}_trail_R"] = (g - cost) / stop_dist
    out.update(battery)
    return out


def _unfilled_travel(out, direction, limit, bars, session_end):
    """Travel of the never-filled setup, measured from the limit price to session
    end — the no-fill opportunity-cost object (A5's key consequence)."""
    if not bars:
        return
    if direction == -1:
        out["unfilled_mfe_pts"] = limit - min(b.low for b in bars)
        out["unfilled_mae_pts"] = max(b.high for b in bars) - limit
    else:
        out["unfilled_mfe_pts"] = max(b.high for b in bars) - limit
        out["unfilled_mae_pts"] = limit - min(b.low for b in bars)


def simulate_market_control(direction: int, entry: float, stop: float,
                            target: float, minutes: list[Bar],
                            eligible_ts: datetime, session_end: datetime):
    """Market-entry control at the eligible bar's open, same stop/target prices."""
    tt = CONFIG["TRADE_THROUGH_TICKS"] * TICK
    hold = [b for b in minutes if b.open_ts >= eligible_ts and b.open_ts < session_end]
    res = dict(ctrl_entry_price=entry, ctrl_stop_dist_pts=float("nan"),
               ctrl_mfe_R=float("nan"), ctrl_mae_R=float("nan"),
               ctrl_outcome_nearest_draw_R=float("nan"),
               ctrl_outcome_nearest_draw_pts=float("nan"))
    if not hold:
        return res
    sd = abs(entry - stop)
    if sd <= 0:
        return res
    res["ctrl_stop_dist_pts"] = sd
    mfe = mae = 0.0
    g = None
    cost = CONFIG["COST_RT_PTS"]
    for b in hold:
        mfe = max(mfe, (entry - b.low) if direction == -1 else (b.high - entry))
        mae = max(mae, (b.high - entry) if direction == -1 else (entry - b.low))
        if g is None:
            s_hit = (b.high >= stop) if direction == -1 else (b.low <= stop)
            t_hit = (not math.isnan(target)) and (
                (b.low <= target - tt) if direction == -1 else (b.high >= target + tt))
            if s_hit:
                g = (entry - stop) if direction == -1 else (stop - entry)
            elif t_hit:
                g = (entry - target) if direction == -1 else (target - entry)
    if g is None:
        last = hold[-1].close
        g = (entry - last) if direction == -1 else (last - entry)
    res["ctrl_mfe_R"], res["ctrl_mae_R"] = mfe / sd, mae / sd
    res["ctrl_outcome_nearest_draw_pts"] = g
    res["ctrl_outcome_nearest_draw_R"] = (g - cost) / sd
    return res


# ------------------------------------------------------------------ row assembly

def event_id_for(date_str, session, direction, level_0, tf, ts_decision) -> str:
    raw = f"{date_str}|{session}|{direction}|{round(level_0 * 4)}|{tf}|{ts_decision.isoformat()}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def run_session(minutes: list[Bar], d: Date, session: str,
                frac: float | None = None,
                day_context: dict | None = None,
                flow_lookup=None):
    """Full session pipeline. Returns (main_rows, tf_rows, cand_rows).
    `minutes` is the flat-filled warm-up+session minute grid (possibly perturbed
    by a gate harness). `day_context` carries PDH/PDL/ONH/ONL/HTF bars computed
    from data no later than the session (never from its future)."""
    frac = CONFIG["MIN_LEG_RETRACE"] if frac is None else frac
    w_utc, s_utc, e_utc = session_window_utc(d, session)
    tf_bars = {k: aggregate_tf(minutes, k) for k in CONFIG["TFS_MIN"]}
    events_by_tf, cands_by_tf = {}, {}
    for k in CONFIG["TFS_MIN"]:
        ev, cd = run_tf_pipeline(tf_bars[k], k, frac, s_utc, e_utc)
        events_by_tf[k], cands_by_tf[k] = ev, cd
    fights = resolve_fights(events_by_tf, minutes[0].open_ts if minutes else w_utc, e_utc)

    # minute ATR for the stress partial-fill rule
    trs = true_ranges(minutes)
    m_atr = {}
    P = CONFIG["ATR_PERIOD"]
    for i, b in enumerate(minutes):
        if i + 1 >= P:
            m_atr[b.close_ts] = sum(trs[i - P + 1:i + 1]) / P

    # session VWAP series (session-anchored, real minutes only)
    vwap_at: dict[datetime, float] = {}
    pv = vv = 0.0
    for b in minutes:
        if b.open_ts >= s_utc and b.real and b.volume > 0:
            tp = (b.high + b.low + b.close) / 3
            pv += tp * b.volume
            vv += b.volume
        if b.open_ts >= s_utc:
            vwap_at[b.close_ts] = (pv / vv) if vv > 0 else float("nan")

    ds = d.isoformat()
    main_rows, tf_rows, cand_rows = [], [], []

    for f in fights:
        exe: TfEvent = f["exe"]
        cand = exe.cand
        direction = f["direction"]
        limit = cand.fifty
        stop_base = tick_round(cand.level_1 + CONFIG["STOP_BUFFER_PTS"]) if direction == -1 \
            else tick_round(cand.level_1 - CONFIG["STOP_BUFFER_PTS"])
        stop_dist = abs(limit - stop_base)
        target = exe.target_price
        tdist = abs(limit - target) if not math.isnan(target) else float("nan")
        r_avail = tdist / stop_dist if stop_dist > 0 and not math.isnan(tdist) else float("nan")
        eid = event_id_for(ds, session, direction, cand.level_0, exe.tf,
                           f["boundary_ts"])

        row = dict(
            event_id=eid, ts_decision=f["boundary_ts"],
            ts_entry_eligible=f["boundary_ts"],
            date=ds, session=session, tf_trigger=exe.tf, direction=direction,
            cluster_id=eid, qualified=f["qualified"], reason=f["reason"],
            resolution_mode=CONFIG["RESOLUTION_MODE"],
            # PXL geometry
            pxl_ts=cand.pivot.ts, pxl_level_0=cand.level_0, pxl_level_1=cand.level_1,
            pxl_50=limit, wick_width_pts=cand.wick_width, pxl_age_bars=exe.pxl_age_bars,
            leg_start_ts=cand.pivot.start_ts, leg_start_price=cand.pivot.start_px,
            leg_height_pts=cand.pivot.leg_height, retrace_frac=cand.retrace_max,
            retrace_high=cand.retrace_extreme,
            pxl_invalidated=cand.invalidated, invalidation_ts=cand.invalidation_ts,
            invalidation_reason=cand.invalidation_reason or
                ("triggered" if f["qualified"] else ""),
            # trigger bar
            disp_open=exe.bar.open, disp_high=exe.bar.high, disp_low=exe.bar.low,
            disp_close=exe.bar.close,
            disp_body_pts=abs(exe.bar.close - exe.bar.open),
            disp_range_pts=exe.bar.high - exe.bar.low,
            disp_body_range_ratio=(abs(exe.bar.close - exe.bar.open) /
                                   (exe.bar.high - exe.bar.low))
                                   if exe.bar.high > exe.bar.low else float("nan"),
            disp_close_loc=((exe.bar.close - exe.bar.low) /
                            (exe.bar.high - exe.bar.low))
                            if exe.bar.high > exe.bar.low else float("nan"),
            atr14_pts=exe.atr14,
            disp_range_atr=((exe.bar.high - exe.bar.low) / exe.atr14)
                            if exe.atr14 and not math.isnan(exe.atr14) else float("nan"),
            disp_vol=exe.bar.volume,
            disp_range_per_vol=((exe.bar.high - exe.bar.low) / exe.bar.volume)
                                if exe.bar.volume else float("nan"),
            break_bars=exe.break_bars,
            break_depth_pts=(cand.level_0 - exe.bar.close) if direction == -1
                             else (exe.bar.close - cand.level_0),
            open_outside_zone=(exe.bar.open > cand.level_1) if direction == -1
                               else (exe.bar.open < cand.level_1),
            close_beyond_zone=(exe.bar.close < cand.level_0) if direction == -1
                               else (exe.bar.close > cand.level_0),
            body_wick_ratio=(abs(exe.bar.close - exe.bar.open) / cand.wick_width)
                             if cand.wick_width > 0 else float("nan"),
            zone_pre_penetrated=cand.born_penetrated,
            n_prior_penetrations=cand.n_penetrations,
            body_excess_pts=abs(exe.bar.close - exe.bar.open) - cand.wick_width,
            # multi-timeframe
            tf_qualifying_set=",".join(str(t) for t in f["tf_qualifying"]),
            tf_agreement_count=len(f["tf_qualifying"]),
            tf_first_ts=f["tf_first_ts"], tf_trigger_ts=exe.close_ts,
            resolution_lag_bars=int((exe.close_ts - f["tf_first_ts"]).total_seconds()
                                    // 60),
            n_events_in_cluster=len(f["events"]),
            # context
            structure_state=exe.structure_state,
            n_desc_highs=exe.n_desc_highs, n_desc_lows=exe.n_desc_lows,
            # fill block
            limit_price=limit, fill_rule_version=CONFIG["FILL_RULE_VERSION"],
            # risk / target
            stop_price_base=stop_base, stop_dist_pts_base=stop_dist,
            target_price=target, target_dist_pts=tdist, r_available=r_avail,
            min_1r_pass=bool(r_avail >= 1.0) if not math.isnan(r_avail) else False,
        )
        # ATR-scaled stop buffer alternatives (recorded, never selected here)
        for name, fr in CONFIG["STOP_BUFFER_ATR_FRACS"].items():
            if exe.atr14 and not math.isnan(exe.atr14):
                buf = max(fr * exe.atr14, CONFIG["STOP_BUFFER_ATR_FLOOR_PTS"])
                sp = tick_round(cand.level_1 + buf) if direction == -1 \
                    else tick_round(cand.level_1 - buf)
                row[f"stop_price_{name}"] = sp
                row[f"stop_dist_pts_{name}"] = abs(limit - sp)
            else:
                row[f"stop_price_{name}"] = float("nan")
                row[f"stop_dist_pts_{name}"] = float("nan")

        # context levels
        ctx = day_context or {}
        close = exe.bar.close
        vw = vwap_at.get(exe.close_ts, float("nan"))
        row["dist_vwap_pts"] = close - vw if not math.isnan(vw) else float("nan")
        for kk in ("pdh", "pdl", "onh", "onl"):
            v = ctx.get(kk, float("nan"))
            row[f"dist_{kk}_pts"] = close - v if not math.isnan(v) else float("nan")
        row["level_set_snapshot"] = json.dumps(
            dict(vwap=None if math.isnan(vw) else round(vw, 2),
                 **{kk: (None if math.isnan(ctx.get(kk, float("nan")))
                         else ctx[kk]) for kk in ("pdh", "pdl", "onh", "onl")}))
        for kk in ("htf_align_15m", "htf_align_1h"):
            sgn = (ctx.get(kk + "_fn") or (lambda ts: float("nan")))(exe.close_ts)
            row[kk] = bool(sgn == direction) if not (isinstance(sgn, float) and
                                                     math.isnan(sgn)) else None

        # fill + outcomes only for qualified fights (an order only exists there)
        if f["qualified"]:
            sim = simulate_fill_and_outcomes(
                direction, limit, stop_base, target, cand.pivot.start_px,
                minutes, f["boundary_ts"], exe.close_ts, e_utc, stop_dist, m_atr)
            row.update(sim)
        else:
            row.update(filled=None)
        ctrl_bar = next((b for b in minutes if b.open_ts >= f["boundary_ts"]), None)
        if ctrl_bar is not None and ctrl_bar.open_ts < e_utc:
            ctrl = simulate_market_control(
                direction, ctrl_bar.open, stop_base, target, minutes,
                f["boundary_ts"], e_utc)
            row.update(ctrl)

        # mode (a) supersede, computed in parallel from the fight's qualified events
        row.update(_mode_a(f, minutes, e_utc, m_atr))

        # flow features
        if flow_lookup is not None:
            row.update(flow_lookup(exe, row))
        else:
            row.update(flow_coverage=False, flow_data_object="book_only",
                       delta_decision_bar=float("nan"), delta_3bar=float("nan"),
                       cvd_state=float("nan"),
                       wall_size_ahead=float("nan"), wall_dist_ticks=float("nan"),
                       book_imbalance=float("nan"), depth_censored=None,
                       spread_est_ticks=float("nan"))
        row["closeloc"] = row["disp_close_loc"]
        # rangex is TOTAL by construction: expanding-window ATR before 14 bars
        # exist, strict ATR14 after (disp_range_atr stays strict-14, NaN-able)
        atx = getattr(exe, "atr_total", float("nan"))
        row["rangex"] = ((exe.bar.high - exe.bar.low) / atx) \
            if atx and not math.isnan(atx) and atx > 0 else float("nan")
        main_rows.append(row)

        # sibling per-TF rows: every event of the fight
        for e in f["events"]:
            c2 = e.cand
            lim2 = c2.fifty
            st2 = tick_round(c2.level_1 + CONFIG["STOP_BUFFER_PTS"]) if direction == -1 \
                else tick_round(c2.level_1 - CONFIG["STOP_BUFFER_PTS"])
            sd2 = abs(lim2 - st2)
            td2 = abs(lim2 - e.target_price) if not math.isnan(e.target_price) else float("nan")
            trow = dict(event_id=eid, tf=e.tf, own_ts_decision=e.close_ts,
                        qualified=e.qualified, reason=e.reason,
                        structure_state=e.structure_state,
                        level_0=c2.level_0, level_1=c2.level_1,
                        wick_width_pts=c2.wick_width, pxl_50=lim2,
                        stop_dist_pts=sd2,
                        r_available=(td2 / sd2) if sd2 > 0 and not math.isnan(td2)
                                     else float("nan"),
                        target_price=e.target_price,
                        subsumed_late=bool(getattr(e, "subsumed_late", False)),
                        boundary_ts=f["boundary_ts"], is_executed=e is exe)
            if e.qualified:
                own_elig = next((b.open_ts for b in minutes
                                 if b.open_ts >= e.close_ts), e.close_ts)
                s2 = simulate_fill_and_outcomes(
                    direction, lim2, st2, e.target_price, c2.pivot.start_px,
                    minutes, own_elig, e.close_ts, e_utc, sd2, m_atr)
                trow.update(filled=s2["filled"], ts_fill=s2["ts_fill"],
                            bars_to_fill=s2["bars_to_fill"],
                            out_nearest_draw_R=s2.get("out_nearest_draw_R", float("nan")),
                            mfe_R=s2.get("mfe_R", float("nan")),
                            mae_R=s2.get("mae_R", float("nan")))
            else:
                trow.update(filled=None, ts_fill=float("nan"),
                            bars_to_fill=float("nan"),
                            out_nearest_draw_R=float("nan"),
                            mfe_R=float("nan"), mae_R=float("nan"))
            tf_rows.append(trow)

    # subsumed-late events that never joined a fight row
    for k, evs in events_by_tf.items():
        for e in evs:
            if getattr(e, "subsumed_late", False):
                c2 = e.cand
                tf_rows.append(dict(
                    event_id="late_" + event_id_for(ds, session, e.direction,
                                                    c2.level_0, e.tf, e.close_ts),
                    tf=e.tf, own_ts_decision=e.close_ts, qualified=e.qualified,
                    reason=e.reason, structure_state=e.structure_state,
                    level_0=c2.level_0, level_1=c2.level_1,
                    wick_width_pts=c2.wick_width, pxl_50=c2.fifty,
                    stop_dist_pts=float("nan"), r_available=float("nan"),
                    target_price=e.target_price, subsumed_late=True,
                    boundary_ts=None, is_executed=False, filled=None,
                    ts_fill=float("nan"), bars_to_fill=float("nan"),
                    out_nearest_draw_R=float("nan"), mfe_R=float("nan"),
                    mae_R=float("nan")))

    for k, cds in cands_by_tf.items():
        for c in cds:
            cand_rows.append(dict(
                date=ds, session=session, tf=k, direction=c.direction,
                pxl_ts=c.pivot.ts, level_0=c.level_0, level_1=c.level_1,
                wick_width_pts=c.wick_width, leg_start_price=c.pivot.start_px,
                leg_height_pts=c.pivot.leg_height, confirm_ts=c.born_ts,
                fate=c.fate or "session_end", n_penetrations=c.n_penetrations,
                born_penetrated=c.born_penetrated,
                liquidity_intact=c.liquidity_intact))
    return main_rows, tf_rows, cand_rows


def _mode_a(fight, minutes, session_end, m_atr):
    """Mode (a) supersede: qualified events in time order; a higher-TF qualification
    replaces the resting limit unless it has already filled."""
    qual = sorted((e for e in fight["events"] if e.qualified),
                  key=lambda e: (e.close_ts, e.tf))
    res = dict(a_executed_tf=None, a_filled=None, a_fill_ts=None,
               a_limit_price=float("nan"), a_stop_dist_pts=float("nan"),
               a_r_available=float("nan"))
    if not qual:
        return res
    direction = fight["direction"]
    tt = CONFIG["TRADE_THROUGH_TICKS"] * TICK
    cur = None            # (event, live_from_ts)
    filled_e = fill_ts = cancelled_e = None
    pending = list(qual)
    scan = [b for b in minutes if b.close_ts > qual[0].close_ts and
            b.open_ts < session_end]
    for b in scan:
        while pending and pending[0].close_ts < b.close_ts:
            e = pending.pop(0)
            if filled_e is None and cancelled_e is None and \
                    (cur is None or e.tf > cur[0].tf):
                elig = next((bb.open_ts for bb in minutes if bb.open_ts >= e.close_ts),
                            e.close_ts)
                cur = (e, elig)
        if cur is None or filled_e is not None or cancelled_e is not None \
                or b.open_ts < cur[1]:
            continue
        e = cur[0]
        lim = e.cand.fifty
        hit = (b.high >= lim + tt) if direction == -1 else (b.low <= lim - tt)
        tgt = e.target_price
        t_touch = (not math.isnan(tgt)) and ((b.low <= tgt) if direction == -1
                                             else (b.high >= tgt))
        if hit:
            filled_e, fill_ts = e, b.close_ts
        elif t_touch:
            cancelled_e = e     # target taken without a fill ends the fight (A5)
    exec_e = filled_e or cancelled_e or (cur[0] if cur else qual[-1])
    lim = exec_e.cand.fifty
    st = tick_round(exec_e.cand.level_1 + CONFIG["STOP_BUFFER_PTS"]) if direction == -1 \
        else tick_round(exec_e.cand.level_1 - CONFIG["STOP_BUFFER_PTS"])
    sd = abs(lim - st)
    td = abs(lim - exec_e.target_price) if not math.isnan(exec_e.target_price) else float("nan")
    res.update(a_executed_tf=exec_e.tf, a_filled=filled_e is not None,
               a_fill_ts=fill_ts if fill_ts else float("nan"),
               a_limit_price=lim, a_stop_dist_pts=sd,
               a_r_available=(td / sd) if sd > 0 and not math.isnan(td) else float("nan"))
    return res
