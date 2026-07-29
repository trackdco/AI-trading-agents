#!/usr/bin/env python3
"""CONFLUENCE STUDY — the FROZEN pipeline. Imported by every runner; never edited mid-run.

DETERMINISTIC. No LLM adjusts weights, thresholds, or feature selection at any point. Every
constant below is frozen before the first fit.

FEATURE POOL (13) — frozen 2026-07-29 after exchangeability gating:
  existing (9): cvd_5 cvd_15 cvd_30 cvd_norm_15 abs_cvd_15 delta_div_15[LOW-POWER]
                absorp_rel vol_15_rel vol_30_rel
  plus       : gap_abs
  new (3)    : ec_delta ec_fp_imb ec_aggr_flip      (ec_delta_hi_lo EXCLUDED: failed
               exchangeability KS 0.264 p 0.008 — excluded, not remedied)
  EXCLUDED   : stack_bid_*, stack_ask_* (failed exchangeability in Part 1)

COMBINATION — ONE family only. Rank-normalised weighted composite; weights by RIDGE against
realised R; penalty chosen INSIDE each fold from a fixed grid by 3-fold CV on the training
trades only. No trees, no boosting, no interactions — now or later.

WALK-FORWARD — expanding window, daily. For trading day D: fit on every trade strictly before
D, score D's trades, advance. Nothing about D or later touches the fit. Predictions begin once
MIN_TRAIN trades exist.

HEADLINE METRIC — Spearman rank correlation between walk-forward prediction and realised R over
all predicted trades. Every walk-forward prediction is out-of-sample by construction.
"""
import numpy as np
import pandas as pd

POOL = ["cvd_5", "cvd_15", "cvd_30", "cvd_norm_15", "abs_cvd_15", "delta_div_15",
        "absorp_rel", "vol_15_rel", "vol_30_rel", "gap_abs",
        "ec_delta", "ec_fp_imb", "ec_aggr_flip"]
# unsigned magnitudes only -> falsifier (a): if this matches the signed composite there is no
# directional information in the pool.
BLIND = ["abs_cvd_15", "absorp_rel", "vol_15_rel", "vol_30_rel", "gap_abs"]
PENALTIES = (0.01, 0.1, 1.0, 10.0, 100.0, 1000.0)
MIN_TRAIN = 40
INNER_FOLDS = 3


def load(repo="/home/user/AI-trading-agents"):
    src = f"{repo}/research/sweep_2026_07/orderflow"
    conf = f"{repo}/research/sweep_2026_07/confluence"
    F = pd.read_csv(f"{src}/part1_features.csv")
    E = pd.read_csv(f"{conf}/entry_candle_features.csv")
    F["ft"] = pd.to_datetime(F.ft, utc=True).astype(str)
    E["ft"] = pd.to_datetime(E.ft, utc=True).astype(str)
    P0 = pd.read_csv(f"{src}/part0_frame.csv")
    P0["ft"] = pd.to_datetime(P0.ft, utc=True).astype(str)
    # `ft` is NOT unique — two books can fill the same minute with different stops — so a
    # key-merge duplicates rows. All three frames were built row-for-row by iterating
    # part0_frame in its own order, so they are concatenated POSITIONALLY and the row
    # correspondence is asserted, not assumed.
    F, E, P0 = (d.reset_index(drop=True) for d in (F, E, P0))
    assert len(F) == len(E) == len(P0), (len(F), len(E), len(P0))
    assert (F.ft.values == E.ft.values).all() and (F.day.values == E.day.values).all()
    assert (F.ft.values == P0.ft.values).all() and (F.day.values == P0.day.values).all()
    ec = [c for c in E.columns if c.startswith("ec_")]
    J = pd.concat([F, E[ec], P0[["micros", "life_min", "mfe_R", "direction"]]], axis=1)
    return J.reset_index(drop=True)


def rank_norm(train_col, apply_col):
    """Map values onto their percentile in the TRAINING distribution, centred at 0.
    Fitted on train only; NaN -> 0 (the centre), so a missing feature is neutral."""
    t = train_col[np.isfinite(train_col)]
    if len(t) < 5:
        return np.zeros_like(apply_col, dtype=float)
    q = np.searchsorted(np.sort(t), apply_col, side="right") / len(t)
    q = np.where(np.isfinite(apply_col), q - 0.5, 0.0)
    return q


def ridge_fit(X, y, lam):
    """Closed-form ridge on centred data. Returns (w, x_mean, y_mean)."""
    xm, ym = X.mean(axis=0), y.mean()
    Xc, yc = X - xm, y - ym
    n_f = X.shape[1]
    A = Xc.T @ Xc + lam * np.eye(n_f)
    try:
        w = np.linalg.solve(A, Xc.T @ yc)
    except np.linalg.LinAlgError:
        w = np.linalg.lstsq(A, Xc.T @ yc, rcond=None)[0]
    return w, xm, ym


def pick_penalty(X, y, rs):
    """3-fold CV over the FIXED penalty grid, inside the training set only."""
    n = len(y)
    if n < INNER_FOLDS * 4:
        return 1.0
    idx = rs.permutation(n)
    folds = np.array_split(idx, INNER_FOLDS)
    best, best_lam = np.inf, 1.0
    for lam in PENALTIES:
        err = 0.0
        for k in range(INNER_FOLDS):
            te = folds[k]
            tr = np.concatenate([folds[j] for j in range(INNER_FOLDS) if j != k])
            w, xm, ym = ridge_fit(X[tr], y[tr], lam)
            pred = (X[te] - xm) @ w + ym
            err += float(np.sum((pred - y[te]) ** 2))
        if err < best:
            best, best_lam = err, lam
    return best_lam


def walk_forward(J, feats, y_col="R", y_override=None, weights=None, seed=0):
    """Expanding-window daily walk-forward. Returns a frame of OOS predictions.

    weights=None      -> ridge-fitted composite (the registered method)
    weights='random'  -> random weights on the rank-normalised features (falsifier c)
    """
    rs = np.random.default_rng(seed)
    y_all = np.asarray(J[y_col].values if y_override is None else y_override, dtype=float)
    days = J.day.values
    u_days = pd.unique(days)
    raw = {f: J[f].values.astype(float) for f in feats}
    out_i, out_p = [], []
    for d in u_days:
        te = np.flatnonzero(days == d)
        tr = np.flatnonzero(days < d)
        if len(tr) < MIN_TRAIN:
            continue
        Xtr = np.column_stack([rank_norm(raw[f][tr], raw[f][tr]) for f in feats])
        Xte = np.column_stack([rank_norm(raw[f][tr], raw[f][te]) for f in feats])
        ytr = y_all[tr]
        if weights == "random":
            w = rs.normal(size=len(feats))
            pred = Xte @ w
        else:
            lam = pick_penalty(Xtr, ytr, rs)
            w, xm, ym = ridge_fit(Xtr, ytr, lam)
            pred = (Xte - xm) @ w + ym
        out_i.append(te)
        out_p.append(pred)
    if not out_i:
        return pd.DataFrame(columns=["i", "pred"])
    i = np.concatenate(out_i)
    p = np.concatenate(out_p)
    return pd.DataFrame(dict(i=i, pred=p))


def spearman(a, b):
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 8:
        return np.nan
    a, b = a[m], b[m]
    ra = np.array(pd.Series(a).rank().to_numpy(), dtype=float, copy=True)
    rb = np.array(pd.Series(b).rank().to_numpy(), dtype=float, copy=True)
    ra -= ra.mean()
    rb -= rb.mean()
    den = np.sqrt((ra ** 2).sum() * (rb ** 2).sum())
    return float((ra * rb).sum() / den) if den > 0 else np.nan


def headline(J, W, y_override=None):
    """Spearman(prediction, realised R) over all walk-forward predictions."""
    if not len(W):
        return np.nan
    y = np.asarray(J["R"].values if y_override is None else y_override, dtype=float)
    return spearman(W.pred.values, y[W.i.values])


def block_shuffle(J, rs):
    """Permute outcomes in DAY BLOCKS to preserve within-day clustering.

    Each day's outcome vector is kept intact as a block; the ORDER of the blocks is shuffled and
    the concatenated stream is reassigned positionally down the chronological trade list. The
    multiset of outcomes is preserved exactly — no duplication, no loss — while the
    feature->outcome link is broken at day granularity.
    """
    days = J.day.values
    u = pd.unique(days)
    blocks = [J.R.values[days == d] for d in u]
    order = rs.permutation(len(blocks))
    stream = np.concatenate([blocks[k] for k in order])
    return stream
