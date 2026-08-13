"""Mechanical inputs the 0.4.x contracts require. No opinion in any of it.

Three things the 0.3.5 toolchain did not produce:

1. `htf_at_level` - T46. The trigger cannot tell his HIGHEST-conviction shape
   (2m closing both sides of a level while the 15m prints a wick that cannot
   close through) from a level that actually failed, unless it is told how the
   5m and 15m have treated that level so far this session. Without it the
   contract says it will grade his best setups C.

2. `flush_inputs` - T30. Path efficiency and the 15m up/down split, which is
   what the thesis reads to decide whether a trending session may be counter-
   traded at all.

3. `management_minutes` - the tier-3 call schedule, computed from bars rather
   than fired on a timer.

Everything here is computed from committed bars strictly before the decision
minute. Nothing takes a view.
"""
from __future__ import annotations

import pandas as pd

from scripts.build_l2_outcomes import load_bars
from src.htf_ma.levels import NY

_BARS = None


def bars():
    global _BARS
    if _BARS is None:
        b = load_bars()
        b["mi"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
        _BARS = b.set_index("mi").sort_index()[["open", "high", "low", "close", "volume"]]
    return _BARS


def _seg(sess_day, day_next, upto):
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t = pd.Timestamp(f"{day_next} {upto}", tz=NY)
    return bars()[(bars().index >= t0) & (bars().index < t)]


def _tf(seg, minutes):
    return seg.resample(f"{minutes}min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()


def htf_at_level(sess_day, day_next, upto, price, side, lookback=30):
    """How the 2m/5m/15m have treated `price` this session, up to `upto`.

    `side` is the candidate's direction. A SHORT rejects resistance, so the FAR
    side is ABOVE the level; a LONG rejects support, so the far side is BELOW.
    `closes_through` counts TF closes on the far side. `far_side` is `body` if
    anything closed there, `wick` if price traded there but never closed there,
    `untouched` if it never got there at all.

    This is the distinction T46 turns on: 15m wick with no close through means
    the level HELD and the 2m closes through it were noise.
    """
    seg = _seg(sess_day, day_next, upto)
    if not len(seg):
        return {}
    above = side.lower().startswith("s")     # short -> far side is above

    def measure(s):
        blk = {}
        for m in (2, 5, 15):
            t = _tf(s, m)
            if not len(t):
                continue
            closes = int((t.close > price).sum() if above else (t.close < price).sum())
            reached = bool((t.high > price).any() if above else (t.low < price).any())
            blk[f"{m}m"] = {"closes_through": closes,
                            "far_side": "body" if closes else ("wick" if reached else "untouched"),
                            "bars": int(len(t))}
        return blk

    cut = pd.Timestamp(f"{day_next} {upto}", tz=NY) - pd.Timedelta(minutes=lookback)
    return {
        # The CURRENT test of the level - this is the one T46 turns on.
        f"recent_{lookback}m": measure(seg[seg.index >= cut]),
        # Context. A level price has oscillated around all night will show a large
        # session count that says nothing about the episode happening now, which is
        # why the recent window is reported first and separately.
        "session_to_date": measure(seg),
        "far_side_is": "above" if above else "below",
        "note": ("closes_through counts closes on the FAR side of the level; far_side is "
                 "body if anything closed there, wick if price traded there without "
                 "closing there, untouched if it never reached. A 15m wick with no close "
                 "through in the recent window, while the 2m closed both sides, is the "
                 "level holding. Level prices are the value AT this minute; VWAP bands "
                 "and MAs move, so the session-to-date count for those is indicative only."),
    }


def flush_inputs(sess_day, day_next, upto):
    """T30. Path efficiency and the 15m directional split, session-to-date."""
    seg = _seg(sess_day, day_next, upto)
    t15 = _tf(seg, 15)
    if len(t15) < 2:
        return {}
    net = float(t15.close.iloc[-1] - t15.open.iloc[0])
    travel = float((t15.close - t15.open).abs().sum())
    up = int((t15.close > t15.open).sum())
    dn = int((t15.close < t15.open).sum())
    return {"path_efficiency": round(abs(net) / travel, 3) if travel else None,
            "net_move_15m": round(net, 2),
            "total_15m_travel": round(travel, 2),
            "candles_15m_up": up, "candles_15m_down": dn,
            "note": "path_efficiency = |net move| / summed 15m body travel, session to date. "
                    "High efficiency with a lopsided count is the flush shape."}


def body_ratio_15m(sess_day, day_next, upto, n=4):
    """|close-open| / range on the last n completed 15m bars. T10 absorption."""
    t15 = _tf(_seg(sess_day, day_next, upto), 15)
    out = []
    for ts, r in t15.tail(n).iterrows():
        rng = float(r.high - r.low)
        out.append({"start": ts.strftime("%H:%M"),
                    "open": float(r.open), "high": float(r.high),
                    "low": float(r.low), "close": float(r.close),
                    "body_ratio": round(float(abs(r.close - r.open) / rng), 2) if rng else None})
    return out


def management_minutes(day_next, fill_minute, side, entry, stop, targets, levels,
                       window_end, cash_open=None, max_minutes=180):
    """Minutes at which tier 3 must be called, computed from bars.

    Fires on: an intermediate structural level between entry and target being
    REACHED and separately BROKEN (a 2m close beyond it), the first target
    printing, a STALL (>=3 minutes with multiple touches of a level and no close
    through), the approach to the cash open, and the window closing.

    Returns an ordered, de-duplicated list of (minute, reason, level, price).
    A position that resolves with an empty list is a detection defect, not a
    clean trade - the caller is expected to say so.
    """
    b = bars()
    t0 = pd.Timestamp(f"{day_next} {fill_minute}", tz=NY)
    w = b[(b.index >= t0) & (b.index <= t0 + pd.Timedelta(minutes=max_minutes))]
    short = side.lower().startswith("s")
    tp1 = targets[0] if targets else None

    # structural levels strictly between entry and the first target
    inter = []
    for name, px in levels.items():
        if px is None:
            continue
        if tp1 is not None and ((short and tp1 < px < entry) or (not short and entry < px < tp1)):
            inter.append((name, float(px)))
    inter.sort(key=lambda x: x[1], reverse=short)

    ev, seen = [], set()

    def add(ts, reason, level, price):
        k = (ts.strftime("%H:%M"), reason, level)
        if k not in seen:
            seen.add(k)
            ev.append({"minute": ts.strftime("%H:%M"), "reason": reason,
                       "level": level, "level_price": price})

    touch_log = {}
    for ts, r in w.iterrows():
        if ts == t0:
            continue
        # stop / target end the position; caller truncates, we just stop emitting
        if (short and r.high >= stop) or (not short and r.low <= stop):
            break
        for name, px in inter:
            reached = (r.low <= px <= r.high)
            if reached:
                add(ts, "intermediate_level_reached", name, px)
                touch_log.setdefault(name, []).append(ts)
            broke = (r.close < px) if short else (r.close > px)
            if broke:
                add(ts, "intermediate_level_broken", name, px)
            # stall: >=3 distinct minutes touching it, no close beyond
            tl = touch_log.get(name, [])
            if len(tl) >= 3 and (ts - tl[0]) >= pd.Timedelta(minutes=3) and not broke:
                add(ts, "stalling", name, px)
        # momentum visibly gone against the position - the contract's own second
        # half of `stalling`. Without this a trade that runs straight from entry to
        # stop without touching an intermediate level gets NO management call at
        # all, which is precisely the 11-of-12 shape tier 3 was built to stop.
        R = abs(entry - stop)
        adverse = ((r.close - entry) / R) if short else ((entry - r.close) / R)
        if adverse >= 0.5:
            add(ts, "stalling", "adverse_excursion_0.5R", None)
        if tp1 is not None and ((short and r.low <= tp1) or (not short and r.high >= tp1)):
            add(ts, "tp1_reached", "target_1", float(tp1))
            break

    if cash_open:
        co = pd.Timestamp(f"{day_next} {cash_open}", tz=NY)
        if t0 < co <= w.index.max():
            add(co - pd.Timedelta(minutes=2), "pre_cash_open", "cash_open_0930", None)
    if window_end:
        we = pd.Timestamp(f"{day_next} {window_end}", tz=NY)
        if t0 < we <= w.index.max():
            add(we, "window_closing", "window_end", None)

    return sorted(ev, key=lambda e: e["minute"])
