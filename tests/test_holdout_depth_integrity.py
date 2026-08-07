"""The 2023/24 holdout depth must be readable by the SAME loaders as the fit window.

The point of a holdout is that its verdict is trustworthy. A silently-short day, a dropped
book level or a lost timezone would all produce a confident wrong answer about whether the
canon generalises, so each is asserted rather than assumed.
"""
from __future__ import annotations

import glob
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
DEPTH = ROOT / "data/reference/depth_2023_24"
REF = ROOT / "data/reference/depth_2025/nq_depth_2025-06-02_ny.csv"
SEALED = ROOT / "data/reference/holdout_2023_24_days.csv"

FILES = sorted(glob.glob(str(DEPTH / "nq_depth_*_ny.csv")))
pytestmark = pytest.mark.skipif(not FILES or not REF.exists(),
                                reason="holdout depth not installed")


@pytest.fixture(scope="module")
def frames():
    return {Path(f).stem.split("_")[2]: pd.read_csv(f) for f in FILES}


def test_every_sealed_day_has_a_depth_file(frames):
    sealed = set(pd.read_csv(SEALED, dtype=str)["day"])
    missing = sorted(sealed - set(frames))
    assert not missing, f"{len(missing)} sealed days without depth: {missing[:10]}"
    assert not set(frames) - sealed, "depth files for days outside the seal"


def test_columns_match_the_fit_window_format(frames):
    ref = list(pd.read_csv(REF).columns)
    for day, d in frames.items():
        assert list(d.columns) == ref, f"{day}: {list(d.columns)} != {ref}"


def test_every_minute_carries_all_twenty_levels(frames):
    """10 bid + 10 ask. A short minute means a truncated book, not a quiet market."""
    for day, d in frames.items():
        per_min = d.groupby("ts").size()
        assert (per_min == 20).all(), (
            f"{day}: {int((per_min != 20).sum())} minutes without 20 levels "
            f"(min {per_min.min()}, max {per_min.max()})")


def test_sides_are_bid_and_ask(frames):
    for day, d in frames.items():
        assert set(d.side.unique()) == {"bid", "ask"}, f"{day}: {set(d.side.unique())}"


def test_timestamps_keep_their_eastern_offset(frames):
    """Naive timestamps would silently shift every fill-minute lookup by hours."""
    for day, d in frames.items():
        first = str(d.ts.iloc[0])
        assert first.endswith(("-04:00", "-05:00")), f"{day}: no ET offset on {first!r}"


def test_window_is_0800_to_1030_et(frames):
    """One minute of slack at the open is expected, not a defect.

    The request boundary is on receive time while the snapshot is stamped with EVENT time,
    so an event arriving just after 08:00:00 can carry a ts_event a fraction earlier and
    floor to 07:59. Observed on 2024-03-22 and nowhere else. It cannot affect anything:
    depth_at takes the last snapshot at-or-before the fill minute, and the earliest canon
    fill is 08:01.
    """
    for day, d in frames.items():
        ts = pd.to_datetime(d.ts)
        mins = ts.dt.hour * 60 + ts.dt.minute
        assert 8 * 60 - 1 <= mins.min() <= 8 * 60, f"{day}: starts {ts.min()}"
        assert mins.max() <= 10 * 60 + 30, f"{day}: runs past 10:30 ({ts.max()})"


def test_the_window_covers_every_canon_fill_minute(frames):
    """The window must reach every minute a canon trade has ever filled in."""
    book = ROOT / "output/canon_book.parquet"
    if not book.exists():
        pytest.skip("canon_book not built")
    fills = pd.read_parquet(book)
    fills = fills.loc[fills["size"] > 0, "fillhm"]
    covered_to = min((pd.to_datetime(d.ts).dt.hour * 60
                      + pd.to_datetime(d.ts).dt.minute).max() for d in frames.values())
    assert covered_to >= fills.max(), (
        f"depth stops at {covered_to} but fills run to {fills.max()}")


def test_prices_and_sizes_are_plausible(frames):
    for day, d in frames.items():
        assert d.price.between(5_000, 40_000).all(), f"{day}: off-band prices"
        assert (d["size"] > 0).all(), f"{day}: non-positive resting size"


def test_canonical_depth_at_reads_a_holdout_day(frames):
    """The function the LIVE ingestor calls must work on this data unchanged."""
    from src.canon.features import depth_at

    day = min(frames)
    d = frames[day].copy()
    d["ts"] = pd.to_datetime(d.ts)
    f = depth_at(d, d.ts.iloc[len(d) // 2], float(d.price.median()), "long")
    assert f, "depth_at returned nothing on holdout data"
    for k in ("dep_thick", "dep_imb", "dep_spread", "dep_support", "dep_resist"):
        assert k in f, f"missing {k}"
    assert f["dep_thick"] > 0
