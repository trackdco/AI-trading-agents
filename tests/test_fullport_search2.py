"""Prior-day value area is known before the cash open, and the pre-registered rules fire once."""

from types import SimpleNamespace

import numpy as np
import pandas as pd

from scripts.run_fullport_search2 import (
    attach,
    resolve_disp,
    resolve_fade,
    resolve_fail,
    trades_of,
)
from scripts.run_hf_limit import build_days

NY = "America/New_York"


def _day(rows, rth_open, i_open=0):
    hm, o, h, l, c = zip(*rows, strict=True)
    return SimpleNamespace(
        hm=np.array(hm),
        o=np.array(o, dtype=float),
        h=np.array(h, dtype=float),
        l=np.array(l, dtype=float),
        c=np.array(c, dtype=float),
        i_open=i_open,
        end=len(rows),
        rth_open=rth_open,
    )


def test_fade_first_touch_does_not_take_the_later_trade():
    area = (100.0, 120.0, 110.0)
    rows = [
        (570, 110.0, 110.5, 109.5, 110.0),
        (571, 110.0, 110.2, 100.0, 101.0),  # touches 100, does not trade through 99.75
        (572, 101.0, 101.0, 99.0, 100.0),  # would fill a resting order
    ]
    day = _day(rows, 110.0)
    first = resolve_fade(day, area, 0.0, "inside", "first")
    rest = resolve_fade(day, area, 0.0, "inside", "rest")
    assert first.placed and first.side == 0
    assert rest.side == 1 and rest.limit == 100.0 and rest.bar == 2
    assert trades_of(day, rest, 1.7)


def test_fade_stays_flat_when_price_never_comes_inside():
    area = (100.0, 120.0, 110.0)
    rows = [(570 + i, 130.0, 131.0, 129.0, 130.0) for i in range(5)]
    day = _day(rows, 130.0)
    ent = resolve_fade(day, area, 0.0, "any", "rest")
    assert ent.placed is False


def test_displacement_buys_the_retest_of_a_broken_high():
    area = (100.0, 120.0, 110.0)
    rows = [
        (570, 119.0, 126.0, 119.0, 125.0),  # closes 5 points through 120, body most of the range
        (571, 124.0, 124.5, 119.5, 122.0),  # trades through 120
    ]
    day = _day(rows, 119.0)
    ent = resolve_disp(day, area, 1, 4.0, "fixed", 60, "close")
    assert ent.placed and ent.side == 1 and ent.limit == 120.0
    assert ent.bar == 1
    # A down close through the low is not this long.
    down = [
        (570, 101.0, 101.0, 94.0, 95.0),
        (571, 96.0, 100.5, 95.0, 99.0),
    ]
    short = resolve_disp(_day(down, 101.0), area, 1, 4.0, "fixed", 60, "close")
    assert short.side == -1 and short.limit == 100.0


def test_failed_auction_needs_two_inside_blocks_then_sells_the_high():
    area = (100.0, 120.0, 110.0)
    rows = []
    for i in range(70):
        close = 130.0 if i < 20 else 110.0
        rows.append((570 + i, close, close + 0.5, close - 0.5, close))
    # Retest the high after the two inside blocks.
    rows.append((640, 115.0, 120.5, 114.0, 116.0))
    day = _day(rows, 130.0)
    ent = resolve_fail(day, area, "m30", "above")
    assert ent.placed and ent.side == -1 and ent.limit == 120.0
    early = _day(rows[:40], 130.0)
    assert resolve_fail(early, area, "m30", "above").placed is False


def test_prior_cash_profile_ignores_today():
    def session(day, sess, close, volume):
        start = pd.Timestamp(f"2024-06-{day:02d} 09:30", tz=NY)
        rows = []
        for i in range(40):
            ts = start + pd.Timedelta(minutes=i)
            px = float(close)
            rows.append({
                "ts_event": ts,
                "hm": 9 * 60 + 30 + i,
                "open": px, "high": px + 1, "low": px - 1, "close": px,
                "volume": volume,
                "vwap": px,
                "sess": sess,
                "onh": px + 5, "onl": px - 5,
                "pdh": 110.0, "pdl": 90.0, "pdc": 100.0,
            })
        return rows

    df = pd.DataFrame(session(3, 1, 100.0, 5.0) + session(4, 2, 400.0, 500.0))
    days = build_days(df)
    attach(df, days)
    assert len(days) == 2
    assert days[0].va_rth is None
    val, vah, poc = days[1].va_rth
    assert poc == 100.0
    assert val == vah == 100.0
    assert days[1].ctx_rth == "above"
