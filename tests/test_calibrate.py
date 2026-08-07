"""Step 8 calibrator: tf parsing + the OPEN-clock matching convention."""
import pandas as pd

from src.backtest.calibrate import _tf_minutes, _within


def test_tf_minutes_parses_hand_and_engine_labels():
    assert _tf_minutes("2M") == 2
    assert _tf_minutes("5m") == 5
    assert _tf_minutes("3min") == 3
    assert _tf_minutes("1M") == 1
    assert _tf_minutes("garbage") == 0     # unparseable -> 0, never raises


def test_open_clock_shift_aligns_hand_open_to_engine_trigger():
    # hand "09:48" on 3M is the OPEN; the engine stamps that candle's CLOSE at 09:51.
    # engine open = trigger_ts - TF must equal the hand open -> 0 min apart.
    hand_open = pd.Timestamp("2026-02-11 09:48", tz="America/New_York")
    engine_trigger = pd.Timestamp("2026-02-11 09:51", tz="America/New_York")   # close label
    engine_open = engine_trigger - pd.Timedelta(minutes=_tf_minutes("3min"))
    assert _within(engine_open, hand_open) == 0.0


def test_within_is_symmetric_minutes():
    a = pd.Timestamp("2026-02-11 09:48", tz="America/New_York")
    b = pd.Timestamp("2026-02-11 10:03", tz="America/New_York")
    assert _within(a, b) == 15.0
    assert _within(b, a) == 15.0
