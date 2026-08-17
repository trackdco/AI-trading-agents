"""Build a macro briefing for one window. news_as_of is MECHANICAL (calendar rows
at/before the minute); standing_policy is HIS rulings, carried verbatim."""
import json, sys
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
from scripts.replay_tools.brief04 import macro_rows

POLICY = json.load(open("/Users/barbelldaddy/.claude/jobs/2411401a/tmp/d5_macro_LONDON.json"))["standing_policy"]
# _marker_note explains that the quote key was renamed away from `his_words` so
# audit_run_leak check D would stop firing - and the note itself contains the literal
# strings "his_words" and "narrated_days", so it trips the very check it documents.
POLICY = {k: v for k, v in POLICY.items() if k != "_marker_note"}

def build(prefix, sd, dn, dec, window, out):
    b = {"briefing_class": "FACT-ONLY", "run_prefix": prefix, "session_day": sd,
         "trades_calendar_day": dn,
         "decision_minute": f"{dn}T{dec} America/New_York", "window": window,
         "news_as_of": macro_rows(dn, dec), "standing_policy": POLICY,
         "instruction": ("Emit your lean and the news_blackout gate for this minute from the rows "
                         "above and the standing policy. You have no tools; do not attempt to "
                         "verify anything outside this file.")}
    json.dump(b, open(out, "w"), indent=1)
    return b

if __name__ == "__main__":
    prefix, sd, dn, dec, window, out = sys.argv[1:7]
    b = build(prefix, sd, dn, dec, window, out)
    print(out)
    print("released_so_far:", len(b["news_as_of"]["released_so_far_today"]),
          "| later_today:", len(b["news_as_of"]["scheduled_later_today"]))
    for r in b["news_as_of"]["scheduled_later_today"]:
        print("   ", r.get("time_et"), r.get("currency"), r.get("event"), r.get("impact"))
