"""Bar-level readings of Jake Ryan's notes. No order routing.

Absorption, trapped traders, and a footprint refresh need tick or market-by-order
data. They are not approximated here. The value area uses 1-minute volume booked
at the close, in 1-point bins, from the Sunday 18:00 ET open through 09:29 ET.
A 15-second candle is not in this data.
"""

from __future__ import annotations

from itertools import pairwise

import numpy as np
import pandas as pd

from src.research.strategies.costs import FLAT_MINUTE, TICK
from src.research.strategies.limit_entry import try_fill

OPEN = 9 * 60 + 30
WINDOW_END = 11 * 60  # 10:00 CT
VALUE_FRAC = 0.70


def value_area(prices: np.ndarray, volumes: np.ndarray, frac: float = VALUE_FRAC):
    """Return (val, vah, poc) in price points. None when the profile is empty."""
    if len(prices) == 0 or float(np.sum(volumes)) <= 0:
        return None
    uniq, inverse = np.unique(prices.astype(np.int64), return_inverse=True)
    vol = np.zeros(len(uniq), dtype=float)
    np.add.at(vol, inverse, volumes)
    poc_i = int(np.argmax(vol))
    lo = hi = poc_i
    acc = float(vol[poc_i])
    need = frac * float(vol.sum())
    while acc + 1e-9 < need and (lo > 0 or hi < len(vol) - 1):
        left = float(vol[lo - 1]) if lo > 0 else -1.0
        right = float(vol[hi + 1]) if hi < len(vol) - 1 else -1.0
        if right > left:
            hi += 1
            acc += float(vol[hi])
        elif left > right:
            lo -= 1
            acc += float(vol[lo])
        elif lo > 0 and hi < len(vol) - 1:
            lo -= 1
            hi += 1
            acc += float(vol[lo]) + float(vol[hi])
        elif hi < len(vol) - 1:
            hi += 1
            acc += float(vol[hi])
        else:
            lo -= 1
            acc += float(vol[lo])
    return float(uniq[lo]), float(uniq[hi]), float(uniq[poc_i])


def _week_sunday(rth_dates: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Sunday that starts the CME week of each RTH date. Monday belongs to the day before."""
    back = (rth_dates.weekday + 1) % 7
    return rth_dates - pd.to_timedelta(back, unit="D")


def profiles_at_open(df: pd.DataFrame) -> dict[pd.Timestamp, tuple[float, float, float]]:
    """Value area known at 09:30 ET. Later bars in the same session are not included."""
    ts = df["ts_event"]
    hm = df["hm"].to_numpy()
    close = np.rint(df["close"].to_numpy()).astype(np.int64)
    vol = df["volume"].to_numpy(dtype=float)
    sess = df["sess"].to_numpy()
    cuts = np.flatnonzero(np.diff(sess)) + 1
    bounds = np.r_[0, cuts, len(df)]
    out: dict[pd.Timestamp, tuple[float, float, float]] = {}
    hist_px: list[int] = []
    hist_vol: list[float] = []
    week = None
    for a, b in pairwise(bounds):
        daytime = np.flatnonzero((hm[a:b] >= OPEN) & (hm[a:b] < 18 * 60))
        if len(daytime) == 0:
            continue
        i_open = int(daytime[0])
        open_ts = ts.iloc[a + i_open]
        rth_day = open_ts.normalize()
        this_week = _week_sunday(pd.DatetimeIndex([rth_day]))[0]
        if week is None or this_week != week:
            hist_px = []
            hist_vol = []
            week = this_week
        pre = np.flatnonzero((hm[a:b] < OPEN) | (hm[a:b] >= 18 * 60))
        if len(pre):
            hist_px.extend(close[a + pre].tolist())
            hist_vol.extend(vol[a + pre].tolist())
        area = value_area(np.asarray(hist_px, dtype=np.int64), np.asarray(hist_vol, dtype=float))
        if area is not None and area[1] > area[0]:
            out[open_ts] = area
        rest = np.flatnonzero((hm[a:b] >= OPEN) & (hm[a:b] < 18 * 60))
        if len(rest):
            hist_px.extend(close[a + rest].tolist())
            hist_vol.extend(vol[a + rest].tolist())
    return out


def _end_index(hm: np.ndarray, minute: int) -> int:
    hit = np.flatnonzero((hm >= minute) & (hm < 18 * 60))
    if len(hit):
        return int(hit[0])
    flat = np.flatnonzero((hm >= FLAT_MINUTE) & (hm < 18 * 60))
    return int(flat[0]) if len(flat) else len(hm)


def first_fill(o, h, l, c, hm, orders: list[tuple], through: bool = True):
    """First trade-through among orders. Two fills on the same bar is no trade.

    Each order is (side, limit, stop, target, start, end). `end` is exclusive.
    """
    hits = []
    for i, (side, limit, _stop, _target, start, end) in enumerate(orders):
        if start < 0 or start >= end:
            continue
        sl = slice(start, end)
        if side == 1:
            gap = o[sl] <= limit - TICK
            touch = l[sl] <= limit - (TICK if through else 0.0)
        else:
            gap = o[sl] >= limit + TICK
            touch = h[sl] >= limit + (TICK if through else 0.0)
        ok = touch & ~gap
        if not ok.any():
            continue
        first = int(np.flatnonzero(ok)[0])
        if gap.any() and int(np.flatnonzero(gap)[0]) <= first:
            continue
        hits.append((start + first, i))
    if not hits:
        return None
    hits.sort()
    bar = hits[0][0]
    same = [i for j, i in hits if j == bar]
    if len(same) != 1:
        return None
    side, limit, stop, target, _start, end = orders[same[0]]
    return try_fill(o, h, l, c, hm, bar, end, side, limit, stop, target, through)
