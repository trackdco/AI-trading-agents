"""Data layer — load 1m NQ bars + the true aggressor-side footprint, and derive the
1-minute session-anchored CVD series. No lookahead is introduced here; downstream
readers slice on closed bars.

CVD sign: the raw footprint carries side B = aggressive BUY, A = aggressive SELL, so
per-minute delta = vol(B) - vol(A) is the CORRECT sign (a buy-dominated minute is
positive). We compute this fresh from the raw parquet and DO NOT negate it. (The
repo's legacy load_cvd_delta() returns the negative of this — that landmine only
applies to that helper, not to raw footprint. See README §CVD-sign.)
"""
from __future__ import annotations

import glob
from datetime import time as dtime

import numpy as np
import pandas as pd


def load_bars(path: str, tz: str) -> pd.DataFrame:
    """1m OHLCV, tz-aware NY, sorted, with a `day` (calendar) column."""
    b = pd.read_parquet(path)
    b["ts_event"] = pd.to_datetime(b["ts_event"], utc=True).dt.tz_convert(tz)
    b = b.sort_values("ts_event").reset_index(drop=True)
    b["day"] = b["ts_event"].dt.normalize()
    return b[["ts_event", "open", "high", "low", "close", "volume", "day"]]


def load_footprint_delta(cvd_glob: str, tz: str) -> pd.Series:
    """Per-minute aggressor delta = vol(B) - vol(A), indexed by tz-aware minute (NY)."""
    files = sorted(glob.glob(cvd_glob))
    if not files:
        raise FileNotFoundError(f"no footprint parquet matched {cvd_glob!r}")
    fp = pd.concat([pd.read_parquet(f, columns=["ts_minute", "side", "volume"]) for f in files],
                   ignore_index=True)
    fp["ts"] = pd.to_datetime(fp["ts_minute"], utc=True).dt.tz_convert(tz)
    fp["signed"] = np.where(fp["side"].to_numpy() == "B", fp["volume"], -fp["volume"])
    delta = fp.groupby("ts")["signed"].sum().sort_index()
    delta.name = "delta"
    return delta


def load_footprint_totals(cvd_glob: str, tz: str) -> pd.Series:
    """Per-minute TOTAL aggressor volume (B + A), indexed by tz-aware minute — for delta%."""
    files = sorted(glob.glob(cvd_glob))
    fp = pd.concat([pd.read_parquet(f, columns=["ts_minute", "volume"]) for f in files],
                   ignore_index=True)
    fp["ts"] = pd.to_datetime(fp["ts_minute"], utc=True).dt.tz_convert(tz)
    tot = fp.groupby("ts")["volume"].sum().sort_index()
    tot.name = "total"
    return tot


def session_cvd(delta: pd.Series, anchor: dtime) -> pd.Series:
    """Session-anchored cumulative CVD (1-min), reset each day at `anchor` (RTH open).

    A new session begins on the first minute at/after `anchor`; the running CVD is the
    cumulative sum of per-minute delta within the current session only.
    """
    idx = delta.index
    # session id = calendar day of the minute, but only minutes at/after anchor count;
    # minutes before anchor belong to the prior (overnight) reset — for an intraday RTH
    # strategy we simply anchor the cumulative sum at the first at/after-anchor minute per day.
    day = idx.normalize()
    at_or_after = idx.time >= anchor
    grp = pd.Series(day, index=idx).where(pd.Series(at_or_after, index=idx))
    # cumulative only over the at/after-anchor minutes, reset per day
    sub = delta[at_or_after]
    csum = sub.groupby(sub.index.normalize()).cumsum()
    out = pd.Series(np.nan, index=idx, name="cvd_session")
    out.loc[csum.index] = csum.values
    return out
