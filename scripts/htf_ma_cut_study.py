#!/usr/bin/env python3
"""THE CUT STUDY — Phase 3 (SPEC-cut-study.md; everything declared there).

Half-1 exploration / Half-2 confirmation, seeded split-half on fit
session-days, stratified by era. Books are arm-separated, executable
(first trigger per structural fight). Score = P(pass eval: +$3,000 AND
>=5 winning days BEFORE EOD trailing-DD breach) at $160 risk/trade,
$2,000 trailing EOD DD, winning day >= $150, 90-day horizon, day-level
bootstrap 2,000 draws, seed 20260807.

    python -m scripts.htf_ma_cut_study --half 1     # exploration
    python -m scripts.htf_ma_cut_study --half 2     # confirmation (survivors only)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SEED, DRAWS = 20260807, 2000
RISK_USD, DD_USD, TARGET_USD, WMIN_USD, QDAYS, HORIZON = \
    160.0, 2000.0, 3000.0, 150.0, 5, 90

# candidate -> (arm(s), kind, bad_bin_rule)   [register, SPEC-cut-study.md]
BINARY_BAD0 = ["flowconf", "thru_delta_conf", "d5_conf", "d15_conf", "d30_conf"]
CONT_LOW_BAD = ["volx", "delta_z", "eff_result", "cvd_slope30", "closeloc",
                "rangex"]
COUNT_HIGH_BAD = ["cnt_ahead_1w", "cnt_beyond_3r"]


def build_books(F: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Executable book per arm: first trigger of each structural fight."""
    out = {}
    for arm in ("reject", "break"):
        R = F[(F.arm == arm) & F.out_ship.notna() & (F.risk > 0)]
        if arm == "break":
            R = R[R.retested.astype(bool)]
        R = R.sort_values("t")
        out[arm] = R.groupby("structural_cluster_id", as_index=False).first()
    return out


def eval_score(day_pnl: pd.Series, seed=SEED, draws=DRAWS) -> tuple[float, float]:
    """P(+$3k AND >=5 winning days before EOD trailing-DD breach, 90 days)."""
    v = day_pnl.to_numpy()
    if len(v) == 0:
        return 0.0, np.nan
    rng = np.random.default_rng(seed)
    passes, t_pass = 0, []
    for _ in range(draws):
        bal, peak, wins = 0.0, 0.0, 0
        ok = False
        days = rng.integers(0, len(v), HORIZON)
        for k, di in enumerate(days):
            bal += v[di]
            if v[di] >= WMIN_USD:
                wins += 1
            if bal <= peak - DD_USD:
                break
            peak = max(peak, bal)
            if bal >= TARGET_USD and wins >= QDAYS:
                ok = True
                t_pass.append(k + 1)
                break
        passes += ok
    return passes / draws, float(np.median(t_pass)) if t_pass else np.nan


def day_pnl(book: pd.DataFrame) -> pd.Series:
    return book.groupby("sess_day").out_ship.sum() * RISK_USD


def book_stats(book: pd.DataFrame) -> dict:
    dp = day_pnl(book)
    cum = dp.cumsum()
    score, med_days = eval_score(dp)
    return {"ev": book.out_ship.mean(), "n": len(book),
            "npd": len(book) / max(book.sess_day.nunique(), 1),
            "green": (dp > 0).mean(),
            "maxdd": (cum.cummax() - cum).max(),
            "score": score, "med_days": med_days}


def cuts_for(book: pd.DataFrame, edges: dict) -> dict[str, pd.Series]:
    """cut name -> boolean mask of REMOVED rows (True = cut)."""
    m = {}
    for c in BINARY_BAD0:
        m[f"{c}==0"] = book[c] == 0
    m["bp5opp==1"] = book.bp5opp == 1
    for c in CONT_LOW_BAD:
        m[f"{c}<Q1"] = book[c] < edges[f"{c}_q25"]
    for c in COUNT_HIGH_BAD:
        m[f"{c}>P75"] = book[c] > edges[f"{c}_q75"]
    m["blocked_snapshot"] = book.admissible_snapshot == False  # noqa: E712
    m["pen_bw<Q1"] = book.pen_bw < edges["pen_bw_q25"]
    m["session==ny_pm"] = book.session == "ny_pm"
    m["confluence>=3"] = book.confluence_count >= 3
    return m


def main() -> None:
    half = int(sys.argv[sys.argv.index("--half") + 1]) if "--half" in sys.argv else 1
    F = pd.read_parquet(ROOT / "output/htf_ma_census/mtable_fit.parquet")
    M = pd.read_parquet(ROOT / "output/htf_ma_census/mtable_fit_structclust.parquet")
    F = F.merge(M, on=["sess_day", "t", "arm", "side", "n_attempts"], how="left")
    B = pd.read_parquet(ROOT / "output/htf_ma_census/censusB_fit.parquet")
    F = F.merge(B[["sess_day", "t", "side", "n_attempts", "kind",
                   "confluence_count", "pen_bw", "admissible_snapshot"]],
                left_on=["sess_day", "t", "side", "n_attempts", "arm"],
                right_on=["sess_day", "t", "side", "n_attempts", "kind"],
                how="left")
    F["era"] = np.where(F.sess_day < "2026-01-01", "H2-2025", "H1-2026")

    # ---- frozen split ------------------------------------------------------
    split_f = ROOT / "output/htf_ma_census/cutstudy_split.csv"
    if split_f.exists():
        sp = pd.read_csv(split_f, dtype=str)
    else:
        rng = np.random.default_rng(SEED)
        rows = []
        for era, g in F.groupby("era"):
            days = np.sort(g.sess_day.unique())
            perm = rng.permutation(len(days))
            for i, d in enumerate(days):
                rows.append({"sess_day": d, "era": era,
                             "half": 1 if perm[i] < len(days) / 2 else 2})
        sp = pd.DataFrame(rows).astype({"sess_day": str, "half": int}).astype({"half": str})
        sp.to_csv(split_f, index=False)
        print(f"split written: {split_f} "
              f"(h1 {sum(sp.half=='1')} days, h2 {sum(sp.half=='2')} days)")
    keep_days = set(sp[sp.half == str(half)].sess_day)
    Fh = F[F.sess_day.isin(keep_days)]
    label = "EXPLORATION (half 1)" if half == 1 else "CONFIRMATION (half 2)"
    print(f"=== CUT STUDY — {label} — {len(keep_days)} days ===")

    books = build_books(Fh)
    # bin edges: ALWAYS computed on half-1 books (frozen for half 2)
    b1 = build_books(F[F.sess_day.isin(set(sp[sp.half == "1"].sess_day))])
    edges = {}
    for arm in ("reject", "break"):
        e = {}
        for c in CONT_LOW_BAD:
            e[f"{c}_q25"] = b1[arm][c].quantile(.25)
        for c in COUNT_HIGH_BAD:
            e[f"{c}_q75"] = b1[arm][c].quantile(.75)
        e["pen_bw_q25"] = b1[arm].pen_bw.quantile(.25)
        edges[arm] = e

    for arm in ("reject", "break"):
        bk = books[arm]
        base = book_stats(bk)
        print(f"\n-- {arm.upper()} book: EV {base['ev']:+.3f}R | n {base['n']} "
              f"({base['npd']:.1f}/day) | green {base['green']*100:.0f}% | "
              f"maxDD ${base['maxdd']:,.0f} | score {base['score']*100:.1f}% "
              f"(med {base['med_days']:.0f}d) --")
        print(f"{'cut':22s} {'rm%':>5s} {'muCut':>7s} {'lift':>7s} "
              f"{'EVaft':>7s} {'n':>5s} {'green':>6s} {'maxDD':>8s} "
              f"{'score':>6s} verdict")
        for name, mask in cuts_for(bk, edges[arm]).items():
            q = mask.mean()
            known = mask.notna().all()
            sub = bk[~mask.fillna(False)]
            if q == 0 or q > 0.6 or len(sub) < 50:
                print(f"{name:22s} {q*100:5.1f} — infeasible bin (declared "
                      f"rule, recorded, not adjusted)")
                continue
            mu = bk[mask.fillna(False)].out_ship.mean()
            lift = q * (base["ev"] - mu) / (1 - q)
            s = book_stats(sub)
            feas = lift >= 0.05
            better = s["score"] >= base["score"]
            verdict = "SURVIVOR" if (feas and better) else \
                ("lift<bar" if not feas else "score↓")
            print(f"{name:22s} {q*100:5.1f} {mu:+7.3f} {lift:+7.3f} "
                  f"{s['ev']:+7.3f} {s['n']:5d} {s['green']*100:5.0f}% "
                  f"${s['maxdd']:7,.0f} {s['score']*100:5.1f}% {verdict}")


if __name__ == "__main__":
    main()
