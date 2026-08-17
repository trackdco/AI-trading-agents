"""Build a thesis briefing: python mk_thesis.py <sess_day> <day_next> <dec> <window> <shot> <chart_levels_json> <macro_json_path> <out_path> [event] [prior_json_path] [since] [refire_reason]"""
import sys, json
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
from scripts.replay_tools.brief04 import thesis_briefing
import pandas as _pd
def _session_calendar(sd, dn):
    return {"session_day_label": sd,
            "session_opens": f"{sd} 18:00 ET ({_pd.Timestamp(sd):%A} evening)",
            "cash_session_traded": f"{dn} ({_pd.Timestamp(dn):%A})",
            "note": "the session-day is LABELLED by the evening it OPENS; the cash session it trades is the FOLLOWING calendar day. Weekday-specific doctrine keys off the CASH day traded, not the label."}


sd, dn, dec, window, shot, chart_levels_json, macro_path, out = sys.argv[1:9]
event = sys.argv[9] if len(sys.argv) > 9 else "window_open"
prior = json.load(open(sys.argv[10])) if len(sys.argv) > 10 and sys.argv[10] != "-" else None
since = sys.argv[11] if len(sys.argv) > 11 and sys.argv[11] != "-" else None
refire = sys.argv[12] if len(sys.argv) > 12 and sys.argv[12] != "-" else None
chart_levels = json.loads(chart_levels_json)
macro = json.load(open(macro_path))
# GUARD. The macro BRIEFING carries standing_policy - his verbatim rulings on which
# events gate entries. The macro AGENT needs those to decide news_blackout; a thesis
# agent does not, and inlining them puts his commentary in front of a tier that is
# supposed to reason from the chart (audit_run_leak checks D and F). Pass the macro
# OUTPUT here, never the briefing. Caught on w49p049_2026-06-21_NYAM_0930_thesis.json.
if isinstance(macro, dict) and "standing_policy" in macro:
    raise SystemExit(
        f"REFUSING to build a thesis briefing from a MACRO BRIEFING ({macro_path}).\n"
        "It contains standing_policy - his verbatim rulings - which must not reach a "
        "thesis agent. Pass the macro agent's OUTPUT json instead.")
ps = {"open_position": None}
ws = {"window": window, "entries": {"LONDON": "03:00-04:59", "NY_PRE": "08:00-09:29 entries cut off 09:10",
      "NY_AM": "09:30-11:00 earliest entry 09:35"}[window],
      "fills_this_window": 0,
      "caps": "written caps LONDON 2 / NY_PRE 1 / NY_AM 2; caps LIFTED for this run, fills beyond written cap are tagged"}
chart_levels["_session_calendar"] = _session_calendar(sd, dn)
chart_levels["_freshness_self_check"] = {
    "why": "the chart canvas can freeze and serve a frame from an earlier minute. The values in this block were read off the live chart AT this decision minute.",
    "instruction": "compare them against the on-chart indicator legend in your screenshot. If they do not match, the capture is STALE: say so in reasoning and emit stand_aside rather than reading a stale chart."}
b = thesis_briefing(sd, dn, dec, window, shot, chart_levels, ps, ws, event=event,
                    prior=prior, since=since, refire_reason=refire, macro=macro)
json.dump(b, open(out, "w"), indent=1)
print(out)
