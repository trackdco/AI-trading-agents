"""Swing structure, HTF flag, and liquidity levels/sweeps (§3, §4).

Swings via fractal pivots on the 15m context frame. HTF flag from the last
alternating highs/lows (HH/HL = uptrend, LH/LL = downtrend, else range).
Liquidity pools = recent swing highs (buy-side) / lows (sell-side); a sweep is
a wick beyond a pool that closes back on the origin side.
"""
from __future__ import annotations

import pandas as pd


def find_pivots(ctx: pd.DataFrame, p: int) -> list[dict]:
    """Fractal pivots on a context (e.g. 15m) frame. Returns time-ordered
    list of {time, price, kind} where kind in {'high','low'}."""
    highs = ctx["high"].to_numpy()
    lows = ctx["low"].to_numpy()
    idx = ctx.index
    piv = []
    for i in range(p, len(ctx) - p):
        hwin_max = highs[i - p:i + p + 1].max()
        lwin_min = lows[i - p:i + p + 1].min()
        if highs[i] == hwin_max and highs[i] >= highs[i - 1] and highs[i] >= highs[i + 1]:
            piv.append({"time": idx[i], "price": float(highs[i]), "kind": "high"})
        if lows[i] == lwin_min and lows[i] <= lows[i - 1] and lows[i] <= lows[i + 1]:
            piv.append({"time": idx[i], "price": float(lows[i]), "kind": "low"})
    piv.sort(key=lambda d: d["time"])
    return piv


def _asof(pivots: list[dict], asof) -> list[dict]:
    return [p for p in pivots if p["time"] <= asof]


def htf_flag(pivots: list[dict], asof) -> str:
    ps = _asof(pivots, asof)
    highs = [p for p in ps if p["kind"] == "high"][-2:]
    lows = [p for p in ps if p["kind"] == "low"][-2:]
    if len(highs) < 2 or len(lows) < 2:
        return "range"
    hh = highs[-1]["price"] > highs[-2]["price"]
    hl = lows[-1]["price"] > lows[-2]["price"]
    lh = highs[-1]["price"] < highs[-2]["price"]
    ll = lows[-1]["price"] < lows[-2]["price"]
    if hh and hl:
        return "uptrend"
    if lh and ll:
        return "downtrend"
    return "range"


def swing_sequence(pivots: list[dict], asof, n: int = 6) -> list[dict]:
    ps = _asof(pivots, asof)[-n:]
    return [{"type": f"swing_{p['kind']}", "price": round(p["price"], 2),
             "time": p["time"].isoformat()} for p in ps]


def liquidity_levels(pivots: list[dict], asof, lookback: int = 8) -> dict:
    ps = _asof(pivots, asof)[-lookback:]
    return {
        "buy_side": [p for p in ps if p["kind"] == "high"],
        "sell_side": [p for p in ps if p["kind"] == "low"],
    }


def detect_sweep(df1m: pd.DataFrame, asof, levels: dict, tol: float,
                 window_bars: int = 20) -> dict | None:
    """Look back ``window_bars`` 1m bars for a wick that swept a pool then
    closed back. Returns the most recent sweep with side, or None.

    side='sell_side' (low swept, closed back up) → supports a LONG.
    side='buy_side'  (high swept, closed back down) → supports a SHORT.
    """
    win = df1m.loc[:asof].tail(window_bars)
    if win.empty:
        return None
    best = None
    for ts, bar in win.iterrows():
        for lv in levels.get("sell_side", []):
            if lv["time"] >= ts:
                continue
            if bar["low"] < lv["price"] - 0.0 and bar["close"] > lv["price"]:
                cand = {"side": "sell_side", "pool_price": lv["price"], "pool_time": lv["time"],
                        "sweep_price": float(bar["low"]), "sweep_time": ts}
                best = cand if best is None or ts >= best["sweep_time"] else best
        for lv in levels.get("buy_side", []):
            if lv["time"] >= ts:
                continue
            if bar["high"] > lv["price"] + 0.0 and bar["close"] < lv["price"]:
                cand = {"side": "buy_side", "pool_price": lv["price"], "pool_time": lv["time"],
                        "sweep_price": float(bar["high"]), "sweep_time": ts}
                best = cand if best is None or ts >= best["sweep_time"] else best
    return best
