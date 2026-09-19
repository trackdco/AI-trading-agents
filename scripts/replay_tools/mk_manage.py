"""Build a manage briefing. Argv: sd dn dec cid shot reason level level_price side entry stop
targets_json conviction chart_levels_json opened_at crowded_json prior_actions_json original_r out [extra_json]"""
import sys, json
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
from scripts.replay_tools.brief04 import manage_briefing
(sd, dn, dec, cid, shot, reason, level, level_price, side, entry, stop, targets_json,
 conviction, chart_levels_json, opened_at, crowded_json, prior_json, original_r, out) = sys.argv[1:20]
extra = json.loads(sys.argv[20]) if len(sys.argv) > 20 else None
b = manage_briefing(sd, dn, dec, cid, shot, reason, level,
                    None if level_price == "-" else float(level_price), side, float(entry),
                    float(stop), json.loads(targets_json), conviction,
                    json.loads(chart_levels_json), opened_at, json.loads(crowded_json),
                    json.loads(prior_json), original_r=None if original_r == "-" else float(original_r))
if extra:
    b.update(extra)
json.dump(b, open(out, "w"), indent=1)
print(out)
