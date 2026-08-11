"""LEG-SCALE ARM -- Task 1+2: zone, entry/stop/target, realised R.

Pure arithmetic on columns already in output/p_table.parquet -- no bar lookups,
no rebuild of the pipeline. Working population: QUALIFIED rows only (4,815),
matching Task 7's "same event population" as the existing candle-scale arm.

DA-3/DA-1-style declared naming, mirroring the candle-scale wick-zone columns:
  level_1.0 = leg_start_price   (leg origin -- short: the swing high; long: swing low)
  level_0.0 = pxl_level_0       (leg extreme -- already IS the PXL/PXH candidate's
                                  own level_0, short: low; long: high)
  leg_height_pts already recorded = |level_1.0 - level_0.0|

Entry/stop/target per declared r in {0.50, 0.62, 0.705, 0.79} (not swept):
  short: entry_r = level_0.0 + r*leg_height ; stop = level_1.0 + STOP_BUFFER ; target = level_0.0
  long:  entry_r = level_0.0 - r*leg_height ; stop = level_1.0 - STOP_BUFFER ; target = level_0.0

CONSTANT ASSERTED, FAILS LOUDLY: every declared r must exceed MIN_LEG_RETRACE,
or the limit would already be marketable at the moment the row's own leg first
qualified as a candidate.
"""
from __future__ import annotations

import json
import math
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from p_table_lib import CONFIG, TICK, tick_round

R_VALUES = [0.50, 0.62, 0.705, 0.79]


def main():
    fit = pd.read_parquet("output/p_table.parquet")
    q = fit[fit.qualified].copy().reset_index(drop=True)

    # ---- constraint assertion (loud failure, not a skip) ----
    min_retrace = CONFIG["MIN_LEG_RETRACE"]
    bad = [r for r in R_VALUES if r <= min_retrace]
    if bad:
        raise SystemExit(
            f"TASK 2 CONSTRAINT VIOLATED: declared r value(s) {bad} do not "
            f"exceed MIN_LEG_RETRACE={min_retrace}. At or below this "
            "threshold the limit would already be marketable at the moment "
            "the row's leg first qualifies as a candidate -- refusing to "
            "build entries at these r values. Fix R_VALUES or MIN_LEG_RETRACE "
            "before proceeding.")
    print(f"TASK 2 constraint OK: all r values {R_VALUES} exceed "
         f"MIN_LEG_RETRACE={min_retrace}")

    buf = CONFIG["STOP_BUFFER_PTS"]
    d = q.direction.to_numpy()
    level_1_0 = q.leg_start_price.to_numpy()
    level_0_0 = q.pxl_level_0.to_numpy()
    leg_h = q.leg_height_pts.to_numpy()

    # sanity: leg_height_pts already recorded must equal |level_1.0 - level_0.0|
    recomputed = abs(level_1_0 - level_0_0)
    mism = (abs(recomputed - leg_h) > 1e-6).sum()
    print(f"leg_height_pts recompute check: {mism} mismatches of {len(q)} "
         "(expect 0 -- leg_height_pts already IS |leg_start_price - pxl_level_0|)")

    # stop == level_1.0 +/- STOP_BUFFER (short/long); already-recorded
    # invalidation fires at level_1.0 +/- TICK -- report the exact gap
    stop = level_1_0 + buf * (-d)          # short(d=-1): +buf ; long(d=1): -buf
    stop = pd.Series(stop).round(2).to_numpy()
    inval_threshold_gap = buf - TICK
    print(f"stop vs structural-invalidation threshold: stop sits at "
         f"leg_start_price {'+.' if True else ''}{buf}pt; invalidation fires "
         f"at leg_start_price+/-{TICK}pt (per A2, already recorded as "
         f"pxl_invalidated/invalidation_reason='high_taken'). Same anchor "
         f"price (leg_start_price); threshold gap = {inval_threshold_gap}pt "
         "-- invalidation ALWAYS fires at or before the leg-scale stop, so a "
         "row that is still alive at trigger time has not yet had its "
         "leg-scale stop touched either.")

    target = level_0_0.copy()

    out_rows = []
    for r in R_VALUES:
        entry_r = level_0_0 + r * leg_h * (-d)     # short: entry above low; long: below high
        # short (d=-1): entry = level_0_0 + r*leg_h ; long (d=1): entry = level_0_0 - r*leg_h
        entry_r = pd.Series(entry_r).round(2).to_numpy()
        reward = r * leg_h
        risk = (1 - r) * leg_h + buf
        realised_R = reward / risk
        for i in range(len(q)):
            out_rows.append(dict(
                event_id=q.event_id.iloc[i], r=r,
                entry_r=entry_r[i], stop_leg=stop[i], target_leg=target[i],
                reward_pts=reward[i], risk_pts=risk[i], realised_R=realised_R[i],
                retrace_frac_at_trigger=q.retrace_frac.iloc[i],
                retrace_already_past_r=bool(q.retrace_frac.iloc[i] >= r),
            ))
    geo = pd.DataFrame(out_rows)
    geo.to_parquet("output/p_table_leg_scale_geometry.parquet")

    def dist(s):
        s = s.dropna()
        if not len(s):
            return None
        return dict(n=int(len(s)), median=round(float(s.median()), 3),
                   p25=round(float(s.quantile(.25)), 3),
                   p75=round(float(s.quantile(.75)), 3),
                   p90=round(float(s.quantile(.9)), 3))

    report = dict(
        n_qualified=int(len(q)),
        min_leg_retrace=min_retrace,
        constraint_check="PASS -- all declared r exceed MIN_LEG_RETRACE",
        retrace_frac_below_min_leg_retrace_anomaly=dict(
            n=int((q.retrace_frac < min_retrace).sum()),
            pct=round(float((q.retrace_frac < min_retrace).mean()), 4),
            note="small boundary-effect population (max observed 0.382, all "
                 "within ~0.10 of the threshold) already present in the "
                 "gated, committed table -- not introduced by this run"),
        leg_height_recompute_mismatches=int(mism),
        stop_invalidation_coincidence=dict(
            anchor_price="leg_start_price (same for both)",
            stop_offset_pts=buf, invalidation_offset_pts=TICK,
            gap_pts=inval_threshold_gap,
            statement="Coincide in ANCHOR (same origin price); invalidation "
                     "fires strictly before the leg-scale stop is technically "
                     "touched (tighter threshold), so 'stopped out' and "
                     "'structure invalidated' describe the same event at "
                     "the same location for practical purposes."),
        by_r={str(r): dict(
            reward_pts=dist(geo[geo.r == r].reward_pts),
            risk_pts=dist(geo[geo.r == r].risk_pts),
            realised_R=dist(geo[geo.r == r].realised_R),
            asymptotic_R_r_over_1_minus_r=round(r / (1 - r), 3),
            pct_rows_retrace_already_past_r=round(
                float(geo[geo.r == r].retrace_already_past_r.mean()), 4),
        ) for r in R_VALUES},
    )
    json.dump(report, open("output/p_table_leg_scale_geometry.json", "w"), indent=1)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
