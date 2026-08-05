#!/usr/bin/env python3
"""NYA-IB50-01 trial 1 — census per docs/PREREG-ib50-continuation.md.
MrZincx IB50 continuation as taught: 60-min IB (09:30-10:30), direction =
toward the second-formed extreme, entry at first IB-mid touch from 10:23
(front-run entries use DEVELOPING levels — lookahead-clean per §5.11-7;
levels freeze at entry), stop = first-formed extreme, target = predicted
extreme, no trade after 11:30, flat 15:55. BE-off (house null default) and
BE-on (+0.35R, trail 0.3R behind peak after +0.5R — the taught R-shape)
both reported.

    python -m scripts.nya_ib50_census
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FR = 1.0


def rep(T, label):
    if not len(T):
        print(f"  {label}: n=0"); return
    net = T.pts - FR
    r_ = net / T.risk
    gw, gl = net[net > 0].sum(), -net[net <= 0].sum()
    print(f"  {label}: n={len(T)} WR {(net>0).mean():.0%} {net.sum():+.0f}pts "
          f"${160*r_.sum():+,.0f} PF {gw/max(gl,1e-9):.2f}")
    for y, g in T.groupby("year"):
        gn = g.pts - FR
        yw, yl = gn[gn > 0].sum(), -gn[gn <= 0].sum()
        print(f"     {y}: n={len(g)} WR {(gn>0).mean():.0%} {gn.sum():+.0f}pts "
              f"PF {yw/max(yl,1e-9):.2f}")


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert("America/New_York")
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]

    out = {"noBE": [], "BE": []}
    ties = skipped_break = 0
    for d, r in R.groupby("gday"):
        r = r.sort_values("ts").reset_index(drop=True)
        if len(r) < 200:
            continue
        ib_mask = r.clock < "10:30"
        ib = r[ib_mask]
        if len(ib) < 50:
            continue
        H, L, C = r.high.to_numpy(), r.low.to_numpy(), r.close.to_numpy()
        cummax = np.maximum.accumulate(H)
        cummin = np.minimum.accumulate(L)
        n_ib = len(ib)
        ibh_f, ibl_f = ib.high.max(), ib.low.min()
        t_hi = ib.index[ib.high >= ibh_f][0]
        t_lo = ib.index[ib.low <= ibl_f][0]
        if t_hi == t_lo:
            ties += 1
            continue
        # entry scan: 10:23 -> 11:30, price must be INSIDE the (developing) IB
        entry = None
        for k in range(len(r)):
            ck = r.clock.iloc[k]
            if ck < "10:23":
                continue
            if ck >= "11:30":
                break
            if ck < "10:30":
                ibh, ibl = cummax[k - 1] if k else H[0], cummin[k - 1] if k else L[0]
                th = np.argmax(H[:k] >= ibh) if k else 0
                tl = np.argmax(L[:k] <= ibl) if k else 0
            else:
                ibh, ibl, th, tl = ibh_f, ibl_f, t_hi, t_lo
            if th == tl:
                continue
            side = -1 if th < tl else 1   # high first -> low predicted to break -> short
            mid = (ibh + ibl) / 2
            # day-death: price breaks an extreme before mid touch -> no trade
            if C[k] > ibh or C[k] < ibl:
                skipped_break += 1
                break
            if L[k] <= mid <= H[k]:
                stop = ibh if side < 0 else ibl        # first-formed extreme
                tgt = ibl if side < 0 else ibh         # predicted-break extreme
                entry = (k, side, mid, stop, tgt)
                break
        if entry is None:
            continue
        k0, side, e, stop0, tgt = entry
        risk = abs(e - stop0)
        if risk <= 0:
            continue
        for arm, use_be in (("noBE", False), ("BE", True)):
            stop, peak = stop0, 0.0
            pts = None
            for j in range(k0 + 1, len(r)):
                hi, lo = H[j], L[j]
                fav = (e - lo) if side < 0 else (hi - e)
                peak = max(peak, fav)
                if use_be:
                    if peak >= 0.5 * risk:
                        cand = (e - (peak - 0.3 * risk)) if side < 0 else (e + peak - 0.3 * risk)
                        if side < 0: stop = min(stop, cand)
                        else: stop = max(stop, cand)
                    elif peak >= 0.35 * risk:
                        if side < 0: stop = min(stop, e)
                        else: stop = max(stop, e)
                if (side < 0 and hi >= stop) or (side > 0 and lo <= stop):
                    pts = side * (stop - e); break
                if (side < 0 and lo <= tgt) or (side > 0 and hi >= tgt):
                    pts = side * (tgt - e); break
            if pts is None:
                pts = side * (C[-1] - e)
            out[arm].append(dict(day=d, year=d[:4], pts=pts, risk=risk,
                                  side=side, clock=r.clock.iloc[k0]))

    print(f"ties {ties} | day-death skips {skipped_break}")
    for arm, lbl in (("noBE", "DEFAULT (no BE — house null)"),
                     ("BE", "AS-TAUGHT BE+trail (+0.35R BE, 0.3R trail after +0.5R)")):
        T = pd.DataFrame(out[arm])
        if len(T):
            T.to_parquet(ROOT / f"output/nya_ib50_census_{arm}.parquet", index=False)
        rep(T, lbl)


if __name__ == "__main__":
    main()
