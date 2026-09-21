#!/usr/bin/env python3
"""HTF MA census gates (SPEC §6) — level-engine subset: G1, G7, G8, G2-lite, G4.

Nothing in the census is believed until these pass. This script runs the gates
that guard the LEVEL ENGINE (the layer where the depth-lookahead class of bug
lives). Census-stage gates (G3 roll, G5 completeness, G6 clustering) run with
the censuses. FIT DAYS ONLY — gates need no holdout data.

    python -m scripts.htf_ma_gates
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                    # noqa: E402
from src.htf_ma.levels import (NY, TFS, bb_ma_asof, vwap_bands,    # noqa: E402
                               profile_at_minutes)

# fit-window days incl. one fall-back DST (2025-11-02) and one spring-forward
# (2026-03-08); plus an ordinary day and the receipt day.
GATE_DAYS = ["2025-11-02", "2025-11-03", "2026-03-08", "2026-03-09", "2026-04-27"]


def day_frame(bars: pd.DataFrame, day: str) -> pd.DataFrame:
    d0 = pd.Timestamp(f"{day} 00:00", tz=NY)
    seg = bars[(bars.index >= d0 - pd.Timedelta(hours=6)) &
               (bars.index < d0 + pd.Timedelta(hours=18))]
    return seg


def main() -> None:
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close", "volume"]]

    fails = 0

    # G8 — resample alignment to exchange clock, not frame start
    seg = day_frame(bars, "2026-04-27")
    for tf in (15, 60):
        tfc = seg.close.resample(f"{tf}min", label="right", closed="left").last().dropna()
        mis = [t for t in tfc.index if (t.minute % tf if tf < 60 else t.minute) != 0]
        ok = len(mis) == 0
        fails += not ok
        print(f"G8 {tf:>2}m boundary alignment: {'PASS' if ok else f'FAIL {mis[:3]}'}")

    # G2-lite — DST transitions: no duplicate or missing minute stamps
    for day in ("2025-11-02", "2026-03-08"):
        seg = day_frame(bars, day)
        dup = seg.index.duplicated().sum()
        ok = dup == 0 and seg.index.is_monotonic_increasing
        fails += not ok
        print(f"G2 {day} (DST): {len(seg):,} rows, dup={dup} -> {'PASS' if ok else 'FAIL'}")

    # G1 — lookahead: perturb all bars strictly after t; levels at t identical
    rng = np.random.default_rng(7)
    for day in GATE_DAYS:
        seg = day_frame(bars, day)
        if seg.empty:
            print(f"G1 {day}: no bars — SKIP")
            continue
        probe = seg.index[int(len(seg) * 0.6)]
        pert = seg.copy()
        after = pert.index > probe
        pert.loc[after, ["open", "high", "low", "close"]] *= 1.37
        pert.loc[after, "volume"] = pert.loc[after, "volume"] * 3 + 17
        ok_all = True
        for tf in TFS:
            a_ma, a_w = bb_ma_asof(seg, tf)
            b_ma, b_w = bb_ma_asof(pert, tf)
            same = (np.isclose(a_ma.loc[:probe], b_ma.loc[:probe], equal_nan=True).all()
                    and np.isclose(a_w.loc[:probe], b_w.loc[:probe], equal_nan=True).all())
            ok_all &= bool(same)
        va, vb = vwap_bands(seg), vwap_bands(pert)
        ok_all &= bool(np.isclose(va.loc[:probe].to_numpy(),
                                  vb.loc[:probe].to_numpy(), equal_nan=True).all())
        fails += not ok_all
        print(f"G1 {day} perturb-after-{probe:%H:%M}: {'PASS' if ok_all else 'FAIL'}")

    # G7 — as-of profile: snapshot at t unchanged by existence of later bars
    for day in ("2026-04-27", "2025-11-03"):
        seg = day_frame(bars, day)
        mins = [seg.index[int(len(seg) * f)] for f in (0.3, 0.6, 0.9)]
        full = profile_at_minutes(seg, mins)
        ok_all = True
        for m in mins:
            trunc = profile_at_minutes(seg[seg.index < m], [m])
            ok_all &= bool(np.isclose(full.loc[m].to_numpy(),
                                      trunc.loc[m].to_numpy(), equal_nan=True).all())
        fails += not ok_all
        print(f"G7 {day} profile as-of ({len(mins)} probes): {'PASS' if ok_all else 'FAIL'}")

    # G4 — determinism: two full recomputes byte-identical
    seg = day_frame(bars, "2026-04-27")
    a1, w1 = bb_ma_asof(seg, 15)
    a2, w2 = bb_ma_asof(seg, 15)
    p1 = profile_at_minutes(seg, [seg.index[500], seg.index[900]])
    p2 = profile_at_minutes(seg, [seg.index[900], seg.index[500]])   # order-independence too
    ok = a1.equals(a2) and w1.equals(w2) and np.allclose(
        p1.sort_index().to_numpy(), p2.sort_index().to_numpy(), equal_nan=True)
    fails += not ok
    print(f"G4 determinism + request-order independence: {'PASS' if ok else 'FAIL'}")

    print(f"\n{'ALL LEVEL-ENGINE GATES PASS' if fails == 0 else f'{fails} GATE(S) FAILED — census may not run'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
