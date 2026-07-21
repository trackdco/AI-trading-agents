"""CVD confirmation layer (spec §CVD). Short-term, at-the-level only — never session-wide
for the divergence read. All reads use 1-minute data up to and including the entry candle
close (no lookahead).

Three signals, combined into the four test modes:
  * initiative delta  — entry-candle delta% >= +thr (long) / <= -thr (short).
  * absorption / lack-of-participation divergence — over the last ~2*swing window, price
    makes a new extreme against the trade while session-CVD fails to confirm it
    (CVD holds / reverses). Captures both "absorption" (CVD pushes, price holds) and
    "exhaustion" (price extends, CVD doesn't).
  * modes: a=none, b=divergence, c=initiative, d=both.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


class CVDBook:
    """Holds the 1-min delta, total, and session-cumulative CVD; answers entry queries."""

    def __init__(self, delta: pd.Series, total: pd.Series, cvd_session: pd.Series,
                 swing_lookback_min: int, initiative_pct: float):
        self.w = max(2, int(swing_lookback_min))     # half-window (minutes)
        self.thr = float(initiative_pct)
        # precompute sorted int64-ns index + value arrays so per-candle reads are O(log n)
        self._index = delta.index                                  # NY tz-aware minute grid
        self._i = delta.index.asi8                                 # sorted minute stamps (ns)
        self._delta = delta.to_numpy("float64")
        self._total = total.reindex(delta.index).fillna(0.0).to_numpy("float64")
        self._cvd = cvd_session.reindex(delta.index).to_numpy("float64")  # may hold NaN pre-anchor

    # -- per-candle delta% over the entry candle's own minutes -------------------
    def candle_delta_pct(self, c_open_ts: pd.Timestamp, c_close_ts: pd.Timestamp) -> float | None:
        """delta% of the entry candle = sum(delta) / sum(total) * 100 over its 1-min bars
        spanning [c_open_ts, c_close_ts)."""
        lo = int(np.searchsorted(self._i, c_open_ts.value, "left"))
        hi = int(np.searchsorted(self._i, c_close_ts.value, "left"))
        if hi <= lo:
            return None
        tot = float(self._total[lo:hi].sum())
        if tot <= 0:
            return None
        return float(self._delta[lo:hi].sum()) / tot * 100.0

    def initiative_ok(self, c_open_ts, c_close_ts, direction: str) -> bool | None:
        dp = self.candle_delta_pct(c_open_ts, c_close_ts)
        if dp is None:
            return None
        return dp >= self.thr if direction == "long" else dp <= -self.thr

    # -- absorption / lack-of-participation divergence at the level --------------
    def divergence_ok(self, entry_ts: pd.Timestamp, direction: str) -> bool | None:
        """Two-window extreme test on 1-min bars in (entry_ts - 2w, entry_ts].

        long : price second-half low <= first-half low (new/equal low) AND session-CVD
               second-half low > first-half low (CVD made a HIGHER low = not confirming).
        short: mirror on highs. Returns None if not enough minutes.
        """
        w = self.w
        lo = int(np.searchsorted(self._i, (entry_ts - pd.Timedelta(minutes=2 * w)).value, "right"))
        hi = int(np.searchsorted(self._i, entry_ts.value, "right"))
        cvd = self._cvd[lo:hi]; pr = self._price[lo:hi]
        keep = ~(np.isnan(cvd) | np.isnan(pr))
        cvd = cvd[keep]; pr = pr[keep]
        if len(cvd) < 4:
            return None
        half = len(cvd) // 2
        c1, c2, p1, p2 = cvd[:half], cvd[half:], pr[:half], pr[half:]
        if direction == "long":
            return bool(p2.min() <= p1.min() + 1e-9 and c2.min() > c1.min())
        else:
            return bool(p2.max() >= p1.max() - 1e-9 and c2.max() < c1.max())

    def bind_price(self, price_1m: pd.Series):
        """Attach the 1-min close aligned to the CVD minute grid (array parallel to self._i)."""
        self._price = price_1m.reindex(self._index).to_numpy("float64")


def mode_gate(mode: str, div_ok, init_ok) -> bool:
    """Apply a CVD test mode. Missing signal (None) is treated as FAIL for a required gate."""
    if mode == "a":
        return True
    if mode == "b":
        return bool(div_ok)
    if mode == "c":
        return bool(init_ok)
    if mode == "d":
        return bool(div_ok) and bool(init_ok)
    raise ValueError(f"unknown cvd mode {mode!r}")
