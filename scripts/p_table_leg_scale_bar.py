"""LEG-SCALE ARM -- Task 4, part A: the fit-era-derived stop bar.

Explicitly does NOT import the M-TABLE's 0.17W/~11-20pt figure (that traces to
this table's own SEALED span -- a leak, already discarded in the prior repair
run and staying discarded). Also does NOT reuse the prior run's "1.5x pooled
1-minute noise floor" proxy -- this run's instruction specifies a different,
more direct construction and this script implements exactly that.

PROCEDURE (stated precisely since a few implementation choices were needed):
  1. Reference population: candle-scale QUALIFIED, FILLED rows (2,927) -- the
     largest, most representative sample already in the table, using the
     existing 'intended entry' (limit_price) and its own fill mechanics.
  2. For each such row, measure MAX ADVERSE EXCURSION from limit_price (points
     against the trade direction) over the 5 REAL MINUTES starting at ts_fill
     (using 1-minute bars -- not the trigger timeframe).
  3. Per session, the bar = the 90th percentile of that MAE distribution --
     i.e. the smallest stop width W such that P(MAE_5min >= W) < 10%, which is
     exactly "the stop width at which the fill-bar stop-out rate falls below
     10%" generalised from one bar to a 5-minute window (the instruction's own
     "over the first 5 minutes" phrase).
  4. Also reports the STRICT fill-bar-only (1-minute) version alongside, since
     "fill-bar stop-out rate" was the literal phrase used -- for comparison,
     not as the declared bar.

No R-multiple, no win/loss, no exit choice anywhere in this computation.
"""
from __future__ import annotations

import json
import math
import os
import sys
from collections import defaultdict
from datetime import date as Date, timedelta

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from p_table_lib import session_window_utc
from build_p_table import load_front_minutes, minute_map_for_day_window

CACHE = os.environ.get(
    "P_TABLE_CACHE",
    "/tmp/claude-0/-home-user-AI-trading-agents/a6ad12c8-81a9-57f1-b548-760dc4a1f9f9/scratchpad/cache")


def main():
    fit = pd.read_parquet("output/p_table.parquet")
    filled = fit[(fit.qualified) & (fit.filled == True)].reset_index(drop=True)  # noqa: E712
    df, front = load_front_minutes(CACHE)

    groups = defaultdict(list)
    for idx, row in filled.iterrows():
        groups[(row.date, row.session)].append(idx)

    mae_1min, mae_5min = {}, {}
    for gi, ((ds, session), idxs) in enumerate(groups.items()):
        d = Date.fromisoformat(ds)
        w_utc, s_utc, e_utc = session_window_utc(d, session)
        mm = minute_map_for_day_window(df, w_utc, e_utc)
        for idx in idxs:
            r = filled.loc[idx]
            direction = int(r.direction)
            limit = r.limit_price
            ts_fill = pd.Timestamp(r.ts_fill).to_pydatetime()
            window = [(t, v) for t, v in mm.items()
                     if ts_fill <= t < ts_fill + timedelta(minutes=5)]
            if not window:
                continue
            window.sort(key=lambda tv: tv[0])
            first = window[0]
            adverse_1 = (first[1][1] - limit) if direction == -1 else (limit - first[1][2])
            adverse_5 = max(
                (v[1] - limit) if direction == -1 else (limit - v[2])
                for _, v in window)
            mae_1min[r.event_id] = max(0.0, adverse_1)
            mae_5min[r.event_id] = max(0.0, adverse_5)
        if (gi + 1) % 200 == 0:
            print(f"  {gi + 1}/{len(groups)} groups", flush=True)

    filled["mae_1min_post_fill_pts"] = filled.event_id.map(mae_1min)
    filled["mae_5min_post_fill_pts"] = filled.event_id.map(mae_5min)
    filled.to_parquet("output/p_table_leg_scale_bar_rows.parquet")

    report = {}
    for session in ("ny_am", "london"):
        sub = filled[filled.session == session]
        m1 = sub.mae_1min_post_fill_pts.dropna()
        m5 = sub.mae_5min_post_fill_pts.dropna()
        report[session] = dict(
            n=int(len(sub)),
            mae_5min=dict(median=round(float(m5.median()), 3),
                          p75=round(float(m5.quantile(.75)), 3),
                          p90=round(float(m5.quantile(.9)), 3),
                          p95=round(float(m5.quantile(.95)), 3)) if len(m5) else None,
            mae_1min_fillbar_only=dict(
                median=round(float(m1.median()), 3),
                p90=round(float(m1.quantile(.9)), 3)) if len(m1) else None,
            DECLARED_BAR_pts=round(float(m5.quantile(.9)), 3) if len(m5) else None,
        )
    report["method"] = ("p90 of max-adverse-excursion-from-limit_price over "
                        "the 5 real minutes starting at ts_fill, on "
                        "candle-scale qualified+filled rows, per session. "
                        "NOT the M-TABLE 0.17W/~11-20pt figure (discarded, "
                        "traces to this table's own sealed span). NOT the "
                        "prior run's pooled-1m-noise-floor proxy -- this is "
                        "a direct, fit-era-only, entry-conditioned measure.")
    json.dump(report, open("output/p_table_leg_scale_bar.json", "w"), indent=1)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
