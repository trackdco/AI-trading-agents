"""Indicator layer — pure, no-lookahead functions over the 1m frame and its
close-labeled resamples.

The VWAP / Bollinger / volume-profile math is VENDORED verbatim from the proven
engine (src/engine/indicators.py) so this package is self-contained and its
closed-bar semantics are identical to the audited engine:

  * 1m base frame is START-labeled (ts_event = interval open); a 1m bar stamped T
    is still forming at T and closes at T+1min.
  * Resampled frames are CLOSE-labeled (closed='left', label='right'): a 5m bar
    stamped 09:35 aggregates 09:30..09:34 and is actionable at 09:35.

Every "as-of ts" reader uses ONLY bars fully closed at ts. No lookahead anywhere.
"""
from __future__ import annotations

from datetime import time as dtime

import numpy as np
import pandas as pd

_ONE_MIN = pd.Timedelta(minutes=1)
_BIN_EPS = 1e-9
_VA_EPS = 1e-9
_OHLCV_AGG = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}


# ---------------------------------------------------------------- resample (vendored)

def resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """1m -> rule bars stamped by CLOSE time (closed='left', label='right'). Empty bins dropped."""
    out = (df.set_index("ts_event").resample(rule, closed="left", label="right").agg(_OHLCV_AGG)
             .dropna(subset=["open"]).reset_index())
    out["volume"] = out["volume"].astype("int64")
    return out


# ---------------------------------------------------------------- session grouping (vendored)

def anchor_session_date(ts: pd.Series, session_open: dtime) -> pd.Series:
    """CME session (trade) date per bar. Bars at/after session_open belong to the NEXT day."""
    roll_next = ts.dt.time >= session_open
    return (ts.dt.normalize() + pd.to_timedelta(roll_next.astype(int), unit="D")).dt.date


def session_date_scalar(ts: pd.Timestamp, session_open: dtime):
    """Scalar version of anchor_session_date — avoids per-call Series construction in hot loops."""
    d = ts.normalize()
    if ts.time() >= session_open:
        d = d + pd.Timedelta(days=1)
    return d.date()


# ---------------------------------------------------------------- Bollinger (vendored)

def bollinger(df: pd.DataFrame, length: int, mult: float) -> pd.DataFrame:
    """BB(length, SMA of close, mult*sigma), population stdev (ddof=0) — TradingView parity."""
    close = df["close"].astype("float64")
    basis = close.rolling(length).mean()
    sd = close.rolling(length).std(ddof=0)
    return pd.DataFrame({"ts_event": df["ts_event"], "basis": basis,
                         "upper": basis + mult * sd, "lower": basis - mult * sd}, index=df.index)


# ---------------------------------------------------------------- anchored VWAP (vendored)

def _anchored_vwap(df: pd.DataFrame, group: pd.Series, bands: list[int]) -> pd.DataFrame:
    """Running TradingView VWAP +/- k*sigma per anchor group (volume-weighted stdev)."""
    src = (df["high"] + df["low"] + df["close"]).astype("float64") / 3.0  # hlc3
    vol = df["volume"].astype("float64")
    cum_v = vol.groupby(group).cumsum()
    cum_pv = (vol * src).groupby(group).cumsum()
    cum_pv2 = (vol * src * src).groupby(group).cumsum()
    vwap = cum_pv / cum_v
    var = (cum_pv2 / cum_v - vwap * vwap).clip(lower=0.0)
    sd = np.sqrt(var)
    out = pd.DataFrame({"ts_event": df["ts_event"], "vwap": vwap}, index=df.index)
    for k in bands:
        out[f"upper_{k}"] = vwap + k * sd
        out[f"lower_{k}"] = vwap - k * sd
    return out


def daily_vwap(df_1m: pd.DataFrame, bands=(1, 2, 3), session_open: dtime = dtime(18, 0)) -> pd.DataFrame:
    """Session-anchored VWAP +/- k*sigma, anchored at the CME open (18:00 ET). Resets each session."""
    group = anchor_session_date(df_1m["ts_event"], session_open)
    return _anchored_vwap(df_1m, group, list(bands))


# ---------------------------------------------------------------- volume profile (vendored)

def volume_profile(sl: pd.DataFrame, bin_points: float, value_area_pct: float) -> dict | None:
    """POC/VAH/VAL from 1m bars (volume spread uniformly across touched 0.25-bins; VA 70%)."""
    if sl.empty:
        return None
    lo_i = np.floor(sl["low"].to_numpy("float64") / bin_points + _BIN_EPS).astype(int)
    hi_i = np.floor(sl["high"].to_numpy("float64") / bin_points + _BIN_EPS).astype(int)
    vol = sl["volume"].to_numpy("float64")
    imin, imax = int(lo_i.min()), int(hi_i.max())
    hist = np.zeros(imax - imin + 1)
    for lo, hi, v in zip(lo_i, hi_i, vol):
        hist[lo - imin: hi - imin + 1] += v / (hi - lo + 1)
    centers = (np.arange(imin, imax + 1) + 0.5) * bin_points
    n = len(hist); total = float(hist.sum())
    poc_i = int(np.argmax(hist)); lo_va = hi_va = poc_i; covered = hist[poc_i]
    target = value_area_pct / 100.0 * total
    while covered + _VA_EPS < target and (lo_va > 0 or hi_va < n - 1):
        below = hist[lo_va - 1] if lo_va > 0 else -np.inf
        above = hist[hi_va + 1] if hi_va < n - 1 else -np.inf
        if above >= below:
            hi_va += 1; covered += hist[hi_va]
        else:
            lo_va -= 1; covered += hist[lo_va]
    return dict(poc=float(centers[poc_i]), vah=float(centers[hi_va]), val=float(centers[lo_va]),
                total_volume=total)


# ---------------------------------------------------------------- ATR / Keltner volatility bands

def atr(df: pd.DataFrame, length: int) -> pd.Series:
    """Wilder ATR over a TF frame. True range then Wilder EMA (alpha = 1/length)."""
    h = df["high"].astype("float64"); l = df["low"].astype("float64"); c = df["close"].astype("float64")
    prev_c = c.shift(1)
    tr = pd.concat([h - l, (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / length, adjust=False, min_periods=length).mean()


def keltner(df: pd.DataFrame, ema_length: int, atr_length: int, mult: float) -> pd.DataFrame:
    """Keltner Channels: EMA(ema_length) +/- mult*ATR(atr_length). The documented vol band."""
    ema = df["close"].astype("float64").ewm(span=ema_length, adjust=False,
                                             min_periods=ema_length).mean()
    a = atr(df, atr_length)
    return pd.DataFrame({"ts_event": df["ts_event"], "kc_mid": ema,
                         "kc_upper": ema + mult * a, "kc_lower": ema - mult * a}, index=df.index)


# ---------------------------------------------------------------- pivots / swings

def pivots(df: pd.DataFrame, k: int) -> pd.DataFrame:
    """Fractal pivots: a swing high is a bar whose high is the max of the +/-k window
    (strictly greater than the k bars each side), swing low symmetric. Confirmed only k
    bars later — the caller must treat a pivot as known no earlier than index+k (no lookahead).
    Returns df with bool columns piv_high / piv_low."""
    h = df["high"].to_numpy("float64"); l = df["low"].to_numpy("float64"); n = len(df)
    ph = np.zeros(n, bool); pl = np.zeros(n, bool)
    for i in range(k, n - k):
        wl, wr = slice(i - k, i), slice(i + 1, i + k + 1)
        if h[i] > h[wl].max() and h[i] > h[wr].max():
            ph[i] = True
        if l[i] < l[wl].min() and l[i] < l[wr].min():
            pl[i] = True
    out = df.copy(); out["piv_high"] = ph; out["piv_low"] = pl
    return out


# ---------------------------------------------------------------- rejection candle

def is_rejection(o: float, h: float, l: float, c: float, level: float, direction: str,
                 wick_frac: float) -> bool:
    """A candle that wicks THROUGH `level` and closes back on the trade side.
    long  = low pierces below level, close back above, lower wick >= wick_frac of range.
    short = high pierces above level, close back below, upper wick >= wick_frac of range.
    """
    rng = h - l
    if rng <= 0:
        return False
    if direction == "long":
        lower_wick = min(o, c) - l
        return l < level and c > level and lower_wick >= wick_frac * rng
    else:
        upper_wick = h - max(o, c)
        return h > level and c < level and upper_wick >= wick_frac * rng
