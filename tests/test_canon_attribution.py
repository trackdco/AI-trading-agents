"""Rejection attribution must reproduce the committed canon book exactly.

The whole value of `rejected_by` is that it says WHICH layer skipped a candidate. If the
re-walk drifts from build_canon's ordering it will still emit confident-looking reasons,
just wrong ones — so the self-validation (re-derived size == the book's size) is the test
that matters, not a spot check on a few rows.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts.canon_attribution import ORDER, attribute

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "output/canon_book.parquet"

pytestmark = pytest.mark.skipif(not BOOK.exists(), reason="canon_book not built")


@pytest.fixture(scope="module")
def book():
    return pd.read_parquet(BOOK)


@pytest.fixture(scope="module")
def attributed(book):
    return attribute(book)


def test_rederived_size_matches_the_committed_book(book, attributed):
    """If this fails, every reason code is suspect — that is the point of it."""
    ref = book.sort_values("fill").reset_index(drop=True)["size"].to_numpy()
    assert np.isclose(ref, attributed["size_rederived"].to_numpy()).all()


def test_every_row_gets_exactly_one_reason(attributed):
    assert attributed.rejected_by.notna().all()
    assert set(attributed.rejected_by.unique()) <= set(ORDER)


def test_taken_and_rejected_partition_the_universe(book, attributed):
    taken = attributed[attributed.rejected_by == "taken"]
    rejected = attributed[attributed.rejected_by != "taken"]
    assert len(taken) + len(rejected) == len(attributed)
    assert (taken["size_rederived"] > 0).all(), "a 'taken' row must carry size"
    assert (rejected["size_rederived"] == 0).all(), "a rejected row must be sized 0"
    assert len(taken) == int((book["size"] > 0).sum())


def test_rejected_candidates_carry_their_counterfactual(attributed):
    """The learning signal: a skipped candidate must still say what it would have done."""
    rejected = attributed[attributed.rejected_by != "taken"]
    assert rejected.dollars.notna().all()


def test_dead_zone_default_matches_the_committed_book(book):
    """canon_mechanical.main() builds the book with NO gate; assuming otherwise misattributes.

    Regression for a real miss: defaulting dead_zones on silently mislabelled two 09:56
    golden candidates until the self-validation caught it.
    """
    with_zones = attribute(book, dead_zones=((595, 600),))
    ref = book.sort_values("fill").reset_index(drop=True)["size"].to_numpy()
    assert not np.isclose(ref, with_zones["size_rederived"].to_numpy()).all(), (
        "applying dead zones should DISAGREE with the committed book — if it agrees, "
        "the book already has them and the default is wrong")


def test_attribution_is_deterministic(book):
    a, b = attribute(book), attribute(book)
    pd.testing.assert_series_equal(a.rejected_by, b.rejected_by)
