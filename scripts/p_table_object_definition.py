"""REPAIR RUN — Task 3(a)/(b): object-definition cascade on the SAME identified
PXL/PXH events.

Holds the population fixed (no re-run of leg tracking or trigger detection
under (b) -- same candidates, same fights, same qualification). Only the wick
ZONE boundary (level_1) is recomputed:

  (a) DA-3 as specced [current]: level_1 = min(open,close) for a PXL / body
      boundary -- already in the table verbatim.
  (b) full candle range: level_1 = the SAME candle's own high (PXL) / low
      (PXH) -- the WICK_TOP_MODE=candle_high variant the SPEC pre-declared as
      a parameter (B5 item 10) but never built, because Angus ruled (a).

DECLARED SIMPLIFICATION, stated once here rather than buried: target_price is
held at definition (a)'s value (the same liquidity draw), because the target
pool is a property of OTHER candidates' level_0 (unaffected by wick_top_mode)
evaluated against THIS row's limit -- recomputing it under (b)'s shifted limit
would require re-deriving the pool per row, which is a rebuild, not a
recompute. target_dist_b is therefore |limit_b - target_price_a|.

(c) is explicitly NOT built here -- Angus rules on the exact construction.

No fill simulation, no outcome, no MFE/MAE. Geometry only.
"""
from __future__ import annotations

import math
import os
import sys
from collections import defaultdict
from datetime import date as Date

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from p_table_lib import CONFIG, aggregate_tf, build_session_minutes, session_window_utc, tick_round
from build_p_table import load_front_minutes, minute_map_for_day_window

CACHE = os.environ.get(
    "P_TABLE_CACHE",
    "/tmp/claude-0/-home-user-AI-trading-agents/a6ad12c8-81a9-57f1-b548-760dc4a1f9f9/scratchpad/cache")


def main():
    fit = pd.read_parquet("output/p_table.parquet")
    df, front = load_front_minutes(CACHE)

    groups = defaultdict(list)
    for idx, row in fit.iterrows():
        groups[(row.date, row.session, int(row.tf_trigger))].append(idx)

    level_1_b = {}
    missing = 0
    for gi, ((ds, session, tf), idxs) in enumerate(groups.items()):
        d = Date.fromisoformat(ds)
        w_utc, s_utc, e_utc = session_window_utc(d, session)
        mm = minute_map_for_day_window(df, w_utc, e_utc)
        built = build_session_minutes(mm, d, session)
        if built is None:
            missing += len(idxs)
            continue
        minutes, _, _ = built
        tf_bars = aggregate_tf(minutes, tf)
        by_close = {b.close_ts: b for b in tf_bars}
        for idx in idxs:
            r = fit.loc[idx]
            pxl_ts = pd.Timestamp(r.pxl_ts).to_pydatetime()
            b = by_close.get(pxl_ts)
            if b is None:
                missing += 1
                continue
            level_1_b[idx] = b.high if r.direction == -1 else b.low
        if (gi + 1) % 500 == 0:
            print(f"  {gi + 1}/{len(groups)} groups", flush=True)

    print(f"lookup complete: {len(level_1_b)} resolved, {missing} missing "
         f"(session-window exclusions in the original exclusion log)")

    buf = CONFIG["STOP_BUFFER_PTS"]
    rows = []
    for idx, l1b in level_1_b.items():
        r = fit.loc[idx]
        l0 = r.pxl_level_0
        direction = int(r.direction)
        wick_b = abs(l1b - l0)
        limit_b = tick_round((l0 + l1b) / 2)
        stop_b = tick_round(l1b + buf) if direction == -1 else tick_round(l1b - buf)
        stop_dist_b = abs(limit_b - stop_b)
        target = r.target_price
        tdist_b = abs(limit_b - target) if not (isinstance(target, float) and math.isnan(target)) else float("nan")
        r_avail_b = tdist_b / stop_dist_b if stop_dist_b > 0 and not math.isnan(tdist_b) else float("nan")
        rows.append(dict(
            event_id=r.event_id, qualified=bool(r.qualified), tf_trigger=int(r.tf_trigger),
            session=r.session, direction=direction,
            leg_height_pts=r.leg_height_pts,
            wick_width_pts_a=r.wick_width_pts, wick_width_pts_b=wick_b,
            stop_dist_pts_a=r.stop_dist_pts_base, stop_dist_pts_b=stop_dist_b,
            r_available_a=r.r_available, r_available_b=r_avail_b,
            level_1_a=r.pxl_level_1, level_1_b=l1b, level_0=l0,
        ))
    out = pd.DataFrame(rows)
    out.to_parquet("output/p_table_object_definition_ab.parquet")
    print(f"wrote {len(out)} rows to output/p_table_object_definition_ab.parquet")

    def dist(s):
        s = s.dropna()
        if not len(s):
            return None
        return dict(n=int(len(s)), median=round(float(s.median()), 3),
                   p25=round(float(s.quantile(.25)), 3),
                   p75=round(float(s.quantile(.75)), 3),
                   p90=round(float(s.quantile(.9)), 3))

    import json
    q = out[out.qualified]
    report = dict(
        n_rows_total=int(len(out)), n_qualified=int(len(q)), n_missing_lookup=missing,
        pooled=dict(
            wick_width_a=dist(q.wick_width_pts_a), wick_width_b=dist(q.wick_width_pts_b),
            stop_dist_a=dist(q.stop_dist_pts_a), stop_dist_b=dist(q.stop_dist_pts_b),
            r_available_a=dist(q.r_available_a), r_available_b=dist(q.r_available_b),
            widening_ratio_b_over_a=dist(q.stop_dist_pts_b / q.stop_dist_pts_a)),
        by_tf={str(tf): dict(
            wick_width_a=dist(q[q.tf_trigger == tf].wick_width_pts_a),
            wick_width_b=dist(q[q.tf_trigger == tf].wick_width_pts_b),
            stop_dist_a=dist(q[q.tf_trigger == tf].stop_dist_pts_a),
            stop_dist_b=dist(q[q.tf_trigger == tf].stop_dist_pts_b),
            r_available_a=dist(q[q.tf_trigger == tf].r_available_a),
            r_available_b=dist(q[q.tf_trigger == tf].r_available_b),
        ) for tf in sorted(q.tf_trigger.unique())},
    )
    # noise floor multiple, using the same session-level noise floor from Task 1/2
    sweep = json.load(open("output/p_table_geometry_sweep.json"))
    nf = sweep["noise_floor_median_1m_TR_pts"]
    for sess in nf:
        sub = q[q.session == sess]
        if len(sub):
            report.setdefault("stop_dist_x_noise_floor_by_session", {})[sess] = dict(
                a=round(float(sub.stop_dist_pts_a.median()) / nf[sess], 3),
                b=round(float(sub.stop_dist_pts_b.median()) / nf[sess], 3))
    json.dump(report, open("output/p_table_object_definition_ab.json", "w"), indent=1)
    print(json.dumps(report, indent=1)[:3000])


if __name__ == "__main__":
    main()
