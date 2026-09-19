"""Limit lifecycle + position resolution on committed bars. Orchestrator only, no doctrine.

Deliberately does NOT carry the 0.3.x mechanical management clauses (tscan's T13
cash-open flatten and T23 runner trail). On the 0.4.2 / 0.2.0 contracts every
management action is tv-manage's judgement call, and firing a mechanical clause
alongside it would both double-manage the position and put the orchestrator's
opinion into the result.
"""
import sys
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
import pandas as pd
from scripts.build_l2_outcomes import load_bars
from src.htf_ma.levels import NY

_B = None


def bars():
    global _B
    if _B is None:
        b = load_bars()
        b["mi"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
        _B = b.set_index("mi").sort_index()[["open", "high", "low", "close", "volume"]]
    return _B


def limit_lifecycle(day_next, place_at, side, limit, cancel_at, expiry_min=10):
    """Resting limit: fill on touch, cancel if price RUNS to the structural level
    first, expire after expiry_min. Returns (status, minute, price)."""
    short = side.lower().startswith("s")
    t0 = pd.Timestamp(f"{day_next} {place_at}", tz=NY)
    w = bars()[(bars().index >= t0) & (bars().index <= t0 + pd.Timedelta(minutes=expiry_min))]
    for t, r in w.iterrows():
        hit = (r.high >= limit) if short else (r.low <= limit)
        ran = None
        if cancel_at is not None:
            ran = (r.low <= cancel_at) if short else (r.high >= cancel_at)
        if ran and not hit:
            return ("no_fill_ran", t.strftime("%H:%M"), float(cancel_at))
        if hit:
            return ("filled", t.strftime("%H:%M"), float(limit))
    return ("no_fill_expired", (t0 + pd.Timedelta(minutes=expiry_min)).strftime("%H:%M"), None)


def resolve(day_next, fill_at, side, entry, stop, target, upto_hours=6, start_after=False):
    # A stop set AT decision minute T is live for the bar STARTING at T - the decision
    # is taken the instant the prior bar closes, which is when that bar opens. Excluding
    # it dated one day-1 exit a minute late (same price, same R).
    """First of stop / target, on bars from fill_at forward. Returns dict or None
    if neither prints inside the horizon (caller then resolves at the horizon)."""
    short = side.lower().startswith("s")
    t0 = pd.Timestamp(f"{day_next} {fill_at}", tz=NY)
    w = bars()[(bars().index > t0) if start_after else (bars().index >= t0)]
    w = w[w.index <= t0 + pd.Timedelta(hours=upto_hours)]
    for t, r in w.iterrows():
        hit_stop = (r.high >= stop) if short else (r.low <= stop)
        hit_tgt = (r.low <= target) if short else (r.high >= target)
        if hit_stop and hit_tgt:
            # both in one bar: unknowable intrabar order, resolve at the STOP
            return {"type": "stop_and_target_same_bar_resolved_at_stop", "price": float(stop),
                    "minute": t.strftime("%H:%M")}
        if hit_stop:
            return {"type": "stop", "price": float(stop), "minute": t.strftime("%H:%M")}
        if hit_tgt:
            return {"type": "target", "price": float(target), "minute": t.strftime("%H:%M")}
    return None


def excursion(day_next, fill_at, side, entry, until):
    """MFE / MAE in points from the fill to `until` (HH:MM), inclusive."""
    short = side.lower().startswith("s")
    t0 = pd.Timestamp(f"{day_next} {fill_at}", tz=NY)
    t1 = pd.Timestamp(f"{day_next} {until}", tz=NY)
    w = bars()[(bars().index >= t0) & (bars().index <= t1)]
    if not len(w):
        return {"mfe": 0.0, "mae": 0.0}
    if short:
        return {"mfe": round(float(entry - w.low.min()), 2),
                "mae": round(float(w.high.max() - entry), 2)}
    return {"mfe": round(float(w.high.max() - entry), 2),
            "mae": round(float(entry - w.low.min()), 2)}


def bar_at(day_next, hhmm, minutes=2):
    """The `minutes`-bar CLOSING at hhmm."""
    t1 = pd.Timestamp(f"{day_next} {hhmm}", tz=NY)
    w = bars()[(bars().index >= t1 - pd.Timedelta(minutes=minutes)) & (bars().index < t1)]
    if not len(w):
        return None
    return {"start": (t1 - pd.Timedelta(minutes=minutes)).strftime("%H:%M"), "closed_at": hhmm,
            "open": float(w.iloc[0].open), "high": float(w.high.max()),
            "low": float(w.low.min()), "close": float(w.iloc[-1].close)}
