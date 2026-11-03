"""Walk-forward and shuffle test for a declared setup. No entry logic.

The caller supplies the trades the setup already produced, each with a
timestamp and a dollar pnl. This module:

- drops anything in the training portion of each fold
- scores only the later fold
- shuffles those out-of-fold outcomes to build a null
- runs the out-of-fold pnls through the prop account

It does not decide to buy or sell. Folds must be declared up front.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd

from src.research.prop.account import PropAccount
from src.research.prop.rules import AccountRules
from src.research.safety import require_research_allowed
from src.research.setup.card import SetupCard


@dataclass(frozen=True)
class Fold:
    test_start: datetime
    test_end: datetime


@dataclass
class HarnessResult:
    n_trades: int
    mean_pnl: float
    null_mean: float
    null_p: float
    passed: bool
    failed: bool
    end_balance: float
    days: int


def _slice_fold(frame: pd.DataFrame, fold: Fold) -> pd.DataFrame:
    ts = pd.to_datetime(frame["ts"], utc=True)
    start = pd.Timestamp(fold.test_start).tz_convert("UTC")
    end = pd.Timestamp(fold.test_end).tz_convert("UTC")
    return frame[(ts >= start) & (ts < end)]


def shuffle_p(pnls: np.ndarray, observed: float, n: int, rng: np.random.Generator) -> tuple[float, float]:
    """One-sided p against a zero-edge sign-flip null.

    Permuting the sample would not change the mean, so it cannot test an edge.
    Each null draw flips the sign of every outcome, which keeps the sizes and
    removes the direction. p is the share of those means that reach the
    observed mean.
    """
    if len(pnls) == 0:
        return float("nan"), float("nan")
    signs = rng.choice(np.array([-1.0, 1.0]), size=(n, len(pnls)))
    null = (signs * pnls).mean(axis=1)
    p = float(np.mean(null >= observed - 1e-12))
    return float(null.mean()), p


def run_declared(
    card: SetupCard,
    trades: pd.DataFrame,
    rules: AccountRules,
    folds: list[Fold],
    *,
    n_shuffles: int = 500,
    seed: int = 20261103,
    kill_path=None,
) -> HarnessResult:
    require_research_allowed(kill_path)
    card.require_declared()
    if len(folds) < 2:
        raise ValueError("walk-forward needs at least two folds declared before the run")
    required = {"ts", "pnl"}
    missing = required - set(trades.columns)
    if missing:
        raise ValueError(f"trades are missing {sorted(missing)}")
    parts = [_slice_fold(trades, fold) for fold in folds]
    # the earliest fold is the training window and is not scored
    scored = pd.concat(parts[1:], ignore_index=True) if len(parts) > 1 else parts[0].iloc[0:0]
    pnls = scored["pnl"].to_numpy(dtype=float) if len(scored) else np.array([])
    observed = float(pnls.mean()) if len(pnls) else float("nan")
    rng = np.random.default_rng(seed)
    null_mean, p_value = shuffle_p(pnls, observed, n_shuffles, rng)
    account = PropAccount(rules)
    if len(scored):
        ordered = scored.sort_values("ts")
        current = None
        for row in ordered.itertuples(index=False):
            day = pd.Timestamp(row.ts).tz_convert("UTC").date()
            if current is None:
                current = day
            elif day != current:
                account.end_day()
                current = day
            if account.failed or (account.passed and rules.stage != "funded"):
                break
            account.apply(float(row.pnl), ts=row.ts, micros=1)
        account.end_day()
    return HarnessResult(
        n_trades=len(pnls),
        mean_pnl=observed,
        null_mean=null_mean,
        null_p=p_value,
        passed=account.passed,
        failed=account.failed,
        end_balance=account.balance,
        days=account.days,
    )
