#!/usr/bin/env python3
"""Winners vs losers on the A/B displacement population — every entry variable
measured AT the candle close (causally clean), FIT ONLY.

Winner = never stopped, positive at 15:55 hold (the raw table's definition).
For each variable: on/off winner rate and R/trade per era. Flow/volume from
fp_minutes (signal bar's own minutes — complete at the close); depth from the
T-1 archive row (honest); bp5opp via the versioned builder at signal start.

    python -m scripts.l3_ab_winner_loser
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.audit_displacement_entry import TFMIN, NY   # noqa: E402
from scripts.build_l2_outcomes import load_bars          # noqa: E402
from scripts.honest_disp_depth import build              # noqa: E402
from src.canon.features import bp5opp                    # noqa: E402


def main() -> None:
    A = build()
    L2 = pd.read_parquet(ROOT / "output/l2_outcomes_fit.parquet",
                         columns=["ts", "tf", "direction", "pattern"])
    A = A.merge(L2.drop_duplicates(["ts", "tf", "direction"]),
                on=["ts", "tf", "direction"], how="left")
    D = A[(A.kind == "displacement") & (A.risk >= 2.0)].copy()
    D["T"] = pd.to_datetime(D["T"], utc=True).dt.tz_convert(NY)
    D["tfm"] = D.tf.map(TFMIN)
    D["sgn"] = np.where(D.direction == "long", 1, -1)
    D["win"] = D.r_hold > 0

    fp = pd.read_parquet(ROOT / "output/fp_minutes.parquet").sort_index()
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()

    flow, volx, closeloc, rangex, bp5 = ([] for _ in range(5))
    res_cache: dict = {}
    for r in D.itertuples():
        t1, t0 = r.T, r.T - pd.Timedelta(minutes=int(r.tfm))
        seg = fp.loc[t0:t1 - pd.Timedelta(minutes=1)]
        if len(seg):
            ds, vs = float(seg.delta.sum()), float(seg.vol.sum())
            flow.append(1.0 if ds * r.sgn > 0 else 0.0)
        else:
            ds, vs = np.nan, np.nan
            flow.append(np.nan)
        day = r.day
        key = (day, int(r.tfm))
        if key not in res_cache:
            db = bars.loc[day]
            try:
                fpd = fp.loc[day]
            except KeyError:
                fpd = None
            rr = (db.high.resample(f"{int(r.tfm)}min", label="right", closed="left").max()
                  - db.low.resample(f"{int(r.tfm)}min", label="right", closed="left").min())
            vv = (fpd.vol.resample(f"{int(r.tfm)}min", label="right", closed="left").sum()
                  if fpd is not None else None)
            res_cache[key] = (rr, rr.shift(1).rolling(20).mean(),
                              vv, vv.shift(1).rolling(20).median() if vv is not None else None)
        rr, atr, vv, vmed = res_cache[key]
        rangex.append(float(rr.get(t1, np.nan) / atr.get(t1, np.nan))
                      if atr is not None and atr.get(t1, np.nan) == atr.get(t1, np.nan)
                      and atr.get(t1, 0) > 0 else np.nan)
        volx.append(float(vs / vmed.get(t1, np.nan))
                    if vmed is not None and vs == vs and vmed.get(t1, np.nan) == vmed.get(t1, np.nan)
                    and vmed.get(t1, 0) > 0 else np.nan)
        try:
            b = bars.loc[t0:t1 - pd.Timedelta(minutes=1)]
            hi, lo, cl = b.high.max(), b.low.min(), b.close.iloc[-1]
            loc = (cl - lo) / (hi - lo) if hi > lo else np.nan
            closeloc.append(loc if r.sgn > 0 else 1 - loc)
        except Exception:
            closeloc.append(np.nan)
        bp5.append(bp5opp(fp, r.direction, t0))
    D["FLOW"], D["VOLX"], D["CLOSELOC"], D["RANGEX"], D["BP5"] = flow, volx, closeloc, rangex, bp5
    for c in ("W", "D", "WALLSZ"):
        D[c] = D[c].where(D.dep_thick.notna())

    checks = [
        ("flow agrees (signal-bar delta)", D.FLOW == 1),
        ("volume >= 1.5x normal", D.VOLX >= 1.5),
        ("closes in top 25% of bar", D.CLOSELOC >= 0.75),
        ("bar >= 1x ATR", D.RANGEX >= 1.0),
        ("absorption before (bp5opp)", D.BP5 == 1),
        ("W: no wall behind", D.W == 1),
        ("D: level visible ahead", D["D"] == 1),
        ("WALLSZ: big wall ahead (>=7)", D.WALLSZ == 1),
        ("risk >= 7pt candle", D.risk >= 7),
        ("risk >= 15pt candle", D.risk >= 15),
    ]
    print(f"population: {len(D):,} A/B trades | winner = unstopped, positive at close\n")
    print(f"{'variable':<32}{'era':<6}{'n on':>6}{'WR on':>7}{'R on':>8}{'n off':>7}"
          f"{'WR off':>8}{'R off':>8}{'edge':>8}")
    for name, cond in checks:
        valid = cond.notna() if hasattr(cond, "notna") else pd.Series(True, index=D.index)
        for era in ("2025", "2026"):
            d = D[(D.era == era) & valid]
            on, off = d[cond.loc[d.index].fillna(False)], d[~cond.loc[d.index].fillna(False)]
            if len(on) < 15 or len(off) < 15:
                continue
            print(f"{name:<32}{era:<6}{len(on):>6,}{on.win.mean()*100:>6.1f}%"
                  f"{on.r_hold.mean():>+8.3f}{len(off):>7,}{off.win.mean()*100:>7.1f}%"
                  f"{off.r_hold.mean():>+8.3f}{on.r_hold.mean()-off.r_hold.mean():>+8.3f}")
    D.to_parquet(ROOT / "output/l3_ab_winner_loser.parquet", index=False)
    print("\nrow-level -> output/l3_ab_winner_loser.parquet  (fit only, holdout untouched)")


if __name__ == "__main__":
    main()
