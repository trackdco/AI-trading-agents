"""FACT-ONLY trigger briefing. No doctrine quotes, no attention fields, no
questions containing their own answer.

His ruling 2026-08-12, after I audited my own briefings and found six field
families that steered the agents: "that is unfair hindsight that they will not
have on live markets." The contract already holds every rule; repeating the
relevant one at the decision point IS the steering. From here a briefing carries
levels, bars, position and cap state, the standing thesis, the leak check and
the screenshot - and nothing that points.
"""
import json, sys
sys.path.insert(0, "/Users/barbelldaddy/.claude/jobs/bdd15866/tmp")
from brief import HOWTO, CHARTNOTE, PROV

def trigger(cid, window, session, dm, candle_start, tf, trunc, shot, thesis, lv,
            chart, signals, pair_shape, levels_closed, price, fills, cap,
            position_state, levels_for_targets, extra=None):
    b = {"role": "tv-trigger", "candidate_id": cid, "window": window, "session": session,
         "decision_minute": dm, "candle_start": candle_start, "timeframe": tf,
         "leak_check": trunc,
         "screenshot": f"/Users/barbelldaddy/tradingview-mcp/screenshots/{shot}",
         "HOW_TO_READ_THIS_SCREENSHOT": HOWTO, "chart_note": CHARTNOTE,
         "level_provenance": PROV, "thesis": thesis,
         "price_at_decision": price,
         "position_state": position_state,
         "macro": {"lean": "neutral", "confidence": "medium", "news_blackout": False},
         "pair_shape": pair_shape, "levels_closed": levels_closed,
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
         "levels_for_target_selection": levels_for_targets,
         "fills_this_window": fills, "window_cap": cap,
         "fill_model_note": "limits are simulated: touch-equals-fill"}
    b.update(signals)
    if extra:
        b.update(extra)
    _assert_candles_are_real(b)
    return b


def _assert_candles_are_real(b):
    """Recompute every hand-supplied candle from the bars and refuse to disagree.

    On 2026-06-24 the 03:24 briefing carried a 3m close of 29813.25 - the close of
    the ONE-MINUTE bar starting 03:24, which had not completed at the decision. The
    true close of the 3m bar 03:21->03:24 was 29822.00. The difference inverted the
    read: 29813.25 sits below the 2m MA and the daily POC (a rejection), 29822.00
    sits above both (acceptance). The trigger agent adjudicated the future.

    Hand-typing OHLC into a briefing is the same class of mistake as hand-typing a
    session high, which was caught earlier this run. So it is no longer allowed to
    pass silently: any candle stated in a briefing is recomputed from committed bars
    over [start, closed_at) and must match, and no candle may close after the
    decision minute.
    """
    import pandas as pd
    from scripts.build_l2_outcomes import load_bars
    from src.htf_ma.levels import NY

    dm = b.get("decision_minute", "")
    if "T" not in dm:
        raise ValueError("briefing has no parseable decision_minute")
    day, dec = dm.split("T")[0], dm.split("T")[1].split()[0]

    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close"]]

    for key in ("signal_candle_3m", "last_completed_2m_bar"):
        c = b.get(key)
        if not isinstance(c, dict) or not c.get("start"):
            continue
        start = str(c["start"]).split()[0]
        end = str(c.get("closed_at") or dec).split()[0]
        if end > dec:
            raise ValueError(f"{key}: closed_at {end} is AFTER the decision minute {dec}")
        s = pd.Timestamp(f"{day} {start}", tz=NY)
        e = pd.Timestamp(f"{day} {end}", tz=NY)
        seg = bars[(bars.index >= s) & (bars.index < e)]
        if not len(seg):
            raise ValueError(f"{key}: no bars in [{start}, {end})")
        truth = {"open": float(seg.iloc[0].open), "high": float(seg.high.max()),
                 "low": float(seg.low.min()), "close": float(seg.iloc[-1].close)}
        wrong = {k: (c[k], truth[k]) for k in truth
                 if k in c and abs(float(c[k]) - truth[k]) > 1e-6}
        if wrong:
            raise ValueError(
                f"{key} disagrees with the bars over [{start}, {end}) "
                f"({len(seg)} minutes) - stated vs true: {wrong}")

    px = b.get("price_at_decision")
    if px is not None:
        prev = bars[bars.index < pd.Timestamp(f"{day} {dec}", tz=NY)]
        if len(prev) and abs(float(px) - float(prev.iloc[-1].close)) > 1e-6:
            raise ValueError(
                f"price_at_decision {px} is not the close of the last completed "
                f"minute before {dec}, which is {float(prev.iloc[-1].close)}")


# The pass-2 (post-escalation) trigger row has lost its leak_check four times this
# run. It is always the re-adjudication row, never the first pass, because the
# pass-2 briefing is built by copying the pass-1 briefing and the ROW is written
# by hand. Copy leak_check onto the pass-2 row from the pass-1 row, always.
PASS2_REMINDER = "copy leak_check from the pass-1 row onto the pass-2 row"
