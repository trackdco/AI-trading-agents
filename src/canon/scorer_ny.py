"""The LIVE decision core for the rebuilt canon (ANGUS sign-off 2026-07-29).

This is the sequential twin of `scripts/funded_book.py`. That script is the spec; this module
must reproduce it decision-for-decision on the same inputs, and
`tests/test_canon_scorer_ny.py` asserts exactly that by replaying every validated trade in
output/aikido_{fit,holdout}.parquet through this class and diffing against `funded_book.run()`
— trade set, tier, risk dollars, micros and P&L, to the cent, on both spans.

WHY THIS MODULE EXISTS (read before changing anything): the previous live core
(`src/canon/scorer.py::NYScorer`) implements the OLD canon, whose substrate shared a 2-trade
cap across pre-market and the golden window instead of 2 per session — starving gold on 56%
of day-books. Everything derived from it is void. See docs/CANON.md. That class stays on disk
only until the runner is cut over; it must never be armed.

WHAT CHANGED, LIVE-VISIBLE (each item is a behavioural change requiring sign-off):
  * ENTRIES ARE UNCAPPED. No 2/day slot, no nth-escalation, no day ladder, no governor, no
    cold trail. Capacity is now bounded by the daily risk BUDGET, not by a trade count.
    -> `RiskLimits.max_trades_per_day` must be raised out of the way or the backstop halts a
       normal day. See docs/ARMING-REFERENCE.md gate R3.
  * The golden window runs 09:40-10:30 (was 09:40-10:00) and pre-market 08:00-09:30.
  * No distance cancel. A resting entry lives until its own session window ends. The engine's
    22pt t_cancel measured INVERTED: it kept -0.180R of trades and killed +0.015R.
  * No 09:55-10:00 dead zone. The rebuilt canon was validated without one; re-imposing it
    would trade a book nobody measured.
  * Gold carries a wall-QUALITY gate on top of the D gate (the aikido cut).
  * Sizing is conviction tiers x a per-day base, and the daily budget scales WITH the base.

CAUSALITY (the property that makes a sequential live twin legitimate at all): every input to
a decision is knowable at that decision's own fill time. Realized P&L counts only positions
that have already CLOSED; open positions contribute their risk, not their unknown outcome.
Nothing reads a later row. This is why the backtest and the live path can agree exactly.

PROTOCOL — evaluate is pure, commit mutates:

    s.start_day(day, buffer=<equity above the trailing line>)
    v = s.evaluate(row)          # pure: safe to call every bar while the order rests
    if not v.taken: cancel the resting order (the budget no longer admits it)
    ...on fill:  s.commit(v)     # registers the position's risk as in-flight
    ...on exit:  s.on_exit(v, pl=<realized dollars>)

`evaluate` is deliberately side-effect free so the execution layer can re-ask the same
question on every closed bar without corrupting state — a resting order whose budget room
was consumed by an earlier fill MUST be cancelled, and that is the only way to notice.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Mapping

import pandas as pd

from scripts.live_thresholds import TH

NY_TZ = "America/New_York"

# ---- session windows (minute-of-day ET). ANGUS 2026-07-30: gold extended to 10:30 --------
PRE_WIN = (480, 570)                    # 08:00-09:30
GOLD_WIN = (580, 630)                   # 09:40-10:30

# ---- frozen gates and score components (scripts/l3_check_trial.py, l3_score_apply.py) ----
# The G and AGE cut points are NOT restated here: they come from the SAME frozen source the
# batch reads (config/live_thresholds.json via scripts.live_thresholds.TH). Restating them
# was tried and was wrong twice over — the conformance test caught it, which is the whole
# reason that test replays the book instead of trusting this module.
RISK_MIN, RISK_MAX = 7.0, 60.0          # Layer-0 stop band; sub-7pt is 14% WR / -0.201R
WALL_D_MIN = 2.75                       # aikido wall-quality cut (gold)
Q_WALLSZ_MIN = 7.0                      # wall-ahead absolute size for the WALLSZ bit
Q_TRIG_MIN = 11.0                       # trigger density, strictly greater
Q_LONSLOPE_MIN = -0.0961                # London cum-delta OLS slope, direction-signed
ELITE_STRUCT = "broke"                  # the elite combo's structural event
ELITE_PER_DAY = 1

# ---- sizing spine (scripts/funded_book.py) ----------------------------------------------
BUDGET_PER_BASE = 800.0 / 150.0         # $800 daily budget at the $150 base
SOFT_FRAC = 280.0 / 800.0               # soft de-risk at 35% of that day's budget
RAMP_BUFFER = 1000.0                    # buffer below this -> half size (live insurance)
MICRO_CLAMP = 40
MNQ_DOLLARS_PER_PT = 2.0


@dataclass(frozen=True)
class Profile:
    """A shipped sizing profile. `cap == base` disables scaling (that IS the lucid profile)."""
    name: str
    base: float
    per: float
    step: float
    after: float
    cap: float

    def base_for(self, buffer: float) -> float:
        if self.per <= 0 or buffer <= self.after:
            return self.base
        return min(self.cap, self.base + math.floor((buffer - self.after) / self.step) * self.per)


LUCID = Profile("lucid", base=150.0, per=0.0, step=2000.0, after=3000.0, cap=150.0)
SCALED600 = Profile("scaled600", base=150.0, per=75.0, step=2000.0, after=3000.0, cap=600.0)
PROFILES = {p.name: p for p in (LUCID, SCALED600)}


def _f(row: Mapping, key: str) -> float:
    v = row.get(key) if hasattr(row, "get") else getattr(row, key, None)
    if v is None:
        return math.nan
    try:
        return float(v)
    except (TypeError, ValueError):
        return math.nan


def _s(row: Mapping, key: str) -> str:
    v = row.get(key) if hasattr(row, "get") else getattr(row, key, None)
    return "" if v is None else str(v)


def session_of(fill_hm: float) -> str:
    """'pre' | 'gold' | 'other' from minute-of-day ET. Anything else is not a canon window."""
    if PRE_WIN[0] <= fill_hm < PRE_WIN[1]:
        return "pre"
    if GOLD_WIN[0] <= fill_hm < GOLD_WIN[1]:
        return "gold"
    return "other"


def checks(row: Mapping, sess: str) -> dict[str, float]:
    """The gates and score bits for one signal. Mirrors scripts/l3_check_trial.py::load
    expression-for-expression; NaN means 'stood down', and scoring treats NaN as 0 exactly
    as l3_score_apply's `.fillna(0)` does."""
    long = _s(row, "direction") == "long"
    thick = _f(row, "dep_thick")
    below_d, above_d = _f(row, "dep_wall_below_d"), _f(row, "dep_wall_above_d")
    behind_d = below_d if long else above_d
    ahead_d = above_d if long else below_d
    ahead_sz = _f(row, "dep_wall_above_sz") if long else _f(row, "dep_wall_below_sz")
    c: dict[str, float] = {}
    # pre-market gate + score components
    c["W"] = math.nan if math.isnan(thick) else float(math.isnan(behind_d))
    c["G"] = float(_f(row, "ent_vs_vwap_sd_dir") >= TH.pre_G_ent_vs_vwap_sd_dir_min)
    c["F_"] = float(_f(row, "fill_delta_conf") == 1)
    # gold gate + score components
    c["D"] = math.nan if math.isnan(thick) else float(not math.isnan(ahead_d))
    c["Tc"] = float(_f(row, "d15_conf") == 1)
    age = _f(row, "on_extreme_age")
    c["AGE"] = math.nan if math.isnan(age) else float(age >= TH.gold_AGE_on_extreme_age_min)
    c["TRIG"] = float(_f(row, "trigdens_30") > Q_TRIG_MIN)
    c["T2"] = float(_f(row, "fill_delta_conf") == 1 or _f(row, "bp5opp") == 1)
    c["WALLSZ"] = float(c["D"] == 1 and ahead_sz >= Q_WALLSZ_MIN)
    c["LONSLOPE"] = float(_f(row, "lon_slope_d") >= Q_LONSLOPE_MIN)
    return c


def _nz(x: float) -> float:
    return 0.0 if math.isnan(x) else x


def score_of(c: Mapping[str, float], sess: str) -> float:
    """Frozen survivor formulas — chosen on 2025, validated on 2026 AND the sealed holdout.
    Never refit here."""
    if sess == "pre":
        return 2 * _nz(c["W"]) + _nz(c["G"]) + _nz(c["F_"])
    return 2 * _nz(c["D"]) + _nz(c["Tc"]) + _nz(c["AGE"]) + _nz(c["TRIG"]) + _nz(c["T2"])


def tier_of(score: float, sess: str) -> float:
    """Conviction tier from the score. Cells are era-consistent in all three eras."""
    if sess == "gold":
        return 0.5 if score <= 3 else (1.0 if score == 4 else 1.5)
    return 0.5 if score <= 2 else (1.0 if score == 3 else 1.5)


def valid_entry(row: Mapping, c: Mapping[str, float], sess: str) -> tuple[bool, str]:
    """(admissible?, refusal reason). The gates, in the order the book applies them."""
    risk = _f(row, "risk")
    if math.isnan(risk) or not (RISK_MIN <= risk <= RISK_MAX):
        return False, "hard_gate_risk"
    if sess == "pre":
        return (True, "") if c["W"] == 1 else (False, "pre_wall_behind")
    if sess == "gold":
        if c["D"] != 1:
            return False, "gold_no_wall_ahead"
        # The aikido wall-QUALITY cut. NOTE dep_wall_below_d is used RAW here, not
        # direction-signed — that is the column the cut was measured on (funded_book.py
        # load_book) and the cut set runs 37-41% WR in every era on exactly this form.
        # Direction-signing it would be a different, unmeasured rule. Do not "fix" it.
        below_d = _f(row, "dep_wall_below_d")
        if (not math.isnan(below_d) and below_d < WALL_D_MIN) or c["WALLSZ"] == 0:
            return False, "gold_wall_quality"
        return True, ""
    return False, "outside_window"


@dataclass
class NYVerdict:
    day: str
    fill: object
    session: str
    score: float
    tier: float                 # 0.5 / 1.0 / 1.5, or 2.0 when the elite combo fires
    elite: bool
    risk_dollars: float         # the dollars this trade is allowed to lose
    micros: int
    risk_pts: float
    taken: bool
    checks: dict
    reasons: list               # ordered refusal / de-risk reasons, always populated
    base: float = 0.0
    budget: float = 0.0
    committed: bool = False


@dataclass
class _Open:
    risk_dollars: float


@dataclass
class NYScorerV2:
    """Sequential `funded_book.run()`. One instance per account; call `start_day` at each
    session boundary with the account's current buffer above its trailing line."""
    profile: Profile = LUCID
    news_gate: object | None = None
    _day: str | None = field(default=None, init=False)
    _base: float = field(default=0.0, init=False)
    _budget: float = field(default=0.0, init=False)
    _soft: float = field(default=0.0, init=False)
    _ramp: float = field(default=1.0, init=False)
    _realized: float = field(default=0.0, init=False)
    _open: dict = field(default_factory=dict, init=False)
    _elite_used: int = field(default=0, init=False)

    # ---- day boundary --------------------------------------------------------------
    def start_day(self, day: str, *, buffer: float) -> None:
        """`buffer` = equity above the account's trailing drawdown line, at day start.
        It sets the day's base, budget, soft trigger and ramp — all frozen for the day,
        exactly as the backtest computes them once per day from the pre-session balance."""
        self._day = str(day)
        self._base = self.profile.base_for(float(buffer))
        self._budget = self._base * BUDGET_PER_BASE
        self._soft = self._budget * SOFT_FRAC
        self._ramp = 0.5 if float(buffer) < RAMP_BUFFER else 1.0
        self._realized = 0.0
        self._open.clear()
        self._elite_used = 0

    # ---- the decision (pure) -------------------------------------------------------
    def evaluate(self, row: Mapping) -> NYVerdict:
        """Pure. Safe to re-ask on every bar while an entry rests — and the execution layer
        MUST, because budget room consumed by an earlier fill has to cancel a resting order."""
        day = str(row["day"]) if "day" in row or hasattr(row, "day") else str(self._day)
        if self._day is not None and day != self._day:
            raise RuntimeError(
                f"row day {day} != scorer day {self._day} — call start_day() at the boundary")
        hm = _f(row, "fill_hm")
        if math.isnan(hm):
            et = pd.to_datetime(row["fill"], utc=True).tz_convert(NY_TZ)
            hm = et.hour * 60 + et.minute
        sess = session_of(hm)
        c = checks(row, sess)
        risk_pts = _f(row, "risk")
        blank = dict(day=day, fill=row["fill"], session=sess, checks=c, risk_pts=risk_pts,
                     base=self._base, budget=self._budget)

        ok, why = valid_entry(row, c, sess)
        if not ok:
            return NYVerdict(score=math.nan, tier=0.0, elite=False, risk_dollars=0.0,
                             micros=0, taken=False, reasons=[why], **blank)

        score = score_of(c, sess)
        tier = tier_of(score, sess)
        reasons: list[str] = []

        # Elite 2.0x — gold only, TRIG & LONSLOPE & a BROKEN structure, max one per day.
        # struct_event is an order-walk observation (did price break through the level ahead
        # before the fill, or reject off it?). If the execution layer cannot supply it, the
        # trade simply sizes at its own tier: absent evidence NEVER escalates size.
        struct = _s(row, "struct_event")
        elite_ready = (sess == "gold" and c["TRIG"] == 1 and c["LONSLOPE"] == 1
                       and struct == ELITE_STRUCT)
        if elite_ready and self._elite_used < ELITE_PER_DAY:
            tier = 2.0
        elif elite_ready:
            reasons.append("elite_used_today")

        # news blackout — a red-folder release voids the entry outright
        if self.news_gate is not None:
            et = pd.to_datetime(row["fill"], utc=True).tz_convert(NY_TZ).tz_localize(None)
            if bool(self.news_gate.blocks(et)):
                return NYVerdict(score=score, tier=tier, elite=(tier == 2.0),
                                 risk_dollars=0.0, micros=0, taken=False,
                                 reasons=[*reasons, "news_blackout"], **blank)

        # soft de-risk: half size once the day's REALIZED loss passes the trigger
        soft = self._realized <= -self._soft
        if soft:
            reasons.append("soft_derisk_half")
        if self._ramp < 1.0:
            reasons.append("dd_ramp_half")
        rd = self._base * tier * self._ramp * (0.5 if soft else 1.0)

        # the budget: realized losses + risk still in flight + this trade must all fit
        inflight = sum(o.risk_dollars for o in self._open.values())
        if max(0.0, -self._realized) + inflight + rd > self._budget:
            return NYVerdict(score=score, tier=tier, elite=(tier == 2.0), risk_dollars=rd,
                             micros=0, taken=False, reasons=[*reasons, "budget_exhausted"],
                             **blank)

        micros = int(min(MICRO_CLAMP, max(1, round(rd / (risk_pts * MNQ_DOLLARS_PER_PT)))))
        return NYVerdict(score=score, tier=tier, elite=(tier == 2.0), risk_dollars=rd,
                         micros=micros, taken=True, reasons=reasons, **blank)

    # ---- state transitions ---------------------------------------------------------
    def commit(self, v: NYVerdict) -> None:
        """Register a FILLED entry: its risk is now in flight and consumes budget room.
        The elite slot is spent here, not at evaluate() — an elite candidate refused by the
        budget leaves the slot available for a later one, exactly as the backtest does."""
        if not v.taken:
            raise RuntimeError("commit() on a verdict that was not taken")
        if v.committed:
            raise RuntimeError("commit() called twice for the same verdict")
        v.committed = True
        if v.tier == 2.0:
            self._elite_used += 1
        self._open[id(v)] = _Open(risk_dollars=v.risk_dollars)

    def on_exit(self, v: NYVerdict, *, pl: float) -> None:
        """Report a CLOSED position's realized dollars. Until this lands the position counts
        as in-flight risk, never as a known outcome."""
        if not v.committed:
            raise RuntimeError("on_exit() before commit()")
        self._open.pop(id(v), None)
        self._realized += float(pl)

    # ---- introspection (journal / Telegram /status) ---------------------------------
    def status(self) -> dict:
        return {"day": self._day, "profile": self.profile.name, "base": self._base,
                "budget": self._budget, "soft_at": -self._soft, "ramp": self._ramp,
                "realized": round(self._realized, 2),
                "inflight_risk": round(sum(o.risk_dollars for o in self._open.values()), 2),
                "open_positions": len(self._open), "elite_used": self._elite_used,
                "room": round(self._budget - max(0.0, -self._realized)
                              - sum(o.risk_dollars for o in self._open.values()), 2)}
