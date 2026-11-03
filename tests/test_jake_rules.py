"""Value area is known at 09:30, and a later bar cannot fill an order that does not exist yet."""

import numpy as np
import pandas as pd

from src.research.strategies.jake_rules import first_fill, profiles_at_open, value_area


def test_value_area_starts_at_the_heaviest_price():
    prices = np.array([10, 11, 12, 13, 14])
    volumes = np.array([1.0, 1.0, 10.0, 1.0, 1.0])
    val, vah, poc = value_area(prices, volumes)
    assert poc == 12
    assert val == vah == 12


def test_monday_profile_excludes_the_cash_session():
    ny = "America/New_York"
    rows = [
        # Sunday 18:00, Monday session. This bar is known at Monday's open.
        ("2024-06-02 18:00", 18 * 60, 100.2, 5.0, 1),
        ("2024-06-02 18:01", 18 * 60 + 1, 101.0, 5.0, 1),
        # Monday 09:30 and 10:00 are not known yet.
        ("2024-06-03 09:30", 9 * 60 + 30, 200.0, 10.0, 1),
        ("2024-06-03 10:00", 10 * 60, 300.0, 10.0, 1),
        # Tuesday's overnight, then Tuesday's open, which must not enter Tuesday's profile.
        ("2024-06-03 18:00", 18 * 60, 110.0, 5.0, 2),
        ("2024-06-04 09:30", 9 * 60 + 30, 400.0, 1000.0, 2),
    ]
    ts, hm, close, vol, sess = zip(*rows, strict=True)
    df = pd.DataFrame({
        "ts_event": pd.to_datetime(list(ts)).tz_localize(ny),
        "hm": hm,
        "close": close,
        "volume": vol,
        "sess": sess,
    })
    areas = profiles_at_open(df)
    monday = areas[pd.Timestamp("2024-06-03 09:30", tz=ny)]
    tuesday = areas[pd.Timestamp("2024-06-04 09:30", tz=ny)]
    assert monday == (100.0, 101.0, 100.0)
    assert tuesday[1] == 300.0
    assert tuesday[2] != 400.0


def test_first_fill_starts_after_the_signal_bar():
    o = np.array([100.0, 101.0, 100.5])
    h = np.array([101.0, 101.5, 101.0])
    l = np.array([99.0, 100.75, 100.5])
    c = np.array([100.5, 101.0, 100.6])
    hm = np.array([9 * 60 + 30, 9 * 60 + 31, 9 * 60 + 32])
    # Buy limit at 100. Bar 0 trades through it. The order starts at bar 1, so that bar cannot fill.
    order = (1, 100.0, 90.0, 110.0, 1, 3)
    assert first_fill(o, h, l, c, hm, [order], True) is None
