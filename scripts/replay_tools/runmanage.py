"""Build one tv-manage briefing. Wiring only - every judgement input is passed in."""
import json, sys
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
from scripts.replay_tools.brief04 import manage_briefing, bars as _b  # noqa
from scripts.replay_tools.lifecycle import bars
import pandas as pd
from src.htf_ma.levels import NY

T = "/Users/barbelldaddy/.claude/jobs/2411401a/tmp"


def tp1_printed(dn, fill_at, dec, side, tp1):
    w = bars()
    w = w[(w.index >= pd.Timestamp(f"{dn} {fill_at}", tz=NY)) &
          (w.index < pd.Timestamp(f"{dn} {dec}", tz=NY))]
    if not len(w):
        return False
    return bool((w.low <= tp1).any() if side.startswith("s") else (w.high >= tp1).any())


def build(run, sd, dn, dec, cid, shot, reason, level, level_price, side, entry, stop,
          targets, conviction, chart_levels, opened_at, prior_actions, original_r,
          thesis_ctx, prior_positions, window_note, out):
    tp1 = targets[0]["price"]
    printed = tp1_printed(dn, opened_at, dec, side, tp1)
    crowded = {"levels_between_tp1_and_tp2": [], "count": 0, "crowded_path": False,
               "note": f"this position has a single target ({tp1:.2f}), so there is no "
                       "TP1-to-TP2 corridor to be crowded."} if len(targets) == 1 else None
    b = manage_briefing(sd, dn, dec, cid, shot, reason, level, level_price, side,
                        entry, stop, targets, conviction, chart_levels, opened_at,
                        crowded, prior_actions, original_r=original_r)
    b["conviction_partial_rule"] = {
        "conviction_of_this_position": conviction,
        "contract_default": "B takes roughly 75% at TP1 and trails the runner. A is 50% "
                            "and holds the rest to the full target; C is 100% out with no runner.",
        "note": "stated as the contract text, not as an instruction - partial_pct is your "
                "decision and is a fraction of what is still open."}
    b["thesis_context"] = thesis_ctx
    b["prior_positions_this_window"] = prior_positions
    b["window_note"] = window_note
    b["BREAKEVEN_RULE"] = {
        "rule": "breakeven is ONLY available after TP1 has printed. Before TP1 it is not a legal action.",
        "tp1": tp1, "tp1_printed_yet": printed,
        "available_to_you_now": ("YES - TP1 has printed" if printed else
                                 "NO - TP1 has not printed, so breakeven is not one of your "
                                 "options at this minute"),
        "what_to_use_instead": "before TP1 a stall is answered with hold, or with trail if a "
                               "level has genuinely broken in your favour and clears the T55 "
                               "floor, or with exit_now if the rejection is decisive.",
        "source": "his standing ruling of 2026-08-16, and RUNBOOK-replay-scoring section 6",
        "orchestrator_enforcement": "a breakeven returned before TP1 has printed is rejected."}
    json.dump(b, open(out, "w"), indent=1)
    return b


if __name__ == "__main__":
    a = json.load(open(sys.argv[1]))
    b = build(**a)
    print(a["out"])
    print("  open_pnl_in_R", b["position"]["open_pnl_in_R"], "| price", b["price_at_decision"],
          "| tp1_printed", b["BREAKEVEN_RULE"]["tp1_printed_yet"])
