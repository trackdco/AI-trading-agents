"""Tests for src/live/detector.py — streamed trigger detection (Phase 4 Stage 8).

Band/tail/window logic is tested fast with a stub detect function. Real-data
stream==cache equivalence is the Stage-8 harness (scripts/detector_parity.py).
"""

from types import SimpleNamespace

import pandas as pd

from src.live.detector import LiveDetector
from src.live.feed import Bar

NY = "America/New_York"


def _bar(ts, c=25000.0):
    t = pd.Timestamp(ts, tz=NY)
    return Bar(ts_event=t, open=c, high=c + 1, low=c - 1, close=c, volume=100.0)


def _stub(windows, out=()):
    def detect(df, start=None, end=None):
        windows.append((start, end))
        return list(out)
    return detect


def test_outside_band_no_detection():
    wins = []
    det = LiveDetector(detect_fn=_stub(wins))
    assert det.on_bar(pd.DataFrame(), _bar("2026-03-17 07:30")) == []   # pre-band
    assert det.on_bar(pd.DataFrame(), _bar("2026-03-17 12:00")) == []   # post-band+tail
    assert wins == [] and det.calls == 0


def test_tail_window_clamped_to_band():
    wins = []
    det = LiveDetector(detect_fn=_stub(wins))
    det.on_bar(pd.DataFrame(), _bar("2026-03-17 07:50"))
    lo, hi = wins[0]
    assert lo == pd.Timestamp("2026-03-17 07:45", tz=NY)    # clamped to band start
    assert hi == pd.Timestamp("2026-03-17 07:50", tz=NY)    # never beyond the bar
    det.on_bar(pd.DataFrame(), _bar("2026-03-17 09:30"))
    lo2, hi2 = wins[1]
    assert lo2 == pd.Timestamp("2026-03-17 09:20", tz=NY)   # 10-minute tail
    assert hi2 == pd.Timestamp("2026-03-17 09:30", tz=NY)


def test_post_band_grace_covers_late_closing_candles():
    wins = []
    det = LiveDetector(detect_fn=_stub(wins))
    det.on_bar(pd.DataFrame(), _bar("2026-03-17 11:05"))    # inside tail grace
    lo, hi = wins[0]
    assert hi == pd.Timestamp("2026-03-17 11:00", tz=NY)    # clamped to band end
    assert lo == pd.Timestamp("2026-03-17 10:55", tz=NY)


def test_unclassified_patterns_dropped():
    trigs = [SimpleNamespace(pattern="A"), SimpleNamespace(pattern="unclassified"),
             SimpleNamespace(pattern="B2")]
    det = LiveDetector(detect_fn=_stub([], out=trigs))
    out = det.on_bar(pd.DataFrame(), _bar("2026-03-17 09:00"))
    assert [t.pattern for t in out] == ["A", "B2"]
