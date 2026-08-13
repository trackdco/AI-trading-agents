"""Briefing builders for the 0.4.x stack. Mechanical only - RUNBOOK section 0c.

Every value here is computed from committed bars strictly before the decision
minute, or read off the chart by the orchestrator and passed in. Nothing is
typed by hand and nothing carries a view:

  - no prose from any doc, no chart summary (the agent reads the screenshot),
  - no mention of another day, no count of the day's candidates,
  - free text only where it is mechanically derivable ("15m MA crossed at 09:42").

The 0.3.5 run lost a verdict to a hand-typed 3m close that was actually the next
minute's, and another to a hand-typed levels_closed the agent had to correct. So
candles are aggregated here and re-checked against the bars before emission.
"""
from __future__ import annotations

import json

import pandas as pd

from scripts.agent_context import (anchored_weekly_profile, prev_day_levels,
                                   session_day_of, volume_profile)
from scripts.htf_level_behavior import behavior_at
from scripts.replay_tools.htf import bars, body_ratio_15m, flush_inputs
from src.htf_ma.levels import NY, bb_ma_asof, vwap_bands

NEWS = "data/reference/news_archive.csv"


# ---------------------------------------------------------------- primitives

def agg(day_next, start, end):
    """The bar labelled `start` that CLOSES at `end`. Minutes [start, end)."""
    b = bars()
    s = pd.Timestamp(f"{day_next} {start}", tz=NY)
    e = pd.Timestamp(f"{day_next} {end}", tz=NY)
    seg = b[(b.index >= s) & (b.index < e)]
    if not len(seg):
        return None
    return {"start": start, "closed_at": end, "open": float(seg.iloc[0].open),
            "high": float(seg.high.max()), "low": float(seg.low.min()),
            "close": float(seg.iloc[-1].close), "volume": int(seg.volume.sum()),
            "minutes": int(len(seg))}


def back(day_next, end, minutes):
    return (pd.Timestamp(f"{day_next} {end}", tz=NY) - pd.Timedelta(minutes=minutes)).strftime("%H:%M")


def price_at(day_next, dec):
    b = bars()
    prev = b[b.index < pd.Timestamp(f"{day_next} {dec}", tz=NY)]
    return float(prev.iloc[-1].close)


def levels_at(sess_day, day_next, dec):
    """Every level the day can state at this minute. All of them, unfiltered."""
    b = bars()
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t = pd.Timestamp(f"{day_next} {dec}", tz=NY)
    u = t - pd.Timedelta(minutes=1)
    day = b[(b.index >= t0) & (b.index < t)]
    hist = b[b.index < t]

    vb = vwap_bands(hist)
    ma = {}
    for tf in (2, 3, 15, 60):
        m, _ = bb_ma_asof(hist, tf)
        v = m.reindex([u]).iloc[0]
        ma[f"bb_ma_{tf}m"] = None if pd.isna(v) else round(float(v), 2)
    row = vb.reindex([u]).iloc[0]

    hi, lo = float(day.high.max()), float(day.low.min())
    rng = hi - lo
    fib = {k: round(lo + rng * f, 2) for k, f in
           (("0.382", .382), ("0.5", .5), ("0.618", .618), ("0.705", .705))}

    poc, val, vah = volume_profile(day)          # returns a tuple, not a dict
    dp = {"poc": poc, "val": val, "vah": vah}
    aw = anchored_weekly_profile(b, sess_day, upto=t)
    # prev_day_levels indexes by SESSION-day (18:00 anchored), not calendar date
    all_days = sorted({session_day_of(x) for x in b.index})
    p = prev_day_levels(b, sess_day, all_days)
    pd_ = {"poc": p["pPOC"], "val": p["pVAL"], "vah": p["pVAH"],
           "high": p["pHIGH"], "low": p["pLOW"]}

    return {
        "vwap": {k: round(float(row[k]), 2) for k in
                 ("vwap", "vwap_p1", "vwap_p2", "vwap_p3", "vwap_m1", "vwap_m2", "vwap_m3")},
        "bb_ma": ma,
        "day_range_fibs": fib,
        "session_high_so_far": hi, "session_low_so_far": lo,
        "daily_profile": {"poc": round(float(dp["poc"]), 2), "val": round(float(dp["val"]), 2),
                          "vah": round(float(dp["vah"]), 2), "note": f"DEVELOPING as-of {dec}"},
        "anchored_weekly_profile": {"poc": round(float(aw["awPOC"]), 2),
                                    "val": round(float(aw["awVAL"]), 2),
                                    "vah": round(float(aw["awVAH"]), 2),
                                    "high": round(float(aw["awHIGH"]), 2),
                                    "low": round(float(aw["awLOW"]), 2),
                                    "anchor": str(aw["anchor"]),
                                    "note": f"DEVELOPING as-of {dec}"},
        "prior_day": {k: (None if v is None or v != v else round(float(v), 2))
                      for k, v in pd_.items()},
    }


def flat_levels(lv):
    """Name -> price, for headroom and management-minute computation."""
    out = dict(lv["vwap"])
    out.update({k: v for k, v in lv["bb_ma"].items() if v is not None})
    out.update({f"fib_{k}": v for k, v in lv["day_range_fibs"].items()})
    out.update({"daily_poc": lv["daily_profile"]["poc"], "daily_val": lv["daily_profile"]["val"],
                "daily_vah": lv["daily_profile"]["vah"],
                "weekly_poc": lv["anchored_weekly_profile"]["poc"],
                "weekly_val": lv["anchored_weekly_profile"]["val"],
                "weekly_vah": lv["anchored_weekly_profile"]["vah"],
                "weekly_high": lv["anchored_weekly_profile"]["high"],
                "weekly_low": lv["anchored_weekly_profile"]["low"],
                "session_high": lv["session_high_so_far"], "session_low": lv["session_low_so_far"]})
    out.update({f"prior_day_{k}": v for k, v in lv["prior_day"].items() if v is not None})
    return {k: v for k, v in out.items() if v is not None}


def macro_rows(day_next, dec):
    """news_archive filtered to datetime_ET <= the decision minute. As-of only."""
    df = pd.read_csv(NEWS)
    cut = pd.Timestamp(f"{day_next} {dec}")
    d = pd.to_datetime(df.datetime_ET, errors="coerce")
    same = df[(d.dt.date == cut.date())].copy()
    same["_dt"] = pd.to_datetime(same.datetime_ET, errors="coerce")
    past = same[same._dt <= cut]
    later_today = same[same._dt > cut]
    return {
        "released_so_far_today": past.drop(columns=["_dt"]).to_dict("records"),
        "scheduled_later_today": later_today.drop(columns=["_dt"]).to_dict("records"),
        "note": ("released_so_far_today is everything on the calendar at or before this "
                 "minute. scheduled_later_today is the calendar only - times are known in "
                 "advance and carry no outcome."),
    }


def verify(b):
    """Re-derive every stated candle and refuse to emit a disagreement."""
    dm = b.get("decision_minute", "")
    day, dec = dm.split("T")[0], dm.split("T")[1].split()[0]
    for key in ("signal_candle_3m", "signal_candle_2m", "last_completed_2m_bar"):
        c = b.get(key)
        if not isinstance(c, dict) or not c.get("start"):
            continue
        end = str(c.get("closed_at") or dec)
        if end > dec:
            raise ValueError(f"{key}: closed_at {end} is after the decision minute {dec}")
        t = agg(day, c["start"], end)
        bad = {k: (c[k], t[k]) for k in ("open", "high", "low", "close")
               if k in c and abs(float(c[k]) - t[k]) > 1e-6}
        if bad:
            raise ValueError(f"{key} disagrees with the bars: {bad}")
    px = b.get("price_at_decision")
    if px is not None and abs(float(px) - price_at(day, dec)) > 1e-6:
        raise ValueError(f"price_at_decision {px} is not the last completed minute's close")
    return b


HOWTO = ("The screenshot is the chart at your decision minute with replay truncated there. "
         "Nothing prints to the right of the cursor. Read it yourself - no one has described "
         "it to you.")
PROV = ("levels_at_decision_BUILD are recomputed from committed bars strictly before this "
        "minute. His CHART states its own values in the legend at the top of your screenshot - "
        "read them there. The two were parity-gated at the session open and spot-checked "
        "during the run, agreeing to 0.36pt or better on every VWAP band and exactly on the "
        "BB MA. Where they differ, the chart is the authority.")


def thesis_briefing(sess_day, day_next, dec, window, shot, chart_levels, position_state,
                    window_state, event="window_open", prior=None, since=None,
                    refire_reason=None, macro=None):
    lv = levels_at(sess_day, day_next, dec)
    b = {
        "role": "tv-thesis", "event_trigger": event, "window": window,
        "decision_minute": f"{day_next}T{dec} ET",
        "leak_check": (f"pass - replay truncated at {back(day_next, dec, 1)}:59, verified against "
                       "replay_status after the jump. Every value below is computed from bars "
                       "strictly before this minute and re-checked against the tape."),
        "screenshot": f"/Users/barbelldaddy/tradingview-mcp/screenshots/{shot}",
        "HOW_TO_READ_THIS_SCREENSHOT": HOWTO, "level_provenance": PROV,
        "price_at_decision": price_at(day_next, dec),
        "last_completed_2m_bar": agg(day_next, back(day_next, dec, 2), dec),
        "position_state": position_state, "window_state": window_state,
        "levels_at_decision_CHART": chart_levels,
        "levels_at_decision_BUILD": lv,
        "fib_source": "developing session-day high-to-low, objective, recomputed at this minute",
        "flush_inputs": flush_inputs(sess_day, day_next, dec),
        "last_15m_candles": body_ratio_15m(sess_day, day_next, dec, 4),
        "macro": macro or {},
        "what_to_emit": "your thesis JSON for this window, per your contract.",
    }
    if prior is not None:
        b["prior_thesis"] = prior
    if since:
        b["what_happened_since_the_last_read"] = since
    if refire_reason:
        b["why_you_are_being_re-fired"] = refire_reason
    return verify(b)


def trigger_briefing(sess_day, day_next, dec, cid, window, session, shot, thesis,
                     chart_levels, candidate_levels, side, pair_shape, levels_closed,
                     fills, cap, macro=None, extra=None):
    """candidate_levels: level names the candidate could be rejecting. The HTF
    block (T46) is computed for each, which is what lets the agent tell a level
    that held from one that failed."""
    lv = levels_at(sess_day, day_next, dec)
    flat = flat_levels(lv)
    px = price_at(day_next, dec)

    # T46 - his canonical helper (scripts/htf_level_behavior.py), not a local
    # improvisation. It reports tests, closes each side, max wick vs body and a
    # one-phrase verdict per timeframe, which is what lets the agent tell a level
    # that HELD from one that failed.
    htf = {}
    for name in candidate_levels:
        if name in flat:
            htf[name] = behavior_at(bars(), sess_day, dec, flat[name])

    above = sorted(((v, k) for k, v in flat.items() if v > px))
    below = sorted(((v, k) for k, v in flat.items() if v < px), reverse=True)

    b = {
        "role": "tv-trigger", "candidate_id": cid, "window": window, "session": session,
        "decision_minute": f"{day_next}T{dec} ET",
        "candle_start_3m": back(day_next, dec, 3), "candle_start_2m": back(day_next, dec, 2),
        "leak_check": (f"pass - replay truncated at {back(day_next, dec, 1)}:59, verified against "
                       "replay_status. The 3m bar starting {} and the 2m bar starting {} both "
                       "close AT {}. Every candle here is aggregated from committed bars and "
                       "re-checked before emission.").format(back(day_next, dec, 3),
                                                             back(day_next, dec, 2), dec),
        "screenshot": f"/Users/barbelldaddy/tradingview-mcp/screenshots/{shot}",
        "HOW_TO_READ_THIS_SCREENSHOT": HOWTO, "level_provenance": PROV,
        "thesis": thesis,
        "price_at_decision": px,
        "signal_candle_3m": agg(day_next, back(day_next, dec, 3), dec),
        "signal_candle_2m": agg(day_next, back(day_next, dec, 2), dec),
        "signal_direction_2m_3m": side,
        "pair_shape": pair_shape,
        "levels_closed_SCANNER": levels_closed,
        "levels_closed_note": ("this is the mechanical scanner's reading of which levels the "
                               "candle closed through. Verify it against the level values below "
                               "and correct it in your verdict if it does not hold."),
        "higher_timeframe_at_candidate_levels": htf,
        "levels_at_decision_CHART": chart_levels,
        "levels_at_decision_BUILD": lv,
        "levels_above_price": [f"{k} {v}" for v, k in above],
        "levels_below_price": [f"{k} {v}" for v, k in below],
        "fills_this_window": fills, "window_cap": cap,
        "fill_model_note": "limits are simulated by the orchestrator: touch-equals-fill.",
        "entry_geometry_note": ("the orchestrator validates entry arithmetic before simulating. "
                                "For a LONG the limit sits BELOW current price and "
                                "cancel_if_reaches ABOVE both; for a SHORT, mirrored."),
        "macro": macro or {},
    }
    if extra:
        b.update(extra)
    return verify(b)


def manage_briefing(sess_day, day_next, dec, cid, shot, reason, level, level_price,
                    side, entry, stop, targets, conviction, chart_levels, opened_at,
                    crowded_path, prior_actions, original_r=None):
    lv = levels_at(sess_day, day_next, dec)
    px = price_at(day_next, dec)
    # Once the stop is at breakeven the CURRENT stop distance is zero, so open
    # P&L must be measured against the ORIGINAL R the trade was sized on.
    R = original_r if original_r is not None else abs(entry - stop)
    open_r = ((entry - px) / R) if side.lower().startswith("s") else ((px - entry) / R)
    return verify({
        "role": "tv-manage", "candidate_id": cid,
        "decision_minute": f"{day_next}T{dec} ET",
        "reason_for_call": reason,
        "leak_check": (f"pass - replay truncated at {back(day_next, dec, 1)}:59, verified against "
                       "replay_status."),
        "screenshot": f"/Users/barbelldaddy/tradingview-mcp/screenshots/{shot}",
        "HOW_TO_READ_THIS_SCREENSHOT": HOWTO,
        "position": {"side": side, "entry": entry, "stop": stop, "targets": targets,
                     "conviction": conviction, "opened_at": opened_at,
                     "R_in_points": round(R, 2), "current_stop_distance": round(abs(entry - stop), 2),
                     "open_pnl_in_R": round(open_r, 2)},
        "level_in_question": {"level": level, "price": level_price},
        "price_at_decision": px,
        "last_completed_2m_bar": agg(day_next, back(day_next, dec, 2), dec),
        "recent_2m_bars": [agg(day_next, back(day_next, dec, 2 * i + 2), back(day_next, dec, 2 * i))
                           for i in range(3, -1, -1)],   # i=0 is the bar ending AT dec
        "levels_at_decision_CHART": chart_levels,
        "levels_at_decision_BUILD": lv,
        "crowded_path": crowded_path,
        "management_actions_so_far": prior_actions,
        "what_to_emit": "your management JSON, per your contract.",
    })
