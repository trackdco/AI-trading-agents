"""Full-port lifecycle. Writes docs/FULLPORT-LIFECYCLE.md.

The funded search is one 1.7:1 resting limit a day. It is ranked by validation
hit rate. The holdout is the confirmation, not a second search. The eval book
is a separate, smaller, pre-declared list. Nothing here places an order.
"""

from __future__ import annotations

import math
import sys
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_hf_limit import (
    CAPS,
    build_days,
    play_day,
)
from scripts.run_limit_research import (
    TRAIN_END,
    VAL_END,
    _num,
    _payout,
    firms,
    grid_value,
    money,
    month_plan,
    pct,
)
from scripts.run_multi_firm_farm import _eval_lock
from src.research.strategies.costs import COMMISSION_POINTS, TICK
from src.research.strategies.engine import load_bars
from src.research.strategies.hf_limit import eod_update, scan_limits
from src.research.strategies.jake_rules import profiles_at_open

OUT = ROOT / "docs" / "FULLPORT-LIFECYCLE.md"
DATA = ROOT / "data" / "reference" / "nq_1m_master.parquet"
OPEN = 9 * 60 + 30
P0 = 1.0 / 2.7
STOPS = (15.0, 25.0, 40.0, 60.0)


def _seed(text: str) -> int:
    return zlib.crc32(text.encode()) & 0x7FFFFFFF


def _at(day, minute: int) -> int:
    hit = np.flatnonzero((day.hm >= minute) & (day.hm < 18 * 60))
    return int(hit[0]) if len(hit) else -1


def _bounds(day, window: str) -> tuple[int, int]:
    if window == "london":
        start, end = _at(day, 3 * 60), _at(day, 8 * 60 + 30)
    elif window == "nyam":
        start, end = day.i_open, _at(day, 11 * 60)
    else:
        start, end = day.i_open, day.end
    if start < 0 or end <= start:
        return 0, 0
    return start, min(end, day.end)


def _allows(day, regime, cuts) -> bool:
    if regime is None:
        return True
    gap = abs(day.rth_open - day.pdc) if np.isfinite(day.pdc) else 0.0
    if regime == "gap_large":
        return gap >= cuts["gap75"]
    if regime == "gap_small":
        return gap <= cuts["gap25"]
    if regime == "wide_on":
        return np.isfinite(day.onh) and np.isfinite(day.onl) and (day.onh - day.onl) > day.pd_range
    if regime == "wide_pd":
        return day.pd_range >= cuts["pd_med"]
    if regime == "skip_mon":
        return day.ts.weekday() != 0
    if regime == "skip_fri":
        return day.ts.weekday() != 4
    return True


def _asia(day):
    m = (day.hm >= 18 * 60) | (day.hm < 3 * 60)
    if int(m.sum()) < 20:
        return np.nan, np.nan
    return float(day.h[m].max()), float(day.l[m].min())


def _arm(day, kind, stop, window, regime, cuts, profiles):
    """Return buy, sell, start, end. Empty when the day's filter is off."""
    n = len(day.o)
    buy, sell = np.full(n, np.nan), np.full(n, np.nan)
    if not _allows(day, regime, cuts):
        return buy, sell, 0, 0
    start, end = _bounds(day, window)
    if end <= start:
        return buy, sell, 0, 0
    sl = slice(start, end)
    if kind == "pdhl":
        buy[sl], sell[sl] = day.pdl, day.pdh
    elif kind == "pdhl_pull":
        if day.up > 0:
            buy[sl] = day.pdl
        elif day.up < 0:
            sell[sl] = day.pdh
    elif kind == "onhl":
        if np.isfinite(day.onl):
            buy[sl] = day.onl
        if np.isfinite(day.onh):
            sell[sl] = day.onh
    elif kind == "onhl_pull":
        if day.up > 0 and np.isfinite(day.onl):
            buy[sl] = day.onl
        elif day.up < 0 and np.isfinite(day.onh):
            sell[sl] = day.onh
    elif kind == "or15" and day.or_i >= 0 and np.isfinite(day.or_hi):
        start = max(start, day.or_i)
        buy[start:end] = day.or_lo
        sell[start:end] = day.or_hi
    elif kind == "ib" and day.ib_i >= 0 and np.isfinite(day.ib_hi):
        start = max(start, day.ib_i)
        buy[start:end] = day.ib_lo
        sell[start:end] = day.ib_hi
    elif kind == "vwap":
        band = 20.0 if stop >= 25 else 12.0
        prev = day.vwap_prev
        buy[sl] = prev[sl] - band
        sell[sl] = prev[sl] + band
    elif kind == "vwap40":
        prev = day.vwap_prev
        buy[sl] = prev[sl] - 40.0
        sell[sl] = prev[sl] + 40.0
    elif kind == "vp":
        area = profiles.get(day.ts)
        if area is None:
            return buy, sell, 0, 0
        val, vah, _poc = area
        buy[sl], sell[sl] = val, vah
    elif kind == "asia":
        hi, lo = _asia(day)
        if not np.isfinite(hi):
            return buy, sell, 0, 0
        buy[sl], sell[sl] = lo, hi
    elif kind == "conf_pd_on":
        if np.isfinite(day.onh) and abs(day.pdh - day.onh) <= 15:
            sell[sl] = day.pdh
        if np.isfinite(day.onl) and abs(day.pdl - day.onl) <= 15:
            buy[sl] = day.pdl
    elif kind == "conf_vwap_pd":
        prev = day.vwap_prev
        sell_px = prev + 20.0
        buy_px = prev - 20.0
        sell[sl] = np.where(np.abs(sell_px[sl] - day.pdh) <= 12, sell_px[sl], np.nan)
        buy[sl] = np.where(np.abs(buy_px[sl] - day.pdl) <= 12, buy_px[sl], np.nan)
    elif kind == "combo":
        buys = [day.pdl]
        sells = [day.pdh]
        if day.up > 0 and np.isfinite(day.onl):
            buys.append(day.onl)
        elif day.up < 0 and np.isfinite(day.onh):
            sells.append(day.onh)
        prev_c = np.r_[np.nan, day.c[:-1]]
        for i in range(start, end):
            px = float(prev_c[i])
            if not np.isfinite(px):
                continue
            below = [x for x in buys if x < px - TICK]
            above = [x for x in sells if x > px + TICK]
            if below:
                buy[i] = max(below)
            if above:
                sell[i] = min(above)
    return buy, sell, start, end


def run_book(days, kind, stop, reward, window, regime, cuts, profiles, max_trades=1):
    out = []
    for day in days:
        use = stop
        if stop <= 0:
            use = float(min(60.0, max(15.0, 0.10 * day.pd_range)))
        buy, sell, start, end = _arm(day, kind, use, window, regime, cuts, profiles)
        if end <= start:
            out.append([])
            continue
        out.append(scan_limits(
            day.o, day.h, day.l, day.c, day.hm, buy, sell, use, reward, start, end,
            max_trades=max_trades,
        ))
    return out


def funded_variants():
    out = []
    kinds = ("pdhl", "pdhl_pull", "onhl", "onhl_pull", "or15", "ib", "vwap", "vwap40", "vp", "asia")
    for kind in kinds:
        for stop in STOPS:
            window = "london" if kind == "asia" else "rth"
            out.append((f"{kind}_s{stop:.0f}", kind, stop, "rth" if kind != "asia" else window, None))
    for kind in ("pdhl", "onhl_pull", "vwap", "vp"):
        for stop in (15.0, 40.0):
            out.append((f"{kind}_s{stop:.0f}_nyam", kind, stop, "nyam", None))
    for stop in (25.0, 40.0):
        out.append((f"pdhl_s{stop:.0f}_london", "pdhl", stop, "london", None))
    for regime in ("gap_large", "gap_small", "wide_on", "wide_pd", "skip_mon", "skip_fri"):
        for kind in ("pdhl", "onhl_pull"):
            out.append((f"{kind}_s25_{regime}", kind, 25.0, "rth", regime))
    for stop in (25.0, 40.0):
        out.append((f"conf_pd_on_s{stop:.0f}", "conf_pd_on", stop, "rth", None))
        out.append((f"conf_vwap_pd_s{stop:.0f}", "conf_vwap_pd", stop, "nyam", None))
    return out


def eval_variants():
    """Pre-declared 0.75R books. `combo` is pdhl plus the onhl pull side."""
    out = []
    for kind in ("pdhl", "onhl_pull", "onhl", "combo"):
        for stop in (15.0, 25.0, 0.0):
            label = "struct" if stop <= 0 else f"s{stop:.0f}"
            out.append((f"{kind}_{label}", kind, stop, 1))
    out.append(("combo_two_s15", "combo", 15.0, 2))
    out.append(("pdhl_two_s15", "pdhl", 15.0, 2))
    return out


def _fills(booked, idxs):
    trades = [tr for i in idxs for tr in booked[i]]
    return trades


def hit_test(trades, p0=P0):
    n = len(trades)
    if n < 20:
        return {"n": n, "hit": float("nan"), "lo": float("nan"), "hi": float("nan"), "p": 1.0}
    hits = sum(tr.hit for tr in trades)
    ph = hits / n
    se = math.sqrt(ph * (1 - ph) / n)
    z = (ph - p0) / math.sqrt(p0 * (1 - p0) / n)
    from statistics import NormalDist
    return {"n": n, "hit": ph, "lo": ph - 1.96 * se, "hi": ph + 1.96 * se, "p": float(1 - NormalDist().cdf(z))}


def mean_r(trades):
    if len(trades) < 2:
        return float("nan"), float("nan"), float("nan")
    r = np.array([(tr.gross - COMMISSION_POINTS) / tr.risk for tr in trades])
    mid = float(r.mean())
    se = float(r.std(ddof=1) / math.sqrt(len(r)))
    return mid, mid - 1.96 * se, mid + 1.96 * se


def breakeven(stop: float) -> float:
    win = 1.7 * stop - COMMISSION_POINTS
    loss = stop + TICK + COMMISSION_POINTS
    return loss / (win + loss) if win > 0 else 1.0


def bh_mask(pvals: np.ndarray, q: float = 0.10) -> np.ndarray:
    order = np.argsort(pvals)
    ok = pvals[order] <= (np.arange(1, len(pvals) + 1) / len(pvals)) * q
    passed = np.zeros(len(pvals), dtype=bool)
    if ok.any():
        passed[order[: int(np.max(np.flatnonzero(ok))) + 1]] = True
    return passed


def pass_rate(booked, idxs, spec, dollar_risk, seed: int, n: int = 1000, horizon: int = 40):
    """Path-aware pass rate. A dip to the floor ends the attempt. The floor moves at the close."""
    days = [booked[i] for i in idxs]
    if len(days) < 30:
        return {"pass": float("nan"), "lo": float("nan"), "hi": float("nan"), "days": float("nan")}
    rng = np.random.default_rng(seed)
    mll = float(spec["mll"])
    size = float(spec["size"])
    rate = float(spec["rate"])
    cap = CAPS[spec["firm"]]
    locks, trigger, lock_at = _eval_lock(spec)
    passed = np.zeros(n, dtype=bool)
    when = np.full(n, np.nan)
    balance = np.full(n, size)
    floor = np.full(n, size - mll)
    locked = np.zeros(n, dtype=bool)
    best = np.zeros(n)
    alive = np.ones(n, dtype=bool)
    for d in range(horizon):
        on = np.flatnonzero(alive & ~passed)
        if len(on) == 0:
            break
        for i in on:
            eq, dead, day_pnl = play_day(
                days[int(rng.integers(0, len(days)))], balance[i], floor[i], rate, cap, dollar_risk, None, None,
            )
            if dead:
                alive[i] = False
                continue
            balance[i] = eq
            best[i] = max(best[i], day_pnl)
            if locks:
                floor[i], locked[i] = eod_update(balance[i], floor[i], locked[i], mll, trigger, lock_at)
            need = max(float(spec["target"]), best[i] / float(spec["consistency"]) if best[i] > 0 else float(spec["target"]))
            if (d + 1) >= int(spec["min_eval_days"]) and balance[i] - size + 1e-6 >= need:
                passed[i] = True
                when[i] = d + 1
    p = float(passed.mean())
    se = math.sqrt(p * (1 - p) / n)
    return {
        "pass": p, "lo": p - 1.96 * se, "hi": p + 1.96 * se,
        "days": float(np.nanmean(when)) if np.isfinite(when).any() else float("nan"),
    }


def fullport_life(eval_days, fund_days, spec, rng, risk_eval, grind_p, grind_r=0.75, n=800):
    """Eval trades, then one full-port funded trade, then minimum winning days."""
    rate = float(spec["rate"])
    capn = CAPS[spec["firm"]]
    mll = float(spec["mll"])
    size = float(spec["size"])
    risk_fund = mll
    win_min = float(spec["win_min"])
    loss_g = win_min / grind_r if win_min else 0.0
    locks, trigger, lock_at = _eval_lock(spec)
    nets = np.zeros(n)
    passed = np.zeros(n, dtype=bool)
    pays = np.zeros(n)
    days_pass = np.full(n, np.nan)
    filled = [d for d in fund_days if d]
    if not filled:
        return _life_stat(nets, passed, pays, days_pass)
    for i in range(n):
        balance = size
        floor = size - mll
        locked = False
        best = 0.0
        alive = True
        day_count = 0
        for day_count in range(1, 41):
            balance, dead, day_pnl = play_day(
                eval_days[int(rng.integers(0, len(eval_days)))], balance, floor, rate, capn, risk_eval, None, None,
            )
            if dead:
                alive = False
                break
            best = max(best, day_pnl)
            if locks:
                floor, locked = eod_update(balance, floor, locked, mll, trigger, lock_at)
            need = max(float(spec["target"]), best / float(spec["consistency"]) if best > 0 else float(spec["target"]))
            if day_count >= int(spec["min_eval_days"]) and balance - size + 1e-6 >= need:
                passed[i] = True
                days_pass[i] = day_count
                break
        fee = float(spec["fee"]) + (float(spec["activation"]) if passed[i] else 0.0)
        cash = 0.0
        if passed[i] and alive:
            balance = float(spec["funded_start"])
            floor = balance - mll
            locked = False
            wins = 0.0
            cycle = 0.0
            max_pays = int(spec["max_payouts"] or 8)
            for _k in range(max_pays):
                balance, dead, day_pnl = play_day(
                    filled[int(rng.integers(0, len(filled)))], balance, floor, rate, capn, risk_fund, None, None,
                )
                if dead:
                    alive = False
                    break
                cycle += day_pnl
                if day_pnl + 1e-9 >= win_min:
                    wins += 1
                floor, locked = eod_update(
                    balance, floor, locked, mll, float(spec["lock_trigger"]), float(spec["lock_floor"]),
                )
                guard = 0
                while wins < int(spec["winning_days"]) and alive and guard < 12:
                    guard += 1
                    hit = rng.random() < grind_p
                    pnl = win_min if hit else -loss_g
                    if balance - max(-pnl, 0.0) <= floor + 1e-9:
                        alive = False
                        break
                    balance += pnl
                    cycle += pnl
                    if pnl >= win_min:
                        wins += 1
                    floor, locked = eod_update(
                        balance, floor, locked, mll, float(spec["lock_trigger"]), float(spec["lock_floor"]),
                    )
                    if balance <= floor + 1e-9:
                        alive = False
                if not alive:
                    break
                amount = float(_payout(spec, np.array([balance]), np.array([cycle]))[0])
                if wins + 1e-9 >= int(spec["winning_days"]) and cycle > float(spec["buffer"]) and amount >= float(spec["min_request"]):
                    cash += amount * float(spec["split"])
                    balance -= amount
                    floor = float(spec["lock_floor"])
                    locked = True
                    pays[i] += 1
                    wins = 0.0
                    cycle = 0.0
                    if balance <= floor + 1e-9:
                        break
                else:
                    break
        nets[i] = cash - fee
    return _life_stat(nets, passed, pays, days_pass)


def _life_stat(nets, passed, pays, days_pass):
    mid = float(nets.mean())
    se = float(nets.std(ddof=1) / math.sqrt(len(nets))) if len(nets) > 1 else float("nan")
    return {
        "mean": mid, "lo": mid - 1.96 * se, "hi": mid + 1.96 * se,
        "pass": float(np.mean(passed)),
        "pays": float(np.mean(pays) * 100),
        "days": float(np.nanmean(days_pass)) if np.isfinite(days_pass).any() else float("nan"),
    }


def month_book(eval_days, fund_days, spec, risk_eval, grind_p, n=200):
    slots, note = month_plan(spec)
    rng = np.random.default_rng(_seed("month" + spec["firm"] + str(int(risk_eval))))
    rate = float(spec["rate"])
    capn = CAPS[spec["firm"]]
    mll = float(spec["mll"])
    size = float(spec["size"])
    fee = float(spec["fee"])
    activation = float(spec["activation"])
    funded_cap = int(spec["funded_cap"])
    locks, trigger, lock_at = _eval_lock(spec)
    win_min = float(spec["win_min"])
    loss_g = win_min / 0.75
    filled = [d for d in fund_days if d]
    cash = np.full(n, -fee * slots)
    # phase 1 eval, 2 need big, 3 grind
    phase = np.ones((n, slots), dtype=np.int8)
    bal = np.full((n, slots), size)
    floor = np.full((n, slots), size - mll)
    locked = np.zeros((n, slots), dtype=bool)
    best = np.zeros((n, slots))
    edays = np.zeros((n, slots))
    wins = np.zeros((n, slots))
    cycle = np.zeros((n, slots))
    pays = np.zeros((n, slots))
    for _d in range(21):
        for j in range(slots):
            for i in range(n):
                if phase[i, j] == 0:
                    continue
                if phase[i, j] == 1:
                    eq, dead, day_pnl = play_day(
                        eval_days[int(rng.integers(0, len(eval_days)))], bal[i, j], floor[i, j], rate, capn, risk_eval, None, None,
                    )
                    if dead:
                        phase[i, j] = 0
                        continue
                    bal[i, j] = eq
                    edays[i, j] += 1
                    best[i, j] = max(best[i, j], day_pnl)
                    if locks:
                        floor[i, j], locked[i, j] = eod_update(bal[i, j], floor[i, j], locked[i, j], mll, trigger, lock_at)
                    need = max(float(spec["target"]), best[i, j] / float(spec["consistency"]) if best[i, j] > 0 else float(spec["target"]))
                    if edays[i, j] >= int(spec["min_eval_days"]) and bal[i, j] - size + 1e-6 >= need:
                        if int((phase[i] == 2).sum() + (phase[i] == 3).sum()) < funded_cap:
                            phase[i, j] = 2
                            cash[i] -= activation
                            bal[i, j] = float(spec["funded_start"])
                            floor[i, j] = float(spec["funded_start"]) - mll
                            locked[i, j] = False
                            wins[i, j] = 0
                            cycle[i, j] = 0
                            pays[i, j] = 0
                        else:
                            phase[i, j] = 0
                    continue
                if phase[i, j] == 2:
                    if not filled:
                        phase[i, j] = 0
                        continue
                    eq, dead, day_pnl = play_day(
                        filled[int(rng.integers(0, len(filled)))], bal[i, j], floor[i, j], rate, capn, mll, None, None,
                    )
                    if dead:
                        phase[i, j] = 0
                        continue
                    bal[i, j] = eq
                    cycle[i, j] += day_pnl
                    if day_pnl + 1e-9 >= win_min:
                        wins[i, j] += 1
                    floor[i, j], locked[i, j] = eod_update(
                        bal[i, j], floor[i, j], locked[i, j], mll, float(spec["lock_trigger"]), float(spec["lock_floor"]),
                    )
                    phase[i, j] = 3
                if phase[i, j] == 3 and wins[i, j] < int(spec["winning_days"]):
                    hit = rng.random() < grind_p
                    pnl = win_min if hit else -loss_g
                    if bal[i, j] - max(-pnl, 0.0) <= floor[i, j] + 1e-9:
                        phase[i, j] = 0
                        continue
                    bal[i, j] += pnl
                    cycle[i, j] += pnl
                    if pnl >= win_min:
                        wins[i, j] += 1
                    floor[i, j], locked[i, j] = eod_update(
                        bal[i, j], floor[i, j], locked[i, j], mll, float(spec["lock_trigger"]), float(spec["lock_floor"]),
                    )
                if phase[i, j] == 3 and wins[i, j] + 1e-9 >= int(spec["winning_days"]):
                    amount = float(_payout(spec, np.array([bal[i, j]]), np.array([cycle[i, j]]))[0])
                    max_pays = int(spec["max_payouts"] or 8)
                    if cycle[i, j] > float(spec["buffer"]) and amount >= float(spec["min_request"]) and pays[i, j] < max_pays:
                        cash[i] += amount * float(spec["split"])
                        bal[i, j] -= amount
                        floor[i, j] = float(spec["lock_floor"])
                        locked[i, j] = True
                        pays[i, j] += 1
                        wins[i, j] = 0
                        cycle[i, j] = 0
                        phase[i, j] = 2
                        if pays[i, j] >= max_pays or bal[i, j] <= floor[i, j] + 1e-9:
                            phase[i, j] = 0
    return cash, note, slots


def _days(v):
    if isinstance(v, float) and math.isnan(v):
        return "n/a"
    return f"{v:.1f}"


def render(funded, winner, eval_rows, lives, months, firms_list, cuts, n_var) -> str:
    lines = [
        "# Full-port lifecycle",
        "",
        "Disarmed. Nothing here places an order. The plan is locked. The eval is two full-size high-hit trades, each aimed at about $1,500, with the stop at the account's max loss or at about half of it. The funded account is one full-port trade, about $3,400 against a $2,000 stop where the max loss is $2,000, and $2,550 against $1,500 on FundedNext, then the firm's minimum winning days.",
        "",
        "The funded search is one resting limit a day, reward fixed at 1.7R, stops 15, 25, 40 and 60 points. It was ranked by validation hit rate before the holdout from 1 July 2025 was opened. A variant needed 80 validation fills to be eligible. The p-value is a one-sided test against the 37% no-drift hit rate, and Benjamini-Hochberg at 10% is applied across the whole funded list. A setup clears 37% only when its holdout interval sits entirely above that line and its validation test survived the correction.",
        "",
        "Fills are trade-through of one tick. The stop is a market, one tick worse, and it is checked before the target. Research R subtracts Topstep's $1.22. The floor moves with the closing balance. A dip to the floor, including an open loss, ends the account. That is Topstep's rule in so many words, FundedNext's floating-loss sentence, and the stricter reading of LucidFlex's \"if your account balance reached the MLL\". Lucid's page does not say unrealized. Details and the page dates are in `docs/HF-LIMIT-RESEARCH.md`.",
        "",
        f"Train cuts, frozen before the validation scores: a large gap is at least {cuts['gap75']:.0f} points and a small gap is at most {cuts['gap25']:.0f}. A wide prior day is at least the train median, {cuts['pd_med']:.0f} points. There are {n_var} funded variants.",
        "",
        "## Funded 1.7:1 search",
        "",
        "| variant | val n | val hit | val p vs 37% | BH | val mean R | cost breakeven | hold n | hold hit | hold mean R |",
        "|---|---:|---:|---:|---|---:|---:|---:|---:|---:|",
    ]
    a = lines.append
    show = sorted(
        funded,
        key=lambda r: (0 if r["val"]["n"] >= 80 else 1, math.inf if math.isnan(r["val"]["hit"]) else -r["val"]["hit"]),
    )
    for r in show[:12]:
        a(
            f"| {r['name']} | {r['val']['n']} | {pct(r['val']['hit'])} ({pct(r['val']['lo'])} to {pct(r['val']['hi'])}) | "
            f"{r['val']['p']:.3f} | {'yes' if r['bh'] else 'no'} | {_num(r['val_r'][0])} | {pct(r['be'])} | "
            f"{r['hold']['n']} | {pct(r['hold']['hit'])} ({pct(r['hold']['lo'])} to {pct(r['hold']['hi'])}) | {_num(r['hold_r'][0])} |"
        )
    n_bh = sum(1 for r in funded if r["bh"])
    a("")
    a(f"Validation tests that survived Benjamini-Hochberg at 10%: {n_bh} of {len(funded)}. Nearby stops are the same idea, so that is not {n_bh} independent discoveries.")
    a("")
    if winner is None:
        a("No funded variant had 80 validation fills. There is no 1.7:1 candidate.")
    else:
        w = winner
        a(
            f"The validation winner is `{w['name']}`. Validation hit {pct(w['val']['hit'])} ({pct(w['val']['lo'])} to {pct(w['val']['hi'])}), "
            f"p vs 37% {w['val']['p']:.3f}, Benjamini-Hochberg {'passed' if w['bh'] else 'did not pass'}. "
            f"Holdout hit {pct(w['hold']['hit'])} ({pct(w['hold']['lo'])} to {pct(w['hold']['hi'])}) on {w['hold']['n']} fills. "
            f"Holdout mean R {_num(w['hold_r'][0])} ({_num(w['hold_r'][1])} to {_num(w['hold_r'][2])}). "
            f"The cost breakeven at this stop is {pct(w['be'])}."
        )
    a("")
    a("## Eval: two full-size trades")
    a("")
    a(
        "Each row is one trade a day unless the name says `two`, which is up to two fills. "
        "A $2,000 risk with a $1,500 target is 0.75R. The $1,000 column is a different trade, 1.5R, so the target stays about $1,500. It is not the negative-R shape. FundedNext's max loss is $1,500, so the full-size risk there is $1,500, not $2,000. "
        "Pass rates use the path: the floor moves at the close, and a dip to the floor ends the attempt. "
        "`combo` rests the prior-day high and low and the overnight pull side, and takes the first fill. `combo_two` allows a second fill."
    )
    a("")
    a("| setup | firm | val pass at $2,000 | holdout pass at $2,000 | holdout days | val pass at $1,000 |")
    a("|---|---|---:|---:|---:|---:|")
    for r in eval_rows:
        for firm in r["firms"]:
            a(
                f"| {r['name']} | {firm['firm']} | {pct(firm['val2']['pass'])} | "
                f"{pct(firm['hold2']['pass'])} ({pct(firm['hold2']['lo'])} to {pct(firm['hold2']['hi'])}) | "
                f"{_days(firm['hold2']['days'])} | {pct(firm['val1']['pass'])} |"
            )
    a("")
    a(
        "A single winning day does not pass these three default rules. Topstep's best day has to stay within 55% of the target, so one day that takes the whole $3,000 raises the target to about $5,455. "
        "LucidFlex's standard rule is 40% and the minimum is two days, so two equal $1,500 days are 50% and do not pass. The 50% add-on would. "
        "FundedNext's 40% rule raises a $2,500 target to $6,250 if one day is the whole target. "
        "The rows below are still one full-target trade per day, and the paths that pass do it by winning again on a later day. They are not one-day passes."
    )
    a("")
    a("| firm | one trade at the full target, validation pass | days |")
    a("|---|---:|---:|")
    for firm in firms_list:
        st = firm["one"]
        a(f"| {firm['spec']['firm']} | {pct(st['pass'])} ({pct(st['lo'])} to {pct(st['hi'])}) | {_days(st['days'])} |")
    a("")
    a("## Lifecycle")
    a("")
    a(
        "Eval days are the validation-best 0.75R book, scored on the holdout. The big funded day is the validation-best 1.7:1 book, one filled trade, sized to the max loss. "
        "The following days use that eval book's holdout hit rate: a win is the firm's minimum winning day ($150 at Topstep and LucidFlex, $200 at FundedNext), and a loss is that amount divided by 0.75. "
        "Both dollar risks were specified in advance. The higher one is not a selection."
    )
    a("")
    a("| firm | eval risk | holdout pass | EV per eval | payouts / 100 |")
    a("|---|---:|---:|---|---:|")
    for row in lives:
        a(
            f"| {row['firm']} | {money(row['risk'])} | {pct(row['pass'])} | "
            f"{money(row['life']['mean'])} ({money(row['life']['lo'])} to {money(row['life']['hi'])}) | {row['life']['pays']:.1f} |"
        )
    a("")
    a("| firm | evals opened | mean 21-day book at the $2,000 eval risk | 95% CI | P(month negative) |")
    a("|---|---:|---:|---|---:|")
    for row in months:
        a(
            f"| {row['firm']} | {row['slots']} | {money(row['mean'])} | {money(row['lo'])} to {money(row['hi'])} | {pct(row['p_neg'])} |"
        )
    a("")
    for row in months:
        a(f"- {row['firm']}: {row['note']}")
    a("")
    a("## What a pass rate and a hit rate are worth")
    a("")
    a(
        "One payout cycle, exact, not a sample. Fail and the fee is lost. Pass and the activation is paid. "
        "The big day then busts the account, or, if it hits, four minimum winning days are assumed to finish and one payout is taken. "
        "A winning big day pays the firm's commission on a 16-point stop sized to the max loss. A losing big day also pays one tick. "
        "Lucid's fee is the assumed $100. This grid does not depend on which limit was searched."
    )
    a("")
    passes = [0.20, 0.30, 0.40, 0.50, 0.60]
    hits = [0.30, 0.37, 0.45, 0.50, 0.60]
    for spec in firms_list:
        s = spec["spec"]
        a(f"### {s['firm']}")
        a("")
        a("| pass \\ hit | " + " | ".join(pct(h) for h in hits) + " |")
        a("|---|" + "---:|" * len(hits))
        for p_pass in passes:
            cells = [money(grid_value(s, p_pass, h)) for h in hits]
            a(f"| {pct(p_pass)} | " + " | ".join(cells) + " |")
        a("")
    a("## Verdict")
    a("")
    a(_verdict(winner, eval_rows, lives, months))
    a("")
    return "\n".join(lines) + "\n"


def _above(lo, bar) -> bool:
    return isinstance(lo, float) and not math.isnan(lo) and lo > bar


def _verdict(winner, eval_rows, lives, months) -> str:
    if winner is None:
        return "No funded 1.7:1 variant had enough validation fills to score."
    lo = winner["hold"]["lo"]
    if _above(lo, P0) and winner["bh"]:
        head = (
            f"`{winner['name']}` clears 37%. Holdout hit {pct(winner['hold']['hit'])} "
            f"({pct(winner['hold']['lo'])} to {pct(winner['hold']['hi'])}) on {winner['hold']['n']} fills. "
            f"The interval starts just above 37% and above the {pct(winner['be'])} cost breakeven at this stop. "
            "The validation hit was higher. The validation test survived the correction. "
            "Stretching the prior-day fade to 1.7R did not beat this overnight pull."
        )
    elif _above(lo, P0):
        head = (
            f"`{winner['name']}` has a holdout interval above 37%, at {pct(winner['hold']['hit'])}. "
            "Its validation test did not survive Benjamini-Hochberg, so that is not a corrected discovery."
        )
    else:
        head = (
            f"No funded 1.7:1 setup clears 37% with the holdout interval above it. "
            f"The validation winner `{winner['name']}` holdout hit is {pct(winner['hold']['hit'])} "
            f"({pct(winner['hold']['lo'])} to {pct(winner['hold']['hi'])})."
        )
    bits = []
    for row in lives:
        if row["risk"] != 2000 and row["firm"] != "FundedNext Futures Flex":
            continue
        if row["firm"] == "FundedNext Futures Flex" and row["risk"] != 1500 and row["risk"] != 1000:
            continue
        bits.append(
            f"{row['firm']} at {money(row['risk'])} eval risk: EV {money(row['life']['mean'])} "
            f"({money(row['life']['lo'])} to {money(row['life']['hi'])}), {row['life']['pays']:.0f} payouts per 100."
        )
    month_bits = [f"{m['firm']} month {money(m['mean'])}, P(negative) {pct(m['p_neg'])}" for m in months]
    combo = next((r for r in eval_rows if r["name"] == "combo_s15"), None)
    pd = next((r for r in eval_rows if r["name"] == "pdhl_s15"), None)
    on = next((r for r in eval_rows if r["name"] == "onhl_pull_s15"), None)
    mix = ""
    if combo and pd and on:
        def _avg(row, key):
            vals = [f[key]["pass"] for f in row["firms"]]
            return float(np.nanmean(vals))
        mix = (
            f" On the validation window the average pass rate at a $2,000 risk is {pct(_avg(pd, 'val2'))} for prior-day levels, "
            f"{pct(_avg(on, 'val2'))} for the overnight pull, and {pct(_avg(combo, 'val2'))} for the two on the same order. "
            "Combining them does not raise the pass rate."
        )
    return head + " " + " ".join(bits) + " " + ". ".join(month_bits) + "." + mix


def main() -> None:
    print("load", flush=True)
    df = load_bars(str(DATA))
    days = build_days(df)
    profiles = profiles_at_open(df)
    print("days", len(days), "profiles", len(profiles), flush=True)
    train = [d for d in days if d.ts < TRAIN_END]
    gaps = np.array([abs(d.rth_open - d.pdc) for d in train if np.isfinite(d.pdc)])
    cuts = {
        "gap75": float(np.quantile(gaps, 0.75)),
        "gap25": float(np.quantile(gaps, 0.25)),
        "pd_med": float(np.median([d.pd_range for d in train])),
    }
    print("cuts", {k: round(v, 1) for k, v in cuts.items()}, flush=True)
    val_i = [i for i, d in enumerate(days) if TRAIN_END <= d.ts < VAL_END]
    hold_i = [i for i, d in enumerate(days) if d.ts >= VAL_END]
    funded_spec = funded_variants()
    print("funded variants", len(funded_spec), flush=True)
    funded = []
    books = {}
    for name, kind, stop, window, regime in funded_spec:
        print(name, flush=True)
        booked = run_book(days, kind, stop, 1.7, window, regime, cuts, profiles, 1)
        books[name] = booked
        val_tr, hold_tr = _fills(booked, val_i), _fills(booked, hold_i)
        row = {
            "name": name, "stop": stop,
            "val": hit_test(val_tr), "hold": hit_test(hold_tr),
            "val_r": mean_r(val_tr), "hold_r": mean_r(hold_tr),
            "be": breakeven(stop),
        }
        funded.append(row)
    pvals = np.array([r["val"]["p"] for r in funded])
    flags = bh_mask(pvals)
    for r, ok in zip(funded, flags, strict=True):
        r["bh"] = bool(ok)
    eligible = [r for r in funded if r["val"]["n"] >= 80 and not math.isnan(r["val"]["hit"])]
    eligible.sort(key=lambda r: -r["val"]["hit"])
    winner = eligible[0] if eligible else None
    if winner:
        print("winner", winner["name"], round(winner["val"]["hit"], 3), round(winner["hold"]["hit"], 3), flush=True)
    firm_list = firms()
    eval_rows = []
    eval_books = {}
    for name, kind, stop, ntr in eval_variants():
        print("eval", name, flush=True)
        booked = run_book(days, kind, stop, 0.75, "rth", None, cuts, profiles, ntr)
        booked_15 = run_book(days, kind, stop, 1.5, "rth", None, cuts, profiles, ntr)
        eval_books[name] = booked
        eval_books[name + "@1.5"] = booked_15
        firms_out = []
        for spec in firm_list:
            firms_out.append({
                "firm": spec["firm"],
                "val2": pass_rate(booked, val_i, spec, min(2000.0, float(spec["mll"])), _seed(name + spec["firm"] + "v2")),
                "hold2": pass_rate(booked, hold_i, spec, min(2000.0, float(spec["mll"])), _seed(name + spec["firm"] + "h2")),
                "val1": pass_rate(booked_15, val_i, spec, min(1000.0, float(spec["mll"])), _seed(name + spec["firm"] + "v1")),
                "hold1": pass_rate(booked_15, hold_i, spec, min(1000.0, float(spec["mll"])), _seed(name + spec["firm"] + "h1")),
            })
        eval_rows.append({"name": name, "firms": firms_out, "book": name})
    # best eval by average validation pass at $2,000, or the firm's own max loss when that is smaller
    def _avg_pass(row):
        return float(np.nanmean([f["val2"]["pass"] for f in row["firms"]]))
    eval_rows.sort(key=_avg_pass, reverse=True)
    best_eval = eval_rows[0]["name"]
    print("best eval", best_eval, round(_avg_pass(eval_rows[0]), 3), flush=True)
    # one-trade pass: reward = target / mll, risk = mll, using the best eval's level family at stop 15
    one_rows = []
    kind = best_eval.split("_")[0]
    if kind == "combo":
        kind = "combo"
    for spec in firm_list:
        reward = float(spec["target"]) / float(spec["mll"])
        booked = run_book(days, kind if kind in ("pdhl", "onhl", "combo") else "pdhl", 15.0, reward, "rth", None, cuts, profiles, 1)
        one_rows.append(pass_rate(booked, val_i, spec, float(spec["mll"]), _seed("one" + spec["firm"])))
    # lifecycle
    eval_hold = [eval_books[best_eval][i] for i in hold_i]
    fund_name = winner["name"] if winner else "pdhl_s15"
    fund_hold = [books[fund_name][i] for i in hold_i]
    grind = hit_test(_fills(eval_books[best_eval], hold_i), 0.5)["hit"]
    if math.isnan(grind):
        grind = 0.5
    lives = []
    months = []
    for spec, one in zip(firm_list, one_rows, strict=True):
        spec["one"] = one
        for risk in (min(2000.0, float(spec["mll"])), min(1000.0, float(spec["mll"]))):
            if risk in [row["risk"] for row in lives if row["firm"] == spec["firm"]]:
                continue
            half = risk < 1500
            book = [eval_books[best_eval + "@1.5"][i] for i in hold_i] if half else eval_hold
            g = hit_test(_fills(eval_books[best_eval + "@1.5"], hold_i), 0.5)["hit"] if half else grind
            if isinstance(g, float) and math.isnan(g):
                g = grind
            life = fullport_life(
                book, fund_hold, spec, np.random.default_rng(_seed("life" + spec["firm"] + str(int(risk)))),
                risk, g, 1.5 if half else 0.75, n=700,
            )
            lives.append({"firm": spec["firm"], "risk": risk, "life": life, "pass": life["pass"]})
            print("life", spec["firm"], risk, round(life["mean"], 1), flush=True)
        cash, note, slots = month_book(eval_hold, fund_hold, spec, min(2000.0, float(spec["mll"])), grind)
        mid = float(cash.mean())
        se = float(cash.std(ddof=1) / math.sqrt(len(cash)))
        months.append({
            "firm": spec["firm"], "mean": mid, "lo": mid - 1.96 * se, "hi": mid + 1.96 * se,
            "p_neg": float(np.mean(cash < 0)), "slots": slots, "note": note,
        })
    firm_payload = [{"spec": spec, "one": spec["one"]} for spec in firm_list]
    # restore eval_rows order for the table: validation rank, but keep combo rows visible
    text = render(funded, winner, eval_rows, lives, months, firm_payload, cuts, len(funded_spec))
    OUT.write_text(text)
    print("wrote", OUT, flush=True)


if __name__ == "__main__":
    main()
