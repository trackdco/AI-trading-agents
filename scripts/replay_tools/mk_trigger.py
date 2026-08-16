"""Build a trigger briefing. Argv:
sess_day day_next dec cid window shot thesis_path chart_levels_json cand_levels_csv
side pair_shape levels_closed_csv fills cap macro_path out [extra_json]
context_extras is computed here (spec: every trigger briefing carries it) and merged into extra."""
import sys, json, subprocess, os
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
from scripts.replay_tools.brief04 import trigger_briefing
import pandas as _pd
def _session_calendar(sd, dn):
    return {"session_day_label": sd,
            "session_opens": f"{sd} 18:00 ET ({_pd.Timestamp(sd):%A} evening)",
            "cash_session_traded": f"{dn} ({_pd.Timestamp(dn):%A})",
            "note": "the session-day is LABELLED by the evening it OPENS; the cash session it trades is the FOLLOWING calendar day. Weekday-specific doctrine keys off the CASH day traded, not the label."}


(sd, dn, dec, cid, window, shot, thesis_path, chart_levels_json, cand_csv,
 side, pair_shape, closed_csv, fills, cap, macro_path, out) = sys.argv[1:17]
extra = json.loads(sys.argv[17]) if len(sys.argv) > 17 else {}

ce = subprocess.run(["/Users/barbelldaddy/AI-trading-agents/.venv/bin/python", "-m",
                     "scripts.context_extras", sd, dec, "--json"],
                    capture_output=True, text=True, cwd="/Users/barbelldaddy/AI-trading-agents")
cl = json.loads(chart_levels_json)
extra["session_calendar"] = _session_calendar(sd, dn)
extra["chart_freshness_self_check"] = {
    "expected_legend_at_this_decision_minute": {
        "BB_20_SMA_close_2_basis": cl.get("bb_basis_2m_last_completed_plot"),
        "VWAP": cl.get("vwap"), "VWAP_p1": cl.get("vwap_p1"), "VWAP_m1": cl.get("vwap_m1")},
    "why": "the chart canvas can freeze and serve a frame from an earlier minute. These are the values the orchestrator read off the live chart AT this decision minute.",
    "instruction": "compare against the on-chart indicator legend in your screenshot. If they do not match, the capture is STALE: return decision pass with constraints_failed [\"stale_chart\"] and say so. Do NOT adjudicate a stale chart."}
extra["context_extras"] = json.loads(ce.stdout)
extra["context_extras_note"] = ("nwog / swept lows-highs / defended_levels computed by scripts.context_extras "
                                "as-of the decision minute. Mechanical, no editorial.")

b = trigger_briefing(sd, dn, dec, cid, window, sd, shot,
                     json.load(open(thesis_path)), json.loads(chart_levels_json),
                     [x for x in cand_csv.split(",") if x], side, pair_shape,
                     [x for x in closed_csv.split(",") if x], json.loads(fills), json.loads(cap),
                     macro=json.load(open(macro_path)), extra=extra)
json.dump(b, open(out, "w"), indent=1)
print(out)
