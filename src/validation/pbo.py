"""Probability of Backtest Overfitting via CSCV — does the selection procedure pick noise?

Bailey, Borwein, López de Prado & Zhu, "The Probability of Backtest Overfitting",
Journal of Computational Finance 20(4), 2017.

The object under test is NOT any single strategy — it is the SELECTION PROCEDURE. Split
the record into S contiguous blocks. For every one of the C(S, S/2) ways of choosing half
the blocks as in-sample, pick the trial that ranks best in-sample, then look up where that
same trial ranks out-of-sample (the complementary half). If selection is finding signal,
the IS winner keeps beating the median OOS; if it is finding noise, its OOS rank is a coin
flip. PBO is the fraction of splits where the IS winner lands at or below the OOS median.
Above ~50% the procedure itself is picking noise, independent of any one result.

Mechanics per split c:
    n*      = argmax of in-sample performance
    omega_c = OOS rank of n* / (N + 1)          (average-tie ranks; 1 = worst)
    lambda_c = logit(omega_c)                    (0 = exactly median OOS)
    PBO     = #{lambda_c <= 0} / #splits

Also reported, from the same splits (the paper's companion diagnostics):
    slope/intercept — OLS of the winner's OOS performance on its IS performance
                      (slope well below 1 = performance degradation under selection)
    prob_oos_loss   — fraction of splits where the IS winner LOSES money out-of-sample

Blocks are CONTIGUOUS in time, so each preserves local serial structure (regime, vol
clustering); what CSCV assumes exchangeable is the blocks, not the rows. Rows should be
day-level (or coarser) P&L — same-day trades share regime and tape, so trade-level rows
would leak across the split and understate overfitting (the stage-3 audit splits by day
for exactly this reason).

The default metric is the per-period Sharpe, computed by a vectorised sums/sums-of-squares
path that never materialises per-split submatrices; memory is O(batch_size x N) no matter
how many splits there are, so the full S=16 (12,870 splits) over ~29k trials runs in
seconds and bounded memory. Any other metric can be passed as a callable at the cost of
one call per split.
"""
from __future__ import annotations

import itertools
import math
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd

MetricFn = Callable[[np.ndarray], np.ndarray]  # (rows, N) -> (N,) performances


@dataclass(frozen=True)
class PBOResult:
    """The verdict, with enough of the split distribution to show its work."""

    pbo: float                # fraction of splits with the IS winner <= median OOS
    n_combinations: int       # C(S, S/2) splits evaluated
    n_blocks: int             # S
    n_trials: int             # N strategies/configurations compared
    n_obs_used: int           # rows actually used (T trimmed to a multiple of S)
    n_obs_dropped: int        # trailing rows dropped by the trim
    logits: np.ndarray        # lambda_c per split — the full distribution
    slope: float              # OLS slope of OOS-vs-IS winner performance
    intercept: float          # OLS intercept of the same
    prob_oos_loss: float      # fraction of splits where the IS winner's OOS perf < 0

    @property
    def overfit(self) -> bool:
        """The conventional read: selection is mostly noise above one half."""
        return self.pbo >= 0.5


def _sharpe_from_sums(s: np.ndarray, ss: np.ndarray, n: int) -> np.ndarray:
    """Per-column Sharpe (ddof=1) from column sums and sums of squares.

    Zero-variance columns get -inf when the mean is <= 0 and +inf otherwise: a flat
    zero line must never out-rank a real candidate, while a constant positive line
    (which real day-level P&L cannot produce) sorts above everything rather than NaN.
    """
    mean = s / n
    var = (ss - s * mean) / (n - 1)
    var = np.maximum(var, 0.0)  # clamp fp negatives from the subtraction
    with np.errstate(divide="ignore", invalid="ignore"):
        sr = mean / np.sqrt(var)
    flat = var == 0.0
    if flat.any():
        sr = np.where(flat, np.where(mean > 0, np.inf, -np.inf), sr)
    return sr


def _winner_stats(
    is_perf: np.ndarray, oos_perf: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per split (rows): the IS winner's IS perf, OOS perf, and average-tie OOS rank."""
    n_star = is_perf.argmax(axis=1)
    take = np.arange(len(is_perf))
    star_is = is_perf[take, n_star]
    star_oos = oos_perf[take, n_star]
    below = (oos_perf < star_oos[:, None]).sum(axis=1)
    tied = (oos_perf == star_oos[:, None]).sum(axis=1) - 1  # excluding the winner itself
    rank = below + 0.5 * tied + 1.0
    return star_is, star_oos, rank


def pbo_cscv(
    returns: pd.DataFrame | np.ndarray,
    n_blocks: int = 16,
    metric: MetricFn | None = None,
    batch_size: int = 256,
) -> PBOResult:
    """CSCV over a T x N matrix: rows are periods (days), columns are trials.

    `n_blocks` (S) must be even; S=16 (12,870 splits) is the paper's standard. T is
    trimmed from the END to a multiple of S so every block is the same length —
    trailing-row trims are reported in the result, never silent.

    `metric` defaults to the vectorised per-period Sharpe. A callable replaces it at
    one call per split: metric(rows_2d) -> (N,) performance vector.
    """
    if isinstance(returns, pd.DataFrame):
        m = returns.to_numpy(dtype=float)
    else:
        m = np.asarray(returns, dtype=float)
    if m.ndim != 2:
        raise ValueError(f"returns must be 2-D (periods x trials), got shape {m.shape}")
    t_all, n_trials = m.shape
    if n_trials < 2:
        raise ValueError("PBO needs >= 2 trials — ranking one strategy is meaningless")
    if not np.isfinite(m).all():
        raise ValueError("returns contain NaN/inf — clean the matrix before scoring it")
    if n_blocks < 2 or n_blocks % 2:
        raise ValueError(f"n_blocks must be even and >= 2, got {n_blocks}")

    rows_per_block = t_all // n_blocks
    if rows_per_block < 1:
        raise ValueError(f"{t_all} rows cannot fill {n_blocks} blocks")
    half = n_blocks // 2
    if rows_per_block * half < 2:
        raise ValueError("each half-sample needs >= 2 rows for a variance")
    used = rows_per_block * n_blocks
    m = m[:used]

    combos = list(itertools.combinations(range(n_blocks), half))
    n_half = rows_per_block * half

    star_is = np.empty(len(combos))
    star_oos = np.empty(len(combos))
    rank = np.empty(len(combos))

    if metric is None:
        # Sharpe fast path: per-block sums/sums-of-squares, then every split is a
        # mask multiply — no submatrix is ever materialised.
        blocks = m.reshape(n_blocks, rows_per_block, n_trials)
        bsum = blocks.sum(axis=1)          # (S, N)
        bss = (blocks**2).sum(axis=1)      # (S, N)
        tsum, tss = bsum.sum(axis=0), bss.sum(axis=0)
        for lo in range(0, len(combos), batch_size):
            batch = combos[lo : lo + batch_size]
            mask = np.zeros((len(batch), n_blocks))
            for i, c in enumerate(batch):
                mask[i, list(c)] = 1.0
            s_is, ss_is = mask @ bsum, mask @ bss
            sr_is = _sharpe_from_sums(s_is, ss_is, n_half)
            sr_oos = _sharpe_from_sums(tsum - s_is, tss - ss_is, used - n_half)
            hi = lo + len(batch)
            star_is[lo:hi], star_oos[lo:hi], rank[lo:hi] = _winner_stats(sr_is, sr_oos)
    else:
        row_ix = np.arange(used).reshape(n_blocks, rows_per_block)
        all_blocks = frozenset(range(n_blocks))
        for i, c in enumerate(combos):
            oos = sorted(all_blocks - set(c))
            p_is = np.asarray(metric(m[row_ix[list(c)].ravel()]), dtype=float)
            p_oos = np.asarray(metric(m[row_ix[oos].ravel()]), dtype=float)
            s_i, s_o, rk = _winner_stats(p_is[None, :], p_oos[None, :])
            star_is[i], star_oos[i], rank[i] = s_i[0], s_o[0], rk[0]

    omega = rank / (n_trials + 1.0)
    logits = np.log(omega / (1.0 - omega))

    finite = np.isfinite(star_is) & np.isfinite(star_oos)
    if finite.sum() >= 2 and np.ptp(star_is[finite]) > 0:
        slope, intercept = np.polyfit(star_is[finite], star_oos[finite], 1)
    else:
        slope, intercept = math.nan, math.nan

    return PBOResult(
        pbo=float((logits <= 0.0).mean()),
        n_combinations=len(combos),
        n_blocks=n_blocks,
        n_trials=n_trials,
        n_obs_used=used,
        n_obs_dropped=t_all - used,
        logits=logits,
        slope=float(slope),
        intercept=float(intercept),
        prob_oos_loss=float((star_oos < 0.0).mean()),
    )
