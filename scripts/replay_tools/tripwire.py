"""Mechanical resolution scanner for tv-thesis `other_side_tripwire`.

RUNBOOK 2b makes the tripwire a SENSOR, not a note: "Every thesis that emits one
gets it checked mechanically at every candle close; the moment the named level+event
resolves, re-fire tv-thesis with event_trigger: other_side_tripwire_resolved - do not
wait for a candidate to wander in and escalate. A branch the thesis wrote down and was
re-read 24 minutes late cost a scored week -2R plus its best trade."

WHY THIS FILE EXISTS. On jn1 session-day 2026-06-01 the orchestrator checked the
tripwire only at candidate decision minutes. The NY_PRE tripwire (bb_ma_15m, event
2m_close_through_with_ma) resolved at 08:22; it surfaced at 08:42, and only because a
trigger agent noticed its own candle was the firing. Five adjudications, one fill, two
management calls and an exit all had to be voided. Checking "at every candle close"
has to be code, not diligence.

The scan is causal: it only ever reads bars that have CLOSED, and it returns the first
minute at which the named event is true. It never looks past the window end.
"""
from __future__ import annotations

import pandas as pd

from scripts.replay_tools.htf import bars
from src.htf_ma.levels import NY, bb_ma_asof


def _tf_closes(day: pd.DataFrame, tf: int):
    o = day.open.resample(f"{tf}min", label="right", closed="left").first().dropna()
    c = day.close.resample(f"{tf}min", label="right", closed="left").last().dropna()
    h = day.high.resample(f"{tf}min", label="right", closed="left").max().dropna()
    l = day.low.resample(f"{tf}min", label="right", closed="left").min().dropna()
    return o, c, h, l


def resolve_tripwire(sess_day: str, day_next: str, level_price: float, event: str,
                     side: str, start: str, end: str, body_min: float = 0.5):
    """First minute in [start, end] at which the tripwire resolves, or None.

    side: the direction the OTHER SIDE would trade. "long" means resolution is an
    UP close through the level; "short" means a DOWN close through.

    event:
      2m_close_through_with_ma - a 2m bar closes beyond `level_price` AND crosses its
                                 own 2m BB MA in the same candle, in `side`'s direction.
      15m_decisive_close       - a 15m bar closes beyond `level_price` with
                                 |close-open|/range >= body_min.
      displacement_from_defended_level - a 2m bar closes beyond `level_price` having
                                 opened on the other side of it (a displacement candle).
    """
    b = bars()
    day = b[f"{sess_day} 18:00":f"{day_next} 13:00"]
    up = side.lower().startswith("l")
    t0 = pd.Timestamp(f"{day_next} {start}", tz=NY)
    t1 = pd.Timestamp(f"{day_next} {end}", tz=NY)

    if event == "15m_decisive_close":
        o, c, h, l = _tf_closes(day, 15)
        for t in c.index:
            if not (t0 <= t <= t1):
                continue
            rng = max(float(h.loc[t] - l.loc[t]), 0.01)
            body = abs(float(c.loc[t] - o.loc[t])) / rng
            through = (float(c.loc[t]) > level_price) if up else (float(c.loc[t]) < level_price)
            if through and body >= body_min:
                return {"minute": t.strftime("%H:%M"), "event": event,
                        "close": float(c.loc[t]), "body_ratio": round(body, 2),
                        "level": level_price}
        return None

    o, c, _, _ = _tf_closes(day, 2)
    ma2, _ = bb_ma_asof(day, 2)
    for t in c.index:
        if not (t0 <= t <= t1):
            continue
        u = t - pd.Timedelta(minutes=1)
        cl, op = float(c.loc[t]), float(o.loc[t])
        through = (cl > level_price) if up else (cl < level_price)
        if not through:
            continue
        if event == "displacement_from_defended_level":
            opened_other_side = (op < level_price) if up else (op > level_price)
            if opened_other_side:
                return {"minute": t.strftime("%H:%M"), "event": event,
                        "open": op, "close": cl, "level": level_price}
        else:                                     # 2m_close_through_with_ma
            if u not in ma2.index or pd.isna(ma2.loc[u]):
                continue
            m = float(ma2.loc[u])
            crossed = ((op - m) * (cl - m) < 0) and ((cl > m) if up else (cl < m))
            if crossed:
                return {"minute": t.strftime("%H:%M"), "event": event,
                        "open": op, "close": cl, "own_ma_2m": round(m, 2),
                        "level": level_price}
    return None


# ---------------------------------------------------------------- dynamic levels
#
# A tripwire is armed with the level's price AT THAT MINUTE, but VWAP bands and BB MAs
# MOVE. Evaluating later bars against the frozen number is wrong in both directions: it
# fires early when the band has risen away, and misses when the band has fallen toward
# price. Measured on jn1 day 1: the NY_PRE tripwire armed "vwap_m1 30459.80" at 08:00
# read as resolved at 08:06 against the frozen number, when the live band was ~14pt
# higher and the thesis's own MA-reclaim clause was unmet; the true resolution was 08:26,
# which is when the orchestrator actually re-fired. So: resolve named levels per bar.

_DYNAMIC = {"vwap", "vwap_p1", "vwap_p2", "vwap_p3", "vwap_m1", "vwap_m2", "vwap_m3",
            "bb_ma_2m", "bb_ma_3m", "bb_ma_15m", "bb_ma_60m"}


def _level_series(day, name):
    """Per-1m series for a named moving level, or None if the name is not dynamic."""
    from src.htf_ma.levels import vwap_bands
    n = (name or "").strip().lower()
    if n.startswith("bb_ma_"):
        tf = int(n.split("_")[-1].rstrip("m"))
        m, _ = bb_ma_asof(day, tf)
        return m
    if n in _DYNAMIC:
        return vwap_bands(day)[n]
    return None


def resolve_tripwire_named(sess_day, day_next, level_name, armed_price, event, side,
                           start, end, body_min=0.5):
    """Like resolve_tripwire, but re-reads `level_name` at every bar when it is a
    moving level (VWAP band / BB MA). Falls back to the armed price for fixed levels
    (profile edges, session extremes, prior-day levels)."""
    b = bars()
    day = b[f"{sess_day} 18:00":f"{day_next} 13:00"]
    ser = _level_series(day, level_name)
    if ser is None:
        return resolve_tripwire(sess_day, day_next, armed_price, event, side, start, end,
                                body_min)
    up = side.lower().startswith("l")
    t0 = pd.Timestamp(f"{day_next} {start}", tz=NY)
    t1 = pd.Timestamp(f"{day_next} {end}", tz=NY)
    o, c, h, l = _tf_closes(day, 15 if event == "15m_decisive_close" else 2)
    ma2, _ = bb_ma_asof(day, 2)
    for t in c.index:
        if not (t0 <= t <= t1):
            continue
        u = t - pd.Timedelta(minutes=1)
        if u not in ser.index or pd.isna(ser.loc[u]):
            continue
        lvl = float(ser.loc[u])
        cl, op = float(c.loc[t]), float(o.loc[t])
        through = (cl > lvl) if up else (cl < lvl)
        if not through:
            continue
        if event == "15m_decisive_close":
            rng = max(float(h.loc[t] - l.loc[t]), 0.01)
            body = abs(cl - op) / rng
            if body >= body_min:
                return {"minute": t.strftime("%H:%M"), "event": event, "close": cl,
                        "live_level": round(lvl, 2), "armed_level": armed_price,
                        "body_ratio": round(body, 2)}
        elif event == "displacement_from_defended_level":
            if (op < lvl) if up else (op > lvl):
                return {"minute": t.strftime("%H:%M"), "event": event, "open": op,
                        "close": cl, "live_level": round(lvl, 2), "armed_level": armed_price}
        else:
            if u not in ma2.index or pd.isna(ma2.loc[u]):
                continue
            m = float(ma2.loc[u])
            if ((op - m) * (cl - m) < 0) and ((cl > m) if up else (cl < m)):
                return {"minute": t.strftime("%H:%M"), "event": event, "open": op,
                        "close": cl, "own_ma_2m": round(m, 2),
                        "live_level": round(lvl, 2), "armed_level": armed_price}
    return None


if __name__ == "__main__":
    import json
    import sys
    sd, dn, price, event, side, start, end = sys.argv[1:8]
    print(json.dumps(resolve_tripwire(sd, dn, float(price), event, side, start, end), indent=1))
