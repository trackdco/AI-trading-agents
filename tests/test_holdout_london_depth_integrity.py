"""The 2023/24 London holdout book must load through the same path as the fit window."""
from __future__ import annotations

import glob
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
DEPTH = ROOT / "data/reference/depth_london_2023_24"
REF = ROOT / "data/reference/depth_london/glbx-mdp3-20250602.mbp-10_condensed.csv"
SEALED = ROOT / "data/reference/holdout_2023_24_days.csv"

FILES = sorted(glob.glob(str(DEPTH / "glbx-mdp3-*.csv")))
pytestmark = pytest.mark.skipif(not FILES or not REF.exists(),
                                reason="london holdout depth not installed")


def _day(path: str) -> str:
    ds = Path(path).name.split("-")[2].split(".")[0]
    return f"{ds[:4]}-{ds[4:6]}-{ds[6:]}"


@pytest.fixture(scope="module")
def frames():
    return {_day(f): pd.read_csv(f) for f in FILES}


def test_every_sealed_day_is_present(frames):
    sealed = set(pd.read_csv(SEALED, dtype=str)["day"])
    assert not sorted(sealed - set(frames)), "sealed days missing from London depth"
    assert not set(frames) - sealed, "London depth files outside the seal"


def test_columns_match_the_fit_window_wide_format(frames):
    ref = list(pd.read_csv(REF).columns)
    for day, d in frames.items():
        assert list(d.columns) == ref, f"{day}: {len(d.columns)} cols vs {len(ref)}"


def test_order_count_columns_survive(frames):
    """The one thing London keeps that NY drops — do not let a reformat lose it."""
    for day, d in frames.items():
        for i in range(10):
            assert f"bid_ct_{i:02d}" in d.columns, f"{day}: bid_ct_{i:02d} missing"
            assert f"ask_ct_{i:02d}" in d.columns, f"{day}: ask_ct_{i:02d} missing"


def test_one_row_per_minute_and_no_short_sessions(frames):
    for day, d in frames.items():
        ts = pd.to_datetime(d.ts_event, utc=True)
        assert len(d) == ts.nunique(), f"{day}: duplicate minutes"
        assert len(d) == 120, f"{day}: {len(d)} minutes, expected 120"


def test_window_is_0800_to_1000_london(frames):
    for day, d in frames.items():
        ts = pd.to_datetime(d.ts_event, utc=True).dt.tz_convert("Europe/London")
        assert ts.dt.hour.min() == 8, f"{day}: starts {ts.min()}"
        assert ts.dt.hour.max() == 9, f"{day}: runs past 10:00 ({ts.max()})"


def test_prices_are_decoded_floats_not_fixed_point(frames):
    for day, d in frames.items():
        assert d.bid_px_00.between(5_000, 40_000).all(), f"{day}: prices look wrong"


def test_london_depth_loader_reads_the_holdout(frames):
    """The real integration: london_depth.load_day pointed at the holdout folder."""
    import scripts.london_depth as L

    original = L.DIR
    try:
        L.DIR = DEPTH
        day = min(frames)
        d = L.load_day(day)
        assert d is not None and len(d) == 2400, f"{day}: {0 if d is None else len(d)} rows"
        assert set(d.side.unique()) == {"bid", "ask"}
        f = L.depth_at(d, d.ts.iloc[len(d) // 2], float(d.price.median()), "long")
        assert f and f["dep_thick"] > 0
    finally:
        L.DIR = original
