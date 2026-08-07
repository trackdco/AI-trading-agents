#!/usr/bin/env python3
"""EXIT STUDY E — pre-registered in docs/PREREG-htf-ma.md BEFORE this run.

Two trader rules (E1 trail, E2/E3 progress-30/45) vs two baselines (B1
first-target-or-stop, B2 hold-with-stop), both Census B arms, fit only.
Captured W per event net of 0.5pt RT. Adoption bar in the prereg.

    python -m scripts.htf_ma_exit_study
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars           # noqa: E402
from src.htf_ma.levels import NY, bb_ma_asof              # noqa: E402

TICK = 0.25
COST_PTS = 0.5
PROG_W = 0.5


def era_of(day: str) -> str:
    return "H2-2025" if day < "2026-01-01" else "H1-2026"


def main() -> None:
    F = pd.read_parquet(ROOT / "output/htf_ma_census/censusB_fit.parquet")
    F["era"] = F.sess_day.map(era_of)
    R = F[(F.kind == "reject") & (F.target_defined == True)].copy()   # noqa: E712
    B = F[(F.kind == "break") & (F.retraced_ma == True)               # noqa: E712
          & (F.target_defined == True)].copy()                        # noqa: E712
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close", "volume"]]

    rows = []
    days = sorted(set(R.sess_day) | set(B.sess_day))
    for k, day in enumerate(days):
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        t1 = t0 + pd.Timedelta(hours=23)
        hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30)) & (bars.index < t1)]
        if hist.empty:
            continue
        ma15, _ = bb_ma_asof(hist, 15)
        f15 = hist.resample("15min", label="right", closed="left").agg(
            {"high": "max", "low": "min", "close": "last"}).dropna()
        ma_f15 = ma15.reindex(f15.index - pd.Timedelta(minutes=1))
        ma_f15.index = f15.index
        seg = hist[(hist.index >= t0) & (hist.index < t1)]
        idx = seg.index
        hi, lo, cl = seg.high.to_numpy(), seg.low.to_numpy(), seg.close.to_numpy()

        for arm, D in (("reject", R[R.sess_day == day]),
                       ("break", B[B.sess_day == day])):
            for r in D.itertuples():
                direction = (-1 if r.side == "below" else 1) if arm == "reject" \
                    else (1 if r.break_dir == "up" else -1)
                if arm == "reject":
                    entry = r.event_px
                    e_t = pd.Timestamp(r.t)
                else:
                    entry = r.retest_px
                    e_t = pd.Timestamp(r.t) + pd.Timedelta(minutes=float(r.t_retest_min))
                j0 = int(np.searchsorted(idx.values, e_t.to_datetime64()))
                if j0 >= len(idx) or not np.isfinite(entry):
                    continue
                stop0 = (r.trig_high + TICK) if direction < 0 else (r.trig_low - TICK)
                tgt = entry + direction * r.next_level_dist_W * r.w15
                cost_w = COST_PTS / r.w15
                base = {"era": r.era, "arm": arm, "side": r.side, "day": day,
                        "cluster_id": r.cluster_id}

                def capw(px):
                    return direction * (px - entry) / r.w15 - cost_w

                # ---- B2 hold-with-stop / E2 / E3 progress, one walk -------
                hold_exit = cl[-1]
                stopped_at = None
                fav_run, tgt_hit_at = 0.0, None
                for j in range(j0, len(idx)):
                    if (lo[j] <= stop0) if direction > 0 else (hi[j] >= stop0):
                        stopped_at = j
                        break
                    fav = direction * ((hi[j] if direction > 0 else lo[j]) - entry) / r.w15
                    fav_run = max(fav_run, fav)
                    if tgt_hit_at is None and \
                            direction * ((hi[j] if direction > 0 else lo[j]) - tgt) >= 0:
                        tgt_hit_at = j
                b2 = capw(stop0) if stopped_at is not None else capw(hold_exit)
                # B1 first-target-or-stop
                if tgt_hit_at is not None and (stopped_at is None or tgt_hit_at <= stopped_at):
                    b1 = capw(tgt)
                elif stopped_at is not None:
                    b1 = capw(stop0)
                else:
                    b1 = capw(hold_exit)
                for M, key in ((30, "E2"), (45, "E3")):
                    jM = int(np.searchsorted(idx.values,
                                             (e_t + pd.Timedelta(minutes=M)).to_datetime64()))
                    if stopped_at is not None and stopped_at < jM:
                        val = capw(stop0)
                    else:
                        prog = False
                        for j in range(j0, min(jM, len(idx))):
                            fav = direction * ((hi[j] if direction > 0 else lo[j]) - entry) / r.w15
                            if fav >= PROG_W or (direction * ((hi[j] if direction > 0
                                                 else lo[j]) - tgt) >= 0):
                                prog = True
                                break
                        if not prog:
                            val = capw(cl[min(jM, len(idx)) - 1])
                        else:
                            val = capw(stop0) if stopped_at is not None else capw(hold_exit)
                    base[key] = val
                # ---- E1 trail --------------------------------------------
                stop = stop0
                exit_px = hold_exit
                fbars = f15[(f15.index > idx[j0])]
                fi = list(fbars.index)
                pos, done = 0, False
                for j in range(j0, len(idx)):
                    if (lo[j] <= stop) if direction > 0 else (hi[j] >= stop):
                        exit_px, done = stop, True
                        break
                    while pos < len(fi) and fi[pos] <= idx[j]:
                        fb = fbars.iloc[pos]
                        m = ma_f15.get(fi[pos], np.nan)
                        if np.isfinite(m) and direction * (fb.close - m) > 0:
                            cand = (fb.low - TICK) if direction > 0 else (fb.high + TICK)
                            if direction * (cand - stop) > 0:
                                stop = cand
                        pos += 1
                base["E1"] = capw(exit_px)
                base["B1"], base["B2"] = b1, b2
                rows.append(base)
        if k % 50 == 0:
            print(f"  {k}/{len(days)} days...", flush=True)

    D = pd.DataFrame(rows)
    D.to_parquet(ROOT / "output/htf_ma_census/exit_study.parquet", index=False)
    print(f"\nexit study: {len(D):,} events\n")
    print(f"{'arm':<8}{'era':<9}{'n':>6} | " +
          " | ".join(f"{c:^15}" for c in ("B1 tgt", "B2 hold", "E1 trail",
                                          "E2 p30", "E3 p45")))
    for arm in ("reject", "break"):
        for era in ("H2-2025", "H1-2026"):
            d = D[(D.arm == arm) & (D.era == era)]
            if len(d) == 0:
                continue
            cells = []
            for c in ("B1", "B2", "E1", "E2", "E3"):
                cm = d.groupby("cluster_id")[c].mean()
                cells.append(f"{d[c].mean():+.3f}/{cm.mean():+.3f}")
            print(f"{arm:<8}{era:<9}{len(d):>6,} | " +
                  " | ".join(f"{c:^15}" for c in cells))
    print("\n(cells: row-level mean / cluster-collapsed mean, captured W net)")
    print("\nADOPTION BAR (prereg): a rule beats BOTH baselines on the cluster")
    print("view in BOTH eras, per arm. Read the table against it; no variants.")


if __name__ == "__main__":
    main()
