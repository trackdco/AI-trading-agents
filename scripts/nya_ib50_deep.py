#!/usr/bin/env python3
"""NYA-IB50-01 trial 3 — the §5.11-9 deep round on the FIT SPAN
(2025-06 -> 2026-07, full coverage): MFE/MAE + time segments
(t+5/15/30/60), IN-TRADE flow (cvd since entry at checkpoints),
depth-at-entry (front-run coverage), and the conviction-sizing arm
(declared score: weekday-floor + entry-delta agreement + book lean;
size = 1 + score units vs flat 1 unit, $160-risk per unit).

    python -m scripts.nya_ib50_deep
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FR = 1.0
CHECKS = (5, 15, 30, 60)
FIT0, FIT1 = "2025-06-01", "2026-07-31"


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert("America/New_York")
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]

    F = pd.read_parquet(ROOT / "output/flow_minute_features.parquet")
    F = F.reset_index().set_index(["gday", "clock"]).sort_index()
    D = pd.read_parquet(ROOT / "output/depth_minutes.parquet")
    D = D.assign(gday=pd.Series(D.index.date, index=D.index).astype(str),
                 clock=D.index.strftime("%H:%M")).set_index(["gday", "clock"])

    # trailing weekday-conditional rejection rates (as trial 2, no lookahead)
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

        # conviction score at entry (causal)
        score = 0
        rw = W.roll_wd.get(d, np.nan)
        if rw == rw and rw >= 0.70: score += 1
        clk = r.clock.iloc[k0]
        try:
            fl = F.loc[(d, clk)]
            if np.sign(fl.delta) == side: score += 1
        except KeyError:
            fl = None
        try:
            dd = D.loc[(d, clk)]
            if (dd.imb - 0.5) * 2 * side > 0.1: score += 1
        except KeyError:
            pass

        rec = dict(day=d, year=d[:4], score=score, risk=risk)
        mfe = mae = 0.0
        done, pts = False, None
        cvd0 = None
        for m in range(1, len(r) - k0):
            j = k0 + m
            hi, lo, cl = H[j], L_[j], C[j]
            fav = (e - lo) if side < 0 else (hi - e)
            adv = (hi - e) if side < 0 else (e - lo)
            if not done:
                mfe, mae = max(mfe, fav), max(mae, adv)
                if (side < 0 and hi >= stop) or (side > 0 and lo <= stop):
                    pts, done = -risk, True
                elif (side < 0 and lo <= tgt) or (side > 0 and hi >= tgt):
                    pts, done = abs(tgt - e), True
            if m in CHECKS:
                r_now = ((e - cl) if side < 0 else (cl - e)) / risk
                rec[f"open{m}"] = int(not done)
                rec[f"r{m}"] = r_now if not done else np.nan
                rec[f"mf{m}"] = mfe / risk
                rec[f"ma{m}"] = -mae / risk
                # in-trade flow: cvd since entry, signed to trade
                try:
                    seg = F.loc[d].loc[r.clock.iloc[k0 + 1]:r.clock.iloc[j]]
                    rec[f"cvd{m}"] = float(seg.delta.sum()) * side
                except Exception:
                    rec[f"cvd{m}"] = np.nan
            if done and m >= max(CHECKS):
                break
        if pts is None:
            pts = side * (C[-1] - e)
        rec["pts"] = pts
        rec["net_r"] = (pts - FR) / risk
        rec["win"] = int(pts - FR > 0)
        rows.append(rec)

    A = pd.DataFrame(rows)
    A.to_parquet(ROOT / "output/nya_ib50_deep.parquet", index=False)
    base = A.win.mean()
    print(f"FIT-SPAN n={len(A)} | base WR {base:.0%} | mean R {A.net_r.mean():+.3f}")

    Wn, Lo = A[A.win == 1], A[A.win == 0]
    print(f"MFE/MAE: losers median MFE {Lo.mf60.median():.2f}R, ever>=+0.5R "
          f"{(Lo.mf60 >= 0.5).mean():.0%}; winners median MAE {-Wn.ma60.median():.2f}R")

    print("\ntime segments (still-open-at-t):")
    for t in (5, 15, 30):
        op = A[A[f"open{t}"] == 1]
        press = op[(op[f"mf{t}"] >= 0.5) & (op[f"r{t}"] > 0) & (op[f"mf{t}"] - op[f"r{t}"] <= 0.25)]
        dying = op[op[f"ma{t}"] <= -0.5]
        for lbl, g in (("PRESS", press), ("DYING", dying)):
            if len(g) >= 8:
                print(f"  t+{t} {lbl}: n={len(g)} WR {g.win.mean():.0%} (base {base:.0%})")
            else:
                print(f"  t+{t} {lbl}: n={len(g)} — thin")

    print("\nin-trade flow (cvd since entry, still-open):")
    for t in (15, 30):
        op = A[(A[f"open{t}"] == 1) & A[f"cvd{t}"].notna()]
        w_, a_ = op[op[f"cvd{t}"] > 0], op[op[f"cvd{t}"] <= 0]
        for lbl, g in (("cvd WITH", w_), ("cvd AGAINST", a_)):
            if len(g) >= 8:
                print(f"  t+{t} {lbl}: n={len(g)} WR {g.win.mean():.0%}")
            else:
                print(f"  t+{t} {lbl}: n={len(g)} — thin")

    print("\nconviction-sizing arm (declared: units = 1 + score, $160-risk/unit):")
    for s, g in A.groupby("score"):
        print(f"  score {s}: n={len(g)} WR {g.win.mean():.0%} meanR {g.net_r.mean():+.3f}")
    flat = 160 * A.net_r.sum()
    conv = 160 * (A.net_r * (1 + A.score)).sum()
    convn = conv / (1 + A.score).mean()
    print(f"  flat-size total ${flat:+,.0f} | conviction-sized ${conv:+,.0f} "
          f"(risk-normalized ${convn:+,.0f})")


if __name__ == "__main__":
    main()
