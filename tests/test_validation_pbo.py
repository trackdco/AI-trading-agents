"""PBO/CSCV — noise vs real-edge behaviour, fast-path equivalence, and the bookkeeping."""
from __future__ import annotations

import numpy as np
import pytest

from src.validation import pbo_cscv


def _sharpe_cols(m: np.ndarray) -> np.ndarray:
    return m.mean(axis=0) / m.std(axis=0, ddof=1)


def test_pure_noise_selection_has_high_pbo():
    # 40 zero-edge trials: the IS winner's OOS rank is a coin flip, PBO ~ 1/2
    rng = np.random.default_rng(23)
    m = rng.normal(0.0, 1.0, size=(320, 40))
    res = pbo_cscv(m, n_blocks=8)
    assert 0.25 < res.pbo < 0.75
    assert 0.2 < res.prob_oos_loss < 0.8
    assert res.n_combinations == 70  # C(8,4)


def test_true_edge_has_low_pbo():
    # one genuinely strong trial dominates in AND out of sample -> low PBO
    rng = np.random.default_rng(29)
    m = rng.normal(0.0, 1.0, size=(320, 40))
    m[:, 7] += 0.25  # daily SR ~ 0.25
    res = pbo_cscv(m, n_blocks=8)
    assert res.pbo < 0.2
    assert not res.overfit
    assert res.prob_oos_loss < 0.2


def test_noise_pbo_exceeds_edge_pbo_at_s16():
    # the paper-standard S=16 (12,870 splits) on a small trial set
    rng = np.random.default_rng(31)
    noise = rng.normal(0.0, 1.0, size=(160, 12))
    edged = noise.copy()
    edged[:, 3] += 0.3
    p_noise = pbo_cscv(noise, n_blocks=16)
    p_edged = pbo_cscv(edged, n_blocks=16)
    assert p_noise.n_combinations == 12_870
    assert p_edged.pbo < p_noise.pbo


def test_callable_metric_matches_fast_path():
    # the sums/sums-of-squares optimisation must be EXACTLY the naive computation
    rng = np.random.default_rng(37)
    m = rng.normal(0.01, 1.0, size=(64, 10))
    fast = pbo_cscv(m, n_blocks=4)
    slow = pbo_cscv(m, n_blocks=4, metric=_sharpe_cols)
    assert fast.pbo == slow.pbo
    np.testing.assert_allclose(fast.logits, slow.logits, rtol=1e-10)
    assert fast.prob_oos_loss == slow.prob_oos_loss


def test_batching_does_not_change_the_answer():
    rng = np.random.default_rng(41)
    m = rng.normal(0.0, 1.0, size=(96, 15))
    a = pbo_cscv(m, n_blocks=8, batch_size=7)
    b = pbo_cscv(m, n_blocks=8, batch_size=1000)
    np.testing.assert_array_equal(a.logits, b.logits)


def test_trim_bookkeeping_and_counts():
    rng = np.random.default_rng(43)
    res = pbo_cscv(rng.normal(size=(103, 5)), n_blocks=6)
    assert res.n_combinations == 20  # C(6,3)
    assert res.n_obs_used == 102     # 103 -> 17 rows/block * 6
    assert res.n_obs_dropped == 1
    assert res.n_blocks == 6
    assert res.n_trials == 5
    assert len(res.logits) == 20


def test_dataframe_input_and_determinism():
    import pandas as pd

    rng = np.random.default_rng(47)
    m = rng.normal(size=(80, 8))
    df = pd.DataFrame(m, columns=[f"cfg_{i}" for i in range(8)])
    a, b = pbo_cscv(df, n_blocks=4), pbo_cscv(m, n_blocks=4)
    assert a.pbo == b.pbo
    np.testing.assert_array_equal(a.logits, b.logits)


def test_flat_column_never_outranks_real_candidates():
    # an all-zero trial (flat P&L) must sort below real candidates, not poison the run
    rng = np.random.default_rng(53)
    m = rng.normal(0.0, 1.0, size=(64, 6))
    m[:, 2] = 0.0
    res = pbo_cscv(m, n_blocks=4)
    assert np.isfinite(res.pbo)
    assert len(res.logits) == 6  # C(4,2)


def test_input_validation():
    rng = np.random.default_rng(59)
    good = rng.normal(size=(64, 4))
    with pytest.raises(ValueError):
        pbo_cscv(good[:, :1])                 # one trial
    with pytest.raises(ValueError):
        pbo_cscv(good, n_blocks=7)            # odd S
    with pytest.raises(ValueError):
        pbo_cscv(good, n_blocks=0)
    with pytest.raises(ValueError):
        pbo_cscv(good[:8], n_blocks=16)       # cannot fill the blocks
    bad = good.copy()
    bad[3, 2] = np.nan
    with pytest.raises(ValueError):
        pbo_cscv(bad)
    with pytest.raises(ValueError):
        pbo_cscv(good.ravel())                # not 2-D
