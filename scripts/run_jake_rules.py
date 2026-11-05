"""Jake Ryan's bar-testable rules, appended to docs/LIMIT-ENTRY-RESEARCH.md.

The rules were written down from his notes before this run. Every one of them
is reported. Holdout is not a second search. Absorption, trapped traders, the
15-second open, CPI straddles, VPN, and bulk account buying are not tested.
"""

from __future__ import annotations

import math
import sys
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_limit_research import (
    EVAL_R,
    FUNDED_R,
    OUT,
    TRAIN_END,
    VAL_END,
    _num,
    _period,
    build_sessions,
    day_dollars,
    days_s,
    eval_stats,
    firms,
    hit_vs_random,
    lifecycle,
    mean_r_ci,
    money,
    pct,
    run_variant,
)
from src.research.strategies.costs import FLAT_MINUTE, TICK
from src.research.strategies.engine import load_bars
from src.research.strategies.jake_rules import (
    OPEN,
    WINDOW_END,
    _end_index,
    first_fill,
    profiles_at_open,
)

MARKER = "## Jake Ryan's rules"
ROOT_DATA = ROOT / "data" / "reference" / "nq_1m_master.parquet"
RULES = (
    ("vp_10_2r", "fade", 10.0, 2.0),
    ("vp_15_2r", "fade", 15.0, 2.0),
    ("vp_10_3r", "fade", 10.0, 3.0),
    ("vp_15_3r", "fade", 15.0, 3.0),
    ("vp_12_poc", "poc", 12.0, 0.0),
    ("revert_open", "revert", 10.0, 0.0),
    ("trend_sweep", "trend", 12.0, 0.0),
)


def _flat(ts) -> dict:
    return {"ts": ts, "filled": False, "target_hit": False, "gross": 0.0, "risk": 0.0}


def _from_fill(ts, got) -> dict:
    if got is None or not got.filled:
        return _flat(ts)
    return {
        "ts": ts,
        "filled": True,
        "target_hit": got.target_hit,
        "gross": got.gross_points,
        "risk": got.risk_points,
    }


def _five(s):
    m = (s.hm >= OPEN) & (s.hm < OPEN + 5)
    if int(m.sum()) < 4 or s.i0930 < 0:
        return None
    return float(s.h[m].max()), float(s.l[m].min()), float(s.o[s.i0930])


def _pre30(s):
    m = (s.hm >= 9 * 60) & (s.hm < OPEN)
    if int(m.sum()) < 10:
        return None
    return float(s.h[m].max()), float(s.l[m].min())


def _orders_for(s, kind: str, stop: float, reward: float, area, gap_cut: float, extend_cut: float):
    flat = _end_index(s.hm, FLAT_MINUTE)
    if kind == "fade" or kind == "poc":
        if area is None or s.i0930 < 0:
            return []
        val, vah, poc = area
        start = s.i0930
        end = _end_index(s.hm, WINDOW_END)
        orders = []
        if kind == "poc":
            if vah - poc >= 8:
                orders.append((-1, vah, vah + stop, poc, start, end))
            if poc - val >= 8:
                orders.append((1, val, val - stop, poc, start, end))
        else:
            dist = reward * stop
            if vah - poc + 1e-9 >= dist:
                orders.append((-1, vah, vah + stop, vah - dist, start, end))
            if poc - val + 1e-9 >= dist:
                orders.append((1, val, val - stop, val + dist, start, end))
        return [o for o in orders if abs(o[1] - o[3]) >= TICK]
    if kind == "revert":
        span = _five(s)
        if span is None:
            return []
        hi, lo, op = span
        start = _end_index(s.hm, OPEN + 5)
        up = hi - op
        down = op - lo
        need = max(extend_cut, stop)
        if up >= need and up >= down:
            return [(-1, hi, hi + stop, op, start, flat)]
        if down >= need and down > up:
            return [(1, lo, lo - stop, op, start, flat)]
        return []
    if kind == "trend":
        if not np.isfinite(s.pdc) or s.i0930 < 0:
            return []
        gap = s.rth_open - float(s.pdc)
        if abs(gap) + 1e-9 < gap_cut:
            return []
        box = _pre30(s)
        if box is None:
            return []
        pre_hi, pre_lo = box
        search = _end_index(s.hm, WINDOW_END)
        if gap > 0:
            for j in range(s.i0930, search):
                if float(s.l[j]) < pre_lo - TICK and float(s.c[j]) > pre_lo:
                    target = s.onh
                    if not np.isfinite(target) or target < pre_lo + stop:
                        return []
                    return [(1, pre_lo, pre_lo - stop, float(target), j + 1, flat)]
        else:
            for j in range(s.i0930, search):
                if float(s.h[j]) > pre_hi + TICK and float(s.c[j]) < pre_hi:
                    target = s.onl
                    if not np.isfinite(target) or target > pre_hi - stop:
                        return []
                    return [(-1, pre_hi, pre_hi + stop, float(target), j + 1, flat)]
    return []


def _run(sessions, profiles, kind, stop, reward, gap_cut, extend_cut) -> list[dict]:
    rows = []
    for s in sessions:
        orders = _orders_for(s, kind, stop, reward, profiles.get(s.ts), gap_cut, extend_cut)
        got = first_fill(s.o, s.h, s.l, s.c, s.hm, orders, True) if orders else None
        rows.append(_from_fill(s.ts, got))
    return rows


def _seed(name: str) -> int:
    return zlib.crc32(name.encode()) & 0x7FFFFFFF


def _hit_line(name: str) -> float | None:
    if name.endswith("2r"):
        return 1.0 / 3.0
    if name.endswith("3r"):
        return 0.25
    return None


def _pair_sum(day: np.ndarray, n: int = 4000) -> np.ndarray:
    rng = np.random.default_rng(7)
    pick = rng.integers(0, len(day), size=(n, 2))
    return day[pick].sum(axis=1)


def _section(results, baselines, sizing, cuts) -> str:
    lines = [
        MARKER,
        "",
        "These are Jake Ryan's rules as written down from two months of reels. The reels are his claims. Nothing in them was checked against a brokerage statement. The rules below were fixed before this run. Every pre-declared rule is in the table. A weak holdout was not a reason to drop one.",
        "",
        "This pass does not approximate absorption from the 1-minute OHLC file. The print count is the `trades` column on the footprint, and that test is `docs/OF-VP-FOOTPRINT-TEST.md`. The first 15-second candle after 08:30 CT is not in the 1-minute file, so that funded-open push is not tested. A 1-minute bar is a different rule. The CPI straddle, a VPN, and buying a batch of accounts for a news release are left out. Those break the firm rules this book is allowed to trade under, or they need a queue-position fill. A sub-second refill of the offer is not in the footprint.",
        "",
        "The volume profile runs from the Sunday 18:00 ET open (17:00 CT) through 09:29 ET the morning of the trade. Monday afternoon is in Tuesday's profile and is not in Monday's. Volume is the 1-minute bar booked at the close, in 1-point bins. The value area is 70% around the point of control. Limits go out at 09:30 ET and cancel at 11:00 ET (10:00 CT) if they have not traded through. A fade is taken only when the point of control is at least the target distance inside the edge, so a 2R target really is a fade toward the middle.",
        "",
        (
            f"The open-reversion needs a first-five-minute push of at least {cuts['extend']:.1f} points, "
            f"the median of that push on the train window. The stop is 10 points beyond the five-minute extreme "
            "and the target is the 09:30 open. The order is live at 09:35."
        ),
        "",
        (
            f"The trend rule needs an overnight gap of at least {cuts['gap']:.1f} points, "
            "the 75th percentile of the train window. After 09:30 it waits for a sweep through the 09:00-09:30 high or low "
            "that closes back inside, then rests a limit at that level on the next bar, with the overnight trend. "
            "The stop is 12 points. The target is the overnight extreme, and only when that extreme is at least one stop away."
        ),
        "",
        "| rule | val n | val hit | val mean R | hold n | hold hit | hold mean R | random-walk hit |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    a = lines.append
    for row in results:
        null = row["null"]
        null_s = pct(null) if null is not None else "see mean R"
        a(
            f"| {row['name']} | {row['val_n']} | {pct(row['val_hit'])} | {_num(row['val_r'][0])} | "
            f"{row['hold_n']} | {pct(row['hold_hit'])} ({pct(row['hold_lo'])} to {pct(row['hold_hi'])}) | "
            f"{_num(row['hold_r'][0])} ({_num(row['hold_r'][1])} to {_num(row['hold_r'][2])}) | {null_s} |"
        )
    a("")
    a(
        "A 2R target is touched by a no-drift path about 33% of the time. A 3R target about 25%. "
        "The point-of-control fade, the open reversion, and the trend sweep do not have one reward, so that single percentage is not their null. Their mean R interval is."
    )
    a("")
    a(
        "Pass rate, one trade a day, stop sized to the max loss and no more than $2,000. "
        "A 2R win on that size is about $4,000, and a 3R win is about $6,000. "
        "The consistency rule then raises the target, because one day is more than half the profit. "
        "The fair coin wins at the no-drift rate for that reward and loses the whole stop otherwise. "
        "The ±$500 coin is the same roughly 26% baseline as the rest of this note."
    )
    a("")
    a("| rule | firm | val pass | holdout pass | holdout days |")
    a("|---|---|---:|---:|---:|")
    for row in results:
        for firm in row["passes"]:
            p = firm
            a(
                f"| {row['name']} | {p['firm']} | {pct(p['val']['pass'])} | "
                f"{pct(p['hold']['pass'])} ({pct(p['hold']['lo'])} to {pct(p['hold']['hi'])}) | {days_s(p['hold']['days'])} |"
            )
    a("")
    a("| firm | fair 2R coin | fair 3R coin | ±$500 coin |")
    a("|---|---:|---:|---:|")
    for row in baselines:
        a(
            f"| {row['firm']} | {pct(row['two']['pass'])} in {days_s(row['two']['days'])} days | "
            f"{pct(row['three']['pass'])} in {days_s(row['three']['days'])} days | "
            f"{pct(row['small']['pass'])} in {days_s(row['small']['days'])} days |"
        )
    a("")
    a("## Sizing the funded day")
    a("")
    a(
        "Same eval book as the lifecycle above (`onhl_pull_none`, the validation winner) and the same grind rate. "
        "The big day is that setup's filled 1.7:1 holdout trades, resized. "
        "Angus risks the max loss, and no more than $2,000. Where the line is $2,000, a target hit is about $3,400 before commission. "
        "FundedNext's line is $1,500, so that trade is sized to $1,500. "
        "Jake's one trade risks $1,300, the middle of his $1,200 to $1,400 band, so the 1.7 reward lands near $2,210, inside the $2,100 to $2,400 band. "
        "His two trades are two independent draws at $1,000 risk, about $1,700 each, and both are taken. "
        "They are two resamples of one setup, not two different signals. "
        "Topstep and LucidFlex pay at most $2,000 in a cycle. FundedNext Flex pays at most $1,500. "
        "A win larger than the cap stays in the account. An up day is the average of days that finished positive. "
        "A down day in the two-trade row is both trades losing. The EV is cash after the cap, the split, and the fee."
    )
    a("")
    a("| firm | sizing | mean up day | mean down day | EV per eval | payouts / 100 |")
    a("|---|---|---:|---:|---|---:|")
    for row in sizing:
        a(
            f"| {row['firm']} | {row['sizing']} | {money(row['win'])} | {money(row['loss'])} | "
            f"{money(row['life']['mean'])} ({money(row['life']['lo'])} to {money(row['life']['hi'])}) | "
            f"{row['life']['payouts_per_100']:.1f} |"
        )
    a("")
    a(_sizing_words(results, sizing))
    a("")
    return "\n".join(lines) + "\n"


def _cost_breakeven(reward: float, stop_pts: float) -> float:
    win = reward * stop_pts - 0.61
    loss = stop_pts + 0.25 + 0.61
    return loss / (win + loss)


def _sizing_words(results, sizing) -> str:
    parts = []
    covered = []
    for row in results:
        r_lo = row["hold_r"][1]
        covers = not (isinstance(r_lo, float) and not math.isnan(r_lo) and r_lo > 0)
        covered.append(covers)
        sentence = (
            f"`{row['name']}` holdout mean R is {_num(row['hold_r'][0])} "
            f"({_num(row['hold_r'][1])} to {_num(row['hold_r'][2])})."
        )
        null = row["null"]
        if null is not None and isinstance(row["hold_lo"], float) and not math.isnan(row["hold_lo"]) and row["hold_lo"] > null:
            stop_pts = 15.0 if "15" in row["name"] else 10.0
            reward = 3.0 if row["name"].endswith("3r") else 2.0
            be = _cost_breakeven(reward, stop_pts)
            side = "above" if row["hold_lo"] > be else "not above"
            sentence += (
                f" The lower end of the hit-rate interval is above the pre-cost {pct(null)} line"
                f" and {side} the {pct(be)} line after commission and one tick of stop slippage."
            )
        parts.append(sentence)
    if covered and all(covered):
        parts.append("Every one of these holdout mean-R intervals covers zero or is below it.")
    best = max(
        (p["hold"]["pass"], p["firm"], row["name"])
        for row in results
        for p in row["passes"]
        if isinstance(p["hold"]["pass"], float) and not math.isnan(p["hold"]["pass"])
    )
    parts.append(
        f"The highest holdout pass rate in the list is {pct(best[0])} for `{best[2]}` on {best[1]}. "
        "That is the neighborhood of the ±$500 coin, and it is above the fair high-R coin because a day with no fill does not take the stop. "
        "It is not the roughly 49% pass rate of the 0.75R book above. None of these rules replaces that book."
    )
    parts.append(
        "The sizing table uses the earlier 1.7:1 fills. A smaller risk does not change their hit rate. "
        "On a two-trade row, an up day can be one win and one loss, and a down day is both trades losing, about two full stops. "
        "Two trades leave the account alive after a single loss. "
        + _two_versus_one(sizing)
        + " That is the sizing, not a new signal, and the 1.7:1 hit rate still has a holdout interval that includes 37%."
    )
    return " ".join(parts)


def _two_versus_one(sizing) -> str:
    by_firm: dict[str, dict[str, float]] = {}
    for row in sizing:
        kind = "two" if "two trades" in row["sizing"] else ("one" if "Jake, one" in row["sizing"] else "angus")
        by_firm.setdefault(row["firm"], {})[kind] = row["life"]["mean"]
    bits = []
    for firm, vals in by_firm.items():
        bits.append(
            f"On {firm} the two-trade EV is {money(vals['two'])} against {money(vals['angus'])} for the single full-risk trade "
            f"and {money(vals['one'])} for the single $1,300 trade."
        )
    return " ".join(bits)


def main() -> None:
    df = load_bars(str(ROOT_DATA))
    sessions = build_sessions(df)
    profiles = profiles_at_open(df)
    print("sessions", len(sessions), "profiles", len(profiles), flush=True)
    gaps = np.array([
        abs(s.rth_open - float(s.pdc))
        for s in sessions
        if s.ts < TRAIN_END and np.isfinite(s.pdc)
    ])
    extends = []
    for s in sessions:
        if s.ts >= TRAIN_END:
            continue
        span = _five(s)
        if span is None:
            continue
        hi, lo, op = span
        extends.append(max(hi - op, op - lo))
    gap_cut = float(np.quantile(gaps, 0.75))
    extend_cut = float(np.median(extends))
    print("gap_cut", round(gap_cut, 2), "extend_cut", round(extend_cut, 2), flush=True)
    firm_list = firms()
    results = []
    for name, kind, stop, reward in RULES:
        print(name, flush=True)
        rows = _run(sessions, profiles, kind, stop, reward, gap_cut, extend_cut)
        val = _period(rows, TRAIN_END, VAL_END)
        hold = _period(rows, VAL_END, None)
        null = _hit_line(name)
        val_hits = sum(r["target_hit"] for r in val if r["filled"])
        hold_hits = sum(r["target_hit"] for r in hold if r["filled"])
        val_n = sum(r["filled"] for r in val)
        hold_n = sum(r["filled"] for r in hold)
        test = hit_vs_random(hold_hits, hold_n, null if null is not None else 0.5)
        hold_sessions = len(hold)
        passes = []
        for spec in firm_list:
            risk = min(2000.0, float(spec["mll"]))
            if val_n < 30:
                val_stat = {"pass": float("nan"), "lo": float("nan"), "hi": float("nan"), "days": float("nan")}
            else:
                val_stat = eval_stats(day_dollars(val, risk, spec["rate"]), spec, _seed(name + spec["firm"]))
            if hold_n < 30:
                hold_stat = {"pass": float("nan"), "lo": float("nan"), "hi": float("nan"), "days": float("nan")}
            else:
                hold_stat = eval_stats(
                    day_dollars(hold, risk, spec["rate"]), spec, _seed(name + spec["firm"] + "h"),
                )
            passes.append({"firm": spec["firm"], "val": val_stat, "hold": hold_stat})
        results.append({
            "name": name,
            "val_n": val_n,
            "hold_n": hold_n,
            "val_hit": (val_hits / val_n) if val_n else float("nan"),
            "hold_hit": test["hit"],
            "hold_lo": test["lo"],
            "hold_hi": test["hi"],
            "val_r": mean_r_ci(val),
            "hold_r": mean_r_ci(hold),
            "null": null,
            "passes": passes,
            "hold_sessions": hold_sessions,
        })
    baselines = []
    for spec in firm_list:
        risk = min(2000.0, float(spec["mll"]))
        two = np.where(np.random.default_rng(2).random(4000) < (1.0 / 3.0), 2.0 * risk, -risk)
        three = np.where(np.random.default_rng(3).random(4000) < 0.25, 3.0 * risk, -risk)
        small = np.where(np.random.default_rng(4).random(4000) < 0.50, 500.0, -500.0)
        baselines.append({
            "firm": spec["firm"],
            "two": eval_stats(two, spec, 51),
            "three": eval_stats(three, spec, 52),
            "small": eval_stats(small, spec, 53),
        })
    ev_rows = run_variant(sessions, "onhl", "pull", "none", True, EVAL_R)
    fu_rows = run_variant(sessions, "onhl", "pull", "none", True, FUNDED_R)
    ev_hold = _period(ev_rows, VAL_END, None)
    fu_hold = [r for r in _period(fu_rows, VAL_END, None) if r["filled"]]
    grind = sum(r["target_hit"] for r in ev_hold if r["filled"]) / max(sum(r["filled"] for r in ev_hold), 1)
    sizing = []
    for spec in firm_list:
        risk_cap = min(2000.0, float(spec["mll"]))
        ev_day = day_dollars(ev_hold, risk_cap, spec["rate"])
        jake_one = min(1300.0, risk_cap)
        jake_two = min(1000.0, risk_cap)
        books = (
            (f"Angus, one trade risking {money(risk_cap)}", day_dollars(fu_hold, risk_cap, spec["rate"]), 40),
            (f"Jake, one trade risking {money(jake_one)}", day_dollars(fu_hold, jake_one, spec["rate"]), 41),
            (
                f"Jake, two trades risking {money(jake_two)} each",
                _pair_sum(day_dollars(fu_hold, jake_two, spec["rate"])),
                42,
            ),
        )
        for label, day, seed in books:
            wins = day[day > 0]
            losses = day[day < 0]
            life = lifecycle(ev_day, day, grind, spec, np.random.default_rng(seed), n=1500)
            sizing.append({
                "firm": spec["firm"],
                "sizing": label,
                "win": float(wins.mean()) if len(wins) else float("nan"),
                "loss": float(losses.mean()) if len(losses) else float("nan"),
                "life": life,
            })
            print(spec["firm"], label, round(life["mean"], 1), flush=True)
    section = _section(results, baselines, sizing, {"gap": gap_cut, "extend": extend_cut})
    old = OUT.read_text()
    if MARKER in old:
        kept = old[: old.index(MARKER)]
    else:
        kept = old
    OUT.write_text(kept.rstrip() + "\n\n" + section)
    print("wrote", OUT, flush=True)


if __name__ == "__main__":
    main()
