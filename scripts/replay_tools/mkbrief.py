"""Build a trigger briefing with every candle DERIVED, never typed.

Two defects this run came from hand-typing numbers into a briefing: a session high
that was 40 points wrong, and a 3m close that was actually the next minute's close
and inverted a verdict. Both were typing, not reasoning. So nothing here is typed:
the signal candle, the last completed lower-timeframe bar, the price at decision and
the session extremes are all aggregated from committed bars, and factbrief's guard
re-derives them a second time and refuses any disagreement.

The caller supplies only what genuinely requires judgement - which candidate, which
direction the signal fired, which levels closed - and never a price.
"""
import json
import sys

import pandas as pd

sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
sys.path.insert(0, "/Users/barbelldaddy/.claude/jobs/bdd15866/tmp")

from scripts.build_l2_outcomes import load_bars
from src.htf_ma.levels import NY
import factbrief

_BARS = None


def bars():
    global _BARS
    if _BARS is None:
        b = load_bars()
        b["mi"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
        _BARS = b.set_index("mi").sort_index()[["open", "high", "low", "close", "volume"]]
    return _BARS


def _agg(day, start, end):
    b = bars()
    seg = b[(b.index >= pd.Timestamp(f"{day} {start}", tz=NY)) & (b.index < pd.Timestamp(f"{day} {end}", tz=NY))]
    if not len(seg):
        return None
    return {"start": start, "closed_at": end, "open": float(seg.iloc[0].open),
            "high": float(seg.high.max()), "low": float(seg.low.min()),
            "close": float(seg.iloc[-1].close), "volume": int(seg.volume.sum())}


def _back(day, end_hhmm, minutes):
    e = pd.Timestamp(f"{day} {end_hhmm}", tz=NY)
    return (e - pd.Timedelta(minutes=minutes)).strftime("%H:%M")


def _repair(lv, day_next, sess_day, dec):
    """Recompute cached fields that came back null, instead of trusting the hole.

    The precap cache for 2026-06-23 03:27 has null fib, null session extremes and a
    null last 2m bar - a partially-failed precap run. These are all derivable from
    committed bars, so a gap is repairable rather than fatal. Left unrepaired it
    would either crash (which is fine) or, far worse, reach a briefing as a zero or
    a stale neighbouring minute's value, which is the shape of the session-high
    defect an agent had to catch earlier this run.

    The developing day range is measured from the 18:00 session anchor to the
    decision minute, exclusive - never to the end of the day.
    """
    b = bars()
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t = pd.Timestamp(f"{day_next} {dec}", tz=NY)
    seg = b[(b.index >= t0) & (b.index < t)]
    if not len(seg):
        raise ValueError(f"no bars between the 18:00 anchor and {dec}")
    hi, lo = float(seg.high.max()), float(seg.low.min())

    if lv.get("session_high_so_far") is None:
        lv["session_high_so_far"] = hi
    if lv.get("session_low_so_far") is None:
        lv["session_low_so_far"] = lo
    if lv.get("fib") is None:
        rng = hi - lo
        lv["fib"] = {f"{f}": round(lo + f * rng, 2) for f in (0.382, 0.5, 0.618, 0.705)}
    if lv.get("last_2m_bar") is None:
        lv["last_2m_bar"] = _agg(day_next, _back(day_next, dec, 2), dec)

    # whatever the cache DID hold must still agree with the bars
    for k, truth in (("session_high_so_far", hi), ("session_low_so_far", lo)):
        if abs(float(lv[k]) - truth) > 1e-6:
            raise ValueError(f"cached {k} {lv[k]} disagrees with the bars ({truth}) at {dec}")


def build(cid, day_next, sess_day, dec, window, session, shot, jsonl, levels_path,
          direction, levels_closed, position_state, fills, cap,
          pair_shape="same_candle", tf="3m", extra_note=None, thesis=None):
    lv = json.load(open(levels_path))[dec]
    _repair(lv, day_next, sess_day, dec)
    if thesis is None:
        rows = [json.loads(l) for l in open(jsonl)]
        # A re-fired thesis REPLACES the window's opening one, so it must be
        # eligible here. Matching only row == "thesis" silently served the dead
        # 09:30 long thesis to the 10:14 candidate on 2026-06-24, after price had
        # broken its invalidation by 500 points and Tier 1 had already been
        # re-fired short. The trigger noticed and returned thesis_stale, but it
        # was reasoning against a thesis that no longer existed.
        live = [r["output"] for r in rows if r.get("row") in ("thesis", "thesis_refire")]
        if not live:
            raise ValueError("no thesis or thesis_refire row in the run log yet")
        thesis = live[-1]

    c3 = _agg(day_next, _back(day_next, dec, 3), dec)
    c2 = _agg(day_next, _back(day_next, dec, 2), dec)
    c3["direction"] = direction

    b = bars()
    prev = b[b.index < pd.Timestamp(f"{day_next} {dec}", tz=NY)]
    px = float(prev.iloc[-1].close)

    V, M = lv["vwap"], lv["bb_ma"]
    named = {"session VWAP": V["vwap"], "vwap_p1": V["vwap_p1"], "vwap_m1": V["vwap_m1"],
             "vwap_p2": V["vwap_p2"], "vwap_m2": V["vwap_m2"],
             "own 2m MA": M["2m"], "own 3m MA": M["3m"], "15m MA": M["15m"], "60m MA": M["60m"],
             "developing daily POC": lv["daily"]["poc"], "developing daily VAH": lv["daily"]["vah"],
             "developing daily VAL": lv["daily"]["val"],
             "prior-day POC": lv["prior_day"]["poc"], "prior-day VAH": lv["prior_day"]["vah"],
             "prior-day VAL": lv["prior_day"]["val"],
             "fib 0.382": lv["fib"]["0.382"], "fib 0.5": lv["fib"]["0.5"],
             "fib 0.618": lv["fib"]["0.618"], "fib 0.705": lv["fib"]["0.705"],
             "session high so far": lv["session_high_so_far"],
             "session low so far": lv["session_low_so_far"]}
    above = sorted(((v, k) for k, v in named.items() if v > px))
    below = sorted(((v, k) for k, v in named.items() if v < px), reverse=True)
    tgt = ("ABOVE " + str(px) + ": " + ", ".join(f"{k} {v}" for v, k in above) +
           ". BELOW: " + ", ".join(f"{k} {v}" for v, k in below) + ".")

    trunc = (f"pass - truncated at {_back(day_next, dec, 1)}:59. The {tf} bar starting {c3['start']} and the "
             f"2m bar starting {c2['start']} both complete AT {dec}. No value in this briefing was typed by "
             f"hand: every candle, the price at decision and the session extremes are aggregated from "
             f"committed bars and re-derived a second time by the builder's guard, which refuses to emit a "
             f"briefing whose stated numbers disagree with the bars or whose candle closes after {dec}.")

    ex = {"entry_geometry_note": "the orchestrator validates entry arithmetic before simulating. For a LONG the "
          "limit sits BELOW current price and cancel_if_reaches sits ABOVE both the price and the limit; for a "
          "SHORT, mirrored."}
    if extra_note:
        ex["direction_note"] = extra_note

    return factbrief.trigger(
        cid=cid, window=window, session=session, dm=f"{day_next}T{dec} ET",
        candle_start=f"{c3['start']} ({tf}) / {c2['start']} (2m)", tf=tf, trunc=trunc, shot=shot,
        thesis=thesis, lv=lv,
        chart={"vwap": V["vwap"], "vwap_p1": V["vwap_p1"], "vwap_m1": V["vwap_m1"],
               "vwap_p2": V["vwap_p2"], "vwap_m2": V["vwap_m2"], "bb_ma_2m": M["2m"],
               "bb_ma_3m": M["3m"], "bb_ma_15m": M["15m"], "bb_ma_60m": M["60m"]},
        signals={"signal_candle_3m": c3, "last_completed_2m_bar": c2,
                 "session_high_this_session": lv["session_high_so_far"],
                 "session_low_this_session": lv["session_low_so_far"]},
        pair_shape=pair_shape, levels_closed=levels_closed, price=px,
        position_state=position_state, fills=fills, cap=cap, levels_for_targets=tgt, extra=ex)
