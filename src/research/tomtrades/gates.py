"""The confluence gates C1-C9, one pure function each.

Each returns a boolean array aligned to the 1-minute frame: True where the gate ALLOWS a
signal. A disabled gate returns all-True, so ablation is just flipping its ``enabled``
flag — no branch anywhere else changes. That property is what the whole exercise rests
on, since the deliverable is per-gate ablations rather than one headline number.

Rule IDs match ``.claude/skills/tomtrades-model/references/confluence-table.md`` (v2),
where each gate's quoted definition, named ambiguity and falsification test live. Where
he gave no number the config default is tagged ``[R]`` and is a placeholder for a sweep,
not a claim about his method.
"""
from __future__ import annotations

from itertools import pairwise

import numpy as np
import pandas as pd

from . import indicators as ind


def _all_true(n: int) -> np.ndarray:
    return np.ones(n, dtype=bool)


def c1_range(df: pd.DataFrame, cfg: dict) -> np.ndarray:
    """Middle-timeframe range condition. His test is mean give-back, not width.

    Evaluated on completed 1h bars and forward-filled onto the minute frame, so a minute
    inside hour H is judged by hours strictly before H.
    """
    n = len(df)
    if not cfg.get("enabled", True):
        return _all_true(n)
    hourly = ind.resample_ohlcv(df, "1h")
    leg_tf = cfg.get("leg_tf", "15min")
    legs_df = ind.resample_ohlcv(df, leg_tf)
    per_hour = int(pd.Timedelta("1h") / pd.Timedelta(leg_tf))
    look = int(cfg["lookback_hours"])
    k = int(cfg["pivot_k"])
    method = cfg.get("method", "mean_retrace")

    # legs are measured on leg_tf bars covering the trailing lookback_hours; see the
    # config note -- hourly bars cannot resolve two legs inside his stated window.
    leg_idx = pd.Series(np.arange(len(legs_df)), index=legs_df["ts_event"])
    end_for_hour = leg_idx.reindex(hourly["ts_event"], method="ffill").to_numpy()
    span = look * per_hour

    vals = np.full(len(hourly), np.nan)
    for i in range(look, len(hourly)):
        end = end_for_hour[i]
        if np.isnan(end) or end < span:
            continue
        end = int(end)
        win = legs_df.iloc[end - span:end]     # strictly prior leg_tf bars
        if method == "mean_retrace":
            vals[i] = ind.mean_retracement(win, k)
        elif method == "median_retrace":
            legs = ind.swing_legs(win, k)
            fr = [min(abs(b[3] - b[1]) / abs(a[3] - a[1]), 2.0)
                  for a, b in pairwise(legs) if abs(a[3] - a[1]) > 0]
            vals[i] = float(np.median(fr)) if fr else np.nan
        elif method == "efficiency":
            vals[i] = ind.efficiency_ratio(win["close"])
        elif method == "width_atr":
            a = ind.atr(hourly.iloc[:i], 24).iloc[-1] if i > 24 else np.nan
            vals[i] = (win["high"].max() - win["low"].min()) / a if a and a > 0 else np.nan
        else:
            raise ValueError(f"unknown c1 method {method!r}")

    if method in ("mean_retrace", "median_retrace"):
        ok = vals >= float(cfg["retrace_min"])
    elif method == "efficiency":
        ok = vals <= float(cfg["efficiency_max"])
    else:
        ok = vals <= float(cfg["width_atr_max"])
    ok &= ~np.isnan(vals)                      # unknown is never "in range"

    flag = pd.Series(ok, index=hourly["ts_event"])
    return flag.reindex(df["ts_event"], method="ffill").fillna(False).to_numpy()


def c2_overextension(state: pd.DataFrame, atr_1h: pd.Series, cfg: dict) -> np.ndarray:
    """Overextension, defined by DURATION and invalidated by a 50% give-back.

    v1 of the audit called magnitude "the single biggest gap"; the wider corpus showed
    he never gives one because persistence is his criterion. ``require_magnitude`` exists
    only to test whether adding magnitude improves on his own definition.
    """
    n = len(state)
    if not cfg.get("enabled", True):
        return _all_true(n)
    ok = (
        (state["run_minutes"].to_numpy() >= int(cfg["min_duration_min"]))
        & (state["retrace_frac"].to_numpy() < float(cfg["invalidation_frac"]))
        & (state["run_dir"].to_numpy() != 0)
        & (state["displacement"].to_numpy() > 0)
    )
    if cfg.get("require_magnitude"):
        a = atr_1h.to_numpy()
        ok &= state["displacement"].to_numpy() >= float(cfg["atr_mult"]) * np.nan_to_num(a)
    if cfg.get("onesided_frac"):
        raise NotImplementedError("onesided_frac is defined in the table but not yet coded")
    return ok


def c3_clock(state: pd.DataFrame, cfg: dict) -> np.ndarray:
    """Minute-of-hour window, plus the 15m-boundary avoidance.

    His stated variants conflict (22-52, 30-45, 20-30, 37). This encodes ONE
    parameterised window; the variants are points in the sweep, never reconciled here.
    """
    n = len(state)
    if not cfg.get("enabled", True):
        return _all_true(n)
    m = state["minute_of_hour"].to_numpy()
    ok = (m >= int(cfg["window_start_min"])) & (m <= int(cfg["window_end_min"]))
    buf = int(cfg.get("boundary_buffer_min", 0))
    if buf:
        # "I don't want to be entering a trade just before the next 15-minute candle open"
        ok &= ((m % 15) < (15 - buf))
    return ok


def c4_correlation(state: pd.DataFrame, corr_ret: pd.Series | None,
                   yen_ret: pd.Series | None, cfg: dict) -> np.ndarray:
    """DXY / yen alignment. ``veto_only`` is the sole version he states as a hard rule.

    ``required`` demands the dollar move oppose the intended trade; the trade is a fade,
    so the intended direction is the opposite of the run direction.
    """
    n = len(state)
    mode = cfg.get("mode", "off")
    if mode == "off" or corr_ret is None:
        return _all_true(n)
    d = np.nan_to_num(corr_ret.to_numpy())
    trade_dir = -state["run_dir"].to_numpy()          # fade the run

    if mode == "required":
        thr = float(cfg.get("corr_min", 0.0))
        return np.sign(d) == -trade_dir if thr == 0 else (
            (np.sign(d) == -trade_dir) & (np.abs(d) >= thr * np.nanstd(d))
        )
    if mode == "veto_only":
        if yen_ret is None:
            return _all_true(n)
        y = np.nan_to_num(yen_ret.to_numpy())
        z = float(cfg.get("veto_z", 1.0))
        sd_d, sd_y = np.nanstd(d) or 1.0, np.nanstd(y) or 1.0
        both_big = (np.abs(d) >= z * sd_d) & (np.abs(y) >= z * sd_y)
        same_way = np.sign(d) == np.sign(y)
        return ~(both_big & same_way)                  # block only the stated case
    raise ValueError(f"unknown c4 mode {mode!r}")


def c5_aoi(df: pd.DataFrame, state: pd.DataFrame, atr_1h: pd.Series, cfg: dict) -> np.ndarray:
    """Area of interest. Primary source is the C1 range boundary, per his own words.

    Likely redundant with C1 — that redundancy is a result to measure, not a reason to
    skip coding it.
    """
    n = len(df)
    if not cfg.get("enabled", True):
        return _all_true(n)
    src = cfg.get("source", "range_boundary")
    band = float(cfg["proximity_atr"]) * np.nan_to_num(atr_1h.to_numpy(), nan=0.0)

    hourly = ind.resample_ohlcv(df, "1h")
    look = 8
    hi = hourly["high"].rolling(look, min_periods=2).max().shift()
    lo = hourly["low"].rolling(look, min_periods=2).min().shift()
    if src == "beyond_n_day":
        days = int(cfg.get("beyond_n_day", 5)) * 24
        hi = hourly["high"].rolling(days, min_periods=2).max().shift()
        lo = hourly["low"].rolling(days, min_periods=2).min().shift()
    elif src not in ("range_boundary",):
        raise NotImplementedError(f"c5 source {src!r} is in the table but not yet coded")

    hi_m = pd.Series(hi.to_numpy(), index=hourly["ts_event"]).reindex(
        df["ts_event"], method="ffill").to_numpy()
    lo_m = pd.Series(lo.to_numpy(), index=hourly["ts_event"]).reindex(
        df["ts_event"], method="ffill").to_numpy()
    rd = state["run_dir"].to_numpy()
    h, low_ = df["high"].to_numpy(), df["low"].to_numpy()
    # an up-run must have reached the upper boundary; a down-run the lower
    up_ok = (rd == 1) & (h >= np.nan_to_num(hi_m, nan=np.inf) - band)
    dn_ok = (rd == -1) & (low_ <= np.nan_to_num(lo_m, nan=-np.inf) + band)
    return up_ok | dn_ok


def session_mask(df: pd.DataFrame, cfg: dict) -> np.ndarray:
    """Trading-session filter on the NY clock (sessions are clock-dependent, unlike C3)."""
    names = cfg.get("enabled") or []
    if not names:
        return _all_true(len(df))
    minutes = df["ts_event"].dt.hour.to_numpy() * 60 + df["ts_event"].dt.minute.to_numpy()
    ok = np.zeros(len(df), dtype=bool)
    for name in names:
        spec = cfg[name]
        s = int(spec["start"][:2]) * 60 + int(spec["start"][3:])
        e = int(spec["end"][:2]) * 60 + int(spec["end"][3:])
        ok |= (minutes >= s) | (minutes < e) if s > e else (minutes >= s) & (minutes < e)
    return ok
