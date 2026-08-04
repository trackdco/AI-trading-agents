"""Deflated Sharpe Ratio — a Sharpe corrected for the fact that you went looking.

Bailey & López de Prado, "The Deflated Sharpe Ratio: Correcting for Selection Bias,
Backtest Overfitting and Non-Normality", Journal of Portfolio Management 40(5), 2014;
PSR from Bailey & López de Prado, "The Sharpe Ratio Efficient Frontier", Journal of
Risk 15(2), 2012.

The chain is:

  PSR(SR*)  probability that the true Sharpe exceeds a benchmark SR*, given the observed
            Sharpe, the track length, and the skew/kurtosis of the returns. Skew and
            kurtosis are NOT optional: fat left tails flatter a raw Sharpe badly, and the
            correction is most of why PSR differs from a naive z-test on trading returns.
  SR0       the Sharpe the BEST of N trials would post under a pure-noise null — the
            expected maximum of N draws. Grows like sqrt(2*ln N) via the variance of the
            trial Sharpes.
  DSR       PSR evaluated against SR0. "Given the search that produced this winner, what
            is the probability its true Sharpe exceeds zero-skill-best-of-N?"

THE NULL IS ESTIMATED FROM THE VARIANCE OF THE TRIAL SHARPES, NOT FROM A NOMINAL TRIAL
COUNT. Charging by grid size over-penalises nested and monotone grids, where the effective
number of independent tests is far below the nominal one (our stage-3 shrinkage model
charges nominal breadth and over-charges small sweeps as a result — a known failure mode).
When the trials are correlated their Sharpes bunch together, the cross-sectional variance
shrinks, and SR0 falls with it: the deflation self-adjusts to the effective search breadth.
Pass the actual trial Sharpes whenever you have them; `n_trials`/`trial_sr_var` exist only
for when you don't.

EVERYTHING IS PER-PERIOD. Sharpes here are in the frequency of the return series (per-day
for day-level P&L); no annualisation anywhere, because PSR's variance formula is written in
observation units. Annualise for display only, after the statistics are done.

No dependencies beyond numpy: Phi and Phi^-1 come from `statistics.NormalDist` (stdlib).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist

import numpy as np

_PHI = NormalDist()
_EULER_GAMMA = 0.5772156649015329  # Euler–Mascheroni constant

# The PSR variance formula is asymptotic; below this many observations the moment
# estimates (especially kurtosis) are noise and the number would be false precision.
MIN_OBS = 4


def _clean(returns: np.ndarray | list[float]) -> np.ndarray:
    r = np.asarray(returns, dtype=float).ravel()
    if r.size < MIN_OBS:
        raise ValueError(f"need >= {MIN_OBS} observations, got {r.size}")
    if not np.isfinite(r).all():
        raise ValueError("returns contain NaN/inf — clean the series before scoring it")
    return r


def sharpe_ratio(returns: np.ndarray | list[float]) -> float:
    """Per-period Sharpe: mean/std (ddof=1) of the return series. Zero-variance raises."""
    r = _clean(returns)
    sd = float(r.std(ddof=1))
    if sd == 0.0:
        raise ValueError("zero-variance returns have no Sharpe ratio")
    return float(r.mean()) / sd


def _moments(r: np.ndarray) -> tuple[float, float]:
    """Population skew (m3/m2^1.5) and NON-EXCESS kurtosis (m4/m2^2; normal = 3),
    the moment convention the PSR/DSR papers use."""
    d = r - r.mean()
    m2 = float((d**2).mean())
    if m2 == 0.0:
        raise ValueError("zero-variance returns have no moments")
    skew = float((d**3).mean()) / m2**1.5
    kurt = float((d**4).mean()) / m2**2
    return skew, kurt


def probabilistic_sharpe_ratio(
    returns: np.ndarray | list[float],
    sr_benchmark: float = 0.0,
) -> float:
    """PSR: P[true Sharpe > sr_benchmark | observed series].

    Phi( (SR - SR*) * sqrt(T - 1) / sqrt(1 - skew*SR + (kurt - 1)/4 * SR^2) )

    With normal returns (skew 0, kurt 3) this collapses to the standard asymptotic
    Sharpe significance test, denominator sqrt(1 + SR^2/2).
    """
    r = _clean(returns)
    sr = sharpe_ratio(r)
    skew, kurt = _moments(r)
    var_term = 1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr**2
    if var_term <= 0.0:
        # The asymptotic variance of the SR estimator went negative — the expansion has
        # broken down (extreme skew against a large SR). No honest number exists here.
        raise ValueError(
            f"PSR variance term is non-positive ({var_term:.4g}); "
            "skew/kurtosis are outside the estimator's validity range"
        )
    z = (sr - sr_benchmark) * math.sqrt(r.size - 1.0) / math.sqrt(var_term)
    return _PHI.cdf(z)


def expected_max_sharpe(n_trials: int, trial_sr_var: float) -> float:
    """SR0: the expected best Sharpe of `n_trials` zero-skill trials whose Sharpes
    scatter with variance `trial_sr_var`.

    sqrt(V) * ( (1-gamma) * Phi^-1(1 - 1/N) + gamma * Phi^-1(1 - 1/(N*e)) )

    One trial means no selection: SR0 = 0 (the formula's N=1 limit diverges; the
    statistical content — E[max of one zero-mean draw] = 0 — does not).
    """
    if n_trials < 1:
        raise ValueError(f"n_trials must be >= 1, got {n_trials}")
    if trial_sr_var < 0.0:
        raise ValueError(f"trial_sr_var must be >= 0, got {trial_sr_var}")
    if n_trials == 1 or trial_sr_var == 0.0:
        return 0.0
    n = float(n_trials)
    return math.sqrt(trial_sr_var) * (
        (1.0 - _EULER_GAMMA) * _PHI.inv_cdf(1.0 - 1.0 / n)
        + _EULER_GAMMA * _PHI.inv_cdf(1.0 - 1.0 / (n * math.e))
    )


@dataclass(frozen=True)
class DSRResult:
    """Everything the verdict needs, so the doc can show its work."""

    dsr: float                # P[true SR > SR0] — the deflated probability
    psr_zero: float           # P[true SR > 0] — undeflated, for the before/after
    sr: float                 # observed per-period Sharpe of the candidate
    sr0: float                # expected max Sharpe of the search under the noise null
    n_obs: int                # track length T
    n_trials: int             # N — how many things were tried
    trial_sr_var: float       # cross-sectional variance of the trial Sharpes
    skew: float               # population skew of the candidate's returns
    kurt: float               # non-excess kurtosis (normal = 3)

    @property
    def significant(self) -> bool:
        """The conventional 95% screen. A screen, not a shipping criterion."""
        return self.dsr >= 0.95


def deflated_sharpe_ratio(
    returns: np.ndarray | list[float],
    trial_sharpes: np.ndarray | list[float] | None = None,
    *,
    n_trials: int | None = None,
    trial_sr_var: float | None = None,
) -> DSRResult:
    """DSR of a candidate selected from a search.

    `returns`: the SELECTED candidate's per-period return series (day-level P&L for us).
    `trial_sharpes`: per-period Sharpe of EVERY trial in the search that produced the
    candidate — the preferred input; N and the null variance are estimated from it,
    which is what makes correlated searches priced correctly. Only when the trial
    Sharpes are genuinely unavailable, pass `n_trials` and `trial_sr_var` explicitly
    (both, and no `trial_sharpes`).
    """
    if trial_sharpes is not None:
        if n_trials is not None or trial_sr_var is not None:
            raise ValueError("pass trial_sharpes OR (n_trials, trial_sr_var), not both")
        ts = np.asarray(trial_sharpes, dtype=float).ravel()
        if not np.isfinite(ts).all():
            raise ValueError("trial_sharpes contain NaN/inf")
        if ts.size < 1:
            raise ValueError("trial_sharpes is empty")
        n_trials = int(ts.size)
        trial_sr_var = float(ts.var(ddof=1)) if ts.size > 1 else 0.0
    elif n_trials is None or trial_sr_var is None:
        raise ValueError("pass trial_sharpes, or BOTH n_trials and trial_sr_var")

    r = _clean(returns)
    sr = sharpe_ratio(r)
    skew, kurt = _moments(r)
    sr0 = expected_max_sharpe(n_trials, trial_sr_var)
    return DSRResult(
        dsr=probabilistic_sharpe_ratio(r, sr_benchmark=sr0),
        psr_zero=probabilistic_sharpe_ratio(r, sr_benchmark=0.0),
        sr=sr,
        sr0=sr0,
        n_obs=int(r.size),
        n_trials=n_trials,
        trial_sr_var=float(trial_sr_var),
        skew=skew,
        kurt=kurt,
    )


def min_track_record_length(
    returns: np.ndarray | list[float],
    sr_benchmark: float = 0.0,
    alpha: float = 0.05,
) -> float:
    """MinTRL: observations needed before the observed Sharpe clears `sr_benchmark`
    at confidence 1-alpha (same paper, same variance formula). Returns +inf when the
    observed Sharpe does not exceed the benchmark at all — no track length fixes that."""
    r = _clean(returns)
    sr = sharpe_ratio(r)
    if sr <= sr_benchmark:
        return float("inf")
    skew, kurt = _moments(r)
    var_term = 1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr**2
    if var_term <= 0.0:
        raise ValueError("variance term non-positive; moments outside validity range")
    z = _PHI.inv_cdf(1.0 - alpha)
    return 1.0 + var_term * (z / (sr - sr_benchmark)) ** 2
