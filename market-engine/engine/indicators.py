"""Indicators — computable-only stack (§2).

- Bollinger Bands (20, SMA, close, 2σ) per timeframe.
- Anchored VWAP with volume-weighted std bands: daily (18:00 ET anchor) and
  NY-session (09:30 ET anchor; NaN before the anchor each day).
- Volume profile (POC / VAH / VAL) from 1m bars, volume spread across each
  bar's range (approximation vs tick data — documented, spec-1 §3).
"""
from __future__ import annotations

from datetime import time

import numpy as np
import pandas as pd


# ---------- Bollinger --------------------------------------------------------
def bollinger(df: pd.DataFrame, length: int = 20, k: float = 2.0) -> pd.DataFrame:
    ma = df["close"].rolling(length).mean()
    sd = df["close"].rolling(length).std(ddof=0)
    return pd.DataFrame({"bb_ma": ma, "bb_upper": ma + k * sd, "bb_lower": ma - k * sd})


# ---------- Anchored VWAP ----------------------------------------------------
def _anchor_group(idx: pd.DatetimeIndex, anchor: time) -> pd.Series:
    """Session-date key: the calendar date of the anchor that opened each bar's
    session. For an 18:00 anchor, bars at/after 18:00 belong to the next day's
    session; for 09:30, bars belong to their own date."""
    d = idx.normalize()
    after = (idx.hour > anchor.hour) | ((idx.hour == anchor.hour) & (idx.minute >= anchor.minute))
    key = d.copy()
    if anchor.hour >= 12:  # evening anchor (daily 18:00) rolls into next session
        key = key.where(~after, d + pd.Timedelta(days=1))
    return pd.Series(key, index=idx)


def anchored_vwap(df1m: pd.DataFrame, anchor: time, only_after: bool,
                  bands: list[float]) -> pd.DataFrame:
    """Return vwap + ±k·σ bands (volume-weighted std) for every 1m bar.

    only_after=True (NY session): bars before the anchor time each day are NaN.
    """
    idx = df1m.index
    tp = (df1m["high"] + df1m["low"] + df1m["close"]) / 3.0
    w = df1m["volume"].clip(lower=0.0)

    grp = _anchor_group(idx, anchor)
    if only_after:
        before = (idx.hour < anchor.hour) | ((idx.hour == anchor.hour) & (idx.minute < anchor.minute))
        mask = pd.Series(before, index=idx)
    else:
        mask = pd.Series(False, index=idx)

    g = pd.DataFrame({"grp": grp.values, "w": w.values, "wtp": (w * tp).values,
                      "wtp2": (w * tp * tp).values}, index=idx)
    cw = g.groupby("grp")["w"].cumsum()
    cwtp = g.groupby("grp")["wtp"].cumsum()
    cwtp2 = g.groupby("grp")["wtp2"].cumsum()

    vwap = cwtp / cw
    var = (cwtp2 / cw) - vwap * vwap
    sigma = np.sqrt(var.clip(lower=0.0))

    out = pd.DataFrame(index=idx)
    out["vwap"] = vwap
    for k in bands:
        out[f"vwap_p{k:g}"] = vwap + k * sigma
        out[f"vwap_m{k:g}"] = vwap - k * sigma
    out.loc[mask.values, :] = np.nan
    return out


# ---------- Volume profile ---------------------------------------------------
def volume_profile(window: pd.DataFrame, bin_pts: float, va_pct: float) -> dict:
    """POC / VAH / VAL over ``window`` (a slice of 1m bars).

    Each bar's volume is spread uniformly across [low, high] in ``bin_pts`` bins.
    """
    if window.empty:
        return {"poc": float("nan"), "vah": float("nan"), "val": float("nan")}

    lo = float(window["low"].min())
    hi = float(window["high"].max())
    if hi <= lo:
        return {"poc": lo, "vah": lo, "val": lo}

    n = max(1, int(np.ceil((hi - lo) / bin_pts)))
    edges = lo + bin_pts * np.arange(n + 1)
    centers = (edges[:-1] + edges[1:]) / 2.0
    hist = np.zeros(n)

    lows = window["low"].to_numpy()
    highs = window["high"].to_numpy()
    vols = window["volume"].to_numpy()
    for l, h, v in zip(lows, highs, vols):
        if v <= 0 or h < l:
            continue
        i0 = int((l - lo) // bin_pts)
        i1 = int((h - lo) // bin_pts)
        i0 = min(max(i0, 0), n - 1)
        i1 = min(max(i1, 0), n - 1)
        span = i1 - i0 + 1
        hist[i0:i1 + 1] += v / span

    poc_i = int(hist.argmax())
    poc = float(centers[poc_i])

    total = hist.sum()
    target = va_pct * total
    lo_i = hi_i = poc_i
    acc = hist[poc_i]
    while acc < target and (lo_i > 0 or hi_i < n - 1):
        left = hist[lo_i - 1] if lo_i > 0 else -1.0
        right = hist[hi_i + 1] if hi_i < n - 1 else -1.0
        if right >= left:
            hi_i += 1
            acc += max(right, 0.0)
        else:
            lo_i -= 1
            acc += max(left, 0.0)
    return {"poc": poc, "vah": float(centers[hi_i]), "val": float(centers[lo_i])}
