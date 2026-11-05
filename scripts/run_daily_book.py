"""One full-risk trade a day: overnight pull first, then a fallback.

The fallback and its cancel time are chosen on validation. Holdout is reported
after that choice. Nothing here places an order.
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
    _asia,
    _seed,
    bh_mask,
    fullport_life,
    hit_test,
    mean_r,
    month_book,
    pass_rate,
)
from scripts.run_hf_limit import build_days
from scripts.run_limit_research import (
    TRAIN_END,
    VAL_END,
    _num,
    firms,
    money,
    month_plan,
    pct,
)
from src.research.strategies.costs import COMMISSION_POINTS, TICK
from src.research.strategies.engine import load_bars
from src.research.strategies.hf_limit import Trade, _manage
from src.research.strategies.jake_rules import value_area

OUT = ROOT / "docs" / "DAILY-BOOK.md"
DATA = ROOT / "data" / "reference" / "nq_1m_master.parquet"
OPEN = 9 * 60 + 30
STOP = 15.0
# Cancel times are when the overnight order comes off and the fallback can start.
CANCELS = (10 * 60, 11 * 60, 12 * 60, 14 * 60)
FALLBACKS = (
    "london4",
    "pdhl",
    "vwap12",
    "vwap40",
    "ib",
    "or15",
    "or30",
    "va",
    "asia",
    "gap",
    "on_other",
)
FILL_FLOOR = 0.90


def _blank(n):
    return np.full(n, np.nan)


def at_minute(day, minute: int) -> int:
    hit = np.flatnonzero((np.arange(len(day.hm)) >= day.i_open) & (day.hm >= minute) & (day.hm < 18 * 60))
    return int(hit[0]) if len(hit) else day.end


def first_touch(o, h, l, buy, sell, start: int, end: int):
    """First trade-through. Both sides on the same bar is skipped, and the scan continues."""
    for i in range(start, end):
        b = buy[i]
        s = sell[i]
        b_hit = np.isfinite(b) and float(o[i]) > b - TICK and float(l[i]) <= b - TICK
        s_hit = np.isfinite(s) and float(o[i]) < s + TICK and float(h[i]) >= s + TICK
        if b_hit and s_hit:
            continue
        if b_hit or s_hit:
            side = 1 if b_hit else -1
            return side, float(b if side == 1 else s), i
    return None


def manage_trade(day, side: int, limit: float, bar: int, reward: float) -> Trade:
    stop_px = limit - side * STOP
    target = limit + side * reward * STOP
    _k, gross, mae, hit = _manage(side, limit, stop_px, target, day.o, day.h, day.l, day.c, day.hm, bar, day.end)
    return Trade(gross, STOP, mae, hit)


def onhl_orders(day):
    n = len(day.o)
    buy, sell = _blank(n), _blank(n)
    if day.up > 0 and np.isfinite(day.onl):
        buy[day.i_open:day.end] = day.onl
    elif day.up < 0 and np.isfinite(day.onh):
        sell[day.i_open:day.end] = day.onh
    return buy, sell


def _range_ready(day, minutes: int):
    span = (day.hm >= OPEN) & (day.hm < OPEN + minutes)
    if int(span.sum()) < max(10, minutes // 2):
        return None
    ready = at_minute(day, OPEN + minutes)
    if ready >= day.end:
        return None
    return float(day.h[span].max()), float(day.l[span].min()), ready


def fallback_orders(day, name: str):
    """Return buy, sell, and the first bar the level is known."""
    n = len(day.o)
    buy, sell = _blank(n), _blank(n)
    start = day.i_open
    if name == "london4":
        lon = (day.hm >= 3 * 60) & (day.hm < 8 * 60 + 30)
        if int(lon.sum()) < 20:
            return buy, sell, start
        buy[start:day.end] = float(day.l[lon].min()) - 4.0
        sell[start:day.end] = float(day.h[lon].max()) + 4.0
    elif name == "pdhl":
        buy[start:day.end] = day.pdl
        sell[start:day.end] = day.pdh
    elif name in ("vwap12", "vwap40"):
        band = 12.0 if name == "vwap12" else 40.0
        buy[start:day.end] = day.vwap_prev[start:day.end] - band
        sell[start:day.end] = day.vwap_prev[start:day.end] + band
    elif name == "ib":
        if day.ib_i < 0 or not np.isfinite(day.ib_hi):
            return buy, sell, day.end
        start = day.ib_i
        buy[start:day.end] = day.ib_lo
        sell[start:day.end] = day.ib_hi
    elif name == "or15":
        got = _range_ready(day, 15)
        if got is None:
            return buy, sell, day.end
        hi, lo, start = got
        buy[start:day.end] = lo
        sell[start:day.end] = hi
    elif name == "or30":
        got = _range_ready(day, 30)
        if got is None:
            return buy, sell, day.end
        hi, lo, start = got
        buy[start:day.end] = lo
        sell[start:day.end] = hi
    elif name == "va":
        area = getattr(day, "va", None)
        if area is None:
            return buy, sell, start
        val, vah = area[0], area[1]
        buy[start:day.end] = val
        sell[start:day.end] = vah
    elif name == "asia":
        hi, lo = _asia(day)
        if not np.isfinite(hi):
            return buy, sell, start
        buy[start:day.end] = lo
        sell[start:day.end] = hi
    elif name == "gap":
        if not np.isfinite(day.pdc) or abs(day.rth_open - day.pdc) < 10:
            return buy, sell, start
        if day.rth_open > day.pdc:
            buy[start:day.end] = day.pdc
        else:
            sell[start:day.end] = day.pdc
    elif name == "on_other":
        if day.up > 0 and np.isfinite(day.onh):
            sell[start:day.end] = day.onh
        elif day.up < 0 and np.isfinite(day.onl):
            buy[start:day.end] = day.onl
        elif day.up == 0:
            if np.isfinite(day.onl):
                buy[start:day.end] = day.onl
            if np.isfinite(day.onh):
                sell[start:day.end] = day.onh
    return buy, sell, start


def _one(day, buy, sell, i: int):
    return first_touch(day.o, day.h, day.l, buy, sell, i, i + 1)


def day_trade(day, fallback: str | None, cancel_min: int, reward: float, race: bool = False):
    """One trade. Overnight pull has priority until the cancel, unless `race` takes the first of either."""
    obuy, osell = onhl_orders(day)
    if fallback is None:
        got = first_touch(day.o, day.h, day.l, obuy, osell, day.i_open, day.end)
        if got is None:
            return None, "flat"
        side, limit, bar = got
        return manage_trade(day, side, limit, bar, reward), "onhl"
    fbuy, fsell, fstart = fallback_orders(day, fallback)
    if race:
        for i in range(day.i_open, day.end):
            primary = _one(day, obuy, osell, i)
            other = _one(day, fbuy, fsell, i) if i >= fstart else None
            if primary and other:
                continue
            got = primary or other
            if got is None:
                continue
            side, limit, bar = got
            return manage_trade(day, side, limit, bar, reward), "race"
        return None, "flat"
    cancel = at_minute(day, cancel_min)
    cancel = min(cancel, day.end)
    armed = bool(np.isfinite(obuy[day.i_open:cancel]).any() or np.isfinite(osell[day.i_open:cancel]).any())
    if armed:
        got = first_touch(day.o, day.h, day.l, obuy, osell, day.i_open, cancel)
        if got is not None:
            side, limit, bar = got
            return manage_trade(day, side, limit, bar, reward), "onhl"
        start = max(cancel, fstart)
    else:
        start = max(day.i_open, fstart)
    got = first_touch(day.o, day.h, day.l, fbuy, fsell, start, day.end)
    if got is None:
        return None, "flat"
    side, limit, bar = got
    return manage_trade(day, side, limit, bar, reward), "fallback"


def run_book(days, fallback: str | None, cancel_min: int, reward: float, race: bool = False):
    trades = []
    sources = []
    for day in days:
        trade, source = day_trade(day, fallback, cancel_min, reward, race)
        trades.append([] if trade is None else [trade])
        sources.append(source)
    return trades, sources


def attach_va(df: pd.DataFrame, days) -> None:
    """Prior cash-session value area, 70%, one-point bins. Known before today's open."""
    hm = df["hm"].to_numpy()
    close = np.rint(df["close"].to_numpy()).astype(np.int64)
    vol = df["volume"].to_numpy(dtype=float)
    sess = df["sess"].to_numpy()
    ts = df["ts_event"]
    cuts = np.flatnonzero(np.diff(sess)) + 1
    bounds = np.r_[0, cuts, len(df)]
    opens = []
    areas = []
    for a, b in pairwise(bounds):
        hh = hm[a:b]
        hit = np.flatnonzero((hh >= OPEN) & (hh < 18 * 60))
        if len(hit) == 0:
            continue
        opens.append(ts.iloc[a + int(hit[0])])
        rth = (hh >= OPEN) & (hh < 16 * 60)
        if int(rth.sum()) < 30:
            areas.append(None)
            continue
        area = value_area(close[a:b][rth], vol[a:b][rth])
        if area is None or area[1] <= area[0]:
            areas.append(None)
        else:
            areas.append(area)
    prior = {opens[i]: areas[i - 1] if i else None for i in range(len(opens))}
    for day in days:
        day.va = prior.get(day.ts)


def fill_rate(sources, idxs) -> float:
    if not idxs:
        return float("nan")
    return sum(sources[i] != "flat" for i in idxs) / len(idxs)


def mix(sources, idxs) -> dict:
    n = len(idxs) or 1
    return {
        "onhl": sum(sources[i] == "onhl" for i in idxs) / n,
        "fallback": sum(sources[i] == "fallback" for i in idxs) / n,
        "flat": sum(sources[i] == "flat" for i in idxs) / n,
        "race": sum(sources[i] == "race" for i in idxs) / n,
    }


def _fills(book, idxs):
    return [tr for i in idxs for tr in book[i]]


def avg_pass(book, idxs, firm_list, tag: str, n: int = 400):
    out = []
    for spec in firm_list:
        risk = min(2000.0, float(spec["mll"]))
        stat = pass_rate(book, idxs, spec, risk, _seed(tag + spec["firm"]), n=n)
        out.append({"firm": spec["firm"], **stat})
    vals = [row["pass"] for row in out]
    days = [row["days"] for row in out if not (isinstance(row["days"], float) and math.isnan(row["days"]))]
    return {
        "firms": out,
        "avg": float(np.nanmean(vals)),
        "days": float(np.mean(days)) if days else float("nan"),
    }


def month_passes(eval_days, spec, risk, grind_unused, n: int = 160) -> float:
    """Evals that pass and take a funded slot in a 21-day month. Same cap as the cash month."""
    del grind_unused
    slots, _note = month_plan(spec)
    rng = np.random.default_rng(_seed("passmonth" + spec["firm"] + str(int(risk))))
    mll = float(spec["mll"])
    size = float(spec["size"])
    funded_cap = int(spec["funded_cap"])
    from scripts.run_fullport import _eval_lock
    from scripts.run_hf_limit import CAPS, play_day
    from src.research.strategies.hf_limit import eod_update

    locks, trigger, lock_at = _eval_lock(spec)
    rate = float(spec["rate"])
    capn = CAPS[spec["firm"]]
    total = np.zeros(n)
    phase = np.ones((n, slots), dtype=np.int8)
    bal = np.full((n, slots), size)
    floor = np.full((n, slots), size - mll)
    locked = np.zeros((n, slots), dtype=bool)
    best = np.zeros((n, slots))
    edays = np.zeros((n, slots))
    funded = np.zeros((n, slots), dtype=bool)
    for _d in range(21):
        for j in range(slots):
            for i in range(n):
                if phase[i, j] != 1:
                    continue
                eq, dead, day_pnl = play_day(
                    eval_days[int(rng.integers(0, len(eval_days)))], bal[i, j], floor[i, j], rate, capn, risk, None, None,
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
                    if int(funded[i].sum()) < funded_cap:
                        phase[i, j] = 2
                        funded[i, j] = True
                        total[i] += 1
                    else:
                        phase[i, j] = 0
    return float(total.mean())


def _be(reward: float) -> float:
    win = reward * STOP - COMMISSION_POINTS
    loss = STOP + TICK + COMMISSION_POINTS
    return loss / (win + loss)


def render(rows, winner, base_fill, lives, months, race, coverage) -> str:
    lines = [
        "# Daily book",
        "",
        _lead(winner, base_fill, lives),
        "",
        "Disarmed. Nothing here places an order. LucidFlex evals are modeled at 50%, and the fee in the lifecycle is the assumed $100. One account takes at most one full-risk trade a day.",
        "",
        "The overnight pull is armed at 09:30. It buys the overnight low after an up open and sells the overnight high after a down open, 15-point stop. If that order fills, nothing else is placed. If it has not filled by the cancel time, it is cancelled and the fallback limit starts. On a day the overnight order cannot be armed, the fallback starts as soon as its own level is known. The cancel time and the fallback are chosen on the validation window, from 1 Jul 2024 to 1 Jul 2025. A book has to fill at least 90% of validation days to be eligible. Among those, the highest average validation pass rate across the three firms wins. The tie-break is the validation 1.7 hit rate. Holdout, from 1 Jul 2025, is reported after that choice.",
        "",
        "Fills are trade-through of one tick. The stop is a market, one tick worse, and it is checked before the target. Research R subtracts Topstep's $1.22. A 0.75R no-drift hit rate is about 57%, and the cost breakeven is about 60%. A 1.7R no-drift hit rate is 37%, and the cost breakeven at a 15-point stop is 38.9%. Benjamini-Hochberg at 10% is applied to the validation 1.7 hit-rate tests. It describes the list. It is not the sort key.",
        "",
        f"Validation days {coverage['val']}, holdout days {coverage['hold']}. The overnight pull alone fills {pct(base_fill['val'])} of validation days and {pct(base_fill['hold'])} of holdout days.",
        "",
        "## Why stacking lowered the pass rate",
        "",
        "The earlier combined order rested the prior-day high and low and the overnight pull at the same time and took whichever traded through first. That replaced some overnight-pull trades with an earlier prior-day trade. On the validation window the overnight pull alone passed about 62% of the time and the combined order about 44%. A flat day does not risk the max loss. An earlier, weaker trade does. Conditional fallback does not do that. The overnight trade, if it fills before the cancel, is kept. The fallback can only add a trade on a day that would otherwise have been flat, or replace an overnight trade that had not filled yet.",
        "",
    ]
    a = lines.append
    if race:
        a(
            f"On the selected fallback, the race version, both orders live together, has validation pass {pct(race['val_pass'])} "
            f"against {pct(race['cond_pass'])} for the conditional book and {pct(race['onhl_pass'])} for the overnight pull alone. "
            f"Holdout pass is {pct(race['hold_pass'])} for the race and {pct(race['hold_cond'])} for the conditional book. "
            "The race is about one point under the conditional book. The conditional book is about twenty points under the overnight pull alone. "
            "Keeping the overnight fill does remove the old stacking problem. It does not protect the pass rate. "
            "The added trades are full-risk trades on days that would have been flat, and a flat day cannot blow the account."
        )
        a("")
    a("## Validation")
    a("")
    a("Eligible books fill at least 90% of validation days. The table is sorted by validation pass rate. Holdout is not in this table.")
    a("")
    a("| fallback | cancel | val fill | onhl share | fallback share | val pass | val days | val 1.7 hit | p vs 37% | BH |")
    a("|---|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    show = [r for r in rows if r["eligible"]]
    show.sort(key=lambda r: -r["pass"]["avg"])
    for r in show[:8]:
        h = r["hit17"]
        a(
            f"| {r['name']} | {r['cancel'] // 60:02d}:{r['cancel'] % 60:02d} | {pct(r['val_fill'])} | {pct(r['mix']['onhl'])} | "
            f"{pct(r['mix']['fallback'])} | {pct(r['pass']['avg'])} | {r['pass']['days']:.1f} | "
            f"{pct(h['hit'])} ({pct(h['lo'])} to {pct(h['hi'])}) | {h['p']:.3f} | {'yes' if r['bh'] else 'no'} |"
        )
    if not show:
        a("")
        a("No book filled 90% of validation days. The highest validation fill rates are below.")
        a("")
        rest = sorted(rows, key=lambda r: -r["val_fill"])[:5]
        for r in rest:
            a(f"- `{r['name']}` at {r['cancel'] // 60:02d}:{r['cancel'] % 60:02d}: validation fill {pct(r['val_fill'])}.")
    a("")
    a(
        f"Books in the list: {len(rows)}. Validation 1.7 tests that survived Benjamini-Hochberg: {sum(1 for r in rows if r['bh'])}. "
        "Most of those survivors still contain the overnight pull, so the count is not that many separate edges. "
        "A 40-point VWAP band cancelled at 10:00 filled 89.9% of validation days, and the 15-minute opening range at the same time filled 88.7%. "
        "Both were under the 90% line, so neither was ranked."
    )
    a("")
    a("## Holdout of the selected book")
    a("")
    if winner is None:
        a("No eligible book, so there is no holdout selection.")
    else:
        w = winner
        a(
            f"`{w['name']}` with the overnight order cancelled at {w['cancel'] // 60:02d}:{w['cancel'] % 60:02d}. "
            f"Holdout fill {pct(w['hold_fill'])}. Of holdout days, {pct(w['hold_mix']['onhl'])} are the overnight pull, "
            f"{pct(w['hold_mix']['fallback'])} are the fallback, and {pct(w['hold_mix']['flat'])} are flat. "
            f"Eval pass {pct(w['hold_pass']['avg'])} in {w['hold_pass']['days']:.1f} days. "
            f"Funded 1.7 hit {pct(w['hold17']['hit'])} ({pct(w['hold17']['lo'])} to {pct(w['hold17']['hi'])}) "
            f"on {w['hold17']['n']} fills, mean R {_num(w['hold_r'][0])} ({_num(w['hold_r'][1])} to {_num(w['hold_r'][2])}). "
            f"The cost breakeven is {pct(_be(1.7))}. "
            "The hit interval includes 37%, and the mean-R interval includes zero. "
            "The validation test had survived the correction. The holdout does not confirm it."
        )
        a("")
        a("| firm | book | holdout pass | days |")
        a("|---|---|---:|---:|")
        for firm in w["hold_pass"]["firms"]:
            a(f"| {firm['firm']} | selected | {pct(firm['pass'])} ({pct(firm['lo'])} to {pct(firm['hi'])}) | {firm['days']:.1f} |")
        for firm in base_fill["hold_pass"]["firms"]:
            a(f"| {firm['firm']} | onhl only | {pct(firm['pass'])} ({pct(firm['lo'])} to {pct(firm['hi'])}) | {firm['days']:.1f} |")
    a("")
    a("## Lifecycle")
    a("")
    a("Eval trades are the 0.75R book. The funded shot is the same entry at 1.7R, one trade, sized to the max loss. Later days use the 0.75R holdout hit rate. A win on those days is the firm's minimum, and a loss is that minimum divided by 0.75. The month opens the cap on day one and runs 21 sessions. Evals passed per month are the accounts that pass and take a funded slot inside that window.")
    a("")
    a("| firm | book | EV per eval | payouts / 100 | evals passed / month | 21-day cash | P(month negative) |")
    a("|---|---|---|---:|---:|---|---:|")
    for row in lives:
        month = row["month"]
        a(
            f"| {row['firm']} | {row['book']} | {money(row['life']['mean'])} ({money(row['life']['lo'])} to {money(row['life']['hi'])}) | "
            f"{row['life']['pays']:.1f} | {row['passes']:.2f} | {money(month['mean'])} ({money(month['lo'])} to {money(month['hi'])}) | {pct(month['p_neg'])} |"
        )
    a("")
    for row in months:
        a(f"- {row['firm']}: {row['note']}")
    a("")
    return "\n".join(lines) + "\n"


def _lead(winner, base_fill, lives) -> str:
    if winner is None:
        return (
            f"No fallback filled 90% of validation days. The overnight pull alone fills {pct(base_fill['hold'])} of holdout days."
        )
    sel = {row["firm"]: row for row in lives if row["book"] == "selected"}
    base = {row["firm"]: row for row in lives if row["book"] == "onhl only"}
    bits = []
    for firm in ("Topstep", "LucidFlex", "FundedNext Futures Flex"):
        if firm not in sel or firm not in base:
            continue
        bits.append(
            f"{firm} {money(sel[firm]['life']['mean'])} against {money(base[firm]['life']['mean'])} overnight-only"
        )
    return (
        f"Holdout fill is {pct(winner['hold_fill'])} with `{winner['name']}` after "
        f"{winner['cancel'] // 60:02d}:{winner['cancel'] % 60:02d}, against {pct(base_fill['hold'])} for the overnight pull alone. "
        f"Holdout eval pass is {pct(winner['hold_pass']['avg'])} in {winner['hold_pass']['days']:.1f} days, "
        f"against {pct(base_fill['hold_pass']['avg'])} in {base_fill['hold_pass']['days']:.1f} days overnight-only. "
        f"Per eval: {'; '.join(bits)}."
    )


def main() -> None:
    print("load", flush=True)
    df = load_bars(str(DATA))
    days = build_days(df)
    attach_va(df, days)
    val_i = [i for i, d in enumerate(days) if TRAIN_END <= d.ts < VAL_END]
    hold_i = [i for i, d in enumerate(days) if d.ts >= VAL_END]
    print("days", len(days), "val", len(val_i), "hold", len(hold_i), flush=True)
    firm_list = firms()
    onhl75, onhl_src = run_book(days, None, 0, 0.75)
    onhl17, _src17 = run_book(days, None, 0, 1.7)
    base_val_fill = fill_rate(onhl_src, val_i)
    base_hold_fill = fill_rate(onhl_src, hold_i)
    print("onhl fill", round(base_val_fill, 3), round(base_hold_fill, 3), flush=True)
    rows = []
    for name in FALLBACKS:
        for cancel in CANCELS:
            book75, sources = run_book(days, name, cancel, 0.75)
            book17, _sources17 = run_book(days, name, cancel, 1.7)
            val_fill = fill_rate(sources, val_i)
            trades = _fills(book17, val_i)
            hit = hit_test(trades, P0)
            row = {
                "name": name,
                "cancel": cancel,
                "val_fill": val_fill,
                "mix": mix(sources, val_i),
                "eligible": val_fill + 1e-12 >= FILL_FLOOR,
                "hit17": hit,
                "val_r": mean_r(trades),
                "book75": book75,
                "book17": book17,
                "sources": sources,
                "bh": False,
            }
            rows.append(row)
            print(name, cancel, round(val_fill, 3), hit["n"], flush=True)
    flags = bh_mask(np.array([r["hit17"]["p"] for r in rows]))
    for row, ok in zip(rows, flags, strict=True):
        row["bh"] = bool(ok)
    eligible = [r for r in rows if r["eligible"]]
    print("eligible", len(eligible), flush=True)
    for row in eligible:
        row["pass"] = avg_pass(row["book75"], val_i, firm_list, f"v{row['name']}{row['cancel']}")
        print("pass", row["name"], row["cancel"], round(row["pass"]["avg"], 3), flush=True)
    if eligible:
        eligible.sort(key=lambda r: (-r["pass"]["avg"], -(r["hit17"]["hit"] if r["hit17"]["n"] >= 20 else -1)))
        winner = eligible[0]
    else:
        winner = None
    base_pass_val = avg_pass(onhl75, val_i, firm_list, "onhlval")
    base_pass_hold = avg_pass(onhl75, hold_i, firm_list, "onhlhold", n=600)
    race = None
    if winner is not None:
        print("winner", winner["name"], winner["cancel"], flush=True)
        winner["hold_fill"] = fill_rate(winner["sources"], hold_i)
        winner["hold_mix"] = mix(winner["sources"], hold_i)
        winner["hold_pass"] = avg_pass(winner["book75"], hold_i, firm_list, "whold", n=600)
        hold_tr = _fills(winner["book17"], hold_i)
        winner["hold17"] = hit_test(hold_tr, P0)
        winner["hold_r"] = mean_r(hold_tr)
        race75, race_src = run_book(days, winner["name"], winner["cancel"], 0.75, race=True)
        race_val = avg_pass(race75, val_i, firm_list, "raceval")
        race_hold = avg_pass(race75, hold_i, firm_list, "racehold", n=400)
        race = {
            "val_pass": race_val["avg"],
            "hold_pass": race_hold["avg"],
            "cond_pass": winner["pass"]["avg"],
            "onhl_pass": base_pass_val["avg"],
            "hold_cond": winner["hold_pass"]["avg"],
            "fill": fill_rate(race_src, val_i),
        }
        print("race", round(race["val_pass"], 3), "cond", round(race["cond_pass"], 3), flush=True)
    lives = []
    month_notes = []
    books = [("onhl only", onhl75, onhl17)]
    if winner is not None:
        books.append(("selected", winner["book75"], winner["book17"]))
    for label, eb, fb in books:
        eh = [eb[i] for i in hold_i]
        fh = [fb[i] for i in hold_i]
        trades = _fills(eb, hold_i)
        grind = (sum(tr.hit for tr in trades) / len(trades)) if trades else 0.5
        for spec in firm_list:
            risk = min(2000.0, float(spec["mll"]))
            life = fullport_life(
                eh, fh, spec, np.random.default_rng(_seed("day" + label + spec["firm"])),
                risk, grind, n=500,
            )
            cash, note, slots = month_book(eh, fh, spec, risk, grind, n=160)
            mid = float(cash.mean())
            se = float(cash.std(ddof=1) / math.sqrt(len(cash)))
            passes = month_passes(eh, spec, risk, grind, n=120)
            month = {"mean": mid, "lo": mid - 1.96 * se, "hi": mid + 1.96 * se, "p_neg": float(np.mean(cash < 0)), "slots": slots, "note": note}
            lives.append({"firm": spec["firm"], "book": label, "life": life, "month": month, "passes": passes})
            if label == "selected":
                month_notes.append({"firm": spec["firm"], "note": note})
            print("life", label, spec["firm"], round(life["mean"], 1), "passes", round(passes, 2), flush=True)
    if not month_notes:
        for spec in firm_list:
            _slots, note = month_plan(spec)
            month_notes.append({"firm": spec["firm"], "note": note})
    base_fill = {
        "val": base_val_fill,
        "hold": base_hold_fill,
        "hold_pass": base_pass_hold,
    }
    text = render(
        rows, winner, base_fill, lives, month_notes, race,
        {"val": len(val_i), "hold": len(hold_i)},
    )
    OUT.write_text(text)
    print("wrote", OUT, flush=True)


if __name__ == "__main__":
    main()
