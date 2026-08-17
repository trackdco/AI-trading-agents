"""Every named structural level at a decision minute, as {name: price}.

Passed wholesale to level_visits so that WHICHEVER level the agent names as its
rejected_level is covered. Choosing a subset would be the orchestrator deciding
which level the setup is about, which runbook 0c forbids.
"""
import sys, json
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
from scripts.replay_tools.brief04 import levels_at

def levelset(sd, dn, dec):
    lv = levels_at(sd, dn, dec)
    out = {}
    for k, v in lv["vwap"].items():
        out[k] = v
    for k, v in lv["bb_ma"].items():
        out[k] = v
    d, w, p = lv["daily_profile"], lv["anchored_weekly_profile"], lv["prior_day"]
    out.update({"daily_poc": d["poc"], "daily_val": d["val"], "daily_vah": d["vah"],
                "weekly_poc": w["poc"], "weekly_val": w["val"], "weekly_vah": w["vah"],
                "weekly_high": w["high"], "weekly_low": w["low"],
                "prior_day_poc": p["poc"], "prior_day_val": p["val"],
                "prior_day_vah": p["vah"], "prior_day_high": p["high"],
                "prior_day_low": p["low"],
                "session_high_so_far": lv["session_high_so_far"],
                "session_low_so_far": lv["session_low_so_far"]})
    return {k: round(float(v), 2) for k, v in out.items() if v is not None}

if __name__ == "__main__":
    print(json.dumps(levelset(*sys.argv[1:4])))
