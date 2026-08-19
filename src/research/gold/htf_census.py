"""BR-1 on gold: does displaced price come back to the 15m Bollinger MA?

The NQ book rests on one number — displaced >=0.5W from the 15m BB MA, price
touches it again before session close 89% of the time, stable across every side
and era (BR-1). Everything downstream was built on that. Nobody has ever measured
it on a metal.

This measures it on GC using ``src.htf_ma.levels.bb_ma_asof`` — the same function,
not a reimplementation — so a difference between the two instruments is a
difference in the market rather than in somebody's definition of a band.

Three things are measured together, because the first is worthless alone:

  touch rate      P(a bar's range contains the MA before session close)   [BR-1]
  before 1W       ...and it arrives before another 1.0W of extension       [BR-2]
  adverse         how far price extends away first, in W                   [BR-4]

And a PLACEBO, which is the part that makes the touch rate mean anything. BR-2
records that a proximity-matched placebo scores 60-63% against the real 64-66% —
i.e. most of the apparent edge is "a level near price gets touched". Here the
control is the MA FROZEN at the moment of displacement: same level, same distance,
same session, but it cannot drift toward price. If the moving MA does not beat the
frozen one, the Bollinger construction is decoration.

Episodes, not bars: after displacing, the state is "awaiting rebalance" until a
touch, so one excursion contributes one row. Counting every displaced bar would
report the same excursion hundreds of times and shrink every interval to nothing.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.htf_ma.levels import bb_ma_asof

NY = "America/New_York"
SESSION_START_H = 18          # CME metals day: 18:00 NY -> +23h
SESSION_HOURS = 23


def _session_day(idx: pd.DatetimeIndex) -> np.ndarray:
    """Label each minute with the 18:00-anchored session day it belongs to."""
    shifted = idx - pd.Timedelta(hours=SESSION_START_H)
    return shifted.date


def _window_of(hour_ny: np.ndarray) -> np.ndarray:
    out = np.full(len(hour_ny), "other", dtype=object)
    out[(hour_ny >= 19) | (hour_ny <= 2)] = "asia"
    out[(hour_ny >= 3) & (hour_ny <= 7)] = "london"
    out[(hour_ny >= 8) & (hour_ny <= 16)] = "ny"
    return out


def displacement_episodes(bars_1m: pd.DataFrame, tf: int = 15,
                          disp_w: float = 0.5, n: int = 20) -> pd.DataFrame:
    """One row per displacement excursion.

    ``bars_1m`` must be indexed by a tz-aware DatetimeIndex and carry
    open/high/low/close. The MA is stamped at the close of its own bar and is only
    consulted from the NEXT bar onward, matching ``bb_ma_asof``'s contract — the
    displacement is detected at t and the touch scan starts at t+1.
    """
    ma_s, w_s = bb_ma_asof(bars_1m, tf, n=n)
    ma, w = ma_s.to_numpy(), w_s.to_numpy()
    hi = bars_1m["high"].to_numpy()
    lo = bars_1m["low"].to_numpy()
    cl = bars_1m["close"].to_numpy()
    idx = bars_1m.index
    sday = _session_day(idx)
    hour = idx.hour.to_numpy()

    rows: list[dict] = []
    start = 0
    for end in np.flatnonzero(np.r_[sday[1:] != sday[:-1], True]) + 1:
        sl = slice(start, end)
        start = end
        # slice EVERY aligned array, including the day/hour labels: indexing a
        # global array with a slice-local offset silently stamps every episode
        # with the first session's day, which collapses the whole run to one
        # session and voids the "before session close" question entirely.
        m, wv, h_, l_, c_ = ma[sl], w[sl], hi[sl], lo[sl], cl[sl]
        sd_, hr_, ix_ = sday[sl], hour[sl], idx[sl]
        N = len(m)
        awaiting = False
        j0 = 0
        side = 0
        d0 = frozen = 0.0
        ext = 0.0
        hit_1w_first = False
        for j in range(N):
            if np.isnan(m[j]) or np.isnan(wv[j]) or wv[j] <= 0:
                continue
            gap = (c_[j] - m[j]) / wv[j]
            if not awaiting:
                if abs(gap) >= disp_w:
                    awaiting, j0, side = True, j, int(np.sign(gap))
                    d0, frozen, ext, hit_1w_first = abs(gap), m[j], 0.0, False
                continue
            # --- awaiting rebalance ------------------------------------------
            ext = max(ext, side * (c_[j] - m[j]) / wv[j] - d0)
            touched = l_[j] <= m[j] <= h_[j]
            if not touched and ext >= 1.0:
                hit_1w_first = True
            if touched:
                rows.append({
                    "ts": ix_[j0], "sess_day": sd_[j0], "hour_ny": hr_[j0],
                    "side": side, "disp_w": d0, "touched": 1,
                    "minutes": int(j - j0), "mins_left": int(N - 1 - j0),
                    "adverse_w": float(ext),
                    "before_1w": int(not hit_1w_first),
                    "placebo_touched": np.nan,   # filled below
                    "frozen": frozen,
                })
                awaiting = False
        if awaiting:
            rows.append({"ts": ix_[j0], "sess_day": sd_[j0], "hour_ny": hr_[j0],
                         "side": side, "disp_w": d0, "touched": 0,
                         "minutes": int(N - 1 - j0), "mins_left": int(N - 1 - j0),
                         "adverse_w": float(ext),
                         "before_1w": 0, "placebo_touched": np.nan, "frozen": frozen})

    ep = pd.DataFrame(rows)
    if ep.empty:
        return ep
    n_days = len(set(sday))
    if ep["sess_day"].nunique() < n_days * 0.5:
        raise AssertionError(
            f"episodes span {ep['sess_day'].nunique()} session-days but the bars span "
            f"{n_days} — the day labels are not tracking the sessions")
    ep["window"] = _window_of(ep["hour_ny"].to_numpy())
    return ep


def touch_within(ep: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Touch rate inside a FIXED horizon, on episodes that had the time to spend.

    The raw per-session rate is confounded: sessions start at 18:00 NY, so an Asia
    displacement has ~20 hours left to rebalance and an NY one has ~4. Comparing the
    windows on that number measures the clock, not the market. Restricting to
    episodes with at least ``horizon`` minutes of session remaining, and asking only
    whether the touch landed inside it, removes the confound.
    """
    e = ep[ep["mins_left"] >= horizon]
    return e.assign(out=((e["touched"] == 1) & (e["minutes"] <= horizon)).astype(int))


def add_placebo(ep: pd.DataFrame, bars_1m: pd.DataFrame) -> pd.DataFrame:
    """Did a STATIC level at the MA's displacement-time value get touched instead?

    Same level, same session, same starting distance — the only thing removed is the
    MA's ability to drift toward price. The gap between the two columns is what the
    Bollinger construction actually contributes.
    """
    hi = bars_1m["high"].to_numpy()
    lo = bars_1m["low"].to_numpy()
    idx = bars_1m.index
    sday = _session_day(idx)
    pos = {t: i for i, t in enumerate(idx)}
    bounds: dict[object, tuple[int, int]] = {}
    start = 0
    for end in np.flatnonzero(np.r_[sday[1:] != sday[:-1], True]) + 1:
        bounds[sday[start]] = (start, end)
        start = end

    out = np.zeros(len(ep), dtype=int)
    for k, r in enumerate(ep.itertuples(index=False)):
        j0 = pos[r.ts]
        _, end = bounds[r.sess_day]
        seg_hi, seg_lo = hi[j0 + 1:end], lo[j0 + 1:end]
        if len(seg_hi) == 0:
            continue
        out[k] = int(np.any((seg_lo <= r.frozen) & (seg_hi >= r.frozen)))
    return ep.assign(placebo_touched=out)
