#!/usr/bin/env python3
"""NYA-IBC-01 stage 2 — the declared leg-B arm lab (family file,
2026-08-05). Uncapped fit-span leg-B events, minute-walked once per event;
each declared arm evaluated on the shared path. Day-level R matrix -> PBO.

    python -m scripts.nya_ibc_stage2
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validation.pbo import pbo_cscv

NY = "America/New_York"
FR = 1.0
FIT0, FIT1 = "2025-06-01", "2026-07-31"

ARMS = {
    "B0_astaught": dict(),
    "B1_cap20": dict(cap=20.0),
    "B2_cap30": dict(cap=30.0),
    "B3_cap50": dict(cap=50.0),
    "B4_quarterIB": dict(frac=0.25),
    "B5_cap30_frontrun": dict(cap=30.0, frontrun=True),
    "B6_cap30_cut": dict(cap=30.0, cut=True),
    "B7_cap30_fr_cut": dict(cap=30.0, frontrun=True, cut=True),
    "B8_full_conviction": dict(cap=30.0, frontrun=True, cut=True, conv=True),
    "B9_astaught_cut": dict(cut=True),
}


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert(NY)
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]

    F = pd.read_parquet(ROOT / "output/flow_minute_features.parquet")
    F = F.reset_index().set_index(["gday", "clock"]).sort_index()
    D = pd.read_parquet(ROOT / "output/depth_minutes.parquet")
    D = D.assign(gday=pd.Series(D.index.date, index=D.index).astype(str),
                 clock=D.index.strftime("%H:%M")).set_index(["gday", "clock"])

    # weekday trailing rates for the conviction score (no lookahead)
    wd_rows = []
    for d, r in R.groupby("gday"):
        r = r.sort_values("ts").reset_index(drop=True)
        if len(r) < 200: continue
        ib = r[r.clock < "10:30"]
        if len(ib) < 50: continue
        ibh, ibl = ib.high.max(), ib.low.min()
        t_hi = ib.index[ib.high >= ibh][0]; t_lo = ib.index[ib.low <= ibl][0]
        if t_hi == t_lo: continue
        pred = "L" if t_hi < t_lo else "H"
        fb = None
        for _, row in r[r.clock >= "10:30"].iterrows():
            if row.high > ibh: fb = "H"; break
            if row.low < ibl: fb = "L"; break
        wd_rows.append(dict(day=d, wd=pd.Timestamp(d).weekday(), success=int(fb == pred)))
    W = pd.DataFrame(wd_rows).set_index("day").sort_index()
    W["roll_wd"] = W.groupby("wd").success.transform(
        lambda s: s.shift(1).rolling(26, min_periods=13).mean())

    rows = []
    for d, r in R.groupby("gday"):
        if not (FIT0 <= d <= FIT1):
            continue
        r = r.sort_values("ts").reset_index(drop=True)
        if len(r) < 200: continue
        ib = r[r.clock < "10:30"]
        if len(ib) < 50: continue
        H, L_, C = r.high.to_numpy(), r.low.to_numpy(), r.close.to_numpy()
        cummax, cummin = np.maximum.accumulate(H), np.minimum.accumulate(L_)
        ibh_f, ibl_f = ib.high.max(), ib.low.min()
        t_hi = ib.index[ib.high >= ibh_f][0]; t_lo = ib.index[ib.low <= ibl_f][0]
        if t_hi == t_lo: continue
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
            # WICK-DEATH universe (stage-1b discovery): any prior wick touch
            # of an extreme after 10:23 kills the day for leg B
            side = -1 if th < tl else 1
            mid = (ibh + ibl) / 2
            if not (L_[k] <= mid <= H[k]):
                k += 1; continue
            e = mid
            stop_full = ibh if side < 0 else ibl
            tgt = ibl if side < 0 else ibh
            risk_full = abs(e - stop_full)
            if risk_full <= 0:
                break
            seq += 1
            # conviction score (causal at entry)
            score = 0
            rw = W.roll_wd.get(d, np.nan)
            if rw == rw and rw >= 0.70: score += 1
            clk = r.clock.iloc[k]
            try:
                fl = F.loc[(d, clk)]
                if np.sign(fl.delta) == side: score += 1
            except KeyError:
                pass
            try:
                dd_ = D.loc[(d, clk)]
                if (dd_.imb - 0.5) * 2 * side > 0.1: score += 1
            except KeyError:
                pass
            # minute path from entry to EOD
            path = list(range(k + 1, len(r)))
            rec = dict(day=d, year=d[:4], seq=seq, frontrun=int(clk < "10:30"),
                       score=score)
            for arm, cfg in ARMS.items():
                if cfg.get("frontrun") and clk >= "10:30":
                    continue
                risk = risk_full
                if cfg.get("cap"):
                    risk = min(risk, cfg["cap"])
                elif cfg.get("frac"):
                    risk = cfg["frac"] * (ibh - ibl)
                stop = e - side * risk
                pts, mae, cvd = None, 0.0, 0.0
                for m, j in enumerate(path, start=1):
                    hi, lo, cl = H[j], L_[j], C[j]
                    adv = (hi - e) if side < 0 else (e - lo)
                    mae = max(mae, adv)
                    try:
                        cvd += float(F.loc[(d, r.clock.iloc[j])].delta) * side
                    except KeyError:
                        pass
                    if (side < 0 and hi >= stop) or (side > 0 and lo <= stop):
                        pts = -risk; break
                    if (side < 0 and lo <= tgt) or (side > 0 and hi >= tgt):
                        pts = abs(tgt - e); break
                    if cfg.get("cut") and m == 15 and (mae / risk >= 0.5 or cvd <= 0):
                        pts = ((e - cl) if side < 0 else (cl - e)); break
                if pts is None:
                    pts = side * (C[-1] - e)
                units = (1 + score) if cfg.get("conv") else 1
                rec[arm] = units * (pts - FR) / risk
                rec[f"{arm}_u"] = units
            rows.append(rec)
            # wick-death: this event's resolution touched an extreme or EOD -> done
            break
        # (single sequence per day under wick-death universe)

    T = pd.DataFrame(rows)
    T.to_parquet(ROOT / "output/nya_ibc_stage2.parquet", index=False)
    print(f"leg-B events (wick-death universe): {len(T)}")
    print(f"{'arm':22s} {'n':>4s} {'WR':>5s} {'sumR':>7s} {'$':>9s} {'25':>6s} {'26':>6s}")
    for arm in ARMS:
        g = T[T[arm].notna()]
        if not len(g):
            continue
        r_ = g[arm] / g.get(f"{arm}_u", 1).fillna(1) if f"{arm}_u" in g else g[arm]
        raw = g[arm]
        yr = {y: round(x.sum(), 1) for y, x in raw.groupby(g.year)}
        print(f"{arm:22s} {len(g):4d} {(raw>0).mean():5.0%} {raw.sum():+7.1f} "
              f"${160*raw.sum():+8,.0f} {yr.get('2025',0):+6.1f} {yr.get('2026',0):+6.1f}")

    M = T.pivot_table(index="day", values=[a for a in ARMS], aggfunc="sum").fillna(0.0)
    res = pbo_cscv(M, n_blocks=8)
    print(f"\nPBO (S=8, {res.n_combinations} splits, {res.n_obs_used} days): {res.pbo:.2f} | "
          f"slope {res.slope:.2f} | P(OOS loss) {res.prob_oos_loss:.2f}")


if __name__ == "__main__":
    main()
