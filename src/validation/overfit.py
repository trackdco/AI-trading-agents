#!/usr/bin/env python3
"""PBO, the Deflated Sharpe Ratio, and walk-forward — the measurements we did not have.

ANGUS 2026-08-06: *"when you over fit, you'll know whether it overfits or not very simply, by
seeing if it holds in holdout or not. also PBO and DSR etc etc."*

WHY THIS EXISTS. Every result this project produces is selected from many candidates, and
until now the correction for that has been a hand-wave. `scripts/separator_scan.py` tested 93
buckets and reported survivors with the note "at a 5% false-positive rate you would expect ~2
to clear by chance". That is a guess. These functions replace it with a number.

The framework survey (research/findings/ai-trading-system-framework.md) found our validation
already ahead of the field on pre-registration, permutation nulls and a sealed holdout, and
missing exactly three things: walk-forward, PBO, DSR. This module is those three.

NO SCIPY in this environment, so the normal CDF and quantile are implemented directly --
`_ncdf` from erfc, `_nppf` from Acklam's rational approximation (|error| < 1.15e-9).

REFERENCES
  Bailey, Borwein, Lopez de Prado & Zhu (2014), "The Probability of Backtest Overfitting"
  Bailey & Lopez de Prado (2014), "The Deflated Sharpe Ratio"
"""

from __future__ import annotations

from itertools import combinations
from math import comb, erfc, exp, log, pi, sqrt

import numpy as np

EULER = 0.5772156649015329


def _ncdf(x: float) -> float:
    return 0.5 * erfc(-x / sqrt(2.0))


def _nppf(p: float) -> float:
    """Inverse normal CDF, Acklam's rational approximation."""
    if not 0.0 < p < 1.0:
        return float("nan")
    a = (-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00)
    b = (-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01)
    c = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00)
    d = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00)
    pl, ph = 0.02425, 1 - 0.02425
    if p < pl:
        q = sqrt(-2 * log(p))
        x = (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    elif p > ph:
        q = sqrt(-2 * log(1 - p))
        x = -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    else:
        q, r = p - 0.5, (p - 0.5) ** 2
        x = (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    # one Halley refinement
    e = _ncdf(x) - p
    u = e * sqrt(2 * pi) * exp(x * x / 2)
    return x - u / (1 + x * u / 2)


def sharpe(x: np.ndarray) -> float:
    """Per-period Sharpe (NOT annualised). Ratio of mean to sd of the period series."""
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 3:
        return np.nan
    s = x.std(ddof=1)
    return float(x.mean() / s) if s > 0 else np.nan


def cscv_pbo(M: np.ndarray, S: int = 16, metric=sharpe) -> dict:
    """Combinatorially Symmetric Cross-Validation → Probability of Backtest Overfitting.

    M : (T, N) per-period performance, one column per candidate strategy. Rows must be in
        time order and aligned across strategies -- a strategy that does not trade on a
        period contributes 0, not NaN, because being flat IS its performance.

    The procedure, from Bailey/Borwein/Lopez de Prado/Zhu: cut the timeline into S blocks;
    for every way of choosing S/2 blocks as in-sample, pick the strategy that wins in-sample
    and look up where it ranks out-of-sample. If the in-sample winner is routinely a
    below-median performer out-of-sample, the selection process is fitting noise.

    PBO is the fraction of splits where the IS-best lands below the OOS median. **PBO > 0.5
    means the selection is worse than useless.** Under 0.1 is the usual comfort bar.

    Why this and not a simple train/test split: one split gives one draw. C(16,8) = 12,870
    draws gives a distribution, and it is symmetric -- every block serves as both IS and OOS,
    so no single lucky period can carry the verdict.
    """
    M = np.asarray(M, float)
    T, N = M.shape
    if N < 2:
        return {"pbo": np.nan, "n_strategies": N, "note": "need >= 2 strategies"}
    rows = (T // S) * S
    blocks = np.array_split(M[:rows], S, axis=0)

    lam, below = [], 0
    for idx in combinations(range(S), S // 2):
        oos_idx = [i for i in range(S) if i not in idx]
        IS = np.vstack([blocks[i] for i in idx])
        OOS = np.vstack([blocks[i] for i in oos_idx])
        is_perf = np.array([metric(IS[:, n]) for n in range(N)])
        if not np.isfinite(is_perf).any():
            continue
        best = int(np.nanargmax(is_perf))
        oos_perf = np.array([metric(OOS[:, n]) for n in range(N)])
        finite = np.isfinite(oos_perf)
        if finite.sum() < 2 or not finite[best]:
            continue
        # rank of the IS winner among OOS performances, 1 = worst
        rank = float((oos_perf[finite] <= oos_perf[best]).sum())
        w = rank / (finite.sum() + 1.0)
        w = min(max(w, 1e-6), 1 - 1e-6)
        lam.append(log(w / (1 - w)))
        below += int(w <= 0.5)
    n = len(lam)
    return {"pbo": below / n if n else np.nan, "n_splits": n, "n_strategies": N,
            "median_logit": float(np.median(lam)) if n else np.nan}


def deflated_sharpe(returns: np.ndarray, n_trials: int, trial_sharpes: np.ndarray) -> dict:
    """Deflated Sharpe Ratio — the probability the observed Sharpe is real given how many
    strategies were tried.

    The intuition that makes it worth the algebra: if you try 800 strategies, the BEST one has
    a high Sharpe even when every one of them is worthless. DSR asks whether the observed
    Sharpe beats what the maximum of N pure-noise trials would have been, and it corrects for
    the non-normality of the return series while doing it (negative skew and fat tails both
    inflate a naive Sharpe).

    returns       the selected strategy's per-period series
    n_trials      how many candidates were searched -- BE HONEST HERE, this is the whole point
    trial_sharpes the Sharpes of all trials, for their variance

    DSR > 0.95 is the usual bar.
    """
    r = np.asarray(returns, float)
    r = r[np.isfinite(r)]
    T = len(r)
    if T < 20:
        return {"dsr": np.nan, "note": "need >= 20 periods"}
    sr = sharpe(r)
    if not np.isfinite(sr):
        return {"dsr": np.nan, "note": "zero variance"}
    m = r.mean()
    sd = r.std(ddof=1)
    g3 = float(((r - m) ** 3).mean() / sd ** 3)          # skew
    g4 = float(((r - m) ** 4).mean() / sd ** 4)          # kurtosis, NOT excess

    ts = np.asarray(trial_sharpes, float)
    ts = ts[np.isfinite(ts)]
    v = float(ts.var(ddof=1)) if len(ts) > 1 else 0.0
    N = max(int(n_trials), 2)
    # expected maximum Sharpe under the null of zero true skill across N trials
    sr0 = sqrt(v) * ((1 - EULER) * _nppf(1 - 1.0 / N) + EULER * _nppf(1 - 1.0 / (N * exp(1))))

    denom = sqrt(max(1e-12, 1 - g3 * sr + (g4 - 1) / 4.0 * sr ** 2))
    z = (sr - sr0) * sqrt(T - 1) / denom
    return {"dsr": _ncdf(z), "sharpe": sr, "sr0": sr0, "z": z, "T": T,
            "skew": g3, "kurtosis": g4, "n_trials": N, "trial_sr_var": v}


def walk_forward(M: np.ndarray, train: int, test: int, metric=sharpe) -> dict:
    """Rolling-origin walk-forward: fit on `train` periods, trade the next `test`, roll.

    Returns the concatenated out-of-sample series produced by always trading whatever won
    in-sample. This is the honest version of "adaptive" -- and note what the framework survey
    found: walk-forward REACTS to regime shifts, it does not anticipate them. A strategy that
    only works because the winner is re-picked every month is a real finding, but it is a
    finding about adaptivity, not about the signal.
    """
    M = np.asarray(M, float)
    T, N = M.shape
    oos, picks = [], []
    start = 0
    while start + train + test <= T:
        IS = M[start:start + train]
        perf = np.array([metric(IS[:, n]) for n in range(N)])
        if np.isfinite(perf).any():
            best = int(np.nanargmax(perf))
            picks.append(best)
            oos.append(M[start + train:start + train + test, best])
        start += test
    if not oos:
        return {"oos": np.array([]), "note": "series too short for this train/test split"}
    o = np.concatenate(oos)
    return {"oos": o, "sharpe": sharpe(o), "mean": float(o.mean()), "total": float(o.sum()),
            "green": float((o > 0).mean()), "n_windows": len(picks),
            "n_distinct_picks": len(set(picks)), "picks": picks}


def report(name: str, oos: np.ndarray, pbo: dict, dsr: dict, wf: dict) -> list[str]:
    L = [f"### {name}", "",
         "| test | value | bar | verdict |", "|---|---:|---|---|"]
    p = pbo.get("pbo", np.nan)
    L.append(f"| PBO | **{p:.3f}** | < 0.10 | "
             f"{'**PASS**' if np.isfinite(p) and p < 0.10 else '**FAIL**'} |"
             if np.isfinite(p) else "| PBO | — | < 0.10 | — |")
    d = dsr.get("dsr", np.nan)
    L.append(f"| Deflated Sharpe | **{d:.3f}** | > 0.95 | "
             f"{'**PASS**' if np.isfinite(d) and d > 0.95 else '**FAIL**'} |"
             if np.isfinite(d) else "| Deflated Sharpe | — | > 0.95 | — |")
    if np.isfinite(dsr.get("sharpe", np.nan)):
        L.append(f"| observed Sharpe | {dsr['sharpe']:.3f} | vs SR0 {dsr['sr0']:.3f} "
                 f"({dsr['n_trials']} trials) | |")
    if "sharpe" in wf and np.isfinite(wf.get("sharpe", np.nan)):
        L.append(f"| walk-forward OOS mean | {wf['mean']:+.3f} | > 0 | "
                 f"{'**PASS**' if wf['mean'] > 0 else '**FAIL**'} |")
        L.append(f"| walk-forward windows | {wf['n_windows']} | — | "
                 f"{wf['n_distinct_picks']} distinct winners |")
    L.append("")
    return L
