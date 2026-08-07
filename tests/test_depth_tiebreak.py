"""Wall selection must be a function of the BOOK, not of the row order it arrives in.

`depth_at` picks the "wall" as the largest visible level on each side of the entry. When
two levels tie on size — common, not exotic, on a book whose levels hold a median 3
contracts — `idxmax` resolves the tie by row position. Row position is an artefact of how
the long frame was assembled, so the same book concatenated in a different order yields a
different wall, a different `dep_wall_*_d`, and a different `FAR = wall_ahead_d > 4.5`.

Measured on the 749-fill fit matrix when this was found (2026-08-07): the two rules
disagree on 180 rows, all of them exact size ties; 45 rows get a different wall distance
and 9 flip FAR.

The fix is largest size, then NEAREST price, with a stable sort. These tests fail on the
`idxmax` version — verified by reverting the patch and re-running, not by assertion.
"""
from __future__ import annotations

import pandas as pd
import pytest

from scripts.london_depth import depth_at

MINUTE = pd.Timestamp("2026-04-15 03:30", tz="America/New_York")


def _book(rows) -> pd.DataFrame:
    """rows: list of (side, price, size) -> the long frame depth_at consumes."""
    return pd.DataFrame([{"ts": MINUTE, "side": s, "price": p, "size": z}
                         for s, p, z in rows])


#: One tie on each side. Above the entry, 21010 and 21030 both hold 9 contracts; below,
#: 20990 and 20970 both hold 8. A correct rule takes the NEAREST of each tied pair.
TIED = [("bid", 20990.0, 8.0), ("bid", 20970.0, 8.0), ("bid", 20950.0, 3.0),
        ("ask", 21010.0, 9.0), ("ask", 21030.0, 9.0), ("ask", 21050.0, 2.0)]
ENTRY = 21000.0


def test_wall_choice_is_independent_of_row_order():
    """THE REGRESSION GUARD: same book, two row orders, identical output.

    This is the whole point. It does not assert which wall is right — only that the
    answer cannot depend on something that carries no information.
    """
    forward = depth_at(_book(TIED), MINUTE, ENTRY, "long")
    reversed_ = depth_at(_book(list(reversed(TIED))), MINUTE, ENTRY, "long")
    assert forward == reversed_, (
        "depth_at returned different walls for the same book in a different row order — "
        f"forward {forward}, reversed {reversed_}. The tie-break is order-dependent.")


@pytest.mark.parametrize("direction", ["long", "short"])
def test_order_independence_holds_for_both_directions(direction):
    """`direction` swaps which side is support vs resist; the walls must not move."""
    a = depth_at(_book(TIED), MINUTE, ENTRY, direction)
    b = depth_at(_book(list(reversed(TIED))), MINUTE, ENTRY, direction)
    assert a == b


def test_tie_resolves_to_the_nearest_level():
    """Largest size, then NEAREST price — the declared rule, pinned by value.

    Nearest is the right reading: a wall's relevance to a trade is how soon price meets
    it, so between two equal-sized levels the closer one is the binding one.
    """
    f = depth_at(_book(TIED), MINUTE, ENTRY, "long")
    assert f["dep_wall_above_sz"] == 9.0
    assert f["dep_wall_above_d"] == 10.0, "must pick 21010 (nearest of the tied 9s), not 21030"
    assert f["dep_wall_below_sz"] == 8.0
    assert f["dep_wall_below_d"] == 10.0, "must pick 20990 (nearest of the tied 8s), not 20970"


def test_a_strictly_larger_far_level_still_wins():
    """Size dominates distance — the tie-break only applies WITHIN a size tie."""
    rows = [("bid", 20990.0, 3.0), ("bid", 20950.0, 40.0),
            ("ask", 21010.0, 3.0), ("ask", 21060.0, 40.0)]
    f = depth_at(_book(rows), MINUTE, ENTRY, "long")
    assert f["dep_wall_above_sz"] == 40.0 and f["dep_wall_above_d"] == 60.0
    assert f["dep_wall_below_sz"] == 40.0 and f["dep_wall_below_d"] == 50.0


def test_three_way_tie_is_also_stable():
    """More than two tied levels — the sort must still be total and stable."""
    rows = [("ask", 21010.0, 5.0), ("ask", 21020.0, 5.0), ("ask", 21030.0, 5.0),
            ("bid", 20990.0, 5.0), ("bid", 20980.0, 5.0), ("bid", 20970.0, 5.0)]
    orders = [rows, list(reversed(rows)), rows[3:] + rows[:3]]
    out = [depth_at(_book(o), MINUTE, ENTRY, "long") for o in orders]
    assert out[0] == out[1] == out[2]
    assert out[0]["dep_wall_above_d"] == 10.0 and out[0]["dep_wall_below_d"] == 10.0
