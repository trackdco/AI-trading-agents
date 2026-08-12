"""FACT-ONLY thesis briefing. Same rule as factbrief: the contract holds every
rule, so repeating the relevant one at the decision point is steering.

Banned here: doctrine quotes, "his ruling", ALL-CAPS attention fields, questions
that contain their own answer, counterfactuals of earlier trades, and any
characterisation of what the session "is" beyond the arithmetic.
"""
import json, sys
sys.path.insert(0, "/Users/barbelldaddy/.claude/jobs/bdd15866/tmp")
from brief import HOWTO, CHARTNOTE, PROV

def thesis(window, dm, trunc, shot, lv, chart, price, last_bar, position_state,
           fills_state, structure, macro, prior=None, since=None, event="window_open",
           refire_reason=None, extra=None):
    b = {"role": "tv-thesis", "event_trigger": event, "window": window,
         "decision_minute": dm, "leak_check": trunc,
         "screenshot": f"/Users/barbelldaddy/tradingview-mcp/screenshots/{shot}",
         "HOW_TO_READ_THIS_SCREENSHOT": HOWTO, "chart_note": CHARTNOTE,
         "level_provenance": PROV,
         "price_at_decision": price, "last_completed_2m_bar": last_bar,
         "position_state": position_state, "window_state": fills_state,
         "levels_at_decision_CHART": chart,
         "levels_at_decision_BUILD": {
             "bb_ma_2m": lv["bb_ma"]["2m"], "bb_ma_3m": lv["bb_ma"]["3m"],
             "bb_ma_15m": lv["bb_ma"]["15m"], "bb_ma_60m": lv["bb_ma"]["60m"],
             "day_range_fibs": lv["fib"],
             "session_high_so_far": lv["session_high_so_far"],
             "session_low_so_far": lv["session_low_so_far"],
             "daily_profile": lv["daily"], "anchored_weekly_profile": lv["weekly"],
             "prior_day": lv["prior_day"],
             "weekly_high": lv["weekly_high"], "weekly_low": lv["weekly_low"]},
         "fib_source": "developing session-day H->L, objective",
         "structure_notes": structure, "macro": macro,
         "what_to_emit": "your standard thesis JSON for this window."}
    if prior is not None: b["prior_thesis"] = prior
    if since: b["what_happened_since_the_last_read"] = since
    if refire_reason: b["why_you_are_being_re-fired"] = refire_reason
    if extra: b.update(extra)
    return b
