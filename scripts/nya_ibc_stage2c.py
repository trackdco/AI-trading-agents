#!/usr/bin/env python3
"""NYA-IBC-01 stage 2c — in-trade diagnosis + management levers, both legs,
fit span (declared in the family file 2026-08-05). One minute-walk per
trade records the path; diagnosis and every declared lever arm evaluate on
the shared path. Post-exit walkout measured for winners.

    python -m scripts.nya_ibc_stage2c
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
CHECKS = (3, 5, 10, 15, 30)


def walk(rday, k0, side, e, stop0, tgt, F, d):
    """Minute path record: checkpoints, MFE/MAE, exit under baseline, walkout."""
    H, L_, C = rday.high.to_numpy(), rday.low.to_numpy(), rday.close.to_numpy()
    clocks = rday.clock.to_list()
    rec, mfe, mae, cvd = {}, 0.0, 0.0, 0.0
    risk = abs(e - stop0)
    done, pts, exit_m = False, None, None
    path = []
    for m in range(1, len(rday) - k0):
        j = k0 + m
        hi, lo, cl = H[j], L_[j], C[j]
        fav = (e - lo) if side < 0 else (hi - e)
        adv = (hi - e) if side < 0 else (e - lo)
        try:
            cvd += float(F.loc[(d, clocks[j]), "delta"]) * side
        except KeyError:
            pass
        path.append((hi, lo, cl, cvd))
        if not done:
            mfe, mae = max(mfe, fav), max(mae, adv)
            if (side < 0 and hi >= stop0) or (side > 0 and lo <= stop0):
                pts, done, exit_m = -risk, True, m
            elif (side < 0 and lo <= tgt) or (side > 0 and hi >= tgt):
                pts, done, exit_m = abs(tgt - e), True, m
        if m in CHECKS:
            rec[f"open{m}"] = int(not done)
            rec[f"r{m}"] = (((e - cl) if side < 0 else (cl - e)) / risk) if not done else np.nan
            rec[f"mf{m}"] = mfe / risk
            rec[f"ma{m}"] = -mae / risk
            rec[f"cvd{m}"] = cvd
    if pts is None:
        pts, exit_m = side * (C[-1] - e), len(rday) - k0 - 1
    # post-exit walkout (winners): furthest favorable beyond TARGET before EOD
    walkout = 0.0
    if pts > 0:
        for j in range(k0 + exit_m + 1, len(rday)):
            beyond = (tgt - L_[j]) if side < 0 else (H[j] - tgt)
            walkout = max(walkout, beyond)
    rec.update(mfe=mfe / risk, mae=-mae / risk, exit_m=exit_m,
               pts=pts, net_r=(pts - FR) / risk, win=int(pts - FR > 0),
               walkout_r=walkout / risk, risk=risk)
    return rec, path


def lever(path, side, e, risk, tgt, arm):
    """Evaluate a declared lever arm on the recorded path. Causal."""
    frac, pnl, stop = 1.0, 0.0, e - side * risk
    peak = 0.0
    p_done = False
    for m, (hi, lo, cl, cvd) in enumerate(path, start=1):
        fav = (e - lo) if side < 0 else (hi - e)
        peak = max(peak, fav)
        # stop first
        if (side < 0 and hi >= stop) or (side > 0 and lo <= stop):
            pnl += frac * side * (stop - e)
            return pnl
        # target handling
        hit_tgt = (side < 0 and lo <= tgt) or (side > 0 and hi >= tgt)
        if hit_tgt:
            if arm == "extend" and not p_done:
                pnl += 0.5 * abs(tgt - e)
                frac, p_done = 0.5, True
                stop = e  # runner rides with stop at entry
            else:
                pnl += frac * abs(tgt - e)
                return pnl
        if arm == "cut3" and m == 3 and (-(cl - e) * side if False else ((e - cl) if side < 0 else (cl - e))) <= -0.5 * risk:
            pnl += frac * side * (cl - e); return pnl
        if arm == "cut3" and m == 3 and peak <= 0 and ((e - cl) if side < 0 else (cl - e)) < 0:
            pass
        if arm == "cut5flow" and m == 5:
            r_now = ((e - cl) if side < 0 else (cl - e)) / risk
            if r_now < 0 and cvd <= 0:
                pnl += frac * side * (cl - e); return pnl
        if arm == "cut15" and m == 15:
            mae_now = max(((hi - e) if side < 0 else (e - lo)) / risk, 0)
            r_now = ((e - cl) if side < 0 else (cl - e)) / risk
            if mae_now >= 0.5 or cvd <= 0:
                pnl += frac * side * (cl - e); return pnl
        if arm == "partial" and not p_done and fav >= 1.0 * risk:
            pnl += 0.5 * 1.0 * risk
            frac, p_done = 0.5, True
        if arm == "partial05" and not p_done and fav >= 0.5 * risk:
            pnl += 0.5 * 0.5 * risk
            frac, p_done = 0.5, True
        if arm == "trail" and peak >= 1.5 * risk:
            cand = e + side * (peak - 0.75 * risk)
            if side * (cand - stop) > 0:
                stop = cand
        if arm == "trailB" and peak >= 1.0 * risk:
            cand = e + side * (peak - 0.5 * risk)
            if side * (cand - stop) > 0:
                stop = cand
    cl = path[-1][2]
    pnl += frac * side * (cl - e)
    return pnl


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert(NY)
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]
    F = pd.read_parquet(ROOT / "output/flow_minute_features.parquet")
    F = F.reset_index().set_index(["gday", "clock"]).sort_index()

    A_tr = [t for t in build_trades() if FIT0 <= t["day"] <= FIT1]
    B_tr = [t for t in build_ib50(B, R) if FIT0 <= t["day"] <= FIT1]
    days = {d: r.sort_values("ts").reset_index(drop=True) for d, r in R.groupby("gday")
            if FIT0 <= d <= FIT1}

    out = {"A": [], "B": []}
    for leg, trades in (("A", A_tr), ("B", B_tr)):
        for t in trades:
            d = t["day"]
            rday = days.get(d)
            if rday is None:
                continue
            fill = t["fill"]
            k0 = int((rday.ts == fill).idxmax()) if (rday.ts == fill).any() else None
            if k0 is None:
                continue
            if leg == "A":
                side, e = t["side"], t["entry"]
                stop0, tgt = t["stop"], t["target"]
            else:
                side, e = t["side"], None
                # rebuild B entry price from its record: entry at mid = fill bar
                # (build_ib50 stored only fill/exit/net_r/side; recompute)
                continue
            rec, path = walk(rday, k0, side, e, stop0, tgt, F, d)
            rec.update(day=d, leg=leg)
            for arm in ("cut3", "cut5flow", "partial", "trail", "extend"):
                pnl = lever(path, side, e, rec["risk"], tgt, arm)
                rec[f"L_{arm}"] = (pnl - FR) / rec["risk"]
            out[leg].append(rec)

    # leg B: rebuild with full detail inline (entry/stop/target needed)
    for d, rday in days.items():
        H, L_, C = rday.high.to_numpy(), rday.low.to_numpy(), rday.close.to_numpy()
        ib = rday[rday.clock < "10:30"]
        if len(ib) < 50 or len(rday) < 200:
            continue
        cummax, cummin = np.maximum.accumulate(H), np.minimum.accumulate(L_)
        ibh_f, ibl_f = ib.high.max(), ib.low.min()
        t_hi = ib.index[ib.high >= ibh_f][0]; t_lo = ib.index[ib.low <= ibl_f][0]
        if t_hi == t_lo:
            continue
        for k in range(len(rday)):
            ck = rday.clock.iloc[k]
            if ck < "10:23": continue
            if ck >= "11:30": break
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
                continue
            e, stop0 = mid, (ibh if side < 0 else ibl)
            tgt = ibl if side < 0 else ibh
            if abs(e - stop0) <= 0:
                break
            rec, path = walk(rday, k, side, e, stop0, tgt, F, d)
            rec.update(day=d, leg="B")
            for arm in ("cut15", "partial05", "trailB"):
                pnl = lever(path, side, e, rec["risk"], tgt, arm)
                rec[f"L_{arm}"] = (pnl - FR) / rec["risk"]
            out["B"].append(rec)
            break

    for leg in ("A", "B"):
        T = pd.DataFrame(out[leg])
        T.to_parquet(ROOT / f"output/nya_ibc_stage2c_{leg}.parquet", index=False)
        Wn, Lo = T[T.win == 1], T[T.win == 0]
        base = 160 * T.net_r.sum()
        print(f"\n===== LEG {leg} (n={len(T)}, WR {T.win.mean():.0%}, baseline ${base:+,.0f}) =====")
        print(f"WINNERS: median MAE {-Wn.mae.median():.2f}R (p75 {-Wn.mae.quantile(0.25):.2f}) | "
              f"median time-to-exit {Wn.exit_m.median():.0f}m | "
              f"median WALKOUT beyond target {Wn.walkout_r.median():+.2f}R (p75 {Wn.walkout_r.quantile(0.75):+.2f})")
        print(f"LOSERS:  median MFE {Lo.mfe.median():.2f}R | ever>=+0.5R {(Lo.mfe>=0.5).mean():.0%} | "
              f"median time-to-exit {Lo.exit_m.median():.0f}m")
        for t_ in (3, 5, 15):
            op = T[T[f"open{t_}"] == 1]
            dy = op[op[f"ma{t_}"] <= -0.5]
            cw = op[op[f"cvd{t_}"] > 0]
            ca = op[op[f"cvd{t_}"] <= 0]
            print(f"t+{t_}: open {len(op)} | dying WR {dy.win.mean():.0%}(n={len(dy)}) | "
                  f"cvd-with WR {cw.win.mean():.0%}(n={len(cw)}) vs against {ca.win.mean():.0%}(n={len(ca)})")
        print("LEVER ARMS ($160-risk):")
        for c in [c for c in T.columns if c.startswith("L_")]:
            tot = 160 * T[c].sum()
            print(f"  {c[2:]:10s}: ${tot:+,.0f} (delta {tot - base:+,.0f})")


if __name__ == "__main__":
    main()
