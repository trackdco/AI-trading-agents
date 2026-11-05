"""Pre-registered strategy families. Parameters were written before the run.

Each function appends signal bars. The entry is the next bar. A higher-timeframe
candle is only used after it has closed.
"""

from __future__ import annotations

from itertools import pairwise

import numpy as np
import pandas as pd

from src.research.strategies.engine import FLAT_MINUTE


def _pack(name, idx, side, stop, target):
    return {
        "name": name,
        "i": np.asarray(idx, dtype=np.int32),
        "side": np.asarray(side, dtype=np.int8),
        "stop": np.asarray(stop, dtype=np.float64),
        "target": np.asarray(target, dtype=np.float64),
    }


def _rr_target(open_next, side, stop, rr):
    risk = side * (open_next - stop)
    return open_next + side * rr * risk


def orb(df: pd.DataFrame, minutes: int, rr: float, fade: bool, name: str):
    o = df["open"].to_numpy()
    h = df["high"].to_numpy()
    l = df["low"].to_numpy()
    c = df["close"].to_numpy()
    hm = df["hm"].to_numpy()
    sess = df["sess"].to_numpy()
    idx, side, stop, tgt = [], [], [], []
    start_m = 9 * 60 + 30
    end_or = start_m + minutes
    # session boundaries
    cuts = np.flatnonzero(np.diff(sess)) + 1
    bounds = np.concatenate([[0], cuts, [len(df)]])
    for a, b in pairwise(bounds):
        hms = hm[a:b]
        or_mask = (hms >= start_m) & (hms < end_or)
        if or_mask.sum() < minutes // 2:
            continue
        rel = np.flatnonzero(or_mask)
        or_hi = h[a:b][rel].max()
        or_lo = l[a:b][rel].min()
        # 18:00 is minute 1080, which is numerically after 09:45, but it is the
        # evening before the opening range exists. Stay in the morning.
        after = np.flatnonzero((hms >= end_or) & (hms < 18 * 60))
        for rel_i in after:
            j = a + rel_i
            if hm[j] >= FLAT_MINUTE - 5:
                break
            close = c[j]
            if not fade:
                if close > or_hi:
                    s, st = 1, or_lo
                elif close < or_lo:
                    s, st = -1, or_hi
                else:
                    continue
            else:
                if h[j] > or_hi and close < or_hi and close > or_lo:
                    s, st = -1, h[j]
                elif l[j] < or_lo and close > or_lo and close < or_hi:
                    s, st = 1, l[j]
                else:
                    continue
            if j + 1 >= b:
                break
            target = _rr_target(o[j + 1], s, st, rr)
            idx.append(j)
            side.append(s)
            stop.append(st)
            tgt.append(target)
            break
    return _pack(name, idx, side, stop, tgt)


def vwap_reversion(df: pd.DataFrame, points: float, rr: float | None, name: str):
    o = df["open"].to_numpy()
    h = df["high"].to_numpy()
    l = df["low"].to_numpy()
    c = df["close"].to_numpy()
    hm = df["hm"].to_numpy()
    vwap = df["vwap"].to_numpy()
    idx, side, stop, tgt = [], [], [], []
    last_sess = None
    armed = True
    sess = df["sess"].to_numpy()
    for j in range(1, len(df) - 1):
        if sess[j] != last_sess:
            last_sess = sess[j]
            armed = True
        if not armed or hm[j] < 10 * 60 or hm[j] >= FLAT_MINUTE - 5:
            continue
        dist = c[j] - vwap[j]
        if dist >= points and c[j] < o[j]:
            s, st = -1, h[j]
        elif dist <= -points and c[j] > o[j]:
            s, st = 1, l[j]
        else:
            continue
        if rr is None:
            target = float(vwap[j])
        else:
            target = _rr_target(o[j + 1], s, st, rr)
        idx.append(j)
        side.append(s)
        stop.append(st)
        tgt.append(target)
        armed = False
    return _pack(name, idx, side, stop, tgt)


def vwap_pullback(df: pd.DataFrame, rr: float, name: str):
    o = df["open"].to_numpy()
    h = df["high"].to_numpy()
    l = df["low"].to_numpy()
    c = df["close"].to_numpy()
    hm = df["hm"].to_numpy()
    vwap = df["vwap"].to_numpy()
    rth_open = df["rth_open"].to_numpy()
    sess = df["sess"].to_numpy()
    idx, side, stop, tgt = [], [], [], []
    last = None
    used = False
    for j in range(1, len(df) - 1):
        if sess[j] != last:
            last = sess[j]
            used = False
        if used or hm[j] < 10 * 60 or hm[j] >= 12 * 60:
            continue
        if np.isnan(rth_open[j]) or np.isnan(vwap[j]):
            continue
        if c[j] > vwap[j] and c[j] > rth_open[j] and l[j] <= vwap[j]:
            s, st = 1, l[j]
        elif c[j] < vwap[j] and c[j] < rth_open[j] and h[j] >= vwap[j]:
            s, st = -1, h[j]
        else:
            continue
        idx.append(j)
        side.append(s)
        stop.append(st)
        tgt.append(_rr_target(o[j + 1], s, st, rr))
        used = True
    return _pack(name, idx, side, stop, tgt)


def prior_day(df: pd.DataFrame, fade: bool, rr: float, name: str):
    o = df["open"].to_numpy()
    h = df["high"].to_numpy()
    l = df["low"].to_numpy()
    c = df["close"].to_numpy()
    hm = df["hm"].to_numpy()
    pdh = df["pdh"].to_numpy()
    pdl = df["pdl"].to_numpy()
    sess = df["sess"].to_numpy()
    idx, side, stop, tgt = [], [], [], []
    last = None
    used = False
    for j in range(1, len(df) - 1):
        if sess[j] != last:
            last = sess[j]
            used = False
        if used or hm[j] < 9 * 60 + 30 or hm[j] >= FLAT_MINUTE - 5:
            continue
        if np.isnan(pdh[j]):
            continue
        if fade:
            if h[j] > pdh[j] and c[j] < pdh[j]:
                s, st = -1, h[j]
            elif l[j] < pdl[j] and c[j] > pdl[j]:
                s, st = 1, l[j]
            else:
                continue
        else:
            if c[j] > pdh[j] and c[j - 1] <= pdh[j]:
                s, st = 1, min(l[j], pdh[j])
            elif c[j] < pdl[j] and c[j - 1] >= pdl[j]:
                s, st = -1, max(h[j], pdl[j])
            else:
                continue
        idx.append(j)
        side.append(s)
        stop.append(st)
        tgt.append(_rr_target(o[j + 1], s, st, rr))
        used = True
    return _pack(name, idx, side, stop, tgt)


def overnight(df: pd.DataFrame, fade: bool, rr: float, name: str):
    o = df["open"].to_numpy()
    h = df["high"].to_numpy()
    l = df["low"].to_numpy()
    c = df["close"].to_numpy()
    hm = df["hm"].to_numpy()
    onh = df["onh"].to_numpy()
    onl = df["onl"].to_numpy()
    sess = df["sess"].to_numpy()
    idx, side, stop, tgt = [], [], [], []
    last = None
    used = False
    for j in range(1, len(df) - 1):
        if sess[j] != last:
            last = sess[j]
            used = False
        # overnight range is complete once RTH starts; do not use a bar before 09:30
        if used or hm[j] < 9 * 60 + 35 or hm[j] >= 11 * 60 + 30:
            continue
        if np.isnan(onh[j]):
            continue
        if fade:
            if h[j] > onh[j] and c[j] < onh[j]:
                s, st = -1, h[j]
            elif l[j] < onl[j] and c[j] > onl[j]:
                s, st = 1, l[j]
            else:
                continue
        else:
            if c[j] > onh[j]:
                s, st = 1, onl[j]
            elif c[j] < onl[j]:
                s, st = -1, onh[j]
            else:
                continue
        idx.append(j)
        side.append(s)
        stop.append(st)
        tgt.append(_rr_target(o[j + 1], s, st, rr))
        used = True
    return _pack(name, idx, side, stop, tgt)


def gap(df: pd.DataFrame, mode: str, name: str):
    """mode: fill_struct, fill_025, go_025."""
    o = df["open"].to_numpy()
    c = df["close"].to_numpy()
    hm = df["hm"].to_numpy()
    pdc = df["pdc"].to_numpy()
    rth_open = df["rth_open"].to_numpy()
    sess = df["sess"].to_numpy()
    idx, side, stop, tgt = [], [], [], []
    last = None
    used = False
    for j in range(1, len(df) - 1):
        if sess[j] != last:
            last = sess[j]
            used = False
        if used or np.isnan(pdc[j]) or np.isnan(rth_open[j]):
            continue
        gap = rth_open[j] - pdc[j]
        if abs(gap) < 15:
            continue
        if mode == "go_025":
            if hm[j] < 9 * 60 + 35 or hm[j] >= 9 * 60 + 45:
                continue
            if gap > 0 and c[j] > rth_open[j]:
                s = 1
            elif gap < 0 and c[j] < rth_open[j]:
                s = -1
            else:
                continue
            st = rth_open[j]
            target = _rr_target(o[j + 1], s, st, 0.25)
        else:
            if hm[j] < 9 * 60 + 30 or hm[j] >= 10 * 60:
                continue
            s = -1 if gap > 0 else 1
            st = rth_open[j] + (abs(gap) if gap > 0 else -abs(gap))
            # stop is one full gap beyond the open, in the gap direction
            st = rth_open[j] + gap
            if mode == "fill_struct":
                target = pdc[j]
            else:
                target = _rr_target(o[j + 1], s, st, 0.25)
        idx.append(j)
        side.append(s)
        stop.append(st)
        tgt.append(target)
        used = True
    return _pack(name, idx, side, stop, tgt)


def stretch(df: pd.DataFrame, rr: float, name: str):
    o = df["open"].to_numpy()
    c = df["close"].to_numpy()
    h = df["high"].to_numpy()
    l = df["low"].to_numpy()
    atr = df["atr"].to_numpy()
    hm = df["hm"].to_numpy()
    idx, side, stop, tgt = [], [], [], []
    last_i = -100
    for j in range(20, len(df) - 1):
        if hm[j] < 9 * 60 + 45 or hm[j] >= FLAT_MINUTE - 5:
            continue
        if j - last_i < 15 or np.isnan(atr[j]) or atr[j] < 1:
            continue
        move = c[j] - c[j - 15]
        if abs(move) < 2 * atr[j]:
            continue
        if move > 0:
            s, st = -1, h[j]
        else:
            s, st = 1, l[j]
        idx.append(j)
        side.append(s)
        stop.append(st)
        tgt.append(_rr_target(o[j + 1], s, st, rr))
        last_i = j
    return _pack(name, idx, side, stop, tgt)


def volume_spike(df: pd.DataFrame, exhaust: bool, name: str):
    o = df["open"].to_numpy()
    h = df["high"].to_numpy()
    l = df["low"].to_numpy()
    c = df["close"].to_numpy()
    hm = df["hm"].to_numpy()
    vol = df["volume"].to_numpy()
    med = df["vol_med"].to_numpy()
    idx, side, stop, tgt = [], [], [], []
    last_i = -30
    roll_hi = pd.Series(h).rolling(10, min_periods=10).max().to_numpy()
    roll_lo = pd.Series(l).rolling(10, min_periods=10).min().to_numpy()
    for j in range(20, len(df) - 1):
        if hm[j] < 9 * 60 + 30 or hm[j] >= FLAT_MINUTE - 5 or j - last_i < 10:
            continue
        if np.isnan(med[j]) or med[j] <= 0 or vol[j] < 3 * med[j]:
            continue
        rng = h[j] - l[j]
        if rng <= 0:
            continue
        loc = (c[j] - l[j]) / rng
        if not exhaust:
            if loc >= 0.75:
                s, st = 1, l[j]
            elif loc <= 0.25:
                s, st = -1, h[j]
            else:
                continue
        else:
            if h[j] >= roll_hi[j] and loc <= 0.4:
                s, st = -1, h[j]
            elif l[j] <= roll_lo[j] and loc >= 0.6:
                s, st = 1, l[j]
            else:
                continue
        idx.append(j)
        side.append(s)
        stop.append(st)
        tgt.append(_rr_target(o[j + 1], s, st, 0.25))
        if not exhaust and name.endswith("100"):
            tgt[-1] = _rr_target(o[j + 1], s, st, 1.0)
        last_i = j
    return _pack(name, idx, side, stop, tgt)


def open_drive(df: pd.DataFrame, name: str):
    """At 10:00, trade the direction of the 09:30-10:00 drive. One setting."""
    o = df["open"].to_numpy()
    h = df["high"].to_numpy()
    l = df["low"].to_numpy()
    c = df["close"].to_numpy()
    hm = df["hm"].to_numpy()
    sess = df["sess"].to_numpy()
    rth_open = df["rth_open"].to_numpy()
    idx, side, stop, tgt = [], [], [], []
    cuts = np.flatnonzero(np.diff(sess)) + 1
    bounds = np.concatenate([[0], cuts, [len(df)]])
    for a, b in pairwise(bounds):
        hms = hm[a:b]
        at = np.flatnonzero(hms == 10 * 60)
        if len(at) == 0:
            continue
        j = a + int(at[0])
        if j + 1 >= len(df) or np.isnan(rth_open[j]):
            continue
        rel = np.flatnonzero((hms >= 9 * 60 + 30) & (hms <= 10 * 60))
        if len(rel) < 10:
            continue
        drive = c[j] - rth_open[j]
        if abs(drive) < 8:
            continue
        if drive > 0:
            s, st = 1, float(l[a:b][rel].min())
        else:
            s, st = -1, float(h[a:b][rel].max())
        idx.append(j)
        side.append(s)
        stop.append(st)
        tgt.append(_rr_target(o[j + 1], s, st, 0.25))
    return _pack(name, idx, side, stop, tgt)


def crt(df: pd.DataFrame, minutes: int, kind: str, rr: float | None, name: str):
    """CRT. `close`: the next HTF candle sweeps and closes back inside.

    `intra`: during the next HTF window, the first closed 1-minute bar that
    has traded outside the prior candle and closes back inside.
    The prior candle is complete before either test looks at it.
    """
    ts = df["ts_event"]
    bucket = ts.dt.floor(f"{minutes}min")
    work = df[["high", "low", "close", "open", "hm"]].copy()
    work["bucket"] = bucket
    work["i"] = np.arange(len(df))
    g = work.groupby("bucket", sort=True)
    agg = g.agg(hi=("high", "max"), lo=("low", "min"), cl=("close", "last"), end_i=("i", "max"), n=("i", "size"))
    buckets = agg.index
    hi = agg["hi"].to_numpy()
    lo = agg["lo"].to_numpy()
    cl = agg["cl"].to_numpy()
    end_i = agg["end_i"].to_numpy()
    o = df["open"].to_numpy()
    h = df["high"].to_numpy()
    l = df["low"].to_numpy()
    c = df["close"].to_numpy()
    hm = df["hm"].to_numpy()
    idx, side, stop, tgt = [], [], [], []
    step = np.timedelta64(minutes, "m")
    bvals = buckets.to_numpy()
    for k in range(len(agg) - 1):
        if bvals[k + 1] - bvals[k] != step:
            continue
        if kind == "close":
            swept_hi = hi[k + 1] > hi[k] and lo[k + 1] >= lo[k] and lo[k] < cl[k + 1] < hi[k]
            swept_lo = lo[k + 1] < lo[k] and hi[k + 1] <= hi[k] and lo[k] < cl[k + 1] < hi[k]
            if not swept_hi and not swept_lo:
                continue
            j = int(end_i[k + 1])
            if j + 1 >= len(df):
                continue
            if hm[j] < 9 * 60 + 30 or hm[j] >= FLAT_MINUTE - 5:
                continue
            if swept_hi:
                s, st = -1, hi[k + 1]
                structural = lo[k]
            else:
                s, st = 1, lo[k + 1]
                structural = hi[k]
            target = structural if rr is None else _rr_target(o[j + 1], s, st, rr)
            idx.append(j)
            side.append(s)
            stop.append(st)
            tgt.append(target)
        else:
            # first 1m close back inside after a sweep, strictly after bucket k has closed
            start = int(end_i[k]) + 1
            end = int(end_i[k + 1])
            swept = False
            s = 0
            st = 0.0
            for j in range(start, end + 1):
                if hm[j] < 9 * 60 + 30 or hm[j] >= FLAT_MINUTE - 5:
                    continue
                if not swept:
                    if h[j] > hi[k] and l[j] < lo[k]:
                        break
                    if h[j] > hi[k]:
                        swept, s, st = True, -1, h[j]
                    elif l[j] < lo[k]:
                        swept, s, st = True, 1, l[j]
                    else:
                        continue
                if s == -1 and l[j] < lo[k]:
                    break
                if s == 1 and h[j] > hi[k]:
                    break
                inside = lo[k] < c[j] < hi[k]
                reclaimed = (s == -1 and c[j] < hi[k]) or (s == 1 and c[j] > lo[k])
                if swept and inside and reclaimed and j + 1 < len(df):
                    st = h[j] if s == -1 else l[j]
                    structural = lo[k] if s == -1 else hi[k]
                    target = structural if rr is None else _rr_target(o[j + 1], s, st, rr)
                    idx.append(j)
                    side.append(s)
                    stop.append(st)
                    tgt.append(target)
                    break
    return _pack(name, idx, side, stop, tgt)


def delta_divergence(df: pd.DataFrame, delta: pd.Series, rr: float, name: str):
    """Fade a 20-bar price extreme when the closed minute's delta disagrees.

    Delta is joined on the bar timestamp. Missing minutes are not signals.
    """
    aligned = delta.reindex(df["ts_event"].dt.tz_convert("UTC").dt.floor("min"))
    dlt = aligned.to_numpy()
    o = df["open"].to_numpy()
    h = df["high"].to_numpy()
    l = df["low"].to_numpy()
    hm = df["hm"].to_numpy()
    roll_hi = pd.Series(h).rolling(20, min_periods=20).max().to_numpy()
    roll_lo = pd.Series(l).rolling(20, min_periods=20).min().to_numpy()
    idx, side, stop, tgt = [], [], [], []
    last_i = -20
    for j in range(20, len(df) - 1):
        if hm[j] < 9 * 60 + 30 or hm[j] >= FLAT_MINUTE - 5 or j - last_i < 10:
            continue
        if np.isnan(dlt[j]):
            continue
        if h[j] >= roll_hi[j] and dlt[j] < 0:
            s, st = -1, h[j]
        elif l[j] <= roll_lo[j] and dlt[j] > 0:
            s, st = 1, l[j]
        else:
            continue
        idx.append(j)
        side.append(s)
        stop.append(st)
        tgt.append(_rr_target(o[j + 1], s, st, rr))
        last_i = j
    return _pack(name, idx, side, stop, tgt)


def main_catalog(df: pd.DataFrame) -> list[dict]:
    """The variants counted by the multiple-testing correction. Written before any result."""
    return [
        crt(df, 15, "close", 0.25, "crt15_close_025"),
        crt(df, 15, "close", 1.0, "crt15_close_100"),
        crt(df, 15, "close", None, "crt15_close_struct"),
        crt(df, 15, "intra", 0.25, "crt15_intra_025"),
        crt(df, 60, "close", 0.25, "crt60_close_025"),
        crt(df, 60, "close", None, "crt60_close_struct"),
        orb(df, 15, 0.25, False, "orb15_break_025"),
        orb(df, 15, 1.0, False, "orb15_break_100"),
        orb(df, 30, 0.25, False, "orb30_break_025"),
        orb(df, 15, 0.25, True, "orb15_fade_025"),
        orb(df, 15, 1.0, True, "orb15_fade_100"),
        vwap_reversion(df, 20, 0.25, "vwap20_rev_025"),
        vwap_reversion(df, 20, 1.0, "vwap20_rev_100"),
        vwap_reversion(df, 40, 0.25, "vwap40_rev_025"),
        vwap_reversion(df, 20, None, "vwap20_rev_struct"),
        vwap_pullback(df, 0.25, "vwap_pb_025"),
        vwap_pullback(df, 1.0, "vwap_pb_100"),
        prior_day(df, True, 0.25, "pd_fade_025"),
        prior_day(df, True, 1.0, "pd_fade_100"),
        prior_day(df, False, 0.25, "pd_break_025"),
        overnight(df, False, 0.25, "on_break_025"),
        overnight(df, True, 0.25, "on_fade_025"),
        gap(df, "fill_struct", "gap_fill_struct"),
        gap(df, "fill_025", "gap_fill_025"),
        gap(df, "go_025", "gap_go_025"),
        stretch(df, 0.25, "stretch_025"),
        stretch(df, 1.0, "stretch_100"),
        volume_spike(df, False, "vol_cont_025"),
        volume_spike(df, False, "vol_cont_100"),
        volume_spike(df, True, "vol_exh_025"),
        open_drive(df, "open_drive_025"),
    ]
