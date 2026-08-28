#!/usr/bin/env python3
"""OFFLINE BRIEFING GENERATOR — the Mac orchestrator's numbers, without the Mac.

    from scripts.offline_briefings import get_bars, build_levels, ...

The replay orchestrator on his Mac assembles agent briefings from committed
bars: `levels_at_decision_CHART` is EMPTY in every saved briefing — the chart
speaks only through the screenshot legend — so every number an agent reasons
over is BUILD-side and therefore recomputable here, offline, with no
TradingView in the loop.

This module produces those numbers by CALLING THE SAME CODE the Mac path
uses — `src/htf_ma/levels.py` for VWAP/BB, `scripts/agent_context.py` for the
profiles, `scripts/htf_level_behavior.py` for the T46 blocks — never by
reimplementing it. Where the Mac path has a convention (integer profile bins,
fibs from the session low, 2dp rounding, the as-of row), this module matches
it and `scripts/certify_offline_briefings.py` PROVES the match against every
briefing the Mac has ever served, field by field.

WHAT THIS DOES NOT DO. It generates the DETERMINISTIC briefing fields.
Cascade fields (thesis, macro, prior_thesis), position/window state, and the
run-specific prose (leak_check, provenance) belong to the harness that drives
a day; the screenshot has no offline equivalent until the chart renderer is
certified. Those are marked, not faked.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.agent_context import (anchored_weekly_profile,      # noqa: E402
                                   volume_profile)
from scripts.build_l2_outcomes import load_bars                  # noqa: E402
from scripts.htf_level_behavior import behavior_at               # noqa: E402
from src.htf_ma.levels import NY, bb_ma_asof, vwap_bands         # noqa: E402

FIBS = (0.382, 0.5, 0.618, 0.705)      # the day-range set in the briefings
BB_TFS = (2, 3, 15, 60)

# The scanner's second-leg population (runbook R2 step 2: "VWAP band / POC /
# profile edge"), pinned by certification against the saved
# `levels_closed_SCANNER` lists: vwap bands, the DAILY value area, and the
# 15m MA — not the weekly/prior-day edges, not the other small-TF MAs (v44
# briefings cross those and the served scanner does not report them; the
# briefing's levels_closed_note exists precisely so the agent can correct).
SCANNER_LEVELS = ("vwap", "vwap_p1", "vwap_p2", "vwap_p3",
                  "vwap_m1", "vwap_m2", "vwap_m3",
                  "daily_poc", "daily_val", "daily_vah", "bb_ma_15m")
SEQ_CANDLES = 3               # runbook R2: a lone own-MA closure lives this long

_BARS = None


def get_bars() -> pd.DataFrame:
    """1m bars indexed NY, cached for the process."""
    global _BARS
    if _BARS is None:
        b = load_bars()
        b["mi"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
        _BARS = b.set_index("mi").sort_index()[
            ["open", "high", "low", "close", "volume"]]
    return _BARS


def session_bounds(sess_day: str, minute: str):
    """(t0, t): session open and the decision minute inside that session."""
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    # DST-safe: fall-back makes 01:00-01:59 ambiguous, spring-forward makes
    # 02:00-02:59 nonexistent. Neither can occur in the certified 03:00+
    # windows, so this changes nothing there; it makes the full-day Asia
    # sweep (00:00-02:59) survive the two transition nights a year.
    t = pd.Timestamp(f"{sess_day} {minute}").tz_localize(
        NY, ambiguous=True, nonexistent="shift_forward")
    if t < t0:
        t += pd.Timedelta(days=1)
    if not (t0 <= t < t0 + pd.Timedelta(hours=23)):
        raise ValueError(f"{minute} outside session-day {sess_day}")
    return t0, t


def all_session_days(bars: pd.DataFrame) -> list[str]:
    d = (bars.index - pd.Timedelta(hours=18)).normalize()
    return sorted({str(x.date()) for x in d.unique()})


def _asof_row(series_frame, t: pd.Timestamp):
    """The as-of row for a decision at t: the last row stamped strictly
    before t. Row t-1m closes AT t, so it is the newest legal value."""
    s = series_frame[series_frame.index < t]
    if s.empty:
        raise ValueError(f"no bars before {t}")
    return s.iloc[-1]


def hist_before(bars: pd.DataFrame, t0: pd.Timestamp, t: pd.Timestamp,
                lookback_rows: int = 2400) -> pd.DataFrame:
    """Session bars plus enough PRIOR TRADED bars for every indicator.

    Measured in bars, not hours: a wall-clock window (the first cut was
    36h) silently starves the 60m BB MA (19 completed hours needed) on any
    session that opens across the weekend gap — every Monday label. Caught
    by certification against wk1 Monday, where bb_ma_60m came back NaN.
    2400 rows ≈ 40 traded hours, enough for BB(20) on 60m with margin.
    """
    idx = bars.index
    pos = int(np.searchsorted(idx.values, t0.to_datetime64()))
    start = idx[max(pos - lookback_rows, 0)]
    return bars[(idx >= start) & (idx < t)]


def candle(bars: pd.DataFrame, t: pd.Timestamp, tf: int) -> dict | None:
    """The tf-minute candle that CLOSES exactly at t, as the briefing shows
    it (start/closed_at strings, int volume)."""
    seg = bars[(bars.index >= t - pd.Timedelta(minutes=tf)) & (bars.index < t)]
    if seg.empty:
        return None
    return {"start": f"{t - pd.Timedelta(minutes=tf):%H:%M}",
            "closed_at": f"{t:%H:%M}",
            "open": float(seg.open.iloc[0]), "high": float(seg.high.max()),
            "low": float(seg.low.min()), "close": float(seg.close.iloc[-1]),
            "volume": int(seg.volume.sum()), "minutes": tf}


def completed_tf_bars(bars: pd.DataFrame, t0: pd.Timestamp, t: pd.Timestamp,
                      tf: int) -> pd.DataFrame:
    """Completed tf-bars of this session as of t (close time <= t),
    indexed by close time — the repo's label=right, closed=left grid."""
    seg = bars[(bars.index >= t0) & (bars.index < t)]
    f = seg.resample(f"{tf}min", label="right", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last",
         "volume": "sum"}).dropna(subset=["open"])
    return f[f.index <= t]


def build_levels(bars: pd.DataFrame, sess_day: str, minute: str,
                 all_days: list[str] | None = None) -> dict:
    """`levels_at_decision_BUILD` + price_at_decision, the Mac conventions."""
    t0, t = session_bounds(sess_day, minute)
    if all_days is None:
        all_days = all_session_days(bars)
    hist = hist_before(bars, t0, t)
    seg = hist[hist.index >= t0]
    if seg.empty:
        raise ValueError(f"no session bars for {sess_day} {minute}")

    vw = _asof_row(vwap_bands(hist), t)
    vwap = {k: round(float(vw[k]), 2) for k in
            ("vwap", "vwap_p1", "vwap_p2", "vwap_p3",
             "vwap_m1", "vwap_m2", "vwap_m3")}

    bb = {}
    for tf in BB_TFS:
        ma, _ = bb_ma_asof(hist, tf)
        bb[f"bb_ma_{tf}m"] = round(float(_asof_row(ma.to_frame("v"), t).v), 2)

    s_hi, s_lo = float(seg.high.max()), float(seg.low.min())
    fibs = {str(f): round(s_lo + f * (s_hi - s_lo), 2) for f in FIBS}

    d_poc, d_val, d_vah = volume_profile(seg)
    aw = anchored_weekly_profile(bars, sess_day, upto=t)

    i = all_days.index(sess_day) if sess_day in all_days else -1
    prior = {}
    if i > 0:
        pa = pd.Timestamp(f"{all_days[i - 1]} 18:00", tz=NY)
        pseg = bars[(bars.index >= pa) & (bars.index < t0)]
        p_poc, p_val, p_vah = volume_profile(pseg)
        prior = {"poc": p_poc, "val": p_val, "vah": p_vah,
                 "high": float(pseg.high.max()), "low": float(pseg.low.min())}

    return {
        "price_at_decision": float(seg.close.iloc[-1]),
        "levels_at_decision_BUILD": {
            "vwap": vwap,
            "bb_ma": bb,
            "day_range_fibs": fibs,
            "session_high_so_far": s_hi,
            "session_low_so_far": s_lo,
            "daily_profile": {"poc": d_poc, "val": d_val, "vah": d_vah,
                              "note": f"DEVELOPING as-of {t:%H:%M}"},
            "anchored_weekly_profile": {
                "poc": aw["awPOC"], "val": aw["awVAL"], "vah": aw["awVAH"],
                "high": aw["awHIGH"], "low": aw["awLOW"],
                "anchor": str(aw["anchor"]),
                "note": f"DEVELOPING as-of {t:%H:%M}"},
            "prior_day": prior,
        },
    }


def level_map(build: dict) -> dict[str, float]:
    """Flat name->price map of every level in the BUILD dict, briefing names."""
    L = build["levels_at_decision_BUILD"]
    out = dict(L["vwap"])
    out.update(L["bb_ma"])
    out.update({f"fib_{k}": v for k, v in L["day_range_fibs"].items()})
    out["session_high"] = L["session_high_so_far"]
    out["session_low"] = L["session_low_so_far"]
    for src, pre in (("daily_profile", "daily"),
                     ("anchored_weekly_profile", "weekly"),
                     ("prior_day", "prior_day")):
        d = L.get(src) or {}
        for k in ("poc", "val", "vah", "high", "low"):
            if k in d and d[k] is not None and np.isfinite(d[k]):
                out[f"{pre}_{k}"] = float(d[k])
    return out


def above_below(build: dict) -> tuple[list[str], list[str]]:
    """`levels_above_price` / `levels_below_price` — every level, unfiltered,
    nearest first, formatted exactly as the briefings print them."""
    px = build["price_at_decision"]
    lm = level_map(build)

    def fmt(name, v):
        return f"{name} {round(v, 2)}"

    above = sorted(((v, n) for n, v in lm.items() if v > px))
    below = sorted(((v, n) for n, v in lm.items() if v <= px), reverse=True)
    return [fmt(n, v) for v, n in above], [fmt(n, v) for v, n in below]


def _crossed(o: float, c: float, level: float) -> bool:
    return (o - level) * (c - level) < 0


def scanner_closed(bars: pd.DataFrame, build: dict, sess_day: str,
                   minute: str) -> list[str]:
    """The mechanical scanner's `levels_closed_SCANNER` read, as the Mac
    serves it: an own-MA tag naming the SIGNAL timeframe, then the second
    levels that tf's candle closed through.

    Conventions recovered by certification against the served lists:
      - both TFs through their own MA this minute -> "own_ma_2m_and_3m",
        second levels the union of both candles' closes-through;
      - exactly one TF through its own MA -> that tf is the signal; second
        levels from ITS candle only (the other candle's crossings are NOT
        reported, even when real — the levels_closed_note delegates the
        correction to the agent);
      - neither through now -> sequential pair: the most recent lone own-MA
        closure within SEQ_CANDLES candles of its tf, tagged
        "own_ma_{tf}m_at_{start}", second levels from the current candle of
        that tf.
    """
    lm = level_map(build)
    t0, t = session_bounds(sess_day, minute)

    def seconds_of(cndl):
        return [n for n in SCANNER_LEVELS
                if n in lm and _crossed(cndl["open"], cndl["close"], lm[n])]

    cn, own_now = {}, {}
    for tf in (2, 3):
        cn[tf] = candle(bars, t, tf) if ((t - t0).total_seconds() / 60) % tf == 0 \
            else None
        own_now[tf] = bool(cn[tf]) and _crossed(cn[tf]["open"], cn[tf]["close"],
                                                lm.get(f"bb_ma_{tf}m", np.nan))

    if own_now[2] and own_now[3]:
        seen, seconds = set(), []
        for tf in (2, 3):
            for n in seconds_of(cn[tf]):
                if n not in seen:
                    seen.add(n)
                    seconds.append(n)
        return ["own_ma_2m_and_3m"] + [n for n in SCANNER_LEVELS
                                       if n in seen]
    for tf in (2, 3):
        if own_now[tf]:
            return [f"own_ma_{tf}m"] + seconds_of(cn[tf])

    # sequential: a lone own-MA closure still live, paired with a second
    # level crossed now. MA is read as-of the earlier candle's close.
    hist = hist_before(bars, t0, t)
    best = None                                    # (age_minutes, tag, tf)
    for tf in (2, 3):
        if cn[tf] is None:
            continue
        ma, _ = bb_ma_asof(hist, tf)
        for k in range(1, SEQ_CANDLES + 1):
            ce = t - pd.Timedelta(minutes=k * tf)
            prev = candle(bars, ce, tf)
            if prev is None:
                continue
            row = ma[ma.index < ce]
            if row.empty or not np.isfinite(row.iloc[-1]):
                continue
            if _crossed(prev["open"], prev["close"], float(row.iloc[-1])):
                age = k * tf
                if best is None or age < best[0]:
                    best = (age, f"own_ma_{tf}m_at_{prev['start']}", tf)
                break
    if best is not None:
        return [best[1]] + seconds_of(cn[best[2]])
    for tf in (3, 2):
        if cn[tf] is not None:
            return seconds_of(cn[tf])
    return []


def htf_blocks(bars: pd.DataFrame, sess_day: str, minute: str,
               levels: dict[str, float]) -> dict:
    """`higher_timeframe_at_candidate_levels` — same script the Mac runs,
    called with the same (rounded) prices the briefing prints."""
    return {name: behavior_at(bars, sess_day, minute, float(px))
            for name, px in levels.items()}


def last_15m_candles(bars: pd.DataFrame, sess_day: str, minute: str,
                     n: int = 4) -> list[dict]:
    t0, t = session_bounds(sess_day, minute)
    f = completed_tf_bars(bars, t0, t, 15).tail(n)
    out = []
    for ts, b in f.iterrows():
        rng = float(b.high - b.low)
        out.append({"start": f"{ts - pd.Timedelta(minutes=15):%H:%M}",
                    "open": float(b.open), "high": float(b.high),
                    "low": float(b.low), "close": float(b.close),
                    "body_ratio": round(abs(b.close - b.open) / rng, 2)
                    if rng > 0 else 0.0})
    return out


def flush_inputs(bars: pd.DataFrame, sess_day: str, minute: str) -> dict:
    """path_efficiency = |net move| / summed 15m body travel, session to
    date — the thesis briefing's flush shape numbers."""
    t0, t = session_bounds(sess_day, minute)
    f = completed_tf_bars(bars, t0, t, 15)
    if f.empty:
        return {}
    bodies = (f.close - f.open).astype(float)
    total = float(bodies.abs().sum())
    # net move is served SIGNED (the direction is information); only the
    # efficiency ratio takes the magnitude.
    net = float(f.close.iloc[-1] - f.open.iloc[0])
    return {"path_efficiency": round(abs(net) / total, 3) if total > 0 else 0.0,
            "net_move_15m": round(net, 2),
            "total_15m_travel": round(total, 2),
            "candles_15m_up": int((bodies > 0).sum()),
            "candles_15m_down": int((bodies < 0).sum())}


def recent_2m_bars(bars: pd.DataFrame, sess_day: str, minute: str,
                   n: int = 4) -> list[dict]:
    """The manage briefing's last-n 2m bars — anchored to the CALL MINUTE,
    not the session's even grid. A manage call at an odd minute (a 3m
    position's timeline) gets odd-grid 2m bars: [t-8,t-6) ... [t-2,t)."""
    _, t = session_bounds(sess_day, minute)
    out = []
    for k in range(n, 0, -1):
        c = candle(bars, t - pd.Timedelta(minutes=2 * (k - 1)), 2)
        if c is not None:
            out.append(c)
    return out
