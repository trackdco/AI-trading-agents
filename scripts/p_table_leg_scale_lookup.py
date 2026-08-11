"""LEG-SCALE ARM -- Task 3 (displacement-on-the-leg, three separable columns)
+ Task 5 (sweep precondition, recorded not filtered).

Grouped by (date, session, tf_trigger) for efficiency: reload the minute grid
once per group (cached front minutes), aggregate to tf once, then compute all
per-row lookups against the SAME bars. Working population: qualified rows only
(4,815), matching Task 1/2/7's population choice.

Mechanical/structural columns only -- no outcome, no selection, no filtering.
"""
from __future__ import annotations

import json
import math
import os
import sys
from collections import defaultdict
from datetime import date as Date, datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from p_table_lib import (CONFIG, NY, UTC, aggregate_tf, build_session_minutes,
                         session_window_utc, true_ranges)
from build_p_table import load_front_minutes, minute_map_for_day_window

CACHE = os.environ.get(
    "P_TABLE_CACHE",
    "/tmp/claude-0/-home-user-AI-trading-agents/a6ad12c8-81a9-57f1-b548-760dc4a1f9f9/scratchpad/cache")

# DECLARED (new, not previously defined anywhere in this build): the Asia
# reference window used ONLY as a sweep-detection reference level, never as a
# traded session (Asia remains excluded from trading per SPEC A1). Standard
# Tokyo-adjacent Globex convention, ET-anchored (DST-safe via zoneinfo).
ASIA_START, ASIA_END = 19, 3   # 19:00 ET (prior evening) -> 03:00 ET
SWEEP_LOOKBACK_BARS_CAP = 200   # bound the backward scan (generous; sessions are short)
SWEEP_CLOSE_BACK_WITHIN_BARS = 3


def asia_window_utc(d: Date):
    start = datetime.combine(d - timedelta(days=1), datetime.min.time(), NY).replace(hour=ASIA_START)
    end = datetime.combine(d, datetime.min.time(), NY).replace(hour=ASIA_END)
    return start.astimezone(UTC), end.astimezone(UTC)


def window_high_low(df: pd.DataFrame, t0: datetime, t1: datetime):
    sub = df[(df.ts >= t0) & (df.ts < t1)]
    if not len(sub):
        return float("nan"), float("nan")
    return float(sub.high.max()), float(sub.low.min())


def find_fvg(bars, direction: int) -> bool:
    """3-bar imbalance in the leg's own direction. direction=-1 (down-leg):
    bar[i].low > bar[i+2].high. direction=1 (up-leg): bar[i].high < bar[i+2].low."""
    for i in range(len(bars) - 2):
        if direction == -1 and bars[i].low > bars[i + 2].high:
            return True
        if direction == 1 and bars[i].high < bars[i + 2].low:
            return True
    return False


def find_consec_closes(bars, direction: int) -> bool:
    """>=2 consecutive close-over-close steps in the leg's direction (a run of
    3 bars: close[i] </> close[i-1] </> close[i-2], i.e. two consecutive
    same-direction steps) -- distinct from 'consecutive down/up CANDLES'."""
    run = 1
    for i in range(1, len(bars)):
        step_ok = (bars[i].close < bars[i - 1].close) if direction == -1 else \
                  (bars[i].close > bars[i - 1].close)
        run = run + 1 if step_ok else 1
        if run >= 3:      # 3 bars = 2 consecutive steps
            return True
    return False


def find_sweep(bars_before_leg, direction: int, refs: dict):
    """refs: {name: (high, low)}. Short (direction=-1): look for a HIGH sweep
    (buy-side liquidity taken) then close back below within N bars. Long
    (direction=1): LOW sweep (sell-side) then close back above."""
    best = None   # (bars_before_leg_end, name)
    for name, (rhi, rlo) in refs.items():
        ref = rhi if direction == -1 else rlo
        if ref is None or (isinstance(ref, float) and math.isnan(ref)):
            continue
        for i, b in enumerate(bars_before_leg):
            took = (b.high > ref) if direction == -1 else (b.low < ref)
            if not took:
                continue
            for j in range(i, min(i + 1 + SWEEP_CLOSE_BACK_WITHIN_BARS, len(bars_before_leg))):
                cb = bars_before_leg[j]
                closed_back = (cb.close < ref) if direction == -1 else (cb.close > ref)
                if closed_back:
                    bars_to_leg = len(bars_before_leg) - 1 - j
                    if best is None or bars_to_leg < best[0]:
                        best = (bars_to_leg, name)
                    break
    return best


def main():
    fit = pd.read_parquet("output/p_table.parquet")
    q = fit[fit.qualified].reset_index(drop=True)
    df, front = load_front_minutes(CACHE)

    groups = defaultdict(list)
    for idx, row in q.iterrows():
        groups[(row.date, row.session, int(row.tf_trigger))].append(idx)

    out = {}
    for gi, ((ds, session, tf), idxs) in enumerate(groups.items()):
        d = Date.fromisoformat(ds)
        w_utc, s_utc, e_utc = session_window_utc(d, session)
        mm = minute_map_for_day_window(df, w_utc, e_utc)
        built = build_session_minutes(mm, d, session)
        if built is None:
            continue
        minutes, _, _ = built
        tf_bars = aggregate_tf(minutes, tf)
        by_close = {b.close_ts: b for b in tf_bars}
        trs = true_ranges(tf_bars)
        atr = [float("nan")] * len(tf_bars)
        P = CONFIG["ATR_PERIOD"]
        for i in range(len(tf_bars)):
            if i + 1 >= P:
                atr[i] = sum(trs[i - P + 1:i + 1]) / P

        # sweep reference windows (per date, independent of session/tf)
        a0, a1 = asia_window_utc(d)
        asia_hi, asia_lo = window_high_low(df, a0, a1)
        on_hi, on_lo = window_high_low(
            df, datetime.combine(d - timedelta(days=1), datetime.min.time(), NY)
                .replace(hour=18).astimezone(UTC), s_utc)
        preopen_hi, preopen_lo = window_high_low(df, w_utc, s_utc)
        refs = dict(overnight=(on_hi, on_lo), asia=(asia_hi, asia_lo),
                   pre_open_range=(preopen_hi, preopen_lo))

        for idx in idxs:
            r = q.loc[idx]
            direction = int(r.direction)
            leg_start_ts = pd.Timestamp(r.leg_start_ts).to_pydatetime()
            pxl_ts = pd.Timestamp(r.pxl_ts).to_pydatetime()
            leg_bars = [b for b in tf_bars if leg_start_ts <= b.close_ts <= pxl_ts]
            pre_leg_bars = [b for b in tf_bars if b.close_ts <= leg_start_ts][-SWEEP_LOOKBACK_BARS_CAP:]

            piv_bar = by_close.get(pxl_ts)
            piv_i = next((i for i, b in enumerate(tf_bars) if b.close_ts == pxl_ts), None)
            atr_at_pivot = atr[piv_i] if piv_i is not None else float("nan")

            fvg = find_fvg(leg_bars, direction)
            consec = find_consec_closes(leg_bars, direction)
            leg_range_atr = (r.leg_height_pts / atr_at_pivot
                             if atr_at_pivot and not math.isnan(atr_at_pivot)
                             and atr_at_pivot > 0 else float("nan"))
            sweep = find_sweep(pre_leg_bars, direction, refs)

            out[r.event_id] = dict(
                fvg_on_leg=fvg, leg_range_atr14_at_pivot=leg_range_atr,
                consec_2_closes_on_leg=consec,
                sweep_present=sweep is not None,
                sweep_extreme=(sweep[1] if sweep else None),
                sweep_bars_before_leg=(sweep[0] if sweep else None),
                atr14_at_pivot_pts=atr_at_pivot,
            )
        if (gi + 1) % 200 == 0:
            print(f"  {gi + 1}/{len(groups)} groups", flush=True)

    res = pd.DataFrame.from_dict(out, orient="index").reset_index().rename(
        columns={"index": "event_id"})
    res.to_parquet("output/p_table_leg_scale_displacement_sweep.parquet")

    print(f"resolved {len(res)} of {len(q)} qualified rows")
    print("fvg_on_leg rate:", round(res.fvg_on_leg.mean(), 4))
    print("consec_2_closes_on_leg rate:", round(res.consec_2_closes_on_leg.mean(), 4))
    print("sweep_present rate:", round(res.sweep_present.mean(), 4))
    print("sweep_extreme distribution:", res.sweep_extreme.value_counts().to_dict())
    print("leg_range_atr14_at_pivot describe:\n", res.leg_range_atr14_at_pivot.describe())


if __name__ == "__main__":
    main()
