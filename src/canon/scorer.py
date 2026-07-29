"""The live decision core (item 4) — the canon's scoring, sized one trade at a time.

`scripts/canon_mechanical.build_canon` and `scripts/london_canon.build_london` are BATCH
frame code: whole-history DataFrames, rolling trails, per-day ladders. A live bot decides
one signal at a time, so this module re-states the same stack sequentially — and the stack
is re-statable ONLY because every stateful construct in the batch is causal: the Layer-3
governor and the Layer-2e cold trail are `rolling(...).mean().shift(1)` (strictly prior
trades), and the Layer-2c/2b day ladders react to realized prior trades of the same day.
Nothing about trade i reads trade i's own outcome, or any later row.

Parity is the whole point: tests/test_canon_scorer_parity.py replays every stored book row
(output/canon_book.parquet, output/london_canon_book.parquet) through
these classes and requires score/size/governor/nth/pl to match the batch column-for-column.
Thresholds come from the SAME frozen source the batch reads (scripts.live_thresholds.TH,
config/live_thresholds.json) plus the inline constants restated in canon_mechanical's
docstring — restated here as module constants with their provenance.

Protocol per NY signal (strict, enforced):

    v  = scorer.decide(row)        # at fill time: everything needed to size the order
    pl = scorer.settle(v, r_3=..., fw_3=..., dollars=...)   # when the outcome is known

`settle` must be called for EVERY decided signal, including size-0 ones: the batch
governor's rolling win-rate is computed over ALL score>=4 signals regardless of size, and
the cold trail over all post-escalation taken signals even when Layer 2c later drops them.
Live, the outcome of an untaken signal is the shadow engine's simulated outcome (the canon
lane runs the engine on every signal regardless) — the same `dollars` the batch used.

The `conf_PM` input field must be fed the LOOK-AHEAD-CLEAN value (`pm_sofar_conf`), as
scripts/canon_news_clean.py does for the arming reference. The fix lives in the feeding,
not here — this module scores whatever `conf_PM` it is given, exactly as build_canon does.

London decides without outcomes entirely (no trails, no cut, no governor — verified
EV-negative to add; see scripts/london_canon.py): `decide(row)` is self-contained and
`pl = dollars * size` is the caller's arithmetic.
"""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Mapping

import pandas as pd

from scripts.live_thresholds import TH

NY_TZ = "America/New_York"

# ---- frozen inline constants (provenance: scripts/canon_mechanical.py docstring) --------
RISK_MIN, RISK_MAX = 7.0, 60.0          # Layer 0 hard gate (NY)
CUT_R3_MAX, CUT_FW3_MAX = -0.1106, -13.0    # Layer 2d 3-min cut (same as exit_driver)
Q_WALLSZ_MIN = 7.0                      # 2025-GOLD q50 wall-ahead absolute size
Q_BIGFD_MIN = 173.0                     # 2025-GOLD q75 |fill-minute delta|
Q_TRIG_MIN = 11.0                       # busy-tape trigger density (strictly greater)
Q_VWAPD_MIN = 0.107                     # SD beyond vwap in trade direction
Q_LONSLOPE_MIN = -0.0961                # London cum-delta OLS slope, dir-signed
R1_CHURN_MIN = 0.0292                   # Layer 2e cold-grind churn threshold (strictly >)
R2_NETPATH_MIN = 0.3328                 # Layer 2e good-PA boost
GOV_WINDOW, GOV_WR_MIN = 15, 0.35       # Layer 3 governor
COLD_WINDOW, COLD_WR_MIN = 20, 0.40     # Layer 2e cold trail
DAY_STOP_DOLLARS = -400.0               # Layer 2c done-for-the-day
LON_RISK_MIN = 9.5                      # London Layer 0 (no upper cap — London-native)
LON_FAR_MIN = 4.5                       # wall AHEAD farther than this = magnet not choke
LON_ROOM_LO, LON_ROOM_HI = 2.48, 9.56   # room_ahead_R band
LON_ASIA_MIN = -748.0                   # dir-signed Asia CVD floor


def _f(row: Mapping, key: str) -> float:
    """Field as float; missing/None -> nan (mirrors a merged-frame NaN)."""
    v = row.get(key) if hasattr(row, "get") else getattr(row, key, None)
    if v is None:
        return math.nan
    try:
        return float(v)
    except (TypeError, ValueError):
        return math.nan


def _nansum(*vals: float) -> float:
    return float(sum(v for v in vals if not math.isnan(v)))


def eff_dollars(*, r_3: float, fw_3: float, risk: float, dollars: float) -> tuple[bool, float]:
    """Layer 2d: (cut3 fired?, effective realized dollars). NaN r/fw never cuts —
    identical to the batch's `.fillna(False)`."""
    cut = (not math.isnan(r_3) and not math.isnan(fw_3)
           and r_3 <= CUT_R3_MAX and fw_3 <= CUT_FW3_MAX)
    return cut, (r_3 * risk * 20.0 if cut else dollars)


# ---- pure per-row checks (expression-for-expression from build_canon) -------------------
def ny_checks(row: Mapping) -> dict[str, float]:
    """The Layer-1 validation bits + Layer-2q quality bits for one NY signal. Values are
    0.0/1.0 or nan exactly where the batch leaves NaN (depth/state unavailable)."""
    long = row["direction"] == "long"
    sgn = 1.0 if long else -1.0
    thick = _f(row, "dep_thick")
    wall_behind_d = _f(row, "dep_wall_below_d") if long else _f(row, "dep_wall_above_d")
    wall_ahead_d = _f(row, "dep_wall_above_d") if long else _f(row, "dep_wall_below_d")
    wall_ahead_sz = _f(row, "dep_wall_above_sz") if long else _f(row, "dep_wall_below_sz")
    c = {}
    # pre-market (frozen as shipped)
    c["W"] = math.nan if math.isnan(thick) else float(math.isnan(wall_behind_d))
    c["F"] = float(_f(row, "fill_delta_conf") == 1)
    c["Tp"] = float(_f(row, "d15") * sgn >= TH.pre_Tp_d15dir_min)
    c["G"] = float(_f(row, "ent_vs_vwap_sd_dir") >= TH.pre_G_ent_vs_vwap_sd_dir_min)
    c["C"] = float((_f(row, "conf_PM") if row["win_"] == "pre" else _f(row, "conf_LON")) == 1)
    # golden-native
    c["D"] = math.nan if math.isnan(thick) else float(not math.isnan(wall_ahead_d))
    c["Tc"] = float(_f(row, "d15_conf") == 1)
    bbw = _f(row, "bbw_state")
    c["X"] = math.nan if math.isnan(bbw) else float(bbw >= TH.gold_X_bbw_state_min)
    age = _f(row, "on_extreme_age")
    c["AGE"] = math.nan if math.isnan(age) else float(age >= TH.gold_AGE_on_extreme_age_min)
    npath = _f(row, "netpath_30")
    c["PAQ"] = math.nan if math.isnan(npath) else float(npath >= TH.gold_PAQ_netpath_30_min)
    # Layer 2q quality bits (never NaN — a NaN input is simply "bit not earned")
    c["WALLSZ"] = float(c["D"] == 1 and wall_ahead_sz >= Q_WALLSZ_MIN)
    c["BIGFD"] = float(abs(_f(row, "fill_delta")) >= Q_BIGFD_MIN)
    c["T2"] = float(_f(row, "fill_delta_conf") == 1 or _f(row, "bp5opp") == 1)
    c["TRIG"] = float(_f(row, "trigdens_30") > Q_TRIG_MIN)
    c["VWAPD"] = float(_f(row, "ent_vs_vwap_sd_dir") >= Q_VWAPD_MIN)
    c["LONSLOPE"] = float(_f(row, "lon_slope_d") >= Q_LONSLOPE_MIN)
    return c


def _ladder_ny(score: float) -> float:
    if score <= 2:
        return 0.0
    return {3: 0.5, 4: 1.0, 5: 1.5}.get(int(score), 0.0)


@dataclass
class NYVerdict:
    day: str
    fill: object
    window: str                          # "pre" | "gold"
    score: float
    size: float                          # final size multiplier (governor NOT folded in)
    governor: float
    nth: int | None                      # day slot consumed, None if not taken pre-2b
    Q: float
    struct: float
    checks: dict
    risk: float
    vetoes: list                         # ordered size-zeroing/modifying reasons
    hard_gated: bool = False
    # settle-time bookkeeping (what state updates this signal owes)
    _hi: bool = False                    # feeds the Layer-3 governor trail
    _taken_for_cold: bool = False        # feeds the Layer-2e cold trail
    _live: bool = False                  # feeds the Layer-2c day ladder


@dataclass
class NYScorer:
    """Sequential build_canon. Feed signals in strict fill order; settle each before the
    next decide (the trails and the day ladder are defined over settled prior trades).

    `dead_zones`: list of (start_hm, end_hm) minute-of-day ET intervals; a fill inside any
    zone is vetoed at the same stage as build_canon's dead-zone cut (after the quality
    tier, before the news gate and before the day slot is consumed). ANGUS RULING
    2026-07-26: [(595, 600)] — no entries 09:55–10:00."""
    news_gate: object | None = None
    dead_zones: tuple = ()
    _gov: deque = field(default_factory=lambda: deque(maxlen=GOV_WINDOW), init=False)
    _gov_cur: float = field(default=math.nan, init=False)
    _cold: deque = field(default_factory=lambda: deque(maxlen=COLD_WINDOW), init=False)
    _cold_cur: float = field(default=math.nan, init=False)
    _day: str | None = field(default=None, init=False)
    _day_taken: int = field(default=0, init=False)
    _day_pl: float = field(default=0.0, init=False)
    _day_out: bool = field(default=False, init=False)
    _pending: NYVerdict | None = field(default=None, init=False)

    def decide(self, row: Mapping) -> NYVerdict:
        if self._pending is not None:
            raise RuntimeError("previous verdict not settled — the trails would be stale")
        day, window, risk = str(row["day"]), row["win_"], _f(row, "risk")
        if day != self._day:
            self._day, self._day_taken, self._day_pl, self._day_out = day, 0, 0.0, False
        c = ny_checks(row)
        struct = (c["W"] + c["Tp"] if window == "pre"
                  else (0.0 if math.isnan(c["D"]) else c["D"]) + c["Tc"])
        # Layer 0 hard gate: outside 7-60pt stops the signal never enters the book at all
        if not (RISK_MIN <= risk <= RISK_MAX):
            return NYVerdict(day=day, fill=row["fill"], window=window, score=math.nan,
                             size=0.0, governor=1.0, nth=None, Q=math.nan, struct=struct,
                             checks=c, risk=risk, vetoes=["hard_gate_risk"], hard_gated=True)
        score = (_nansum(c["W"], c["F"], c["Tp"], c["G"], c["C"]) if window == "pre"
                 else _nansum(c["D"], c["Tc"], c["X"], c["AGE"], c["PAQ"]))
        Q = c["WALLSZ"] + c["BIGFD"] + c["T2"] + c["TRIG"] + c["VWAPD"] + c["LONSLOPE"]
        size, vetoes = _ladder_ny(score), []
        # Layer 2q (gold only)
        if window == "gold" and size > 0:
            if Q <= 1:
                size, _ = 0.0, vetoes.append("gold_q_low")
            elif Q >= 3:
                size = min(size + 0.5, 1.5)
        # dead-zone entry cut (ANGUS 2026-07-26) — same stage/order as build_canon
        if self.dead_zones:
            hm = _f(row, "fillhm")
            if math.isnan(hm):
                et = pd.to_datetime(row["fill"], utc=True).tz_convert(NY_TZ)
                hm = et.hour * 60 + et.minute
            for z0, z1 in self.dead_zones:
                if z0 <= hm < z1:
                    if size > 0:
                        vetoes.append("dead_zone")
                    size = 0.0
                    break
        # news blackout — after the ladder, before the nth slot is consumed
        if self.news_gate is not None and size >= 0:
            et = pd.to_datetime(row["fill"], utc=True).tz_convert(NY_TZ).tz_localize(None)
            if bool(self.news_gate.blocks(et)):
                if size > 0:
                    vetoes.append("news_blackout")
                size = 0.0
        # Layer 3 governor (state advances only at score>=4 rows, from prior hi trades)
        if score >= 4 and len(self._gov) == GOV_WINDOW:
            self._gov_cur = sum(self._gov) / GOV_WINDOW
        governor = 0.5 if (not math.isnan(self._gov_cur)
                           and self._gov_cur < GOV_WR_MIN) else 1.0
        # Layer 2b: the slot is consumed by any signal sized here, even if 2b then vetoes it
        nth = None
        if size > 0:
            self._day_taken += 1
            nth = self._day_taken
            if nth >= 2 and score < 4:
                size, _ = 0.0, vetoes.append("nth_escalation")
        taken_for_cold = size > 0
        # Layer 2e sizing mods (cold state advances only at taken rows, from prior taken)
        if taken_for_cold and len(self._cold) == COLD_WINDOW:
            self._cold_cur = sum(self._cold) / COLD_WINDOW
        cold = not math.isnan(self._cold_cur) and self._cold_cur < COLD_WR_MIN
        r1 = cold and _f(row, "churn_flow_30") > R1_CHURN_MIN
        r2 = _f(row, "netpath_30") >= R2_NETPATH_MIN and not r1
        if r1:
            size, _ = size * 0.5, vetoes.append("r1_cold_grind_half")
        elif r2:
            size *= 1.5
        # Layer 2c day ladder (realized prior losses only)
        live = size > 0
        if live and (self._day_out or (self._day_pl < 0 and struct < 2
                                       and row["pattern"] != "A")):
            size, live = 0.0, False
            vetoes.append("day_ladder_drop")
        v = NYVerdict(day=day, fill=row["fill"], window=window, score=score, size=size,
                      governor=governor, nth=nth, Q=Q, struct=struct, checks=c, risk=risk,
                      vetoes=vetoes)
        v._hi, v._taken_for_cold, v._live = score >= 4, taken_for_cold, live
        self._pending = v
        return v

    def settle(self, v: NYVerdict, *, r_3: float, fw_3: float, dollars: float) -> float:
        """Feed the signal's outcome (engine-derived for untaken signals). Returns pl."""
        if v.hard_gated:
            return 0.0
        if self._pending is not v:
            raise RuntimeError("settle() called out of order")
        self._pending = None
        r_3, fw_3, dollars = float(r_3), float(fw_3), float(dollars)
        _, eff = eff_dollars(r_3=r_3, fw_3=fw_3, risk=v.risk, dollars=dollars)
        pl = eff * v.size * v.governor
        if v._hi:
            self._gov.append(eff > 0)
        if v._taken_for_cold:
            self._cold.append(eff > 0)
        if v._live:
            self._day_pl += pl
            if self._day_pl <= DAY_STOP_DOLLARS:
                self._day_out = True
        return pl


# ---- London -----------------------------------------------------------------------------
def london_checks(row: Mapping) -> dict[str, float]:
    long = row["direction"] == "long"
    sgn = 1.0 if long else -1.0
    wall_behind_d = _f(row, "dep_wall_below_d") if long else _f(row, "dep_wall_above_d")
    wall_ahead_d = _f(row, "dep_wall_above_d") if long else _f(row, "dep_wall_below_d")
    risk = _f(row, "risk")
    room = ((1 - _f(row, "ent_on_pos")) if long else _f(row, "ent_on_pos")) * _f(row, "on_range")
    room_r = room / risk
    return {"W": float(math.isnan(wall_behind_d)),
            "FAR": float(wall_ahead_d > LON_FAR_MIN),
            "ROOM": float(LON_ROOM_LO < room_r <= LON_ROOM_HI),
            "ASIA": float(_f(row, "cvd_ASIA") * sgn >= LON_ASIA_MIN),
            "room_R": room_r}


def _ladder_london(score: float) -> float:
    if score <= 1:
        return 0.0
    return {2: 0.5, 3: 1.0, 4: 1.5}.get(int(score), 0.0)


@dataclass
class LondonVerdict:
    day: str
    fill: object
    score: float
    size: float
    nth: int | None
    checks: dict
    vetoes: list
    hard_gated: bool = False


@dataclass
class LondonScorer:
    """Sequential build_london. No outcomes needed — London has no trails, no governor,
    no in-trade cut (all verified EV-null/negative; the engine's management harvests the
    alpha). decide() is self-contained; pl = dollars * size is the caller's arithmetic."""
    _day: str | None = field(default=None, init=False)
    _day_taken: int = field(default=0, init=False)

    def decide(self, row: Mapping) -> LondonVerdict:
        day, risk = str(row["day"]), _f(row, "risk")
        if day != self._day:
            self._day, self._day_taken = day, 0
        c = london_checks(row)
        if not risk >= LON_RISK_MIN:     # NaN risk fails too — hard gate
            return LondonVerdict(day=day, fill=row["fill"], score=math.nan, size=0.0,
                                 nth=None, checks=c, vetoes=["hard_gate_risk"],
                                 hard_gated=True)
        score = c["W"] + c["FAR"] + c["ROOM"] + c["ASIA"]
        size, vetoes = _ladder_london(score), []
        # Layer 2p: score-2 continuation (B) is a bleeder
        if row["pattern"] == "B" and score == 2 and size > 0:
            size, _ = 0.0, vetoes.append("pattern_b_score2")
        # Layer 2f: order-flow stack
        opp5 = _f(row, "opp5")
        struct = c["W"] + c["FAR"] + c["ROOM"]
        of2 = c["ASIA"] == 1 and opp5 < 2
        of0 = c["ASIA"] == 0 and opp5 >= 2
        if size > 0 and struct >= 2 and of2:
            size = min(size * 1.5, 1.5)
        if size > 0 and of0 and score == 2:
            size, _ = 0.0, vetoes.append("of_stack_zero")
        if size > 0 and of0:
            size, _ = size * 0.5, vetoes.append("of_stack_half")
        # Layer 2b: nth escalation (slot consumed by any signal sized here)
        nth = None
        if size > 0:
            self._day_taken += 1
            nth = self._day_taken
            if nth >= 2 and score < 3:
                size, _ = 0.0, vetoes.append("nth_escalation")
        return LondonVerdict(day=day, fill=row["fill"], score=score, size=size, nth=nth,
                             checks=c, vetoes=vetoes)
