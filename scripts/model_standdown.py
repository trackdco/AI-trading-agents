#!/usr/bin/env python3
"""Multivariate walk-forward stand-down model (Angus 23-Jul round 3) — the angle I skipped.

Target = the DECISION-RELEVANT label: sign of the no-forecast portfolio's realized P&L in a
given (day, window). Predict "this window loses" from pre-decision features, respecting causality:
  PRE  window (decide 08:00): only pre-08:00 info (overnight/Asia/London/prior-day/calendar).
  GOLD window (decide 09:30): everything through 09:30 (all pre-market flow + depth + pre result).

Model: HistGradientBoostingClassifier, shallow. Validation: TimeSeriesSplit walk-forward (train
past -> predict future, threshold tuned on TRAIN only). Metrics: OOF AUC AND the honest dollar
result — total portfolio $ after the model's skip decisions vs ungated. Run flow-only (all days)
and flow+depth (depth-covered days) to isolate depth's marginal value.

    python -m scripts.model_standdown
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import roc_auc_score
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
NY = "America/New_York"

PRE8 = ["cvd_ON", "cvd_ASIA", "cvd_LON", "eff_ON", "eff_ASIA", "eff_LON", "on_range",
        "absz_cvd_ON", "z_cvd_ON", "rel_range", "rel_vol", "inventory_pts", "on_extreme_age",
        "on_eff_path", "yday_red", "red_streak", "yday_orc", "gap_open_pts", "imbal_share_20",
        "imbal_share_10", "trap_rate_10", "range_pctl_20", "pdc_loc", "on_nr_rank", "dow",
        "edge_top_delta_ON", "edge_bot_delta_ON", "px_chg_ON"]
THRU930 = PRE8 + ["cvd_PM", "eff_PM", "cvd_r2_PM", "pm_eff_path", "pm_crosses", "pm_flip",
                  "cvd_accel_PM", "absorb_ct_PM", "burst_ct_PM", "big_print_share_PM",
                  "maxmin_delta_PM", "px_chg_PM", "pos_800", "pm_early_delta", "pm_late_delta",
                  "sweep_lh_PM", "sweep_ll_PM", "vwap2_lo_PM", "vwap2_up_PM", "absz_cvd_PM"]
DEPTH_PRE = ["d_pre_imb_mean", "d_pre_imb_std", "d_pre_imb_last", "d_pre_absimb_mean",
             "d_pre_nearimb_mean", "d_pre_totsz_mean", "d_pre_totsz_trend", "d_pre_imb_trend",
             "d_pre_spread_mean", "d_pre_imb_flips", "d_pre_thin_frac"]


def build():
    F = pd.read_parquet("output/dayflow_v2.parquet")
    S = pd.read_parquet("output/trade_angles.parquet")
    S["win_"] = np.where(S.fillmi.dt.hour * 60 + S.fillmi.dt.minute < 570, "pre", "gold")
    q1 = S[(S.pattern == "B2") & (S.yr == 2025) & (S.conf_PM == 1)].cvd_PM.abs().quantile(0.25)
    keep = (((S.pattern == "B2") & (S.conf_PM == 1) & (S.cvd_PM.abs() >= q1) & (S.path_lo == 0)) |
            ((S.pattern == "B") & (S.conf_last15 == 1) & (S.div15 == 0)) |
            ((S.pattern == "A") & (S.conf_PM == 1)))
    K = S[keep].copy()
    winpl = K.groupby(["day", "win_"]).dollars.sum().reset_index()
    dep = pd.read_parquet("output/depth_daywin.parquet")
    return F, winpl, dep


def walk(df, feats, tag):
    """df: one row per window-observation with features + 'pl' + 'day'. Walk-forward."""
    df = df.sort_values("day").reset_index(drop=True)
    df = df.dropna(subset=["pl"])
    feats = [c for c in feats if c in df and df[c].notna().sum() >= 20 and df[c].nunique() >= 3]
    X = df[feats].astype(float).values
    y = (df.pl < 0).astype(int).values
    pl = df.pl.values
    n = len(df)
    if n < 70 or y.sum() < 12 or (1 - y).sum() < 12:
        print(f"  {tag}: too few ({n} obs, {int(y.sum())} loss) — skip"); return
    tss = TimeSeriesSplit(n_splits=4, test_size=max(20, n // 6))
    oof_p = np.full(n, np.nan)
    base_test = kept_test = 0.0
    sized_test = []
    for tr, te in tss.split(X):
        if len(tr) < 40 or y[tr].sum() < 6 or (1 - y[tr]).sum() < 6:
            base_test += pl[te].sum(); kept_test += pl[te].sum(); continue
        m = HistGradientBoostingClassifier(max_depth=3, max_iter=150, learning_rate=0.06,
                                           l2_regularization=2.0, min_samples_leaf=12,
                                           max_bins=64, early_stopping=False, random_state=0)
        try:
            m.fit(X[tr], y[tr])
        except Exception as e:
            base_test += pl[te].sum(); kept_test += pl[te].sum(); continue
        pte = m.predict_proba(X[te])[:, 1]
        oof_p[te] = pte
        base_test += pl[te].sum()
        kept_test += pl[te][pte < 0.5].sum()                       # FIXED skip P(loss)>=0.5
        # 3-tier SIZE (robust, no capital change: renormalize by mean size)
        sz = np.where(pte < 0.4, 1.0, np.where(pte < 0.6, 0.6, 0.25))
        sized_test.append((pl[te] * sz, sz))
    ok = ~np.isnan(oof_p)
    auc = roc_auc_score(y[ok], oof_p[ok]) if ok.sum() > 10 and y[ok].sum() else float("nan")
    spl = np.concatenate([a for a, _ in sized_test]); ssz = np.concatenate([s for _, s in sized_test])
    sized = spl.sum() / ssz.mean()                                 # normalize so avg size = 1 contract
    print(f"  {tag}: n={n} feats={len(feats)}  loss%={y.mean():.0%}  OOF-AUC={auc:.3f}  "
          f"| $ ungated {base_test:+7,.0f}  skip@.5 {kept_test:+7,.0f}  sized {sized:+7,.0f}")


def main():
    F, winpl, dep = build()
    Fd = F.reset_index()
    W = winpl.merge(Fd, on="day", how="left")
    Wd = W.merge(dep.reset_index(), on="day", how="left")

    print("=== PRE window (decide 08:00, pre-08:00 features only) ===")
    pre = W[W.win_ == "pre"].rename(columns={"dollars": "pl"})
    walk(pre.assign(pl=pre.pl), [c for c in PRE8 if c in pre], "PRE flow-only (all days)")

    print("\n=== GOLD window (decide 09:30, through-09:30 features) ===")
    gold = W[W.win_ == "gold"].rename(columns={"dollars": "pl"})
    walk(gold.assign(pl=gold.pl), [c for c in THRU930 if c in gold], "GOLD flow-only (all days)")

    print("\n=== GOLD window + DEPTH (depth-covered days only) ===")
    goldd = Wd[Wd.win_ == "gold"].rename(columns={"dollars": "pl"})
    goldd = goldd.dropna(subset=["d_pre_imb_mean"])
    walk(goldd.assign(pl=goldd.pl), [c for c in THRU930 + DEPTH_PRE if c in goldd], "GOLD flow (depth days)")
    walk(goldd.assign(pl=goldd.pl), [c for c in THRU930 if c in goldd], "GOLD flow-only (same days, no depth)")

    print("\n=== PRE window + DEPTH (depth-covered days) ===")
    pred = Wd[Wd.win_ == "pre"].rename(columns={"dollars": "pl"}).dropna(subset=["d_pre_imb_mean"])
    walk(pred.assign(pl=pred.pl), [c for c in PRE8 + DEPTH_PRE if c in pred], "PRE flow+depth")
    walk(pred.assign(pl=pred.pl), [c for c in PRE8 if c in pred], "PRE flow-only (same days)")


if __name__ == "__main__":
    main()
