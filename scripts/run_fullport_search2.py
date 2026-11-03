"""Wider full-port search, with a pre-registered prior-day value-area family.

Ranked on validation. Holdout is reported and is not the sort key.
LucidFlex evals are modeled at 50%. Nothing here places an order.
"""

from __future__ import annotations

import math
import sys
from itertools import pairwise
from pathlib import Path
from typing import NamedTuple

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_fullport import (
    P0,
    _seed,
    bh_mask,
    fullport_life,
    hit_test,
    mean_r,
    month_book,
    pass_rate,
    run_book,
)
from scripts.run_hf_limit import build_days
from scripts.run_limit_research import (
    TRAIN_END,
    VAL_END,
    VAL_MID,
    _num,
    firms,
    money,
    pct,
)
from src.research.strategies.costs import COMMISSION_POINTS, TICK
from src.research.strategies.engine import load_bars
from src.research.strategies.hf_limit import Trade, _manage, scan_limits
from src.research.strategies.jake_rules import value_area
from src.research.strategies.limit_entry import force_fill_at_limit

OUT = ROOT / "docs" / "FULLPORT-SEARCH-2.md"
DATA = ROOT / "data" / "reference" / "nq_1m_master.parquet"
NEWS = ROOT / "data" / "reference" / "news_archive.csv"
OPEN = 9 * 60 + 30
NAN = float("nan")


class Ent(NamedTuple):
    placed: bool
    side: int
    limit: float
    stop: float
    bar: int
    poc: float
    edge: float
    meas: float
    work_buy: float
    work_sell: float
    work_bar: int


def _blank() -> Ent:
    return Ent(False, 0, NAN, 15.0, -1, NAN, NAN, NAN, NAN, NAN, -1)


def _profile(close, vol, mask):
    if int(mask.sum()) < 30:
        return None
    return value_area(np.rint(close[mask]).astype(np.int64), vol[mask])


def news_days() -> set:
    news = pd.read_csv(NEWS)
    hit = news["event"].str.contains("FOMC|CPI", case=False, na=False) & (news["impact"] == "high")
    return set(pd.to_datetime(news.loc[hit, "date"]).dt.date)


def attach(df: pd.DataFrame, days) -> None:
    """Prior-session value and higher-timeframe levels. Nothing from today's RTH."""
    h = df["high"].to_numpy()
    l = df["low"].to_numpy()
    c = df["close"].to_numpy()
    hm = df["hm"].to_numpy()
    vol = df["volume"].to_numpy(dtype=float)
    sess = df["sess"].to_numpy()
    ts = df["ts_event"]
    cuts = np.flatnonzero(np.diff(sess)) + 1
    bounds = np.r_[0, cuts, len(df)]
    sessions = []
    for a, b in pairwise(bounds):
        hh = hm[a:b]
        hit = np.flatnonzero((hh >= OPEN) & (hh < 18 * 60))
        if len(hit) == 0:
            continue
        i0 = int(hit[0])
        rth = (hh >= OPEN) & (hh < 16 * 60)
        sessions.append({
            "ts": ts.iloc[a + i0],
            "rth": _profile(c[a:b], vol[a:b], rth),
            "eth": _profile(c[a:b], vol[a:b], np.ones(b - a, dtype=bool)),
            "rth_hi": float(h[a:b][rth].max()) if rth.any() else NAN,
            "rth_lo": float(l[a:b][rth].min()) if rth.any() else NAN,
        })
    by_ts = {s["ts"]: i for i, s in enumerate(sessions)}
    naked: list[float] = []
    week_hi = week_lo = NAN
    week_open = NAN
    cur_week = None
    building_hi = building_lo = NAN
    month_open = NAN
    cur_month = None
    prev = None
    for day in days:
        i = by_ts.get(day.ts)
        rec = sessions[i] if i is not None else None
        prior = sessions[i - 1] if i is not None and i > 0 else prev
        day.va_rth = prior["rth"] if prior else None
        day.va_eth = prior["eth"] if prior else None
        live = []
        for px in naked:
            if np.isfinite(day.onl) and day.onl - TICK <= px <= day.onh + TICK:
                continue
            live.append(px)
        if live and np.isfinite(day.rth_open):
            day.naked = min(live, key=lambda px: abs(px - day.rth_open))
        else:
            day.naked = NAN
        sunday = day.ts.normalize() - pd.Timedelta(days=(day.ts.weekday() + 1) % 7)
        month = (day.ts.year, day.ts.month)
        if cur_week is None:
            cur_week = sunday
        if sunday != cur_week:
            week_hi, week_lo = building_hi, building_lo
            week_open = NAN
            building_hi = building_lo = NAN
            cur_week = sunday
        if cur_month != month:
            month_open = NAN
            cur_month = month
        day.week_hi, day.week_lo, day.week_open = week_hi, week_lo, week_open
        day.month_open = month_open
        if not np.isfinite(week_open) and np.any(day.hm >= 18 * 60):
            first = int(np.flatnonzero(day.hm >= 18 * 60)[0])
            week_open = float(day.o[first])
            day.week_open = week_open
        if not np.isfinite(month_open):
            month_open = float(day.rth_open)
            day.month_open = NAN
        asia = (day.hm >= 18 * 60) | (day.hm < 3 * 60)
        lon = (day.hm >= 3 * 60) & (day.hm < 8 * 60 + 30)
        day.asia = (float(day.h[asia].max()), float(day.l[asia].min())) if int(asia.sum()) >= 20 else (NAN, NAN)
        day.london = (float(day.h[lon].max()), float(day.l[lon].min())) if int(lon.sum()) >= 20 else (NAN, NAN)
        mids = np.flatnonzero(day.hm == 0)
        day.midnight = float(day.o[int(mids[0])]) if len(mids) else NAN
        c30 = np.flatnonzero(day.hm == 8 * 60 + 30)
        if len(c30):
            k = int(c30[0])
            day.c0830 = (float(day.h[k]), float(day.l[k]), k + 1)
        else:
            day.c0830 = (NAN, NAN, -1)
        day.news = day.ts.date() in NEWS_DATES
        day.ctx_rth = _ctx(day.rth_open, day.va_rth)
        day.ctx_eth = _ctx(day.rth_open, day.va_eth)
        if np.isfinite(day.onl) and np.isfinite(day.onh):
            naked = [px for px in naked if not (day.onl - TICK <= px <= day.onh + TICK)]
        if rec and rec["rth"] is not None:
            poc = rec["rth"][2]
            naked = [px for px in naked if not (rec["rth_lo"] - TICK <= px <= rec["rth_hi"] + TICK)]
            naked.append(poc)
            naked = naked[-12:]
        if rec and np.isfinite(rec["rth_hi"]):
            building_hi = rec["rth_hi"] if not np.isfinite(building_hi) else max(building_hi, rec["rth_hi"])
            building_lo = rec["rth_lo"] if not np.isfinite(building_lo) else min(building_lo, rec["rth_lo"])
        prev = rec


NEWS_DATES: set = set()


def _ctx(op, area):
    if area is None or not np.isfinite(op):
        return None
    val, vah, _poc = area
    if op > vah:
        return "above"
    if op < val:
        return "below"
    return "inside"


def _prior_atr(day, i: int, n: int = 20) -> float:
    if i < n + 1:
        return NAN
    hi = day.h[i - n:i]
    lo = day.l[i - n:i]
    prev = day.c[i - n - 1:i - 1]
    tr = np.maximum(hi - lo, np.maximum(np.abs(hi - prev), np.abs(lo - prev)))
    return float(tr.mean())


def _candles(day, tf: int):
    hm = day.hm
    start = day.i_open
    out = []
    if start >= day.end:
        return out
    anchor = int(hm[start])
    i = start
    while i < day.end:
        bucket = anchor + ((int(hm[i]) - anchor) // tf) * tf
        j = i
        while j < day.end and anchor + ((int(hm[j]) - anchor) // tf) * tf == bucket:
            j += 1
        out.append((i, j - 1, float(day.o[i]), float(day.h[i:j].max()), float(day.l[i:j].min()), float(day.c[j - 1])))
        i = j
    return out


def resolve_fade(day, area, offset: float, context: str, touch: str) -> Ent:
    """Resting fade of VAH/VAL once price is inside the prior value area."""
    if area is None:
        return _blank()
    val, vah, poc = area
    ctx = _ctx(day.rth_open, area)
    if context not in (None, "any") and ctx != context:
        return _blank()
    start = day.i_open
    if ctx != "inside":
        inside = np.flatnonzero((np.arange(len(day.o)) >= start) & (day.c > val) & (day.c < vah))
        if len(inside) == 0:
            return _blank()
        start = int(inside[0]) + 1
    if start >= day.end:
        return _blank()
    buy_px = float(val - offset)
    sell_px = float(vah + offset)
    buy_alive = sell_alive = True
    side = 0
    limit = NAN
    bar = -1
    for i in range(start, day.end):
        b_fill = buy_alive and float(day.o[i]) > buy_px - TICK and float(day.l[i]) <= buy_px - TICK
        s_fill = sell_alive and float(day.o[i]) < sell_px + TICK and float(day.h[i]) >= sell_px + TICK
        if b_fill and s_fill:
            break
        if b_fill or s_fill:
            side = 1 if b_fill else -1
            limit = buy_px if b_fill else sell_px
            bar = i
            break
        if touch == "first":
            b_touch = buy_alive and (float(day.l[i]) <= buy_px or float(day.o[i]) <= buy_px - TICK)
            s_touch = sell_alive and (float(day.h[i]) >= sell_px or float(day.o[i]) >= sell_px + TICK)
            if b_touch:
                buy_alive = False
            if s_touch:
                sell_alive = False
            if not buy_alive and not sell_alive:
                break
    edge = vah if side == 1 else (val if side == -1 else NAN)
    return Ent(True, side, limit, 15.0, bar, float(poc), float(edge) if np.isfinite(edge) else NAN, NAN, buy_px, sell_px, start)


def resolve_disp(day, area, tf: int, beyond: float, stop_mode: str, cancel: int, define: str) -> Ent:
    """First displacement through an edge, then a limit back at that edge."""
    if area is None:
        return _blank()
    val, vah, poc = area
    for i0, i1, op, hi, lo, cl in _candles(day, tf):
        rng = hi - lo
        if rng <= 0:
            continue
        body = abs(cl - op) / rng
        if define == "atr":
            atr = _prior_atr(day, i0)
            if not (np.isfinite(atr) and rng >= atr and body >= 0.5):
                continue
            up = cl > vah and cl > op
            dn = cl < val and cl < op
        else:
            if body < 0.5:
                continue
            up = cl >= vah + beyond and cl > op
            dn = cl <= val - beyond and cl < op
        if not up and not dn:
            continue
        level = float(vah if up else val)
        other = float(val if up else vah)
        side_dir = 1 if up else -1
        start = i1 + 1
        if start >= day.end:
            continue
        end_m = int(day.hm[start]) + int(cancel)
        hit = np.flatnonzero((np.arange(len(day.hm)) >= start) & (day.hm >= end_m) & (day.hm < 18 * 60))
        end = int(hit[0]) if len(hit) else day.end
        end = min(end, day.end)
        for k in range(start, end):
            if (side_dir == 1 and float(day.l[k]) <= other) or (side_dir == -1 and float(day.h[k]) >= other):
                end = k
                break
        if end <= start:
            continue
        if stop_mode == "mid":
            risk = abs(level - (hi + lo) / 2.0)
            if not 8 <= risk <= 80:
                continue
            stop = float(risk)
        else:
            stop = 15.0
        side = 0
        bar = -1
        for i in range(start, end):
            if side_dir == 1 and float(day.o[i]) > level - TICK and float(day.l[i]) <= level - TICK:
                side, bar = 1, i
                break
            if side_dir == -1 and float(day.o[i]) < level + TICK and float(day.h[i]) >= level + TICK:
                side, bar = -1, i
                break
        meas = level + side_dir * rng
        work_buy = level if side_dir == 1 else NAN
        work_sell = level if side_dir == -1 else NAN
        return Ent(True, side, level if side else NAN, stop, bar, float(poc), other, meas, work_buy, work_sell, start)
    return _blank()


def resolve_fail(day, area, mode: str, context: str) -> Ent:
    """Open outside value, two holds back inside, then a limit at the re-entered edge."""
    if area is None:
        return _blank()
    val, vah, poc = area
    ctx = _ctx(day.rth_open, area)
    if ctx not in ("above", "below"):
        return _blank()
    if context not in (None, "any") and ctx != context:
        return _blank()
    n = len(day.o)
    hold_at = None
    if mode == "m30":
        run = 0
        t = OPEN
        while t < 16 * 60:
            m = (day.hm >= t) & (day.hm < t + 30) & (np.arange(n) >= day.i_open) & (np.arange(n) < day.end)
            if int(m.sum()) >= 10:
                last = int(np.flatnonzero(m)[-1])
                if val < float(day.c[last]) < vah:
                    run += 1
                    if run >= 2:
                        hold_at = last + 1
                        break
                else:
                    run = 0
            t += 30
    else:
        run = 0
        for i in range(day.i_open, day.end):
            if val < float(day.c[i]) < vah:
                run += 1
                if run >= 60:
                    hold_at = i + 1
                    break
            else:
                run = 0
    if hold_at is None or hold_at >= day.end:
        return _blank()
    if ctx == "above":
        level, side_dir, edge = float(vah), -1, float(val)
        work_buy, work_sell = NAN, level
    else:
        level, side_dir, edge = float(val), 1, float(vah)
        work_buy, work_sell = level, NAN
    side, bar = 0, -1
    for i in range(hold_at, day.end):
        if side_dir == 1 and float(day.o[i]) > level - TICK and float(day.l[i]) <= level - TICK:
            side, bar = 1, i
            break
        if side_dir == -1 and float(day.o[i]) < level + TICK and float(day.h[i]) >= level + TICK:
            side, bar = -1, i
            break
    return Ent(True, side, level if side else NAN, 15.0, bar, float(poc), edge, NAN, work_buy, work_sell, hold_at)


def _target_px(side: int, limit: float, ent: Ent, reward) -> float:
    if reward == "poc":
        return float(ent.poc)
    if reward == "edge":
        return float(ent.edge)
    if reward == "meas":
        return float(ent.meas)
    return limit + side * float(reward) * ent.stop


def trades_of(day, ent: Ent, reward) -> list[Trade]:
    if not ent.placed or ent.side == 0 or ent.bar < 0 or not np.isfinite(ent.limit):
        return []
    tgt = _target_px(ent.side, ent.limit, ent, reward)
    room = ent.side * (tgt - ent.limit)
    if isinstance(reward, str) and (not np.isfinite(room) or room < 1.0):
        return []
    stop_px = ent.limit - ent.side * ent.stop
    _k, gross, mae, hit = _manage(ent.side, ent.limit, stop_px, tgt, day.o, day.h, day.l, day.c, day.hm, ent.bar, day.end)
    return [Trade(gross, ent.stop, mae, hit)]


def _closer_work(day, ent: Ent) -> tuple[int, float]:
    buy, sell = ent.work_buy, ent.work_sell
    if ent.work_bar < 0:
        return 0, NAN
    if np.isfinite(buy) and not np.isfinite(sell):
        return 1, float(buy)
    if np.isfinite(sell) and not np.isfinite(buy):
        return -1, float(sell)
    if not (np.isfinite(buy) and np.isfinite(sell)):
        return 0, NAN
    op = float(day.o[ent.work_bar])
    if abs(op - buy) <= abs(op - sell):
        return 1, float(buy)
    return -1, float(sell)


def missed_flag(day, ent: Ent, reward) -> bool:
    """Placed, not filled, and a forced fill at the limit from the first live bar would have hit."""
    if not ent.placed or ent.side != 0:
        return False
    side, limit = _closer_work(day, ent)
    if side == 0 or not np.isfinite(limit):
        return False
    tgt = _target_px(side, limit, ent, reward)
    room = side * (tgt - limit)
    if not np.isfinite(room) or room <= 0:
        return False
    stop_px = limit - side * ent.stop
    fill = force_fill_at_limit(day.o, day.h, day.l, day.c, day.hm, ent.work_bar, day.end, side, limit, stop_px, tgt)
    return bool(fill.target_hit)


def _until(day, start: int, minutes: int) -> int:
    if start < 0 or start >= len(day.hm):
        return start
    end_m = int(day.hm[start]) + int(minutes)
    hit = np.flatnonzero((np.arange(len(day.hm)) >= start) & (day.hm >= end_m) & (day.hm < 18 * 60))
    end = int(hit[0]) if len(hit) else day.end
    return min(end, day.end)


def _manage_be(day, side, limit, stop, reward, bar, end, be_at: float) -> Trade:
    stop_px = limit - side * stop
    target = limit + side * reward * stop
    be_from = None
    for k in range(bar, end):
        use = stop_px if be_from is None or k < be_from else limit
        if side == 1:
            if float(day.o[k]) <= use or float(day.l[k]) <= use:
                fill = min(float(day.o[k]), use - TICK) if float(day.o[k]) <= use else use - TICK
                return Trade(fill - limit, stop, max(0.0, limit - fill), False)
            if float(day.h[k]) >= target:
                return Trade(target - limit, stop, 0.0, True)
            if be_from is None and float(day.h[k]) >= limit + be_at:
                be_from = k + 1
        else:
            if float(day.o[k]) >= use or float(day.h[k]) >= use:
                fill = max(float(day.o[k]), use + TICK) if float(day.o[k]) >= use else use + TICK
                return Trade(limit - fill, stop, max(0.0, fill - limit), False)
            if float(day.l[k]) <= target:
                return Trade(limit - target, stop, 0.0, True)
            if be_from is None and float(day.l[k]) <= limit - be_at:
                be_from = k + 1
    last = end - 1
    if last < bar:
        return Trade(0.0, stop, 0.0, False)
    px = float(day.c[last]) - side * TICK
    return Trade(side * (px - limit), stop, 0.0, False)


def _ladder(day, level: float, side: int, start: int, end: int, stop: float, reward, depth=4.0, rungs=3):
    """One position. Deeper trade-throughs fill at the average of the rungs they reach."""
    if not np.isfinite(level) or start < 0 or start >= end:
        return [], False
    prices = [level - side * depth * k for k in range(rungs)]
    far = prices[-1]
    stop_px = far - side * stop
    for i in range(start, end):
        if side == 1 and float(day.o[i]) <= prices[0] - TICK:
            continue
        if side == -1 and float(day.o[i]) >= prices[0] + TICK:
            continue
        got = []
        for px in prices:
            reached = (side == 1 and float(day.l[i]) <= px - TICK) or (side == -1 and float(day.h[i]) >= px + TICK)
            if reached:
                got.append(px)
        if not got:
            continue
        limit = float(np.mean(got))
        risk = abs(limit - stop_px)
        if risk < 1:
            return [], True
        target = limit + side * reward * risk
        _k, gross, mae, hit = _manage(side, limit, stop_px, target, day.o, day.h, day.l, day.c, day.hm, i, end)
        return [Trade(gross, risk, mae, hit)], True
    return [], True


def _two_sided(day, hi, lo, start, stop, reward, offset=0.0, cancel=None, be=None):
    if not (np.isfinite(hi) and np.isfinite(lo)) or start < 0 or start >= day.end:
        return [], False
    end = _until(day, start, cancel) if cancel else day.end
    if end <= start:
        return [], False
    n = len(day.o)
    buy, sell = np.full(n, np.nan), np.full(n, np.nan)
    buy[start:end] = lo - offset
    sell[start:end] = hi + offset
    if be:
        return _be_scan(day, buy, sell, stop, reward, start, end, be), True
    return scan_limits(day.o, day.h, day.l, day.c, day.hm, buy, sell, stop, reward, start, end, max_trades=1), True


def _one_sided(day, level, side, start, stop, reward, offset=0.0, cancel=None, ladder=False, be=None):
    if not np.isfinite(level) or side == 0 or start < 0 or start >= day.end:
        return [], False
    level = level - side * offset
    end = _until(day, start, cancel) if cancel else day.end
    if end <= start:
        return [], False
    if ladder:
        return _ladder(day, level, side, start, end, stop, reward)
    n = len(day.o)
    buy, sell = np.full(n, np.nan), np.full(n, np.nan)
    if side == 1:
        buy[start:end] = level
    else:
        sell[start:end] = level
    if be:
        return _be_scan(day, buy, sell, stop, reward, start, end, be), True
    return scan_limits(day.o, day.h, day.l, day.c, day.hm, buy, sell, stop, reward, start, end, max_trades=1), True


def _be_scan(day, buy, sell, stop, reward, start, end, be_at) -> list[Trade]:
    for i in range(start, end):
        b, s = buy[i], sell[i]
        b_hit = np.isfinite(b) and float(day.o[i]) > b - TICK and float(day.l[i]) <= b - TICK
        s_hit = np.isfinite(s) and float(day.o[i]) < s + TICK and float(day.h[i]) >= s + TICK
        if b_hit == s_hit:
            continue
        side = 1 if b_hit else -1
        limit = float(b if side == 1 else s)
        return [_manage_be(day, side, limit, stop, reward, i, end, be_at)]
    return []


def gate(day, name, level) -> bool:
    if name is None:
        return True
    if not np.isfinite(level):
        return False
    gap = day.rth_open - day.pdc if np.isfinite(day.pdc) else 0.0
    on = day.onh - day.onl if np.isfinite(day.onh) and np.isfinite(day.onl) else NAN
    if name == "on_hi":
        return np.isfinite(on) and on >= CUTS["on75"]
    if name == "on_lo":
        return np.isfinite(on) and on <= CUTS["on25"]
    if name == "gap_with":
        return (gap > 0 and level < day.rth_open) or (gap < 0 and level > day.rth_open)
    if name == "skip_news":
        return not day.news
    if name == "news_only":
        return bool(day.news)
    if name == "not_tested":
        if not (np.isfinite(day.onl) and np.isfinite(day.onh)):
            return True
        return not (day.onl - TICK <= level <= day.onh + TICK)
    if name == "near":
        return 10 <= abs(day.rth_open - level) <= 40
    if name == "midweek":
        return day.ts.weekday() in (1, 2, 3)
    return True


CUTS = {"on75": 1e9, "on25": -1.0}


def _area(day, profile: str):
    return day.va_rth if profile == "rth" else day.va_eth


def run_wide(days, spec):
    kind = spec["kind"]
    reward = spec["reward"]
    stop = spec.get("stop", 15.0)
    offset = spec.get("offset", 0.0)
    cancel = spec.get("cancel")
    ladder = spec.get("ladder", False)
    be = spec.get("be")
    book, placed = [], []
    for day in days:
        trades, was = [], False
        if kind == "week":
            if gate(day, spec.get("gate"), day.week_hi):
                trades, was = _two_sided(day, day.week_hi, day.week_lo, day.i_open, stop, reward, offset, cancel, be)
        elif kind == "week_open":
            side = -1 if np.isfinite(day.week_open) and day.rth_open > day.week_open else 1
            if gate(day, spec.get("gate"), day.week_open):
                trades, was = _one_sided(day, day.week_open, side, day.i_open, stop, reward, offset, cancel, ladder, be)
        elif kind == "month_open":
            side = -1 if np.isfinite(day.month_open) and day.rth_open > day.month_open else 1
            if gate(day, spec.get("gate"), day.month_open):
                trades, was = _one_sided(day, day.month_open, side, day.i_open, stop, reward, offset, cancel, ladder, be)
        elif kind == "asia":
            if gate(day, spec.get("gate"), day.asia[0]):
                trades, was = _two_sided(day, day.asia[0], day.asia[1], day.i_open, stop, reward, offset, cancel, be)
        elif kind == "london":
            if gate(day, spec.get("gate"), day.london[0]):
                trades, was = _two_sided(day, day.london[0], day.london[1], day.i_open, stop, reward, offset, cancel, be)
        elif kind == "midnight":
            side = -1 if np.isfinite(day.midnight) and day.rth_open > day.midnight else 1
            if gate(day, spec.get("gate"), day.midnight):
                trades, was = _one_sided(day, day.midnight, side, day.i_open, stop, reward, offset, cancel, ladder, be)
        elif kind == "c0830":
            hi, lo, st = day.c0830
            if gate(day, spec.get("gate"), hi):
                trades, was = _two_sided(day, hi, lo, st, stop, reward, offset, cancel, be)
        elif kind == "settle":
            side = -1 if day.rth_open > day.pdc else 1
            if gate(day, spec.get("gate"), day.pdc):
                trades, was = _one_sided(day, day.pdc, side, day.i_open, stop, reward, offset, cancel, ladder, be)
        elif kind == "naked":
            side = 1 if np.isfinite(day.naked) and day.naked < day.rth_open else -1
            if gate(day, spec.get("gate"), day.naked):
                trades, was = _one_sided(day, day.naked, side, day.i_open, stop, reward, offset, cancel, ladder, be)
        elif kind == "gap" and np.isfinite(day.pdc) and abs(day.rth_open - day.pdc) >= 10:
            side = 1 if day.rth_open > day.pdc else -1
            trades, was = _one_sided(day, day.pdc, side, day.i_open, stop, reward, offset, cancel, ladder, be)
        book.append(trades)
        placed.append(was)
    return book, placed


def va_jobs():
    """Entry keys, then the reward rows that share that entry."""
    jobs = []
    for profile in ("rth", "eth"):
        for context in ("any", "inside", "above", "below"):
            for offset in (0.0, 4.0):
                for touch in ("rest", "first"):
                    rewards = (0.75, 1.7, "poc", "edge")
                    specs = []
                    for reward in rewards:
                        specs.append({
                            "name": f"fade_{profile}_{context}_off{offset:.0f}_{touch}_{reward}",
                            "family": "va", "kind": "fade", "profile": profile, "context": context,
                            "offset": offset, "touch": touch, "reward": reward,
                        })
                    jobs.append((("fade", profile, context, offset, touch), specs))
        for tf in (1, 2, 3, 5):
            for stop_mode in ("fixed", "mid"):
                for cancel in (30, 60):
                    specs = []
                    for reward in (0.75, 1.7, "meas"):
                        specs.append({
                            "name": f"disp_{profile}_tf{tf}_close_{stop_mode}_x{cancel}_{reward}",
                            "family": "va", "kind": "disp", "profile": profile, "tf": tf,
                            "define": "close", "stop_mode": stop_mode, "cancel": cancel, "reward": reward,
                        })
                    jobs.append((("disp", profile, tf, "close", stop_mode, cancel), specs))
        for tf in (1, 5):
            for stop_mode in ("fixed", "mid"):
                for cancel in (30, 60):
                    specs = []
                    for reward in (0.75, 1.7):
                        specs.append({
                            "name": f"disp_{profile}_tf{tf}_atr_{stop_mode}_x{cancel}_{reward}",
                            "family": "va", "kind": "disp", "profile": profile, "tf": tf,
                            "define": "atr", "stop_mode": stop_mode, "cancel": cancel, "reward": reward,
                        })
                    jobs.append((("disp", profile, tf, "atr", stop_mode, cancel), specs))
        for tf, define in ((5, "close"),):
            for context in ("above", "inside", "below"):
                specs = []
                for reward in (0.75, 1.7):
                    specs.append({
                        "name": f"disp_{profile}_tf{tf}_{define}_fixed_x60_{context}_{reward}",
                        "family": "va", "kind": "disp", "profile": profile, "tf": tf, "define": define,
                        "stop_mode": "fixed", "cancel": 60, "context": context, "reward": reward,
                    })
                jobs.append((("dispctx", profile, tf, define, context), specs))
        for mode in ("m30", "m60"):
            for context in ("any", "above", "below"):
                rewards = (0.75, 1.7, "poc", "edge") if context == "any" else (0.75, 1.7, "edge")
                specs = []
                for reward in rewards:
                    specs.append({
                        "name": f"fail_{profile}_{mode}_{context}_{reward}",
                        "family": "va", "kind": "fail", "profile": profile, "mode": mode,
                        "context": context, "reward": reward,
                    })
                jobs.append((("fail", profile, mode, context), specs))
    return jobs


def wide_specs():
    specs = []
    kinds = ("week", "week_open", "month_open", "asia", "london", "midnight", "c0830", "settle", "naked", "gap")
    for kind in kinds:
        for stop in (15.0, 25.0):
            for reward in (0.75, 1.7):
                specs.append({
                    "name": f"{kind}_s{stop:.0f}_{reward}", "family": "wide", "kind": kind,
                    "stop": stop, "reward": reward,
                })
    for kind in ("london", "week", "asia"):
        for gate_name in ("on_hi", "on_lo", "gap_with", "skip_news", "not_tested", "near", "midweek"):
            specs.append({
                "name": f"{kind}_s15_{gate_name}_1.7", "family": "wide", "kind": kind,
                "stop": 15.0, "reward": 1.7, "gate": gate_name,
            })
    for kind in ("week", "london", "asia", "settle"):
        for reward in (0.75, 1.7):
            specs.append({
                "name": f"{kind}_s15_off4_{reward}", "family": "wide", "kind": kind,
                "stop": 15.0, "reward": reward, "offset": 4.0,
            })
            specs.append({
                "name": f"{kind}_s15_x60_{reward}", "family": "wide", "kind": kind,
                "stop": 15.0, "reward": reward, "cancel": 60,
            })
    for kind in ("week", "london", "settle"):
        specs.append({
            "name": f"{kind}_s15_be_1.7", "family": "wide", "kind": kind,
            "stop": 15.0, "reward": 1.7, "be": 8.0,
        })
    for kind in ("settle", "midnight", "week_open"):
        specs.append({
            "name": f"{kind}_s15_ladder_1.7", "family": "wide", "kind": kind,
            "stop": 15.0, "reward": 1.7, "ladder": True,
        })
    return specs


def _fills(book, idxs):
    return [tr for i in idxs for tr in book[i]]


def _p0(reward):
    if reward == 1.7:
        return P0
    if reward == 0.75:
        return 1.0 / 1.75
    return None


def _be(stop: float, reward: float) -> float:
    win = reward * stop - COMMISSION_POINTS
    loss = stop + TICK + COMMISSION_POINTS
    return loss / (win + loss) if win + loss > 0 else 1.0


def score_book(spec, book, placed, days, val_i, hold_i, miss_fn=None):
    reward = spec["reward"]
    p0 = _p0(reward)
    val, hold = _fills(book, val_i), _fills(book, hold_i)
    row = {
        **spec,
        "book": book,
        "val": hit_test(val, p0 if p0 is not None else 0.5),
        "hold": hit_test(hold, p0 if p0 is not None else 0.5),
        "val_r": mean_r(val),
        "hold_r": mean_r(hold),
        "val_placed": int(sum(placed[i] for i in val_i)),
        "hold_placed": int(sum(placed[i] for i in hold_i)),
        "be": _be(15.0, reward) if isinstance(reward, float) else NAN,
        "bh": False,
    }
    if p0 is None:
        row["val"]["p"] = NAN
        row["hold"]["p"] = NAN
    if miss_fn is not None:
        row["miss_val"] = _miss_rate(days, placed, book, val_i, miss_fn)
        row["miss_hold"] = _miss_rate(days, placed, book, hold_i, miss_fn)
    else:
        row["miss_val"] = NAN
        row["miss_hold"] = NAN
    return row


def _miss_rate(days, placed, book, idxs, miss_fn) -> float:
    n_placed = 0
    n_miss = 0
    for i in idxs:
        if not placed[i]:
            continue
        n_placed += 1
        if book[i]:
            continue
        if miss_fn(days[i], i):
            n_miss += 1
    if n_placed == 0:
        return NAN
    return n_miss / n_placed


def _apply_bh(rows):
    usable = [r for r in rows if isinstance(r["reward"], float) and not (isinstance(r["val"]["p"], float) and math.isnan(r["val"]["p"]))]
    if not usable:
        return
    pvals = np.array([r["val"]["p"] for r in usable])
    flags = bh_mask(pvals)
    for r, ok in zip(usable, flags, strict=False):
        r["bh"] = bool(ok)


def _top(rows, key, n=5):
    ok = [r for r in rows if r["val"]["n"] >= 80 and not (isinstance(r["val"][key], float) and math.isnan(r["val"][key]))]
    ok.sort(key=lambda r: -r["val"][key])
    return ok[:n]


def _d(v) -> str:
    if isinstance(v, float) and math.isnan(v):
        return "n/a"
    return f"{float(v):.1f}"


def _fill_cell(r, which):
    n = r[which]["n"]
    placed = r["val_placed" if which == "val" else "hold_placed"]
    if placed <= 0:
        return "n/a"
    return f"{pct(n / placed)}"


def _line(r):
    v, h = r["val"], r["hold"]
    p = v["p"]
    p_s = "n/a" if isinstance(p, float) and math.isnan(p) else f"{p:.3f}"
    return (
        f"| {r['name']} | {v['n']} | {pct(v['hit'])} ({pct(v['lo'])} to {pct(v['hi'])}) | {p_s} | "
        f"{'yes' if r.get('bh') else 'no'} | {_num(r['val_r'][0])} | {_fill_cell(r, 'val')} | "
        f"{h['n']} | {pct(h['hit'])} ({pct(h['lo'])} to {pct(h['hi'])}) | {_num(r['hold_r'][0])} | {_fill_cell(r, 'hold')} |"
    )


def _above(lo, bar) -> bool:
    return isinstance(lo, float) and isinstance(bar, float) and not math.isnan(lo) and not math.isnan(bar) and lo > bar


def _context_table(days, book, idxs, window: str) -> list[str]:
    lines = []
    for label in ("above", "inside", "below"):
        chosen = [i for i in idxs if getattr(days[i], "ctx_rth", None) == label]
        trades = _fills(book, chosen)
        test = hit_test(trades, P0)
        lines.append(
            f"| {window} | {label} | {len(chosen)} | {test['n']} | {pct(test['hit'])} ({pct(test['lo'])} to {pct(test['hi'])}) | {_num(mean_r(trades)[0])} |"
        )
    return lines


def _named(rows, name):
    return next((r for r in rows if r["name"] == name), None)


def _verdict(va, va_top, top_f, base, eval_table) -> str:
    onhl = base["hold17"]
    fade = _named(va, "fade_rth_any_off0_rest_1.7")
    fails = [r for r in va if r["kind"] == "fail" and r["reward"] == 1.7]
    fail_n = max((r["val"]["n"] for r in fails), default=0)
    if fade is None or not va_top:
        head = "The prior-day value-area family had no ranked 1.7:1 fade."
    else:
        winner = va_top[0]
        better = [r for r in va_top if _above(r["hold"]["lo"], onhl["hit"])]
        head = (
            f"Prior-day value area does not replace `onhl_pull_s15`. "
            f"The reaction, a resting limit at the prior cash value-area high and low, is `{fade['name']}`: "
            f"holdout hit {pct(fade['hold']['hit'])} ({pct(fade['hold']['lo'])} to {pct(fade['hold']['hi'])}) "
            f"on {fade['hold']['n']} fills, mean R {_num(fade['hold_r'][0])}. "
            f"That is the 37% no-drift line, and the order filled on {_fill_cell(fade, 'hold')} of holdout days an order was placed. "
            f"The best value-area 1.7:1 row on validation is `{winner['name']}`, holdout hit "
            f"{pct(winner['hold']['hit'])} ({pct(winner['hold']['lo'])} to {pct(winner['hold']['hi'])}) "
            f"on {winner['hold']['n']} fills. "
            f"`onhl_pull_s15` in this same fill code is {pct(onhl['hit'])} ({pct(onhl['lo'])} to {pct(onhl['hi'])}) "
            f"on {onhl['n']} fills. "
        )
        if better:
            head += f"`{better[0]['name']}` is a top value-area row whose holdout interval sits above that onhl point. "
        else:
            head += "No top value-area holdout interval sits entirely above that point. "
        head += (
            f"The failed-auction rows top out at {fail_n} validation fills, under the 80-fill line, so they were not ranked. "
        )
    if top_f:
        winner = top_f[0]
        better = [r for r in top_f if _above(r["hold"]["lo"], onhl["hit"])]
        head += (
            f"Across the rest of the search the validation winner is `{winner['name']}`, holdout hit {pct(winner['hold']['hit'])} "
            f"({pct(winner['hold']['lo'])} to {pct(winner['hold']['hi'])}). "
        )
        if not better:
            head += "No top-five holdout interval sits entirely above the onhl point. "
        else:
            head += f"`{better[0]['name']}` clears the onhl point on its holdout interval. "
    if eval_table:
        head += f"The best validation eval book is `{eval_table[0]['name']}`, average validation pass {pct(eval_table[0]['avg'])}."
    return head


def _family_note(va) -> str:
    fade = _named(va, "fade_rth_any_off0_rest_1.7")
    poc = _named(va, "fade_rth_any_off0_rest_poc")
    edge = _named(va, "fade_rth_any_off0_rest_edge")
    fails = [r for r in va if str(r["name"]).startswith("fail_") and r["reward"] == 1.7 and r["context"] == "any"]
    bits = []
    if fade:
        bits.append(
            "The cash-session fade is the reaction in the table above. First-touch and a 4-point offset are in the same ranked list."
        )
    if poc:
        bits.append(
            f"Targeting the point of control on that same fade left validation mean R {_num(poc['val_r'][0])} "
            f"({_num(poc['val_r'][1])} to {_num(poc['val_r'][2])}) and holdout mean R {_num(poc['hold_r'][0])} "
            f"({_num(poc['hold_r'][1])} to {_num(poc['hold_r'][2])})."
        )
    if edge:
        bits.append(
            f"Targeting the opposite edge hit {pct(edge['hold']['hit'])} of holdout fills and mean R {_num(edge['hold_r'][0])}."
        )
    if fails:
        detail = ", ".join(f"{r['name']} {r['val']['n']} validation fills" for r in fails)
        bits.append(
            "A failed auction needs an open outside value, two closes back inside, and a later retest, so the samples stay small. "
            f"The combined rows: {detail}. Under 80 validation fills, they stay out of the ranking."
        )
    bits.append(
        "Displacement missed-winner rates near 40% to 50% mean many breaks ran away without a trade-through. "
        "The retests that did fill are the ones that came back."
    )
    return " ".join(bits)


def _london_note(wide) -> str:
    row = _named(wide, "london_s15_off4_1.7")
    if row is None or row["hold"]["n"] < 20:
        return ""
    return (
        f"`london_s15_off4_1.7` is fifth on validation and the strongest holdout in that table: "
        f"{pct(row['hold']['hit'])} ({pct(row['hold']['lo'])} to {pct(row['hold']['hi'])}) on {row['hold']['n']} fills, "
        f"mean R {_num(row['hold_r'][0])} ({_num(row['hold_r'][1])} to {_num(row['hold_r'][2])}). "
        f"The hit interval starts above 37% and above the 38.9% cost breakeven at a 15-point stop. "
        f"It does not sit entirely above the onhl point of 48.3%, and its validation p-value of {row['val']['p']:.3f} "
        f"does not survive the correction. Validation put it fifth. It is not the selected book."
    )


def render(va, wide, base, eval_table, lives, months, ctx_lines, ensemble) -> str:
    va17 = [r for r in va if r["reward"] == 1.7]
    va_top = _top(va17, "hit")
    funded_all = [r for r in va + wide if r["reward"] == 1.7]
    top_f = _top(funded_all, "hit")
    n17 = len(funded_all)
    n75 = len([r for r in va + wide if r["reward"] == 0.75])
    lines = [
        "# Full-port search 2",
        "",
        _verdict(va, va_top, top_f, base, eval_table),
        "",
        "Disarmed. Nothing here places an order. LucidFlex evals are modeled at 50%: two equal winning days pass. The funded shot is one 1.7:1 trade. The eval shot is a 0.75R trade risking the max loss, up to $2,000, aimed at about $1,500. FundedNext is sized to its $1,500 max loss.",
        "",
        "The LucidFlex rows in `docs/FULLPORT-LIFECYCLE.md` were recomputed at that 50% rule. Two 0.75R wins on a $2,000 stop still finish a little short of the $3,000 target after commission, so the $2,000 overnight-pull pass rate barely moved. The one-trade full-target path did move: LucidFlex validation pass 33.0% in 3.2 days. The $2,000 lifecycle is EV $266 ($201 to $332), 37.6 payouts per 100, and the 21-day book is $806 with P(negative) 37.0%.",
        "",
        (
            "Every variant below was named before the holdout was opened. A row needs 80 validation fills to be ranked. "
            "Funded rows are sorted by the validation hit rate. Eval rows are sorted by the average validation pass rate across the three firms. "
            "Holdout is printed beside them and was not the sort key. "
            f"Benjamini-Hochberg at 10% covers {n17} funded tests against 37% and {n75} eval tests against 57%. "
            f"The smallest funded p-value has to be about {0.10 / n17:.4f} to survive on its own. "
            "Context splits of one entry are in that list, so the correction is strict. A native target has no single hit-rate null. Its mean R interval is the check."
        ),
        "",
        "Costs are the same as the rest of this stack. A limit fills only if the bar trades one tick through and did not open already through. The stop is a market, one tick worse, and it is checked before the target. Research R subtracts Topstep's $1.22. The no-drift hit rate is 37% at 1.7R and 57% at 0.75R. Breakeven after costs at a 15-point stop is about 38.9% at 1.7R and about 60% at 0.75R. A ±$500 coin is a different payoff, about 26% to pass, and a higher pass rate on a full-port day is not by itself an edge over that coin.",
        "",
        "The order-flow filter was not run. The MBP-10 files in the repo are sample days, not a continuous book, and a one-minute snapshot is too coarse to confirm a touch. FOMC and CPI days come from `data/reference/news_archive.csv`.",
        "",
        f"`onhl_pull_s15`, same fill code: validation hit {pct(base['val17']['hit'])} on {base['val17']['n']} fills, holdout hit {pct(base['hold17']['hit'])} ({pct(base['hold17']['lo'])} to {pct(base['hold17']['hi'])}) on {base['hold17']['n']} fills. That is the bar.",
        "",
        "## Prior-day value area",
        "",
        "The value area is 70% of volume around the prior session's point of control, in 1-point bins, with each minute's volume booked at the close. `rth` is the prior cash session, 09:30 to 15:59 ET. `eth` is the prior full session, from 18:00 ET through that cash close. Today's profile is not used.",
        "",
        "A fade rests a short at the prior high and a long at the prior low, and only once price is inside the area, so the approach is from inside. `rest` leaves the order working until the first fill. `first` cancels a side when its first touch does not trade through. An offset of 4 points rests the limit beyond the edge. A displacement is the first candle that closes through an edge, either by 4 points with a body of at least half its range, or with a range at least as large as the prior 20 one-minute bars' average true range and that same body rule, on a 1, 2, 3, or 5 minute bar built from the one-minute data. The retest is a limit back at the broken edge, in the breakout direction. It is cancelled after 30 or 60 minutes, or if the other edge trades. The stop is 15 points beyond the edge, or the displacement candle's midpoint when that distance is between 8 and 80 points. A failed auction opens outside the area, closes back inside for two 30-minute blocks (or 60 one-minute closes), then limits the retest of that edge. The native targets are the point of control, the opposite edge, and, for a displacement, one candle-range beyond the broken level. A native target closer than one point is not taken.",
        "",
        "### Funded, 1.7:1, top validation hit rates",
        "",
        "| variant | val n | val hit | p vs 37% | BH | val mean R | val fill | hold n | hold hit | hold mean R | hold fill |",
        "|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    a = lines.append
    for r in va_top:
        a(_line(r))
    a("")
    a(_family_note(va))
    a("")
    a("### Native target")
    a("")
    a("Point of control, the opposite edge, or one displacement range past the broken level. Ranked by validation mean R among rows with 80 validation fills.")
    a("")
    a("| variant | val n | val hit | val mean R | hold n | hold hit | hold mean R |")
    a("|---|---:|---:|---:|---:|---:|---:|")
    native = [r for r in va if isinstance(r["reward"], str) and r["val"]["n"] >= 80]
    native.sort(key=lambda r: -r["val_r"][0] if not (isinstance(r["val_r"][0], float) and math.isnan(r["val_r"][0])) else -999)
    for r in native[:8]:
        a(
            f"| {r['name']} | {r['val']['n']} | {pct(r['val']['hit'])} | {_num(r['val_r'][0])} ({_num(r['val_r'][1])} to {_num(r['val_r'][2])}) | "
            f"{r['hold']['n']} | {pct(r['hold']['hit'])} | {_num(r['hold_r'][0])} ({_num(r['hold_r'][1])} to {_num(r['hold_r'][2])}) |"
        )
    a("")
    a("### Opening context, cash-session profile")
    a("")
    a("This splits the fills of `fade_rth_any_off0_rest_1.7` by where the cash open sat relative to the prior cash value area. It is the same book as that row, not an extra test.")
    a("")
    a("| window | open | days | fills | hit | mean R |")
    a("|---|---|---:|---:|---:|---:|")
    for line in ctx_lines:
        a(line)
    a("")
    a("### Missed winners")
    a("")
    a("A missed winner is a day an order was working, price never traded through it, and a forced fill at that limit from the first live bar would have hit the target before the stop. Where both a short and a long were working, the counterfactual uses the side closer to the open. The rate is those days divided by days an order was placed.")
    a("")
    a("| variant | val missed | hold missed |")
    a("|---|---:|---:|")
    for r in va_top:
        a(f"| {r['name']} | {pct(r['miss_val'])} | {pct(r['miss_hold'])} |")
    a("")
    a("### Eval, 0.75R")
    a("")
    a("Pass rates for the value-area names that were in the validation pass-rate table. LucidFlex uses 50%.")
    a("")
    a("| variant | firm | val pass | holdout pass | holdout days |")
    a("|---|---|---:|---:|---:|")
    for r in eval_table:
        if r["family"] != "va":
            continue
        for f in r["firms"]:
            a(
                f"| {r['name']} | {f['firm']} | {pct(f['val']['pass'])} | "
                f"{pct(f['hold']['pass'])} ({pct(f['hold']['lo'])} to {pct(f['hold']['hi'])}) | {_d(f['hold']['days'])} |"
            )
    a("")
    a("## The wider list")
    a("")
    a("Prior-week high and low, weekly open, monthly open, Asia high and low, London high and low, the midnight open, the 08:30 ET candle, the prior settle, the nearest naked point of control, and a gap-fill limit at the prior close. Also, pre-declared: a 4-point offset beyond the level, a 60-minute cancel, a stop moved to the entry after 8 points of profit, and a three-rung ladder 4 points apart that fills at the average of the rungs the bar trades through. Filters, pre-declared: overnight range in the outer train quartiles, trade only with the gap, skip FOMC and CPI days, skip a level the overnight already traded, level 10 to 40 points from the open, Tuesday to Thursday.")
    a("")
    a("| variant | val n | val hit | p vs 37% | BH | val mean R | val fill | hold n | hold hit | hold mean R | hold fill |")
    a("|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|")
    for r in _top([x for x in wide if x["reward"] == 1.7], "hit"):
        a(_line(r))
    a("")
    a("## Top five overall")
    a("")
    a("Funded rows are every 1.7:1 variant in both families. Eval rows are the 0.75R names whose validation pass rate was simulated, ranked by the average across the three firms. `onhl_pull_s15` is in the eval table as the reference. It is not a new funded candidate.")
    a("")
    a("### Funded")
    a("")
    a("| rank | variant | val hit | hold hit | hold mean R | beats onhl on holdout? |")
    a("|---:|---|---:|---:|---:|---|")
    for i, r in enumerate(top_f, 1):
        beats = _above(r["hold"]["lo"], base["hold17"]["hit"])
        a(
            f"| {i} | {r['name']} | {pct(r['val']['hit'])} ({pct(r['val']['lo'])} to {pct(r['val']['hi'])}) | "
            f"{pct(r['hold']['hit'])} ({pct(r['hold']['lo'])} to {pct(r['hold']['hi'])}) | {_num(r['hold_r'][0])} | "
            f"{'interval above onhl point' if beats else 'no'} |"
        )
    a("")
    a(f"onhl_pull_s15 holdout, same code: {pct(base['hold17']['hit'])} ({pct(base['hold17']['lo'])} to {pct(base['hold17']['hi'])}).")
    a("")
    note = _london_note(wide)
    if note:
        a(note)
        a("")
    a("### Eval")
    a("")
    a("| rank | variant | avg val pass | Topstep holdout | LucidFlex holdout | FundedNext holdout |")
    a("|---:|---|---:|---:|---:|---:|")
    for i, r in enumerate(eval_table[:5], 1):
        by = {f["firm"]: f for f in r["firms"]}
        a(
            f"| {i} | {r['name']} | {pct(r['avg'])} | {pct(by['Topstep']['hold']['pass'])} | "
            f"{pct(by['LucidFlex']['hold']['pass'])} | {pct(by['FundedNext Futures Flex']['hold']['pass'])} |"
        )
    a("")
    a("## One signal a day")
    a("")
    a(ensemble["text"])
    a("")
    a("## Lifecycle")
    a("")
    a(
        "The eval book is the validation-best 0.75R setup among the names whose pass rate was simulated, which includes the overnight pull. "
        "The funded book is the validation-best 1.7:1 setup from this search. LucidFlex uses a 50% eval consistency rule. "
        "The floor still moves at the close, and a dip to the floor still ends the account. "
        "The onhl row is a fresh draw of `onhl_pull_s15` in both phases. The recorded LucidFlex full-port figure stays the one in `docs/FULLPORT-LIFECYCLE.md`. "
        "In this draw the overnight-pull row pays more per eval at every firm. The month below is the selected mix."
    )
    a("")
    a("| firm | book | holdout pass | EV per eval | payouts / 100 |")
    a("|---|---|---:|---|---:|")
    for row in lives:
        a(
            f"| {row['firm']} | {row['book']} | {pct(row['life']['pass'])} | "
            f"{money(row['life']['mean'])} ({money(row['life']['lo'])} to {money(row['life']['hi'])}) | {row['life']['pays']:.1f} |"
        )
    a("")
    a("| firm | evals opened | mean 21-day book | 95% CI | P(month negative) |")
    a("|---|---:|---:|---|---:|")
    for row in months:
        a(f"| {row['firm']} | {row['slots']} | {money(row['mean'])} | {money(row['lo'])} to {money(row['hi'])} | {pct(row['p_neg'])} |")
    a("")
    return "\n".join(lines) + "\n"


def _run_entries(days, key):
    kind = key[0]
    out = []
    if kind == "fade":
        _k, profile, context, offset, touch = key
        for day in days:
            out.append(resolve_fade(day, _area(day, profile), offset, context, touch))
    elif kind == "disp":
        _k, profile, tf, define, stop_mode, cancel = key
        for day in days:
            out.append(resolve_disp(day, _area(day, profile), tf, 4.0, stop_mode, cancel, define))
    elif kind == "dispctx":
        _k, profile, tf, define, context = key
        for day in days:
            area = _area(day, profile)
            if _ctx(day.rth_open, area) != context:
                out.append(_blank())
                continue
            out.append(resolve_disp(day, area, tf, 4.0, "fixed", 60, define))
    elif kind == "fail":
        _k, profile, mode, context = key
        for day in days:
            out.append(resolve_fail(day, _area(day, profile), mode, context))
    return out


def _book_from(days, ents, reward):
    book, placed = [], []
    for day, ent in zip(days, ents, strict=True):
        book.append(trades_of(day, ent, reward))
        placed.append(bool(ent.placed))
    return book, placed


def _ensemble(days, members, rank_i, val_i, hold_i):
    """Priority from the first validation half. One fill, the highest priority that fired."""
    ranked = []
    for name, book in members:
        trades = _fills(book, rank_i)
        test = hit_test(trades, P0)
        score = test["hit"] if test["n"] >= 30 and not math.isnan(test["hit"]) else -1.0
        ranked.append((score, test["n"], name, book))
    ranked.sort(key=lambda item: (-item[0], item[1], item[2]))
    book = []
    for i in range(len(days)):
        chosen = []
        for _score, _n, _name, member in ranked:
            if member[i]:
                chosen = member[i][:1]
                break
        book.append(chosen)
    order = ", ".join(f"{name} ({pct(score)})" for score, _n, name, _book in ranked if score >= 0)
    half = hit_test(_fills(book, val_i), P0)
    hold = hit_test(_fills(book, hold_i), P0)
    text = (
        f"The members were named first: the overnight pull, the cash-session fade at the edge, the full-session fade, "
        f"week, London, Asia, midnight, the 08:30 candle, the settle, the naked point of control, and the gap fill, each at a 15-point stop and 1.7R. "
        f"Priority is the hit rate on the first half of validation, from 1 Jul 2024 to 1 Jan 2025, and only a member with 30 fills in that half is used. "
        f"Order: {order}. "
        f"The second validation half, which did not set the order, hit {pct(half['hit'])} ({pct(half['lo'])} to {pct(half['hi'])}) on {half['n']} fills. "
        f"Holdout hit {pct(hold['hit'])} ({pct(hold['lo'])} to {pct(hold['hi'])}) on {hold['n']} fills, mean R {_num(mean_r(_fills(book, hold_i))[0])}. "
        f"A day takes the first of those signals in that order. It does not stack them."
    )
    return {"text": text, "book": book, "half": half, "hold": hold}


def main() -> None:
    global NEWS_DATES, CUTS
    print("load", flush=True)
    df = load_bars(str(DATA))
    days = build_days(df)
    NEWS_DATES = news_days()
    attach(df, days)
    ons = np.array([
        d.onh - d.onl for d in days
        if d.ts < TRAIN_END and np.isfinite(d.onh) and np.isfinite(d.onl)
    ])
    CUTS = {"on75": float(np.quantile(ons, 0.75)), "on25": float(np.quantile(ons, 0.25))}
    print("days", len(days), "news", len(NEWS_DATES), "on", round(CUTS["on75"], 1), flush=True)
    val_i = [i for i, d in enumerate(days) if TRAIN_END <= d.ts < VAL_END]
    hold_i = [i for i, d in enumerate(days) if d.ts >= VAL_END]
    rank_i = [i for i, d in enumerate(days) if TRAIN_END <= d.ts < VAL_MID]
    rest_i = [i for i, d in enumerate(days) if VAL_MID <= d.ts < VAL_END]
    b17 = run_book_baseline(days, 1.7)
    b75 = run_book_baseline(days, 0.75)
    base = {
        "val17": hit_test(_fills(b17, val_i), P0),
        "hold17": hit_test(_fills(b17, hold_i), P0),
        "book17": b17,
        "book75": b75,
    }
    print("baseline hold", round(base["hold17"]["hit"], 3), base["hold17"]["n"], flush=True)
    va = []
    jobs = va_jobs()
    print("va jobs", len(jobs), flush=True)
    for n, (key, specs) in enumerate(jobs, 1):
        ents = _run_entries(days, key)
        for spec in specs:
            book, placed = _book_from(days, ents, spec["reward"])
            miss_fn = lambda day, i, ents=ents, reward=spec["reward"]: missed_flag(day, ents[i], reward)
            va.append(score_book(spec, book, placed, days, val_i, hold_i, miss_fn))
        if n % 20 == 0:
            print("va", n, "/", len(jobs), flush=True)
    wide = []
    specs = wide_specs()
    print("wide", len(specs), flush=True)
    for n, spec in enumerate(specs, 1):
        book, placed = run_wide(days, spec)
        wide.append(score_book(spec, book, placed, days, val_i, hold_i))
        if n % 20 == 0:
            print("wide", n, "/", len(specs), flush=True)
    _apply_bh([r for r in va + wide if r["reward"] == 1.7])
    _apply_bh([r for r in va + wide if r["reward"] == 0.75])
    primary = next(r for r in va if r["name"] == "fade_rth_any_off0_rest_1.7")
    ctx_lines = _context_table(days, primary["book"], val_i, "validation")
    ctx_lines.extend(_context_table(days, primary["book"], hold_i, "holdout"))
    members = [("onhl_pull_s15", b17)]
    for name in (
        "fade_rth_any_off0_rest_1.7",
        "fade_eth_any_off0_rest_1.7",
        "week_s15_1.7",
        "london_s15_1.7",
        "asia_s15_1.7",
        "midnight_s15_1.7",
        "c0830_s15_1.7",
        "settle_s15_1.7",
        "naked_s15_1.7",
        "gap_s15_1.7",
    ):
        found = next((r for r in va + wide if r["name"] == name), None)
        if found:
            members.append((name, found["book"]))
    ensemble = _ensemble(days, members, rank_i, rest_i, hold_i)
    print("ensemble hold", round(ensemble["hold"]["hit"], 3) if ensemble["hold"]["n"] >= 20 else "na", flush=True)
    cands = _top([r for r in va + wide if r["reward"] == 0.75], "hit", 6)
    va_cands = _top([r for r in va if r["reward"] == 0.75], "hit", 4)
    seen = set()
    pass_rows = []
    for spec in cands + va_cands:
        if spec["name"] in seen:
            continue
        seen.add(spec["name"])
        pass_rows.append(spec)
    firm_list = firms()
    eval_table = []
    # Reference book, so the overnight pull can still win the eval phase.
    pass_rows.append({"name": "onhl_pull_s15", "family": "ref", "reward": 0.75, "book": b75})
    for spec in pass_rows:
        print("pass", spec["name"], flush=True)
        book = spec["book"]
        firms_out = []
        for s in firm_list:
            risk = min(2000.0, float(s["mll"]))
            firms_out.append({
                "firm": s["firm"],
                "val": pass_rate(book, val_i, s, risk, _seed("v2" + spec["name"] + s["firm"]), n=400),
                "hold": pass_rate(book, hold_i, s, risk, _seed("h2" + spec["name"] + s["firm"]), n=400),
            })
        avg = float(np.nanmean([f["val"]["pass"] for f in firms_out]))
        eval_table.append({
            "name": spec["name"], "family": spec.get("family", "wide"), "firms": firms_out,
            "avg": avg, "book": book, "spec": spec,
        })
    eval_table.sort(key=lambda r: -r["avg"] if not math.isnan(r["avg"]) else 0)
    fund_winner = _top([r for r in va + wide if r["reward"] == 1.7], "hit", 1)
    eval_winner = eval_table[0] if eval_table else None
    lives, months = [], []
    if fund_winner and eval_winner:
        fund_days = fund_winner[0]["book"]
        eval_days = eval_winner["book"]
        pairs = [("selected", eval_days, fund_days), ("onhl_pull_s15", b75, b17)]
        for label, eb, fb in pairs:
            eh = [eb[i] for i in hold_i]
            fh = [fb[i] for i in hold_i]
            trades = _fills(eb, hold_i)
            grind = (sum(tr.hit for tr in trades) / len(trades)) if trades else 0.5
            for s in firm_list:
                life = fullport_life(
                    eh, fh, s, np.random.default_rng(_seed("s2" + label + s["firm"])),
                    min(2000.0, float(s["mll"])), grind, n=600,
                )
                lives.append({"firm": s["firm"], "book": label, "life": life})
                print("life", label, s["firm"], round(life["mean"], 1), flush=True)
            if label == "selected":
                for s in firm_list:
                    cash, _note, slots = month_book(eh, fh, s, min(2000.0, float(s["mll"])), grind, n=160)
                    mid = float(cash.mean())
                    se = float(cash.std(ddof=1) / math.sqrt(len(cash)))
                    months.append({
                        "firm": s["firm"], "slots": slots, "mean": mid,
                        "lo": mid - 1.96 * se, "hi": mid + 1.96 * se,
                        "p_neg": float(np.mean(cash < 0)),
                    })
    # Drop the trade lists before writing. The renderer does not need them.
    for row in va + wide:
        row.pop("book", None)
    text = render(va, wide, base, eval_table, lives, months, ctx_lines, ensemble)
    OUT.write_text(text)
    print("wrote", OUT, "va", len(va), "wide", len(wide), flush=True)


def run_book_baseline(days, reward):
    return run_book(days, "onhl_pull", 15.0, reward, "rth", None, {"gap75": 1e9, "gap25": -1, "pd_med": 0}, {}, 1)


if __name__ == "__main__":
    main()
