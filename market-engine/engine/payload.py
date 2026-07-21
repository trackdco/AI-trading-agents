"""Build the 20-field Engine candidate from a detected Trigger + context.

Where a field needs a data source not present in 1m OHLCV (bid/ask spread,
cross-asset risk tone), the value is an explicit null with a `note` — the Engine
never fabricates. News comes from config/news_calendar.csv.
"""
from __future__ import annotations

import pandas as pd

_TRIGGER_ENUM = {"rejection_block": "order_block", "displacement": "displacement"}
_PLAYBOOK = {
    "A": "Pattern A — Reversal: over-extension / HTF range extreme → rejection block against the prior move → retest (strategy §4).",
    "B": "Pattern B — Reclaim: price on the wrong side of the cluster → displacement back through → retest of the reclaimed cluster (strategy §4).",
    "B2": "Pattern B2 — Continuation: established move → pullback to cluster → rejection block with the move → retest (strategy §4).",
}


def upcoming_news(news_df: pd.DataFrame, asof, horizon_min: int = 120) -> list[dict]:
    if news_df is None or news_df.empty:
        return []
    end = asof + pd.Timedelta(minutes=horizon_min)
    up = news_df[(news_df["datetime_et"] >= asof) & (news_df["datetime_et"] <= end)]
    return [{"event": r["event"], "impact": r["impact"],
             "time": r["datetime_et"].isoformat(),
             "minutes_until": round((r["datetime_et"] - asof).total_seconds() / 60.0, 1)}
            for _, r in up.iterrows()]


def build(trig, ctx: dict) -> dict:
    asof = ctx["asof"]
    tz = ctx["tz"]
    sweep = ctx.get("sweep")
    kz_start, kz_end = ctx["kill_zone"]
    in_kz = kz_start <= asof.time() <= kz_end
    opt_start, opt_end = ctx["optimal_window"]
    in_opt = opt_start <= asof.time() <= opt_end

    vol_ratio = ctx.get("vol_ratio")

    payload = {
        "candidate_direction": trig.direction,

        "higher_timeframe_swing_sequence": ctx["swing_sequence"],

        "price_position_in_range": {
            "current": round(ctx["last_close"], 2),
            "range_high": round(ctx["range_high"], 2),
            "range_low": round(ctx["range_low"], 2),
        },

        "upcoming_news_events": ctx["upcoming_news"],

        "current_session": ctx["session"],

        "broad_risk_tone": {
            "tone": ctx["risk_tone"],
            "derived_from": "NQ-internal proxy (15m HTF flag + session drift). "
                            "Cross-asset inputs (yields/VIX/ES) not wired — pending a "
                            "multi-instrument feed; treat as provisional.",
            "htf_flag": trig.htf_flag,
        },

        "liquidity_pool_swept": (
            {"pool": f"{sweep['side'].replace('_', '-')} liquidity at swept level",
             "price": round(sweep["pool_price"], 2),
             "time": sweep["pool_time"].isoformat(),
             "sweep_extreme": round(sweep["sweep_price"], 2)}
            if sweep else None
        ),

        "liquidity_draw_target": {
            "level": trig.target_label,
            "price": trig.target,
        },

        "entry_relative_to_sweep": (
            "after" if sweep and sweep["sweep_time"] <= asof else "none"
        ),

        "entry_trigger_type": _TRIGGER_ENUM.get(trig.trigger_type, "none"),
        "_engine_trigger_detail": {
            "mechanism": trig.trigger_type,
            "cluster_types": trig.cluster["distinct_types"],
            "confluence_count": trig.cluster["count"],
            "over_extension": trig.over_extension,
        },

        "entry_price": trig.entry,

        "trigger_zone": {
            "low": trig.zone_low,
            "high": trig.zone_high,
            "coincident_levels": [
                {"type": l["type"], "label": l["label"], "price": round(l["price"], 2)}
                for l in trig.cluster["levels"]
            ],
            "distinct_confluence_types": trig.cluster["count"],
        },

        "spread_and_fill_data": {
            "spread_pts": None,
            "note": "Not observable from 1m OHLCV. Requires an L1/MBP feed "
                    "(available in the live Databento path). Null by design.",
        },

        "current_time_window": {
            "time": asof.isoformat(),
            "kill_zone": "NY AM (09:30–11:00 ET)",
            "in_kill_zone": bool(in_kz),
        },

        "recent_volume_and_volatility": {
            "volume_vs_avg": (round(vol_ratio, 2) if vol_ratio is not None else None),
            "regime": ctx.get("regime", "unknown"),
            "chop_flag": ctx.get("chop_flag"),
        },

        "setup_timing_alignment": {
            "has_narrower_optimal_window": True,
            "optimal_window": "09:30–10:30 ET AM impulse",
            "current_matches": bool(in_opt),
        },

        "stop_price": trig.stop,
        "invalidation_price": trig.invalidation,
        "target_price": trig.target,

        "playbook_match": {
            "matched": True,
            "pattern": trig.pattern,
            "entry": _PLAYBOOK[trig.pattern],
            "with_trend": trig.with_trend,
        },
    }
    return payload
