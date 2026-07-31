"""RESEARCH ONLY (claude/agent-exit-london-r1). The one gate every bar-loading path in
the agent-exit experiment must call.

WHY THIS EXISTS: `data/reference/nq_1m_master.parquet` spans 2023-01-02 .. 2026-07-15
and physically CONTAINS every sealed 2023/24 holdout day. The frozen pipeline's own
protections (`load_pop` year guards, `guard_holdout_days`, `fit_only` in
london_combined_job.py) live inside code paths this research harness does not call —
a raw `pd.read_parquet` on the master, or any accidental read of a `*_holdout*` path,
bypasses all of them silently. This module is the explicit stand-in for this branch.

NO WARNINGS, NO FILTER-AND-CONTINUE. A year-2023/2024 timestamp or a "holdout" path is
a hard error — the caller's job is to fix the bug, not to have the guard quietly drop
rows and keep going (a `.pipe(filter_fit_years)` that returns a smaller-but-valid frame
is exactly the kind of "worked around it" fix that would let a sealed row slip through
unnoticed on a later, less careful call site).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

SEALED_YEARS = {2023, 2024}


class HoldoutTouchedError(RuntimeError):
    """Raised the instant any code path in this experiment could touch sealed data."""


def assert_fit_only(df: pd.DataFrame, ts_col: str, source: str) -> None:
    """Raise if `df[ts_col]` contains any sealed-era (2023/2024) timestamp, or if
    `source` names a holdout path. Call this on every DataFrame read from a bar/depth/
    footprint file before it is used for anything."""
    if "holdout" in source.lower():
        raise HoldoutTouchedError(
            f"HOLDOUT PATH REFUSED: '{source}' names a holdout artifact. This "
            "experiment is fit-span-only until the two rev-3 signatures land.")
    if ts_col not in df.columns:
        raise HoldoutTouchedError(
            f"assert_fit_only: column '{ts_col}' not found in frame from {source} — "
            "cannot verify the span; fix the call site rather than skip the check.")
    yrs = pd.to_datetime(df[ts_col]).dt.year
    bad = SEALED_YEARS & set(yrs.unique().tolist())
    if bad:
        n = int(yrs.isin(SEALED_YEARS).sum())
        raise HoldoutTouchedError(
            f"SEALED SPAN TOUCHED: {source} contains {n} row(s) with year(s) {bad}. "
            "The sealed 2023/24 holdout may not be read by this experiment. Filter "
            "the SOURCE data before this call — do not silently drop rows here.")


def filter_to_fit_years(df: pd.DataFrame, ts_col: str, source: str,
                        allowed_years: set[int] = frozenset({2025, 2026})) -> pd.DataFrame:
    """The ONE legitimate place sealed rows may be dropped rather than raised on:
    `nq_1m_master.parquet` is a SHARED, unpartitioned raw file spanning 2023-2026 by
    design (fit/holdout separation lives in which days are SLICED from it, not in the
    file's contents) — so `assert_fit_only` on the raw load always fails, correctly,
    and is the wrong tool there. This function is the explicit, LOGGED alternative for
    that one case: it prints exactly how many rows of which years were dropped, then
    returns a frame `assert_fit_only` will pass. Every OTHER file in this experiment
    (L0/L1/L3, any *_fit.parquet) is span-partitioned already and must go through
    `assert_fit_only` (hard-raise), never through this filter — silently filtering an
    already-fit file would hide a real upstream bug instead of catching it."""
    yrs = pd.to_datetime(df[ts_col]).dt.year
    keep = yrs.isin(allowed_years)
    dropped = (~keep).sum()
    if dropped:
        dropped_years = sorted(set(yrs[~keep].unique().tolist()))
        print(f"holdout_guard.filter_to_fit_years({source}): dropping {dropped:,} "
              f"row(s) from year(s) {dropped_years} — keeping {allowed_years} only")
    out = df[keep].reset_index(drop=True)
    assert_fit_only(out, ts_col, source)   # self-check: the filter must have worked
    return out


def assert_path_fit_only(path: str | Path) -> None:
    """Path-only check for call sites that haven't loaded the frame yet (e.g. before
    an expensive parquet read) — refuses a holdout-named path before any I/O happens."""
    p = str(path).lower()
    if "holdout" in p:
        raise HoldoutTouchedError(
            f"HOLDOUT PATH REFUSED: '{path}' names a holdout artifact. This "
            "experiment is fit-span-only until the two rev-3 signatures land.")
