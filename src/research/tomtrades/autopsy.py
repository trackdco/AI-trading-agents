"""Loser autopsy: can a winner be told from a loser at the moment of entry?

The question has a precise form here, because the simulator's losses are all exactly
-1R (the stop is a fill at a known price, no gaps or slippage modelled). So

    EV = p * E[RR | win] - (1 - p)

and RR is *knowable at entry* — it is |target - entry| / risk, fixed the moment the
order goes in. That gives the autopsy two separate handles, and confusing them is the
easiest way to fool yourself:

  (a) does anything predict **p**, the probability of reaching the target first?
  (b) does anything predict **RR**, the size of the win?

(b) is trivially yes: RR is a deterministic function of entry-time quantities. It is
NOT a finding. The only question that matters is whether p is INDEPENDENT of RR — if
it is, selecting high-RR trades is free and the arithmetic can be fixed; if p falls as
RR rises, there is no escape by selection and the geometry itself has to change.

Rules this module obeys, all of them from the repo's own base-rate history:

  BR-41  Post-entry variables are partly the outcome. ``hold_bars``, ``mfe_r``,
         ``mae_r`` and ``exit_reason`` appear here only as ANATOMY, and are never
         offered to a predictor. They are labelled in ``FEATURES`` with
         ``actionable=False`` and the model builder refuses them.
  Law 2  Risk-coupled features are flagged, not silently used. ``risk`` is the
         denominator of every R, so anything built from it shares an axis with the
         outcome. Flagged features are reported and also excluded in a ``_clean`` run.
  Law 3  Dual currency. A win-rate move that costs EV is a refutation, not a finding,
         so every table carries both.
  BR-42  Day-clustered resampling. Trades cluster inside sessions; i.i.d. intervals
         overstate confidence.
  BR-97  Permutation calibration is the gate, not the p-value from a formula. The
         survival machinery passes roughly 5% of pure noise, so every headline number
         is run against shuffled outcomes and reported next to that null.

Nothing in here tunes a parameter. Where a rule variant is priced (the breakeven stop,
the cost ladder) it is priced as a variant and reported with the size of the menu it
was chosen from.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import gates as G
from . import indicators as ind

SEED = 20260813
DRAWS = 2000
MIN_N = 30          # below this, counts only — no interpretation


# --------------------------------------------------------------------------- features
@dataclass(frozen=True)
class Feature:
    name: str
    kind: str            # "cont" | "bin" | "cat"
    law2: bool           # shares an axis with risk, the R denominator
    actionable: bool     # False = post-entry, anatomy only (BR-41)
    note: str


FEATURES: tuple[Feature, ...] = (
    # --- shape of the setup ------------------------------------------------------
    Feature("run_displacement", "cont", False, True, "size of the hourly run being faded"),
    Feature("disp_atr", "cont", False, True, "same, in ATR units"),
    Feature("run_minutes", "cont", False, True, "minutes of one-way run at the signal (C2)"),
    Feature("retrace_frac", "cont", False, True, "give-back off the run extreme at signal (C2)"),
    Feature("sweep_depth", "cont", False, True, "how far past the swept swing price ran"),
    Feature("sweep_depth_atr", "cont", False, True, "same, in ATR units"),
    Feature("bars_since_arm", "cont", False, True, "bars from sweep to shift confirmation"),
    Feature("break_dist_atr", "cont", False, True, "how far the break bar closed past the level"),
    Feature("bar_range_atr", "cont", False, True, "size of the trigger candle"),
    Feature("nested", "bin", False, True, "C7 approximation: sub-shift inside the retrace"),
    # --- context -----------------------------------------------------------------
    Feature("c1_value", "cont", False, True, "C1 mean-retracement, continuous (range-ness)"),
    Feature("dist_boundary_atr", "cont", False, True, "distance from the 8h range edge (C5)"),
    Feature("atr_1h", "cont", False, True, "volatility regime"),
    Feature("vol_z", "cont", False, True, "trigger-bar volume vs its trailing 60-bar mean"),
    Feature("minute_of_hour", "cont", False, True, "C3, his clock"),
    Feature("hour_ny", "cat", False, True, "hour of the NY day"),
    Feature("dow", "cat", False, True, "day of week"),
    Feature("is_long", "bin", False, True, "direction of the fade"),
    # --- risk-coupled (Law 2) ------------------------------------------------------
    Feature("risk_pts", "cont", True, True, "stop distance in points — the R denominator"),
    Feature("risk_atr", "cont", True, True, "stop distance in ATR units"),
    Feature("rr_at_entry", "cont", True, True, "payoff if it wins; NOT a predictor of p"),
    # --- anatomy only (BR-41) ------------------------------------------------------
    Feature("entry_slip_r", "cont", True, False, "fill gap vs signal close — known too late"),
    Feature("hold_bars", "cont", False, False, "post-entry"),
    Feature("mfe_r", "cont", False, False, "post-entry"),
    Feature("mae_r", "cont", False, False, "post-entry"),
)

MODEL_COLS = [f.name for f in FEATURES if f.actionable and f.kind != "cat"]
CLEAN_COLS = [f.name for f in FEATURES if f.actionable and f.kind != "cat" and not f.law2]


def _session_of(hour_ny: np.ndarray) -> np.ndarray:
    """A non-overlapping partition of the clock, for permutation cells only.

    The config's asia/london windows overlap by an hour; a permutation null needs
    disjoint cells, so this is a coarser split and is used for nothing else.
    """
    out = np.full(len(hour_ny), "other", dtype=object)
    out[(hour_ny >= 19) | (hour_ny <= 2)] = "asia"
    out[(hour_ny >= 3) & (hour_ny <= 7)] = "london"
    out[(hour_ny >= 8) & (hour_ny <= 16)] = "ny"
    return out


def annotate(trades: pd.DataFrame, df: pd.DataFrame, ctx, cfg: dict) -> pd.DataFrame:
    """Attach every entry-time feature to the trade rows.

    Everything is read at ``signal_idx`` — the bar whose close confirmed the shift —
    except the fill itself. No column here consults a bar after the signal, which is
    what makes the separation question answerable rather than circular.
    """
    B = trades.copy().reset_index(drop=True)
    si = B["signal_idx"].to_numpy().astype(int)

    atr = np.nan_to_num(ctx.atr_1h_min.to_numpy(), nan=np.nan)[si]
    B["atr_1h"] = atr
    B["disp_atr"] = B["run_displacement"].to_numpy() / atr
    B["sweep_depth_atr"] = B["sweep_depth"].to_numpy() / atr
    B["break_dist_atr"] = B["break_dist"].to_numpy() / atr
    B["risk_pts"] = B["risk"].to_numpy()
    B["risk_atr"] = B["risk"].to_numpy() / atr

    st = ctx.state
    B["run_minutes"] = st["run_minutes"].to_numpy()[si]
    B["retrace_frac"] = st["retrace_frac"].to_numpy()[si]

    rng = (df["high"].to_numpy() - df["low"].to_numpy())[si]
    B["bar_range_atr"] = rng / atr

    vol = df["volume"].to_numpy().astype(float)
    v_mu = pd.Series(vol).rolling(60, min_periods=20).mean().to_numpy()
    v_sd = pd.Series(vol).rolling(60, min_periods=20).std().to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        vz = (vol - v_mu) / v_sd
    B["vol_z"] = vz[si]

    c1 = G.c1_value_series(df, cfg["c1_range"])
    B["c1_value"] = c1.reindex(df["ts_event"], method="ffill").to_numpy()[si]

    hourly = ind.resample_ohlcv(df, "1h")
    hi = hourly["high"].rolling(8, min_periods=2).max().shift()
    lo = hourly["low"].rolling(8, min_periods=2).min().shift()
    hi_m = pd.Series(hi.to_numpy(), index=hourly["ts_event"]).reindex(
        df["ts_event"], method="ffill").to_numpy()[si]
    lo_m = pd.Series(lo.to_numpy(), index=hourly["ts_event"]).reindex(
        df["ts_event"], method="ffill").to_numpy()[si]
    ext = B["pattern_ext"].to_numpy()
    d = B["direction"].to_numpy()
    # a short fades an up-run, so its reference edge is the range HIGH
    edge = np.where(d < 0, hi_m, lo_m)
    B["dist_boundary_atr"] = np.abs(ext - edge) / atr

    B["is_long"] = (d > 0).astype(int)
    B["entry_slip_r"] = d * (B["entry"].to_numpy() - B["entry_ref_close"].to_numpy()) / B["risk"]

    ny = pd.to_datetime(B["entry_ts"]).dt.tz_convert("America/New_York")
    B["hour_ny"] = ny.dt.hour
    B["dow"] = ny.dt.dayofweek
    B["sess_day"] = ny.dt.date
    B["year"] = ny.dt.year
    B["session"] = _session_of(B["hour_ny"].to_numpy())
    # Permutation cells are SESSION ONLY. The base-rate library strafifies by
    # (session, mech) because there `mech` is a nuisance stratum; here direction is a
    # feature under test, and putting it in the cell definition would make its own
    # effect unfalsifiable — the null would preserve the per-direction outcome
    # distribution exactly, so every shuffle would reproduce it. Held constant instead,
    # which keeps the grouping code identical and leaves direction testable.
    B["mech"] = "cbr"
    B["mech_dir"] = np.where(d > 0, "long", "short")   # label for reporting only

    B["out"] = B["pnl_r"].astype(float)
    B["win"] = (B["out"] > 0).astype(float)
    return B


# ------------------------------------------------------------------ small statistics
def _rank(x: np.ndarray) -> np.ndarray:
    """Average ranks, NaN-safe (NaNs get the mean rank, i.e. no signal)."""
    x = np.asarray(x, dtype=float)
    ok = ~np.isnan(x)
    r = np.full(len(x), (ok.sum() + 1) / 2.0)
    if ok.sum() == 0:
        return r
    s = pd.Series(x[ok]).rank(method="average").to_numpy()
    r[ok] = s
    return r


def spearman(x, y) -> float:
    rx, ry = _rank(x), _rank(y)
    sx, sy = rx.std(), ry.std()
    if sx == 0 or sy == 0:
        return np.nan
    return float(np.mean((rx - rx.mean()) * (ry - ry.mean())) / (sx * sy))


def auc(y: np.ndarray, score: np.ndarray) -> float:
    """P(score of a winner > score of a loser), ties counted as half."""
    y = np.asarray(y).astype(bool)
    n1, n0 = int(y.sum()), int((~y).sum())
    if n1 == 0 or n0 == 0:
        return np.nan
    r = _rank(score)
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def dboot_mean(df: pd.DataFrame, col: str, draws: int = DRAWS, seed: int = SEED):
    """Day-clustered bootstrap CI for a mean (BR-42): resample DAYS, not trades."""
    g = df.groupby("sess_day")[col].agg(["sum", "count"])
    s, n = g["sum"].to_numpy(), g["count"].to_numpy()
    if len(s) < 3:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    i = rng.integers(0, len(s), (draws, len(s)))
    c = n[i].sum(1)
    st = np.divide(s[i].sum(1), c, out=np.full(draws, np.nan), where=c > 0)
    return float(np.nanpercentile(st, 2.5)), float(np.nanpercentile(st, 97.5))


def permute(B: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Null: shuffle the OUTCOME within each (session, mech) cell.

    Every feature, every cell size and the outcome distribution survive; only the
    pairing between a trade's features and its result is destroyed. Same construction
    as ``scripts/conviction_lib.permute`` — deliberately, so results are comparable
    with the base-rate book.
    """
    rng = np.random.default_rng(seed)
    Bn = B.reset_index(drop=True).copy()
    for idx in Bn.groupby(["session", "mech"]).groups.values():
        idx = np.asarray(idx)
        if len(idx) < 2:
            continue
        perm = rng.permutation(idx)
        for c in ("out", "win"):
            Bn.loc[idx, c] = Bn.loc[perm, c].to_numpy()
    return Bn


def _pval(real: float, null: np.ndarray) -> float:
    """Two-sided empirical p with the +1 correction, so it is never reported as zero."""
    ok = null[~np.isnan(null)]
    if not len(ok) or np.isnan(real):
        return np.nan
    return (1 + int((np.abs(ok) >= abs(real)).sum())) / (1 + len(ok))


def calibrate_many(fns: dict, B: pd.DataFrame, n_perm: int = 200, base: int = 900000):
    """Calibrate a whole battery against ONE set of shuffles.

    Every statistic sees the same nulls, which is both far cheaper — the shuffle, not
    the statistic, is the expensive part — and more honest: the family of tests is
    evaluated against a common null rather than each against its own private draw.
    Returns {name: (real, null_array, p)}.
    """
    real = {k: float(f(B)) for k, f in fns.items()}
    nulls = {k: [] for k in fns}
    for i in range(n_perm):
        Bn = permute(B, base + i)
        for k, f in fns.items():
            try:
                nulls[k].append(float(f(Bn)))
            except (ValueError, ZeroDivisionError, np.linalg.LinAlgError):
                # a shuffle can leave a cell degenerate; that is a NaN draw
                nulls[k].append(np.nan)
    return {k: (real[k], np.array(nulls[k], dtype=float),
                _pval(real[k], np.array(nulls[k], dtype=float))) for k in fns}


def calibrate(fn, B: pd.DataFrame, n_perm: int = 200, base: int = 900000):
    """Single-statistic form of :func:`calibrate_many`. Returns (real, null, p)."""
    return calibrate_many({"_": fn}, B, n_perm=n_perm, base=base)["_"]


# ------------------------------------------------------------------------- the tables
def bucket_table(B: pd.DataFrame, feat: str, q: int = 5, min_n: int = MIN_N) -> pd.DataFrame:
    """Dual-currency profile of one feature, with day-clustered CIs on EV."""
    x = B[feat]
    if B[feat].nunique(dropna=True) <= max(6, q):
        b = x.astype("object").where(x.notna(), "na")
    else:
        b = pd.qcut(x, q, duplicates="drop")
    rows = []
    for lvl, gl in B.groupby(b, observed=True):
        lo, hi = dboot_mean(gl, "out") if len(gl) >= min_n else (np.nan, np.nan)
        rows.append({"bucket": str(lvl), "n": len(gl), "days": gl["sess_day"].nunique(),
                     "mean_x": float(pd.to_numeric(gl[feat], errors="coerce").mean()),
                     "win_pct": 100 * float(gl["win"].mean()),
                     "ev": float(gl["out"].mean()), "ev_lo": lo, "ev_hi": hi,
                     "thin": len(gl) < min_n})
    return pd.DataFrame(rows)


def univariate(B: pd.DataFrame, feats=None, n_perm: int = 200) -> pd.DataFrame:
    """One row per feature: how hard does it separate, and does the null do as well?

    Two currencies, each calibrated. ``rho_win`` is the rank correlation with the
    win/loss bit; ``rho_ev`` with the realised R. A feature that moves win rate but not
    EV has not found an edge — it has found a cheaper win.
    """
    feats = feats or [f for f in FEATURES if f.actionable]
    use = [f for f in feats
           if f.name in B.columns
           and not np.all(np.isnan(B[f.name].to_numpy(dtype=float)))
           and np.nanstd(B[f.name].to_numpy(dtype=float)) > 0]
    fns = {}
    for f in use:
        fns[f"win|{f.name}"] = (lambda d, c=f.name:
                                spearman(d[c].to_numpy(dtype=float), d["win"].to_numpy()))
        fns[f"ev|{f.name}"] = (lambda d, c=f.name:
                               spearman(d[c].to_numpy(dtype=float), d["out"].to_numpy()))
    cal = calibrate_many(fns, B, n_perm=n_perm)
    rows = []
    for f in use:
        rw, nullw, pw = cal[f"win|{f.name}"]
        re_, nulle, pe = cal[f"ev|{f.name}"]
        x = B[f.name].to_numpy(dtype=float)
        rows.append({"feature": f.name, "law2": f.law2, "n": int((~np.isnan(x)).sum()),
                     "rho_win": rw, "p_win": pw, "null_win_sd": float(np.nanstd(nullw)),
                     "rho_ev": re_, "p_ev": pe, "null_ev_sd": float(np.nanstd(nulle)),
                     "note": f.note})
    out = pd.DataFrame(rows)
    # A family of this size throws survivors on its own: the Benjamini-Hochberg
    # threshold is what a p-value has to beat before it is worth a second look.
    m = len(out)
    out = out.sort_values("p_ev").reset_index(drop=True)
    out["bh_thresh_ev"] = [(i + 1) / m * 0.10 for i in range(m)]
    out["survives_ev"] = out["p_ev"] <= out["bh_thresh_ev"]
    return out


# -------------------------------------------------------------- the multivariate test
def _fit_logit(X: np.ndarray, y: np.ndarray, l2: float = 1.0, iters: int = 60) -> np.ndarray:
    """Ridge-penalised logistic regression by IRLS. The intercept is not penalised."""
    A = np.column_stack([np.ones(len(X)), X])
    w = np.zeros(A.shape[1])
    P = np.eye(A.shape[1]) * l2
    P[0, 0] = 0.0
    for _ in range(iters):
        p = 1.0 / (1.0 + np.exp(-np.clip(A @ w, -30, 30)))
        W = p * (1 - p) + 1e-9
        g = A.T @ (y - p) - P @ w
        H = (A.T * W) @ A + P
        try:
            step = np.linalg.solve(H, g)
        except np.linalg.LinAlgError:
            step = np.linalg.lstsq(H, g, rcond=None)[0]
        w += step
        if np.max(np.abs(step)) < 1e-9:
            break
    return w


def _prep(X: pd.DataFrame) -> np.ndarray:
    """Median-impute and clip, so one wild ATR ratio cannot dominate a fit."""
    A = X.to_numpy(dtype=float).copy()
    for j in range(A.shape[1]):
        col = A[:, j]
        med = np.nanmedian(col)
        col[np.isnan(col)] = med if not np.isnan(med) else 0.0
        lo, hi = np.nanpercentile(col, [1, 99])
        A[:, j] = np.clip(col, lo, hi)
    return A


def day_folds(B: pd.DataFrame, folds: int = 5, seed: int = SEED) -> np.ndarray:
    """Assign every trade a fold via its DAY, so a day is never on both sides."""
    days = np.array(sorted(B["sess_day"].unique()))
    rng = np.random.default_rng(seed)
    fold_of = dict(zip(days, rng.permutation(len(days)) % folds))
    return B["sess_day"].map(fold_of).to_numpy()


def oos_predictions(B: pd.DataFrame, cols: list[str], folds: int = 5,
                    seed: int = SEED, l2: float = 1.0) -> np.ndarray:
    """Out-of-sample P(win), with folds split by DAY so no day is in both sides.

    Splitting by trade would let a model learn "this day was good" from one of its own
    trades and score the rest — the classic way an intraday backtest reports an AUC it
    cannot reproduce live.
    """
    fold = day_folds(B, folds=folds, seed=seed)
    X = _prep(B[cols])
    y = B["win"].to_numpy(dtype=float)
    pred = np.full(len(B), np.nan)
    for k in range(folds):
        tr, te = fold != k, fold == k
        if tr.sum() < 50 or te.sum() == 0:
            continue
        mu, sd = X[tr].mean(0), X[tr].std(0)
        sd[sd == 0] = 1.0
        w = _fit_logit((X[tr] - mu) / sd, y[tr], l2=l2)
        z = np.column_stack([np.ones(te.sum()), (X[te] - mu) / sd]) @ w
        pred[te] = 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))
    return pred


def oos_auc(B: pd.DataFrame, cols: list[str], folds: int = 5, seed: int = SEED) -> float:
    return _auc_from(B, oos_predictions(B, cols, folds=folds, seed=seed))


def _auc_from(B: pd.DataFrame, p: np.ndarray) -> float:
    ok = ~np.isnan(p)
    return auc(B["win"].to_numpy()[ok].astype(bool), p[ok])


def oos_auc_within(B: pd.DataFrame, cols: list[str], strat: str = "rr_at_entry",
                   q: int = 5, folds: int = 5, seed: int = SEED) -> float:
    """AUC pooled WITHIN strata of ``strat``, weighted by each stratum's pair count.

    A model told "the target is close" will score a high headline AUC without knowing
    anything useful, because near targets are hit more often and pay less. Holding
    reward:risk fixed asks the sharper question: among trades that pay the same, can it
    still pick the winners?
    """
    return _auc_within_from(B, oos_predictions(B, cols, folds=folds, seed=seed), strat, q)


def _auc_within_from(B: pd.DataFrame, p: np.ndarray, strat: str, q: int) -> float:
    d = B.assign(_p=p).dropna(subset=["_p"])
    b = pd.qcut(d[strat], q, duplicates="drop")
    num = den = 0.0
    for _, gl in d.groupby(b, observed=True):
        y = gl["win"].to_numpy().astype(bool)
        n1, n0 = int(y.sum()), int((~y).sum())
        if n1 == 0 or n0 == 0:
            continue
        a = auc(y, gl["_p"].to_numpy())
        num += a * n1 * n0
        den += n1 * n0
    return float(num / den) if den else np.nan


def top_bin_ev(B: pd.DataFrame, cols: list[str], bins: int = 5,
               folds: int = 5, seed: int = SEED) -> float:
    """Realised EV of the trades the model would actually have taken.

    This is the decision statistic: rank by out-of-sample expected value, keep the top
    bin, and report what it made. Calibrated against shuffled outcomes it answers the
    only question the user cares about — is there a findable subset that pays?
    """
    return _top_bin_from(B, oos_predictions(B, cols, folds=folds, seed=seed), bins)


def _top_bin_from(B: pd.DataFrame, p: np.ndarray, bins: int) -> float:
    rr = B["rr_at_entry"].to_numpy(dtype=float)
    d = B.assign(_evhat=p * rr - (1 - p)).dropna(subset=["_evhat"])
    if len(d) < bins * 5:
        return np.nan
    cut = np.nanpercentile(d["_evhat"], 100 * (1 - 1 / bins))
    top = d[d["_evhat"] >= cut]
    return float(top["out"].mean()) if len(top) else np.nan


def model_stats(B: pd.DataFrame, cols: list[str], bins: int = 5, folds: int = 5,
                seed: int = SEED) -> dict:
    """All three model verdicts off ONE cross-validation, so a null costs one fit."""
    p = oos_predictions(B, cols, folds=folds, seed=seed)
    return {"auc": _auc_from(B, p),
            "auc_within_rr": _auc_within_from(B, p, "rr_at_entry", bins),
            "top_bin_ev": _top_bin_from(B, p, bins)}


def calibrate_dict(fn, B: pd.DataFrame, n_perm: int = 40, base: int = 900000):
    """:func:`calibrate_many` for a function that returns several statistics at once."""
    real = fn(B)
    nulls: dict[str, list] = {k: [] for k in real}
    for i in range(n_perm):
        r = fn(permute(B, base + i))
        for k in real:
            nulls[k].append(float(r.get(k, np.nan)))
    return {k: (real[k], np.array(nulls[k], dtype=float),
                _pval(real[k], np.array(nulls[k], dtype=float))) for k in real}


def selection_table(B: pd.DataFrame, cols: list[str], bins: int = 5,
                    folds: int = 5, seed: int = SEED) -> pd.DataFrame:
    """Rank trades by out-of-sample expected value and see whether the top bin pays.

    EV-hat uses each trade's OWN reward:risk, which is known at entry, so this is the
    real decision: given what I can see now, is this trade worth taking?
    """
    p = oos_predictions(B, cols, folds=folds, seed=seed)
    rr = B["rr_at_entry"].to_numpy(dtype=float)
    ev_hat = p * rr - (1 - p)
    d = B.assign(_p=p, _evhat=ev_hat).dropna(subset=["_evhat"])
    b = pd.qcut(d["_evhat"], bins, duplicates="drop")
    rows = []
    for lvl, gl in d.groupby(b, observed=True):
        lo, hi = dboot_mean(gl, "out")
        rows.append({"ev_hat_bin": str(lvl), "n": len(gl), "days": gl["sess_day"].nunique(),
                     "pred_ev": float(gl["_evhat"].mean()),
                     "win_pct": 100 * float(gl["win"].mean()),
                     "realised_ev": float(gl["out"].mean()), "ev_lo": lo, "ev_hi": hi})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------- the anatomy
def arithmetic(B: pd.DataFrame) -> dict:
    """The identity the whole strategy lives or dies on, spelled out."""
    w = B[B["out"] > 0]["out"]
    losses = B[B["out"] <= 0]["out"]
    p = float((B["out"] > 0).mean())
    mw = float(w.mean()) if len(w) else np.nan
    ml = float(losses.mean()) if len(losses) else np.nan
    return {
        "n": len(B), "days": int(B["sess_day"].nunique()),
        "win_pct": 100 * p, "mean_win_r": mw, "mean_loss_r": ml,
        "ev": float(B["out"].mean()),
        "ev_check": p * mw + (1 - p) * ml,
        "breakeven_win_pct": 100 * (-ml) / (mw - ml) if mw > ml else np.nan,
        "breakeven_mean_win_r": (1 - p) * (-ml) / p if p > 0 else np.nan,
        "mean_rr_at_entry": float(B["rr_at_entry"].mean()),
        "median_rr_at_entry": float(B["rr_at_entry"].median()),
        "pct_rr_below_1": 100 * float((B["rr_at_entry"] < 1).mean()),
    }


def exit_census(B: pd.DataFrame) -> pd.DataFrame:
    g = B.groupby("exit_reason")
    return pd.DataFrame({
        "n": g.size(), "share_pct": 100 * g.size() / len(B),
        "mean_r": g["out"].mean(), "median_hold_min": g["hold_bars"].median(),
    }).reset_index()


def loser_excursions(B: pd.DataFrame, levels=(0.1, 0.2, 0.3, 0.4, 0.5)) -> pd.DataFrame:
    """How far into profit the losers travelled before dying (BR-41: anatomy only).

    This does not license a filter — MFE is not known at entry. It prices the question
    "was the stop ever safe?", which is a question about the exit rule, and the exit
    rule can then be re-simulated honestly.
    """
    losers = B[B["out"] <= 0]
    rows = [{"reached_r": lv, "pct_of_losers": 100 * float((losers["mfe_r"] >= lv).mean()),
             "n": int((losers["mfe_r"] >= lv).sum())} for lv in levels]
    return pd.DataFrame(rows)


def cost_ladder(B: pd.DataFrame, tick: float, ticks=(0, 1, 2, 3), commission_pts: float = 0.0):
    """Realised EV net of a round-turn cost, expressed per trade.

    Cost bites in R, and R is scaled by each trade's own stop distance, so a tick costs
    more on the tight-stop trades. Charging a flat R haircut would understate it.
    """
    rows = []
    risk = B["risk"].to_numpy(dtype=float)
    out = B["out"].to_numpy(dtype=float)
    for t in ticks:
        c = (t * tick + commission_pts) / risk
        rows.append({"cost_ticks_round_turn": t,
                     "mean_cost_r": float(np.mean(c)),
                     "ev_net": float(np.mean(out - c)),
                     "win_pct_net": 100 * float(np.mean((out - c) > 0))})
    return pd.DataFrame(rows)


def split_half(B: pd.DataFrame, col: str = "out") -> tuple[float, float]:
    """EV in the first and second half of the sample, split on the day axis.

    The cheapest guard against a rule variant that only worked in one regime. Not a
    holdout — the variant menu was chosen with both halves visible — but a variant that
    flips sign between halves is dead regardless.
    """
    days = np.array(sorted(B["sess_day"].unique()))
    if len(days) < 4:
        return np.nan, np.nan
    mid = days[len(days) // 2]
    a = B[B["sess_day"] < mid][col]
    b = B[B["sess_day"] >= mid][col]
    return (float(a.mean()) if len(a) else np.nan,
            float(b.mean()) if len(b) else np.nan)


def category_table(B: pd.DataFrame, col: str) -> pd.DataFrame:
    """Plain cell means with day-clustered CIs, for the strata the null cannot see.

    The permutation shuffles WITHIN session, so a session main effect survives every
    shuffle by construction and its p-value would be meaningless. Those effects are
    reported here as intervals instead, and read as intervals.
    """
    rows = []
    for lvl, gl in B.groupby(col, observed=True):
        lo, hi = dboot_mean(gl, "out")
        rows.append({col: lvl, "n": len(gl), "days": gl["sess_day"].nunique(),
                     "win_pct": 100 * float(gl["win"].mean()),
                     "ev": float(gl["out"].mean()), "ev_lo": lo, "ev_hi": hi,
                     "thin": len(gl) < MIN_N})
    return pd.DataFrame(rows)


def stability(B: pd.DataFrame, by: str = "year") -> pd.DataFrame:
    rows = []
    for lvl, gl in B.groupby(by):
        lo, hi = dboot_mean(gl, "out")
        rows.append({by: lvl, "n": len(gl), "days": gl["sess_day"].nunique(),
                     "win_pct": 100 * float(gl["win"].mean()),
                     "ev": float(gl["out"].mean()), "ev_lo": lo, "ev_hi": hi})
    return pd.DataFrame(rows)
