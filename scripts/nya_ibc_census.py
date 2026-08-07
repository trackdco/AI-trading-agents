#!/usr/bin/env python3
"""NYA-IBC-01 stage 1 — raw fit-span trigger census, both legs, no
optimization. Fit span 2025-06 -> 2026-07 (§5.11-9a). Raw as-taught
geometry: leg A = certified fade default; leg B = IB50 as-taught (full
opposite-extreme stop — Angus flagged it oversized; caps are STAGE 2).
Base 1pt friction, $160-risk. §5.11-2 event-universe sensitivity reported
(first-touch default + the all-touches ceiling for leg A).

    python -m scripts.nya_ibc_census
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.nya_ivb_desk_run import build_trades
from scripts.nya_ib_complex_overlap import build_ib50

NY = "America/New_York"
FR = 1.0
FIT0, FIT1 = "2025-06-01", "2026-07-31"


def pack(rs, label):
    r = pd.Series([x for x in rs])
    if not len(r):
        print(f"  {label}: n=0"); return
    wins = (r > 0)
    gw, gl = r[r > 0].sum(), -r[r <= 0].sum()
    print(f"  {label}: n={len(r)} | WR {wins.mean():.1%} | sum {r.sum():+.1f}R "
          f"${160*r.sum():+,.0f} | PF(R) {gw/max(gl,1e-9):.2f} | "
          f"mean {r.mean():+.3f}R | median win {r[r>0].median():+.2f}R / "
          f"loss {r[r<=0].median():+.2f}R")


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert(NY)
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]
    fit_days = sorted(d for d in set(B.gday) if FIT0 <= d <= FIT1)
    n_sessions = len([d for d in fit_days if len(B[B.gday == d]) > 300])

    A = [t for t in build_trades() if FIT0 <= t["day"] <= FIT1]
    Bt = [t for t in build_ib50(B, R) if FIT0 <= t["day"] <= FIT1]

    # leg A all-touches ceiling (§5.11-2): count window touches without the
    # one-per-day / close-break veto
    allA = 0
    for d, r in R.groupby("gday"):
        if not (FIT0 <= d <= FIT1):
            continue
        r = r.sort_values("ts").reset_index(drop=True)
        ib = r[r.clock < "10:00"]
        if len(ib) < 25 or len(r) < 200:
            continue
        ibh, ibl = ib.high.max(), ib.low.min()
        if ibh <= ibl:
            continue
        win = r[(r.clock >= "10:00") & (r.clock < "10:30")]
        allA += int(((win.high >= ibh) | (win.low <= ibl)).sum() > 0) and \
            int((win.high >= ibh).sum() + (win.low <= ibl).sum())

    print(f"NYA-IBC-01 STAGE 1 — RAW FIT-SPAN CENSUS ({FIT0} -> {FIT1}, "
          f"{n_sessions} sessions)")
    print(f"\nLEG A (fade, 30-min IB reversal):")
    print(f"  raw triggers: {len(A)} first-touch tradeable days "
          f"(~{len(A)/n_sessions*5:.1f}/wk) | window touch-minutes {allA} (raw contact volume; "
          f"the tradeable all-touch expansion measured at +34% on the full span, trial 10)")
    pack([t["mech_R"] for t in A], "raw P&L (as-taught default)")
    for y in ("2025", "2026"):
        pack([t["mech_R"] for t in A if t["day"][:4] == y], f"  {y}")

    print(f"\nLEG B (IB50 continuation, 60-min IB):")
    print(f"  raw triggers: {len(Bt)} mid-touch days (~{len(Bt)/n_sessions*5:.1f}/wk); "
          f"day-death skips + no-touch days = {n_sessions - len(Bt)}")
    pack([t["net_r"] for t in Bt], "raw P&L (as-taught, full-extreme stop)")
    for y in ("2025", "2026"):
        pack([t["net_r"] for t in Bt if t["day"][:4] == y], f"  {y}")

    sA = pd.Series({t["day"]: t["mech_R"] for t in A})
    sB = pd.Series({t["day"]: t["net_r"] for t in Bt})
    U = pd.DataFrame({"A": sA, "B": sB}).fillna(0.0)
    both = ((U.A != 0) & (U.B != 0)).sum()
    comb = 160 * (U.A + U.B)
    print(f"\nCOMPLEX (raw, both legs, $160/leg):")
    print(f"  active days: {len(U)} (A-only {(U.A != 0).sum() - both}, "
          f"B-only {(U.B != 0).sum() - both}, both {both}) | day corr "
          f"{U.A.corr(U.B):+.3f}")
    print(f"  combined ${comb.sum():+,.0f} | A ${160*U.A.sum():+,.0f} | "
          f"B ${160*U.B.sum():+,.0f}")
    seq = comb.cumsum()
    print(f"  combined trade-seq maxDD ${(seq.cummax()-seq).max():,.0f}")


if __name__ == "__main__":
    main()
