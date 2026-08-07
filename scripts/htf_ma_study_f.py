#!/usr/bin/env python3
"""STUDY F — close_dist_bw as CONTINUOUS conviction weight (prereg §F).

Reject arm, fit. Capture under the SHIPPED convention (hold-with-stop at the
trigger-candle extreme ±1 tick, session close 17:00), net 0.5pt. Two declared
tests, read against the prereg bar, no variants:
  1. Spearman(close_dist_rank, captured W) > 0 in BOTH eras.
  2. Untuned ladder (rank quartiles -> 0.5/1.0/1.5/2.0) beats unweighted on
     mean capture PER UNIT WEIGHT, cluster view, BOTH eras.

    python -m scripts.htf_ma_study_f
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars           # noqa: E402
from src.htf_ma.levels import NY                          # noqa: E402

TICK = 0.25
COST_PTS = 0.5
LADDER = {0: 0.5, 1: 1.0, 2: 1.5, 3: 2.0}


def main() -> None:
    F = pd.read_parquet(ROOT / "output/htf_ma_census/censusB_fit.parquet")
    F["era"] = np.where(F.sess_day < "2026-01-01", "H2-2025", "H1-2026")
    R = F[(F.kind == "reject") & (F.target_defined == True)].copy()   # noqa: E712
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["high", "low", "close"]]

    caps = np.full(len(R), np.nan)
    R = R.reset_index(drop=True)
    for day, g in R.groupby("sess_day"):
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        seg = bars[(bars.index >= t0) & (bars.index < t0 + pd.Timedelta(hours=23))]
        if seg.empty:
            continue
        idx = seg.index
        hi, lo, cl = seg.high.to_numpy(), seg.low.to_numpy(), seg.close.to_numpy()
        for i, r in g.iterrows():
            d = -1 if r.side == "below" else 1
            entry = r.event_px
            stop = (r.trig_high + TICK) if d < 0 else (r.trig_low - TICK)
            j0 = int(np.searchsorted(idx.values, pd.Timestamp(r.t).to_datetime64()))
            exit_px = cl[-1]
            for j in range(j0, len(idx)):
                if (lo[j] <= stop) if d > 0 else (hi[j] >= stop):
                    exit_px = stop
                    break
            caps[i] = d * (exit_px - entry) / r.w15 - COST_PTS / r.w15
    R["cap"] = caps
    R = R[R.cap.notna() & R.close_dist_bw.notna()]

    lines = []
    def emit(s=""):
        print(s)
        lines.append(s)

    emit("STUDY F — close_dist_bw continuous rank (prereg §F), reject arm, "
         "shipped exit (hold-with-stop)")
    passes = []
    for era in ("H2-2025", "H1-2026"):
        d = R[R.era == era].copy()
        d["rank"] = d.close_dist_bw.rank(pct=True)
        rho, p = spearmanr(d["rank"], d.cap)
        ok1 = rho > 0
        d["q"] = pd.qcut(d["rank"], 4, labels=False)
        d["wt"] = d.q.map(LADDER)
        cm_u = d.groupby("cluster_id").cap.mean()
        wcap = (d.cap * d.wt).groupby(d.cluster_id).sum() / \
               d.wt.groupby(d.cluster_id).sum()
        ok2 = wcap.mean() > cm_u.mean()
        passes += [ok1, ok2]
        emit(f"  {era}: n={len(d):,} | TEST1 Spearman rho {rho:+.3f} (p={p:.1e}) "
             f"-> {'PASS' if ok1 else 'FAIL'}")
        emit(f"          TEST2 ladder-weighted {wcap.mean():+.4f}W vs unweighted "
             f"{cm_u.mean():+.4f}W per unit weight (cluster view) "
             f"-> {'PASS' if ok2 else 'FAIL'}")
        emit(f"          quartile mean caps: " + " ".join(
            f"Q{int(q)+1} {d[d.q==q].cap.mean():+.3f}" for q in range(4)))
    final = all(passes)
    emit(f"\nPREREG BAR (both tests, both eras): {'PASS — close_dist_bw ships as '
         'the conviction rank feeding the existing ladder, weights not gates'
         if final else 'FAIL — reported as a miss, no variants'}")
    with open(ROOT / "docs/PREREG-htf-ma.md", "a") as fh:
        fh.write("\n## F — RESULT (run 2026-08-07)\n\n```\n" + "\n".join(lines)
                 + "\n```\n")
    print("\nappended -> docs/PREREG-htf-ma.md")


if __name__ == "__main__":
    main()
