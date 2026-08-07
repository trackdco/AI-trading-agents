"""Feature-library parity (LIVE-STACK #2): the shared src/canon/features.py functions
must reproduce the backtest's stored feature columns to the decimal.

For every trade in output/trade_matrix.parquet that had depth coverage, recompute the
depth features from the SAME raw depth CSVs via src.canon.features.depth_at and assert
they equal the stored dep_* columns exactly. This is the guarantee that moving the
definitions into the shared library (so the live ingestor imports them) changed nothing —
the live path scores on the identical math the +$106k book was validated on.

Skips cleanly when the research artifacts (gitignored output/ + reference depth) are not
present, so the test is a no-op in a bare checkout and a hard gate where the data lives.
"""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import pytest

from src.canon.features import depth_at, load_depth_day, tape_features

MATRIX = Path("output/trade_matrix.parquet")
FP_MINUTES = Path("output/fp_minutes.parquet")
DEP_COLS = [
    "dep_thick", "dep_imb", "dep_spread", "dep_support", "dep_resist", "dep_sup_m_res",
    "dep_wall_above_d", "dep_wall_above_sz", "dep_thick_d5m",
    "dep_wall_below_d", "dep_wall_below_sz",
]


def _load_trades():
    if not MATRIX.exists():
        pytest.skip(f"{MATRIX} not present (gitignored research artifact) — parity gate "
                    "runs where the data lives")
    t = pd.read_parquet(MATRIX)
    covered = t[t["dep_thick"].notna()].copy()
    # need at least one day's depth CSV on disk, else the reference data is absent too
    if load_depth_day(str(covered["day"].iloc[0])) is None:
        pytest.skip("reference depth CSVs not present — parity gate runs where the data lives")
    return covered


def _eq(a, b) -> bool:
    an, bn = (a is None or (isinstance(a, float) and math.isnan(a))), \
             (b is None or (isinstance(b, float) and math.isnan(b)))
    if an or bn:
        return an and bn                      # both missing == match
    return math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=1e-9)


def test_depth_features_reproduce_backtest_matrix():
    trades = _load_trades()
    day_cache: dict[str, pd.DataFrame | None] = {}
    checked = 0
    mismatches = []
    for t in trades.itertuples():
        day = str(t.day)
        if day not in day_cache:
            day_cache[day] = load_depth_day(day)
        dep = day_cache[day]
        if dep is None:
            continue                          # day's CSV absent — not a mismatch, just uncovered
        got = depth_at(dep, t.fillmi, float(t.entry), t.direction)
        for col in DEP_COLS:
            stored = getattr(t, col, float("nan"))
            recomputed = got.get(col, float("nan"))
            if not _eq(stored, recomputed):
                mismatches.append((day, str(t.fillmi), col, stored, recomputed))
        checked += 1

    assert checked > 0, "no trades with on-disk depth were checked — data wiring is wrong"
    assert not mismatches, (
        f"{len(mismatches)} depth-feature mismatches across {checked} trades; "
        f"first 5: {mismatches[:5]}"
    )


# tape/CVD columns that tape_features emits and trade_matrix stores
TAPE_COLS = [
    "pm_sofar_cvd", "pm_sofar_abscvd", "pm_sofar_eff", "pm_sofar_crosses",
    "pm_sofar_patheff", "pm_sofar_conf", "op_sofar_cvd", "op_sofar_eff", "op_sofar_conf",
    "d5", "d5_conf", "d15", "d15_conf", "d30", "d30_conf",
    "pathpos", "fill_vol_rel", "fill_delta", "fill_delta_conf",
]


def _tape_prep():
    """Replicate scripts/trade_matrix.py's fp_minutes preprocessing exactly."""
    if not MATRIX.exists() or not FP_MINUTES.exists():
        pytest.skip("output/trade_matrix.parquet or output/fp_minutes.parquet absent "
                    "— tape parity gate runs where the data lives")
    m = pd.read_parquet(FP_MINUTES)
    m.index = pd.DatetimeIndex(m.index)
    m = m.sort_index()
    m["cum"] = m.groupby("sday").delta.cumsum()
    m["runmin"] = m.groupby("sday").cum.cummin()
    m["runmax"] = m.groupby("sday").cum.cummax()
    daymed = m.groupby("sday").vol.median()
    byday = {d: g for d, g in m.groupby("sday")}
    return byday, daymed


def test_tape_features_reproduce_backtest_matrix():
    byday, daymed = _tape_prep()
    trades = pd.read_parquet(MATRIX)
    checked, mismatches = 0, []
    for t in trades.itertuples():
        g = byday.get(str(t.day))
        if g is None:
            continue
        upto = g[g.index < t.fillmi]
        got = tape_features(upto, t.direction, t.fillmi, float(daymed[str(t.day)]))
        for col in TAPE_COLS:
            if not hasattr(t, col):
                continue
            if not _eq(getattr(t, col), got.get(col, float("nan"))):
                mismatches.append((str(t.day), str(t.fillmi), col,
                                   getattr(t, col), got.get(col, float("nan"))))
        checked += 1
    assert checked > 0, "no trades checked — fp_minutes/trade_matrix day keys don't line up"
    assert not mismatches, (
        f"{len(mismatches)} tape-feature mismatches across {checked} trades; "
        f"first 5: {mismatches[:5]}"
    )
