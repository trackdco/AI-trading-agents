#!/usr/bin/env python3
"""RUN CENSUS — how far does each fight actually run, exit-agnostic.

WHY THIS EXISTS: every EV figure on this family so far is scored against
targets that are NOT the trader's (M1 -> the 15m MA; M2/M3 -> the nearest
structure beyond entry). His actual exit is 75% at 3R plus a trail. A
"does not price" verdict under the wrong target says little about the
trades themselves.

`mfe_r` as recorded in race_outcomes is TRUNCATED — the outcome walk
stops accumulating excursion the moment the target is hit. This script
re-walks every fight with NO target at all: from entry, forward, until
the stop is hit or the session segment ends, recording the full
excursion path. That makes the run distribution independent of any exit
choice, which is the only fair way to ask "do high-conviction trades run
further than base?".

ALSO ADDS DELTA-DIVERGENCE signals at the decision minute (price making
an extreme that cumulative delta does not confirm) — a family the
agree/disagree flow signals do not capture.

    python -m scripts.race_runs [--build]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from src.htf_ma.levels import NY                                    # noqa: E402

OUT = ROOT / "output/htf_ma_census/race_runs.parquet"
WIDE = ROOT / "output/htf_ma_census/race_wide.parquet"
FP = ROOT / "output/fp_minutes_full.parquet"
RTARGETS = [1, 2, 3, 5, 8]
HORIZONS = [5, 15, 30, 60]


def day_runs(bars, fpd, sess_day, rows):
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t1 = t0 + pd.Timedelta(hours=23)
    seg = bars[(bars.index >= t0) & (bars.index < t1)]
    if seg.empty:
        return []
    idx = seg.index
    hi, lo, cl = (seg.high.to_numpy(), seg.low.to_numpy(),
                  seg.close.to_numpy())
    N = len(idx)
    out = []
    for r in rows:
        t = pd.Timestamp(r["t"])
        j0 = int(np.searchsorted(idx.values, t.to_datetime64()))
        if j0 >= N:
            continue
        d = int(r["direction"])
        entry, stop = float(r["entry"]), float(r["stop"])
        risk = abs(entry - stop)
        if risk <= 0:
            continue
        # ---- untruncated walk: NO target, stop or session end only
        mfe = mae = 0.0
        j_peak = j0
        stop_j = None
        for j in range(j0, N):
            adv = d * ((hi[j] if d > 0 else lo[j]) - entry) / risk
            adverse = d * ((lo[j] if d > 0 else hi[j]) - entry) / risk
            if adv > mfe:
                mfe, j_peak = adv, j
            mae = min(mae, adverse)
            if (lo[j] <= stop) if d > 0 else (hi[j] >= stop):
                stop_j = j
                break
        end_j = stop_j if stop_j is not None else N - 1
        rec = {"scid": r["scid"], "run_mfe_r": mfe, "run_mae_r": mae,
               "stopped": stop_j is not None,
               "bars_held": int(end_j - j0),
               "mins_to_peak": int(j_peak - j0),
               "eod_r": d * (cl[end_j] - entry) / risk}
        for R in RTARGETS:
            rec[f"reach_{R}r"] = bool(mfe >= R)
        for H in HORIZONS:
            k = min(j0 + H, N - 1)
            if k > j0:
                w_hi = hi[j0:k + 1].max() if d > 0 else lo[j0:k + 1].min()
                rec[f"exc_{H}m_r"] = d * (w_hi - entry) / risk
            else:
                rec[f"exc_{H}m_r"] = np.nan
        # ---- delta divergence at the DECISION minute (p = j0 - 1)
        p = j0 - 1
        for W in (5, 15, 30):
            a = max(p - W + 1, 0)
            if fpd is None or p < 0 or a > p:
                rec[f"div_{W}m"] = np.nan
                rec[f"dvg_{W}m"] = np.nan
                continue
            wnd = fpd[(fpd.index >= idx[a]) & (fpd.index <= idx[p])]
            if len(wnd) < max(3, W // 3):
                rec[f"div_{W}m"] = np.nan
                rec[f"dvg_{W}m"] = np.nan
                continue
            dpx = cl[p] - cl[a]
            dcvd = float(wnd.delta.sum())
            # divergence = price and cumulative delta disagree in sign
            rec[f"div_{W}m"] = float(np.sign(dpx) != np.sign(dcvd)
                                     and dpx != 0 and dcvd != 0)
            # signed strength, oriented to the TRADE: positive means the
            # divergence favours this trade (price ran the other way on
            # weakening opposing delta)
            rng = np.percentile(np.abs(np.diff(cl[max(a - 60, 0):p + 1])),
                                90) if p - a > 5 else np.nan
            sc = (dpx / rng) if (np.isfinite(rng) and rng > 0) else np.nan
            rec[f"dvg_{W}m"] = (-d * sc) if np.isfinite(sc) else np.nan
        out.append(rec)
    return out


def main() -> None:
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low",
                                              "close", "volume"]]
    B = pd.read_parquet(WIDE)
    B["t"] = pd.to_datetime(B.t)
    fp = pd.read_parquet(FP).sort_index()

    rows = B[["scid", "sess_day", "t", "direction", "entry",
              "stop"]].to_dict("records")
    days = sorted(B.sess_day.unique())
    res = []
    for k, day in enumerate(days):
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        fpd = fp[(fp.index >= t0) & (fp.index < t0 + pd.Timedelta(hours=23))]
        dr = [r for r in rows if r["sess_day"] == day]
        res.extend(day_runs(bars, fpd if len(fpd) else None, day, dr))
        if k % 40 == 0:
            print(f"  {k}/{len(days)}...", flush=True)
    R = pd.DataFrame(res)
    R.to_parquet(OUT, index=False)
    print(f"written: {OUT.name} ({len(R):,} rows)")

    M = B.merge(R, on="scid", how="inner")
    print(f"\njoined {len(M)} fights")
    print(f"TRUNCATION CHECK — recorded mfe_r vs untruncated run_mfe_r:")
    print(f"  recorded  p50 {M.mfe_r.median():.2f}  p90 "
          f"{M.mfe_r.quantile(.9):.2f}  max {M.mfe_r.max():.1f}")
    print(f"  true run  p50 {M.run_mfe_r.median():.2f}  p90 "
          f"{M.run_mfe_r.quantile(.9):.2f}  max {M.run_mfe_r.max():.1f}")
    und = (M.run_mfe_r > M.mfe_r + 1e-9).mean() * 100
    print(f"  fights whose true run EXCEEDS the recorded mfe: {und:.1f}%")
    print(f"\nP(reach R before stop), whole book:")
    for Rt in RTARGETS:
        print(f"   {Rt}R: {M[f'reach_{Rt}r'].mean()*100:5.1f}%")
    print(f"\nstopped {M.stopped.mean()*100:.1f}%   median bars held "
          f"{M.bars_held.median():.0f}   median mins to peak "
          f"{M.mins_to_peak.median():.0f}")
    print("\ndivergence coverage: " + "  ".join(
        f"{w}m {M[f'div_{w}m'].notna().mean()*100:.0f}% "
        f"(fires {M[f'div_{w}m'].mean()*100:.0f}%)" for w in (5, 15, 30)))


if __name__ == "__main__":
    main()
