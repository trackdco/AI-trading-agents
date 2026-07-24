"""Ingestor orchestration tests against synthetic sequences (LIVE-STACK Step 4).

Verifies the rolling minute-tape accumulator (session-anchored cum/runmin/runmax) and that
feature_row assembles tape/CVD + depth families from live-pushed state — no lookahead.
"""
from __future__ import annotations

import math

import pandas as pd

from src.canon.ingestor import CanonIngestor, MinuteTape, ReplaySource

NY = "America/New_York"


def _ts(day, hm):
    return pd.Timestamp(f"{day} {hm}", tz=NY).tz_convert("UTC")


def test_minute_tape_running_state_per_session():
    t = MinuteTape()
    # three 08:xx minutes on 2026-03-17; cum = running CVD, runmin/runmax track it
    for hm, d in (("08:00", 10.0), ("08:01", -4.0), ("08:02", 6.0)):
        t.add_minute(_ts("2026-03-17", hm), d, vol=100.0, vwp=10.0)
    df = t.frame()
    assert list(df.cum) == [10.0, 6.0, 12.0]
    assert list(df.runmin) == [10.0, 6.0, 6.0]
    assert list(df.runmax) == [10.0, 10.0, 12.0]
    assert list(df.sday) == ["2026-03-17"] * 3
    assert list(df.hm) == [480, 481, 482]


def test_minute_tape_resets_cum_on_new_session():
    t = MinuteTape()
    t.add_minute(_ts("2026-03-17", "20:00"), 5.0, 1.0, 1.0)   # session 2026-03-18 (post 18:00)
    t.add_minute(_ts("2026-03-18", "08:00"), 3.0, 1.0, 1.0)   # same session 2026-03-18
    t.add_minute(_ts("2026-03-19", "08:00"), 7.0, 1.0, 1.0)   # new session 2026-03-19
    df = t.frame()
    assert list(df.sday) == ["2026-03-18", "2026-03-18", "2026-03-19"]
    assert list(df.cum) == [5.0, 8.0, 7.0]                    # cum resets on the new session


def test_feature_row_tape_family_no_lookahead():
    ing = CanonIngestor()
    for hm, d in (("08:00", 10.0), ("08:01", -4.0), ("08:02", 6.0)):
        ing.on_minute_tape(_ts("2026-03-17", hm), d, vol=100.0, vwp=10.0)
    # trigger just after the last minute
    f = ing.feature_row(_ts("2026-03-17", "08:03"), entry=101.0, direction="long")
    assert f["pm_sofar_cvd"] == 12.0                          # 10 - 4 + 6, all pre-fill
    assert f["pm_sofar_conf"] == 1                            # cvd>0 and long
    assert f["d5"] == 12.0 and f["fill_delta"] == 6.0
    # a fill BEFORE the last minute must not see it (no lookahead)
    f2 = ing.feature_row(_ts("2026-03-17", "08:02"), entry=101.0, direction="long")
    assert f2["pm_sofar_cvd"] == 6.0                          # only 08:00 + 08:01


def test_feature_row_depth_family_from_book():
    ing = CanonIngestor()
    ing.on_depth({"action": "A", "order_id": 1, "side": "B", "price": 100.0, "size": 40})
    ing.on_depth({"action": "A", "order_id": 2, "side": "A", "price": 101.0, "size": 10})
    f = ing.feature_row(_ts("2026-03-17", "08:03"), entry=100.5, direction="long")
    assert f["dep_thick"] == 50 and math.isclose(f["dep_spread"], 1.0)
    assert f["dep_support"] == 40 and f["dep_resist"] == 10   # long: bid=support


def test_replay_source_drives_bars_and_tape():
    bars = pd.DataFrame({
        "ts_event": [_ts("2026-03-17", "08:00"), _ts("2026-03-17", "08:01")],
        "open": [100.0, 101.0], "high": [101.0, 102.0], "low": [99.0, 100.0],
        "close": [100.5, 101.5], "volume": [500.0, 400.0],
    })
    fp = pd.DataFrame({"delta": [10.0, -4.0], "vol": [100.0, 80.0], "vwp": [100.0, 101.0]},
                      index=pd.DatetimeIndex([_ts("2026-03-17", "08:00"),
                                              _ts("2026-03-17", "08:01")]))
    ing = CanonIngestor()
    ReplaySource(bars, fp).drive(ing)
    assert len(ing._bars) == 2
    assert list(ing.tape.frame().cum) == [10.0, 6.0]
