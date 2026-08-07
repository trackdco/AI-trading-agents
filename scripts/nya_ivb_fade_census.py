#!/usr/bin/env python3
"""NYA-IVB-01 trial 2 — branch B (pre-break range fade) L0 census, per
docs/PREREG-fab-ivb.md. Branch A died at trial 1; branch B rides a different
premise: while the completed IB is unbroken, its extremes mean-revert.

Event: first TOUCH of the IB high or low in 10:00-10:30, while no 1-min close
beyond either extreme has yet occurred. Race from the touch price: IB midpoint
(revert) vs a 1-min close beyond the touched extreme (break = loss for the
premise). Conservative: break checked first per bar. Census also previews the
fade's raw economics at the promotion-rule default geometry (stop 0.25 x IB
beyond the extreme, target mid) WITHOUT declaring it tested — no arms here.

    python -m scripts.nya_ivb_fade_census
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert("America/New_York")
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]

    rows = []
    for d, r in R.groupby("gday"):
        r = r.sort_values("ts").reset_index(drop=True)
        ib = r[r.clock < "10:00"]
        if len(ib) < 25 or len(r) < 200:
            continue
        ibh, ibl = ib.high.max(), ib.low.min()
        rng = ibh - ibl
        if rng <= 0:
            continue
        mid = (ibh + ibl) / 2
        win = r[(r.clock >= "10:00") & (r.clock < "10:30")]
        touched = None
        for i, row in win.iterrows():
            if row.close > ibh or row.close < ibl:
                break  # IB broke before a clean touch -> no event
            if row.high >= ibh:
                touched = ("short", i); break
            if row.low <= ibl:
                touched = ("long", i); break
        if touched is None:
            continue
        side, i0 = touched
        entry = ibh if side == "short" else ibl
        after = r.loc[i0 + 1:]
        outcome = 0
        for j, row in after.iterrows():
            if side == "short":
                if row.close > ibh: outcome = -1; break
                if row.low <= mid: outcome = 1; break
            else:
                if row.close < ibl: outcome = -1; break
                if row.high >= mid: outcome = 1; break
        era = "23-24" if d[:4] in ("2023", "2024") else d[:4]
        rows.append(dict(day=d, era=era, side=side, rng=rng, outcome=outcome))
    T = pd.DataFrame(rows)
    T.to_parquet(ROOT / "output/nya_ivb_fade_census.parquet", index=False)
    print(f"fade events: {len(T)} | long {int((T.side=='long').sum())} short {int((T.side=='short').sum())}")
    for era, g in T.groupby("era"):
        res = g[g.outcome != 0]
        print(f"  {era}: n={len(g)} | revert-to-mid first {(res.outcome>0).mean():.0%} "
              f"(resolved {len(res)})")
    for s, g in T.groupby("side"):
        res = g[g.outcome != 0]
        print(f"  {s}: n={len(g)} revert {(res.outcome>0).mean():.0%}")


if __name__ == "__main__":
    main()
