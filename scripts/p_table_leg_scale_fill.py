"""LEG-SCALE ARM -- Task 7: fill/cancellation/unfilled-travel simulation for
the leg-scale entry, per r, on the SAME qualified event population as the
existing candle-scale arm.

Deliberately narrow: fill boolean, cancellation reason, and unfilled travel
(favourable-direction excursion from entry_r, mirroring unfilled_mfe_pts)
ONLY. No MFE/MAE hold-through, no exit battery, no R-multiple, no win/loss --
those are outcome statistics and stay out of scope per this run's discipline.

Cancellation (mirrors A5's structure with this arm's own target/invalidation):
  (a) filled -- trade-through >=1 tick beyond entry_r
  (b) target (pxl_level_0, the leg extreme) reached without fill
  (c) invalidation -- leg_start_price +/- TICK reached without fill (A2's own
      threshold; Task 2 already established this precedes/coincides with the
      nominal leg-scale stop)
  (d) session end
"""
from __future__ import annotations

import json
import math
import os
import sys
from collections import defaultdict
from datetime import date as Date

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from p_table_lib import CONFIG, TICK, build_session_minutes, session_window_utc
from build_p_table import load_front_minutes, minute_map_for_day_window
from p_table_geometry_sweep import time_bucket_for

CACHE = os.environ.get(
    "P_TABLE_CACHE",
    "/tmp/claude-0/-home-user-AI-trading-agents/a6ad12c8-81a9-57f1-b548-760dc4a1f9f9/scratchpad/cache")
R_VALUES = [0.50, 0.62, 0.705, 0.79]


def simulate_leg_scale(direction, entry_r, target, leg_start_price, minutes,
                       eligible_ts, session_end):
    tt = CONFIG["TRADE_THROUGH_TICKS"] * TICK
    live = [b for b in minutes if b.open_ts >= eligible_ts and b.open_ts < session_end]
    fill_cond = (lambda b: b.high >= entry_r + tt) if direction == -1 else \
                (lambda b: b.low <= entry_r - tt)
    tgt_cond = (lambda b: b.low <= target) if direction == -1 else \
               (lambda b: b.high >= target)
    inval_cond = (lambda b: b.high >= leg_start_price + TICK) if direction == -1 else \
                 (lambda b: b.low <= leg_start_price - TICK)

    for i, b in enumerate(live):
        if fill_cond(b):
            return dict(filled=True, bars_to_fill=i + 1, cancel_reason=None,
                       unfilled_travel_pts=float("nan"))
        if tgt_cond(b):
            return dict(filled=False, bars_to_fill=float("nan"),
                       cancel_reason="target_taken",
                       unfilled_travel_pts=_travel(direction, entry_r, live, session_end))
        if inval_cond(b):
            return dict(filled=False, bars_to_fill=float("nan"),
                       cancel_reason="invalidated",
                       unfilled_travel_pts=_travel(direction, entry_r, live, session_end))
    return dict(filled=False, bars_to_fill=float("nan"), cancel_reason="session_end",
               unfilled_travel_pts=_travel(direction, entry_r, live, session_end))


def _travel(direction, entry_r, bars, session_end):
    if not bars:
        return float("nan")
    if direction == -1:
        return entry_r - min(b.low for b in bars)
    return max(b.high for b in bars) - entry_r


def main():
    fit = pd.read_parquet("output/p_table.parquet")
    geo = pd.read_parquet("output/p_table_leg_scale_geometry.parquet")
    q = fit[fit.qualified].reset_index(drop=True)
    df, front = load_front_minutes(CACHE)

    groups = defaultdict(list)
    for idx, row in q.iterrows():
        groups[(row.date, row.session)].append(idx)

    rows = []
    for gi, ((ds, session), idxs) in enumerate(groups.items()):
        d = Date.fromisoformat(ds)
        w_utc, s_utc, e_utc = session_window_utc(d, session)
        mm = minute_map_for_day_window(df, w_utc, e_utc)
        built = build_session_minutes(mm, d, session)
        if built is None:
            continue
        minutes, _, _ = built
        for idx in idxs:
            r_row = q.loc[idx]
            direction = int(r_row.direction)
            elig = pd.Timestamp(r_row.ts_entry_eligible).to_pydatetime()
            leg_start_price = r_row.leg_start_price
            tb = time_bucket_for(session, r_row.tf_trigger_ts)
            for rv in R_VALUES:
                g = geo[(geo.event_id == r_row.event_id) & (geo.r == rv)]
                if not len(g):
                    continue
                g = g.iloc[0]
                sim = simulate_leg_scale(direction, g.entry_r, g.target_leg,
                                         leg_start_price, minutes, elig, e_utc)
                rows.append(dict(
                    event_id=r_row.event_id, r=rv, session=session,
                    direction=direction, time_bucket=tb,
                    tf_trigger=int(r_row.tf_trigger),
                    stop_dist_leg_pts=g.risk_pts, **sim))
        if (gi + 1) % 200 == 0:
            print(f"  {gi + 1}/{len(groups)} groups", flush=True)

    res = pd.DataFrame(rows)
    res.to_parquet("output/p_table_leg_scale_fill.parquet")
    print(f"simulated {len(res)} (event,r) pairs from {len(q)} qualified rows")

    def dist(s):
        s = s.dropna()
        if not len(s):
            return None
        return dict(n=int(len(s)), median=round(float(s.median()), 3),
                   p25=round(float(s.quantile(.25)), 3),
                   p75=round(float(s.quantile(.75)), 3),
                   p90=round(float(s.quantile(.9)), 3))

    report = {}
    for rv in R_VALUES:
        sub = res[res.r == rv]
        by_bucket = {}
        for (sess, tb), g in sub.groupby(["session", "time_bucket"]):
            filled = g[g.filled]
            unf = g[~g.filled]
            by_bucket[f"{sess}|{tb}"] = dict(
                n_qualified=int(len(g)),
                fill_rate=round(float(g.filled.mean()), 4),
                cancel_reasons={str(k): int(v) for k, v in
                               g[~g.filled].cancel_reason.value_counts().items()},
                unfilled_travel_pts=dist(unf.unfilled_travel_pts),
                stop_dist_leg_pts=dist(g.stop_dist_leg_pts))
        report[str(rv)] = by_bucket
    json.dump(report, open("output/p_table_leg_scale_fill_report.json", "w"), indent=1)
    print(json.dumps(report, indent=1)[:6000])


if __name__ == "__main__":
    main()
