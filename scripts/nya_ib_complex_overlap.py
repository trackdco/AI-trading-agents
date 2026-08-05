#!/usr/bin/env python3
"""IB COMPLEX overlap study (ANGUS: are fade + continuation the canon's A/B
of the IB?). Leg A = certified fade (30-min IB, extreme reversal). Leg B =
IB50 continuation (60-min IB, mid -> predicted break). Full span: per-day
co-occurrence, direction relationship, simultaneous-open conflicts,
day-level P&L correlation, and the combined two-leg book.

    python -m scripts.nya_ib_complex_overlap
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.nya_ivb_desk_run import build_trades  # leg A, full detail

NY = "America/New_York"
FR = 1.0


def build_ib50(B, R):
    out = []
    for d, r in R.groupby("gday"):
        r = r.sort_values("ts").reset_index(drop=True)
        if len(r) < 200: continue
        ib = r[r.clock < "10:30"]
        if len(ib) < 50: continue
        H, L_, C = r.high.to_numpy(), r.low.to_numpy(), r.close.to_numpy()
        cummax, cummin = np.maximum.accumulate(H), np.minimum.accumulate(L_)
        ibh_f, ibl_f = ib.high.max(), ib.low.min()
        t_hi = ib.index[ib.high >= ibh_f][0]; t_lo = ib.index[ib.low <= ibl_f][0]
        if t_hi == t_lo: continue
        entry = None
        for k in range(len(r)):
            ck = r.clock.iloc[k]
            if ck < "10:23": continue
            if ck >= "11:30": break
            if ck < "10:30":
                ibh, ibl = cummax[k - 1], cummin[k - 1]
                th = np.argmax(H[:k] >= ibh); tl = np.argmax(L_[:k] <= ibl)
            else:
                ibh, ibl, th, tl = ibh_f, ibl_f, t_hi, t_lo
            if th == tl: continue
            side = -1 if th < tl else 1
            mid = (ibh + ibl) / 2
            if C[k] > ibh or C[k] < ibl: break
            if L_[k] <= mid <= H[k]:
                entry = (k, side, mid, ibh if side < 0 else ibl, ibl if side < 0 else ibh)
                break
        if entry is None: continue
        k0, side, e, stop, tgt = entry
        risk = abs(e - stop)
        if risk <= 0: continue
        pts, jx = None, len(r) - 1
        for j in range(k0 + 1, len(r)):
            if (side < 0 and H[j] >= stop) or (side > 0 and L_[j] <= stop):
                pts, jx = -risk, j; break
            if (side < 0 and L_[j] <= tgt) or (side > 0 and H[j] >= tgt):
                pts, jx = abs(tgt - e), j; break
        if pts is None:
            pts = side * (C[-1] - e)
        out.append(dict(day=d, side=side, fill=r.ts.iloc[k0], exit=r.ts.iloc[jx],
                        net_r=(pts - FR) / risk))
    return out


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert(NY)
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]

    A = {t["day"]: t for t in build_trades()}
    Bt = {t["day"]: t for t in build_ib50(B, R)}
    days = sorted(set(A) | set(Bt))
    both = [d for d in days if d in A and d in Bt]
    print(f"days with any IB trade: {len(days)} | fade-only {len(set(A)-set(Bt))} | "
          f"ib50-only {len(set(Bt)-set(A))} | BOTH {len(both)}")

    same = opp = 0
    opp_open = 0
    rel_rows = []
    for d in both:
        a, b = A[d], Bt[d]
        if a["side"] == b["side"]: same += 1
        else: opp += 1
        # simultaneously open AND opposed?
        a0, a1 = a["fill"], a["mech_exit_ts"]
        b0, b1 = b["fill"], b["exit"]
        overlap = max(0.0, (min(a1, b1) - max(a0, b0)).total_seconds() / 60)
        if overlap > 0 and a["side"] != b["side"]:
            opp_open += 1
        rel_rows.append(dict(day=d, same=int(a["side"] == b["side"]),
                             overlap_min=overlap,
                             a_r=a["mech_R"], b_r=b["net_r"]))
    REL = pd.DataFrame(rel_rows)
    print(f"both-days direction: same {same} / opposed {opp} "
          f"({opp/(same+opp):.0%} opposed) | simultaneously-open-and-opposed days: {opp_open}")
    print(f"median overlap while both open: {REL.overlap_min.median():.0f} min")
    if len(REL) >= 10:
        print(f"both-days trade-R correlation: "
              f"{np.corrcoef(REL.a_r, REL.b_r)[0,1]:+.3f}")
        print(f"  when SAME direction (n={REL.same.sum()}): "
              f"A {REL[REL.same==1].a_r.mean():+.2f}R B {REL[REL.same==1].b_r.mean():+.2f}R")
        print(f"  when OPPOSED (n={(1-REL.same).sum()}): "
              f"A {REL[REL.same==0].a_r.mean():+.2f}R B {REL[REL.same==0].b_r.mean():+.2f}R")

    # day-level series + combined book
    sA = pd.Series({d: A[d]["mech_R"] for d in A})
    sB = pd.Series({d: Bt[d]["net_r"] for d in Bt})
    U = pd.DataFrame({"A": sA, "B": sB}).fillna(0.0)
    print(f"\nday-level union correlation: {U.A.corr(U.B):+.3f}")
    comb = 160 * (U.A + U.B)
    print("combined two-leg book ($160-risk/leg):")
    for y, g in comb.groupby(U.index.str[:4]):
        print(f"  {y}: n_days={int((g!=0).sum())} ${g.sum():+,.0f}")
    print(f"  TOTAL ${comb.sum():+,.0f} | fade alone ${160*U.A.sum():+,.0f} | "
          f"ib50 alone ${160*U.B.sum():+,.0f}")
    seq = comb.cumsum()
    print(f"  combined maxDD ${(seq.cummax()-seq).max():,.0f}")


if __name__ == "__main__":
    main()
