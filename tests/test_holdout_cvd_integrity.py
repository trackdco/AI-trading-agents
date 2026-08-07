"""The 2023/24 holdout tape must be usable by the SAME loaders as the fit-window tape.

A holdout is only worth running if its inputs are trustworthy. These checks are cheap and
they fail loudly rather than letting a silently-short month produce a confident wrong
verdict about whether the canon generalises.
"""
from __future__ import annotations

import glob
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
CVD = ROOT / "data/reference/cvd"
SEALED = ROOT / "data/reference/holdout_2023_24_days.csv"
NY = "America/New_York"

HOLDOUT = sorted(glob.glob(str(CVD / "footprint_holdout_*.parquet")))
REF = CVD / "footprint_apr2026.parquet"

pytestmark = pytest.mark.skipif(not HOLDOUT or not REF.exists(),
                                reason="holdout CVD not installed")


@pytest.fixture(scope="module")
def tape():
    return {f: pd.read_parquet(f) for f in HOLDOUT}


def test_schema_and_dtypes_match_the_committed_reference(tape):
    ref = pd.read_parquet(REF)
    for f, d in tape.items():
        assert list(d.columns) == list(ref.columns), f"{Path(f).name} schema drift"
        assert d.ts_minute.dtype == ref.ts_minute.dtype, f"{Path(f).name} ts resolution/tz"
        assert d.volume.dtype == np.int64, f"{Path(f).name} volume not int64 (uint32 wraps)"
        assert d.trades.dtype == np.int64, f"{Path(f).name} trades not int64"


def test_every_sealed_day_is_present_in_the_tape(tape):
    sealed = set(pd.read_csv(SEALED, dtype=str)["day"])
    present = set()
    for d in tape.values():
        ts = pd.to_datetime(d.ts_minute, utc=True).dt.tz_convert(NY)
        present |= set(ts.dt.strftime("%Y-%m-%d"))
    missing = sorted(sealed - present)
    assert not missing, f"{len(missing)} sealed days absent from the tape: {missing[:10]}"


def test_no_duplicate_minutes_across_files(tape):
    """Overlapping months would double-count volume in any concatenated CVD series."""
    idx = pd.concat([pd.Series(pd.to_datetime(d.ts_minute, utc=True).unique())
                     for d in tape.values()])
    assert not idx.duplicated().any(), "the same minute appears in two holdout files"


def test_sides_are_B_and_A_only(tape):
    for f, d in tape.items():
        assert set(d.side.unique()) <= {"B", "A"}, f"{Path(f).name}: unexpected side values"


def test_prices_are_plausible_front_month_NQ(tape):
    """Guards the band-clean. Calendar-spread prints land in the low hundreds — the
    existing q3/q4 2025 reference files carry ~2% of exactly that contamination."""
    for f, d in tape.items():
        assert d.price.between(5_000, 40_000).all(), (
            f"{Path(f).name}: {int((~d.price.between(5_000, 40_000)).sum())} rows off-band "
            f"({d.price.min():,.0f}-{d.price.max():,.0f})")


def test_window_is_the_overnight_span_the_features_need(tape):
    """CVD features reach back through Asia and London, so the tape must cover
    18:00 ET (prior day) -> 11:00 ET, i.e. ET hours 18-23 and 0-10 — and nothing else."""
    hours = set()
    for d in tape.values():
        ts = pd.to_datetime(d.ts_minute, utc=True).dt.tz_convert(NY)
        hours |= {int(h) for h in ts.dt.hour.unique()}
    assert hours <= set(range(11)) | set(range(18, 24)), f"unexpected ET hours: {sorted(hours)}"
    assert {0, 3, 8, 10, 18, 22} <= hours, f"window is short: {sorted(hours)}"


def test_volume_is_positive_everywhere(tape):
    for f, d in tape.items():
        assert (d.volume > 0).all(), f"{Path(f).name}: non-positive volume rows"
        assert (d.trades > 0).all(), f"{Path(f).name}: non-positive trade counts"
