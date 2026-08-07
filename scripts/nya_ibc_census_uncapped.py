#!/usr/bin/env python3
"""NYA-IBC-01 stage 1b — UNCAPPED raw census (ANGUS: "i prefer getting raw
data off of no trade cap... itll look uglier but there will be more to
decipher"). Every trigger, sequential non-overlapping re-entries, fit span.

Leg A: every touch of an intact 30-min-IB extreme in 10:00-10:30 while no
1-min close sits outside the IB; after a trade resolves, the scan resumes.
Leg B: every mid touch 10:23-11:30 while inside the 60-min IB; note the
structural fact — leg B's resolution (either extreme hit) IS the day-death
event, so re-entries can only follow EOD-less mid-oscillation, and the
uncapped expansion is expected small. Base 1pt friction, $160-risk.

    python -m scripts.nya_ibc_census_uncapped
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NY = "America/New_York"
FR = 1.0
FIT0, FIT1 = "2025-06-01", "2026-07-31"


def pack(df, label):
    if not len(df):
        print(f"  {label}: n=0"); return
    r = df.net_r
    gw, gl = r[r > 0].sum(), -r[r <= 0].sum()
    print(f"  {label}: n={len(df)} | WR {(r>0).mean():.1%} | {r.sum():+.1f}R "
          f"${160*r.sum():+,.0f} | PF(R) {gw/max(gl,1e-9):.2f} | mean {r.mean():+.3f}R")


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert(NY)
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]

    legA, legB = [], []
    for d, r in R.groupby("gday"):
        if not (FIT0 <= d <= FIT1):
            continue
        r = r.sort_values("ts").reset_index(drop=True)
        if len(r) < 200:
            continue
        H, L_, C = r.high.to_numpy(), r.low.to_numpy(), r.close.to_numpy()

        # ---------------- LEG A uncapped (30-min IB) ----------------
        ib = r[r.clock < "10:00"]
        if len(ib) >= 25:
            ibh, ibl = ib.high.max(), ib.low.min()
            rng = ibh - ibl
            if rng > 0:
                mid = (ibh + ibl) / 2
                k = r.index[r.clock >= "10:00"][0] if (r.clock >= "10:00").any() else None
                win_end = "10:30"
                seq = 0
                while k is not None and k < len(r) and r.clock.iloc[k] < win_end:
                    if C[k] > ibh or C[k] < ibl:
                        break
                    side = -1 if H[k] >= ibh else (1 if L_[k] <= ibl else 0)
                    if not side:
                        k += 1
                        continue
                    e = ibh if side < 0 else ibl
                    stop = e - side * 0.25 * rng
                    risk = abs(e - stop)
                    pts, jx = None, len(r) - 1
                    for j in range(k + 1, len(r)):
                        if (side < 0 and H[j] >= stop) or (side > 0 and L_[j] <= stop):
                            pts, jx = -risk, j; break
                        if (side < 0 and L_[j] <= mid) or (side > 0 and H[j] >= mid):
                            pts, jx = abs(mid - e), j; break
                    if pts is None:
                        pts = side * (C[-1] - e)
                    seq += 1
                    legA.append(dict(day=d, year=d[:4], seq=seq,
                                     net_r=(pts - FR) / risk))
                    k = jx + 1  # resume scan after resolution

        # ---------------- LEG B uncapped (60-min IB) ----------------
        ib6 = r[r.clock < "10:30"]
        if len(ib6) < 50:
            continue
        cummax, cummin = np.maximum.accumulate(H), np.minimum.accumulate(L_)
        ibh_f, ibl_f = ib6.high.max(), ib6.low.min()
        t_hi = ib6.index[ib6.high >= ibh_f][0]; t_lo = ib6.index[ib6.low <= ibl_f][0]
        if t_hi == t_lo:
            continue
        k = 0
        seq = 0
        while k < len(r):
            ck = r.clock.iloc[k]
            if ck < "10:23":
                k += 1; continue
            if ck >= "11:30":
                break
            if ck < "10:30":
                ibh, ibl = cummax[k - 1], cummin[k - 1]
                th = np.argmax(H[:k] >= ibh); tl = np.argmax(L_[:k] <= ibl)
            else:
                ibh, ibl, th, tl = ibh_f, ibl_f, t_hi, t_lo
            if th == tl or C[k] > ibh or C[k] < ibl:
                break
            side = -1 if th < tl else 1
            mid = (ibh + ibl) / 2
            if not (L_[k] <= mid <= H[k]):
                k += 1; continue
            e = mid
            stop = ibh if side < 0 else ibl
            tgt = ibl if side < 0 else ibh
            risk = abs(e - stop)
            pts, jx = None, len(r) - 1
            for j in range(k + 1, len(r)):
                if (side < 0 and H[j] >= stop) or (side > 0 and L_[j] <= stop):
                    pts, jx = -risk, j; break
                if (side < 0 and L_[j] <= tgt) or (side > 0 and H[j] >= tgt):
                    pts, jx = abs(tgt - e), j; break
            if pts is None:
                pts = side * (C[-1] - e)
            seq += 1
            legB.append(dict(day=d, year=d[:4], seq=seq, net_r=(pts - FR) / risk))
            k = jx + 1

    A_, B_ = pd.DataFrame(legA), pd.DataFrame(legB)
    A_.to_parquet(ROOT / "output/nya_ibc_uncapped_A.parquet", index=False)
    B_.to_parquet(ROOT / "output/nya_ibc_uncapped_B.parquet", index=False)

    print("NYA-IBC-01 STAGE 1b — UNCAPPED RAW CENSUS (fit span)")
    print(f"\nLEG A: {len(A_)} events on {A_.day.nunique()} days "
          f"(vs 112 capped; max/day {A_.groupby('day').size().max()})")
    pack(A_, "ALL events")
    for y, g in A_.groupby("year"):
        pack(g, f"  {y}")
    pack(A_[A_.seq == 1], "first-of-day (the old cap)")
    pack(A_[A_.seq >= 2], "re-entries (the uncapped ugly)")

    print(f"\nLEG B: {len(B_)} events on {B_.day.nunique()} days "
          f"(vs 138 capped; max/day {B_.groupby('day').size().max()})")
    pack(B_, "ALL events")
    for y, g in B_.groupby("year"):
        pack(g, f"  {y}")
    pack(B_[B_.seq >= 2], "re-entries")


if __name__ == "__main__":
    main()
