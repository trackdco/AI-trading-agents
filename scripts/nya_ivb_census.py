#!/usr/bin/env python3
"""NYA-IVB-01 — L0 census per docs/PREREG-fab-ivb.md. No P&L, no arms: base
rates only. Trial 1 of the family ledger (research/candidates/nya-ivb.md).

Definitions (frozen by the prereg):
  IB          09:30-10:00 high/low from 1-min bars.
  Break event first 1-min CLOSE beyond IB high (long) or IB low (short) at
              or after 10:00, RTH only.
  Race test   from the break close: target = entry +/- 1 x IB range, stop =
              the mirror; conservative intrabar tie-break (stop first);
              unresolved by 16:00 -> day-close sign vs entry decides a
              half-credit metric reported separately (census transparency).
  Close test  P(16:00 close is beyond entry in break direction by ANY amount)
              and by >= 1 x IB range — the literal reading of the +13.5%
              at-1:1 claim.
  MFE ladder  post-break favorable excursion quantiles in IB-range units —
              the "protection level" derivation.

    python -m scripts.nya_ivb_census
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

    A = pd.read_parquet(ROOT / "output/amt_days.parquet").set_index("day")

    rows = []
    for d, r in R.groupby("gday"):
        r = r.sort_values("ts")
        if len(r) < 200:
            continue
        ib = r[r.clock < "10:00"]
        post = r[r.clock >= "10:00"]
        if len(ib) < 25 or len(post) < 100:
            continue
        ibh, ibl = ib.high.max(), ib.low.min()
        rng = ibh - ibl
        if rng <= 0:
            continue
        up = post[post.close > ibh]
        dn = post[post.close < ibl]
        t_up = up.ts.iloc[0] if len(up) else pd.NaT
        t_dn = dn.ts.iloc[0] if len(dn) else pd.NaT
        if pd.isna(t_up) and pd.isna(t_dn):
            side, entry, tbrk = 0, np.nan, pd.NaT
        elif pd.isna(t_dn) or (not pd.isna(t_up) and t_up < t_dn):
            side, entry, tbrk = 1, up.close.iloc[0], t_up
        else:
            side, entry, tbrk = -1, dn.close.iloc[0], t_dn
        rec = dict(day=d, year=d[:4], ib_rng=rng, side=side,
                   ib_atr=rng / A.loc[d, "vwap_sigma"] if d in A.index and A.loc[d, "vwap_sigma"] > 0 else np.nan,
                   open_type=A.loc[d, "open_type"] if d in A.index else None,
                   day_type=A.loc[d, "day_type"] if d in A.index else None)
        if side != 0:
            after = post[post.ts >= tbrk]
            tgt = entry + side * rng
            stp = entry - side * rng
            hit = 0
            for hi, lo, cl in after[["high", "low", "close"]].to_numpy():
                if (side > 0 and lo <= stp) or (side < 0 and hi >= stp):
                    hit = -1; break
                if (side > 0 and hi >= tgt) or (side < 0 and lo <= tgt):
                    hit = 1; break
            close = after.close.iloc[-1]
            mfe = (after.high.max() - entry) if side > 0 else (entry - after.low.min())
            rec.update(race=hit,
                       close_beyond=int(np.sign(close - entry) == side),
                       close_beyond_1r=int(side * (close - entry) >= rng),
                       mfe_r=mfe / rng,
                       brk_clock=tbrk.strftime("%H:%M"))
        rows.append(rec)

    C = pd.DataFrame(rows)
    C.to_parquet(ROOT / "output/nya_ivb_census.parquet", index=False)
    brk = C[C.side != 0]
    print(f"sessions {len(C)} | with a break {len(brk)} ({len(brk)/len(C):.0%}) | "
          f"long {int((brk.side>0).sum())} short {int((brk.side<0).sum())}")
    for era, g in brk.groupby(brk.year.map(lambda y: "23-24" if y in ("2023", "2024") else y)):
        res = g[g.race != 0]
        print(f"  {era}: n={len(g)} | race@1:1 win {(res.race>0).mean():.1%} (resolved {len(res)}) | "
              f"close-beyond {g.close_beyond.mean():.1%} | close>=1R {g.close_beyond_1r.mean():.1%} | "
              f"median MFE {g.mfe_r.median():.2f}R")
    for s, lbl in [(1, "LONG"), (-1, "SHORT")]:
        g = brk[brk.side == s]; res = g[g.race != 0]
        print(f"  {lbl}: n={len(g)} race win {(res.race>0).mean():.1%} | close-beyond {g.close_beyond.mean():.1%}")
    print("MFE quantiles (R):", {q: round(float(brk.mfe_r.quantile(q)), 2) for q in (.3, .5, .65, .7, .8)})
    print("break clock:", brk.brk_clock.value_counts().head(5).to_dict())
    ibq = pd.qcut(brk.ib_rng, 3, labels=["narrow", "mid", "wide"])
    for b, g in brk.groupby(ibq, observed=True):
        res = g[g.race != 0]
        print(f"  IB {b}: n={len(g)} race win {(res.race>0).mean():.1%} close-beyond {g.close_beyond.mean():.1%}")


if __name__ == "__main__":
    main()
