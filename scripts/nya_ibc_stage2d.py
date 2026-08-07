#!/usr/bin/env python3
"""NYA-IBC-01 stage 2d — leg-A structural target arms (declared in the
family file). One minute-walk per trade per arm; developing targets (VWAP,
bands) are chased at each minute's value; static targets frozen at entry.
Sub-0.5R structural levels substitute IB mid (counted).

    python -m scripts.nya_ibc_stage2d
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.nya_ivb_desk_run import build_trades

NY = "America/New_York"
FR = 1.0
FIT0, FIT1 = "2025-06-01", "2026-07-31"
ARMS = ("T0_mid", "T1_far_extreme", "T2_vwap", "T3_sigma_band",
        "T4_session_extreme", "T5_pd_close", "T6_trail")


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert(NY)
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]
    rth_close = B[B.clock == "15:59"].groupby("gday").close.last()
    all_days = sorted(set(B.gday))
    pd_close = {all_days[i]: float(rth_close.get(all_days[i - 1], np.nan))
                for i in range(1, len(all_days))}

    trades = [t for t in build_trades() if FIT0 <= t["day"] <= FIT1]
    days = {d: r.sort_values("ts").reset_index(drop=True) for d, r in R.groupby("gday")
            if FIT0 <= d <= FIT1}

    rows, subs = [], {a: 0 for a in ARMS}
    for t in trades:
        d = t["day"]
        r = days.get(d)
        if r is None:
            continue
        k0 = int((r.ts == t["fill"]).idxmax()) if (r.ts == t["fill"]).any() else None
        if k0 is None:
            continue
        side, e, stop, mid = t["side"], t["entry"], t["stop"], t["target"]
        risk = t["risk"]
        H, L_, C, V = r.high.to_numpy(), r.low.to_numpy(), r.close.to_numpy(), \
            r.volume.clip(lower=0).to_numpy().astype(float)
        tp = (H + L_ + C) / 3
        cv = np.maximum(V.cumsum(), 1)
        vwap = (tp * V).cumsum() / cv
        var = np.clip((tp ** 2 * V).cumsum() / cv - vwap ** 2, 0, None)
        sd = np.sqrt(var)
        # static targets at entry
        ibh30, ibl30 = (stop - (-1) * 0 , 0)  # placeholder (not used)
        far_extreme = (e - side * 0) if False else None
        # far IB extreme: entry is at one extreme; far = other side = mid*2 - e
        far = 2 * mid - e
        sess_ext = float(L_[:k0].min()) if side < 0 else float(H[:k0].max())
        pdc = pd_close.get(d, np.nan)

        rec = dict(day=d, year=d[:4])
        for arm in ARMS:
            tgt_static, developing, trail_mode = None, None, False
            if arm == "T0_mid":
                tgt_static = mid
            elif arm == "T1_far_extreme":
                tgt_static = far
            elif arm == "T2_vwap":
                developing = "vwap"
            elif arm == "T3_sigma_band":
                developing = "band"
            elif arm == "T4_session_extreme":
                tgt_static = sess_ext
            elif arm == "T5_pd_close":
                tgt_static = pdc
            elif arm == "T6_trail":
                trail_mode = True
            # substitution rule for static structural targets
            if tgt_static is not None and arm not in ("T0_mid",):
                if not (tgt_static == tgt_static) or side * (tgt_static - e) < 0.5 * risk:
                    tgt_static = mid
                    subs[arm] += 1
            cur_stop, peak, pnl = stop, 0.0, None
            mfe = 0.0
            for j in range(k0 + 1, len(r)):
                hi, lo, cl = H[j], L_[j], C[j]
                fav = (e - lo) if side < 0 else (hi - e)
                peak = max(peak, fav)
                mfe = max(mfe, fav)
                if trail_mode and peak >= 1.0 * risk:
                    cand = e + side * (peak - 0.75 * risk)
                    if side * (cand - cur_stop) > 0:
                        cur_stop = cand
                if (side < 0 and hi >= cur_stop) or (side > 0 and lo <= cur_stop):
                    pnl = side * (cur_stop - e); break
                if developing == "vwap":
                    tgt_now = vwap[j]
                elif developing == "band":
                    tgt_now = vwap[j] - side * sd[j]
                else:
                    tgt_now = tgt_static
                if not trail_mode and tgt_now == tgt_now and side * (tgt_now - e) >= 0.25 * risk:
                    if (side < 0 and lo <= tgt_now) or (side > 0 and hi >= tgt_now):
                        pnl = side * (tgt_now - e); break
            if pnl is None:
                pnl = side * (C[-1] - e)
            rec[arm] = (pnl - FR) / risk
            rec[f"{arm}_mfe"] = mfe / risk
        rows.append(rec)

    T = pd.DataFrame(rows)
    T.to_parquet(ROOT / "output/nya_ibc_stage2d.parquet", index=False)
    print(f"LEG-A TARGET ARMS (fit span, n={len(T)}):")
    print(f"{'arm':20s} {'WR':>5s} {'sumR':>7s} {'$':>9s} {'capt':>5s} {'sub':>4s}  25/26")
    for arm in ARMS:
        g = T[arm]
        wins = g[g > 0]
        capt = (wins / T.loc[wins.index, f"{arm}_mfe"].clip(lower=0.01)).mean() if len(wins) else 0
        yr = {y: round(x.sum(), 1) for y, x in g.groupby(T.year)}
        print(f"{arm:20s} {(g>0).mean():5.0%} {g.sum():+7.1f} ${160*g.sum():+8,.0f} "
              f"{capt:5.2f} {subs[arm]:4d}  {yr.get('2025',0):+.1f}/{yr.get('2026',0):+.1f}")


if __name__ == "__main__":
    main()
