"""Minimal invariant tests. Run: python -m pytest market-engine/tests -q"""
from datetime import time

import numpy as np
import pandas as pd

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import indicators  # noqa: E402

TZ = "America/New_York"


def _frame(day="2026-01-13"):
    idx = pd.date_range(f"{day} 09:25", f"{day} 09:40", freq="1min", tz=TZ)
    n = len(idx)
    return pd.DataFrame({
        "open": np.linspace(100, 110, n), "high": np.linspace(101, 111, n),
        "low": np.linspace(99, 109, n), "close": np.linspace(100.5, 110.5, n),
        "volume": np.full(n, 10.0),
    }, index=idx)


def test_ny_vwap_nan_before_open_present_after():
    """Architecture invariant #1: NY VWAP does not exist before 09:30 ET."""
    df = _frame()
    nv = indicators.anchored_vwap(df, time(9, 30), only_after=True, bands=[1.0])
    assert nv.loc[df.index[df.index.time < time(9, 30)], "vwap"].isna().all()
    assert not np.isnan(nv.loc[pd.Timestamp("2026-01-13 09:35", tz=TZ), "vwap"])


def test_daily_vwap_exists_before_930():
    df = _frame()
    dv = indicators.anchored_vwap(df, time(18, 0), only_after=False, bands=[1.0])
    assert not dv["vwap"].isna().any()


def test_volume_profile_poc_in_range():
    df = _frame()
    vp = indicators.volume_profile(df, bin_pts=1.0, va_pct=0.70)
    assert df["low"].min() <= vp["poc"] <= df["high"].max()
    assert vp["val"] <= vp["poc"] <= vp["vah"]
