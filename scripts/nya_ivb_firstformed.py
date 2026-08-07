#!/usr/bin/env python3
"""NYA-IVB-01 trial 13 — first-formed-extreme conditioning split
(docs/PREREG-ivb-firstformed.md). Source: MrZincx/Edgeful "IB by rejection"
(first-formed IB extreme holds ~73% of days). Hypothesis: our fade of the
FIRST-formed extreme is the aligned half; fading the second-formed extreme
fights the break stat.

Geometry is the default spec, byte-for-byte the era-script sim (30-min IB
09:30-10:00, touch window 10:00-10:30, close-break veto, stop 0.25xIB,
target mid, EOD close, FR=1.0, $160-risk). First-formed = extreme whose
final IB value printed at the earlier minute; same-minute tie excluded.

    python -m scripts.nya_ivb_firstformed
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validation.permnull import perm_pvalue

FR = 1.0


def sim_exit(r, i0, side, entry, stop, mid):
    pts = None
    for hi, lo, _cl in r.loc[i0 + 1:][["high", "low", "close"]].to_numpy():
        if side < 0:
            if hi >= stop: pts = entry - stop; break
            if lo <= mid: pts = entry - mid; break
        else:
            if lo <= stop: pts = stop - entry; break
            if hi >= mid: pts = mid - entry; break
    if pts is None:
        cl = r.close.iloc[-1]
        pts = (entry - cl) if side < 0 else (cl - entry)
    return pts


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert("America/New_York")
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]

    default_rows, raw_rows = [], []
    ties = 0
    for d, r in R.groupby("gday"):
        r = r.sort_values("ts").reset_index(drop=True)
        ib = r[r.clock < "10:00"]
        if len(ib) < 25 or len(r) < 200:
            continue
        ibh, ibl = ib.high.max(), ib.low.min()
        rng = ibh - ibl
        if rng <= 0:
            continue
        t_hi = ib.index[ib.high >= ibh][0]
        t_lo = ib.index[ib.low <= ibl][0]
        if t_hi == t_lo:
            ties += 1
            continue
        first = "H" if t_hi < t_lo else "L"
        mid = (ibh + ibl) / 2
        win = r[(r.clock >= "10:00") & (r.clock < "10:30")]

        touch_default = touch_raw = None
        for i, row in win.iterrows():
            if touch_raw is None:
                if row.high >= ibh: touch_raw = (-1, i)
                elif row.low <= ibl: touch_raw = (1, i)
            if touch_default is None:
                if row.close > ibh or row.close < ibl:
                    touch_default = False
                elif row.high >= ibh: touch_default = (-1, i)
                elif row.low <= ibl: touch_default = (1, i)
            if touch_raw is not None and touch_default is not None:
                break

        for touch, rows in ((touch_default, default_rows), (touch_raw, raw_rows)):
            if not touch:
                continue
            side, i0 = touch
            entry = ibh if side < 0 else ibl
            stop = entry - side * 0.25 * rng
            pts = sim_exit(r, i0, side, entry, stop, mid)
            faded = "H" if side < 0 else "L"
            rows.append(dict(day=d, year=d[:4], pts=pts, risk=abs(entry - stop),
                             faded_first=int(faded == first)))

    print(f"ties excluded: {ties}")
    for name, rows in (("DEFAULT (tradeable)", default_rows), ("RAW TOUCHES", raw_rows)):
        T = pd.DataFrame(rows)
        T["net"] = T.pts - FR
        T["r"] = T.net / T.risk
        print(f"\n=== {name}: n={len(T)} ===")
        for lbl, g in [("FADE-FIRST-FORMED", T[T.faded_first == 1]),
                       ("FADE-SECOND-FORMED", T[T.faded_first == 0])]:
            gw, gl = g.net[g.net > 0].sum(), -g.net[g.net <= 0].sum()
            print(f"{lbl}: n={len(g)} WR {(g.net>0).mean():.0%} {g.net.sum():+.0f}pts "
                  f"${160*g.r.sum():+,.0f} PF {gw/max(gl,1e-9):.2f}")
            for y, gy in g.groupby("year"):
                yw, yl = gy.net[gy.net > 0].sum(), -gy.net[gy.net <= 0].sum()
                print(f"   {y}: n={len(gy)} WR {(gy.net>0).mean():.0%} "
                      f"{gy.net.sum():+.0f}pts ${160*gy.r.sum():+,.0f} "
                      f"PF {yw/max(yl,1e-9):.2f}")
        if name.startswith("DEFAULT"):
            T.to_parquet(ROOT / "output/nya_ivb_firstformed.parquet", index=False)
            res = perm_pvalue(T.r.to_numpy(), T.faded_first.to_numpy().astype(bool),
                              T.year.to_numpy(), n=10_000, seed=7)
            print(f"\nPERMNULL (within-year shuffle): observed lift "
                  f"{res['observed_lift']:+.3f}R  p={res['p_value']:.3f}  "
                  f"null p95 {res['null_p95']:+.3f}")
            a, b = T.r[T.faded_first == 1], T.r[T.faded_first == 0]
            tt = (a.mean() - b.mean()) / np.sqrt(a.var(ddof=1)/len(a) + b.var(ddof=1)/len(b))
            print(f"Welch t={tt:.2f}, effect t/sqrt(n)={tt/np.sqrt(len(T)):.4f}")


if __name__ == "__main__":
    main()
