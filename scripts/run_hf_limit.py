"""High-frequency resting-limit search. Writes docs/HF-LIMIT-RESEARCH.md.

The variant list is fixed before the holdout is opened. Rank is validation mean R
among setups that average at least five fills a day. Holdout scores that one
choice. A positive claim also needs the validation sign-flip test to survive
Benjamini-Hochberg across the whole list. Nothing here places an order.
"""

from __future__ import annotations

import math
import sys
import zlib
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_limit_research import (
    TRAIN_END,
    VAL_END,
    _num,
    _payout,
    firms,
    money,
    month_plan,
    pct,
)
from scripts.run_multi_firm_farm import _eval_lock
from scripts.run_strategy_research import deflated_sharpe
from src.research.strategies.costs import (
    COMMISSION_POINTS,
    FLAT_MINUTE,
    MNQ_DOLLARS_PER_POINT,
    TICK,
)
from src.research.strategies.engine import load_bars
from src.research.strategies.hf_limit import (
    eod_update,
    path_blow,
    scan_limits,
)

OUT = ROOT / "docs" / "HF-LIMIT-RESEARCH.md"
DATA = ROOT / "data" / "reference" / "nq_1m_master.parquet"
OPEN = 9 * 60 + 30
POINT = MNQ_DOLLARS_PER_POINT
STOPS = (4.0, 8.0, 12.0, 15.0)
REWARDS = (0.75, 1.0)
CAPS = {"Topstep": 50, "LucidFlex": 40, "FundedNext Futures Flex": 30}
RISKS = (200.0, 400.0, 800.0, 1200.0)
DAILY_LOSS = (None, 500.0, 1000.0)
DAILY_WIN = (None, 750.0, 1500.0)


@dataclass
class Day:
    ts: pd.Timestamp
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    hm: np.ndarray
    vwap_prev: np.ndarray
    i_open: int
    end: int
    onh: float
    onl: float
    pdh: float
    pdl: float
    pdc: float
    rth_open: float
    pd_range: float
    up: int
    or_hi: float
    or_lo: float
    or_i: int
    ib_hi: float
    ib_lo: float
    ib_i: int
    roll_h: dict
    roll_l: dict


def _roll_prior(x: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(x), np.nan)
    if len(x) <= n:
        return out
    view = np.lib.stride_tricks.sliding_window_view(x, n)
    out[n:] = view[: len(x) - n].max(axis=1)
    return out


def _roll_min_prior(x: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(x), np.nan)
    if len(x) <= n:
        return out
    view = np.lib.stride_tricks.sliding_window_view(x, n)
    out[n:] = view[: len(x) - n].min(axis=1)
    return out


def build_days(df: pd.DataFrame) -> list[Day]:
    o = df["open"].to_numpy()
    h = df["high"].to_numpy()
    l = df["low"].to_numpy()
    c = df["close"].to_numpy()
    hm = df["hm"].to_numpy()
    vwap = df["vwap"].to_numpy()
    sess = df["sess"].to_numpy()
    ts = df["ts_event"]
    onh = df["onh"].to_numpy()
    onl = df["onl"].to_numpy()
    pdh = df["pdh"].to_numpy()
    pdl = df["pdl"].to_numpy()
    pdc = df["pdc"].to_numpy()
    cuts = np.flatnonzero(np.diff(sess)) + 1
    bounds = np.r_[0, cuts, len(df)]
    days = []
    for a, b in pairwise(bounds):
        sl = slice(a, b)
        hh = hm[sl]
        hit = np.flatnonzero((hh >= OPEN) & (hh < 18 * 60))
        if len(hit) == 0 or not np.isfinite(pdh[a]):
            continue
        i_open = int(hit[0])
        flat = np.flatnonzero((hh >= FLAT_MINUTE) & (hh < 18 * 60))
        end = int(flat[0]) if len(flat) else len(hh)
        if end <= i_open + 5:
            continue
        prev = np.full(b - a, np.nan)
        prev[1:] = vwap[sl][:-1]
        span = (hh >= OPEN) & (hh < OPEN + 15)
        ib = (hh >= OPEN) & (hh < OPEN + 60)
        or_i = int(np.flatnonzero(hh >= OPEN + 15)[0]) if np.any(hh >= OPEN + 15) else -1
        ib_i = int(np.flatnonzero(hh >= OPEN + 60)[0]) if np.any(hh >= OPEN + 60) else -1
        rth_open = float(o[a + i_open])
        settle = float(pdc[a])
        pd_range = float(pdh[a] - pdl[a])
        if not np.isfinite(pd_range) or pd_range <= 0:
            continue
        hi = h[sl]
        lo = l[sl]
        days.append(Day(
            ts=ts.iloc[a + i_open],
            o=o[sl], h=hi, l=lo, c=c[sl], hm=hh, vwap_prev=prev,
            i_open=i_open, end=end,
            onh=float(onh[a]) if np.isfinite(onh[a]) else np.nan,
            onl=float(onl[a]) if np.isfinite(onl[a]) else np.nan,
            pdh=float(pdh[a]), pdl=float(pdl[a]), pdc=settle,
            rth_open=rth_open, pd_range=pd_range,
            up=1 if rth_open > settle else (-1 if rth_open < settle else 0),
            or_hi=float(hi[span].max()) if span.sum() >= 10 else np.nan,
            or_lo=float(lo[span].min()) if span.sum() >= 10 else np.nan,
            or_i=or_i,
            ib_hi=float(hi[ib].max()) if ib.sum() >= 40 else np.nan,
            ib_lo=float(lo[ib].min()) if ib.sum() >= 40 else np.nan,
            ib_i=ib_i,
            roll_h={n: _roll_prior(hi, n) for n in (10, 20, 30)},
            roll_l={n: _roll_min_prior(lo, n) for n in (10, 20, 30)},
        ))
    return days


def _blank(n):
    return np.full(n, np.nan)


def limits_for(day: Day, kind: str, param):
    n = len(day.o)
    buy, sell = _blank(n), _blank(n)
    start = day.i_open
    if kind == "vwap":
        start = day.i_open + 1
        buy[start:day.end] = day.vwap_prev[start:day.end] - param
        sell[start:day.end] = day.vwap_prev[start:day.end] + param
    elif kind == "range":
        start = day.i_open + int(param)
        buy[start:day.end] = day.roll_l[int(param)][start:day.end]
        sell[start:day.end] = day.roll_h[int(param)][start:day.end]
    elif kind == "onhl_pull":
        if day.up > 0 and np.isfinite(day.onl):
            buy[start:day.end] = day.onl
        elif day.up < 0 and np.isfinite(day.onh):
            sell[start:day.end] = day.onh
    elif kind == "onhl_fade":
        if np.isfinite(day.onl):
            buy[start:day.end] = day.onl
        if np.isfinite(day.onh):
            sell[start:day.end] = day.onh
    elif kind == "pdhl":
        buy[start:day.end] = day.pdl
        sell[start:day.end] = day.pdh
    elif kind == "or15" and day.or_i >= 0 and np.isfinite(day.or_hi):
        start = day.or_i
        buy[start:day.end] = day.or_lo
        sell[start:day.end] = day.or_hi
    elif kind == "ib" and day.ib_i >= 0 and np.isfinite(day.ib_hi):
        start = day.ib_i
        buy[start:day.end] = day.ib_lo
        sell[start:day.end] = day.ib_hi
    elif kind == "round":
        start = day.i_open + 1
        prev = day.c
        step = float(param)
        for i in range(start, day.end):
            px = float(prev[i - 1])
            below = math.floor(px / step) * step
            if abs(px - below) < TICK:
                below -= step
            above = below + step
            buy[i] = below
            sell[i] = above
    elif kind == "halfhour":
        blocks = [OPEN + 30 * k for k in range(12)]
        for left, right in pairwise(blocks):
            m = (day.hm >= left) & (day.hm < right)
            if int(m.sum()) < 8:
                continue
            nxt = (day.hm >= right) & (day.hm < right + 30) & (np.arange(n) < day.end)
            sell[nxt] = float(day.h[m].max())
            buy[nxt] = float(day.l[m].min())
    return buy, sell, start


def variant_list():
    out = []
    for band in (6.0, 10.0, 16.0):
        for stop in STOPS:
            for reward in REWARDS:
                out.append((f"vwap_{band:.0f}_s{stop:.0f}_r{reward}", "vwap", band, stop, reward))
    for n in (10, 20, 30):
        for stop in STOPS:
            for reward in REWARDS:
                out.append((f"range_{n}_s{stop:.0f}_r{reward}", "range", float(n), stop, reward))
    for kind in ("onhl_pull", "onhl_fade", "pdhl", "or15", "ib", "halfhour"):
        for stop in STOPS:
            for reward in REWARDS:
                out.append((f"{kind}_s{stop:.0f}_r{reward}", kind, 0.0, stop, reward))
    for step in (25.0, 50.0):
        for stop in STOPS:
            for reward in (1.0,):
                out.append((f"round_{step:.0f}_s{stop:.0f}_r{reward}", "round", step, stop, reward))
    return out


def _seed(text: str) -> int:
    return zlib.crc32(text.encode()) & 0x7FFFFFFF


def sign_flip_p(r: np.ndarray, n_perm: int, seed: int) -> float:
    if len(r) < 8:
        return 1.0
    rng = np.random.default_rng(seed)
    # A permutation on every fill is the same test. Past 2,500 fills the mean is
    # already precise, and the sign matrix would be the expensive object.
    if len(r) > 2500:
        r = r[rng.choice(len(r), 2500, replace=False)]
    obs = float(r.mean())
    signs = rng.integers(0, 2, size=(n_perm, len(r))) * 2 - 1
    null = (signs * r).mean(axis=1)
    return float(np.mean(null >= obs - 1e-15))


def bh_mask(pvals: np.ndarray, q: float = 0.10) -> np.ndarray:
    order = np.argsort(pvals)
    ok = pvals[order] <= (np.arange(1, len(pvals) + 1) / len(pvals)) * q
    passed = np.zeros(len(pvals), dtype=bool)
    if ok.any():
        passed[order[: int(np.max(np.flatnonzero(ok))) + 1]] = True
    return passed


def mean_ci(x: np.ndarray) -> tuple[float, float, float]:
    if len(x) < 2:
        return float("nan"), float("nan"), float("nan")
    mid = float(x.mean())
    se = float(x.std(ddof=1) / math.sqrt(len(x)))
    return mid, mid - 1.96 * se, mid + 1.96 * se


def breakeven(reward: float, stop: float) -> float:
    win = reward * stop - COMMISSION_POINTS
    loss = stop + TICK + COMMISSION_POINTS
    if win <= 0:
        return 1.0
    return loss / (win + loss)


def hit_ci(hits: int, n: int, p0: float) -> dict:
    if n < 20:
        return {"hit": float("nan"), "lo": float("nan"), "hi": float("nan"), "p": 1.0}
    ph = hits / n
    se = math.sqrt(ph * (1.0 - ph) / n)
    z = (ph - p0) / math.sqrt(p0 * (1.0 - p0) / n)
    from statistics import NormalDist
    return {"hit": ph, "lo": ph - 1.96 * se, "hi": ph + 1.96 * se, "p": float(1.0 - NormalDist().cdf(z))}


def run_variant(days, kind, param, stop, reward, through=1, first_only=False):
    booked = []
    for day in days:
        buy, sell, start = limits_for(day, kind, param)
        booked.append(scan_limits(
            day.o, day.h, day.l, day.c, day.hm, buy, sell, stop, reward, start, day.end, through, first_only,
        ))
    return booked


def _rs(booked, idxs) -> np.ndarray:
    vals = []
    for i in idxs:
        for tr in booked[i]:
            vals.append((tr.gross - COMMISSION_POINTS) / tr.risk)
    return np.asarray(vals, dtype=float)


def _daily(booked, idxs) -> np.ndarray:
    out = np.zeros(len(idxs))
    for k, i in enumerate(idxs):
        out[k] = sum((tr.gross - COMMISSION_POINTS) / tr.risk for tr in booked[i])
    return out


def sharpe_day(daily: np.ndarray) -> float:
    if len(daily) < 5 or float(daily.std(ddof=1)) == 0:
        return float("nan")
    return float(daily.mean() / daily.std(ddof=1))


def contracts_for(stop_pts, dollar_risk, room, rate, cap) -> int:
    per = (stop_pts + TICK) * POINT + rate
    if per <= 0 or room <= per:
        return 0
    n = int(dollar_risk // per)
    n = min(n, int((room - 1.0) // per), cap)
    return max(n, 0)


def _dollars(tr, ncon, rate):
    return tr.gross * POINT * ncon - rate * ncon, tr.mae * POINT * ncon + rate * ncon


def play_day(trades, equity, floor, rate, cap, dollar_risk, daily_loss, daily_win):
    """Return (equity, dead, day_pnl). A dip to the floor ends the account."""
    day_pnl = 0.0
    for tr in trades:
        room = equity - floor
        ncon = contracts_for(tr.risk, dollar_risk, room, rate, cap)
        if ncon < 1:
            continue
        pnl, mae_d = _dollars(tr, ncon, rate)
        planned = (tr.risk + TICK) * POINT * ncon + rate * ncon
        if daily_loss is not None and day_pnl - planned < -daily_loss:
            continue
        if path_blow(equity, floor, mae_d):
            return floor, True, day_pnl - min(mae_d, room)
        equity += pnl
        day_pnl += pnl
        if equity <= floor + 1e-9:
            return floor, True, day_pnl
        if daily_loss is not None and day_pnl <= -daily_loss:
            break
        if daily_win is not None and day_pnl >= daily_win:
            break
    return equity, False, day_pnl


def one_account(eval_days, fund_days, spec, rng, dollar_risk, daily_loss, daily_win, eval_h=40, fund_h=40):
    cap = CAPS[spec["firm"]]
    rate = float(spec["rate"])
    mll = float(spec["mll"])
    size = float(spec["size"])
    balance = size
    floor = size - mll
    locked = False
    best = 0.0
    alive = True
    passed = False
    locks, trigger, lock_at = _eval_lock(spec)
    day_count = 0
    for _ in range(eval_h):
        if not alive or passed:
            break
        trades = eval_days[int(rng.integers(0, len(eval_days)))]
        balance, dead, day_pnl = play_day(trades, balance, floor, rate, cap, dollar_risk, daily_loss, daily_win)
        day_count += 1
        if dead:
            alive = False
            break
        best = max(best, day_pnl)
        if locks:
            floor, locked = eod_update(balance, floor, locked, mll, trigger, lock_at)
        need = max(float(spec["target"]), best / float(spec["consistency"]) if best > 0 else float(spec["target"]))
        if day_count >= int(spec["min_eval_days"]) and balance - size + 1e-6 >= need:
            passed = True
    fee = float(spec["fee"]) + (float(spec["activation"]) if passed else 0.0)
    cash = 0.0
    pays = 0
    if passed and alive:
        f_start = float(spec["funded_start"])
        balance = f_start
        floor = f_start - mll
        locked = False
        wins = 0.0
        cycle = 0.0
        need_wins = int(spec["winning_days"])
        max_pays = int(spec["max_payouts"] or 8)
        for _ in range(fund_h):
            trades = fund_days[int(rng.integers(0, len(fund_days)))]
            balance, dead, day_pnl = play_day(
                trades, balance, floor, rate, cap, dollar_risk, daily_loss, daily_win,
            )
            if dead:
                alive = False
                break
            cycle += day_pnl
            if day_pnl + 1e-9 >= float(spec["win_min"]):
                wins += 1
            floor, locked = eod_update(
                balance, floor, locked, mll, float(spec["lock_trigger"]), float(spec["lock_floor"]),
            )
            amount = float(_payout(spec, np.array([balance]), np.array([cycle]))[0])
            take = wins + 1e-9 >= need_wins and cycle > float(spec["buffer"]) and amount >= float(spec["min_request"])
            if take and pays < max_pays:
                cash += amount * float(spec["split"])
                balance -= amount
                floor = float(spec["lock_floor"])
                locked = True
                pays += 1
                wins = 0.0
                cycle = 0.0
                if pays >= max_pays:
                    break
                if balance <= floor + 1e-9:
                    alive = False
                    break
    return cash - fee, passed, pays, day_count if passed else np.nan


def summarise_lives(rows):
    net = np.array([r[0] for r in rows])
    passed = np.array([r[1] for r in rows])
    pays = np.array([r[2] for r in rows], dtype=float)
    days = np.array([r[3] for r in rows], dtype=float)
    mid, lo, hi = mean_ci(net)
    return {
        "mean": mid, "lo": lo, "hi": hi,
        "pass": float(passed.mean()),
        "pays": float(pays.mean() * 100),
        "days": float(np.nanmean(days)) if np.isfinite(days).any() else float("nan"),
    }


def run_lives(eval_days, fund_days, spec, dollar_risk, daily_loss, daily_win, n, seed):
    rng = np.random.default_rng(seed)
    rows = [
        one_account(eval_days, fund_days, spec, rng, dollar_risk, daily_loss, daily_win)
        for _ in range(n)
    ]
    return summarise_lives(rows)


def month_cash(days, spec, dollar_risk, daily_loss, daily_win, n=250):
    """21 trading days. `slots` evals open on day one. A pass converts only while a funded seat is free."""
    slots, note = month_plan(spec)
    rng = np.random.default_rng(_seed("month" + spec["firm"] + str(dollar_risk)))
    cap = CAPS[spec["firm"]]
    rate = float(spec["rate"])
    mll = float(spec["mll"])
    size = float(spec["size"])
    fee = float(spec["fee"])
    activation = float(spec["activation"])
    funded_cap = int(spec["funded_cap"])
    locks, trigger, lock_at = _eval_lock(spec)
    phase = np.ones((n, slots), dtype=np.int8)
    bal = np.full((n, slots), size)
    floor = np.full((n, slots), size - mll)
    locked = np.zeros((n, slots), dtype=bool)
    best = np.zeros((n, slots))
    edays = np.zeros((n, slots))
    fwins = np.zeros((n, slots))
    cycle = np.zeros((n, slots))
    pays = np.zeros((n, slots))
    cash = np.full(n, -fee * slots)
    for _d in range(21):
        converted = np.zeros((n, slots), dtype=bool)
        for j in range(slots):
            on = phase[:, j] == 1
            if not on.any():
                continue
            for i in np.flatnonzero(on):
                trades = days[int(rng.integers(0, len(days)))]
                eq, dead, day_pnl = play_day(
                    trades, bal[i, j], floor[i, j], rate, cap, dollar_risk, daily_loss, daily_win,
                )
                if dead:
                    phase[i, j] = 0
                    continue
                bal[i, j] = eq
                edays[i, j] += 1
                best[i, j] = max(best[i, j], day_pnl)
                if locks:
                    floor[i, j], locked[i, j] = eod_update(
                        bal[i, j], floor[i, j], locked[i, j], mll, trigger, lock_at,
                    )
                need = max(float(spec["target"]), best[i, j] / float(spec["consistency"]) if best[i, j] > 0 else float(spec["target"]))
                if edays[i, j] >= int(spec["min_eval_days"]) and bal[i, j] - size + 1e-6 >= need:
                    if int((phase[i] == 2).sum()) < funded_cap:
                        phase[i, j] = 2
                        converted[i, j] = True
                        cash[i] -= activation
                        bal[i, j] = float(spec["funded_start"])
                        floor[i, j] = float(spec["funded_start"]) - mll
                        locked[i, j] = False
                        fwins[i, j] = 0.0
                        cycle[i, j] = 0.0
                        pays[i, j] = 0.0
                    else:
                        phase[i, j] = 0
        for j in range(slots):
            on = (phase[:, j] == 2) & ~converted[:, j]
            if not on.any():
                continue
            for i in np.flatnonzero(on):
                trades = days[int(rng.integers(0, len(days)))]
                eq, dead, day_pnl = play_day(
                    trades, bal[i, j], floor[i, j], rate, cap, dollar_risk, daily_loss, daily_win,
                )
                if dead:
                    phase[i, j] = 0
                    continue
                bal[i, j] = eq
                cycle[i, j] += day_pnl
                if day_pnl + 1e-9 >= float(spec["win_min"]):
                    fwins[i, j] += 1
                floor[i, j], locked[i, j] = eod_update(
                    bal[i, j], floor[i, j], locked[i, j], mll,
                    float(spec["lock_trigger"]), float(spec["lock_floor"]),
                )
                amount = float(_payout(spec, np.array([bal[i, j]]), np.array([cycle[i, j]]))[0])
                max_pays = int(spec["max_payouts"] or 8)
                take = (
                    fwins[i, j] + 1e-9 >= int(spec["winning_days"])
                    and cycle[i, j] > float(spec["buffer"])
                    and amount >= float(spec["min_request"])
                    and pays[i, j] < max_pays
                )
                if take:
                    cash[i] += amount * float(spec["split"])
                    bal[i, j] -= amount
                    floor[i, j] = float(spec["lock_floor"])
                    locked[i, j] = True
                    pays[i, j] += 1
                    fwins[i, j] = 0.0
                    cycle[i, j] = 0.0
                    if pays[i, j] >= max_pays or bal[i, j] <= floor[i, j] + 1e-9:
                        phase[i, j] = 0
    return cash, note, slots


def split_account(eval_days, big_days, spec, rng, big_risk, two):
    """The current book: 0.75R eval days, then one 1.7:1 day or two $1,000 days, then a grind."""
    cap = CAPS[spec["firm"]]
    rate = float(spec["rate"])
    mll = float(spec["mll"])
    size = float(spec["size"])
    risk = min(big_risk, mll)
    balance = size
    floor = size - mll
    locked = False
    best = 0.0
    passed = False
    alive = True
    locks, trigger, lock_at = _eval_lock(spec)
    days_used = 0
    for _ in range(40):
        trades = eval_days[int(rng.integers(0, len(eval_days)))]
        balance, dead, day_pnl = play_day(trades, balance, floor, rate, cap, risk, None, None)
        days_used += 1
        if dead:
            alive = False
            break
        best = max(best, day_pnl)
        if locks:
            floor, locked = eod_update(balance, floor, locked, mll, trigger, lock_at)
        need = max(float(spec["target"]), best / float(spec["consistency"]) if best > 0 else float(spec["target"]))
        if days_used >= int(spec["min_eval_days"]) and balance - size + 1e-6 >= need:
            passed = True
            break
    fee = float(spec["fee"]) + (float(spec["activation"]) if passed else 0.0)
    cash = 0.0
    pays = 0
    if passed and alive:
        balance = float(spec["funded_start"])
        floor = balance - mll
        locked = False
        wins = 0.0
        cycle = 0.0
        filled = [d for d in big_days if d]
        if not filled:
            return cash - fee, passed, pays, days_used
        grind_p = float(np.mean([tr.hit for d in eval_days for tr in d])) if any(eval_days) else 0.0
        win_min = float(spec["win_min"])
        loss_g = win_min / 0.75 if win_min else 0.0
        max_pays = int(spec["max_payouts"] or 8)
        for _cycle_i in range(max_pays):
            picks = [filled[int(rng.integers(0, len(filled)))] for _ in range(2 if two else 1)]
            unit = 1000.0 if two else risk
            dead = False
            day_pnl = 0.0
            for trs in picks:
                balance, dead, pnl = play_day(trs, balance, floor, rate, cap, unit, None, None)
                day_pnl += pnl
                if dead:
                    break
            if dead:
                alive = False
                break
            cycle += day_pnl
            if day_pnl + 1e-9 >= win_min:
                wins += 1.0
            floor, locked = eod_update(
                balance, floor, locked, mll, float(spec["lock_trigger"]), float(spec["lock_floor"]),
            )
            while wins < int(spec["winning_days"]) and alive:
                hit = rng.random() < grind_p
                pnl = win_min if hit else -loss_g
                if path_blow(balance, floor, max(-pnl, 0.0)):
                    alive = False
                    balance = floor
                    break
                balance += pnl
                cycle += pnl
                day_pnl = pnl
                if pnl >= win_min:
                    wins += 1
                if balance <= floor + 1e-9:
                    alive = False
                    break
                floor, locked = eod_update(
                    balance, floor, locked, mll, float(spec["lock_trigger"]), float(spec["lock_floor"]),
                )
            if not alive:
                break
            amount = float(_payout(spec, np.array([balance]), np.array([cycle]))[0])
            if wins + 1e-9 >= int(spec["winning_days"]) and cycle > float(spec["buffer"]) and amount >= float(spec["min_request"]):
                cash += amount * float(spec["split"])
                balance -= amount
                floor = float(spec["lock_floor"])
                locked = True
                pays += 1
                wins = 0.0
                cycle = 0.0
                if balance <= floor + 1e-9:
                    break
            else:
                break
    return cash - fee, passed, pays, days_used if passed else np.nan


def main() -> None:
    print("load", flush=True)
    df = load_bars(str(DATA))
    days = build_days(df)
    print("days", len(days), flush=True)
    val_i = [i for i, d in enumerate(days) if TRAIN_END <= d.ts < VAL_END]
    hold_i = [i for i, d in enumerate(days) if d.ts >= VAL_END]
    variants = variant_list()
    print("variants", len(variants), flush=True)
    rows = []
    for name, kind, param, stop, reward in variants:
        print(name, flush=True)
        booked = run_variant(days, kind, param, stop, reward)
        rv, rh = _rs(booked, val_i), _rs(booked, hold_i)
        dv = _daily(booked, val_i)
        fills_v = int(sum(len(booked[i]) for i in val_i))
        fills_h = int(sum(len(booked[i]) for i in hold_i))
        p0 = 1.0 / (1.0 + reward)
        hv = hit_ci(sum(tr.hit for i in val_i for tr in booked[i]), fills_v, p0)
        hh = hit_ci(sum(tr.hit for i in hold_i for tr in booked[i]), fills_h, p0)
        rows.append({
            "name": name, "kind": kind, "param": param, "stop": stop, "reward": reward,
            "p": sign_flip_p(rv, 800, _seed(name)),
            "dsr": deflated_sharpe(rv, len(variants)) if len(rv) else 0.0,
            "val_r": mean_ci(rv), "hold_r": mean_ci(rh),
            "val_n": len(rv), "hold_n": len(rh),
            "fpd_v": fills_v / len(val_i), "fpd_h": fills_h / len(hold_i),
            "hv": hv, "hh": hh,
            "sharpe_v": sharpe_day(dv), "sharpe_h": sharpe_day(_daily(booked, hold_i)),
            "be": breakeven(reward, stop), "p0": p0,
        })
    pvals = np.array([r["p"] for r in rows])
    survive = bh_mask(pvals)
    for r, ok in zip(rows, survive, strict=True):
        r["bh"] = bool(ok)
    eligible = [r for r in rows if r["fpd_v"] >= 5 and r["val_n"] >= 200]
    eligible.sort(key=lambda r: 1.0 if math.isnan(r["val_r"][0]) else -r["val_r"][0])
    winner = eligible[0] if eligible else None
    firm_list = firms()
    policies = []
    chosen = {}
    if winner is not None:
        booked = run_variant(days, winner["kind"], winner["param"], winner["stop"], winner["reward"])
        val_days = [booked[i] for i in val_i]
        hold_days = [booked[i] for i in hold_i]
        for spec in firm_list:
            best = None
            for risk in RISKS:
                for loss in DAILY_LOSS:
                    for win in DAILY_WIN:
                        stat = run_lives(val_days, val_days, spec, risk, loss, win, 300, _seed(winner["name"] + spec["firm"]))
                        rec = {"firm": spec["firm"], "risk": risk, "loss": loss, "win": win, "val": stat}
                        policies.append(rec)
                        if best is None or stat["mean"] > best["val"]["mean"]:
                            best = rec
            hold = run_lives(
                hold_days, hold_days, spec, best["risk"], best["loss"], best["win"], 800,
                _seed("hold" + spec["firm"]),
            )
            cash, note, slots = month_cash(hold_days, spec, best["risk"], best["loss"], best["win"])
            mid, lo, hi = mean_ci(cash)
            chosen[spec["firm"]] = {
                "policy": best, "hold": hold, "month": mid, "mlo": lo, "mhi": hi,
                "p_neg": float(np.mean(cash < 0)), "slots": slots, "note": note,
            }
            print("chosen", spec["firm"], best["risk"], best["loss"], best["win"], round(hold["mean"], 1), flush=True)
    # comparison book under the same floor rules
    compare = []
    if winner is not None:
        eval_book = []
        big_book = []
        for day in days:
            stop = min(80.0, max(8.0, 0.10 * day.pd_range))
            buy, sell = _blank(len(day.o)), _blank(len(day.o))
            if day.up > 0 and np.isfinite(day.onl):
                buy[day.i_open:day.end] = day.onl
            elif day.up < 0 and np.isfinite(day.onh):
                sell[day.i_open:day.end] = day.onh
            eval_book.append(scan_limits(
                day.o, day.h, day.l, day.c, day.hm, buy, sell, stop, 0.75, day.i_open, day.end, 1, True,
            ))
            big_book.append(scan_limits(
                day.o, day.h, day.l, day.c, day.hm, buy, sell, stop, 1.7, day.i_open, day.end, 1, True,
            ))
        ev_h = [eval_book[i] for i in hold_i]
        bg_h = [big_book[i] for i in hold_i]
        for spec in firm_list:
            for label, two in (("onhl 0.75R / 1.7:1", False), ("onhl two $1,000 risks", True)):
                rng = np.random.default_rng(_seed(label + spec["firm"]))
                got = [split_account(ev_h, bg_h, spec, rng, min(2000.0, float(spec["mll"])), two) for _ in range(800)]
                compare.append({"firm": spec["firm"], "label": label, "stat": summarise_lives(got)})
                print("cmp", spec["firm"], label, round(compare[-1]["stat"]["mean"], 1), flush=True)
    # fill sensitivity on the winner
    sens = None
    if winner is not None:
        base = _rs(booked, hold_i)
        rng = np.random.default_rng(9)
        dropped = {}
        for frac in (0.25, 0.50):
            keep = rng.random(len(base)) >= frac
            dropped[frac] = mean_ci(base[keep]) if keep.sum() >= 2 else (float("nan"),) * 3
        retwo = run_variant(days, winner["kind"], winner["param"], winner["stop"], winner["reward"], through=2)
        sens = {"base": mean_ci(base), "drop": dropped, "two_tick": mean_ci(_rs(retwo, hold_i))}
    OUT.write_text(render(rows, winner, chosen, compare, sens, len(val_i), len(hold_i)))
    print("wrote", OUT, flush=True)


def _fmt_policy(p) -> str:
    loss = "no daily loss stop" if p["loss"] is None else f"stop for the day after {money(p['loss'])}"
    win = "no daily profit stop" if p["win"] is None else f"stop for the day after {money(p['win'])}"
    return f"risk {money(p['risk'])} a trade, {loss}, {win}"


def render(rows, winner, chosen, compare, sens, n_val, n_hold) -> str:
    lines = [
        "# High-frequency limit research",
        "",
        "Disarmed. Nothing here places an order. Angus's thesis is that a small net expectancy, about +0.1R, at five or more fills a day, beats a rare setup, because the variance is smaller and an eval or a payout cycle finishes sooner.",
        "",
        "The list below was fixed before the holdout from 1 July 2025 was opened. A setup is eligible only if the validation window averages at least five fills a day and has at least 200 fills. The winner is the eligible setup with the highest validation mean R. Its holdout is the confirmation. Separately, a sign-flip test that mean R is above zero is run on every variant, and Benjamini-Hochberg at 10% is applied across the whole list. A holdout interval above zero is a surviving edge only when that variant also passed the validation correction. Showing other holdout cells is so the ranking can be checked. Those cells were not the sort key.",
        "",
        "## Drawdown, from the live pages",
        "",
        "All three trails move with the closing balance, not with an intraday high. A spike that is given back by the close does not lift the floor. A dip that reaches the floor, including an open loss, ends the account even if the close would have recovered.",
        "",
        "- Topstep, page dated 18 September 2026, [What is the Maximum Loss Limit?](https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit): \"The MLL is a trailing limit. It rises as your end-of-day balance grows, but never moves down.\" And: \"The MLL updates at the end of each trading day but is monitored in real time throughout the session. Both realized and unrealized P&L count toward it.\" A 50K combine starts at $50,000 with the floor at $48,000, and the floor locks at $50,000 once it has trailed up to the start. A 50K express funded account starts at $0, the floor starts at -$2,000, and the floor locks at $0 once the balance reaches $2,000. The [daily loss limit](https://help.topstep.com/en/articles/10490293-daily-loss-limit-in-the-trading-combine-and-express-funded-account) is optional. If it is on, a 50K account's published figure is $1,000, and hitting it flattens the account for the session. It is not, by itself, the end of the account. The main table does not buy that option.",
        "- LucidFlex, page dated 26 August 2026, [LucidFlex Drawdown](https://support.lucidtrading.com/en/articles/12945815-lucidflex-drawdown): \"LucidFlex evaluation and funded accounts use an End-of-Day Drawdown (EOD Drawdown) system to calculate the Max Loss Limit (MLL).\" \"At the end of each trading session, the system calculates the account's highest closing balance.\" A 50K account's max loss is $2,000, the trail balance is $52,100, and the locked floor is $50,100. The same page says \"If your account balance reached the MLL, your account will be breached.\" It does not use the words unrealized or floating. Topstep and FundedNext do. This sim still treats a dip to the floor as a breach, which is the stricter reading of that sentence, and it does not lift the floor on an intraday high. The [customization page](https://support.lucidtrading.com/en/articles/16226050-lucidflex-customization) makes a daily loss limit optional and calls it a soft lockout. It does not print the dollar amount, so none is applied. The fee is the assumed $100.",
        "- FundedNext Flex, [Flex Challenge rules](https://helpfutures.fundednext.com/en/articles/17229829-fundednext-futures-flex-challenge-all-rules), updated 13 October 2026: the 50K target is $2,500, the max loss is $1,500, and \"The MLL adjusts at the end of each trading day, not in real time.\" \"If your floating loss breaches the MLL during a live trade, your account is breached instantly.\" \"No. The Flex Challenge has no daily loss limit at any stage.\" The floor in this sim locks at $50,100, which a $1,500 trail reaches when the close is $51,600. The same page caps the account at 30 micros. LucidFlex's funded page caps a 50K at 40 micros. Topstep's combine parameters cap a 50K at 50 micros. Size never exceeds those caps.",
        "",
        "Inside a trade, the worst open loss is the path down to the stop, or through it if the bar gaps the stop. If that open loss reaches the floor, the account is over and the later target does not count. The floor is then updated from the close only.",
        "",
        "## The search",
        "",
        "Families, all resting limits, trade-through of one tick, one position at a time, flat at 15:55 ET. Stops are 4, 8, 12 and 15 points. Targets are 0.75R and 1R, except the round-number fades, which are 1R only.",
        "",
        "- VWAP, 6, 10 or 16 points off the prior bar's session VWAP. The band is known before the fill bar.",
        "- The prior 10, 20 or 30 one-minute bars, faded at the high and the low.",
        "- Overnight high and low, the pull side only (the old `onhl_pull_none` idea, allowed to fill more than once) and both sides. Prior-day high and low. The 15-minute opening range, after 09:45. The 60-minute initial balance, after 10:30.",
        "- The 25-point and 50-point rounds around the prior close, updated every bar.",
        "- The high and low of the previous 30-minute block, faded during the next block.",
        "",
        f"There are {len(rows)} variants. Validation sessions: {n_val}. Holdout sessions: {n_hold}. Research R subtracts Topstep's $1.22 ({_num(COMMISSION_POINTS)} points). A no-drift path hits 0.75R about 57% of the time and 1R about 50% of the time. Breakeven is higher, because the stop fills one tick worse and the commission comes off both outcomes. The lifecycle then uses each firm's own MNQ rate. FundedNext does not print one, so that row is charged $1.22.",
        "",
        "| variant | val fills/day | val n | val hit | breakeven | val mean R | val p | BH | hold fills/day | hold mean R | hold Sharpe/day |",
        "|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|",
    ]
    a = lines.append
    ranked = sorted(
        rows,
        key=lambda r: (
            0 if r["fpd_v"] >= 5 and r["val_n"] >= 200 else 1,
            math.inf if math.isnan(r["val_r"][0]) else -r["val_r"][0],
        ),
    )
    for r in ranked[:15]:
        a(
            f"| {r['name']} | {r['fpd_v']:.2f} | {r['val_n']} | {pct(r['hv']['hit'])} | {pct(r['be'])} | "
            f"{_num(r['val_r'][0])} ({_num(r['val_r'][1])} to {_num(r['val_r'][2])}) | {r['p']:.3f} | "
            f"{'yes' if r['bh'] else 'no'} | {r['fpd_h']:.2f} | "
            f"{_num(r['hold_r'][0])} ({_num(r['hold_r'][1])} to {_num(r['hold_r'][2])}) | {_num(r['sharpe_h'])} |"
        )
    n_elig = sum(1 for r in rows if r["fpd_v"] >= 5 and r["val_n"] >= 200)
    n_bh = sum(1 for r in rows if r["bh"])
    a("")
    a(
        f"Eligible on validation: {n_elig}. Variants whose validation sign-flip test survived Benjamini-Hochberg at 10%: {n_bh}. "
        "Nearby stops and targets are the same idea repeated, so that count is not a count of independent discoveries. The claim is the one pre-chosen variant."
    )
    a("")
    if winner is None:
        a("No variant averaged five fills a day on the validation window with at least 200 fills. There is no high-frequency candidate to take forward.")
    else:
        w = winner
        a(f"The validation winner is `{w['name']}`. Validation fills per day {w['fpd_v']:.2f}, hit {pct(w['hv']['hit'])} against a no-drift {pct(w['p0'])} and a breakeven {pct(w['be'])}. Validation mean R {_num(w['val_r'][0])} ({_num(w['val_r'][1])} to {_num(w['val_r'][2])}), Sharpe per day {_num(w['sharpe_v'])}. Holdout fills per day {w['fpd_h']:.2f}, hit {pct(w['hh']['hit'])} ({pct(w['hh']['lo'])} to {pct(w['hh']['hi'])}), mean R {_num(w['hold_r'][0])} ({_num(w['hold_r'][1])} to {_num(w['hold_r'][2])}), Sharpe per day {_num(w['sharpe_h'])}. Benjamini-Hochberg on the validation test: {'passed' if w['bh'] else 'did not pass'}.")
        a("")
        if sens is not None:
            a("## Fills at this frequency")
            a("")
            a("A one-tick trade-through is already a stricter fill than a touch. It is not a queue. At five or more attempts a day, the orders you actually get are the ones price went through, which is the adverse selection a resting limit suffers. Two further checks, on the winner only, not used to choose it:")
            a("")
            d25, d50 = sens["drop"][0.25], sens["drop"][0.50]
            a(f"- Drop a random 25% of the holdout fills, as a missed queue: mean R {_num(d25[0])} ({_num(d25[1])} to {_num(d25[2])}).")
            a(f"- Drop a random 50%: mean R {_num(d50[0])} ({_num(d50[1])} to {_num(d50[2])}).")
            a(f"- Require two ticks of trade-through instead of one, and rescan: mean R {_num(sens['two_tick'][0])} ({_num(sens['two_tick'][1])} to {_num(sens['two_tick'][2])}).")
            a("")
        a("## Lifecycle")
        a("")
        a("The same holdout days are the eval and the funded account. Size is chosen on the validation lifecycle, per firm: dollar risk per trade, a daily loss stop that only ends the session, and a daily profit stop. The stop loss of a new trade has to fit inside the room down to the floor, and inside the contract cap. The holdout column is that one policy. The onhl rows are the current book, replayed with the same floor rules: a 0.75R eval and a 1.7:1 funded day, and the same funded day as two $1,000 risks. Their grind days still use the 0.75R hit rate, booked at the firm's minimum winning day.")
        a("")
        a("| firm | book | policy | holdout pass | days | EV per eval | payouts / 100 |")
        a("|---|---|---|---:|---:|---|---:|")
        for spec_name, item in chosen.items():
            p = item["policy"]
            h = item["hold"]
            hdays = "n/a" if math.isnan(h["days"]) else f"{h['days']:.1f}"
            a(
                f"| {spec_name} | `{w['name']}` | {_fmt_policy(p)} | {pct(h['pass'])} | {hdays} | "
                f"{money(h['mean'])} ({money(h['lo'])} to {money(h['hi'])}) | {h['pays']:.1f} |"
            )
        for row in compare:
            st = row["stat"]
            days = "n/a" if math.isnan(st["days"]) else f"{st['days']:.1f}"
            a(
                f"| {row['firm']} | {row['label']} | the earlier sizing | {pct(st['pass'])} | {days} | "
                f"{money(st['mean'])} ({money(st['lo'])} to {money(st['hi'])}) | {st['pays']:.1f} |"
            )
        a("")
        a("| firm | evals opened | mean 21-day book | 95% CI | P(month negative) |")
        a("|---|---:|---:|---|---:|")
        for spec_name, item in chosen.items():
            a(
                f"| {spec_name} | {item['slots']} | {money(item['month'])} | {money(item['mlo'])} to {money(item['mhi'])} | {pct(item['p_neg'])} |"
            )
        a("")
        for spec_name, item in chosen.items():
            a(f"- {spec_name}: {item['note']}")
        a("")
    a("A trade that opens and closes inside one minute can be shorter than FundedNext's 10-second micro-scalping clock. The minute bars cannot see that clock, so this study does not claim those trades are exempt.")
    a("")
    a("## Verdict")
    a("")
    a(_verdict(winner, rows, sens, chosen))
    a("")
    return "\n".join(lines) + "\n"


def _verdict(winner, rows, sens, chosen) -> str:
    if winner is None:
        fastest = max(rows, key=lambda r: r["fpd_v"])
        return (
            f"No setup averaged five fills a day on the validation window. "
            f"The busiest was `{fastest['name']}` at {fastest['fpd_v']:.2f} fills a day. "
            "The thesis, as a high-frequency book, does not get a candidate."
        )
    lo = winner["hold_r"][1]
    above = isinstance(lo, float) and not math.isnan(lo) and lo > 0
    n_bh = sum(1 for r in rows if r["bh"])
    claim = (
        f"`{winner['name']}` was the eligible validation winner, at {winner['fpd_v']:.2f} fills a day. "
        f"Holdout hit {pct(winner['hh']['hit'])} ({pct(winner['hh']['lo'])} to {pct(winner['hh']['hi'])}) "
        f"against a no-drift {pct(winner['p0'])} and a breakeven {pct(winner['be'])}. "
        f"Holdout mean R is {_num(winner['hold_r'][0])} ({_num(winner['hold_r'][1])} to {_num(winner['hold_r'][2])}). "
    )
    if above and winner["bh"]:
        claim += (
            f"That interval is above zero, and the validation test was one of {n_bh} that survived Benjamini-Hochberg. "
            "Under the one-tick trade-through cost model, this is a holdout edge."
        )
    elif above:
        claim += "The interval is above zero, and the validation test did not survive the correction, so it is not a corrected discovery."
    else:
        claim += "That interval does not sit above zero. No high-frequency setup here has a holdout edge that survives costs and the correction."
    if sens is not None:
        d50 = sens["drop"][0.50]
        covers = not (isinstance(d50[1], float) and not math.isnan(d50[1]) and d50[1] > 0)
        two = sens["two_tick"]
        two_ok = isinstance(two[1], float) and not math.isnan(two[1]) and two[1] > 0
        claim += (
            " Requiring two ticks of trade-through "
            + ("still leaves the mean-R interval above zero. " if two_ok else "does not leave the mean-R interval above zero. ")
            + (
                "Dropping half the fills, a harsh missed-queue check, makes that interval cover zero."
                if covers
                else "Dropping half the fills still leaves the interval above zero."
            )
        )
    if chosen:
        bits = []
        for firm, item in chosen.items():
            bits.append(f"{firm} 21-day book {money(item['month'])}, P(month negative) {pct(item['p_neg'])}")
        claim += (
            " The per-eval EV is the whole life of the account. A 21-day month often ends before that life does. "
            + ". ".join(bits) + "."
        )
    return claim


if __name__ == "__main__":
    main()
