"""HTF-structure agent (assignment #2) — nested 4H/daily structure judgment.

docs/TASK-FOR-PAT-regime-agent.md assignment #2, same desk contract as
src/desk/regime_agent.py (strict JSON, fail-closed, single 08:00-ET cutoff,
journaled blobs, zero-tools agent file).

The judgment this agent owns: the engine's LTF "reversals" are only safe when
they fade a 4H leg that is a ROTATION inside a contained daily range; fading a
leg that is a SEGMENT of a genuine higher-TF trend is fatal. Mechanical k=2
swing classification whipsaws exactly when it matters — the nesting call is the
agent's job. The mechanical reads are therefore INCLUDED in the briefing as the
baseline the agent must beat or consciously endorse.

Sanctioned interlock (task doc): the same day's regime-agent verdict, when one
exists, is part of this briefing ("war regime => legs are trend segments =>
fades off"). This is a one-directional, journaled, Angus-specified dependency —
distinct from the forbidden grader-to-grader visibility in the unanimity Desk.

4H bars are SESSION-ANCHORED here (18:00 ET open -> bins at 18/22/02/06/10/14
wall-clock ET, DST-safe): the engine's resampler is midnight-origin and its
session-anchored 4H was deferred (blueprint I-7); this desk-side resampler is
briefing input prep, not an engine change.
"""

from __future__ import annotations

import json
from datetime import datetime, time as dtime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
from pydantic import BaseModel, field_validator, model_validator

NY = ZoneInfo("America/New_York")
CUTOFF_ET = dtime(8, 0)
SWING_K = 2                     # the mechanical baseline's fractal lookback
DAILY_BARS_IN_BRIEFING = 60
H4_BARS_IN_BRIEFING = 30
AGENT_FILE = Path(".claude/agents/htf-structure.md")

DAILY_CONTEXTS = ("range", "trend_up", "trend_down", "unknown")
H4_LEGS = ("up", "down", "range")
NESTINGS = ("rotation", "trend_segment", "unknown")


# ------------------------------------------------------------------ verdict schema

class HTFStructureVerdict(BaseModel, extra="forbid"):
    """Strict-JSON daily structure verdict (task-doc contract + desk fields)."""

    schema_version: str
    agent_version: str
    date: str
    daily_context: str            # range | trend_up | trend_down | unknown
    h4_leg: str                   # up | down | range
    h4_leg_nested_as: str         # rotation | trend_segment | unknown — THE judgment
    fade_permitted: bool
    continuation_only: bool
    confidence: str               # low | medium | high
    rationale: str                # <= 600 chars, briefing facts only
    cited_evidence: list[str]     # 1..8 briefing-field references
    playbook_notes: str           # <= 1500 chars adaptation memory

    @field_validator("daily_context")
    @classmethod
    def _dc(cls, v: str) -> str:
        if v not in DAILY_CONTEXTS:
            raise ValueError(f"daily_context must be one of {DAILY_CONTEXTS}")
        return v

    @field_validator("h4_leg")
    @classmethod
    def _leg(cls, v: str) -> str:
        if v not in H4_LEGS:
            raise ValueError(f"h4_leg must be one of {H4_LEGS}")
        return v

    @field_validator("h4_leg_nested_as")
    @classmethod
    def _nest(cls, v: str) -> str:
        if v not in NESTINGS:
            raise ValueError(f"h4_leg_nested_as must be one of {NESTINGS}")
        return v

    @field_validator("confidence")
    @classmethod
    def _conf(cls, v: str) -> str:
        if v not in ("low", "medium", "high"):
            raise ValueError("confidence must be low|medium|high")
        return v

    @field_validator("rationale")
    @classmethod
    def _rat(cls, v: str) -> str:
        if not v or len(v) > 600:
            raise ValueError("rationale must be 1..600 chars")
        return v

    @field_validator("cited_evidence")
    @classmethod
    def _ev(cls, v: list[str]) -> list[str]:
        if not v or len(v) > 8:
            raise ValueError("cited_evidence must have 1..8 items")
        return v

    @field_validator("playbook_notes")
    @classmethod
    def _notes(cls, v: str) -> str:
        if len(v) > 1500:
            raise ValueError("playbook_notes must be <= 1500 chars")
        return v

    @model_validator(mode="after")
    def _consistency(self) -> "HTFStructureVerdict":
        if self.fade_permitted and self.continuation_only:
            raise ValueError("fade_permitted and continuation_only are mutually exclusive")
        if self.daily_context == "unknown" and self.fade_permitted:
            raise ValueError("fade_permitted requires a known daily_context (fail-safe)")
        if self.h4_leg_nested_as == "trend_segment" and self.fade_permitted:
            raise ValueError("a trend_segment leg must not permit fades (the core rule)")
        return self


class HTFGate(BaseModel, extra="forbid"):
    """Engine-consumable structure gate (one per session day)."""

    date: str
    fade_permitted: bool
    continuation_only: bool
    daily_context: str
    h4_leg: str


def verdict_to_gate(v: HTFStructureVerdict) -> HTFGate:
    return HTFGate(date=v.date, fade_permitted=v.fade_permitted,
                   continuation_only=v.continuation_only,
                   daily_context=v.daily_context, h4_leg=v.h4_leg)


# ------------------------------------------------------------------ structure math

def resample_h4(df_1m: pd.DataFrame) -> pd.DataFrame:
    """Session-anchored 4H bars: bins start 18/22/02/06/10/14 wall-clock ET.

    Wall-clock anchoring makes the 18:00 session open a bin edge on both sides
    of a DST change (tz library does the offsets; no offset arithmetic here).
    Only COMPLETE input coverage matters to the caller: the last (possibly
    partial) bin is dropped so a briefing never contains a forming 4H bar.
    """
    ts = df_1m["ts_event"].dt.tz_convert(NY)
    mins = ts.dt.hour * 60 + ts.dt.minute
    bin_start_min = ((mins - 18 * 60) % (24 * 60)) // 240 * 240
    start_delta = pd.to_timedelta((mins - 18 * 60) % (24 * 60) - bin_start_min, unit="m")
    bin_start = ts - start_delta
    g = df_1m.assign(_bin=bin_start.dt.floor("min")).groupby("_bin", sort=True)
    out = pd.DataFrame({
        "open": g["open"].first(), "high": g["high"].max(),
        "low": g["low"].min(), "close": g["close"].last(),
    }).reset_index(names="ts_open")
    return out.iloc[:-1] if len(out) else out    # drop the forming bin


def fractal_swings(bars: pd.DataFrame, label_col: str, k: int = SWING_K) -> dict:
    """Mechanical k-fractal swings (the baseline read the agent judges).

    A swing high is strictly higher than the k bars each side (mirror for lows).
    Returns the last 6 of each as (label, price) pairs, oldest -> newest.
    """
    hi, lo = bars["high"].to_numpy(), bars["low"].to_numpy()
    labels = bars[label_col].astype(str).to_numpy()
    sh, sl = [], []
    for i in range(k, len(bars) - k):
        if hi[i] > max(*hi[i - k:i], *hi[i + 1:i + k + 1]):
            sh.append((labels[i], round(float(hi[i]), 2)))
        if lo[i] < min(*lo[i - k:i], *lo[i + 1:i + k + 1]):
            sl.append((labels[i], round(float(lo[i]), 2)))
    return {"swing_highs": sh[-6:], "swing_lows": sl[-6:]}


def mech_classify(swings: dict) -> str:
    """The engine's HH/HL–LH/LL mapping over the last two confirmed swings."""
    sh = [p for _, p in swings["swing_highs"]]
    sl = [p for _, p in swings["swing_lows"]]
    if len(sh) < 2 or len(sl) < 2:
        return "unknown"
    up = sh[-1] > sh[-2] and sl[-1] > sl[-2]
    down = sh[-1] < sh[-2] and sl[-1] < sl[-2]
    return "trend_up" if up else "trend_down" if down else "range"


def mech_leg(swings: dict, last_price: float) -> dict:
    """Mechanical current-leg read: direction from the most recent confirmed swing."""
    candidates = []
    if swings["swing_highs"]:
        candidates.append(("high", *swings["swing_highs"][-1]))
    if swings["swing_lows"]:
        candidates.append(("low", *swings["swing_lows"][-1]))
    if not candidates:
        return {"direction": "range", "from_swing": None, "travel_pts": None}
    kind, label, price = max(candidates, key=lambda c: c[1])   # newest by label
    direction = "up" if kind == "low" and last_price > price else \
                "down" if kind == "high" and last_price < price else "range"
    return {"direction": direction, "from_swing": {"kind": kind, "at": label, "price": price},
            "travel_pts": round(last_price - price, 2)}


# ------------------------------------------------------------------ briefing

def _r(x: float, nd: int = 2) -> float:
    return round(float(x), nd)


def build_structure_briefing(
    date: str,
    df_1m: pd.DataFrame,
    regime_verdicts: pd.DataFrame | None = None,
    playbook_notes: str = "",
) -> dict:
    """Pre-open structure briefing for `date`. ONE cutoff (08:00 ET), applied here."""
    cutoff = pd.Timestamp(datetime.combine(pd.Timestamp(date).date(), CUTOFF_ET), tz=NY)
    past = df_1m[df_1m["ts_event"] < cutoff]
    if past.empty:
        raise ValueError(f"no bars before cutoff {cutoff} — cannot brief")

    # daily bars (CME 18:00 boundary), completed sessions only
    ts = past["ts_event"].dt.tz_convert(NY)
    sess = (ts + pd.Timedelta(hours=6)).dt.date
    frame = past.assign(_sd=sess)
    today_sd = pd.Timestamp(date).date()
    prior = frame[frame["_sd"] < today_sd]
    if prior.empty:
        raise ValueError(f"no completed sessions before {date}")
    g = prior.groupby("_sd", sort=True)
    daily = pd.DataFrame({
        "open": g["open"].first(), "close": g["close"].last(),
        "high": g["high"].max(), "low": g["low"].min(),
    }).reset_index(names="day")
    daily["day"] = daily["day"].astype(str)

    d_swings = fractal_swings(daily, "day")
    daily_rows = [
        {"day": r.day, "o": _r(r.open), "h": _r(r.high), "l": _r(r.low), "c": _r(r.close),
         "net": _r(r.close - r.open)}
        for r in daily.tail(DAILY_BARS_IN_BRIEFING).itertuples()
    ]

    # 4H bars (session-anchored), completed bins only, incl. today's overnight bins
    h4 = resample_h4(past)
    h4["label"] = h4["ts_open"].astype(str)
    h4_swings = fractal_swings(h4, "label")
    h4_rows = [
        {"t": r.label, "o": _r(r.open), "h": _r(r.high), "l": _r(r.low), "c": _r(r.close)}
        for r in h4.tail(H4_BARS_IN_BRIEFING).itertuples()
    ]

    last_px = float(past["close"].iloc[-1])

    # sanctioned interlock: today's regime verdict, if one has been produced
    interlock: dict | str = "no regime verdict available for this date"
    if regime_verdicts is not None and not regime_verdicts.empty:
        row = regime_verdicts[regime_verdicts["date"] == date]
        if not row.empty:
            r0 = row.iloc[0]
            interlock = {k: r0[k] for k in
                         ("regime", "directional_bias", "stand_down", "size_multiplier",
                          "confidence") if k in row.columns}

    return {
        "schema_version": "1.0",
        "date": date,
        "cutoff_et": cutoff.isoformat(),
        "last_price": _r(last_px),
        "daily_bars": daily_rows,
        "daily_swings_mechanical": {**d_swings, "classification": mech_classify(d_swings)},
        "h4_bars": h4_rows,
        "h4_swings_mechanical": {**h4_swings, "leg": mech_leg(h4_swings, last_px)},
        "location": {
            "vs_last_daily_swing_high": None if not d_swings["swing_highs"] else
                _r(last_px - d_swings["swing_highs"][-1][1]),
            "vs_last_daily_swing_low": None if not d_swings["swing_lows"] else
                _r(last_px - d_swings["swing_lows"][-1][1]),
        },
        "regime_verdict_today": interlock,
        "playbook_notes": playbook_notes or "(none yet)",
    }


# ------------------------------------------------------------------ parse (fail-closed)

def parse_verdict(raw: str, expect_date: str) -> HTFStructureVerdict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        text = text[4:] if text.startswith("json") else text
    v = HTFStructureVerdict.model_validate(json.loads(text))
    if v.date != expect_date:
        raise ValueError(f"verdict date {v.date} != briefing date {expect_date}")
    return v
