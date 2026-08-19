"""Pure indicator maths for the tomtrades CBR detector.

Every function here is a pure function of a closed-bar frame. Nothing reads a bar that
has not finished, so lookahead cannot enter through this module — it could only be
introduced by a caller misaligning an output, which is what ``test_no_lookahead`` checks.

Databento 1-minute bars are START-labeled (``ts_event`` is the interval open), the same
convention ``src/engine/sessions.py`` documents for NQ, so every resample uses
``label="left"`` and a resampled bar's timestamp is its own open.
"""
from __future__ import annotations

from itertools import pairwise

import numpy as np
import pandas as pd


def resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Resample START-labeled 1m bars to a coarser START-labeled frame."""
    out = (
        df.set_index("ts_event")
        .resample(rule, label="left", closed="left")
        .agg(open=("open", "first"), high=("high", "max"),
             low=("low", "min"), close=("close", "last"), volume=("volume", "sum"))
        .dropna(subset=["open"])
    )
    return out.reset_index()


def atr(df: pd.DataFrame, n: int) -> pd.Series:
    """Wilder-style ATR via a simple rolling mean of true range, shifted one bar.

    The shift matters: ATR at bar *t* must be computable from bars strictly before *t*,
    otherwise a gate keyed off it peeks at the bar it is deciding.
    """
    prev_close = df["close"].shift()
    tr = pd.concat(
        [df["high"] - df["low"],
         (df["high"] - prev_close).abs(),
         (df["low"] - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.rolling(n, min_periods=max(2, n // 2)).mean().shift()


def pivot_flags(high: pd.Series, low: pd.Series, k: int) -> tuple[pd.Series, pd.Series]:
    """k-bar fractal pivots. Returns (is_pivot_high, is_pivot_low), both shifted.

    A pivot at bar *i* is only *known* k bars later, since it needs k bars either side.
    The returned flags are therefore placed at the bar where the pivot becomes
    confirmable (i + k), not at the extreme itself. Callers wanting the extreme's price
    read it from the value columns; callers wanting to act must use these flags.
    """
    n = len(high)
    ph = np.zeros(n, dtype=bool)
    pl = np.zeros(n, dtype=bool)
    hv, lv = high.to_numpy(), low.to_numpy()
    for i in range(k, n - k):
        window_h = hv[i - k:i + k + 1]
        window_l = lv[i - k:i + k + 1]
        if hv[i] == window_h.max() and (window_h == hv[i]).sum() == 1:
            ph[i] = True
        if lv[i] == window_l.min() and (window_l == lv[i]).sum() == 1:
            pl[i] = True
    # place the flag where the pivot becomes confirmable
    return (pd.Series(ph, index=high.index).shift(k, fill_value=False),
            pd.Series(pl, index=low.index).shift(k, fill_value=False))


def swing_legs(df: pd.DataFrame, k: int) -> list[tuple[int, float, int, float]]:
    """Alternating pivot-to-pivot legs as (start_idx, start_px, end_idx, end_px).

    Consecutive same-side pivots collapse to the more extreme one, so the result strictly
    alternates high-low-high, which is what makes a retracement fraction well defined.
    """
    ph, pl = pivot_flags(df["high"], df["low"], k)
    # undo the confirmability shift to recover where the extreme actually sat
    ph_i = [i - k for i in np.flatnonzero(ph.to_numpy())]
    pl_i = [i - k for i in np.flatnonzero(pl.to_numpy())]
    marks = sorted([(i, "H") for i in ph_i if i >= 0] + [(i, "L") for i in pl_i if i >= 0])
    if not marks:
        return []
    hv, lv = df["high"].to_numpy(), df["low"].to_numpy()

    cleaned: list[tuple[int, str]] = []
    for idx, kind in marks:
        if cleaned and cleaned[-1][1] == kind:
            prev_idx = cleaned[-1][0]
            better = (hv[idx] > hv[prev_idx]) if kind == "H" else (lv[idx] < lv[prev_idx])
            if better:
                cleaned[-1] = (idx, kind)
            continue
        cleaned.append((idx, kind))

    legs = []
    for (i0, k0), (i1, _) in pairwise(cleaned):
        p0 = hv[i0] if k0 == "H" else lv[i0]
        p1 = lv[i1] if k0 == "H" else hv[i1]
        legs.append((i0, float(p0), i1, float(p1)))
    return legs


def mean_retracement(df: pd.DataFrame, k: int) -> float:
    """His range test: on average, how much of each move gets given back.

    *"I identify a range as whether on average over those past 5 to 12 plus hours how
    much we correct the previous move"*. For each leg, the retracement is the next leg's
    size as a fraction of it; the mean over the window is the statistic. Returns NaN when
    there are too few legs to average, which the caller must treat as "unknown", never
    as "not a range".
    """
    legs = swing_legs(df, k)
    if len(legs) < 2:
        return float("nan")
    fracs = []
    for (_, a0, _, a1), (_, b0, _, b1) in pairwise(legs):
        size = abs(a1 - a0)
        if size <= 0:
            continue
        fracs.append(min(abs(b1 - b0) / size, 2.0))
    return float(np.mean(fracs)) if fracs else float("nan")


def efficiency_ratio(close: pd.Series) -> float:
    """Kaufman efficiency: |net move| / summed absolute moves. Low = rangey."""
    if len(close) < 2:
        return float("nan")
    path = close.diff().abs().sum()
    return float("nan") if path == 0 else float(abs(close.iloc[-1] - close.iloc[0]) / path)


def hourly_run_state(df: pd.DataFrame, tz_anchor: str = "UTC") -> pd.DataFrame:
    """Per-bar state of the intra-hour directional run — the raw material for C2.

    For each bar, measured from its hour's open using only bars up to and including it:

    ``run_dir``      +1/-1/0, sign of (extreme so far - hour open)
    ``run_minutes``  minutes elapsed since the hour open
    ``displacement`` |extreme so far - hour open|
    ``retrace_frac`` how far price has come back off that extreme, as a fraction of
                     displacement — his invalidation test (*"pulling back to around 50%
                     or more"*)
    ``minute_of_hour`` position within the hour, the C3 signal
    """
    ts = df["ts_event"].dt.tz_convert(tz_anchor)
    hour_id = ts.dt.floor("h")
    o, h, low_, c = (df[x].to_numpy() for x in ("open", "high", "low", "close"))
    n = len(df)
    run_dir = np.zeros(n, dtype=np.int8)
    disp = np.zeros(n)
    retr = np.zeros(n)
    mins = np.zeros(n, dtype=np.int16)

    hid = hour_id.to_numpy()
    minute = ts.dt.minute.to_numpy()
    hour_open = 0.0
    hi_ext = lo_ext = 0.0
    start = 0
    for i in range(n):
        if i == 0 or hid[i] != hid[i - 1]:
            hour_open, hi_ext, lo_ext, start = o[i], h[i], low_[i], i
        else:
            hi_ext, lo_ext = max(hi_ext, h[i]), min(lo_ext, low_[i])
        up = hi_ext - hour_open
        dn = hour_open - lo_ext
        if up >= dn and up > 0:
            run_dir[i], disp[i] = 1, up
            retr[i] = (hi_ext - c[i]) / up
        elif dn > 0:
            run_dir[i], disp[i] = -1, dn
            retr[i] = (c[i] - lo_ext) / dn
        mins[i] = i - start  # bar count == minutes on a complete 1m series
        _ = minute  # minute-of-hour comes from the timestamp, below

    return pd.DataFrame(
        {
            "run_dir": run_dir,
            "run_minutes": mins,
            "displacement": disp,
            "retrace_frac": np.clip(retr, 0.0, 5.0),
            "minute_of_hour": ts.dt.minute.to_numpy(),
            "hour_id": hid,
        },
        index=df.index,
    )


def rolling_return(close: pd.Series, bars: int) -> pd.Series:
    """Fractional return over ``bars``, shifted so bar t sees only closed history."""
    return (close / close.shift(bars) - 1.0).shift()


def zscore(series: pd.Series, window: int) -> pd.Series:
    """Rolling z-score, shifted one bar."""
    mu = series.rolling(window, min_periods=max(2, window // 2)).mean()
    sd = series.rolling(window, min_periods=max(2, window // 2)).std(ddof=0)
    return ((series - mu) / sd.replace(0.0, np.nan)).shift()
