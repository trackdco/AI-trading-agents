"""Jake Ryan's YouTube rules, pre-registered as V1-V4. Nothing here places an order.

The absorption flag is the minute-bar proxy in the spec. It is not his sub-minute
bubble. Thresholds that the transcripts never numbered are frozen below.
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

from scripts.run_fullport import (
    P0,
    _seed,
    bh_mask,
    fullport_life,
    hit_test,
    mean_r,
)
from scripts.run_hf_limit import build_days
from scripts.run_limit_research import (
    TRAIN_END,
    VAL_END,
    _num,
    firms,
    money,
    pct,
)
from src.research.strategies.costs import COMMISSION_POINTS, FLAT_MINUTE, TICK
from src.research.strategies.engine import load_bars
from src.research.strategies.hf_limit import Trade, _manage, scan_limits
from src.research.strategies.jake_rules import VALUE_FRAC, _week_sunday, value_area

OUT = ROOT / "docs" / "JAKERYAN-METHOD-TEST.md"
DATA = ROOT / "data" / "reference" / "nq_1m_master.parquet"
CVD = ROOT / "data" / "reference" / "cvd"
NY = "America/New_York"
OPEN = 9 * 60 + 30
END_WIN = 11 * 60 + 30
LTF_START = 6 * 60 + 30
# The spec writes "delta >= +X" and never gives X. Frozen as strictly positive.
X_DELTA = 0.0
POKE_MAX = 25.0
STOP_PAD = 2.0
STOP_CAP = 20.0
ALIGN_PTS = 10.0
CONF_PTS = 5.0
V2_STOP = 10.0
V3_STOP = 12.0
V4_STOP_PAD = 10.0
HOUSE_MAX_STOP = 80.0
WARMUP = 20
COUNTS: dict[str, int] = {}


def bump(key: str) -> None:
    COUNTS[key] = COUNTS.get(key, 0) + 1

CONTINUOUS = (
    "footprint_q3_2025.parquet",
    "footprint_q4_2025.parquet",
    "footprint_jan2026.parquet",
    "footprint_feb_mar2026.parquet",
    "footprint_apr2026.parquet",
    "footprint_may_jul2026.parquet",
)


def tick_area(ticks: np.ndarray, vols: np.ndarray):
    """70% value area on 1-tick bins. Empty ticks carry no volume."""
    if len(ticks) == 0 or float(np.sum(vols)) <= 0:
        return None
    area = value_area(ticks.astype(np.int64), vols.astype(float), VALUE_FRAC)
    if area is None:
        return None
    val, vah, poc = (float(x) * TICK for x in area)
    if vah <= val:
        return None
    return val, vah, poc


def short_absorption(o, h, l, c, ask, bid, i: int, level: float, p80: float) -> bool:
    """Heavy ask volume, no reward, tagged within 2 points of the level."""
    if i < 0 or not np.isfinite(p80) or not np.isfinite(ask[i]) or not np.isfinite(bid[i]):
        return False
    rng = float(h[i] - l[i])
    if rng <= 0:
        return False
    delta = float(ask[i] - bid[i])
    close_pos = (float(c[i]) - float(l[i])) / rng
    return (
        float(h[i]) >= level - 2.0
        and float(ask[i]) >= p80
        and delta > X_DELTA
        and float(c[i]) <= float(o[i]) + TICK
        and close_pos <= 0.5
    )


def long_absorption(o, h, l, c, ask, bid, i: int, level: float, p80: float) -> bool:
    if i < 0 or not np.isfinite(p80) or not np.isfinite(ask[i]) or not np.isfinite(bid[i]):
        return False
    rng = float(h[i] - l[i])
    if rng <= 0:
        return False
    delta = float(ask[i] - bid[i])
    close_pos = (float(c[i]) - float(l[i])) / rng
    return (
        float(l[i]) <= level + 2.0
        and float(bid[i]) >= p80
        and delta < -X_DELTA
        and float(c[i]) >= float(o[i]) - TICK
        and close_pos >= 0.5
    )


def refreshed(ask, bid, c, extreme: float, j: int, side: int) -> bool:
    """Next bar: delta flips, and the close takes out the absorption extreme."""
    if j < 0 or not np.isfinite(ask[j]) or not np.isfinite(bid[j]):
        return False
    delta = float(ask[j] - bid[j])
    if side == -1:
        return delta < 0 and float(c[j]) < extreme
    return delta > 0 and float(c[j]) > extreme


def in_window(hm: int) -> bool:
    return OPEN <= int(hm) <= END_WIN


def manage(o, h, l, c, hm, side: int, fill: float, stop_px: float, targets: list[tuple[float, float]], entry_i: int, end: int):
    """Stop before targets. `targets` are (fraction, price), nearest first. Remaining size flats at 15:55."""
    remaining = 1.0
    pnl = 0.0
    mae = 0.0
    hit = False
    ordered = sorted(targets, key=lambda item: side * (item[1] - fill))
    for k in range(entry_i, end):
        if hm[k] >= FLAT_MINUTE:
            if k == entry_i:
                return pnl, mae, False
            px = float(c[k - 1]) - side * TICK
            pnl += remaining * side * (px - fill)
            return pnl, mae, hit
        if side == 1:
            mae = max(mae, fill - float(l[k]))
            if float(o[k]) <= stop_px or float(l[k]) <= stop_px:
                exit_px = min(float(o[k]), stop_px - TICK) if float(o[k]) <= stop_px else stop_px - TICK
                pnl += remaining * (exit_px - fill)
                mae = max(mae, fill - exit_px)
                return pnl, mae, hit
            while ordered and float(h[k]) >= ordered[0][1] and remaining > 1e-9:
                frac, px = ordered.pop(0)
                take = min(frac, remaining)
                pnl += take * (px - fill)
                remaining -= take
                hit = True
            if remaining <= 1e-9:
                return pnl, mae, hit
        else:
            mae = max(mae, float(h[k]) - fill)
            if float(o[k]) >= stop_px or float(h[k]) >= stop_px:
                exit_px = max(float(o[k]), stop_px + TICK) if float(o[k]) >= stop_px else stop_px + TICK
                pnl += remaining * (fill - exit_px)
                mae = max(mae, exit_px - fill)
                return pnl, mae, hit
            while ordered and float(l[k]) <= ordered[0][1] and remaining > 1e-9:
                frac, px = ordered.pop(0)
                take = min(frac, remaining)
                pnl += take * (fill - px)
                remaining -= take
                hit = True
            if remaining <= 1e-9:
                return pnl, mae, hit
    last = end - 1
    if last < entry_i:
        return 0.0, mae, False
    px = float(c[last]) - side * TICK
    pnl += remaining * side * (px - fill)
    return pnl, mae, hit


def as_trade(gross: float, risk: float, mae: float, hit: bool) -> Trade:
    return Trade(gross, risk, mae, hit)


def _finite_level(px: float, level: float) -> bool:
    return np.isfinite(px) and np.isfinite(level) and abs(px - level) <= CONF_PTS


def confluent(edge: float, levels: list[float]) -> bool:
    if not np.isfinite(edge):
        return False
    nearest = round(edge / 100.0) * 100.0
    if abs(edge - nearest) <= CONF_PTS:
        return True
    return any(_finite_level(edge, level) for level in levels)


def v4_direction(onh: float, onl: float, close: float, on_range: float, median: float) -> int:
    """1 = overnight rally continuation, -1 = selloff continuation, 0 = no regime."""
    if not (np.isfinite(onh) and np.isfinite(onl) and np.isfinite(close) and np.isfinite(median)):
        return 0
    if on_range <= 1.5 * median or on_range <= 0:
        return 0
    pos = (close - onl) / on_range
    if pos >= 0.80:
        return 1
    if pos <= 0.20:
        return -1
    return 0


def null_hit(risk: float, reward: float) -> float:
    """No-drift chance the target is touched before the stop. Stop fill is one tick worse."""
    if risk <= 0 or reward <= 0:
        return float("nan")
    return risk / (risk + reward)


def r_test(trades: list[Trade], p0: float | None):
    rs = np.array([(tr.gross - COMMISSION_POINTS) / tr.risk for tr in trades]) if trades else np.array([])
    n = len(trades)
    if n < 2:
        mid = (float("nan"), float("nan"), float("nan"))
    elif n < 20:
        mid = (float(rs.mean()), float("nan"), float("nan"))
    else:
        mid = mean_r(trades)
    if n < 20:
        p_r = 1.0
        ph = (sum(tr.hit for tr in trades) / n) if n else float("nan")
        hit = {"n": n, "hit": ph, "lo": float("nan"), "hi": float("nan"), "p": 1.0}
    else:
        se = float(rs.std(ddof=1) / math.sqrt(n))
        z = mid[0] / se if se > 0 else 0.0
        from statistics import NormalDist
        p_r = float(1 - NormalDist().cdf(z))
        hit = hit_test(trades, p0 if p0 is not None and not math.isnan(p0) else 0.5)
    if p0 is None or (isinstance(p0, float) and math.isnan(p0)):
        hit["p"] = float("nan")
    if n == 0:
        dist = (float("nan"),) * 3
    else:
        dist = tuple(float(np.quantile(rs, q)) for q in (0.10, 0.50, 0.90))
    return {"n": n, "r": mid, "p_r": p_r, "hit": hit, "dist": dist, "p0": p0 if p0 is not None else float("nan")}


def _apply_bh(rows):
    usable = [r for r in rows if r["hold"]["n"] >= 20]
    if not usable:
        return
    flags = bh_mask(np.array([r["hold"]["p_r"] for r in usable]))
    for row, ok in zip(usable, flags, strict=True):
        row["bh"] = bool(ok)


def load_footprint():
    """Minute ask/bid volume, and tick-bin volume, from the continuous tape only."""
    minutes = []
    ticks = []
    for name in CONTINUOUS:
        path = CVD / name
        frame = pd.read_parquet(path, columns=["ts_minute", "price", "side", "volume"])
        frame["ts_minute"] = pd.to_datetime(frame["ts_minute"], utc=True).dt.tz_convert(NY)
        ask = np.where(frame["side"].to_numpy() == "B", frame["volume"].to_numpy(), 0)
        bid = np.where(frame["side"].to_numpy() == "A", frame["volume"].to_numpy(), 0)
        tmp = pd.DataFrame({"ts": frame["ts_minute"].to_numpy(), "ask": ask, "bid": bid})
        minutes.append(tmp.groupby("ts", sort=False)[["ask", "bid"]].sum())
        tick = np.rint(frame["price"].to_numpy() / TICK).astype(np.int32)
        vol = pd.DataFrame({"ts": frame["ts_minute"].to_numpy(), "tick": tick, "volume": frame["volume"].to_numpy()})
        ticks.append(vol.groupby(["ts", "tick"], sort=False)["volume"].sum())
        print("foot", name, len(frame), flush=True)
    minute = pd.concat(minutes)
    minute = minute.groupby(level=0).sum()
    tick = pd.concat(ticks)
    tick = tick.groupby(level=[0, 1]).sum()
    return minute, tick


def attach(days, df: pd.DataFrame, minute: pd.DataFrame, tick: pd.Series) -> None:
    """Add footprint arrays and the Sunday-anchored tick profile. Causal at 09:30."""
    ts = df["ts_event"]
    hm = df["hm"].to_numpy()
    sess = df["sess"].to_numpy()
    cuts = np.flatnonzero(np.diff(sess)) + 1
    bounds = np.r_[0, cuts, len(df)]
    by_open = {}
    for a, b in pairwise(bounds):
        hit = np.flatnonzero((hm[a:b] >= OPEN) & (hm[a:b] < 18 * 60))
        if len(hit) == 0:
            continue
        by_open[ts.iloc[a + int(hit[0])]] = (a, b)
    tick_df = tick.reset_index()
    tick_df.columns = ["ts", "tick", "volume"]
    bar_ts = pd.DataFrame({"ts": ts, "hm": hm, "sess": sess})
    merged = tick_df.merge(bar_ts, on="ts", how="inner")
    pre_groups = {}
    ltf_groups = {}
    rth_groups = {}
    for sess_id, part in merged.groupby("sess", sort=False):
        key = int(sess_id)
        pre = part[(part["hm"] < OPEN) | (part["hm"] >= 18 * 60)]
        ltf = part[(part["hm"] >= LTF_START) & (part["hm"] < OPEN)]
        rth = part[(part["hm"] >= OPEN) & (part["hm"] < 16 * 60)]
        pre_groups[key] = pre.groupby("tick")["volume"].sum().to_dict() if len(pre) else {}
        ltf_groups[key] = ltf.groupby("tick")["volume"].sum().to_dict() if len(ltf) else {}
        rth_groups[key] = rth.groupby("tick")["volume"].sum().to_dict() if len(rth) else {}
    minute_ask = minute["ask"]
    minute_bid = minute["bid"]
    hist: dict[int, float] = {}
    week = None
    on_ranges = []
    rth_ranges = []
    ask_hist: dict[int, list[float]] = {}
    bid_hist: dict[int, list[float]] = {}
    delta5_hist: list[float] = []
    for day in days:
        bounds_day = by_open.get(day.ts)
        day.ask = np.full(len(day.o), np.nan)
        day.bid = np.full(len(day.o), np.nan)
        day.covered = False
        day.va = None
        day.ltf = None
        day.p80_ask = {}
        day.p80_bid = {}
        day.delta5 = float("nan")
        day.delta5_p10 = float("nan")
        day.delta5_p90 = float("nan")
        day.regime = 0
        day.close_0929 = float("nan")
        day.atr20 = float(np.mean(rth_ranges[-WARMUP:])) if len(rth_ranges) >= WARMUP else float("nan")
        day.on_med = float(np.median(on_ranges[-WARMUP:])) if len(on_ranges) >= WARMUP else float("nan")
        if bounds_day is None:
            continue
        a, b = bounds_day
        stamps = ts.iloc[a:b]
        ask = minute_ask.reindex(stamps).to_numpy(dtype=float)
        bid = minute_bid.reindex(stamps).to_numpy(dtype=float)
        day.ask = ask
        day.bid = bid
        window = (day.hm >= OPEN) & (day.hm <= END_WIN)
        present = np.isfinite(ask) & window
        day.covered = int(present.sum()) >= 100 and int(window.sum()) >= 100
        pre_m = (day.hm < OPEN) | (day.hm >= 18 * 60)
        last_pre = np.flatnonzero(pre_m)
        if len(last_pre):
            day.close_0929 = float(day.c[int(last_pre[-1])])
        on_range = day.onh - day.onl if np.isfinite(day.onh) and np.isfinite(day.onl) else float("nan")
        day.regime = v4_direction(day.onh, day.onl, day.close_0929, on_range, day.on_med)
        # thresholds from prior covered sessions only, frozen before this session is appended
        if day.covered:
            for minute_of in range(OPEN, END_WIN + 1):
                past_a = ask_hist.get(minute_of, [])
                past_b = bid_hist.get(minute_of, [])
                if len(past_a) >= WARMUP:
                    day.p80_ask[minute_of] = float(np.quantile(past_a[-WARMUP:], 0.80))
                if len(past_b) >= WARMUP:
                    day.p80_bid[minute_of] = float(np.quantile(past_b[-WARMUP:], 0.80))
            slots = np.flatnonzero((day.hm >= OPEN - 5) & (day.hm < OPEN))
            if len(slots) >= 5 and np.isfinite(ask[slots]).all():
                day.delta5 = float(np.sum(ask[slots] - bid[slots]))
            if len(delta5_hist) >= WARMUP:
                day.delta5_p10 = float(np.quantile(delta5_hist[-WARMUP:], 0.10))
                day.delta5_p90 = float(np.quantile(delta5_hist[-WARMUP:], 0.90))
        sess_id = int(sess[a])
        sunday = _week_sunday(pd.DatetimeIndex([day.ts.normalize()]))[0]
        if week is None or sunday != week:
            hist = {}
            week = sunday
        pre = pre_groups.get(sess_id, {})
        for px, vol in pre.items():
            hist[px] = hist.get(px, 0.0) + float(vol)
        if hist:
            ticks = np.fromiter(hist.keys(), dtype=np.int64)
            vols = np.fromiter(hist.values(), dtype=float)
            day.va = tick_area(ticks, vols)
        ltf = ltf_groups.get(sess_id, {})
        if ltf:
            ticks = np.fromiter(ltf.keys(), dtype=np.int64)
            vols = np.fromiter(ltf.values(), dtype=float)
            day.ltf = tick_area(ticks, vols)
        for px, vol in rth_groups.get(sess_id, {}).items():
            hist[px] = hist.get(px, 0.0) + float(vol)
        if day.covered:
            for minute_of in range(OPEN, END_WIN + 1):
                hit = np.flatnonzero(day.hm == minute_of)
                if len(hit) == 0 or not np.isfinite(ask[int(hit[0])]):
                    continue
                k = int(hit[0])
                ask_hist.setdefault(minute_of, []).append(float(ask[k]))
                bid_hist.setdefault(minute_of, []).append(float(bid[k]))
            if np.isfinite(day.delta5):
                delta5_hist.append(day.delta5)
        if np.isfinite(on_range):
            on_ranges.append(float(on_range))
        rth = (day.hm >= OPEN) & (day.hm < 16 * 60)
        if int(rth.sum()) >= 30:
            rth_ranges.append(float(day.h[rth].max() - day.l[rth].min()))


def _entry_index(day, refresh_i: int) -> int:
    entry = refresh_i + 1
    if entry >= day.end or entry >= len(day.hm):
        return -1
    if not in_window(day.hm[entry]) or day.hm[entry] >= 18 * 60:
        return -1
    return entry


def _market_fill(day, side: int, entry_i: int, stop_px: float, cap: float | None):
    fill = float(day.o[entry_i]) + side * TICK
    risk = abs(fill - stop_px)
    if side * (stop_px - fill) >= 0:
        return None
    if risk < 2.0 or risk > HOUSE_MAX_STOP:
        return None
    if cap is not None and risk > cap + 1e-9:
        return None
    return fill, risk


def _signal(day, side: int, absorb_i: int, level: float, pad: float, cap: float | None, poke: float | None, fixed: float | None):
    """Return ('skip', None) when the refresh is real but the stop is too wide, else ('out', None) or ('trade', setup)."""
    if side == -1:
        if poke is not None and float(day.h[absorb_i]) > level + poke:
            return "out", None
        extreme = float(day.h[absorb_i])
        stop_px = extreme + pad
    else:
        if poke is not None and float(day.l[absorb_i]) < level - poke:
            return "out", None
        extreme = float(day.l[absorb_i])
        stop_px = extreme - pad
    refresh_i = absorb_i + 1
    if refresh_i >= len(day.hm) or not in_window(day.hm[refresh_i]):
        return "out", None
    if not refreshed(day.ask, day.bid, day.c, extreme, refresh_i, side):
        return "out", None
    entry_i = _entry_index(day, refresh_i)
    if entry_i < 0:
        return "out", None
    if fixed is not None:
        stop_px = float(day.o[entry_i]) + side * TICK - side * fixed
    filled = _market_fill(day, side, entry_i, stop_px, cap if fixed is None else fixed)
    if filled is None:
        return "skip", None
    fill, risk = filled
    if fixed is not None:
        risk = fixed
        stop_px = fill - side * fixed
    return "trade", {"side": side, "fill": fill, "stop": stop_px, "risk": risk, "entry": entry_i, "absorb": absorb_i}


def first_fade(day, level_short: float, level_long: float, pad: float, cap: float | None, poke: float | None, attempts: int = 2, fixed: float | None = None, tag: str | None = None):
    """First refreshed flag whose stop fits. A too-wide stop uses an attempt. A failed refresh does not."""
    seen = 0
    i = day.i_open
    while i < day.end - 2 and seen < attempts:
        if not in_window(day.hm[i]):
            if day.hm[i] > END_WIN and day.hm[i] < 18 * 60:
                break
            i += 1
            continue
        minute = int(day.hm[i])
        short_on = np.isfinite(level_short) and short_absorption(
            day.o, day.h, day.l, day.c, day.ask, day.bid, i, level_short, day.p80_ask.get(minute, float("nan")),
        )
        long_on = np.isfinite(level_long) and long_absorption(
            day.o, day.h, day.l, day.c, day.ask, day.bid, i, level_long, day.p80_bid.get(minute, float("nan")),
        )
        if short_on and long_on:
            i += 1
            continue
        if not short_on and not long_on:
            i += 1
            continue
        if tag and day.ts >= VAL_END:
            bump(tag + "_flag")
        side = -1 if short_on else 1
        level = level_short if short_on else level_long
        status, setup = _signal(day, side, i, level, pad, cap, poke, fixed)
        if status == "trade":
            return setup
        if status == "skip":
            seen += 1
            if tag and day.ts >= VAL_END:
                bump(tag + "_skip")
        i += 1
    return None


def trade_from(day, setup, targets: list[tuple[float, float]]) -> list[Trade]:
    if setup is None:
        return []
    good = []
    for frac, px in targets:
        if not np.isfinite(px):
            continue
        room = setup["side"] * (px - setup["fill"])
        if room < 1.0:
            continue
        good.append((frac, px))
    if not good:
        return []
    scale = sum(frac for frac, _px in good)
    good = [(frac / scale, px) for frac, px in good]
    gross, mae, hit = manage(
        day.o, day.h, day.l, day.c, day.hm, setup["side"], setup["fill"], setup["stop"], good, setup["entry"], day.end,
    )
    trade = as_trade(gross, setup["risk"], mae, hit)
    if len(good) == 1:
        trade.planned = abs(good[0][1] - setup["fill"])
    return [trade]


def v1_setup(day, count: bool = False):
    if not day.covered or day.regime != 0 or day.va is None:
        return None
    val, vah, poc = day.va
    found = first_fade(day, vah, val, STOP_PAD, STOP_CAP, POKE_MAX, 2, tag="v1" if count else None)
    if found is None:
        return None
    if found["side"] == -1 and not (found["fill"] > poc):
        return None
    if found["side"] == 1 and not (found["fill"] < poc):
        return None
    edge = val if found["side"] == -1 else vah
    found["poc"] = poc
    found["edge"] = edge
    if count and day.ts >= VAL_END:
        bump("v1_trade")
    return found


def v2_setup(day, count: bool = False):
    if not day.covered or day.regime != 0 or day.ltf is None or not np.isfinite(day.atr20):
        return None
    span = (day.hm >= LTF_START) & (day.hm < OPEN)
    if int(span.sum()) < 60:
        return None
    width = float(day.h[span].max() - day.l[span].min())
    if width >= day.atr20 * 0.4:
        return None
    val, vah, _poc = day.ltf
    found = first_fade(day, vah, val, 0.0, None, None, 2, fixed=V2_STOP, tag="v2" if count else None)
    if found is None:
        return None
    ltf_edge = val if found["side"] == -1 else vah
    target = ltf_edge
    if day.va is not None:
        htf_edge = day.va[0] if found["side"] == -1 else day.va[1]
        if np.isfinite(htf_edge) and abs(htf_edge - ltf_edge) <= ALIGN_PTS:
            target = htf_edge
    found["target"] = target
    if count and day.ts >= VAL_END:
        bump("v2_trade")
    return found


def v3_orders(day, cancel: bool):
    if not day.covered or day.regime != 0 or day.va is None:
        return []
    val, vah, poc = day.va
    lon = (day.hm >= 3 * 60) & (day.hm < 8 * 60 + 30)
    levels = [day.onh, day.onl]
    if int(lon.sum()) >= 20:
        levels.extend([float(day.h[lon].max()), float(day.l[lon].min())])
    end = day.end
    after = np.flatnonzero((day.hm > END_WIN) & (day.hm < 18 * 60) & (np.arange(len(day.hm)) >= day.i_open))
    if len(after):
        end = min(end, int(after[0]))
    if end <= day.i_open:
        return []
    n = len(day.o)
    buy = np.full(n, np.nan)
    sell = np.full(n, np.nan)
    if confluent(val, levels):
        blocked = cancel and np.isfinite(day.delta5) and np.isfinite(day.delta5_p10) and day.delta5 <= day.delta5_p10
        if cancel and not (np.isfinite(day.delta5) and np.isfinite(day.delta5_p10)):
            blocked = True
        if not blocked:
            buy[day.i_open:end] = val
    if confluent(vah, levels):
        blocked = cancel and np.isfinite(day.delta5) and np.isfinite(day.delta5_p90) and day.delta5 >= day.delta5_p90
        if cancel and not (np.isfinite(day.delta5) and np.isfinite(day.delta5_p90)):
            blocked = True
        if not blocked:
            sell[day.i_open:end] = vah
    if not np.isfinite(buy[day.i_open:end]).any() and not np.isfinite(sell[day.i_open:end]).any():
        return []
    return buy, sell, end, poc


def v3_native(day, cancel: bool):
    orders = v3_orders(day, cancel)
    if not orders:
        return []
    buy, sell, end, poc = orders
    return _limit_target(day, buy, sell, end, poc)


def v3_fixed(day, cancel: bool, reward: float):
    orders = v3_orders(day, cancel)
    if not orders:
        return []
    buy, sell, end, _poc = orders
    return scan_limits(day.o, day.h, day.l, day.c, day.hm, buy, sell, V3_STOP, reward, day.i_open, end, max_trades=1)


def _limit_target(day, buy, sell, end, target: float):
    """One trade-through limit, target a price, stop 12 points."""
    for i in range(day.i_open, end):
        b, s = buy[i], sell[i]
        b_hit = np.isfinite(b) and float(day.o[i]) > b - TICK and float(day.l[i]) <= b - TICK
        s_hit = np.isfinite(s) and float(day.o[i]) < s + TICK and float(day.h[i]) >= s + TICK
        if b_hit and s_hit:
            return []
        if not b_hit and not s_hit:
            continue
        side = 1 if b_hit else -1
        limit = float(b if side == 1 else s)
        if side * (target - limit) < 1.0:
            return []
        stop_px = limit - side * V3_STOP
        _k, gross, mae, hit = _manage(side, limit, stop_px, target, day.o, day.h, day.l, day.c, day.hm, i, day.end)
        trade = as_trade(gross, V3_STOP, mae, hit)
        trade.planned = abs(target - limit)
        return [trade]
    return []


def v4_setup(day, count: bool = False):
    if not day.covered or day.regime == 0 or not np.isfinite(day.onh) or not np.isfinite(day.onl):
        return None
    if day.regime == -1:
        found = first_fade(day, day.onh, float("nan"), V4_STOP_PAD, None, None, 2, tag="v4" if count else None)
        if found is None:
            return None
        swept = float(day.h[day.i_open:found["absorb"] + 1].max())
        if swept <= day.onh:
            return None
        stop_px = swept + V4_STOP_PAD
        filled = _market_fill(day, -1, found["entry"], stop_px, None)
        if filled is None:
            return None
        found["fill"], found["risk"] = filled
        found["stop"] = stop_px
        found["target"] = day.onl
        if count and day.ts >= VAL_END:
            bump("v4_trade")
        return found
    found = first_fade(day, float("nan"), day.onl, V4_STOP_PAD, None, None, 2, tag="v4" if count else None)
    if found is None:
        return None
    swept = float(day.l[day.i_open:found["absorb"] + 1].min())
    if swept >= day.onl:
        return None
    stop_px = swept - V4_STOP_PAD
    filled = _market_fill(day, 1, found["entry"], stop_px, None)
    if filled is None:
        return None
    found["fill"], found["risk"] = filled
    found["stop"] = stop_px
    found["target"] = day.onh
    if count and day.ts >= VAL_END:
        bump("v4_trade")
    return found


def run_variant(days, name: str):
    book = []
    for day in days:
        if name == "v1_blend":
            setup = v1_setup(day, count=True)
            book.append(trade_from(day, setup, [(0.5, setup["poc"]), (0.5, setup["edge"])]) if setup else [])
        elif name == "v1_3r":
            setup = v1_setup(day)
            book.append(trade_from(day, setup, [(1.0, setup["fill"] + setup["side"] * 3.0 * setup["risk"])]) if setup else [])
        elif name == "v1_5r":
            setup = v1_setup(day)
            book.append(trade_from(day, setup, [(1.0, setup["fill"] + setup["side"] * 5.0 * setup["risk"])]) if setup else [])
        elif name == "v2_edge":
            setup = v2_setup(day, count=True)
            book.append(trade_from(day, setup, [(1.0, setup["target"])]) if setup else [])
        elif name == "v3_poc":
            book.append(v3_native(day, False))
        elif name == "v3_cancel":
            book.append(v3_native(day, True))
        elif name == "v3_3r":
            book.append(v3_fixed(day, False, 3.0))
        elif name == "v3_5r":
            book.append(v3_fixed(day, False, 5.0))
        elif name == "v4_on":
            setup = v4_setup(day, count=True)
            book.append(trade_from(day, setup, [(1.0, setup["target"])]) if setup else [])
        else:
            book.append([])
    return book


VARIANTS = (
    ("v1_blend", "V1", "50/50 at the point of control and the opposite edge"),
    ("v1_3r", "V1", "same entry, target 3R"),
    ("v1_5r", "V1", "same entry, target 5R"),
    ("v2_edge", "V2", "opposite edge of the 06:30-09:29 profile, or the weekly edge when the two are within 10 points"),
    ("v3_poc", "V3", "resting limit, target the point of control"),
    ("v3_cancel", "V3", "same limit, cancelled when the prior five-minute delta is against it at the 90th percentile"),
    ("v3_3r", "V3", "same limit, target 3R"),
    ("v3_5r", "V3", "same limit, target 5R"),
    ("v4_on", "V4", "opposite overnight extreme"),
)


def _fills(book, idxs):
    return [tr for i in idxs for tr in book[i]]


def score_fixed(book, idxs, reward: float | None):
    trades = _fills(book, idxs)
    if reward is not None and trades:
        p0 = float(np.mean([null_hit(tr.risk, reward * tr.risk) for tr in trades]))
    else:
        planned = [null_hit(tr.risk, tr.planned) for tr in trades if np.isfinite(getattr(tr, "planned", np.nan))]
        p0 = float(np.mean(planned)) if planned else float("nan")
    return r_test(trades, p0)


def london_book(days, reward: float):
    out = []
    for day in days:
        lon = (day.hm >= 3 * 60) & (day.hm < 8 * 60 + 30)
        if int(lon.sum()) < 20:
            out.append([])
            continue
        n = len(day.o)
        buy = np.full(n, np.nan)
        sell = np.full(n, np.nan)
        buy[day.i_open:day.end] = float(day.l[lon].min()) - 4.0
        sell[day.i_open:day.end] = float(day.h[lon].max()) + 4.0
        out.append(scan_limits(
            day.o, day.h, day.l, day.c, day.hm, buy, sell, 15.0, reward, day.i_open, day.end, max_trades=1,
        ))
    return out


def _line(name, label, row) -> str:
    h = row["hold"]
    return (
        f"| {name} | {label} | {h['n']} | {pct(h['hit']['hit'])} ({pct(h['hit']['lo'])} to {pct(h['hit']['hi'])}) | "
        f"{_num(h['p0'])} | {_num(h['r'][0])} ({_num(h['r'][1])} to {_num(h['r'][2])}) | "
        f"{_num(h['dist'][0])} / {_num(h['dist'][1])} / {_num(h['dist'][2])} | {h['p_r']:.3f} | "
        f"{'yes' if row.get('bh') else 'no'} |"
    )


def render(rows, base, lives, coverage) -> str:
    lines = [
        "# Jake Ryan method test",
        "",
        _lead(rows, base),
        "",
        "Disarmed. Nothing here places an order. The rules are the four variants in the 5 Nov 2026 YouTube note, and no others. LucidFlex evals are modeled at 50%.",
        "",
        "The footprint in the repo is one row per minute, per price, per aggressor side, from 1 Jun 2025 through 15 Jul 2026. A same-minute 80th percentile needs 20 prior sessions, so June is the warmup and the first scored window is the holdout from 1 Jul 2025. There is no train sample and no real validation month for this flag. The list was frozen before that holdout was read. Benjamini-Hochberg at 10% is applied to the holdout test of mean R above zero, across the nine rows. That correction is on the first look, not on a separate validation pass.",
        "",
        "His trigger is a sub-minute bubble and an offer that refreshes within seconds. This test uses the whole minute. A minute can show heavy buying and a down close even when the buying was rewarded for most of that minute. The flag is the spec's proxy, and it is coarse.",
        "",
        f"Coverage: {coverage}",
        "",
        "## How the four variants were frozen",
        "",
        "Session is 09:30 to 11:30 ET. One filled trade per variant per day. A completed absorption that is then skipped because the stop is wider than 20 points uses up one of two attempts. The weekly value area is 70% of footprint volume on 1-tick bins, from Sunday 18:00 ET through 09:29 ET that morning. Today's cash session is not in it. Empty ticks add no volume.",
        "",
        "The spec says ask volume at or above the 80th percentile of the last 20 days' same minute, and delta at least +X. No transcript gives X, so X is zero: delta has to be strictly positive for a short and strictly negative for a long. A short also needs the close at or below the open plus one tick, and in the lower half of the bar. The next bar needs negative delta and a close below the absorption bar's low. The mirror is the long. The order is a market at the next bar's open, one tick worse. The stop is a market, one tick worse than the stop price, and it is checked before the target. Research R subtracts Topstep's $1.22. A limit does not pay the entry tick. A market does.",
        "",
        "V1 fades the weekly high or low, allows a poke of 25 points, and skips a stop wider than 20 points past the fill. The fade has to point at the point of control. Half the size exits there and half at the other edge. On a large-overnight day, defined under V4, this fade stands down.",
        "",
        "V2 uses the 06:30-09:29 range only when that range is under 0.4 times the prior 20 cash-session ranges. The stop is 10 points from the fill. The target is the other edge of that profile. If the weekly edge in the same direction is within 10 points of it, the target is the weekly edge.",
        "",
        "V3 rests a limit at the weekly high or low only when that price is within 5 points of the overnight high or low, the London high or low (03:00-08:30), or a multiple of 100. The stop is 12 points. The optional filter cancels the long when the 09:25-09:29 delta is at or below the prior 20-day 10th percentile, and cancels the short at the 90th. If those percentiles are not ready, the filtered row does not trade.",
        "",
        "V4 requires the overnight range to be more than 1.5 times the prior 20-day median, and the 09:29 close in the top or bottom 20% of that range. A selloff looks for a sweep of the overnight high and the short flag; a rally looks for a sweep of the overnight low. The stop is 10 points beyond the absorption extreme. The target is the other overnight extreme. V1, V2, and V3 do not fade on these days.",
        "",
        "## Holdout",
        "",
        "Hit rate is the share of trades that reached the target before the stop. For the 50/50 row it is the share that reached the point of control. The null is the no-drift hit rate from that trade's stop and target. The 50/50 row has no single null. Mean R subtracts the commission. The p-value is mean R above zero. The distribution is the 10th, 50th, and 90th percentile of net R.",
        "",
        "| variant | target | n | hit | null hit | mean R | R 10 / 50 / 90 | p | BH |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    a = lines.append
    for row in rows:
        a(_line(row["name"], row["label"], row))
    a("")
    a(_counts_sentence())
    a("")
    a("## Same days, overnight pull and London")
    a("")
    a("`onhl_pull_s15` is a 15-point stop. London high and low are rested 4 points beyond the 03:00-08:30 range, same 15-point stop. Both are scored only on the holdout days where the footprint covers the morning, so the comparison is the same calendar. The full-sample overnight-pull holdout from the earlier note was 48.3% (39.3% to 57.3%) on 118 fills at 1.7R.")
    a("")
    a("| book | n | hit | mean R |")
    a("|---|---:|---:|---:|")
    for row in base:
        a(f"| {row['name']} | {row['n']} | {pct(row['hit'])} ({pct(row['lo'])} to {pct(row['hi'])}) | {_num(row['r'][0])} ({_num(row['r'][1])} to {_num(row['r'][2])}) |")
    a("")
    a("## Lifecycle")
    a("")
    a("Each day is at most one trade, sized to the max loss, up to $2,000. The eval path is the usual one: the account has to clear the target with the firm's consistency rule, so two equal winning days pass LucidFlex and a single day does not. The funded path is one shot of whatever that variant actually pays, then the firm's minimum winning days. The grind uses the share of these holdout trades that finished with a positive gross result. The overnight-pull row is a 0.75R eval and a 1.7R funded shot. The London row is the same shape. A fresh draw of those two is in the table so the dollar comparison uses this sample.")
    a("")
    a("| firm | book | holdout pass | EV per eval | payouts / 100 |")
    a("|---|---|---:|---|---:|")
    for row in lives:
        a(
            f"| {row['firm']} | {row['book']} | {pct(row['life']['pass'])} | "
            f"{money(row['life']['mean'])} ({money(row['life']['lo'])} to {money(row['life']['hi'])}) | {row['life']['pays']:.1f} |"
        )
    a("")
    a("## What a real tick test would take")
    a("")
    a("The minute flag cannot see a single large print or an offer that reappears a few seconds later. Those need Databento `GLBX.MDP3`, symbol the NQ front month on the same roll as the one-minute master.")
    a("")
    a("`trades` is every fill with aggressor side, size, and exchange timestamp. That is the bubble and the true footprint profile. `mbo` is every order add, cancel, and modify. That is the refresh and an iceberg. GEX walls are options data. They are not in CME futures, so Databento will not supply the levels he imports from Discord.")
    a("")
    a("To rerun this holdout on the real trigger, pull both schemas from 1 Jun 2025 through 15 Jul 2026. The extra June is the 20-session warmup. Restricting the clock to 18:00 ET through 11:30 ET covers the weekly profile and the entry window. To choose a variant before reading the holdout, the pull has to start where the one-minute master starts, 2 Jan 2023, and run through 15 Jul 2026.")
    a("")
    a("Databento's public pricing page, read 5 Nov 2026, bills historical data by the uncompressed binary size and confirms a usage-based rate plus subscription plans. The page's rate table is drawn in the browser and did not come through as text. The unit-price sheet they still publish, dated 11 Dec 2024, lists `GLBX.MDP3` historical `trades` at $28 per GB and historical `mbo` at $1.80 per GB. New accounts get $125 of credit. The exact bill for a request is their `metadata.get_cost` call, not this note.")
    a("")
    a("This repo's April 2026 footprint note counts about 7.7 million front-month NQ trades in that month. The public `trades` fields pack to about 48 bytes. That is about 0.37 GB, about $10 at $28 per GB, which is the same $10 to $20 per month this project already used for the trades tape. Thirteen months, June 2025 through July 2026, is on the order of $130 to $260 if every month looks like April. The 2023-to-2026 span is longer, and 2023/24 volume was about half, so the trades bill for the whole master is a few hundred dollars. That is an estimate from the tick count, not an invoice.")
    a("")
    a("`mbo` is not priced by the trade count. April's ten-level book export in this repo was described as about 13 GB compressed and about 144 GB raw, and the project had been using about $80 for a month of that book. Market-by-order is a different schema. The $1.80 per GB rate is the listed price. The gigabytes are the part that has to be quoted before anyone buys it.")
    a("")
    return "\n".join(lines) + "\n"


def _counts_sentence() -> str:
    def n(key: str) -> int:
        return COUNTS.get(key, 0)
    return (
        f"On the holdout the weekly-edge absorption bar fired {n('v1_flag')} times. "
        f"{n('v1_skip')} of those refreshed and were then dropped for a stop wider than 20 points, and {n('v1_trade')} became a trade. "
        f"The rest never printed the next-bar refresh. "
        f"The three-hour range fade flagged {n('v2_flag')} times and filled {n('v2_trade')}. "
        f"The continuation flagged {n('v4_flag')} times and filled {n('v4_trade')}. "
        "A row with fewer than 20 fills has no interval. Its hit rate is the raw count."
    )


def _lead(rows, base) -> str:
    onhl = next((r for r in base if r["name"] == "onhl_pull_s15 1.7R"), None)
    if onhl is None or not rows:
        return "No variant produced a holdout sample."
    ranked = [r for r in rows if r["hold"]["n"] >= 20]
    if not ranked:
        return (
            f"None of the nine pre-registered rows reached 20 holdout fills. "
            f"`onhl_pull_s15` on these same mornings is mean R {_num(onhl['r'][0])} "
            f"({_num(onhl['r'][1])} to {_num(onhl['r'][2])}) on {onhl['n']} fills."
        )
    better = []
    for row in ranked:
        lo = row["hold"]["r"][1]
        if isinstance(lo, float) and not math.isnan(lo) and lo > onhl["r"][0]:
            better.append(row)
    top = max(ranked, key=lambda r: r["hold"]["r"][0] if not math.isnan(r["hold"]["r"][0]) else -999)
    head = (
        f"No Jake Ryan variant beats `onhl_pull_s15` on this holdout. "
        f"The best mean R in the nine is `{top['name']}`, {_num(top['hold']['r'][0])} "
        f"({_num(top['hold']['r'][1])} to {_num(top['hold']['r'][2])}) on {top['hold']['n']} fills. "
        f"The overnight pull on the same days, at 1.7R, is mean R {_num(onhl['r'][0])} "
        f"({_num(onhl['r'][1])} to {_num(onhl['r'][2])}) on {onhl['n']} fills, hit {pct(onhl['hit'])}."
    )
    if better:
        names = ", ".join(r["name"] for r in better)
        head += f" Rows whose mean-R interval sits entirely above the overnight-pull point: {names}."
    else:
        head += " No row has a mean-R interval that sits entirely above that overnight-pull point."
    return head


def main() -> None:
    print("load bars", flush=True)
    df = load_bars(str(DATA))
    days = build_days(df)
    minute, tick = load_footprint()
    print("attach", len(days), flush=True)
    attach(days, df, minute, tick)
    covered = [i for i, d in enumerate(days) if d.covered]
    hold_i = [i for i in covered if days[i].ts >= VAL_END]
    val_i = [i for i in covered if TRAIN_END <= days[i].ts < VAL_END]
    ready = [i for i in hold_i if days[i].p80_ask]
    print("covered", len(covered), "val", len(val_i), "hold", len(hold_i), "hold ready", len(ready), flush=True)
    from scripts.run_fullport import run_book

    onhl17 = run_book(days, "onhl_pull", 15.0, 1.7, "rth", None, {"gap75": 1e9, "gap25": -1, "pd_med": 0}, {}, 1)
    onhl75 = run_book(days, "onhl_pull", 15.0, 0.75, "rth", None, {"gap75": 1e9, "gap25": -1, "pd_med": 0}, {}, 1)
    lon17 = london_book(days, 1.7)
    lon75 = london_book(days, 0.75)
    base = []
    for name, book, p0 in (
        ("onhl_pull_s15 1.7R", onhl17, P0),
        ("onhl_pull_s15 0.75R", onhl75, 1.0 / 1.75),
        ("london +4pt 1.7R", lon17, P0),
        ("london +4pt 0.75R", lon75, 1.0 / 1.75),
    ):
        trades = _fills(book, hold_i)
        test = hit_test(trades, p0)
        base.append({"name": name, "n": test["n"], "hit": test["hit"], "lo": test["lo"], "hi": test["hi"], "r": mean_r(trades), "book": book})
        print(name, test["n"], round(test["hit"], 3) if test["n"] >= 20 else None, flush=True)
    rows = []
    books = {}
    for name, _family, label in VARIANTS:
        print(name, flush=True)
        book = run_variant(days, name)
        books[name] = book
        reward = 3.0 if name.endswith("3r") else 5.0 if name.endswith("5r") else None
        hold = score_fixed(book, hold_i, reward)
        print(" ", hold["n"], flush=True)
        rows.append({"name": name, "label": label, "hold": hold, "bh": False, "book": book})
    _apply_bh(rows)
    firm_list = firms()
    lives = []
    # Baselines use the 0.75 book for the eval and the 1.7 book for the funded shot.
    pairs = [
        ("onhl_pull_s15", onhl75, onhl17),
        ("london +4pt", lon75, lon17),
    ]
    for name, _family, _label in VARIANTS:
        pairs.append((name, books[name], books[name]))
    for label, eval_book, fund_book in pairs:
        eh = [eval_book[i] for i in hold_i]
        fh = [fund_book[i] for i in hold_i]
        trades = _fills(eval_book, hold_i)
        grind = (sum(1 for tr in trades if tr.gross > 0) / len(trades)) if trades else 0.5
        for spec in firm_list:
            life = fullport_life(
                eh, fh, spec, np.random.default_rng(_seed("jake" + label + spec["firm"])),
                min(2000.0, float(spec["mll"])), grind, n=400,
            )
            lives.append({"firm": spec["firm"], "book": label, "life": life})
            print("life", label, spec["firm"], round(life["mean"], 1), flush=True)
    coverage = (
        f"{len(covered)} mornings have footprint on at least 100 of the 09:30-11:30 minutes. "
        f"{len(val_i)} of those fall before 1 Jul 2025, which is the warmup rather than a selection set. "
        f"{len(hold_i)} are the holdout."
    )
    OUT.write_text(render(rows, base, lives, coverage))
    print("counts", COUNTS, flush=True)
    print("wrote", OUT, flush=True)


if __name__ == "__main__":
    main()
