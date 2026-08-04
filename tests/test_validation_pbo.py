"""PBO/CSCV — noise vs real-edge behaviour, fast-path equivalence, and the bookkeeping."""
from __future__ import annotations

import math

import numpy as np
import pytest

from src.validation import pbo_cscv


def _sharpe_cols(m: np.ndarray) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        return m.mean(axis=0) / m.std(axis=0, ddof=1)


def test_pure_noise_selection_has_high_pbo():
    # zero-edge trials: the IS winner's OOS rank is a coin flip, PBO ~ 1/2. A single
    # run's PBO has sd ~0.19, so assert on the mean of three seeded runs, not one draw.
    runs = [
        pbo_cscv(np.random.default_rng(s).normal(0.0, 1.0, size=(320, 40)), n_blocks=8)
        for s in (23, 24, 25)
    ]
    assert 0.3 < np.mean([r.pbo for r in runs]) < 0.7
    assert 0.25 < np.mean([r.prob_oos_loss for r in runs]) < 0.75
    assert runs[0].n_combinations == 70  # C(8,4)


def test_true_edge_has_low_pbo():
    # one genuinely strong trial dominates in AND out of sample -> low PBO
    def run(seed: int):
        m = np.random.default_rng(seed).normal(0.0, 1.0, size=(320, 40))
        m[:, 7] += 0.3  # daily SR ~ 0.3
        return pbo_cscv(m, n_blocks=8)

    runs = [run(s) for s in (29, 30, 31)]
    assert np.mean([r.pbo for r in runs]) < 0.25
    assert np.mean([r.prob_oos_loss for r in runs]) < 0.25
    assert not runs[0].overfit


def test_noise_pbo_exceeds_edge_pbo_at_s16():
    # the paper-standard S=16 (12,870 splits) on a small trial set
    rng = np.random.default_rng(31)
    noise = rng.normal(0.0, 1.0, size=(160, 12))
    edged = noise.copy()
    edged[:, 3] += 0.4
    p_noise = pbo_cscv(noise, n_blocks=16)
    p_edged = pbo_cscv(edged, n_blocks=16)
    assert p_noise.n_combinations == 12_870
    assert p_edged.pbo < p_noise.pbo


def test_known_answer_by_hand():
    # T=4, N=4, S=2: both splits fully hand-computable. Winner col A in split 1
    # (IS Sharpe sqrt(2)), col B in split 2; the winner's OOS series is [0, 2] in both
    # splits and col D is an exact copy of it, so the winner TIES D out-of-sample:
    # rank = 1 below (C) + 0.5 tie + 1 = 2.5 of N+1=5 -> omega = 0.5 -> logit = 0.0
    # exactly, both splits. Pins the omega normalisation, the average-tie path, the
    # lambda <= 0 convention (PBO = 1.0 here), and the slope/intercept orientation.
    m = np.array([
        #  A    B    C    D
        [1.0, 0.0, -1.0, 0.0],
        [3.0, 2.0,  1.0, 2.0],   # block 0
        [0.0, 1.0, -3.0, 0.0],
        [2.0, 5.0,  1.0, 2.0],   # block 1
    ])
    res = pbo_cscv(m, n_blocks=2)
    assert res.n_combinations == 2
    np.testing.assert_array_equal(res.logits, [0.0, 0.0])
    assert res.pbo == 1.0
    assert res.prob_oos_loss == 0.0
    oos_star = 1.0 / math.sqrt(2.0)          # mean 1 / sd(ddof=1) sqrt(2) of [0, 2]
    assert res.slope == pytest.approx(0.0, abs=1e-12)
    assert res.intercept == pytest.approx(oos_star, abs=1e-12)


def test_trim_drops_the_tail_not_the_head():
    # 13 rows, S=4 -> 12 used; a huge outlier in the LAST row must change nothing
    rng = np.random.default_rng(61)
    m = rng.normal(0.0, 1.0, size=(13, 5))
    m[-1] += 1e6
    a = pbo_cscv(m, n_blocks=4)
    b = pbo_cscv(m[:12], n_blocks=4)
    assert a.n_obs_dropped == 1 and b.n_obs_dropped == 0
    np.testing.assert_array_equal(a.logits, b.logits)
    assert a.prob_oos_loss == b.prob_oos_loss


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
    # an all-zero trial (flat P&L) must sort below real candidates, not poison the
    # run. Sharp form: since the flat column can never WIN, the per-split winner
    # series — and everything derived from it — must be identical to the run with
    # the flat column removed entirely.
    rng = np.random.default_rng(53)
    clean = rng.normal(0.0, 1.0, size=(64, 5))
    with_flat = np.insert(clean, 2, 0.0, axis=1)
    a = pbo_cscv(with_flat, n_blocks=4)
    b = pbo_cscv(clean, n_blocks=4)
    assert len(a.logits) == 6  # C(4,2)
    assert a.prob_oos_loss == b.prob_oos_loss
    assert a.slope == pytest.approx(b.slope)
    assert a.pbo == pytest.approx(b.pbo, abs=0.2)  # omega denominators shift by 1


def test_callable_metric_rejects_nan():
    # a naive mean/std metric yields 0/0 = NaN on a flat column; silently crowning
    # the NaN column IS-winner of every split is the failure mode this must refuse
    rng = np.random.default_rng(67)
    m = rng.normal(0.0, 1.0, size=(64, 6))
    m[:, 2] = 0.0
    with pytest.raises(ValueError, match="NaN"):
        pbo_cscv(m, n_blocks=4, metric=_sharpe_cols)
    with pytest.raises(ValueError, match="one value per trial"):
        pbo_cscv(rng.normal(size=(64, 4)), n_blocks=4, metric=lambda x: x.mean(0)[:2])


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
    with pytest.raises(ValueError):
        pbo_cscv(good, batch_size=0)          # empty batch loop would return garbage
    with pytest.raises(ValueError):
        pbo_cscv(good, batch_size=-1)
    bad = good.copy()
    bad[3, 2] = np.nan
    with pytest.raises(ValueError):
        pbo_cscv(bad)
    with pytest.raises(ValueError):
        pbo_cscv(good.ravel())                # not 2-D
