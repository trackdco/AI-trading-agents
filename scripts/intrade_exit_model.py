#!/usr/bin/env python3
"""IN-TRADE EARLY-EXIT — multivariate model, day-grouped CV, permutation
calibration, and the policy decision test.

Reads:
  race_wide.parquet        entry/stop/direction/session/mech + decision-time
                            (pre-entry) covariates
  race_intrade_features.parquet   in-trade snapshots at N in {1,2,3,5,10}
                            minutes after entry (built by
                            scripts/intrade_exit_features.py, NO information
                            after entry+N)
  race_runs.parquet        run_mfe_r (untruncated, stop-truncated run) ->
                            is_junk = run_mfe_r < 0.5
  race_realexit.parquet    real_out (actual shipped exit), reached_3r, j0/j_exit

For each horizon N: logistic regression + gradient boosting (HistGB), fit on
STATIC (pre-entry) covariates + the N-specific in-trade snapshot, evaluated
with GroupKFold on sess_day (a day never appears in both train and test).
Headline: out-of-fold AUC vs a permutation null (labels shuffled within
session x mech, 20 draws).

Then the decision test: "at entry+N, if OOF P(junk) > threshold, exit at
market" is simulated against (a) do-nothing (the real shipped exit) and
(b)/(c) blanket -0.5R / -0.75R stops (same 3R-target + breakeven/trail
machinery as race_realexit.score_one, only the initial stop distance
changes) -- book EV and P(3R).

    python -m scripts.intrade_exit_model
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.race_realexit import day_arrays, score_one             # noqa: E402
from src.htf_ma.levels import NY                                    # noqa: E402

warnings.filterwarnings("ignore")

CENSUS = ROOT / "output/htf_ma_census"
HORIZONS = [1, 2, 3, 5, 10]
N_FOLDS = 5
N_PERM = 20
SEED = 20260808
COST_R_TOTAL_PTS = 1.0
STOP_BLANKETS = [0.5, 0.75]

STATIC_COLS = ["mech", "session", "is_long", "tf_won", "n_aff", "w15", "risk",
              "disp_w", "epi_max_w", "flowconf", "volx", "closeloc", "rangex",
              "atr30_over_w", "risk_over_atr30", "px_vs_ma15_w",
              "ma15_ahead_r", "n_struct_ahead", "open_space", "day_range_w",
              "pos_in_day_range", "dow", "month", "tmin"]
CAT_COLS = ["mech", "session"]

INTRADE_KEYS = ["exc_fav_r", "exc_adv_r", "close_r", "green_ever", "green_now",
                "back_thru_entry", "frac_red_bars", "mean_bar_range_r",
                "range_vs_base", "vol_ratio", "delta_share", "dist_ma15_r",
                "ma15_move_r", "already_stopped", "n_bars"]


def load_master() -> pd.DataFrame:
    B = pd.read_parquet(CENSUS / "race_wide.parquet")
    F = pd.read_parquet(CENSUS / "race_intrade_features.parquet")
    R = pd.read_parquet(CENSUS / "race_runs.parquet")
    X = pd.read_parquet(CENSUS / "race_realexit.parquet")
    keep_x = ["scid", "real_out", "reached_3r", "exit_mode", "j0", "j_exit",
              "cost_r"]
    M = (B.merge(F.drop(columns=["mech", "session", "direction", "sess_day"]),
                on="scid", how="inner")
          .merge(R[["scid", "run_mfe_r", "mins_to_peak"]], on="scid", how="inner")
          .merge(X[keep_x], on="scid", how="inner"))
    assert len(M) == len(B), f"merge dropped rows: {len(M)} vs {len(B)}"
    M["is_junk"] = (M.run_mfe_r < 0.5).astype(int)
    M["is_real_loss"] = (M.real_out < 0).astype(int)
    return M


def feature_cols(h: int) -> list[str]:
    return STATIC_COLS + [f"h{h}_{k}" for k in INTRADE_KEYS]


def make_pipe(kind: str, cat_cols: list[str], num_cols: list[str]) -> Pipeline:
    if kind == "lr":
        pre = ColumnTransformer([
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
            ("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                              ("sc", StandardScaler())]), num_cols)])
        clf = LogisticRegression(max_iter=3000, class_weight="balanced",
                                 C=1.0)
    else:
        pre = ColumnTransformer([
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
            ("num", SimpleImputer(strategy="median"), num_cols)])
        clf = HistGradientBoostingClassifier(
            max_depth=3, max_iter=150, learning_rate=0.06,
            l2_regularization=1.0, random_state=SEED,
            class_weight="balanced")
    return Pipeline([("pre", pre), ("clf", clf)])


def oof_proba(Xh: pd.DataFrame, y: np.ndarray, groups: np.ndarray, kind: str,
             cat_cols: list[str], num_cols: list[str], n_folds: int) -> np.ndarray:
    pipe = make_pipe(kind, cat_cols, num_cols)
    cv = GroupKFold(n_splits=n_folds)
    p = cross_val_predict(pipe, Xh, y, groups=groups, cv=cv,
                          method="predict_proba")
    return p[:, 1]


def permute_within_strata(y: np.ndarray, strata: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    yp = y.copy()
    for s in np.unique(strata):
        idx = np.where(strata == s)[0]
        yp[idx] = rng.permutation(y[idx])
    return yp


def run_horizon(M: pd.DataFrame, h: int, n_folds: int = N_FOLDS,
                n_perm: int = N_PERM) -> dict:
    cols = feature_cols(h)
    Xh = M[cols].copy()
    y = M.is_junk.to_numpy()
    groups = M.sess_day.to_numpy()
    strata = (M.session.astype(str) + "|" + M.mech.astype(str)).to_numpy()
    num_cols = [c for c in cols if c not in CAT_COLS]

    result = {"h": h}
    oof = {}
    for kind in ("lr", "gbm"):
        p = oof_proba(Xh, y, groups, kind, CAT_COLS, num_cols, n_folds)
        oof[kind] = p
        auc = roc_auc_score(y, p)
        result[f"auc_{kind}"] = auc
        # secondary target: real_out < 0 directly
        auc_real = roc_auc_score(M.is_real_loss.to_numpy(), p)
        result[f"auc_{kind}_realloss"] = auc_real
        result[f"spearman_{kind}_realout"] = spearmanr(p, M.real_out).statistic

    rng = np.random.default_rng(SEED)
    null_auc = {"lr": [], "gbm": []}
    for i in range(n_perm):
        yp = permute_within_strata(y, strata, rng)
        for kind in ("lr", "gbm"):
            pp = oof_proba(Xh, yp, groups, kind, CAT_COLS, num_cols, n_folds)
            null_auc[kind].append(roc_auc_score(yp, pp))
    for kind in ("lr", "gbm"):
        arr = np.array(null_auc[kind])
        result[f"null_mean_{kind}"] = arr.mean()
        result[f"null_lo_{kind}"] = np.percentile(arr, 2.5)
        result[f"null_hi_{kind}"] = np.percentile(arr, 97.5)
        result[f"null_p_{kind}"] = (arr >= result[f"auc_{kind}"]).mean()
        result[f"null_arr_{kind}"] = arr

    result["oof_lr"] = oof["lr"]
    result["oof_gbm"] = oof["gbm"]
    return result


# ---------------------------------------------------------------- POLICY ----

def tight_stop_book(M: pd.DataFrame, bars: pd.DataFrame, stop_r: float) -> pd.DataFrame:
    """Blanket tighter stop: same day_arrays/score_one machinery as the real
    exit (3R target, breakeven+trail runner), only the INITIAL stop distance
    changes to stop_r * original risk."""
    rows = []
    for day, sub in M.groupby("sess_day"):
        dd = day_arrays(bars, day)
        if dd is None:
            continue
        for r in sub.itertuples():
            d = int(r.direction)
            entry, risk = float(r.entry), float(r.risk)
            stop = entry - d * stop_r * risk
            res = score_one(dd, r.t, d, entry, stop, risk)
            if res is None:
                continue
            res["scid"] = r.scid
            rows.append(res)
    T = pd.DataFrame(rows)
    return M[["scid"]].merge(T[["scid", "real_out", "reached_3r"]], on="scid",
                              how="inner")


def policy_row(M: pd.DataFrame, h: int, oof_p: np.ndarray, thresh: float,
              label: str) -> dict:
    resolved = M[f"h{h}_resolved_early"].to_numpy()
    close_r = M[f"h{h}_close_r"].to_numpy()
    cost_r = M["cost_r"].to_numpy()
    flag = (oof_p > thresh) & (~resolved)
    policy_out = np.where(resolved, M.real_out.to_numpy(),
                          np.where(flag, close_r - cost_r, M.real_out.to_numpy()))
    policy_r3 = np.where(resolved, M.reached_3r.to_numpy(),
                         np.where(flag, False, M.reached_3r.to_numpy()))
    n_flagged = int(flag.sum())
    # of the flagged, how many were TRUE junk (run_mfe_r<0.5) vs cut runners
    junk_among_flagged = M.is_junk.to_numpy()[flag].mean() if n_flagged else np.nan
    cut_runners = int(((M.reached_3r.to_numpy()) & flag).sum())
    return dict(h=h, policy=label, thresh=thresh, n_flagged=n_flagged,
               flag_frac=flag.mean(), pct_junk_of_flagged=junk_among_flagged,
               runners_cut=cut_runners, ev=policy_out.mean(),
               p3r=policy_r3.mean(), sum_r=policy_out.sum())


def main() -> None:
    print("loading master frame...", flush=True)
    M = load_master()
    print(f"  {len(M)} fights, {M.sess_day.nunique()} days, "
          f"is_junk rate {M.is_junk.mean()*100:.1f}%, "
          f"real_out sum {M.real_out.sum():+.1f}R, mean {M.real_out.mean():+.4f}R")

    print("\n" + "=" * 100)
    print("PER-HORIZON MODEL FIT + PERMUTATION CALIBRATION")
    print("=" * 100)
    results = {}
    for h in HORIZONS:
        print(f"\n--- horizon {h}m ---", flush=True)
        res = run_horizon(M, h)
        results[h] = res
        print(f"  LR  OOF AUC {res['auc_lr']:.4f}  | null mean {res['null_mean_lr']:.4f} "
              f"[{res['null_lo_lr']:.4f},{res['null_hi_lr']:.4f}]  p={res['null_p_lr']:.3f}")
        print(f"  GBM OOF AUC {res['auc_gbm']:.4f}  | null mean {res['null_mean_gbm']:.4f} "
              f"[{res['null_lo_gbm']:.4f},{res['null_hi_gbm']:.4f}]  p={res['null_p_gbm']:.3f}")
        print(f"  vs real_out<0 : LR AUC {res['auc_lr_realloss']:.4f}  GBM AUC "
              f"{res['auc_gbm_realloss']:.4f}")
        print(f"  spearman(OOF p_junk, real_out): LR {res['spearman_lr_realout']:+.4f}  "
              f"GBM {res['spearman_gbm_realout']:+.4f}")

    # persist OOF predictions + AUC summary
    oof_frame = M[["scid", "sess_day", "session", "mech", "direction",
                   "is_junk", "is_real_loss", "run_mfe_r", "real_out",
                   "reached_3r", "cost_r"]].copy()
    for h in HORIZONS:
        oof_frame[f"h{h}_resolved_early"] = M[f"h{h}_resolved_early"]
        oof_frame[f"h{h}_close_r"] = M[f"h{h}_close_r"]
        oof_frame[f"h{h}_oof_lr"] = results[h]["oof_lr"]
        oof_frame[f"h{h}_oof_gbm"] = results[h]["oof_gbm"]
    oof_frame.to_parquet(CENSUS / "intrade_exit_oof.parquet", index=False)

    auc_rows = []
    for h in HORIZONS:
        r = results[h]
        for kind in ("lr", "gbm"):
            auc_rows.append(dict(h=h, model=kind, auc=r[f"auc_{kind}"],
                                 auc_realloss=r[f"auc_{kind}_realloss"],
                                 spearman_realout=r[f"spearman_{kind}_realout"],
                                 null_mean=r[f"null_mean_{kind}"],
                                 null_lo=r[f"null_lo_{kind}"],
                                 null_hi=r[f"null_hi_{kind}"],
                                 null_p=r[f"null_p_{kind}"]))
    AUC = pd.DataFrame(auc_rows)
    AUC.to_csv(CENSUS / "intrade_exit_auc.csv", index=False)
    print("\nwritten: intrade_exit_oof.parquet, intrade_exit_auc.csv")

    print("\n" + "=" * 100)
    print("BLANKET TIGHTER-STOP BASELINES (same 3R+trail engine, tighter initial stop)")
    print("=" * 100)
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close",
                                              "volume"]]
    tight = {}
    for sr in STOP_BLANKETS:
        T = tight_stop_book(M, bars, sr)
        tight[sr] = T
        print(f"  -{sr}R stop: n={len(T)}  EV {T.real_out.mean():+.4f}R  "
              f"sum {T.real_out.sum():+.1f}R  P(3R) {T.reached_3r.mean()*100:.1f}%")
    TW = pd.concat([T.assign(stop_r=sr) for sr, T in tight.items()])
    TW.to_parquet(CENSUS / "intrade_exit_tightstops.parquet", index=False)

    print("\n" + "=" * 100)
    print("THE POLICY TABLE — early-exit rule vs do-nothing vs blanket stops")
    print("=" * 100)
    do_nothing = dict(h=np.nan, policy="do_nothing", thresh=np.nan,
                      n_flagged=0, flag_frac=0.0, pct_junk_of_flagged=np.nan,
                      runners_cut=0, ev=M.real_out.mean(), p3r=M.reached_3r.mean(),
                      sum_r=M.real_out.sum())
    rows = [do_nothing]
    for sr, T in tight.items():
        rows.append(dict(h=np.nan, policy=f"blanket_-{sr}R", thresh=np.nan,
                         n_flagged=len(T), flag_frac=1.0,
                         pct_junk_of_flagged=np.nan, runners_cut=np.nan,
                         ev=T.real_out.mean(), p3r=T.reached_3r.mean(),
                         sum_r=T.real_out.sum()))
    THRESH_GRID = [0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75]
    for h in HORIZONS:
        for kind, col in (("lr", "oof_lr"), ("gbm", "oof_gbm")):
            p = results[h][col]
            for th in THRESH_GRID:
                rows.append(policy_row(M, h, p, th, f"h{h}_{kind}"))
    POL = pd.DataFrame(rows)
    POL.to_csv(CENSUS / "intrade_exit_policy.csv", index=False)
    print("written: intrade_exit_policy.csv, intrade_exit_tightstops.parquet")
    print(f"\ndo_nothing: EV {do_nothing['ev']:+.4f}R  sum {do_nothing['sum_r']:+.1f}R  "
          f"P(3R) {do_nothing['p3r']*100:.1f}%")

    # print best row per horizon per model (max EV) as a quick pointer
    print("\nbest EV row per horizon x model (by threshold sweep):")
    for h in HORIZONS:
        for kind in ("lr", "gbm"):
            sub = POL[(POL.h == h) & (POL.policy == f"h{h}_{kind}")]
            best = sub.loc[sub.ev.idxmax()]
            print(f"  h={h:2d} {kind:3s} best@thresh={best.thresh:.2f}  "
                  f"flag_frac={best.flag_frac*100:5.1f}%  EV {best.ev:+.4f}R  "
                  f"P(3R) {best.p3r*100:5.1f}%  runners_cut={int(best.runners_cut)}")


if __name__ == "__main__":
    main()
