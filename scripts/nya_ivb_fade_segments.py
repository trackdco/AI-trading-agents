#!/usr/bin/env python3
"""NYA-IVB-01 trial 11 — the §5.12-5 time-segment schema + in-trade signatures
for the IB fade book (default spec, full span). Canon Part-6 method exactly:
at t+2/3/5/8/10 minutes from entry record open/r/mfe/mae; mine the three
signatures. POPULATION SEMANTICS: signature stats condition on "still open at
t" (the decision-relevant set); stated explicitly per the dissection's
survivorship caveat.

    python -m scripts.nya_ivb_fade_segments
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CHECKS = (2, 3, 5, 8, 10)
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
        ibh, ibl = ib.high.max(), ib.low.min(); rng = ibh - ibl
        if rng <= 0:
            continue
        mid = (ibh + ibl) / 2
        win = r[(r.clock >= "10:00") & (r.clock < "10:30")]
        touch = None
        for i, row in win.iterrows():
            if row.close > ibh or row.close < ibl:
                break
            if row.high >= ibh: touch = (-1, i); break
            if row.low <= ibl: touch = (1, i); break
        if touch is None:
            continue
        side, i0 = touch
        entry = ibh if side < 0 else ibl
        stop = entry - side * 0.25 * rng
        risk = abs(entry - stop)
        rec = dict(day=d, year=d[:4])
        mfe = mae = 0.0
        done, pts = False, None
        for m, (j, row) in enumerate(r.loc[i0 + 1:].iterrows(), start=1):
            fav = (entry - row.low) if side < 0 else (row.high - entry)
            adv = (row.high - entry) if side < 0 else (entry - row.low)
            if not done:
                mfe, mae = max(mfe, fav), max(mae, adv)
                if (side < 0 and row.high >= stop) or (side > 0 and row.low <= stop):
                    pts, done = -risk, True
                elif (side < 0 and row.low <= mid) or (side > 0 and row.high >= mid):
                    pts, done = abs(mid - entry), True
            if m in CHECKS:
                cl_r = ((entry - row.close) if side < 0 else (row.close - entry)) / risk
                rec[f"open{m}"] = int(not done)
                rec[f"r{m}"] = cl_r if not done else np.nan
                rec[f"mf{m}"] = mfe / risk
                rec[f"ma{m}"] = -mae / risk
            if m >= max(CHECKS) and done:
                break
        if pts is None:
            cl = r.close.iloc[-1]
            pts = (entry - cl) if side < 0 else (cl - entry)
        rec["win"] = int(pts - FR > 0)
        rec["net_r"] = (pts - FR) / risk
        rows.append(rec)
    T = pd.DataFrame(rows)
    T.to_parquet(ROOT / "output/nya_ivb_fade_segments.parquet", index=False)
    base = T.win.mean()
    print(f"{len(T)} trades, base WR {base:.1%} | population = still-open-at-t (conditioning set)")
    for t in (3, 5):
        op = T[T[f"open{t}"] == 1]
        press = op[(op[f"mf{t}"] >= 0.5) & (op[f"r{t}"] > 0) & (op[f"mf{t}"] - op[f"r{t}"] <= 0.25)]
        dying = op[op[f"ma{t}"] <= -0.5]
        give = op[(op[f"r{t}"] > 0) & (op[f"mf{t}"] - op[f"r{t}"] > 0.25)]
        print(f"t+{t}: open {len(op)}")
        for lbl, g in [("PRESS", press), ("DYING", dying), ("GIVEBACK", give)]:
            if len(g) >= 10:
                yr = " ".join(f"{y}:{gg.win.mean():.0%}(n={len(gg)})" for y, gg in g.groupby("year") if len(gg) >= 5)
                print(f"  {lbl}: n={len(g)} WR {g.win.mean():.0%} (base {base:.0%}) | {yr}")
            else:
                print(f"  {lbl}: n={len(g)} — thin")


if __name__ == "__main__":
    main()
