"""Two-phase limit research. Writes docs/LIMIT-ENTRY-RESEARCH.md.

Eval and funded are separate searches, both fixed before the holdout is used
to choose. The eval search ranks by validation pass rate. The funded search
ranks by validation hit rate on the 1.7:1 target. Holdout is the confirmation
of those two choices, not a second search. A result beats the random baseline
only when its holdout interval sits entirely above it: about 26% for an eval
pass, and 37% for a 1.7:1 hit.

Disarmed. No orders are sent.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_multi_firm_farm import _eval_lock, _trail, load_survey
from src.research.strategies.costs import (
    COMMISSION_POINTS,
    COMMISSION_RT_USD,
    FLAT_MINUTE,
    MNQ_DOLLARS_PER_POINT,
    TICK,
)
from src.research.strategies.engine import load_bars
from src.research.strategies.limit_entry import (
    MAX_RISK,
    MIN_RISK,
    force_fill_at_limit,
    try_fill,
)

TRAIN_END = pd.Timestamp("2024-07-01", tz="America/New_York")
VAL_END = pd.Timestamp("2025-07-01", tz="America/New_York")
VAL_MID = pd.Timestamp("2025-01-01", tz="America/New_York")
OUT = ROOT / "docs" / "LIMIT-ENTRY-RESEARCH.md"
LEVELS = ("pdhl", "settle", "onhl", "or5", "or30", "ib60", "vwap", "round")
STYLES = ("fade", "pull")
FILTERS = ("none", "wide_on", "gap", "hot30")
REFERENCE = "pdhl_fade_none"


@dataclass
class Sess:
    ts: pd.Timestamp
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    hm: np.ndarray
    pdh: float
    pdl: float
    pdc: float
    pd_range: float
    onh: float
    onl: float
    on_range: float
    rth_open: float
    or5: tuple[float, float] | None
    or30: tuple[float, float] | None
    ib: tuple[float, float] | None
    or30_vol: float
    vwap: float
    atr: float
    round_lo: float
    round_hi: float
    hot30: bool
    wide_on: bool
    gap_hot: bool
    up: int
    i0930: int
    i0931: int
    i0935: int
    i1000: int
    i1030: int


def _idx(hm: np.ndarray, minute: int) -> int:
    """First daytime bar at or after `minute`. The session opens at 18:00, which is numerically later than 09:30."""
    hit = np.flatnonzero((hm >= minute) & (hm < 18 * 60))
    return int(hit[0]) if len(hit) else -1


def _span(hm, h, l, vol, start, stop, minimum: int) -> tuple[float, float, float] | None:
    m = (hm >= start) & (hm < stop)
    if int(m.sum()) < minimum:
        return None
    return float(h[m].max()), float(l[m].min()), float(vol[m].sum())


def build_sessions(df: pd.DataFrame) -> list[Sess]:
    o = df["open"].to_numpy()
    h = df["high"].to_numpy()
    l = df["low"].to_numpy()
    c = df["close"].to_numpy()
    hm = df["hm"].to_numpy()
    vol = df["volume"].to_numpy()
    atr = df["atr"].to_numpy()
    vwap = df["vwap"].to_numpy()
    sess = df["sess"].to_numpy()
    ts = df["ts_event"]
    pdh = df["pdh"].to_numpy()
    pdl = df["pdl"].to_numpy()
    pdc = df["pdc"].to_numpy()
    onh = df["onh"].to_numpy()
    onl = df["onl"].to_numpy()
    cuts = np.flatnonzero(np.diff(sess)) + 1
    bounds = np.r_[0, cuts, len(df)]
    raw: list[Sess] = []
    or30_hist: list[float] = []
    vol_hist: list[float] = []
    for a, b in pairwise(bounds):
        sl = slice(a, b)
        hh, ll = hm[sl], l[sl]
        span5 = _span(hh, h[sl], ll, vol[sl], 9 * 60 + 30, 9 * 60 + 35, 4)
        span30 = _span(hh, h[sl], ll, vol[sl], 9 * 60 + 30, 10 * 60, 20)
        span60 = _span(hh, h[sl], ll, vol[sl], 9 * 60 + 30, 10 * 60 + 30, 40)
        i0930 = _idx(hh, 9 * 60 + 30)
        if i0930 < 0 or not np.isfinite(pdh[a]):
            continue
        rth_open = float(o[a + i0930])
        pd_range = float(pdh[a] - pdl[a])
        if not np.isfinite(pd_range) or pd_range <= 0:
            continue
        on_hi = float(onh[a]) if np.isfinite(onh[a]) else float("nan")
        on_lo = float(onl[a]) if np.isfinite(onl[a]) else float("nan")
        on_range = on_hi - on_lo if np.isfinite(on_hi) and np.isfinite(on_lo) else float("nan")
        or30_range = (span30[0] - span30[1]) if span30 else float("nan")
        or30_vol = span30[2] if span30 else float("nan")
        med_r = float(np.median(or30_hist[-20:])) if len(or30_hist) >= 20 else float("nan")
        med_v = float(np.median(vol_hist[-20:])) if len(vol_hist) >= 20 else float("nan")
        hot = bool(
            np.isfinite(med_r)
            and np.isfinite(or30_range)
            and (or30_range > med_r or (np.isfinite(med_v) and or30_vol > 1.5 * med_v))
        )
        if np.isfinite(or30_range):
            or30_hist.append(or30_range)
            vol_hist.append(or30_vol)
        i_form = _idx(hh, 9 * 60 + 34)
        below = math.floor(rth_open / 100.0) * 100.0
        if abs(rth_open - below) < TICK:
            below -= 100.0
        above = below + 100.0
        if abs(rth_open - above) < TICK:
            above += 100.0
        vwap_px = float(vwap[a + i_form]) if i_form >= 0 and np.isfinite(vwap[a + i_form]) else float("nan")
        atr_px = float(atr[a + i_form]) if i_form >= 0 and np.isfinite(atr[a + i_form]) else float("nan")
        gap = abs(rth_open - float(pdc[a]))
        raw.append(Sess(
            ts=ts.iloc[a + i0930],
            o=o[sl], h=h[sl], l=ll, c=c[sl], hm=hh,
            pdh=float(pdh[a]), pdl=float(pdl[a]), pdc=float(pdc[a]), pd_range=pd_range,
            onh=on_hi, onl=on_lo, on_range=on_range,
            rth_open=rth_open,
            or5=(span5[0], span5[1]) if span5 else None,
            or30=(span30[0], span30[1]) if span30 else None,
            ib=(span60[0], span60[1]) if span60 else None,
            or30_vol=or30_vol,
            vwap=vwap_px, atr=atr_px,
            round_lo=below, round_hi=above,
            hot30=hot,
            wide_on=bool(np.isfinite(on_range) and on_range > pd_range),
            gap_hot=bool(gap > 0.3 * pd_range),
            up=1 if rth_open > float(pdc[a]) else (-1 if rth_open < float(pdc[a]) else 0),
            i0930=i0930,
            i0931=_idx(hh, 9 * 60 + 31),
            i0935=_idx(hh, 9 * 60 + 35),
            i1000=_idx(hh, 10 * 60),
            i1030=_idx(hh, 10 * 60 + 30),
        ))
    return raw


def _order(side: int, limit: float, buffer: float, reward: float) -> tuple | None:
    if side not in (1, -1) or not np.isfinite(limit) or not (MIN_RISK <= buffer <= MAX_RISK):
        return None
    if side == 1:
        return side, limit, limit - buffer, limit + reward * buffer
    return side, limit, limit + buffer, limit - reward * buffer


def _orders(s: Sess, level: str, style: str, reward: float) -> list[tuple]:
    buf = max(MIN_RISK, 0.10 * s.pd_range)
    start = s.i0930
    sides: list[tuple[int, float, int]] = []
    if level == "pdhl":
        sides = [(1, s.pdl, start), (-1, s.pdh, start)]
    elif level == "settle":
        side = -1 if s.up > 0 else (1 if s.up < 0 else 0)
        if style == "pull":
            side = -side
        if side:
            sides = [(side, s.pdc, start)]
    elif level == "onhl":
        sides = [(1, s.onl, start), (-1, s.onh, start)]
    elif level == "or5" and s.or5 and s.i0935 >= 0:
        sides = [(1, s.or5[1], s.i0935), (-1, s.or5[0], s.i0935)]
    elif level == "or30" and s.or30 and s.i1000 >= 0:
        sides = [(1, s.or30[1], s.i1000), (-1, s.or30[0], s.i1000)]
    elif level == "ib60" and s.ib and s.i1030 >= 0:
        sides = [(1, s.ib[1], s.i1030), (-1, s.ib[0], s.i1030)]
    elif level == "vwap" and s.i0935 >= 0 and np.isfinite(s.vwap) and np.isfinite(s.atr) and s.atr > 0:
        if s.up > 0:
            sides = [(-1 if style == "fade" else 1, s.vwap - s.atr if style == "pull" else s.vwap + s.atr, s.i0935)]
        elif s.up < 0:
            sides = [(1 if style == "fade" else -1, s.vwap + s.atr if style == "pull" else s.vwap - s.atr, s.i0935)]
    elif level == "round" and s.i0931 >= 0:
        sides = [(1, s.round_lo, s.i0931), (-1, s.round_hi, s.i0931)]
    if style == "pull" and level not in ("settle", "vwap"):
        sides = [x for x in sides if x[0] == s.up]
    out = []
    for side, limit, place in sides:
        made = _order(side, limit, buf, reward)
        if made and place >= 0:
            out.append((*made, place))
    return out


def _allowed(s: Sess, style: str, filt: str) -> bool:
    if filt == "wide_on":
        return not s.wide_on
    if filt == "gap":
        return (not s.gap_hot) if style == "fade" else s.gap_hot
    if filt == "hot30":
        return (not s.hot30) if style == "fade" else s.hot30
    return True


def _place(order, filt: str, s: Sess) -> int:
    place = order[4]
    if filt == "hot30":
        place = max(place, s.i1000)
    return place


def _session_end(hm: np.ndarray) -> int:
    """First daytime bar at or after 15:55. The 18:00 open is not the flat."""
    hit = np.flatnonzero((hm >= FLAT_MINUTE) & (hm < 18 * 60))
    return int(hit[0]) if len(hit) else len(hm)


def _first_bar(side: int, limit: float, o: np.ndarray, h: np.ndarray, l: np.ndarray, through: bool) -> int | None:
    """First bar that trades the limit before a gap kills the order. None if it never does."""
    extra = TICK if through else 0.0
    if side == 1:
        gap = o <= limit - TICK
        touch = l <= limit - extra
    else:
        gap = o >= limit + TICK
        touch = h >= limit + extra
    ok = touch & ~gap
    if not ok.any():
        return None
    first_ok = int(np.flatnonzero(ok)[0])
    if gap.any() and int(np.flatnonzero(gap)[0]) <= first_ok:
        return None
    return first_ok


def run_variant(
    sessions: list[Sess],
    level: str,
    style: str,
    filt: str,
    through: bool,
    reward: float,
    count_missed: bool = False,
) -> list[dict]:
    rows = []
    for s in sessions:
        if not _allowed(s, style, filt):
            rows.append(_flat(s.ts))
            continue
        orders = _orders(s, level, style, reward)
        if not orders:
            rows.append(_flat(s.ts))
            continue
        orders = [(*o[:4], _place(o, filt, s)) for o in orders]
        orders = [o for o in orders if o[4] >= 0]
        if not orders:
            rows.append(_flat(s.ts))
            continue
        end = _session_end(s.hm)
        hits: list[tuple[int, int]] = []
        for i, (side, limit, _stop, _target, place) in enumerate(orders):
            if place < 0 or place >= end:
                continue
            rel = _first_bar(side, limit, s.o[place:end], s.h[place:end], s.l[place:end], through)
            if rel is not None:
                hits.append((place + rel, i))
        filled = False
        target_hit = False
        gross = 0.0
        risk = 0.0
        missed = False
        if hits:
            hits.sort()
            bar = hits[0][0]
            same = [i for j, i in hits if j == bar]
            if len(same) == 1:
                side, limit, stop, target = orders[same[0]][:4]
                got = try_fill(
                    s.o, s.h, s.l, s.c, s.hm, bar, len(s.o), side, limit, stop, target, through,
                )
                filled = got.filled
                target_hit = got.target_hit
                gross = got.gross_points
                risk = got.risk_points
        if count_missed and not filled:
            for side, limit_px, stop, target, place in orders:
                if place < 0:
                    continue
                ghost = force_fill_at_limit(
                    s.o, s.h, s.l, s.c, s.hm, place, len(s.o), side, limit_px, stop, target,
                )
                if ghost.target_hit:
                    missed = True
                    break
        rows.append({
            "ts": s.ts,
            "filled": filled,
            "target_hit": target_hit,
            "gross": gross,
            "risk": risk,
            "missed": missed,
            "placed": True,
        })
    return rows


def _flat(ts) -> dict:
    return {
        "ts": ts, "filled": False, "target_hit": False, "gross": 0.0,
        "risk": 0.0, "missed": False, "placed": False,
    }


def _period(rows: list[dict], start, end) -> list[dict]:
    out = []
    for row in rows:
        ts = row["ts"]
        if start is not None and ts < start:
            continue
        if end is not None and ts >= end:
            continue
        out.append(row)
    return out


def _r(rows: list[dict]) -> np.ndarray:
    filled = [row for row in rows if row["filled"] and row["risk"] > 0]
    if not filled:
        return np.array([])
    return np.array([(row["gross"] - COMMISSION_POINTS) / row["risk"] for row in filled])


def _mean(x: np.ndarray) -> float:
    return float(x.mean()) if len(x) else float("nan")


def pack(rows: list[dict]) -> dict:
    rr = _r(rows)
    placed = sum(bool(row.get("placed")) for row in rows)
    filled = sum(row["filled"] for row in rows)
    hits = sum(row["target_hit"] for row in rows if row["filled"])
    missed = sum(row["missed"] for row in rows)
    empty = {
        "n": 0,
        "mean": float("nan"),
        "hit": float("nan"),
        "fill": 0.0,
        "miss": 0.0,
        "placed": placed,
    }
    if len(rr) == 0:
        return empty
    return {
        "n": len(rr),
        "mean": float(rr.mean()),
        "hit": hits / filled if filled else float("nan"),
        "fill": filled / placed if placed else 0.0,
        "miss": missed / placed if placed else 0.0,
        "placed": placed,
    }


EVAL_R = 1500.0 / 2000.0
FUNDED_R = 1.7
RANDOM_HIT_17 = 1.0 / (1.0 + FUNDED_R)
WALK_HIT_075 = 1.0 / (1.0 + EVAL_R)
ND = NormalDist()
FIRM_KEYS = ("topstep_50k", "lucid_flex_50k", "fundednext_flex_50k")
# Lucid prints MNQ at $0.50 per side. FundedNext prints no MNQ rate.
FIRM_RATES = {
    "Topstep": COMMISSION_RT_USD,
    "LucidFlex": 1.00,
    "FundedNext Futures Flex": COMMISSION_RT_USD,
}
STOP_DOLLARS_PER_MNQ = 16.0 * MNQ_DOLLARS_PER_POINT
STOP_SLIP_PER_MNQ = TICK * MNQ_DOLLARS_PER_POINT


def money(v: float) -> str:
    if isinstance(v, float) and math.isnan(v):
        return "n/a"
    return f"${v:,.0f}"


def pct(v: float) -> str:
    if isinstance(v, float) and math.isnan(v):
        return "n/a"
    return f"{100 * v:.1f}%"


def days_s(v: float) -> str:
    if isinstance(v, float) and math.isnan(v):
        return "n/a"
    return f"{float(v):.1f}"


def _num(v: float) -> str:
    if isinstance(v, float) and math.isnan(v):
        return "n/a"
    return f"{v:.3f}"


def _finite(v: float, fallback: float) -> float:
    if isinstance(v, float) and math.isnan(v):
        return fallback
    return float(v)


def day_dollars(rows: list[dict], risk_dollars: float, rate: float) -> np.ndarray:
    """Scale each fill to a dollar stop. Unfilled days are zero. Commission is the firm's MNQ rate."""
    out = np.zeros(len(rows))
    scale = MNQ_DOLLARS_PER_POINT
    for i, row in enumerate(rows):
        if not row["filled"] or row["risk"] <= 0:
            continue
        contracts = risk_dollars / (row["risk"] * scale)
        out[i] = row["gross"] * scale * contracts - rate * contracts
    return out


def stack_smaller(day: np.ndarray, copies: int, rng: np.random.Generator, n: int = 4000) -> np.ndarray:
    """`copies` independent trades, each at 1/copies of the original dollar risk."""
    pick = day[rng.integers(0, len(day), size=(n, copies))]
    return pick.sum(axis=1) / copies


def eval_stats(day: np.ndarray, spec: dict, seed: int, n: int = 1500, horizon: int = 40) -> dict:
    if len(day) < 30:
        return {"pass": float("nan"), "lo": float("nan"), "hi": float("nan"), "days": float("nan")}
    rng = np.random.default_rng(seed)
    draws = day[rng.integers(0, len(day), size=(n, horizon))]
    size = float(spec["size"])
    mll = float(spec["mll"])
    target = float(spec["target"])
    cons = float(spec["consistency"])
    min_days = int(spec["min_eval_days"])
    intraday = spec["stated_breach"] == "intraday"
    balance = np.full(n, size)
    floor = np.full(n, size - mll)
    high = balance.copy()
    locked = np.zeros(n, dtype=bool)
    best = np.zeros(n)
    alive = np.ones(n, dtype=bool)
    passed = np.zeros(n, dtype=bool)
    when = np.full(n, np.nan)
    locks, trigger, lock_at = _eval_lock(spec)
    for d in range(horizon):
        on = alive & ~passed
        if not on.any():
            break
        pnl = draws[:, d]
        room = balance - floor
        die = on & intraday & (pnl < 0) & (-pnl > room + 1e-9)
        alive &= ~die
        on = alive & ~passed
        balance = np.where(on, balance + pnl, balance)
        dead = on & (balance <= floor + 1e-9)
        alive &= ~dead
        on = alive & ~passed
        best = np.where(on, np.maximum(best, pnl), best)
        floor, high, locked = _trail(balance, floor, high, locked, on, trigger, lock_at, mll, locks)
        profit = balance - size
        need = np.maximum(target, np.where(best > 0, best / cons, target))
        now = on & ((d + 1) >= min_days) & (profit + 1e-6 >= need)
        when = np.where(now & ~passed, d + 1, when)
        passed |= now
    p = float(passed.mean())
    se = math.sqrt(max(p * (1.0 - p), 0.0) / n)
    days = float(np.nanmean(when)) if np.isfinite(when).any() else float("nan")
    return {"pass": p, "lo": p - 1.96 * se, "hi": p + 1.96 * se, "days": days}


def hit_vs_random(hits: int, n: int, p0: float = RANDOM_HIT_17) -> dict:
    if n < 20:
        return {"hit": float("nan"), "lo": float("nan"), "hi": float("nan"), "p": 1.0}
    ph = hits / n
    se = math.sqrt(ph * (1.0 - ph) / n)
    z = (ph - p0) / math.sqrt(p0 * (1.0 - p0) / n)
    return {"hit": ph, "lo": ph - 1.96 * se, "hi": ph + 1.96 * se, "p": float(1.0 - ND.cdf(z))}


def firms() -> list[dict]:
    survey = load_survey()
    out = []
    for key in FIRM_KEYS:
        spec = dict(survey[key])
        if spec.get("fee") is None:
            spec["fee"] = 100.0
            spec["fee_assumed"] = True
        else:
            spec["fee_assumed"] = False
        spec["rate"] = FIRM_RATES[spec["firm"]]
        spec["rate_note"] = (
            "MNQ rate is not printed; this row is charged Topstep's $1.22"
            if spec["firm"].startswith("FundedNext")
            else "the firm's own MNQ card"
        )
        out.append(spec)
    return out


def _payout(spec: dict, balance: np.ndarray, cycle: np.ndarray) -> np.ndarray:
    base = spec["payout_base"]
    fraction = float(spec["payout_fraction"])
    if base == "balance":
        raw = fraction * np.maximum(balance, 0.0)
    elif base == "total_profit":
        raw = fraction * np.maximum(balance - float(spec["funded_start"]), 0.0)
    else:
        raw = fraction * np.maximum(cycle, 0.0)
    if spec["cap"]:
        raw = np.minimum(raw, float(spec["cap"]))
    return raw


def _one_payout(spec: dict, balance: float, cycle: float) -> float:
    amount = float(_payout(spec, np.array([balance]), np.array([cycle]))[0])
    if amount + 1e-9 < float(spec["min_request"]):
        return 0.0
    if cycle <= float(spec["buffer"]):
        return 0.0
    return amount


def lifecycle(
    eval_day: np.ndarray,
    funded_day: np.ndarray,
    grind_p: float,
    spec: dict,
    rng: np.random.Generator,
    n: int = 1500,
) -> dict:
    """One purchase. Eval days are resampled. The funded day is one 1.7:1 trade. Grind days use `grind_p`."""
    mll = float(spec["mll"])
    win_min = float(spec["win_min"])
    grind_loss = win_min / EVAL_R if win_min else 0.0
    intraday = spec["stated_breach"] == "intraday"
    passed_flag = np.zeros(n, dtype=bool)
    size = float(spec["size"])
    balance = np.full(n, size)
    floor = np.full(n, size - mll)
    high = balance.copy()
    locked = np.zeros(n, dtype=bool)
    best = np.zeros(n)
    alive = np.ones(n, dtype=bool)
    locks, trigger, lock_at = _eval_lock(spec)
    days_used = np.zeros(n)
    for d in range(40):
        on = alive & ~passed_flag
        if not on.any():
            break
        pnl = eval_day[rng.integers(0, len(eval_day), size=n)]
        room = balance - floor
        die = on & intraday & (pnl < 0) & (-pnl > room + 1e-9)
        alive &= ~die
        on = alive & ~passed_flag
        balance = np.where(on, balance + pnl, balance)
        dead = on & (balance <= floor + 1e-9)
        alive &= ~dead
        on = alive & ~passed_flag
        days_used = np.where(on, d + 1, days_used)
        best = np.where(on, np.maximum(best, pnl), best)
        floor, high, locked = _trail(balance, floor, high, locked, on, trigger, lock_at, mll, locks)
        profit = balance - size
        need = np.maximum(
            float(spec["target"]),
            np.where(best > 0, best / float(spec["consistency"]), float(spec["target"])),
        )
        now = on & ((d + 1) >= int(spec["min_eval_days"])) & (profit + 1e-6 >= need)
        passed_flag |= now
    fee = np.full(n, float(spec["fee"])) + np.where(passed_flag, float(spec["activation"]), 0.0)
    f_start = float(spec["funded_start"])
    f_bal = np.full(n, f_start)
    f_floor = np.full(n, f_start - mll)
    f_high = f_bal.copy()
    f_locked = np.zeros(n, dtype=bool)
    f_alive = passed_flag.copy()
    cash = np.zeros(n)
    n_pay = np.zeros(n)
    need_wins = int(spec["winning_days"])
    # A firm with no payout cap is run through eight cycles. Later cycles are rare.
    cycles = int(spec["max_payouts"] or 8)
    for _cycle in range(cycles):
        on = f_alive
        if not on.any():
            break
        big = funded_day[rng.integers(0, len(funded_day), size=n)]
        room = f_bal - f_floor
        die = on & intraday & (big < 0) & (-big > room + 1e-9)
        f_alive &= ~die
        on = f_alive
        f_bal = np.where(on, f_bal + big, f_bal)
        dead = on & (f_bal <= f_floor + 1e-9)
        f_alive &= ~dead
        on = f_alive
        wins = (on & (big >= win_min)).astype(float)
        cycle = np.where(on, big, 0.0)
        f_floor, f_high, f_locked = _trail(
            f_bal, f_floor, f_high, f_locked, on,
            float(spec["lock_trigger"]), float(spec["lock_floor"]), mll, True,
        )
        for _g in range(need_wins + 2):
            want = f_alive & (wins < need_wins)
            if not want.any():
                break
            hit = rng.random(n) < grind_p
            gp = np.where(hit, win_min, -grind_loss)
            room = f_bal - f_floor
            die = want & intraday & (gp < 0) & (-gp > room + 1e-9)
            f_alive &= ~die
            want = f_alive & (wins < need_wins)
            f_bal = np.where(want, f_bal + gp, f_bal)
            dead = want & (f_bal <= f_floor + 1e-9)
            f_alive &= ~dead
            want = f_alive & (wins < need_wins)
            wins = np.where(want & hit, wins + 1, wins)
            cycle = np.where(want, cycle + gp, cycle)
            f_floor, f_high, f_locked = _trail(
                f_bal, f_floor, f_high, f_locked, want,
                float(spec["lock_trigger"]), float(spec["lock_floor"]), mll, True,
            )
        amount = _payout(spec, f_bal, cycle)
        take = (
            f_alive
            & (wins + 1e-9 >= need_wins)
            & (cycle > float(spec["buffer"]))
            & (amount >= float(spec["min_request"]))
        )
        if spec["max_payouts"] is not None:
            take &= n_pay < spec["max_payouts"]
        f_bal = np.where(take, f_bal - amount, f_bal)
        cash = np.where(take, cash + amount * float(spec["split"]), cash)
        n_pay = np.where(take, n_pay + 1, n_pay)
        f_floor = np.where(take, float(spec["lock_floor"]), f_floor)
        f_locked = f_locked | take
        f_alive &= take
        f_alive &= ~(take & (f_bal <= f_floor + 1e-9))
    net = cash - fee
    mean = float(net.mean())
    se = float(net.std(ddof=1) / math.sqrt(n))
    passer_days = days_used[passed_flag]
    return {
        "mean": mean,
        "lo": mean - 1.96 * se,
        "hi": mean + 1.96 * se,
        "pass": float(passed_flag.mean()),
        "payouts_per_100": float(n_pay.mean() * 100),
        "days": float(passer_days.mean()) if len(passer_days) else float("nan"),
        "net": net,
    }


def grid_value(spec: dict, p_pass: float, p_hit: float) -> float:
    """Exact EV of one payout cycle. A miss busts. A hit is followed by four finished minimum days and one payout."""
    mll = float(spec["mll"])
    contracts = mll / STOP_DOLLARS_PER_MNQ
    comm = float(spec["rate"]) * contracts
    big = FUNDED_R * mll - comm
    cycle = big + 4.0 * float(spec["win_min"])
    balance = float(spec["funded_start"]) + cycle
    amount = _one_payout(spec, balance, cycle)
    cash = amount * float(spec["split"])
    fee = float(spec["fee"])
    activation = float(spec["activation"])
    return -fee + p_pass * (-activation + p_hit * cash)


def month_plan(spec: dict) -> tuple[int, str]:
    """How many evaluations the month opens, and why that number is the cap."""
    if spec["firm"] == "Topstep":
        return (
            int(spec["eval_cap"]),
            "15 Combines opened on day one. Topstep publishes no Combine cap; 15 is the comparison batch in the rules file. At most 5 can be funded.",
        )
    if spec["firm"] == "LucidFlex":
        return (
            int(spec["eval_cap"]),
            "10 evaluations opened on day one, which is also the household combined cap. At most 5 can be funded.",
        )
    return (
        10,
        "10 challenges opened on day one. The help centre allows 10 issued in a calendar month. The survey's eval_cap of 15 is not used for this month. At most 5 can be funded.",
    )


def month_at_cap(
    eval_day: np.ndarray,
    funded_day: np.ndarray,
    grind_p: float,
    spec: dict,
    rng: np.random.Generator,
    n: int = 400,
    days: int = 21,
    fill_rate: float = 1.0,
) -> np.ndarray:
    """21 trading days. Fees for every opened eval come out on day one. No replacement past the cap."""
    slots, _note = month_plan(spec)
    fee = float(spec["fee"])
    activation = float(spec["activation"])
    mll = float(spec["mll"])
    size = float(spec["size"])
    target = float(spec["target"])
    cons = float(spec["consistency"])
    min_days = int(spec["min_eval_days"])
    intraday = spec["stated_breach"] == "intraday"
    win_min = float(spec["win_min"])
    grind_loss = win_min / EVAL_R if win_min else 0.0
    need_wins = int(spec["winning_days"])
    f_start = float(spec["funded_start"])
    funded_cap = int(spec["funded_cap"])
    locks, trigger, lock_at = _eval_lock(spec)
    phase = np.ones((n, slots), dtype=np.int8)
    bal = np.full((n, slots), size)
    floor = np.full((n, slots), size - mll)
    high = np.full((n, slots), size)
    locked = np.zeros((n, slots), dtype=bool)
    best = np.zeros((n, slots))
    edays = np.zeros((n, slots))
    f_bal = np.full((n, slots), f_start)
    f_floor = np.full((n, slots), f_start - mll)
    f_high = np.full((n, slots), f_start)
    f_locked = np.zeros((n, slots), dtype=bool)
    wins = np.zeros((n, slots))
    cycle = np.zeros((n, slots))
    n_pay = np.zeros((n, slots))
    stage = np.zeros((n, slots), dtype=np.int8)
    cash = np.full(n, -fee * slots)
    for _d in range(days):
        converted = np.zeros((n, slots), dtype=bool)
        for j in range(slots):
            on = phase[:, j] == 1
            if not on.any():
                continue
            pnl = eval_day[rng.integers(0, len(eval_day), size=n)]
            room = bal[:, j] - floor[:, j]
            die = on & intraday & (pnl < 0) & (-pnl > room + 1e-9)
            phase[:, j] = np.where(die, 0, phase[:, j])
            on = phase[:, j] == 1
            bal[:, j] = np.where(on, bal[:, j] + pnl, bal[:, j])
            dead = on & (bal[:, j] <= floor[:, j] + 1e-9)
            phase[:, j] = np.where(dead, 0, phase[:, j])
            on = phase[:, j] == 1
            edays[:, j] = np.where(on, edays[:, j] + 1, edays[:, j])
            best[:, j] = np.where(on, np.maximum(best[:, j], pnl), best[:, j])
            floor[:, j], high[:, j], locked[:, j] = _trail(
                bal[:, j], floor[:, j], high[:, j], locked[:, j], on, trigger, lock_at, mll, locks,
            )
            profit = bal[:, j] - size
            need = np.maximum(target, np.where(best[:, j] > 0, best[:, j] / cons, target))
            now = on & (edays[:, j] + 1e-9 >= min_days) & (profit + 1e-6 >= need)
            n_funded = (phase == 2).sum(axis=1)
            can = now & (n_funded < funded_cap)
            phase[:, j] = np.where(can, 2, phase[:, j])
            phase[:, j] = np.where(now & ~can, 0, phase[:, j])
            converted[:, j] = can
            cash = np.where(can, cash - activation, cash)
            f_bal[:, j] = np.where(can, f_start, f_bal[:, j])
            f_floor[:, j] = np.where(can, f_start - mll, f_floor[:, j])
            f_high[:, j] = np.where(can, f_start, f_high[:, j])
            f_locked[:, j] = np.where(can, False, f_locked[:, j])
            wins[:, j] = np.where(can, 0.0, wins[:, j])
            cycle[:, j] = np.where(can, 0.0, cycle[:, j])
            n_pay[:, j] = np.where(can, 0.0, n_pay[:, j])
            stage[:, j] = np.where(can, 0, stage[:, j])
        for j in range(slots):
            on = (phase[:, j] == 2) & ~converted[:, j]
            if not on.any():
                continue
            want_big = on & (stage[:, j] == 0)
            want_grind = on & (stage[:, j] == 1)
            big = funded_day[rng.integers(0, len(funded_day), size=n)]
            got_fill = rng.random(n) < fill_rate
            hit = rng.random(n) < grind_p
            gp = np.where(hit, win_min, -grind_loss)
            # A day with no fill keeps the account waiting for the 1.7:1 trade.
            pnl = np.where(want_big & got_fill, big, np.where(want_grind, gp, 0.0))
            use = (want_big & got_fill) | want_grind
            room = f_bal[:, j] - f_floor[:, j]
            die = use & intraday & (pnl < 0) & (-pnl > room + 1e-9)
            phase[:, j] = np.where(die, 0, phase[:, j])
            use = use & (phase[:, j] == 2)
            f_bal[:, j] = np.where(use, f_bal[:, j] + pnl, f_bal[:, j])
            dead = use & (f_bal[:, j] <= f_floor[:, j] + 1e-9)
            phase[:, j] = np.where(dead, 0, phase[:, j])
            use = use & (phase[:, j] == 2)
            wins[:, j] = np.where(use & want_big & (big >= win_min), wins[:, j] + 1, wins[:, j])
            wins[:, j] = np.where(use & want_grind & hit, wins[:, j] + 1, wins[:, j])
            cycle[:, j] = np.where(use, cycle[:, j] + pnl, cycle[:, j])
            f_floor[:, j], f_high[:, j], f_locked[:, j] = _trail(
                f_bal[:, j], f_floor[:, j], f_high[:, j], f_locked[:, j], use,
                float(spec["lock_trigger"]), float(spec["lock_floor"]), mll, True,
            )
            survived_big = use & want_big
            stage[:, j] = np.where(survived_big, 1, stage[:, j])
            amount = _payout(spec, f_bal[:, j], cycle[:, j])
            take = (
                use
                & (phase[:, j] == 2)
                & (wins[:, j] + 1e-9 >= need_wins)
                & (cycle[:, j] > float(spec["buffer"]))
                & (amount >= float(spec["min_request"]))
            )
            if spec["max_payouts"] is not None:
                take &= n_pay[:, j] < spec["max_payouts"]
            f_bal[:, j] = np.where(take, f_bal[:, j] - amount, f_bal[:, j])
            cash = np.where(take, cash + amount * float(spec["split"]), cash)
            n_pay[:, j] = np.where(take, n_pay[:, j] + 1, n_pay[:, j])
            f_floor[:, j] = np.where(take, float(spec["lock_floor"]), f_floor[:, j])
            f_locked[:, j] = f_locked[:, j] | take
            stage[:, j] = np.where(take, 0, stage[:, j])
            wins[:, j] = np.where(take, 0.0, wins[:, j])
            cycle[:, j] = np.where(take, 0.0, cycle[:, j])
            broke = take & (f_bal[:, j] <= f_floor[:, j] + 1e-9)
            phase[:, j] = np.where(broke, 0, phase[:, j])
            if spec["max_payouts"] is not None:
                done = take & (n_pay[:, j] >= spec["max_payouts"])
                phase[:, j] = np.where(done, 0, phase[:, j])
    return cash


def _rank_pass(row: tuple) -> tuple:
    p = row[0]
    if isinstance(p, float) and math.isnan(p):
        return (1, 0.0)
    return (0, -float(p))


def _hit_key(row: dict) -> float:
    h = row["fu_val_pack"]["hit"]
    if isinstance(h, float) and math.isnan(h):
        return -1.0
    return float(h)


def _ci(mean: float, sample: np.ndarray) -> tuple[float, float]:
    se = float(sample.std(ddof=1) / math.sqrt(len(sample)))
    return mean - 1.96 * se, mean + 1.96 * se


def mean_r_ci(rows: list[dict]) -> tuple[float, float, float]:
    rr = _r(rows)
    if len(rr) < 2:
        return float("nan"), float("nan"), float("nan")
    mid = float(rr.mean())
    se = float(rr.std(ddof=1) / math.sqrt(len(rr)))
    return mid, mid - 1.96 * se, mid + 1.96 * se


def main() -> None:
    print("bars", flush=True)
    df = load_bars(str(ROOT / "data" / "reference" / "nq_1m_master.parquet"))
    sessions = build_sessions(df)
    print("sessions", len(sessions), flush=True)
    firm_list = firms()
    catalog = []
    for level in LEVELS:
        for style in STYLES:
            for filt in FILTERS:
                name = f"{level}_{style}_{filt}"
                print(name, flush=True)
                ev = run_variant(sessions, level, style, filt, True, EVAL_R)
                fu = run_variant(sessions, level, style, filt, True, FUNDED_R)
                catalog.append({
                    "name": name,
                    "level": level,
                    "style": style,
                    "filt": filt,
                    "eval": ev,
                    "funded": fu,
                })
    ranked: dict[str, list] = {spec["firm"]: [] for spec in firm_list}
    for item in catalog:
        ev_val = _period(item["eval"], TRAIN_END, VAL_END)
        ev_hold = _period(item["eval"], VAL_END, None)
        fu_val = _period(item["funded"], TRAIN_END, VAL_END)
        fu_hold = _period(item["funded"], VAL_END, None)
        item["ev_val_pack"] = pack(ev_val)
        item["ev_hold_pack"] = pack(ev_hold)
        item["fu_val_pack"] = pack(fu_val)
        item["fu_hold_pack"] = pack(fu_hold)
        fu_hits = sum(row["target_hit"] for row in fu_val if row["filled"])
        item["fu_val_test"] = hit_vs_random(fu_hits, item["fu_val_pack"]["n"])
        fu_hits_h = sum(row["target_hit"] for row in fu_hold if row["filled"])
        item["fu_hold_test"] = hit_vs_random(fu_hits_h, item["fu_hold_pack"]["n"])
        for spec in firm_list:
            risk = min(2000.0, float(spec["mll"]))
            day = day_dollars(ev_val, risk, spec["rate"])
            if item["ev_val_pack"]["n"] < 80:
                stat = {"pass": float("nan"), "lo": float("nan"), "hi": float("nan"), "days": float("nan")}
            else:
                stat = eval_stats(day, spec, seed=11 + int(spec["mll"]))
            ranked[spec["firm"]].append((stat["pass"], item, stat))
    chosen = {}
    reference = {}
    for spec in firm_list:
        board = ranked[spec["firm"]]
        board.sort(key=_rank_pass)
        chosen[spec["firm"]] = board[0]
        for p, item, stat in board:
            if item["name"] == REFERENCE:
                reference[spec["firm"]] = (p, stat, item)
                break
    eligible = [row for row in catalog if row["fu_val_pack"]["n"] >= 100]
    eligible.sort(key=_hit_key, reverse=True)
    funded_winner = eligible[0] if eligible else catalog[0]
    baselines = []
    for spec in firm_list:
        risk = min(2000.0, float(spec["mll"]))
        win = EVAL_R * risk
        coin50 = np.where(np.random.default_rng(1).random(4000) < 0.50, win, -risk)
        walk = np.where(np.random.default_rng(2).random(4000) < WALK_HIT_075, win, -risk)
        small = np.where(np.random.default_rng(3).random(4000) < 0.50, 500.0, -500.0)
        baselines.append({
            "firm": spec["firm"],
            "coin50": eval_stats(coin50, spec, 21),
            "walk": eval_stats(walk, spec, 22),
            "small": eval_stats(small, spec, 23),
        })
    lives = []
    months = []
    touched: dict[str, dict] = {}
    missed: dict[tuple, dict] = {}

    def _touch(item: dict, reward: float) -> dict:
        key = (item["name"], reward, False)
        if key not in touched:
            rows = run_variant(
                sessions, item["level"], item["style"], item["filt"], False, reward, count_missed=True,
            )
            touched[key] = pack(_period(rows, VAL_END, None))
        return touched[key]

    def _miss(item: dict, reward: float) -> dict:
        key = (item["name"], reward)
        if key not in missed:
            rows = run_variant(
                sessions, item["level"], item["style"], item["filt"], True, reward, count_missed=True,
            )
            missed[key] = pack(_period(rows, VAL_END, None))
        return missed[key]

    for spec in firm_list:
        _score, item, val_stat = chosen[spec["firm"]]
        risk = min(2000.0, float(spec["mll"]))
        ev_hold = _period(item["eval"], VAL_END, None)
        fu_hold = _period(funded_winner["funded"], VAL_END, None)
        ev_day = day_dollars(ev_hold, risk, spec["rate"])
        fu_filled = [row for row in fu_hold if row["filled"]]
        fu_day = day_dollars(fu_filled, risk, spec["rate"])
        hold_stat = eval_stats(ev_day, spec, 31)
        four = stack_smaller(ev_day, 4, np.random.default_rng(32))
        four_stat = eval_stats(four, spec, 33)
        grind_p = _finite(item["ev_hold_pack"]["hit"], 0.0)
        life = lifecycle(ev_day, fu_day, grind_p, spec, np.random.default_rng(40), n=1500)
        month = month_at_cap(
            ev_day, fu_day, grind_p, spec, np.random.default_rng(41), n=400,
            fill_rate=_finite(funded_winner["fu_hold_pack"]["fill"], 0.0),
        )
        miss_pack = _miss(item, EVAL_R)
        lives.append({
            "firm": spec["firm"],
            "eval_name": item["name"],
            "funded_name": funded_winner["name"],
            "hold": hold_stat,
            "four": four_stat,
            "val": val_stat,
            "life": life,
            "month": month,
            "eval_hit": item["ev_hold_pack"]["hit"],
            "eval_val_hit": item["ev_val_pack"]["hit"],
            "eval_val_n": item["ev_val_pack"]["n"],
            "eval_n": item["ev_hold_pack"]["n"],
            "eval_fill": item["ev_hold_pack"]["fill"],
            "eval_miss": miss_pack["miss"],
            "eval_mean": item["ev_hold_pack"]["mean"],
            "grind_p": grind_p,
            "risk": risk,
            "rate_note": spec["rate_note"],
            "fee_assumed": spec["fee_assumed"],
            "touch": _touch(item, EVAL_R),
        })
        mean = float(month.mean())
        lo, hi = _ci(mean, month)
        slots, note = month_plan(spec)
        months.append({
            "firm": spec["firm"],
            "mean": mean,
            "lo": lo,
            "hi": hi,
            "p_neg": float(np.mean(month < 0)),
            "slots": slots,
            "note": note,
            "funded_cap": spec["funded_cap"],
        })
        print("life", spec["firm"], round(life["mean"], 1), "pass", round(hold_stat["pass"], 3), flush=True)
    funded_touch = _touch(funded_winner, FUNDED_R)
    funded_miss = _miss(funded_winner, FUNDED_R)
    funded_r = mean_r_ci(_period(funded_winner["funded"], VAL_END, None))
    # Eval mean R is the same trade list for every firm when they share a setup.
    for row in lives:
        chosen_item = next(item for p, item, stat in ranked[row["firm"]] if item["name"] == row["eval_name"])
        row["eval_r_ci"] = mean_r_ci(_period(chosen_item["eval"], VAL_END, None))
    passes = [0.20, 0.30, 0.40, 0.50, 0.60]
    hits = [0.30, 0.37, 0.45, 0.50, 0.60]
    grid = []
    for spec in firm_list:
        for p_pass in passes:
            for p_hit in hits:
                grid.append({
                    "firm": spec["firm"],
                    "pass": p_pass,
                    "hit": p_hit,
                    "ev": grid_value(spec, p_pass, p_hit),
                })
    text = render(
        catalog, chosen, funded_winner, baselines, lives, months, grid, firm_list,
        reference, funded_touch, funded_miss, funded_r,
    )
    OUT.write_text(text)
    print("wrote", OUT, flush=True)


def render(
    catalog, chosen, funded_winner, baselines, lives, months, grid, firm_list,
    reference, funded_touch, funded_miss, funded_r,
) -> str:
    lines = [
        "# Limit-entry research",
        "",
        "Disarmed. Nothing here places an order. Eval and funded are two different setups, and each one was chosen on the validation window (1 July 2024 through 30 June 2025) before the holdout from 1 July 2025 was opened. The eval search ranks by pass rate. The funded search ranks by the share of fills that hit a 1.7:1 target before the stop. The holdout scores those choices once. It is not a second search.",
        "",
        "The eval book is allowed to lose money per trade. Its job is to pass. A target of 0.75R needs about a 57% hit rate before costs, and about 60% at a 16-point stop after the MNQ commission and one tick of stop slippage, just to break even on the trade. The funded book is the opposite shape: $3,400 against a $2,000 stop where the max loss is $2,000, and $2,550 against a $1,500 stop on FundedNext, whose max loss is $1,500. A random path hits 1.7R about 37% of the time. Fifty percent would be an edge. The earlier ±$500 coin passes a Topstep combine about 26% of the time. That 26% figure is a different payoff, so a 0.75R book can beat it with no edge at all.",
        "",
        "There are 64 limit variants. Ranking all of them and then quoting the winner's validation p-value would overstate the result. The holdout of the single validation winner is the check that accounts for the search.",
        "",
        "## Fills",
        "",
        "The order is live only on a bar after the level was known. Trade-through, which is the rule that chooses the setups: a buy fills at the limit only if the low is at least one tick through it, and the bar did not open already through it. A gap through the limit is not a fill. Touch-fill is reported afterwards, only for the chosen setups, and it is not allowed to change the choice. The stop is a market order, one tick worse, and it is checked before the target on the same bar. The target is a limit at its price, with no extra slippage. Research R subtracts Topstep's MNQ $1.22 from the points. The lifecycle uses each firm's own card. FundedNext does not print an MNQ rate, so that row is charged $1.22 and labelled. Lucid's card is $0.50 per side, $1.00 round turn.",
        "",
        "Levels: prior-day high and low, prior settle, overnight high and low as of 09:30, the 5-minute opening range, the 30-minute opening range, the 60-minute initial balance, VWAP plus or minus one ATR taken from the 09:34 bar and first eligible at 09:35, and the 100-point rounds around the open, first eligible at 09:31. Fade rests both sides and takes the first fill. If both sides fill on the same bar, there is no trade. Pullback rests only the side of the open versus the prior settle. Filters: none; skip a session whose overnight range is wider than the prior day's range; a gap rule that turns fades off and pullbacks on when the open is more than 30% of the prior day's range away from the settle; a hot-open rule, known only after 10:00, that does the same when the first 30 minutes are wider than their prior-20 median or heavier than 1.5 times that volume median. The stop is the maximum of 8 points and 10% of the prior day's range, and no wider than 80.",
        "",
        "## Eval: pass rate",
        "",
        "One trade a day. The stop risks the account's max loss, and no more than $2,000. The target is 0.75 of that risk: $1,500 where the max loss is $2,000, and $1,125 on FundedNext. A variant needs at least 80 validation fills to be ranked. The winner for each firm is the highest validation pass rate. Days to pass are the mean among the paths that passed, inside a 40-day horizon.",
        "",
        "The interval on a pass rate is the simulation error from 1,500 resamples of the recorded days. Those days are treated as the true distribution. The interval does not add a second layer of uncertainty for the size of the holdout.",
        "",
        "| firm | chosen on validation | val pass | val days | holdout pass | holdout days | holdout fills | holdout hit | fill rate | missed winners | mean R |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    a = lines.append
    for row in lives:
        a(
            f"| {row['firm']} | {row['eval_name']} | {pct(row['val']['pass'])} | {days_s(row['val']['days'])} | "
            f"{pct(row['hold']['pass'])} ({pct(row['hold']['lo'])} to {pct(row['hold']['hi'])}) | "
            f"{days_s(row['hold']['days'])} | {row['eval_n']} | {pct(row['eval_hit'])} | {pct(row['eval_fill'])} | "
            f"{pct(row['eval_miss'])} | {_num(row['eval_mean'])} |"
        )
    a("")
    a(
        f"`{REFERENCE}` was named before the ranking. It is not the selection unless it also won the validation pass rate."
    )
    a("")
    a("| firm | reference val pass | reference val days |")
    a("|---|---:|---:|")
    for spec in firm_list:
        _p, stat, _item = reference[spec["firm"]]
        a(f"| {spec['firm']} | {pct(stat['pass'])} | {days_s(stat['days'])} |")
    a("")
    a(
        "Four smaller trades, each one quarter of the size. Each copy is an independent draw from the same holdout days, not a second setup and not four fills from one session. It shows what the pass rate would do if four uncorrelated copies of this one edge existed. That was not found, and it was not used to choose."
    )
    a("")
    a("| firm | four-trade holdout pass | days |")
    a("|---|---:|---:|")
    for row in lives:
        a(
            f"| {row['firm']} | {pct(row['four']['pass'])} ({pct(row['four']['lo'])} to {pct(row['four']['hi'])}) | "
            f"{days_s(row['four']['days'])} |"
        )
    a("")
    a(
        "Same simulator, no limit signal. `50% on the 0.75R payoff` wins 0.75 of the stop or loses the stop, half the time. That hit rate is worse than a no-drift path, which touches 0.75R before the stop about "
        f"{pct(WALK_HIT_075)} of the time. `Random-walk 0.75R` uses that {pct(WALK_HIT_075)} rate and the same dollar payoff, with no commission. "
        "`±$500` is the earlier small-step coin. On Topstep that coin is the roughly 26% baseline. Beating it does not mean the limit has an edge."
    )
    a("")
    a("| firm | 50% on 0.75R | random-walk 0.75R | ±$500 coin |")
    a("|---|---:|---:|---:|")
    for row in baselines:
        a(
            f"| {row['firm']} | {pct(row['coin50']['pass'])} in {days_s(row['coin50']['days'])} days | "
            f"{pct(row['walk']['pass'])} in {days_s(row['walk']['days'])} days | "
            f"{pct(row['small']['pass'])} in {days_s(row['small']['days'])} days |"
        )
    a("")
    a("## Funded: 1.7:1 hit rate")
    a("")
    a(
        f"The validation winner is `{funded_winner['name']}`. Hit rate is target-before-stop among fills. "
        f"The random-walk line is {pct(RANDOM_HIT_17)}. The p-value is a one-sided normal test against that line, "
        "for this one holdout. It is not a corrected p-value across the 64 variants. The validation p-value is there so the ranking can be checked."
    )
    a("")
    fv, fh = funded_winner["fu_val_pack"], funded_winner["fu_hold_pack"]
    vt, ht = funded_winner["fu_val_test"], funded_winner["fu_hold_test"]
    a(
        f"- Validation: n={fv['n']}, hit {pct(vt['hit'])} ({pct(vt['lo'])} to {pct(vt['hi'])}), "
        f"p vs 37% {vt['p']:.3f}, fill {pct(fv['fill'])}, mean R {_num(fv['mean'])}."
    )
    a(
        f"- Holdout: n={fh['n']}, hit {pct(ht['hit'])} ({pct(ht['lo'])} to {pct(ht['hi'])}), "
        f"p vs 37% {ht['p']:.3f}, fill {pct(fh['fill'])}, missed winners {pct(funded_miss['miss'])}, "
        f"mean R {_num(funded_r[0])} ({_num(funded_r[1])} to {_num(funded_r[2])})."
    )
    a(
        f"- Touch-fill holdout of this funded winner, not used to choose: hit {pct(funded_touch['hit'])}, "
        f"mean R {_num(funded_touch['mean'])}, fill {pct(funded_touch['fill'])}, n={funded_touch['n']}."
    )
    a("")
    a("Touch-fill holdout of each firm's eval winner, also not used to choose.")
    a("")
    a("| firm | eval setup | touch hit | touch mean R | touch fill |")
    a("|---|---|---:|---:|---:|")
    for row in lives:
        t = row["touch"]
        a(f"| {row['firm']} | {row['eval_name']} | {pct(t['hit'])} | {_num(t['mean'])} | {pct(t['fill'])} |")
    a("")
    a(
        "Highest validation hit rates, whether or not the row had enough fills to be chosen. "
        "A row needed 100 validation fills. Holdout is shown beside them and was not the sort key."
    )
    a("")
    a("| variant | val n | val hit | val p vs 37% | hold n | hold hit | hold mean R |")
    a("|---|---:|---:|---:|---:|---:|---:|")
    top = sorted(catalog, key=_hit_key, reverse=True)[:12]
    for row in top:
        a(
            f"| {row['name']} | {row['fu_val_pack']['n']} | {pct(row['fu_val_pack']['hit'])} | {row['fu_val_test']['p']:.3f} | "
            f"{row['fu_hold_pack']['n']} | {pct(row['fu_hold_pack']['hit'])} | {_num(row['fu_hold_pack']['mean'])} |"
        )
    a("")
    a("## One lifecycle")
    a("")
    a(
        "Each row is one eval purchase. The eval days are the holdout of that firm's validation winner, sized to its max loss, and a day with no fill is a zero. "
        "The big funded day is one filled holdout trade from the funded winner, sized the same way. A day that never fills is not treated as a finished attempt. "
        "On the 21-day clock, the account waits and tries again. "
        "The following days, up to the firm's count of winning days, use the eval setup's holdout target-hit rate: a win is booked at the firm's minimum winning day, and a loss is that amount divided by 0.75. "
        "No extra commission is added on those small days. Then the firm's payout rule, including the cap, the split, the buffer, and the stated intraday or end-of-day breach. "
        "Lucid's fee is the assumed $100. A passed Topstep combine also pays the $149 activation. "
        "Topstep does not cap the number of payouts. The sim stops after eight."
    )
    a("")
    a("| firm | eval setup | funded setup | stop sized to | grind hit | holdout pass | EV per eval | payouts / 100 |")
    a("|---|---|---|---:|---:|---:|---|---:|")
    for row in lives:
        life = row["life"]
        a(
            f"| {row['firm']} | {row['eval_name']} | {row['funded_name']} | {money(row['risk'])} | {pct(row['grind_p'])} | "
            f"{pct(row['hold']['pass'])} | {money(life['mean'])} ({money(life['lo'])} to {money(life['hi'])}) | "
            f"{life['payouts_per_100']:.1f} |"
        )
    a("")
    for row in lives:
        notes = []
        if row["fee_assumed"]:
            notes.append("the fee is an assumed $100; the help centre does not print it")
        if row["firm"].startswith("FundedNext"):
            notes.append(row["rate_note"])
        if notes:
            a(f"{row['firm']}: " + ". ".join(notes) + ".")
    a("")
    a("## Monthly cash flow")
    a("")
    a(
        "A month is 21 trading days. Every evaluation the cap allows is opened on day one and its fee is charged then. "
        "A failure is not replaced, because the cap is already used. A pass converts to a funded account only while the funded count is under the firm's cap, and it does not trade on the day it passes. "
        "Payouts are only the ones that clear inside the 21 days. EV per eval, above, is the full life of the account and can run past the month. "
        "P(month negative) is the share of 400 households whose 21-day net is below zero."
    )
    a("")
    a("| firm | evals opened | funded cap | mean month | 95% CI | P(month negative) |")
    a("|---|---:|---:|---:|---|---:|")
    for row in months:
        a(
            f"| {row['firm']} | {row['slots']} | {row['funded_cap']} | {money(row['mean'])} | "
            f"{money(row['lo'])} to {money(row['hi'])} | {pct(row['p_neg'])} |"
        )
    a("")
    for row in months:
        a(f"- {row['firm']}: {row['note']}")
    a("")
    a("## What each improvement is worth")
    a("")
    a(
        "Rows are the eval pass rate. Columns are the funded 1.7:1 hit rate. The cell is the exact expected value of one eval under a one-cycle model, not a sample. "
        "Fail, and you lose the fee. Pass, and you pay the activation. The big day then either busts the account or, if it hits, four minimum winning days are assumed to finish and one payout is taken. "
        "A winning big day pays the firm's commission on a 16-point stop sized to the max loss. A losing big day also pays one tick of stop slippage. The four small days are assumed, not simulated, so a grind that would have busted the account is not in this grid. "
        "Lucid's fee is the assumed $100. Read a cell as: this pass rate and this hit rate are worth this many dollars per eval, before any second payout."
    )
    a("")
    passes = [0.20, 0.30, 0.40, 0.50, 0.60]
    hits = [0.30, 0.37, 0.45, 0.50, 0.60]
    for spec in firm_list:
        a(f"### {spec['firm']}")
        a("")
        a("| pass \\ hit | " + " | ".join(pct(h) for h in hits) + " |")
        a("|---|" + "---:|" * len(hits))
        for p_pass in passes:
            cells = []
            for p_hit in hits:
                ev = next(
                    g["ev"] for g in grid
                    if g["firm"] == spec["firm"] and g["pass"] == p_pass and g["hit"] == p_hit
                )
                cells.append(money(ev))
            a(f"| {pct(p_pass)} | " + " | ".join(cells) + " |")
        a("")
    a("## Verdict")
    a("")
    a(_verdict(lives, funded_winner, baselines, funded_r))
    a("")
    return "\n".join(lines) + "\n"


def _clears(lo: float, bar: float) -> bool:
    return isinstance(lo, float) and not math.isnan(lo) and lo > bar


def _verdict(lives, funded_winner, baselines, funded_r) -> str:
    ht = funded_winner["fu_hold_test"]
    parts = [
        (
            f"The funded winner `{funded_winner['name']}` holdout hit rate is {pct(ht['hit'])} "
            f"({pct(ht['lo'])} to {pct(ht['hi'])})."
        )
    ]
    if _clears(ht["lo"], RANDOM_HIT_17):
        parts.append("That interval sits above the 37% random-walk line.")
    else:
        parts.append(
            "That interval does not sit above the 37% random-walk line, so a 50% hit on the 1.7:1 funded day was not found."
        )
    if _clears(funded_r[1], 0.0):
        parts.append(
            f"Holdout mean R is {_num(funded_r[0])} ({_num(funded_r[1])} to {_num(funded_r[2])}), above zero."
        )
    elif isinstance(funded_r[2], float) and not math.isnan(funded_r[2]) and funded_r[2] < 0:
        parts.append(
            f"Holdout mean R is {_num(funded_r[0])} ({_num(funded_r[1])} to {_num(funded_r[2])}), below zero."
        )
    else:
        parts.append(
            f"Holdout mean R is {_num(funded_r[0])} ({_num(funded_r[1])} to {_num(funded_r[2])}). That interval covers zero."
        )
    names = {row["eval_name"] for row in lives}
    if len(names) == 1:
        row = lives[0]
        ph = float(row["eval_hit"])
        n = int(row["eval_n"])
        se = math.sqrt(ph * (1.0 - ph) / n) if n else float("nan")
        lo, hi = ph - 1.96 * se, ph + 1.96 * se
        parts.append(
            f"The eval search was allowed to return a negative-R book. `{row['eval_name']}` is not one. "
            f"Its 0.75R holdout hit rate is {pct(ph)} ({pct(lo)} to {pct(hi)}) on {n} fills, "
            f"against {pct(WALK_HIT_075)} for a no-drift path and about 60% to break even after commission and one tick of stop slippage. "
            f"Holdout mean R is {_num(row['eval_r_ci'][0])} ({_num(row['eval_r_ci'][1])} to {_num(row['eval_r_ci'][2])}). "
            f"Validation hit was {pct(row['eval_val_hit'])} on {row['eval_val_n']} fills. "
            + (
                "The same variant won the funded ranking."
                if row["eval_name"] == funded_winner["name"]
                else "The funded ranking chose a different variant."
            )
        )
    by_base = {row["firm"]: row for row in baselines}
    for row in lives:
        base = by_base[row["firm"]]
        small = base["small"]["pass"]
        walk = base["walk"]["pass"]
        sentence = (
            f"{row['firm']} holdout pass {pct(row['hold']['pass'])} "
            f"({pct(row['hold']['lo'])} to {pct(row['hold']['hi'])}), "
            f"against the ±$500 coin at {pct(small)} and the random-walk 0.75R book at {pct(walk)}."
        )
        if _clears(row["hold"]["lo"], small):
            sentence += " The interval clears the ±$500 coin."
        else:
            sentence += " The interval does not clear the ±$500 coin."
        if _clears(row["hold"]["lo"], walk):
            sentence += " It also clears the random-walk 0.75R book."
        else:
            sentence += " It does not clear the random-walk 0.75R book, which is the fair comparison for this payoff."
        life = row["life"]
        if _clears(life["lo"], 0.0):
            sentence += f" Lifecycle EV is {money(life['mean'])}, and that interval is above zero."
        elif isinstance(life["hi"], float) and not math.isnan(life["hi"]) and life["hi"] < 0:
            sentence += f" Lifecycle EV is {money(life['mean'])}, and that interval is below zero."
        else:
            sentence += f" Lifecycle EV is {money(life['mean'])}, and the interval covers zero."
        parts.append(sentence)
    parts.append(
        "The lifecycle dollar interval resamples those recorded days. It is not a second test of the 1.7:1 hit rate against 37%."
    )
    return " ".join(parts)


if __name__ == "__main__":
    main()


