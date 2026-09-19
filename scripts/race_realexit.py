#!/usr/bin/env python3
"""REAL-EXIT RESCORE — the trader's actual shipped exit, not the structural
target the census used everywhere else.

THE PROBLEM (see docs/real-exit-rescore.md): M1 was scored against first
passage to the 15m MA; M2/M3 against first structure beyond entry. Those
close at a median ~0.5R. The untruncated run census (race_runs.parquet)
shows the true excursion reaches p90 7.66R, and 47.4% of fights ran
further than their recorded (target-truncated) mfe_r. The family's
"does not price" verdict was measured on a trade the trader would never
hold that way.

THE ACTUAL EXIT, implemented exactly:
  * 75% of the position exits at a LIMIT at entry + 3*risk (3R).
  * 25% trails the 15m BB(20) middle band: exits the first time a 15m
    candle CLOSES through the MA against the position.
  * Stop = the recorded `stop` for the WHOLE position until 3R prints;
    once the 75% comes off, the runner's stop moves to breakeven.
  * Same-bar convention: stop wins over target in the same 1m bar
    (mirrors race_outcomes.walk()).
  * Cost: 0.5pt entry-side + 0.5pt exit-side (the exit-side cost is
    apportioned across the two legs by size, so splitting the exit does
    not by itself increase total cost) = 1.0pt round trip, i.e.
    cost_r = 1.0 / risk, subtracted once from the blended result.
  * EOD flatten at session end (sess_day 18:00 + 23h) if nothing else
    has fired.

TWO-PHASE MODEL (read directly off the task's own outcome formula,
"0.75*3 + 0.25*(runner) when 3R reached; -1 (+cost) when stopped first"):
before 3R prints, the WHOLE position is governed only by the initial
stop vs the 3R limit (race, stop wins ties) — the 15m trail is not yet
live for either leg. Only once 3R has printed does the runner exist and
start watching (a) the breakeven stop and (b) the 15m close-trail, from
the bar AFTER the 3R print (no same-bar entanglement between the target
fill and the runner's own risk state).

    python -m scripts.race_realexit
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.conviction_lib import add_counts, load, signals        # noqa: E402
from src.htf_ma.levels import NY, bb_ma_asof                        # noqa: E402

OUT = ROOT / "output/htf_ma_census/race_realexit.parquet"
COST_R_TOTAL_PTS = 1.0     # 0.5pt entry-side + 0.5pt exit-side (apportioned)


def day_arrays(bars: pd.DataFrame, sess_day: str):
    """Per-day 1m segment arrays + the 15m trail-fire booleans (long/short),
    causal (bb_ma_asof as-of only), built once per session-day."""
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t1 = t0 + pd.Timedelta(hours=23)
    hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30)) & (bars.index < t1)]
    seg = hist[(hist.index >= t0) & (hist.index < t1)]
    if seg.empty:
        return None
    idx = seg.index
    N = len(idx)

    ma15, _ = bb_ma_asof(hist, 15)
    f15 = hist.resample("15min", label="right", closed="left").agg(
        {"open": "first", "high": "max", "low": "min",
         "close": "last"}).dropna()
    f15 = f15[(f15.index > t0) & (f15.index <= t1)]
    # SAME grammar as trigger_race_census's M2/M3 state machine: the MA
    # line the candle is judged against, at the candle's own close minute.
    ma_at15 = ma15.reindex(f15.index - pd.Timedelta(minutes=1)).to_numpy()
    pos15 = np.searchsorted(idx.values, f15.index.values)   # first bar of NEXT bucket
    closing_pos = pos15 - 1                                  # the candle's own close bar
    valid = (closing_pos >= 0) & (closing_pos < N) & np.isfinite(ma_at15)
    fclose = f15.close.to_numpy()

    trail_long = np.zeros(N, dtype=bool)
    trail_short = np.zeros(N, dtype=bool)
    cp = closing_pos[valid]
    trail_long[cp] = fclose[valid] < ma_at15[valid]
    trail_short[cp] = fclose[valid] > ma_at15[valid]

    return dict(idx=idx, hi=seg.high.to_numpy(), lo=seg.low.to_numpy(),
                cl=seg.close.to_numpy(), N=N,
                trail_long=trail_long, trail_short=trail_short)


def score_one(dd: dict, t, d: int, entry: float, stop: float, risk: float):
    idx, hi, lo, cl, N = dd["idx"], dd["hi"], dd["lo"], dd["cl"], dd["N"]
    trail = dd["trail_long"] if d > 0 else dd["trail_short"]
    j0 = int(np.searchsorted(idx.values, pd.Timestamp(t).to_datetime64()))
    if j0 >= N:
        return None

    tgt = entry + d * 3.0 * risk
    cost_r = COST_R_TOTAL_PTS / risk

    # ---- PHASE 1: initial stop vs the 3R limit. Same-bar -> stop wins.
    j = j0
    stopped_j = hit3_j = None
    while j < N:
        stop_hit = (lo[j] <= stop) if d > 0 else (hi[j] >= stop)
        if stop_hit:
            stopped_j = j
            break
        tgt_hit = (lo[j] <= tgt <= hi[j]) if d > 0 else (hi[j] >= tgt >= lo[j])
        if tgt_hit:
            hit3_j = j
            break
        j += 1

    if stopped_j is not None:
        raw = -1.0
        return dict(scid=None, reached_3r=False, exit_mode="stop",
                    runner_mode=None, runner_raw=np.nan, raw_result=raw,
                    real_out=raw - cost_r, cost_r=cost_r,
                    j0=j0, j_exit=stopped_j)

    if hit3_j is None:          # neither stop nor 3R by session end
        raw = d * (cl[N - 1] - entry) / risk
        return dict(scid=None, reached_3r=False, exit_mode="eod_phase1",
                    runner_mode=None, runner_raw=np.nan, raw_result=raw,
                    real_out=raw - cost_r, cost_r=cost_r,
                    j0=j0, j_exit=N - 1)

    # ---- PHASE 2: the 25% runner, breakeven stop + 15m trail, from the
    # bar AFTER the 3R print.
    be = entry
    j2 = hit3_j + 1
    runner_raw, mode, j_exit = None, "eod", N - 1
    while j2 < N:
        be_hit = (lo[j2] <= be) if d > 0 else (hi[j2] >= be)
        if be_hit:
            runner_raw, mode, j_exit = 0.0, "breakeven", j2
            break
        if trail[j2]:
            runner_raw, mode, j_exit = d * (cl[j2] - entry) / risk, "trail", j2
            break
        j2 += 1
    if runner_raw is None:
        runner_raw = d * (cl[N - 1] - entry) / risk

    raw = 0.75 * 3.0 + 0.25 * runner_raw
    return dict(scid=None, reached_3r=True, exit_mode=f"3r+{mode}",
                runner_mode=mode, runner_raw=runner_raw, raw_result=raw,
                real_out=raw - cost_r, cost_r=cost_r,
                j0=j0, j_exit=j_exit)


def main() -> None:
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low",
                                              "close", "volume"]]

    B = add_counts(signals(load()))
    B["t"] = pd.to_datetime(B.t)
    assert (B.risk > 0).all(), "non-positive risk in the frame"

    rows = []
    days = sorted(B.sess_day.unique())
    for k, day in enumerate(days):
        dd = day_arrays(bars, day)
        if dd is None:
            continue
        sub = B[B.sess_day == day]
        for r in sub.itertuples():
            res = score_one(dd, r.t, int(r.direction), float(r.entry),
                            float(r.stop), float(r.risk))
            if res is None:
                print(f"  WARNING: {r.scid} entry bar out of segment "
                      "(no real-exit score)")
                continue
            res["scid"] = r.scid
            rows.append(res)
        if k % 40 == 0:
            print(f"  {k}/{len(days)}...", flush=True)

    Rx = pd.DataFrame(rows)
    M = B.merge(Rx, on="scid", how="inner")
    print(f"\nscored {len(M)} / {len(B)} fights "
          f"({len(B) - len(M)} dropped for out-of-segment entry)")
    M.to_parquet(OUT, index=False)
    print(f"written: {OUT}")


if __name__ == "__main__":
    main()
