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


# LEAK GUARD. A manage briefing's window_note must never name FUTURE candidate
# minutes or their directions. Doing so tells a manager holding a position that
# the scanner will fire at 10:18 and that it will be SHORT - forward information
# about the tape, caught by audit_run_leak check C on 2026-06-21. The window_note
# may describe the window and standing rules; it may not describe what is coming.
import re as _re


def assert_no_future_minutes(text, dec, label=""):
    """Raise if `text` names a clock time strictly after the decision minute."""
    # Window and rule BOUNDARIES are contract constants the agent legitimately needs -
    # they describe the schedule, not the tape, and they are identical on every day.
    # Anything else later than the decision minute is a fact about what is coming.
    ALLOWED = {"03:00", "04:59", "08:00", "09:10", "09:29", "09:30", "09:35",
               "11:00", "18:00", "09:00", "10:00"}
    dh, dm = int(dec[:2]), int(dec[3:5])
    dmin = dh * 60 + dm
    bad = []
    for m in _re.finditer(r"\b([0-2]?\d):([0-5]\d)\b", str(text)):
        tok = m.group(0)
        if tok in ALLOWED:
            continue
        t = int(m.group(1)) * 60 + int(m.group(2))
        if t > dmin:
            bad.append(tok)
    # A clock time is not the only way to leak the future. "There are no further
    # candidates on the scanner" names no minute but still tells the manager the
    # window is structurally quiet ahead - and the scanner list is derived from the
    # WHOLE day's bars, so stating it leaks the scan. The time regex missed this
    # entirely; these phrases are blacklisted outright.
    FORWARD_PHRASES = ("further candidate", "further london candidate",
                       "no further", "still to be adjudicated", "are still to be",
                       "remaining candidate", "candidates remain", "will fire",
                       "upcoming candidate", "later candidate")
    low = str(text).lower()
    hit = [p for p in FORWARD_PHRASES if p in low]
    if hit:
        raise SystemExit(
            f"FORWARD REFERENCE IN BRIEFING TEXT ({label}) at decision {dec}: {hit}.\n"
            "A briefing may not tell an agent what the scanner will or will not do next - "
            "the scanner list is derived from the whole day's bars. Rewrite without it.")
    if bad:
        raise SystemExit(
            f"FUTURE MINUTES IN BRIEFING TEXT ({label}) at decision {dec}: {sorted(set(bad))}.\n"
            "A briefing may not name a clock time after its own decision minute - that is "
            "forward information about the tape. Rewrite the text without them.")


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
    assert_no_future_minutes(window_note.get("text", ""), dec, "window_note")
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
