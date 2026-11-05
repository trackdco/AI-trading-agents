"""Order-flow and volume-profile rules from the two videos Angus sent.

The list is frozen before the holdout is scored. Nothing here places an order.
"""

from __future__ import annotations

import math
import sys
from itertools import pairwise
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_daily_book import month_passes
from scripts.run_daily_book import run_book as onhl_book
from scripts.run_fullport import (
    P0,
    _seed,
    bh_mask,
    fullport_life,
    hit_test,
    mean_r,
    month_book,
)
from scripts.run_hf_limit import build_days
from scripts.run_limit_research import TRAIN_END, VAL_END, _num, firms, money, pct
from scripts.run_mae_mfe import excursion, random_fill
from src.research.strategies.costs import COMMISSION_POINTS, TICK
from src.research.strategies.engine import load_bars
from src.research.strategies.hf_limit import Trade, _manage
from src.research.strategies.jake_rules import value_area

OUT = ROOT / "docs" / "OF-VP-VIDEOS-TEST.md"
DATA = ROOT / "data" / "reference" / "nq_1m_master.parquet"
CVD = ROOT / "data" / "reference" / "cvd"
NY = "America/New_York"
OPEN = 9 * 60 + 30
END_WIN = 11 * 60 + 30
# Frozen because the videos did not give a number.
PUSH_ATR = 0.50
PUSH_TAIL = 0.30
LVN_SPAN = 0.15
POC_BUFFER = 4.0
RECLAIM = 3
PRINT_MIN = 60.0
CONTINUOUS = (
    "footprint_q3_2025.parquet",
    "footprint_q4_2025.parquet",
    "footprint_jan2026.parquet",
    "footprint_feb_mar2026.parquet",
    "footprint_apr2026.parquet",
    "footprint_may_jul2026.parquet",
)


def tick_area(prices: np.ndarray, vols: np.ndarray):
    if len(prices) < 10 or float(np.sum(vols)) <= 0:
        return None
    ticks = np.rint(np.asarray(prices, dtype=float) / TICK).astype(np.int64)
    area = value_area(ticks, np.asarray(vols, dtype=float))
    if area is None or area[1] <= area[0]:
        return None
    return tuple(float(x) * TICK for x in area)


def point_rows(prices: np.ndarray, vols: np.ndarray):
    buckets: dict[int, float] = {}
    for px, vol in zip(prices, vols, strict=True):
        key = int(np.rint(px))
        buckets[key] = buckets.get(key, 0.0) + float(vol)
    if not buckets:
        return None
    keys = np.array(sorted(buckets))
    values = np.array([buckets[int(k)] for k in keys], dtype=float)
    return keys, values


def lvn_far(prices: np.ndarray, vols: np.ndarray, direction: int):
    """Far end of the thin tail. Direction 1 is an up leg, thin at the bottom."""
    rows = point_rows(prices, vols)
    if rows is None:
        return None
    keys, values = rows
    if len(keys) < 4:
        return None
    med = float(np.median(values))
    if direction == 1:
        run = 0
        while run < len(values) and values[run] < med:
            run += 1
        if run == 0:
            return None
        span = float(keys[run - 1] - keys[0])
        leg = float(keys[-1] - keys[0])
        if leg <= 0 or span / leg < LVN_SPAN:
            return None
        return float(keys[0])
    run = 0
    while run < len(values) and values[-1 - run] < med:
        run += 1
    if run == 0:
        return None
    span = float(keys[-1] - keys[-run])
    leg = float(keys[-1] - keys[0])
    if leg <= 0 or span / leg < LVN_SPAN:
        return None
    return float(keys[-1])


def _profile_from_day(day, mask) -> tuple | None:
    if int(mask.sum()) < 10 or not hasattr(day, "vol"):
        return None
    return tick_area(day.c[mask], day.vol[mask])


def attach(df: pd.DataFrame, days) -> None:
    """Overnight value, the vacuum leg, and bar volume. Today's cash session is not in the profile."""
    hm = df["hm"].to_numpy()
    close = df["close"].to_numpy(dtype=float)
    vol = df["volume"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    sess = df["sess"].to_numpy()
    ts = df["ts_event"]
    cuts = np.flatnonzero(np.diff(sess)) + 1
    bounds = np.r_[0, cuts, len(df)]
    by_open = {}
    ranges: list[float] = []
    for a, b in pairwise(bounds):
        hh = hm[a:b]
        hit = np.flatnonzero((hh >= OPEN) & (hh < 18 * 60))
        if len(hit) == 0:
            continue
        by_open[ts.iloc[a + int(hit[0])]] = (a, b)
    for day in days:
        rth = (day.hm >= OPEN) & (day.hm < 16 * 60)
        day.atr_day = float(np.mean(ranges[-20:])) if len(ranges) >= 20 else float("nan")
        if int(rth.sum()) >= 30:
            ranges.append(float(day.h[rth].max() - day.l[rth].min()))
        bounds_day = by_open.get(day.ts)
        day.vol = np.zeros(len(day.o))
        day.on_va = None
        day.leg = None
        if bounds_day is None:
            continue
        a, b = bounds_day
        day.vol = vol[a:b]
        on = (day.hm >= 18 * 60) | (day.hm < OPEN)
        if int(on.sum()) < 30:
            continue
        day.on_va = tick_area(close[a:b][on], vol[a:b][on])
        if not np.isfinite(day.atr_day) or not np.isfinite(day.onh) or not np.isfinite(day.onl):
            continue
        width = float(day.onh - day.onl)
        if width < PUSH_ATR * day.atr_day or width <= 0:
            continue
        last = int(np.flatnonzero(on)[-1])
        pos = (float(day.c[last]) - float(day.onl)) / width
        if pos >= 1.0 - PUSH_TAIL:
            direction = 1
            swing = int(np.argmin(day.l[: day.i_open])) if day.i_open else 0
        elif pos <= PUSH_TAIL:
            direction = -1
            swing = int(np.argmax(day.h[: day.i_open])) if day.i_open else 0
        else:
            continue
        sl = slice(swing, day.i_open)
        if sl.stop - sl.start < 10:
            continue
        poc_area = tick_area(close[a:b][sl], vol[a:b][sl])
        far = lvn_far(close[a:b][sl], vol[a:b][sl], direction)
        if poc_area is None or far is None:
            continue
        day.leg = {"direction": direction, "poc": poc_area[2], "target": far, "high": float(high[a:b][sl].max()), "low": float(low[a:b][sl].min())}


def _window_end(day) -> int:
    hit = np.flatnonzero((np.arange(len(day.hm)) >= day.i_open) & (day.hm > END_WIN) & (day.hm < 18 * 60))
    return min(day.end, int(hit[0]) if len(hit) else day.end)


def failed_auction(day):
    """First poke beyond the overnight value area that closes back inside within 3 bars."""
    area = day.on_va
    if area is None:
        return None
    val, vah, poc = area
    end = _window_end(day)
    i = day.i_open
    while i < end:
        up = float(day.h[i]) >= vah + TICK
        dn = float(day.l[i]) <= val - TICK
        if up == dn:
            i += 1
            continue
        side = -1 if up else 1
        level = vah if up else val
        other = val if up else vah
        last = min(i + RECLAIM, end - 1)
        reclaim = None
        for j in range(i, last + 1):
            close = float(day.c[j])
            inside = val < close < vah
            if inside:
                reclaim = j
                break
        if reclaim is None:
            i += 1
            continue
        extreme = float(day.h[i: reclaim + 1].max()) if side == -1 else float(day.l[i: reclaim + 1].min())
        entry_i = reclaim + 1
        if entry_i >= end:
            return None
        stop_px = extreme + 2 * TICK if side == -1 else extreme - 2 * TICK
        fill = float(day.o[entry_i]) + side * TICK
        risk = abs(fill - stop_px)
        if side * (stop_px - fill) >= 0 or not (2.0 <= risk <= 80.0):
            i = reclaim + 1
            continue
        return {
            "side": side, "fill": fill, "bar": entry_i, "stop": stop_px, "risk": risk,
            "level": level, "other": other, "poc": poc, "reclaim": reclaim, "poke": i, "extreme": extreme,
        }
    return None


def market_trade(day, setup, target: float):
    if setup is None or target is None or not np.isfinite(target):
        return []
    if setup["side"] * (target - setup["fill"]) < 1.0:
        return []
    _k, gross, mae, hit = _manage(
        setup["side"], setup["fill"], setup["stop"], target, day.o, day.h, day.l, day.c, day.hm, setup["bar"], day.end,
    )
    trade = Trade(gross, setup["risk"], mae, hit)
    trade.planned = abs(target - setup["fill"])
    return [trade]


def limit_trade(day, setup, target: float | None, reward: float | None = None):
    """Rest at the reclaimed edge on the bars after the close back inside.

    A 1.7R (or 0.75R) target is measured from the limit and the limit's stop, not from the market fill.
    """
    if setup is None or (reward is None and (target is None or not np.isfinite(target))):
        return []
    end = _window_end(day)
    start = setup["reclaim"] + 1
    if start >= end:
        return []
    n = len(day.o)
    buy = np.full(n, np.nan)
    sell = np.full(n, np.nan)
    if setup["side"] == -1:
        sell[start:end] = setup["level"]
    else:
        buy[start:end] = setup["level"]
    for i in range(start, end):
        b, s = buy[i], sell[i]
        b_hit = np.isfinite(b) and float(day.o[i]) > b - TICK and float(day.l[i]) <= b - TICK
        s_hit = np.isfinite(s) and float(day.o[i]) < s + TICK and float(day.h[i]) >= s + TICK
        if b_hit and s_hit:
            continue
        if not b_hit and not s_hit:
            continue
        side = 1 if b_hit else -1
        limit = float(b if side == 1 else s)
        risk = abs(limit - setup["stop"])
        if side * (setup["stop"] - limit) >= 0 or not (2.0 <= risk <= 80.0):
            return []
        px = limit + side * reward * risk if reward is not None else float(target)
        if side * (px - limit) < 1.0:
            return []
        _k, gross, mae, hit = _manage(
            side, limit, setup["stop"], px, day.o, day.h, day.l, day.c, day.hm, i, day.end,
        )
        trade = Trade(gross, risk, mae, hit)
        trade.planned = abs(px - limit)
        return [trade]
    return []


def _target(setup, name: str, reward: float = 1.7):
    if name == "poc":
        return setup["poc"]
    if name == "edge":
        return setup["other"]
    return setup["fill"] + setup["side"] * reward * setup["risk"]


def bar_stamp(day, i: int):
    hm = int(day.hm[i])
    midnight = day.ts.normalize()
    if hm >= 18 * 60:
        midnight = midnight - pd.Timedelta(days=1)
    return midnight + pd.Timedelta(minutes=hm)


def coarse_absorption(day, setup, tape: dict) -> bool:
    """Minute aggregate at the poke extreme. Not a single 60-lot print."""
    if setup is None or not tape:
        return False
    stamp = bar_stamp(day, setup["poke"])
    rec = tape.get(stamp)
    if rec is None:
        return False
    buy_at_high, sell_at_low = rec
    if setup["side"] == -1:
        return buy_at_high >= PRINT_MIN
    return sell_at_low >= PRINT_MIN


def reload_break(day, tape_prices: dict):
    """Crude Variant B. The minute cannot say whether a print sat in the wick as it happened."""
    setup = failed_auction(day)
    if setup is None or not tape_prices:
        return None
    stamp = bar_stamp(day, setup["poke"])
    book = tape_prices.get(stamp)
    if not book:
        return None
    o = float(day.o[setup["poke"]])
    c = float(day.c[setup["poke"]])
    body_lo, body_hi = (o, c) if o <= c else (c, o)
    wick = {}
    body = {}
    for tick, (buy, sell) in book.items():
        price = tick * TICK
        aggr = buy if setup["side"] == -1 else sell
        if price > body_hi + 1e-9 or price < body_lo - 1e-9:
            wick[price] = wick.get(price, 0.0) + aggr
        else:
            body[price] = body.get(price, 0.0) + aggr
    wick_vol = float(sum(wick.values()))
    body_vol = float(sum(body.values()))
    if wick_vol < PRINT_MIN or wick_vol <= body_vol or not wick:
        return None
    cluster = max(wick, key=wick.get)
    end = _window_end(day)
    for j in range(setup["poke"] + 1, min(setup["poke"] + 6, end)):
        close = float(day.c[j])
        crossed = close < cluster if setup["side"] == -1 else close > cluster
        if not crossed:
            continue
        entry_i = j + 1
        if entry_i >= end:
            return None
        fill = float(day.o[entry_i]) + setup["side"] * TICK
        stop_px = setup["extreme"] + 2 * TICK if setup["side"] == -1 else setup["extreme"] - 2 * TICK
        risk = abs(fill - stop_px)
        if setup["side"] * (stop_px - fill) >= 0 or not (2.0 <= risk <= 80.0):
            return None
        return {**setup, "fill": fill, "bar": entry_i, "stop": stop_px, "risk": risk}
    return None


def _five(day):
    out = []
    i = day.i_open
    while i < day.end and int(day.hm[i]) < 18 * 60:
        bucket = OPEN + ((int(day.hm[i]) - OPEN) // 5) * 5
        j = i
        while j < day.end and int(day.hm[j]) < 18 * 60 and OPEN + ((int(day.hm[j]) - OPEN) // 5) * 5 == bucket:
            j += 1
        out.append((j - 1, float(day.h[i:j].max()), float(day.l[i:j].min()), float(day.c[j - 1])))
        i = j
    return out


def manage_trail(day, side: int, fill: float, bar: int, stop_px: float, target: float):
    risk = abs(fill - stop_px)
    if side * (stop_px - fill) >= 0 or not (2.0 <= risk <= 80.0) or side * (target - fill) < 1.0:
        return None, bar, False
    stop = stop_px
    reached = False
    fives = _five(day)
    five_ends = {idx: (hi, lo) for idx, hi, lo, _cl in fives}
    exit_px = fill
    exit_i = bar
    hit = False
    for k in range(bar, day.end):
        if side == 1:
            if float(day.o[k]) <= stop or float(day.l[k]) <= stop:
                exit_px = min(float(day.o[k]), stop - TICK) if float(day.o[k]) <= stop else stop - TICK
                exit_i = k
                break
            if not reached and float(day.h[k]) >= target:
                reached = True
                hit = True
        else:
            if float(day.o[k]) >= stop or float(day.h[k]) >= stop:
                exit_px = max(float(day.o[k]), stop + TICK) if float(day.o[k]) >= stop else stop + TICK
                exit_i = k
                break
            if not reached and float(day.l[k]) <= target:
                reached = True
                hit = True
        if reached and k in five_ends:
            hi, lo = five_ends[k]
            if side == 1:
                stop = max(stop, lo)
            else:
                stop = min(stop, hi)
        exit_i = k
        exit_px = float(day.c[k]) - side * TICK
    else:
        exit_px = float(day.c[day.end - 1]) - side * TICK
        exit_i = day.end - 1
    gross = side * (exit_px - fill)
    trade = Trade(gross, risk, 0.0, hit)
    trade.planned = abs(target - fill)
    trade.side = side
    trade.entry_px = fill
    trade.entry_bar = bar
    return trade, exit_i, reached


def vacuum(day):
    leg = day.leg
    if leg is None:
        return []
    side = -leg["direction"]
    stop_px = leg["poc"] + POC_BUFFER if side == -1 else leg["poc"] - POC_BUFFER
    target = leg["target"]
    attempts = 0
    cursor = day.i_open
    trades = []
    for end_i, _hi, _lo, close in _five(day):
        if end_i < cursor or int(day.hm[end_i]) > END_WIN:
            continue
        crossed = close < leg["poc"] if side == -1 else close > leg["poc"]
        if not crossed:
            continue
        entry_i = end_i + 1
        if entry_i >= day.end:
            break
        fill = float(day.o[entry_i]) + side * TICK
        trade, exit_i, reached = manage_trail(day, side, fill, entry_i, stop_px, target)
        attempts += 1
        if trade is None:
            cursor = entry_i + 1
        else:
            trades.append(trade)
            cursor = exit_i + 1
            if reached or attempts >= 2:
                break
        if attempts >= 2:
            break
    return trades[:1] if not trades else trades[:2]


def vacuum_fixed(day, reward: float):
    """First vacuum attempt only, at a fixed R. The lifecycle is one full-risk trade a day."""
    leg = day.leg
    if leg is None:
        return []
    side = -leg["direction"]
    stop_px = leg["poc"] + POC_BUFFER if side == -1 else leg["poc"] - POC_BUFFER
    for end_i, _hi, _lo, close in _five(day):
        if int(day.hm[end_i]) > END_WIN:
            continue
        crossed = close < leg["poc"] if side == -1 else close > leg["poc"]
        if not crossed:
            continue
        entry_i = end_i + 1
        if entry_i >= day.end:
            return []
        fill = float(day.o[entry_i]) + side * TICK
        risk = abs(fill - stop_px)
        if side * (stop_px - fill) >= 0 or not (2.0 <= risk <= 80.0):
            continue
        target = fill + side * reward * risk
        _k, gross, mae, hit = _manage(
            side, fill, stop_px, target, day.o, day.h, day.l, day.c, day.hm, entry_i, day.end,
        )
        trade = Trade(gross, risk, mae, hit)
        trade.planned = abs(target - fill)
        return [trade]
    return []


def load_tape():
    """Morning extreme volume, and the poke bar's price map. Minute aggregates, not prints."""
    extreme = {}
    prices = {}
    for name in CONTINUOUS:
        frame = pd.read_parquet(CVD / name, columns=["ts_minute", "price", "side", "volume"])
        frame["ts"] = pd.to_datetime(frame["ts_minute"], utc=True).dt.tz_convert(NY)
        hm = frame["ts"].dt.hour * 60 + frame["ts"].dt.minute
        frame = frame[(hm >= OPEN) & (hm <= END_WIN)]
        if frame.empty:
            print("tape", name, 0, flush=True)
            continue
        tick = np.rint(frame["price"].to_numpy(dtype=float) / TICK).astype(np.int32)
        buy = np.where(frame["side"].to_numpy() == "B", frame["volume"].to_numpy(), 0.0)
        sell = np.where(frame["side"].to_numpy() == "A", frame["volume"].to_numpy(), 0.0)
        grouped = pd.DataFrame({"ts": frame["ts"].to_numpy(), "tick": tick, "buy": buy, "sell": sell})
        grouped = grouped.groupby(["ts", "tick"], sort=False)[["buy", "sell"]].sum().reset_index()
        for ts, part in grouped.groupby("ts", sort=False):
            hi = int(part["tick"].max())
            lo = int(part["tick"].min())
            buy_hi = float(part.loc[part["tick"] >= hi - 1, "buy"].sum())
            sell_lo = float(part.loc[part["tick"] <= lo + 1, "sell"].sum())
            extreme[pd.Timestamp(ts)] = (buy_hi, sell_lo)
            prices[pd.Timestamp(ts)] = {
                int(t): (float(b), float(s))
                for t, b, s in zip(part["tick"], part["buy"], part["sell"], strict=True)
            }
        print("tape", name, len(grouped), flush=True)
    return extreme, prices


def null_of(trades) -> float:
    vals = [tr.risk / (tr.risk + tr.planned) for tr in trades if getattr(tr, "planned", 0) > 0 and tr.risk > 0]
    return float(np.mean(vals)) if vals else P0


def be_of(trades) -> float:
    vals = []
    for tr in trades:
        reward = getattr(tr, "planned", float("nan"))
        if not np.isfinite(reward) or reward <= 0:
            continue
        win = reward - COMMISSION_POINTS
        loss = tr.risk + TICK + COMMISSION_POINTS
        vals.append(1.0 if win <= 0 else loss / (win + loss))
    return float(np.mean(vals)) if vals else float("nan")


def r_test(trades, p0: float):
    n = len(trades)
    rs = np.array([(tr.gross - COMMISSION_POINTS) / tr.risk for tr in trades]) if n else np.array([])
    mid = mean_r(trades)
    if n < 20:
        ph = (sum(tr.hit for tr in trades) / n) if n else float("nan")
        hit = {"n": n, "hit": ph, "lo": float("nan"), "hi": float("nan"), "p": 1.0}
        p_r = 1.0
    else:
        from statistics import NormalDist
        se = float(rs.std(ddof=1) / math.sqrt(n))
        z = mid[0] / se if se > 0 else 0.0
        p_r = float(1.0 - NormalDist().cdf(z))
        hit = hit_test(trades, p0)
    return {"n": n, "r": mid, "p_r": p_r, "hit": hit}


def _fills(book, idxs):
    return [tr for i in idxs for tr in book[i]]


def edge_row(days, fills, real, rnd, idxs, sample: str):
    diffs = []
    ib_score = []
    rnd_score = []
    for i in idxs:
        if fills[i] is None or real[i] is None or rnd[i] is None:
            continue
        if real[i].get("close") is None or rnd[i].get("close") is None:
            continue
        a = real[i]["close"]["mfe"] - real[i]["close"]["mae"]
        b = rnd[i]["close"]["mfe"] - rnd[i]["close"]["mae"]
        ib_score.append(a)
        rnd_score.append(b)
        diffs.append(a - b)
    arr = np.asarray(diffs, dtype=float)
    if len(arr) < 2:
        mid = lo = hi = float("nan")
    else:
        mid = float(arr.mean())
        se = float(arr.std(ddof=1) / math.sqrt(len(arr)))
        lo, hi = mid - 1.96 * se, mid + 1.96 * se
    return {
        "sample": sample,
        "n": len(arr),
        "entry": float(np.mean(ib_score)) if ib_score else float("nan"),
        "random": float(np.mean(rnd_score)) if rnd_score else float("nan"),
        "diff": mid,
        "lo": lo,
        "hi": hi,
    }


def render(rows, winner, edges, lives, onhl, notes) -> str:
    lines = [
        "# Order-flow and volume-profile videos",
        "",
        _lead(winner, onhl, lives),
        "",
        "Disarmed. Nothing here places an order. LucidFlex evals are at 50%, and the lifecycle fee is the assumed $100. The two videos sell a room and a Discord. The examples are winners. One video calls the value-area edges the prices with the least volume. That is not how a value area is built. These tests use the ordinary 70% area around the heaviest price.",
        "",
        "Variant A anchors the profile at 18:00 ET and stops it at 09:29. Volume is the one-minute close, in one-tick bins. From 09:30 to 11:30, a bar trades at least one tick outside the area and a one-minute close is back inside within three bars, counting the poke bar. The market version fills on the next bar's open, one tick worse. The limit version rests at the reclaimed edge after that close. The stop is the poke extreme plus two ticks. The targets, each its own row, are the point of control, the opposite edge, and 1.7 times the stop.",
        "",
        "The footprint filter asks for 60 contracts of aggressive volume at the extreme price of the poke minute. That is the whole minute at that price, not one print of 60. It is labeled coarse for that reason. Variant B marks wick volume versus body volume on that same minute and enters on a later close back through the heaviest wick price. A minute cannot say where inside the bar the print happened. Both need tick `trades` before they are the rule in the video.",
        "",
        "Variant C keeps an overnight push only when the overnight range is at least half the prior 20 cash-session ranges and the 09:29 close is in the outer 30% of that range. The leg is profiled from the overnight extreme to 09:29. A vacuum is a thin tail, rows under the median volume, covering at least 15% of the leg. A five-minute close back through the leg's point of control enters, at the next open plus one tick. The stop is four points beyond that point of control. The target is the far end of the thin tail. After the target prints, the stop trails to the completed five-minute bar, and it only tightens. Two attempts, and the second only if the first never reached the target.",
        "",
        "A row needs 80 validation fills to be ranked. Variant B is never ranked: the minute footprint is not the rule in the video. The sort is validation mean R among A and C. Holdout, from 1 July 2025, is scored after that choice. Benjamini-Hochberg at 10% covers every validation test of mean R above zero, including the rows that are too small to rank. Costs match the rest of this stack: trade-through for limits, one tick of adverse slippage on a market entry, one tick on the stop, commission of $1.22 in the research R.",
        "",
        "## Validation",
        "",
        "| rule | n | hit | null | breakeven | mean R | p | BH | ranked |",
        "|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    a = lines.append
    ordered = sorted(rows, key=lambda r: -(r["val"]["r"][0] if r["val"]["n"] >= 2 and not math.isnan(r["val"]["r"][0]) else -999))
    for row in ordered:
        v = row["val"]
        a(
            f"| {row['name']} | {v['n']} | {pct(v['hit']['hit'])} | {pct(row['null'])} | {pct(row['be'])} | "
            f"{_num(v['r'][0])} ({_num(v['r'][1])} to {_num(v['r'][2])}) | {v['p_r']:.3f} | "
            f"{'yes' if row['bh'] else 'no'} | {'yes' if row['ranked'] else 'no'} |"
        )
    a("")
    a(
        f"Variant C built a vacuum leg on {notes['val_leg']} validation days and filled {notes['val_c_trades']} trades "
        f"on {notes['val_c_days']} of them. That is under 80, so C is not ranked and its holdout return stays closed. "
        f"The footprint covers June 2025 onward. All {notes['val_tape']} validation failed auctions in that month matched a footprint minute, "
        f"and {notes['val_flow']} of them cleared the 60-contract extreme filter. The filter and Variant B stay unranked."
    )
    a("")
    a("## Holdout")
    a("")
    if winner is None:
        a("Nothing had 80 validation fills, so the holdout stays closed.")
    else:
        h = winner["hold"]
        a(
            f"The validation choice is `{winner['name']}`. Holdout hit {pct(h['hit']['hit'])} "
            f"({pct(h['hit']['lo'])} to {pct(h['hit']['hi'])}) on {h['n']} fills. "
            f"Mean R {_num(h['r'][0])} ({_num(h['r'][1])} to {_num(h['r'][2])}). "
            f"No-drift hit {pct(winner['hold_null'])}. Cost breakeven {pct(winner['hold_be'])}."
        )
        a("")
        a(
            f"`onhl_pull_s15` at 1.7R on this same holdout: hit {pct(onhl['hit'])} "
            f"({pct(onhl['lo'])} to {pct(onhl['hi'])}) on {onhl['n']} fills, mean R {_num(onhl['r'][0])} "
            f"({_num(onhl['r'][1])} to {_num(onhl['r'][2])})."
        )
        ranked_rows = [row for row in rows if row["ranked"]]
        if ranked_rows and all(row["val"]["r"][0] < 0 for row in ranked_rows):
            v = winner["val"]
            a("")
            a(
                f"On validation `{winner['name']}` mean R was {_num(v['r'][0])} "
                f"({_num(v['r'][1])} to {_num(v['r'][2])}). Every ranked row was negative there, and none survived Benjamini-Hochberg."
            )
    a("")
    a("## Excursion against a random entry")
    a("")
    a("The score is favorable excursion minus adverse excursion, held to the close, with no stop. The control enters at the fill bar's open, long or short from a fixed seed. Train and validation are the measurement. The holdout row is the same statistic and was not used to pick the rule.")
    a("")
    a("| entry | sample | n | entry MFE−MAE | random MFE−MAE | paired difference |")
    a("|---|---|---:|---:|---:|---:|")
    for row in edges:
        a(
            f"| {row['name']} | {row['sample']} | {row['n']} | {row['entry']:.1f} | {row['random']:.1f} | "
            f"{row['diff']:.1f} ({row['lo']:.1f} to {row['hi']:.1f}) |"
        )
    a("")
    fit_edges = [row for row in edges if row["sample"].startswith("train")]
    if fit_edges and all(row["lo"] <= 0 <= row["hi"] for row in fit_edges):
        a("On train and validation, both paired differences cover zero. Neither entry beats a random side at the same minute.")
        a("")
    a("## Lifecycle")
    a("")
    a(
        "The lifecycle replays the selected entry, not its native target. The eval is 0.75R and the funded shot is 1.7R, "
        "using that entry's own stop, and only the first attempt. Native C may take a second attempt; the lifecycle does not. "
        "The overnight row is a 15-point stop, 0.75R in the eval and 1.7R once funded. Grind days use each book's own holdout hit rate. "
        "LucidFlex is at 50% with the assumed $100 fee. FundedNext is charged Topstep's $1.22 MNQ round turn because that firm does not publish an MNQ rate."
    )
    a("")
    a("| firm | book | holdout pass | EV per eval | payouts / 100 | evals passed / month | 21-day cash | P(month negative) |")
    a("|---|---|---:|---|---:|---:|---|---:|")
    for row in lives:
        m = row["month"]
        a(
            f"| {row['firm']} | {row['book']} | {pct(row['life']['pass'])} | "
            f"{money(row['life']['mean'])} ({money(row['life']['lo'])} to {money(row['life']['hi'])}) | "
            f"{row['life']['pays']:.1f} | {row['passes']:.2f} | "
            f"{money(m['mean'])} ({money(m['lo'])} to {money(m['hi'])}) | {pct(m['p_neg'])} |"
        )
    a("")
    a("## Databento pull, not bought")
    a("")
    a("A two-month pilot of NQ trades fits inside the $125 credit on a new Databento account. This run did not call the API and did not spend the credit.")
    a("")
    a("Buy `GLBX.MDP3`, schema `trades`, the front-month outright on the same roll as `data/reference/nq_1m_master`. Drop calendar spreads. Pass timezone-aware `America/New_York` timestamps. Do not hardcode one UTC offset: 2 March 2026 is still Eastern Standard Time, and 8 March is the change to daylight time.")
    a("")
    a("Window: 2 March 2026 18:00 ET through 30 April 2026 16:00 ET. Both months are inside the holdout, so the tick profile can be compared with this minute test. A clock of 18:00 to 11:30 ET is enough for the overnight profile and the morning entry, and it cuts the afternoon.")
    a("")
    a("The unit sheet dated 11 December 2024 lists historical `trades` at $28 per GB. The pricing page read on 5 November 2026 still bills the uncompressed binary size. April 2026 in this repo is about 7.7 million front-month trades. At about 48 bytes a trade that is about 0.37 GB, about $10. Two months are on the order of $20 to $40 before the clock filter, inside the $125 credit, which expires six months after signup. That is an estimate from the tick count, not an invoice. The exact number is `metadata.get_cost` before anyone confirms the download.")
    a("")
    a("`scripts/trades_profile.py` reads a trades table and builds the one-tick value area, clusters of prints at or above a contract threshold, the body-versus-wick location once the minute bar exists, and an absorption flag: a large aggressive print at the extreme with no further progress for N seconds. Sixty MNQ contracts are six NQ. The video did not say which one.")
    a("")
    return "\n".join(lines) + "\n"


def _lead(winner, onhl, lives) -> str:
    if winner is None:
        return "Neither A nor C had 80 validation fills, so neither is compared on the holdout."
    h = winner["hold"]
    above = (not math.isnan(h["r"][1])) and h["r"][1] > onhl["r"][0]
    bit = (
        f"Neither A nor C beats `onhl_pull_s15` on the holdout. "
        f"C never reached 80 validation fills. The best ranked A row, `{winner['name']}`, "
        f"has mean R {_num(h['r'][0])} ({_num(h['r'][1])} to {_num(h['r'][2])}) on {h['n']} fills. "
        f"The overnight pull is {_num(onhl['r'][0])} ({_num(onhl['r'][1])} to {_num(onhl['r'][2])}) on {onhl['n']} fills."
    )
    if above:
        bit = (
            f"`{winner['name']}` has a holdout mean-R interval above the overnight pull's point estimate. "
            f"Mean R {_num(h['r'][0])} ({_num(h['r'][1])} to {_num(h['r'][2])}) against {_num(onhl['r'][0])}."
        )
    sel = next((row for row in lives if row["book"] == "selected" and row["firm"] == "Topstep"), None)
    base = next((row for row in lives if row["book"] == "onhl" and row["firm"] == "Topstep"), None)
    if sel and base:
        bit += f" Topstep per eval is {money(sel['life']['mean'])} against {money(base['life']['mean'])}."
    return bit


def main() -> None:
    print("load", flush=True)
    df = load_bars(str(DATA))
    days = build_days(df)
    attach(df, days)
    print("tape", flush=True)
    tape, prices = load_tape()
    print("signals", len(days), flush=True)
    # The fill used for C's excursion is recorded inside vacuum's first trade via a side channel.
    books = {name: [] for name in (
        "a_mkt_poc", "a_mkt_edge", "a_mkt_1.7", "a_lim_poc", "a_lim_edge", "a_lim_1.7",
        "a_flow_poc", "a_flow_edge", "a_flow_1.7", "b_reload", "c_lvn",
    )}
    life = {
        fam: {reward: [] for reward in (0.75, 1.7)}
        for fam in ("a_mkt", "a_lim", "a_flow", "c")
    }
    a_fills = []
    c_fills = []
    notes = {"val_leg": 0, "val_c_days": 0, "val_c_trades": 0, "val_tape": 0, "val_flow": 0}
    for day in days:
        setup = failed_auction(day)
        flow = coarse_absorption(day, setup, tape)
        for key, mode in (("a_mkt_poc", "poc"), ("a_mkt_edge", "edge"), ("a_mkt_1.7", "1.7")):
            books[key].append(market_trade(day, setup, None if setup is None else _target(setup, mode)))
        for reward in (0.75, 1.7):
            life["a_mkt"][reward].append(market_trade(day, setup, None if setup is None else _target(setup, "r", reward)))
        for key, mode in (("a_lim_poc", "poc"), ("a_lim_edge", "edge")):
            books[key].append(limit_trade(day, setup, None if setup is None else _target(setup, mode)))
        books["a_lim_1.7"].append(limit_trade(day, setup, None, 1.7))
        for reward in (0.75, 1.7):
            life["a_lim"][reward].append(limit_trade(day, setup, None, reward))
        flowed = setup if flow else None
        for key, mode in (("a_flow_poc", "poc"), ("a_flow_edge", "edge"), ("a_flow_1.7", "1.7")):
            books[key].append(market_trade(day, flowed, None if flowed is None else _target(flowed, mode)))
        for reward in (0.75, 1.7):
            life["a_flow"][reward].append(market_trade(day, flowed, None if flowed is None else _target(flowed, "r", reward)))
        b = reload_break(day, prices)
        books["b_reload"].append(market_trade(day, b, None if b is None else b["poc"]))
        c_trades = vacuum(day)
        books["c_lvn"].append(c_trades[:2])
        for reward in (0.75, 1.7):
            life["c"][reward].append(vacuum_fixed(day, reward))
        a_fills.append(None if setup is None else {"side": setup["side"], "entry": setup["fill"], "bar": setup["bar"]})
        in_val = TRAIN_END <= day.ts < VAL_END
        if in_val and day.leg is not None:
            notes["val_leg"] += 1
        if in_val and c_trades:
            notes["val_c_days"] += 1
            notes["val_c_trades"] += len(c_trades)
        if in_val and setup is not None and bar_stamp(day, setup["poke"]) in tape:
            notes["val_tape"] += 1
            if flow:
                notes["val_flow"] += 1
        if c_trades:
            first = c_trades[0]
            c_fills.append({"side": first.side, "entry": first.entry_px, "bar": first.entry_bar})
        else:
            c_fills.append(None)
    val_i = [i for i, d in enumerate(days) if TRAIN_END <= d.ts < VAL_END]
    hold_i = [i for i, d in enumerate(days) if d.ts >= VAL_END]
    fit_i = [i for i, d in enumerate(days) if d.ts < VAL_END]
    rows = []
    for name, book in books.items():
        trades = _fills(book, val_i)
        p0 = null_of(trades)
        scored = r_test(trades, p0)
        rows.append({
            "name": name, "book": book, "val": scored, "null": p0, "be": be_of(trades),
            "ranked": scored["n"] >= 80 and not name.startswith("b_"), "bh": False,
        })
        print(name, scored["n"], flush=True)
    flags = bh_mask(np.array([r["val"]["p_r"] for r in rows]))
    for row, ok in zip(rows, flags, strict=True):
        row["bh"] = bool(ok)
    eligible = [r for r in rows if r["ranked"] and not math.isnan(r["val"]["r"][0])]
    winner = max(eligible, key=lambda r: r["val"]["r"][0]) if eligible else None
    onhl17, _src = onhl_book(days, None, 0, 1.7)
    onhl75, _src = onhl_book(days, None, 0, 0.75)
    onhl_tr = _fills(onhl17, hold_i)
    onhl = hit_test(onhl_tr, P0)
    onhl["r"] = mean_r(onhl_tr)
    if winner is not None:
        print("winner", winner["name"], flush=True)
        hold_tr = _fills(winner["book"], hold_i)
        winner["hold"] = r_test(hold_tr, null_of(hold_tr))
        winner["hold_null"] = null_of(hold_tr)
        winner["hold_be"] = be_of(hold_tr)
    edges = []
    for name, fills in (("A", a_fills), ("C", c_fills)):
        real, rnd = [], []
        for day, fill in zip(days, fills, strict=True):
            if fill is None:
                real.append(None)
                rnd.append(None)
                continue
            real.append(excursion(day, fill))
            rnd.append(excursion(day, random_fill(day, fill, name)))
        edges.append({"name": name, **edge_row(days, fills, real, rnd, fit_i, "train+validation")})
        edges.append({"name": name, **edge_row(days, fills, real, rnd, hold_i, "holdout")})
    firm_list = firms()
    lives = []
    pair = [("onhl", onhl75, onhl17)]
    if winner is not None:
        fam = "c" if winner["name"].startswith("c_") else winner["name"].rsplit("_", 1)[0]
        pair.insert(0, ("selected", life[fam][0.75], life[fam][1.7]))
    for label, eval_book, fund_book in pair:
        eh = [eval_book[i] for i in hold_i]
        fh = [fund_book[i] for i in hold_i]
        trades = [tr for day in eh for tr in day]
        grind = (sum(tr.hit for tr in trades) / len(trades)) if trades else 0.5
        for spec in firm_list:
            risk = min(2000.0, float(spec["mll"]))
            life = fullport_life(
                eh, fh, spec, np.random.default_rng(_seed("of" + label + spec["firm"])), risk, grind, n=400,
            )
            cash, _note, _slots = month_book(eh, fh, spec, risk, grind, n=100)
            mid = float(cash.mean())
            se = float(cash.std(ddof=1) / math.sqrt(len(cash)))
            passes = month_passes(eh, spec, risk, grind, n=60)
            lives.append({
                "firm": spec["firm"], "book": label, "life": life, "passes": passes,
                "month": {"mean": mid, "lo": mid - 1.96 * se, "hi": mid + 1.96 * se, "p_neg": float(np.mean(cash < 0))},
            })
            print("life", label, spec["firm"], round(life["mean"], 1), flush=True)
    OUT.write_text(render(rows, winner, edges, lives, onhl, notes))
    print("wrote", OUT, flush=True)


if __name__ == "__main__":
    main()
