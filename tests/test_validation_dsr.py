"""DSR/PSR — known-answer pins, monotonicity, and the noise-search calibration cases."""
from __future__ import annotations

import math
from statistics import NormalDist

import numpy as np
import pytest

from src.validation import (
    deflated_sharpe_ratio,
    expected_max_sharpe,
    min_track_record_length,
    probabilistic_sharpe_ratio,
    sharpe_ratio,
)


def _standardised(rng: np.random.Generator, draw, n: int) -> np.ndarray:
    """A series with EXACT mean 0 / sd 1 (ddof=1) but the draw's skew/kurtosis shape."""
    x = draw(rng, n)
    return (x - x.mean()) / x.std(ddof=1)


def test_zero_mean_series_has_psr_half():
    # alternating +/-1: mean 0, so SR = 0 and P[true SR > 0] must be exactly 1/2
    r = np.tile([1.0, -1.0], 50)
    assert sharpe_ratio(r) == 0.0
    assert probabilistic_sharpe_ratio(r) == pytest.approx(0.5)


def test_single_trial_normal_collapses_to_sharpe_z_test():
    # THE PINNED CASE FROM THE BRIEF: one trial, ~normal returns -> DSR must collapse
    # to the standard asymptotic Sharpe significance test Phi(SR*sqrt(T-1)/sqrt(1+SR^2/2)).
    rng = np.random.default_rng(7)
    r = rng.normal(0.05, 1.0, 5000)
    res = deflated_sharpe_ratio(r, n_trials=1, trial_sr_var=0.0)
    sr = sharpe_ratio(r)
    z_test = NormalDist().cdf(sr * math.sqrt(len(r) - 1) / math.sqrt(1 + sr**2 / 2))
    assert res.sr0 == 0.0
    assert res.dsr == res.psr_zero
    # normal data's sampled skew/kurt are not exactly 0/3, so approximate, not exact
    assert res.dsr == pytest.approx(z_test, abs=0.01)


def test_negative_skew_lowers_psr_at_equal_sharpe():
    # same exact SR by construction; the left-tailed series must score a LOWER PSR —
    # skew/kurtosis are most of why DSR differs from a raw Sharpe on trading returns
    rng = np.random.default_rng(11)
    z_sym = _standardised(rng, lambda g, n: g.normal(size=n), 4000)
    z_neg = _standardised(rng, lambda g, n: -g.lognormal(0.0, 0.7, size=n), 4000)
    sym, neg = 0.05 + z_sym, 0.05 + z_neg
    assert sharpe_ratio(sym) == pytest.approx(sharpe_ratio(neg))
    assert probabilistic_sharpe_ratio(neg) < probabilistic_sharpe_ratio(sym)


def test_expected_max_sharpe_pinned_value():
    # V=1, N=10: (1-g)*z(1-1/10) + g*z(1-1/(10e)) with g = Euler-Mascheroni
    assert expected_max_sharpe(10, 1.0) == pytest.approx(1.5746, abs=5e-3)


def test_expected_max_sharpe_monotone_and_limits():
    assert expected_max_sharpe(1, 1.0) == 0.0
    assert expected_max_sharpe(50, 0.0) == 0.0
    v = [expected_max_sharpe(n, 0.04) for n in (2, 10, 100, 10_000)]
    assert v == sorted(v) and v[0] > 0
    assert expected_max_sharpe(100, 0.09) == pytest.approx(
        1.5 * expected_max_sharpe(100, 0.04)
    )  # scales with sqrt(V)
    with pytest.raises(ValueError):
        expected_max_sharpe(0, 1.0)
    with pytest.raises(ValueError):
        expected_max_sharpe(10, -0.1)
    # NaN slips past a bare `< 0` check — it must raise, not return a NaN DSR
    with pytest.raises(ValueError):
        expected_max_sharpe(10, float("nan"))
    with pytest.raises(ValueError):
        expected_max_sharpe(10, float("inf"))


def test_deflation_is_strict_when_search_happened():
    rng = np.random.default_rng(3)
    r = rng.normal(0.1, 1.0, 500)
    res = deflated_sharpe_ratio(r, n_trials=100, trial_sr_var=0.01)
    assert res.sr0 > 0
    assert res.dsr < res.psr_zero


def test_best_of_pure_noise_search_is_not_significant():
    # 200 zero-edge strategies; the raw PSR of the winner looks great, the DSR does not.
    rng = np.random.default_rng(42)
    trials = rng.normal(0.0, 0.01, size=(252, 200))
    sharpes = np.array([sharpe_ratio(trials[:, i]) for i in range(200)])
    best = int(np.argmax(sharpes))
    res = deflated_sharpe_ratio(trials[:, best], trial_sharpes=sharpes)
    assert res.psr_zero > 0.95        # selection bias makes the winner LOOK significant
    assert res.dsr < 0.90             # deflation prices the search and rejects it
    assert not res.significant
    assert res.n_trials == 200


def test_true_edge_survives_deflation():
    # one genuinely good strategy among 100 noise trials keeps its significance
    rng = np.random.default_rng(5)
    trials = rng.normal(0.0, 0.01, size=(400, 100))
    trials[:, 17] = rng.normal(0.004, 0.01, 400)  # daily SR ~0.4, T=400
    sharpes = np.array([sharpe_ratio(trials[:, i]) for i in range(100)])
    assert int(np.argmax(sharpes)) == 17
    res = deflated_sharpe_ratio(trials[:, 17], trial_sharpes=sharpes)
    assert res.dsr > 0.95
    assert res.significant


def test_trial_sharpes_and_explicit_null_agree():
    rng = np.random.default_rng(9)
    r = rng.normal(0.05, 1.0, 300)
    ts = rng.normal(0.0, 0.1, 500)
    a = deflated_sharpe_ratio(r, trial_sharpes=ts)
    b = deflated_sharpe_ratio(r, n_trials=500, trial_sr_var=float(ts.var(ddof=1)))
    assert a.dsr == pytest.approx(b.dsr)
    assert a.sr0 == pytest.approx(b.sr0)
    # result-field wiring: every reported number must be the thing its name claims
    d = r - r.mean()
    m2 = (d**2).mean()
    assert a.sr == pytest.approx(r.mean() / r.std(ddof=1))
    assert a.n_obs == 300
    assert a.n_trials == 500
    assert a.trial_sr_var == pytest.approx(float(ts.var(ddof=1)))
    assert a.skew == pytest.approx((d**3).mean() / m2**1.5)
    assert a.kurt == pytest.approx((d**4).mean() / m2**2)


def test_single_trial_sharpe_means_no_deflation():
    # a length-1 trial_sharpes list is the no-search case: SR0 = 0, DSR = PSR(0)
    rng = np.random.default_rng(21)
    r = rng.normal(0.05, 1.0, 300)
    res = deflated_sharpe_ratio(r, trial_sharpes=[0.3])
    assert res.n_trials == 1
    assert res.sr0 == 0.0
    assert res.dsr == res.psr_zero


def test_kurtosis_convention_is_pinned_non_excess():
    # the PSR variance formula needs NON-excess kurtosis (normal = 3). An
    # excess-kurtosis regression is second-order in SR, so no behavioural test
    # catches it — pin the convention through the public result instead.
    rng = np.random.default_rng(17)
    res = deflated_sharpe_ratio(rng.normal(0.05, 1.0, 20_000), n_trials=1, trial_sr_var=0.0)
    assert res.kurt == pytest.approx(3.0, abs=0.25)
    assert abs(res.skew) < 0.1


def test_psr_matches_reference_formula_on_fat_tails():
    # independent recomputation of the full PSR formula on a fat-tailed series —
    # any silent change to the moment estimators or the variance term breaks this
    rng = np.random.default_rng(19)
    r = 0.02 + rng.standard_t(5, 3000)
    sr = r.mean() / r.std(ddof=1)
    d = r - r.mean()
    m2 = (d**2).mean()
    skew, kurt = (d**3).mean() / m2**1.5, (d**4).mean() / m2**2
    z = sr * math.sqrt(len(r) - 1) / math.sqrt(1 - skew * sr + (kurt - 1) / 4 * sr**2)
    assert probabilistic_sharpe_ratio(r) == pytest.approx(NormalDist().cdf(z), abs=1e-12)


def test_min_track_record_length():
    rng = np.random.default_rng(13)
    r = rng.normal(0.1, 1.0, 1000)
    m05 = min_track_record_length(r, alpha=0.05)
    m10 = min_track_record_length(r, alpha=0.10)
    assert 0 < m10 < m05 < float("inf")
    # a Sharpe at/below the benchmark can never clear it, at any length
    assert min_track_record_length(r, sr_benchmark=10.0) == float("inf")
    # pin the formula itself: 1 + var_term * (z_alpha / SR)^2, independently recomputed
    sr = r.mean() / r.std(ddof=1)
    d = r - r.mean()
    m2 = (d**2).mean()
    skew, kurt = (d**3).mean() / m2**1.5, (d**4).mean() / m2**2
    var_term = 1 - skew * sr + (kurt - 1) / 4 * sr**2
    expected = 1 + var_term * (NormalDist().inv_cdf(0.95) / sr) ** 2
    assert m05 == pytest.approx(expected, abs=1e-9)


def test_input_validation():
    with pytest.raises(ValueError):
        sharpe_ratio([1.0, 2.0, 3.0])                    # too short
    with pytest.raises(ValueError):
        sharpe_ratio([1.0, 1.0, 1.0, 1.0])               # zero variance
    with pytest.raises(ValueError):
        probabilistic_sharpe_ratio([1.0, np.nan, 2.0, 3.0])
    r = np.random.default_rng(1).normal(size=100)
    with pytest.raises(ValueError):
        deflated_sharpe_ratio(r)                         # no null spec at all
    with pytest.raises(ValueError):
        deflated_sharpe_ratio(r, n_trials=10)            # variance missing
    with pytest.raises(ValueError):
        deflated_sharpe_ratio(r, trial_sharpes=[0.1, 0.2], n_trials=2)  # both forms
    with pytest.raises(ValueError):
        deflated_sharpe_ratio(r, trial_sharpes=[0.1, np.inf])
