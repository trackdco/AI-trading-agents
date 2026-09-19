#!/usr/bin/env python3
"""STUDY D-capture — confluence bins in NET R (prereg §D-capture, declared bar).

Shipped exits per arm (reject hold-with-stop; break first-target-or-stop).
NET R = (exit-entry)/stop_distance, 0.5pt cost per event. Bar on the reject
arm: (a) powered-bin means non-decreasing, both eras; (b) top powered bin
positive with 95% cluster interval clear of zero, both eras. Context tables
(session, profile-age) reported unbarred.

    python -m scripts.htf_ma_study_d_capture
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars           # noqa: E402
from src.htf_ma.levels import NY                          # noqa: E402

TICK = 0.25
COST_PTS = 0.5
MIN_CL = 30
BINS = [("1", lambda c: c <= 1), ("2", lambda c: c == 2), ("3", lambda c: c == 3),
        ("4", lambda c: c == 4), ("5+", lambda c: c >= 5)]


def main() -> None:
    F = pd.read_parquet(ROOT / "output/htf_ma_census/censusB_fit.parquet")
    F["era"] = np.where(F.sess_day < "2026-01-01", "H2-2025", "H1-2026")
    E = F[(F.target_defined == True) &                                 # noqa: E712
          ((F.kind == "reject") | ((F.kind == "break") & F.retraced_ma))].copy()
    E["arm"] = np.where(E.kind == "reject", "reject", "break")
    E = E.reset_index(drop=True)
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["high", "low", "close"]]

    netR = np.full(len(E), np.nan)
    for day, g in E.groupby("sess_day"):
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        seg = bars[(bars.index >= t0) & (bars.index < t0 + pd.Timedelta(hours=23))]
        if seg.empty:
            continue
        idx = seg.index
        hi, lo, cl = seg.high.to_numpy(), seg.low.to_numpy(), seg.close.to_numpy()
        for i, r in g.iterrows():
            d = (-1 if r.side == "below" else 1) if r.arm == "reject" \
                else (1 if r.break_dir == "up" else -1)
            entry = r.event_px if r.arm == "reject" else r.retest_px
            e_t = pd.Timestamp(r.t) if r.arm == "reject" else \
                pd.Timestamp(r.t) + pd.Timedelta(minutes=float(r.t_retest_min))
            stop = (r.trig_high + TICK) if d < 0 else (r.trig_low - TICK)
            risk = abs(entry - stop)
            if not (np.isfinite(entry) and risk > 0):
                continue
            tgt = entry + d * r.next_level_dist_W * r.w15
            j0 = int(np.searchsorted(idx.values, e_t.to_datetime64()))
            exit_px = cl[-1]
            for j in range(j0, len(idx)):
                if (lo[j] <= stop) if d > 0 else (hi[j] >= stop):
                    exit_px = stop
                    break
                if r.arm == "break" and \
                        d * ((hi[j] if d > 0 else lo[j]) - tgt) >= 0:
                    exit_px = tgt
                    break
            netR[i] = (d * (exit_px - entry) - COST_PTS) / risk
    E["netR"] = netR
    E = E[E.netR.notna() & E.confluence_count.notna()]

    lines = []
    def emit(s=""):
        print(s)
        lines.append(s)

    emit("STUDY D-capture — confluence bins in NET R (prereg bar on reject arm)")
    verdicts = []
    for arm in ("reject", "break"):
        emit(f"\n[{arm}]")
        for era in ("H2-2025", "H1-2026"):
            d = E[(E.arm == arm) & (E.era == era)]
            means, tops = [], None
            row = []
            for name, sel in BINS:
                b = d[sel(d.confluence_count)]
                cm = b.groupby("cluster_id").netR.mean()
                if len(cm) < MIN_CL:
                    row.append(f"{name}:UNDERPWR(n{len(cm)})")
                    continue
                mu = cm.mean()
                se = cm.std(ddof=1) / np.sqrt(len(cm))
                lo95, hi95 = mu - 1.96 * se, mu + 1.96 * se
                means.append(mu)
                tops = (mu, lo95, len(cm))
                row.append(f"{name}:{mu:+.3f}[{lo95:+.3f},{hi95:+.3f}](n{len(cm)})")
            mono = all(means[k] <= means[k + 1] + 1e-12 for k in range(len(means) - 1))
            top_ok = tops is not None and tops[0] > 0 and tops[1] > 0
            if arm == "reject":
                verdicts += [mono, top_ok]
            emit(f"  {era}: " + " ".join(row))
            emit(f"          monotone(powered)={'Y' if mono else 'N'} | "
                 f"top-bin>0 w/ CI clear={'Y' if top_ok else 'N'}")
    final = all(verdicts)
    emit(f"\nPREREG BAR (reject arm, both parts, both eras): "
         f"{'PASS' if final else 'FAIL — miss recorded, no variants'}")

    emit("\n== context (unbarred): reject netR by bin x session (pooled eras) ==")
    dR = E[E.arm == "reject"]
    for s in ("asia", "london", "ny_pre", "ny_rth_am", "ny_pm"):
        d = dR[dR.session == s]
        row = []
        for name, sel in BINS:
            b = d[sel(d.confluence_count)]
            cm = b.groupby("cluster_id").netR.mean()
            row.append(f"{name}:{cm.mean():+.2f}(n{len(cm)})" if len(cm) >= 15 else f"{name}:--")
        emit(f"  {s:<10} " + " ".join(row))
    emit("\n== context (unbarred): reject netR by bin x profile-age tercile ==")
    dR = dR.copy()
    dR["age"] = pd.qcut(dR.profile_min, 3, labels=["early", "mid", "late"])
    for a in ("early", "mid", "late"):
        d = dR[dR.age == a]
        row = []
        for name, sel in BINS:
            b = d[sel(d.confluence_count)]
            cm = b.groupby("cluster_id").netR.mean()
            row.append(f"{name}:{cm.mean():+.2f}(n{len(cm)})" if len(cm) >= 15 else f"{name}:--")
        emit(f"  {a:<6} " + " ".join(row))

    with open(ROOT / "docs/PREREG-htf-ma.md", "a") as fh:
        fh.write("\n## D-capture — RESULT (run 2026-08-07)\n\n```\n"
                 + "\n".join(lines) + "\n```\n")
    print("\nappended -> docs/PREREG-htf-ma.md")


if __name__ == "__main__":
    main()
