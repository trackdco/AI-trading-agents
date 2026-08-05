#!/usr/bin/env python3
"""NYA-IVB-01 trial 6 — branch B era discipline: the taught geometry on the
FULL candle span (2023-2026). Same event and sim as the trial-4 retest, no
flow gates (candles only — flow gates don't exist before 2025-06). This is
the era rung: the flow-span result (PF 1.63) must not be a regime fluke.

    python -m scripts.nya_ivb_fade_era
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FR = 1.0


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
        touch = None
        for i, row in win.iterrows():
            if row.close > ibh or row.close < ibl:
                break
            if row.high >= ibh:
                touch = (-1, i); break
            if row.low <= ibl:
                touch = (1, i); break
        if touch is None:
            continue
        side, i0 = touch
        entry = ibh if side < 0 else ibl
        stop = entry - side * 0.25 * rng
        pts = None
        for hi, lo, cl in r.loc[i0 + 1:][["high", "low", "close"]].to_numpy():
            if side < 0:
                if hi >= stop: pts = entry - stop; break
                if lo <= mid: pts = entry - mid; break
            else:
                if lo <= stop: pts = stop - entry; break
                if hi >= mid: pts = mid - entry; break
        if pts is None:
            cl = r.close.iloc[-1]
            pts = (entry - cl) if side < 0 else (cl - entry)
        era = "23-24" if d[:4] in ("2023", "2024") else d[:4]
        rows.append(dict(day=d, era=era, half=d[:4] + ("H1" if d[5:7] < "07" else "H2"),
                         pts=pts, risk=abs(entry - stop)))
    T = pd.DataFrame(rows)
    T.to_parquet(ROOT / "output/nya_ivb_fade_era.parquet", index=False)
    for era, g in T.groupby("era"):
        net = g.pts - FR
        r_ = net / g.risk
        gw, gl = net[net > 0].sum(), -net[net <= 0].sum()
        print(f"{era}: n={len(g)} WR {(net>0).mean():.0%} {net.sum():+.0f}pts "
              f"${160*r_.sum():+,.0f} PF {gw/max(gl,1e-9):.2f}")
    net = T.pts - FR
    print(f"ALL: n={len(T)} WR {(net>0).mean():.0%} {net.sum():+.0f}pts "
          f"PF {net[net>0].sum()/max(-net[net<=0].sum(),1e-9):.2f}")


if __name__ == "__main__":
    main()
