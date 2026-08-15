"""Build one trigger briefing end-to-end from a small spec dict.

Wraps mk_trigger and fills the standing extras the run spec requires on every
trigger briefing (chart_truncation_note, position_state, the outer-band mechanical
gate with its arithmetic spelled out, escalation_state, news_note, scanner_detail)
so a candidate is one call instead of hand-assembly.

Usage:  .venv/bin/python -m scripts.replay_tools.mkcand '<json spec>'   (or a path to it)

Spec keys: sd dn dec cid window shot thesis_path chart_levels(dict) cand_levels(list)
  side pair_shape levels_closed(list) fills cap_written escalation(dict)
  macro_path scanner_detail news_blackout(bool)
Optional: position_state(dict), out, extra(dict) merged last.
"""
import sys, json, subprocess, os

ROOT = "/Users/barbelldaddy/AI-trading-agents"
PY = f"{ROOT}/.venv/bin/python"


def build(s):
    dec, cid, sd = s["dec"], s["cid"], s["sd"]
    out = s.get("out") or f"{ROOT}/output/briefings/jn1_{sd}_{cid}_{dec.replace(':','')}_trigger.json"
    cap = {"window": s["window"], "written_cap": s["cap_written"],
           "caps_lifted": True, "fills_so_far": s["fills"]}
    r = subprocess.run(
        [PY, "-m", "scripts.replay_tools.mk_trigger", sd, s["dn"], dec, cid, s["window"],
         s["shot"], s["thesis_path"], json.dumps(s["chart_levels"]),
         ",".join(s["cand_levels"]), s["side"], s["pair_shape"],
         ",".join(s["levels_closed"]), str(s["fills"]), json.dumps(cap),
         s["macro_path"], out],
        capture_output=True, text=True, cwd=ROOT)
    if r.returncode:
        raise SystemExit("mk_trigger failed:\n" + r.stderr[-3000:])

    b = json.load(open(out))
    px = b["price_at_decision"]
    cl = b["levels_at_decision_CHART"]
    up = s["side"] == "up"
    band = cl["vwap_p2"] if up else cl["vwap_m2"]
    fires = (px >= band) if up else (px <= band)
    b["chart_truncation_note"] = (
        "decision minute %s; the last COMPLETE 2m bar closes %s. Deliberate and leak-safe; "
        "legend values were read at that cursor." % (dec, b["signal_candle_2m"]["closed_at"]))
    b["position_state"] = s.get("position_state") or {"state": "FLAT", "fills_this_window": s["fills"]}
    b["MECHANICAL_GATE_outer_band_fade_only"] = {
        "rule": "a SHORT at/through vwap_m2/m3 or a LONG at/through vwap_p2/p3 is a pass "
                "regardless of trigger quality.",
        "arithmetic": "%s candidate; %s %s vs price %.2f - gate %s." % (
            "up" if up else "down", "vwap_p2" if up else "vwap_m2", band, px,
            "FIRES" if fires else "does NOT fire")}
    b["VALID_RETEST_ANCHORS"] = {
        "rule": ("an entry retest level must be one of: a 2-minute, 3-minute or 5-minute moving "
                 "average; a VWAP level; or a volume-profile level."),
        "not_valid": ("moving averages on any timeframe higher than 5 minutes (including the 15m and "
                      "60m MAs), Bollinger outer bands, and Fibonacci retracement levels. None of "
                      "these may be used as retest_level."),
        "source": "his standing rulings of 2026-08-15",
        "scope": ("this constrains retest_level only. It says nothing about direction, conviction, "
                  "targets, stop placement, or whether to take at all."),
        "orchestrator_enforcement": ("the orchestrator validates retest_level against this rule before "
                                     "simulating a fill and rejects a take row that violates it."),
    }
    b["CANCEL_IF_REACHES_RULE"] = {
        "rule": ("cancel_if_reaches is ALWAYS your first target. If price reaches TP1 before the limit "
                 "fills, the move has gone without you and the order is cancelled."),
        "consequence": ("your choice of TP1 therefore does two jobs: it sets the first target AND it "
                        "sets the distance the order will tolerate before being abandoned."),
        "source": "his standing ruling of 2026-08-15",
        "orchestrator_enforcement": ("the orchestrator rejects a take row whose cancel_if_reaches price "
                                     "is not equal to targets[0].price."),
    }
    b["escalation_state"] = s["escalation"]
    b["news_note"] = ("news_blackout TRUE this window - entries are gated."
                      if s["news_blackout"] else "news_blackout false this window.")
    b["scanner_detail"] = s["scanner_detail"]
    if s.get("extra"):
        b.update(s["extra"])
    json.dump(b, open(out, "w"), indent=1)
    return out, fires


if __name__ == "__main__":
    a = sys.argv[1]
    spec = json.load(open(a)) if os.path.exists(a) else json.loads(a)
    p, fires = build(spec)
    print(p)
    print("outer_band_gate_fires", fires)
