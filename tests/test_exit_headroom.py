"""Excursion must be PATH-CORRECT: a dead position cannot inherit a later move.

Regression for a real error. The first cut measured max favourable excursion from the fill
to 16:00 regardless of when the position died, so a trade stopped out at 09:00 picked up a
rally that happened at 15:00. It reported 84% of LOSING trades reaching +2R in profit —
impossible, and the tell that the measure was meaningless.
"""
from __future__ import annotations

import pandas as pd
import pytest

from scripts.exit_headroom import excursions

NY = "America/New_York"


def _bars(day, prices):
    """One bar per minute from 09:00 ET; `prices` are (low, high) pairs."""
    ts = pd.date_range(f"{day} 09:00", periods=len(prices), freq="1min", tz=NY)
    return pd.DataFrame({
        "ts": ts, "day": day,
        "mins": ts.hour * 60 + ts.minute,
        "low": [p[0] for p in prices],
        "high": [p[1] for p in prices],
        "open": [p[0] for p in prices], "close": [p[1] for p in prices],
        "volume": 100,
    })


def _book(day, entry, stop, direction="long", R=1.0, dollars=100.0):
    return pd.DataFrame([{
        "day": day, "fill": pd.Timestamp(f"{day} 09:00", tz=NY), "win_": "pre",
        "direction": direction, "entry": entry, "stop": stop, "risk": abs(entry - stop),
        "R": R, "dollars": dollars, "size": 1.0,
    }])


def test_stopped_out_position_does_not_inherit_a_later_rally():
    """THE BUG: long stops out on bar 2, then price triples. MFE must reflect the stop-out."""
    day = "2025-06-02"
    bars = _bars(day, [
        (100.0, 101.0),      # 09:00 fill at 100, stop 95
        (94.0, 100.0),       # 09:01 STOPPED OUT (low 94 <= 95)
        (100.0, 200.0),      # 09:02 huge rally the position never saw
        (200.0, 300.0),
    ])
    E = excursions(_book(day, entry=100.0, stop=95.0), bars)
    assert len(E) == 1
    row = E.iloc[0]
    assert row.stopped_out
    # risk = 5pts; the position only ever saw high 101 => (101-100)/5 = 0.2R
    assert row.mfe_R_eod == pytest.approx(0.2), f"inherited the rally: {row.mfe_R_eod}R"
    assert row.mfe_R_eod < 1.0


def test_surviving_position_keeps_its_full_excursion():
    day = "2025-06-02"
    bars = _bars(day, [
        (100.0, 101.0),
        (99.0, 110.0),       # never touches the 95 stop
        (105.0, 120.0),
    ])
    E = excursions(_book(day, entry=100.0, stop=95.0), bars)
    row = E.iloc[0]
    assert not row.stopped_out
    assert row.mfe_R_eod == pytest.approx(4.0)      # (120-100)/5


def test_short_side_uses_the_opposite_stop_and_extreme():
    day = "2025-06-02"
    bars = _bars(day, [
        (99.0, 100.0),       # fill 100, stop 105 (short)
        (90.0, 99.0),        # runs 2R in favour, never hits 105
        (85.0, 95.0),
    ])
    E = excursions(_book(day, entry=100.0, stop=105.0, direction="short"), bars)
    row = E.iloc[0]
    assert not row.stopped_out
    assert row.mfe_R_eod == pytest.approx(3.0)      # (100-85)/5


def test_short_stopped_out_does_not_inherit_a_later_selloff():
    day = "2025-06-02"
    bars = _bars(day, [
        (99.0, 100.0),
        (100.0, 106.0),      # STOPPED (high 106 >= 105)
        (10.0, 20.0),        # collapse the short never participated in
    ])
    E = excursions(_book(day, entry=100.0, stop=105.0, direction="short"), bars)
    row = E.iloc[0]
    assert row.stopped_out
    assert row.mfe_R_eod == pytest.approx(0.2)      # (100-99)/5
