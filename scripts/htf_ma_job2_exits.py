#!/usr/bin/env python3
"""JOB 2 — fixed-R and scale-out exit sweep (prereg: docs/PREREG-htf-ma.md).

MFE-in-R distribution first (never yet produced), then singles at
1/1.5/2/2.5/3/4/5/6R, then partials {50,75}% at {1,1.5,2}R with remainder
(hold | E1-trail). Legs are independent walks from entry (the prior partial
convention); partial leg fills at target minus one tick; costs 0.5pt/RT once
per trade. Baselines: first-structural-target, hold-with-stop. Plateau bar
per prereg; monthly LODO reported for the winner. Both arms, both eras,
cluster-collapsed. Frame persisted.

    python -m scripts.htf_ma_job2_exits
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
SINGLES = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0]
PARTIALS = [(p, T, rem) for p in (0.50, 0.75) for T in (1.0, 1.5, 2.0)
            for rem in ("hold", "trail")]


def main() -> None:
    F = pd.read_parquet(ROOT / "output/htf_ma_census/censusB_fit.parquet")
    F["era"] = np.where(F.sess_day < "2026-01-01", "H2-2025", "H1-2026")
    E = F[(F.target_defined == True) &                                 # noqa: E712
          ((F.kind == "reject") | ((F.kind == "break") & F.retraced_ma))].copy()
    E["arm"] = np.where(E.kind == "reject", "reject", "break")
    E = E.reset_index(drop=True)
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close", "volume"]]

    recs = []
    for day, g in E.groupby("sess_day"):
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30)) &
                    (bars.index < t0 + pd.Timedelta(hours=23))]
        if hist.empty:
            continue
        seg = hist[hist.index >= t0]
        idx = seg.index
        hi, lo, cl = seg.high.to_numpy(), seg.low.to_numpy(), seg.close.to_numpy()
        ma15, _ = bb_ma_asof(hist, 15)
        f15 = hist.resample("15min", label="right", closed="left").agg(
            {"high": "max", "low": "min", "close": "last"}).dropna()
        ma_f15 = ma15.reindex(f15.index - pd.Timedelta(minutes=1))
        ma_f15.index = f15.index
        for r in g.itertuples():
            d = (-1 if r.side == "below" else 1) if r.arm == "reject" \
                else (1 if r.break_dir == "up" else -1)
            entry = r.event_px if r.arm == "reject" else r.retest_px
            e_t = pd.Timestamp(r.t) if r.arm == "reject" else \
                pd.Timestamp(r.t) + pd.Timedelta(minutes=float(r.t_retest_min))
            stop = (r.trig_high + TICK) if d < 0 else (r.trig_low - TICK)
            risk = abs(entry - stop)
            if not (np.isfinite(entry) and risk > 0):
                continue
            j0 = int(np.searchsorted(idx.values, e_t.to_datetime64()))
            if j0 >= len(idx):
                continue
            cost_r = COST_PTS / risk
            # one pass: stop bar, MFE, first-touch bar per target R
            stop_j, mfe = None, 0.0
            touch: dict[float, int] = {}
            for j in range(j0, len(idx)):
                if (lo[j] <= stop) if d > 0 else (hi[j] >= stop):
                    stop_j = j
                    break
                fav = d * ((hi[j] if d > 0 else lo[j]) - entry) / risk
                mfe = max(mfe, fav)
                for T in SINGLES:
                    if T not in touch and fav >= T:
                        touch[T] = j
            eod_r = d * (cl[-1] - entry) / risk
            hold_r = (-1.0 if stop_j is not None else eod_r)
            # E1 trail leg (from entry)
            tstop, trail_r = stop, None
            fbars = f15[f15.index > idx[j0]]
            fi = list(fbars.index)
            pos = 0
            for j in range(j0, len(idx)):
                if (lo[j] <= tstop) if d > 0 else (hi[j] >= tstop):
                    trail_r = d * (tstop - entry) / risk
                    break
                while pos < len(fi) and fi[pos] <= idx[j]:
                    fb = fbars.iloc[pos]
                    m = ma_f15.get(fi[pos], np.nan)
                    if np.isfinite(m) and d * (fb.close - m) > 0:
                        cand = (fb.low - TICK) if d > 0 else (fb.high + TICK)
                        if d * (cand - tstop) > 0:
                            tstop = cand
                    pos += 1
            if trail_r is None:
                trail_r = eod_r
            # B1 first-structural-target
            tgt = entry + d * r.next_level_dist_W * r.w15
            b1_r = hold_r
            for j in range(j0, (stop_j if stop_j is not None else len(idx))):
                if d * ((hi[j] if d > 0 else lo[j]) - tgt) >= 0:
                    b1_r = d * (tgt - entry) / risk
                    break
            rec = {"era": r.era, "arm": r.arm, "cluster_id": r.cluster_id,
                   "month": r.sess_day[:7], "mfe": mfe,
                   "B1": b1_r - cost_r, "B2": hold_r - cost_r}
            for T in SINGLES:
                hit = T in touch and (stop_j is None or touch[T] < stop_j)
                rec[f"S{T}"] = ((T * risk - TICK) / risk if hit else hold_r) - cost_r
            for p, T, rem in PARTIALS:
                hit = T in touch and (stop_j is None or touch[T] < stop_j)
                leg1 = (T * risk - TICK) / risk if hit else None
                leg2 = hold_r if rem == "hold" else trail_r
                v = (p * leg1 + (1 - p) * leg2) if leg1 is not None else \
                    (hold_r if rem == "hold" else trail_r)
                rec[f"P{int(p*100)}_{T}_{rem}"] = v - cost_r
            recs.append(rec)
    D = pd.DataFrame(recs)
    D.to_parquet(ROOT / "output/htf_ma_census/job2_frame.parquet", index=False)

    lines = []
    def emit(s=""):
        print(s)
        lines.append(s)

    emit("JOB 2 — exit sweep (prereg bar: interior-of-plateau, beat both baselines, both eras, per arm)")
    emit("\n== MFE distribution in R (first time produced) ==")
    for arm in ("reject", "break"):
        for era in ("H2-2025", "H1-2026"):
            m = D[(D.arm == arm) & (D.era == era)].mfe
            shares = " ".join(f">={T}R:{(m>=T).mean()*100:.0f}%" for T in (1, 2, 3, 5))
            emit(f"  {arm:<7} {era}: p50 {m.median():.2f} p75 {m.quantile(.75):.2f} "
                 f"p90 {m.quantile(.9):.2f} p95 {m.quantile(.95):.2f} max {m.max():.1f} | {shares}")

    cfgs = [f"S{T}" for T in SINGLES] + \
           [f"P{int(p*100)}_{T}_{rem}" for p, T, rem in PARTIALS]
    emit("\n== cluster-collapsed mean netR per config (vs B1/B2) ==")
    results = {}
    for arm in ("reject", "break"):
        emit(f"[{arm}]")
        for era in ("H2-2025", "H1-2026"):
            d = D[(D.arm == arm) & (D.era == era)]
            base1 = d.groupby("cluster_id").B1.mean().mean()
            base2 = d.groupby("cluster_id").B2.mean().mean()
            vals = {c: d.groupby("cluster_id")[c].mean().mean() for c in cfgs}
            results[(arm, era)] = (vals, base1, base2)
            best = max(vals, key=vals.get)
            emit(f"  {era}: B1 {base1:+.3f} B2 {base2:+.3f} | best {best} "
                 f"{vals[best]:+.3f} | " +
                 " ".join(f"{c}:{v:+.3f}" for c, v in sorted(vals.items(),
                          key=lambda kv: -kv[1])[:6]))
    emit("\n== plateau reading (singles line; a winner needs itself+neighbours > both baselines, both eras) ==")
    for arm in ("reject", "break"):
        okT = []
        for k, T in enumerate(SINGLES):
            ok = True
            for era in ("H2-2025", "H1-2026"):
                vals, b1, b2 = results[(arm, era)]
                for Tn in {SINGLES[max(0, k - 1)], T, SINGLES[min(len(SINGLES) - 1, k + 1)]}:
                    ok &= vals[f"S{Tn}"] > b1 and vals[f"S{Tn}"] > b2
            if ok:
                okT.append(T)
        emit(f"  {arm}: interior-plateau singles = {okT if okT else 'NONE'}")
        for p, T, rem in PARTIALS:
            c = f"P{int(p*100)}_{T}_{rem}"
            ok = all(results[(arm, era)][0][c] > results[(arm, era)][1]
                     and results[(arm, era)][0][c] > results[(arm, era)][2]
                     for era in ("H2-2025", "H1-2026"))
            if ok:
                emit(f"  {arm}: partial {c} beats both baselines, both eras")
    with open(ROOT / "docs/PREREG-htf-ma.md", "a") as fh:
        fh.write("\n## Job 2 — RESULT (run 2026-08-08)\n\n```\n" + "\n".join(lines) + "\n```\n")
    print("\nappended -> docs/PREREG-htf-ma.md (monthly LODO for any winner runs on the persisted frame)")


if __name__ == "__main__":
    main()
