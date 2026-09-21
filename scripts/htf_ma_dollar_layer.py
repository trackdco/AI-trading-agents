#!/usr/bin/env python3
"""PHASE B — the dollar layer (B1 target x size, B2 two-phase sizing, B3
stop-once-green). Book: A+S1 (first-of-fight reject, flowconf != 0), full
fit. All sims day-block bootstrap, whole days with intraday order
preserved, seed 20260807, 2,000 draws.

Declared constants: qualifying-day floor $250 (trader to confirm exact
Lucid figure; sensitivity printed), eval target +$3,000, trailing EOD DD
$2,000, eval horizon 90 trading days. Funded stage: line locks once peak
>= +$2,000 (50k lock); payout $2,000 when balance >= $4,000 AND >= 5
qualifying days since last payout; 250-day year.

Exit generalization: out_ship at partial target T from mfe_r/out_trail —
verified to reproduce the stored out_ship at T=3 before any grid runs.

    python -m scripts.htf_ma_dollar_layer
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SEED, DRAWS = 20260807, 2000
TICK, COST = 0.25, 0.5
TARGET, DD, WMIN, QD, HORIZON = 3000.0, 2000.0, 250.0, 5, 90


def load_book() -> pd.DataFrame:
    F = pd.read_parquet(ROOT / "output/htf_ma_census/mtable_fit.parquet")
    M = pd.read_parquet(ROOT /
                        "output/htf_ma_census/mtable_fit_structclust.parquet")
    F = F.merge(M, on=["sess_day", "t", "arm", "side", "n_attempts"],
                how="left")
    R = F[(F.arm == "reject") & F.out_ship.notna()
          & (F.risk > 0)].sort_values("t")
    bk = R.groupby("structural_cluster_id", as_index=False).first()
    return bk[bk.flowconf != 0].copy()


def out_at_T(bk: pd.DataFrame, T: float) -> pd.Series:
    cost_r = COST / bk.risk
    trail_gross = bk.out_trail + cost_r
    reached = bk.mfe_r >= T
    leg = 0.75 * (T - TICK / bk.risk) + 0.25 * trail_gross - cost_r
    return pd.Series(np.where(reached, leg, bk.out_trail), index=bk.index)


def eval_sim(day_vals: np.ndarray, day_wins: np.ndarray,
             seed=SEED, draws=DRAWS, wmin=None):
    rng = np.random.default_rng(seed)
    n = len(day_vals)
    passes, tpass = 0, []
    for _ in range(draws):
        bal = peak = 0.0
        wins = 0
        for k, di in enumerate(rng.integers(0, n, HORIZON)):
            bal += day_vals[di]
            wins += day_wins[di]
            if bal <= peak - DD:
                break
            peak = max(peak, bal)
            if bal >= TARGET and wins >= QD:
                passes += 1
                tpass.append(k + 1)
                break
    return passes / draws, (float(np.median(tpass)) if tpass else np.nan)


def funded_sim(day_r: np.ndarray, s_pre: float, s_post: float,
               seed=SEED, draws=DRAWS):
    rng = np.random.default_rng(seed)
    n = len(day_r)
    busts, wd_all, lockd = 0, [], []
    for _ in range(draws):
        bal = peak = 0.0
        locked = False
        wins, wd, lday = 0, 0.0, np.nan
        for k, di in enumerate(rng.integers(0, n, 250)):
            size = s_post if locked else s_pre
            pnl = day_r[di] * size
            bal += pnl
            peak = max(peak, bal)
            if not locked and peak >= DD:
                locked, lday = True, k + 1
            line = 0.0 if locked else peak - DD
            if bal <= line:
                busts += 1
                break
            if pnl >= WMIN:
                wins += 1
            if locked and bal >= 4000.0 and wins >= QD:
                bal -= 2000.0
                wd += 2000.0
                wins = 0
        wd_all.append(wd)
        lockd.append(lday)
    return (busts / draws, float(np.median(wd_all)),
            float(np.nanmedian(lockd)))


def main() -> None:
    bk = load_book()
    days = bk.sess_day.nunique()
    print(f"book: A+S1 reject | {len(bk)} fights | {days} days "
          f"({len(bk)/days:.1f}/day)")
    chk = out_at_T(bk, 3.0)
    err = (chk - bk.out_ship).abs().max()
    print(f"T-formula check vs stored out_ship at T=3: max |err| = {err:.2e}")
    assert err < 1e-9, "T generalization does not reproduce the table"

    print("\n== B1: (partial target T, size) grid — score = P(pass eval: "
          f"+${TARGET:,.0f} AND >={QD} days >= ${WMIN:,.0f} before "
          f"${DD:,.0f} EOD-trailing breach, {HORIZON}d) ==")
    print(f"{'T':>3s} {'size':>5s} {'EV(R)':>7s} {'$/day':>7s} "
          f"{'qday%':>6s} {'score':>6s} {'med_d':>6s}")
    for T in (2.0, 3.0, 4.0, 5.0):
        r = out_at_T(bk, T)
        day_r = bk.assign(o=r).groupby("sess_day").o.sum()
        for size in (150, 300, 450, 600):
            dv = (day_r * size).to_numpy()
            dw = (day_r * size >= WMIN).to_numpy().astype(int)
            sc, md = eval_sim(dv, dw)
            print(f"{T:3.0f} {size:5d} {r.mean():+7.3f} {dv.mean():7.0f} "
                  f"{dw.mean()*100:5.1f}% {sc*100:5.1f}% {md:6.0f}")

    print("\n== B1 floor sensitivity at the (T=3, size=300) cell ==")
    day_r = bk.groupby("sess_day").out_ship.sum()
    for wmin in (150.0, 250.0, 350.0):
        dv = (day_r * 300).to_numpy()
        dw = (dv >= wmin).astype(int)
        sc, md = eval_sim(dv, dw, wmin=wmin)
        print(f"  floor ${wmin:,.0f}: qday {dw.mean()*100:.1f}% | "
              f"score {sc*100:.1f}% (med {md:.0f}d)")

    print("\n== B2: two-phase sizing across the DD lock (funded stage, "
          "250d, payout $2k @ bal>=$4k & 5 qdays) ==")
    dr = day_r.to_numpy()
    print(f"{'S_pre':>6s} {'S_post':>7s} {'P(bust)':>8s} "
          f"{'med $/yr':>9s} {'med lock d':>10s}")
    for s_pre in (150, 300, 600):
        for s_post in (150, 300, 600):
            pb, wd, ld = funded_sim(dr, s_pre, s_post)
            print(f"{s_pre:6d} {s_post:7d} {pb*100:7.1f}% {wd:9,.0f} "
                  f"{ld:10.0f}")

    print("\n== B3: stop-once-green-by-X (size 300; approximation: entries "
          "stop once cumulative BOOKED day P&L >= X, trigger order) ==")
    bs = bk.sort_values(["sess_day", "t"])
    for X in (250.0, 400.0, 600.0, 1000.0, np.inf):
        rows = []
        for d, g in bs.groupby("sess_day"):
            cum, keep = 0.0, []
            for r in g.itertuples():
                if cum >= X:
                    break
                keep.append(r.Index)
                cum += r.out_ship * 300
            rows.extend(keep)
        sub = bs.loc[rows]
        dv = (sub.groupby("sess_day").out_ship.sum() * 300)
        dv = dv.reindex(day_r.index, fill_value=0.0).to_numpy()
        dw = (dv >= WMIN).astype(int)
        sc, md = eval_sim(dv, dw)
        lbl = "none" if np.isinf(X) else f"{X:,.0f}"
        print(f"  X=${lbl:>6s}: trades {len(sub):5d} | $/day {dv.mean():6.0f}"
              f" | qday {dw.mean()*100:5.1f}% | score {sc*100:5.1f}% "
              f"(med {md:.0f}d)")


if __name__ == "__main__":
    main()
