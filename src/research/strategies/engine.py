"""Fill model. Signal on a closed bar, enter at the next bar's open, stop before target."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.research.strategies.costs import (
    COMMISSION_POINTS,
    FLAT_MINUTE,
    MAX_STOP,
    MIN_STOP,
    TICK,
)


@dataclass
class Trade:
    name: str
    entry_i: int
    exit_i: int
    ts: np.datetime64
    side: int
    risk_points: float
    pnl_points: float
    r_net: float


def load_bars(path: str = "data/reference/nq_1m_master.parquet") -> pd.DataFrame:
    df = pd.read_parquet(path).sort_values("ts_event").reset_index(drop=True)
    ts = df["ts_event"]
    date = ts.dt.normalize()
    hour = ts.dt.hour
    sess = date.where(hour < 18, date + pd.Timedelta(days=1))
    df["sess"] = sess.astype("int64")
    df["hm"] = ts.dt.hour * 60 + ts.dt.minute
    df["year"] = ts.dt.year
    prev_c = df["close"].shift(1)
    tr = np.maximum(df["high"] - df["low"], np.maximum((df["high"] - prev_c).abs(), (df["low"] - prev_c).abs()))
    df["atr"] = pd.Series(tr).rolling(20, min_periods=20).mean().to_numpy()
    df["pv"] = df["open"] * df["volume"]
    df["vwap"] = df.groupby("sess", sort=False)["pv"].cumsum() / df.groupby("sess", sort=False)["volume"].cumsum()
    vol_med = df["volume"].rolling(20, min_periods=20).median().shift(1)
    df["vol_med"] = vol_med
    # prior RTH high/low/close, known at the next session
    rth = (df["hm"] >= 9 * 60 + 30) & (df["hm"] < 16 * 60)
    rth_stats = df.loc[rth].groupby("sess").agg(hi=("high", "max"), lo=("low", "min"), cl=("close", "last"), op=("open", "first"))
    rth_stats["pdh"] = rth_stats["hi"].shift(1)
    rth_stats["pdl"] = rth_stats["lo"].shift(1)
    rth_stats["pdc"] = rth_stats["cl"].shift(1)
    on = (df["hm"] >= 18 * 60) | (df["hm"] < 9 * 60 + 30)
    on_stats = df.loc[on].groupby("sess").agg(onh=("high", "max"), onl=("low", "min"))
    df = df.join(rth_stats[["pdh", "pdl", "pdc", "op"]], on="sess")
    df = df.join(on_stats, on="sess")
    df["rth_open"] = df.groupby("sess")["op"].transform("first")
    return df


def simulate(
    name: str,
    signal_i: np.ndarray,
    side: np.ndarray,
    stop: np.ndarray,
    target: np.ndarray,
    o: np.ndarray,
    h: np.ndarray,
    l: np.ndarray,
    c: np.ndarray,
    hm: np.ndarray,
    sess: np.ndarray,
    ts: np.ndarray,
) -> list[Trade]:
    """One position at a time. Both sides of a bar hit the stop first."""
    n = len(o)
    order = np.argsort(signal_i, kind="mergesort")
    trades: list[Trade] = []
    cursor = -1
    for k in order:
        i = int(signal_i[k])
        entry_i = i + 1
        if entry_i <= cursor or entry_i >= n:
            continue
        if sess[entry_i] != sess[i]:
            continue
        if hm[entry_i] >= FLAT_MINUTE:
            continue
        s = int(side[k])
        if s not in (1, -1):
            continue
        stop_px = float(stop[k])
        tgt_px = float(target[k])
        planned = float(o[entry_i])
        risk = s * (planned - stop_px)
        if not (MIN_STOP <= risk <= MAX_STOP):
            continue
        if s * (tgt_px - planned) <= 0:
            continue
        entry_px = planned + s * TICK
        stop_fill = stop_px - s * TICK
        tgt_fill = tgt_px - s * TICK
        exit_i = entry_i
        exit_px = entry_px
        for j in range(entry_i, n):
            if sess[j] != sess[entry_i]:
                exit_i = j - 1
                exit_px = float(c[exit_i]) - s * TICK
                break
            hit_stop, hit_tgt, stop_at = _hits(s, float(o[j]), float(h[j]), float(l[j]), stop_px, tgt_px, stop_fill, tgt_fill)
            if hit_stop:
                exit_i = j
                exit_px = stop_at
                break
            if hit_tgt:
                exit_i = j
                exit_px = tgt_fill
                break
            if hm[j] >= FLAT_MINUTE:
                exit_i = j
                exit_px = float(c[j]) - s * TICK
                break
        else:
            exit_i = n - 1
            exit_px = float(c[exit_i]) - s * TICK
        pnl = s * (exit_px - entry_px) - COMMISSION_POINTS
        trades.append(
            Trade(name, entry_i, exit_i, ts[entry_i], s, risk, pnl, pnl / risk)
        )
        cursor = exit_i
    return trades


def _hits(side, op, hi, lo, stop_px, tgt_px, stop_fill, tgt_fill):
    if side == 1:
        if op <= stop_px:
            return True, False, min(op, stop_fill)
        if lo <= stop_px:
            return True, False, stop_fill
        if hi >= tgt_px:
            return False, True, tgt_fill
        return False, False, stop_fill
    if op >= stop_px:
        return True, False, max(op, stop_fill)
    if hi >= stop_px:
        return True, False, stop_fill
    if lo <= tgt_px:
        return False, True, tgt_fill
    return False, False, stop_fill
