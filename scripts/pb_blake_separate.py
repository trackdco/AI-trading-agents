#!/usr/bin/env python3
"""What separates a PB-Blake winner from a loser — entry features and order flow.

FIT WINDOW 2025-06 -> 2026-07 (Angus's ruling; it is also where the flow data starts).
OUT OF FIT   2023-01 -> 2025-05, held back and never looked at while choosing anything.

THE MULTIPLE-TESTING PROBLEM IS THE WHOLE PROBLEM. 185 fit trades against ~40 features means
the best-looking variable is guaranteed to look good even if every one of them is noise. A
per-feature p-value answers the wrong question. So the headline test here is a FAMILY-WISE
permutation null: shuffle the outcome labels, recompute EVERY feature's separation, keep the
single best, repeat. That distribution is what "the best of 40 tries on noise" actually looks
like, and a real feature has to clear it -- not clear 0.05.

Separation is measured as AUC (the probability a random winner scores above a random loser).
0.50 is nothing. It is rank-based, so it does not care about outliers or units.

    python -m scripts.pb_blake_separate
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FIT = ROOT / "output/pb_fit.csv"
OOS = ROOT / "output/pb_oos.csv"
FLOW = ROOT / "output/fp_minutes.parquet"
N_PERM = 2000
RNG = np.random.default_rng(7)

SKIP = {"day", "side", "pool", "window", "exit", "year", "R", "tp1_hit", "stopped",
        "r_max", "entry", "stop", "tp1", "ent_i", "sweep_i", "hm", "p_null", "edge"}

# Features that MECHANICALLY determine the outcome through target distance rather than by
# carrying information. A wider stop puts the target nearer in R, so it is hit more often and
# pays less -- that is the win-rate/payoff dial, not an edge, and on a raw win/lose label these
# dominate every ranking. They are excluded from the family and reported separately.
TAUTOLOGICAL = {"r_tp1", "risk", "risk_atr", "travel_atr", "extern_R", "sweep_depth",
                "sweep_depth_atr", "gap_pts", "gap_atr", "atr60", "travel_per_bar"}


def auc(x: np.ndarray, y: np.ndarray) -> float:
    """P(random y=1 scores above random y=0), from ranks. Ties count as half."""
    ok = ~np.isnan(x)
    x, y = x[ok], y[ok]
    if y.sum() == 0 or (~y.astype(bool)).sum() == 0:
        return np.nan
    r = pd.Series(x).rank().to_numpy()
    n1 = y.sum()
    n0 = len(y) - n1
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def add_flow(T: pd.DataFrame) -> pd.DataFrame:
    """Order flow at and before the entry. NOTHING from the entry bar itself: the fill is at the
    OPEN of ent_i, so that minute's delta is still unknown when the decision is made. Features
    stop at the inverting bar, ent_i-1."""
    fp = pd.read_parquet(FLOW).reset_index()
    fp = fp.rename(columns={fp.columns[0]: "mi"})
    fp["key"] = fp.sday.astype(str) + "_" + fp.hm.astype(int).astype(str)
    fmap = fp.set_index("key")[["b", "a", "vol", "delta"]]

    def grab(day: str, h0: int, h1: int) -> pd.DataFrame:
        keys = [f"{day}_{m}" for m in range(h0, h1 + 1)]
        return fmap.reindex([k for k in keys if k in fmap.index])

    rows = []
    for _, r in T.iterrows():
        sgn = 1.0 if r.side == "long" else -1.0
        e = int(r.hm)                                   # entry bar minute-of-day
        inv = e - 1                                     # the inverting bar
        sw = e - int(r.bars_to_entry)                   # the sweep bar
        d = r.day
        f_inv = grab(d, inv, inv)
        f5 = grab(d, e - 5, inv)
        f15 = grab(d, e - 15, inv)
        f_leg = grab(d, sw, inv)
        f_sw = grab(d, sw, sw)
        f_base = grab(d, max(570, e - 60), inv)
        v_base = f_base.vol.mean() if len(f_base) else np.nan
        rows.append({
            "fl_delta_inv": sgn * f_inv.delta.sum() if len(f_inv) else np.nan,
            "fl_delta_5": sgn * f5.delta.sum() if len(f5) else np.nan,
            "fl_delta_15": sgn * f15.delta.sum() if len(f15) else np.nan,
            "fl_delta_leg": sgn * f_leg.delta.sum() if len(f_leg) else np.nan,
            "fl_delta_sweep": sgn * f_sw.delta.sum() if len(f_sw) else np.nan,
            # normalised: raw delta scales with volume, which scales with time of day
            "fl_delta_leg_n": (sgn * f_leg.delta.sum() / f_leg.vol.sum()
                               if len(f_leg) and f_leg.vol.sum() else np.nan),
            "fl_delta_5_n": (sgn * f5.delta.sum() / f5.vol.sum()
                             if len(f5) and f5.vol.sum() else np.nan),
            "fl_vol_inv_rel": (f_inv.vol.sum() / v_base
                               if len(f_inv) and v_base else np.nan),
            "fl_vol_sweep_rel": (f_sw.vol.sum() / v_base
                                 if len(f_sw) and v_base else np.nan),
            "fl_vol_leg_rel": (f_leg.vol.mean() / v_base
                               if len(f_leg) and v_base else np.nan),
            # book imbalance at the inverting bar: resting size on the side you are joining
            "fl_book_imb": ((f_inv.b.sum() - f_inv.a.sum()) * sgn /
                            max(f_inv.b.sum() + f_inv.a.sum(), 1) if len(f_inv) else np.nan),
            # absorption at the extreme: price made the low, did flow agree?
            "fl_absorb": (sgn * f_sw.delta.sum() / max(f_sw.vol.sum(), 1)
                          if len(f_sw) and f_sw.vol.sum() else np.nan),
        })
    return pd.concat([T.reset_index(drop=True), pd.DataFrame(rows)], axis=1)


def report(T: pd.DataFrame, label: str) -> None:
    w = (T.R > 0)
    pf = T.R[T.R > 0].sum() / max(-T.R[T.R < 0].sum(), 1e-9)
    print(f"{label:26} n={len(T):4d}  win={w.mean():5.1%}  PF={pf:5.2f}  avgR={T.R.mean():+.3f}")


def main() -> int:
    fit = add_flow(pd.read_csv(FIT))
    oos = add_flow(pd.read_csv(OOS))
    # GEOMETRY-NEUTRAL TARGET. For a driftless random walk P(+kR before -1R) = 1/(1+k) exactly,
    # so each trade has its own expected hit rate from its own geometry. The residual
    #     edge = hit - 1/(1+r_tp1)
    # is mean-zero under "no edge" REGARDLESS of where the stop and target sit. Ranking features
    # against this asks the only question worth asking: does the feature predict outperformance
    # of the trade's own geometry?
    for D in (fit, oos):
        D["p_null"] = 1.0 / (1.0 + D.r_tp1)
        D["edge"] = D.tp1_hit.astype(float) - D.p_null
    y = (fit.R > 0).astype(int).to_numpy()
    e = fit.edge.to_numpy(float)

    feats = [c for c in fit.columns if c not in SKIP and c not in TAUTOLOGICAL
             and pd.api.types.is_numeric_dtype(fit[c])]
    print(f"FIT 2025-06 -> 2026-07 | {len(fit)} trades, {y.sum()} winners, "
          f"{len(y)-y.sum()} losers, {len(feats)} features\n")
    report(fit, "fit baseline")
    report(oos, "out-of-fit baseline")

    # ---------- per-feature separation, against the geometry-neutral residual ----------
    def rcorr(x: np.ndarray, t: np.ndarray) -> float:
        ok = ~np.isnan(x)
        if ok.sum() < 30 or np.nanstd(x[ok]) == 0:
            return np.nan
        return float(pd.Series(x[ok]).rank().corr(pd.Series(t[ok]).rank()))

    A = {f: rcorr(fit[f].to_numpy(float), e) for f in feats}
    A = {k: v for k, v in A.items() if not np.isnan(v)}
    ranked = sorted(A.items(), key=lambda kv: -abs(kv[1]))

    # ---------- FAMILY-WISE null: best-of-all-features under shuffled labels ----------
    X = fit[list(A)].to_numpy(float)
    best_null = np.empty(N_PERM)
    for i in range(N_PERM):
        es = RNG.permutation(e)
        best_null[i] = max(abs(rcorr(X[:, j], es)) for j in range(X.shape[1]))
    thr95 = np.quantile(best_null, 0.95)
    obs_best = abs(ranked[0][1])
    p_fw = float((best_null >= obs_best).mean())

    print(f"\nvs GEOMETRY-NEUTRAL edge (hit minus its own random-walk probability)")
    print(f"{'feature':22} {'rho':>7}  {'top-half edge':>14} {'bot-half edge':>14}")
    for f, a in ranked[:16]:
        v = fit[f].to_numpy(float)
        m = np.nanmedian(v)
        hi = fit.edge[v > m].mean()
        lo = fit.edge[v <= m].mean()
        flag = "  *" if abs(a) >= thr95 else ""
        print(f"{f:22} {a:+7.3f}  {hi:+14.3f} {lo:+14.3f}{flag}")

    print(f"\n  (tautological geometry features, excluded from the family above:)")
    for f in sorted(TAUTOLOGICAL):
        if f in fit and pd.api.types.is_numeric_dtype(fit[f]):
            print(f"   {f:22} AUC vs win/lose {auc(fit[f].to_numpy(float), y):.3f}   "
                  f"rho vs edge {rcorr(fit[f].to_numpy(float), e):+.3f}")

    print(f"\nFAMILY-WISE NULL ({N_PERM} label shuffles, best of {len(A)} features each time)")
    print(f"  95th pct of best-|AUC-0.5| on pure noise : {thr95:.3f}")
    print(f"  best observed                            : {obs_best:.3f}  ({ranked[0][0]})")
    print(f"  family-wise p                            : {p_fw:.4f}")
    print(f"  VERDICT: {'a feature clears the noise ceiling' if p_fw < 0.05 else 'NOTHING clears it — every feature is within what 40 tries on noise produce'}")

    # ---------- categoricals ----------
    print("\ncategorical splits — FIT vs OUT-OF-FIT side by side:")
    print(f"   {'':18} {'fit n':>6} {'win':>7} {'PF':>6} {'edge':>7}   "
          f"{'oos n':>6} {'win':>7} {'PF':>6} {'edge':>7}")
    for col in ("side", "window", "pool", "tf"):
        for lvl in sorted(fit[col].unique(), key=str):
            x = fit[fit[col] == lvl]
            z = oos[oos[col] == lvl]
            if len(x) < 8:
                continue
            pfx = x.R[x.R > 0].sum() / max(-x.R[x.R < 0].sum(), 1e-9)
            pfz = z.R[z.R > 0].sum() / max(-z.R[z.R < 0].sum(), 1e-9)
            print(f"   {col}={str(lvl):12} {len(x):6d} {(x.R>0).mean():7.1%} {pfx:6.2f} "
                  f"{x.edge.mean():+7.3f}   {len(z):6d} {(z.R>0).mean():7.1%} {pfz:6.2f} "
                  f"{z.edge.mean():+7.3f}")

    # ---------- does the single best feature survive out of fit? ----------
    bf, ba = ranked[0]
    cut = fit[bf].median()
    hi_side = "above" if ba > 0 else "below"
    print(f"\nbest feature carried to out-of-fit: {bf} {hi_side} its FIT median ({cut:.3f})")
    for nm, D in (("fit", fit), ("out-of-fit", oos)):
        sel = D[bf] > cut if ba > 0 else D[bf] < cut
        if sel.sum() > 5:
            report(D[sel], f"  {nm} {bf} {hi_side}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
