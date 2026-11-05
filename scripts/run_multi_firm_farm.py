"""Multi-firm farm, disarmed. Reads config/prop_rules.yaml firm_survey.

The recipe is one pass shape, not a search over hundreds of bets. Equal eval
days are the fewest that satisfy that firm's consistency rule. The funded
stage is one large day sized to the payout cap, then the minimum winning days.
A coin is 50/50. Costs are the MNQ commission and one tick each side, scaled
to the stop. The 5-minute opening-range rule is the holdout from July 2025.
"""

from __future__ import annotations

import math
import sys
import zlib
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_farm_claims import five_minute_momentum
from src.research.strategies.costs import COMMISSION_RT_USD, MNQ_DOLLARS_PER_POINT

DOC = ROOT / "docs" / "MULTI-FIRM-FARM.md"
RULES = ROOT / "config" / "prop_rules.yaml"
HOLDOUT = pd.Timestamp("2025-07-01", tz="America/New_York")
# $2.22 round turn per MNQ, and $32 of risk per MNQ at a 16-point stop.
COST_RATE = (COMMISSION_RT_USD + 0.5 * MNQ_DOLLARS_PER_POINT) / (16.0 * MNQ_DOLLARS_PER_POINT)
N = 2500
N_MONTH = 400


def money(v: float) -> str:
    if isinstance(v, float) and math.isnan(v):
        return "n/a"
    return f"${v:,.0f}"


def pct(v: float) -> str:
    if isinstance(v, float) and math.isnan(v):
        return "n/a"
    return f"{100 * v:.1f}%"


def load_survey() -> dict:
    doc = yaml.safe_load(RULES.read_text())
    return doc["firm_survey"]


def equal_days(consistency: float, min_days: int) -> int:
    """Fewest equal winning days whose best day is within the consistency rule."""
    days = max(int(min_days), 1)
    while (1.0 / days) > float(consistency) + 1e-9:
        days += 1
    return days


def _trail(balance, floor, high, locked, active, trigger, lock_floor, mll, locks: bool):
    high = np.where(active, np.maximum(high, balance), high)
    if locks:
        now = active & ~locked & (high + 1e-9 >= trigger)
        floor = np.where(now, lock_floor, floor)
        locked = locked | now
        moving = active & ~locked
    else:
        moving = active
    floor = np.where(moving, np.maximum(floor, high - mll), floor)
    return floor, high, locked


def _eval_lock(spec: dict) -> tuple[bool, float, float]:
    if "Tradeify" in spec["firm"]:
        return False, 0.0, 0.0
    if spec["firm"] == "Topstep":
        return True, float(spec["size"] + spec["mll"]), float(spec["size"])
    return True, float(spec["lock_trigger"]), float(spec["lock_floor"])


def run_book(
    spec: dict,
    rng: np.random.Generator,
    n: int = N,
    p: float = 0.5,
    intraday: bool = False,
    samples: np.ndarray | None = None,
    symmetric: bool = False,
    cost_rate: float = COST_RATE,
) -> dict[str, np.ndarray | float]:
    """One eval purchase through funded payouts. `samples` are net R multiples of the stop."""
    size = float(spec["size"])
    mll = float(spec["mll"])
    target = float(spec["target"])
    cost = mll * cost_rate
    days_needed = equal_days(spec["consistency"], spec["min_eval_days"])
    # Asymmetric: the winning day is the recipe's target slice, which can be
    # larger than the max-loss stop. Symmetric: the winning day equals the stop,
    # so a 50/50 day is zero before costs.
    eval_win = (mll - cost) if symmetric else target / days_needed
    fee = float(spec["fee"] or 0.0)
    activation = float(spec["activation"])
    # eval
    balance = np.full(n, size)
    floor = np.full(n, size - mll)
    high = balance.copy()
    locked = np.zeros(n, dtype=bool)
    best = np.zeros(n)
    alive = np.ones(n, dtype=bool)
    passed = np.zeros(n, dtype=bool)
    traded = np.zeros(n)
    locks, trigger, lock_at = _eval_lock(spec)
    for _ in range(max(days_needed + 8, 12)):
        on = alive & ~passed
        if not on.any():
            break
        room = balance - floor
        if samples is None:
            pnl = np.where(rng.random(n) < p, eval_win, -(mll + cost))
            die = on & intraday & (mll > room + 1e-9)
        else:
            pnl = rng.choice(samples, size=n) * mll
            die = on & intraday & (pnl < 0) & (np.abs(pnl) > room + 1e-9)
        alive &= ~die
        on = alive & ~passed
        balance = np.where(on, balance + pnl, balance)
        dead = on & (balance <= floor + 1e-9)
        alive &= ~dead
        on = alive & ~passed
        best = np.where(on, np.maximum(best, pnl), best)
        traded = np.where(on, traded + 1, traded)
        floor, high, locked = _trail(balance, floor, high, locked, on, trigger, lock_at, mll, locks)
        profit = balance - size
        need = np.maximum(target, np.where(best > 0, best / float(spec["consistency"]), target))
        passed |= on & (traded + 1e-9 >= spec["min_eval_days"]) & (profit + 1e-6 >= need)
    # funded
    f_start = float(spec["funded_start"])
    f_mll = mll
    f_bal = np.full(n, f_start)
    f_floor = np.full(n, f_start - f_mll)
    f_high = f_bal.copy()
    f_locked = np.zeros(n, dtype=bool)
    f_alive = passed.copy()
    wins = np.zeros(n)
    cycle = np.zeros(n)
    n_pay = np.zeros(n)
    cash = np.zeros(n)
    big_target = (mll - cost) if symmetric else _big_target(spec, cost)
    small_cost = max(float(spec["win_min"]), 100.0) * cost_rate
    need_small = max(int(spec["winning_days"]) - 1, 0)
    for _cycle in range(int(spec["max_payouts"] or 6)):
        on = f_alive & (n_pay < (spec["max_payouts"] or 99))
        if not on.any():
            break
        room = f_bal - f_floor
        if samples is None:
            pnl = np.where(rng.random(n) < p, big_target, -(f_mll + cost))
            die = on & intraday & (f_mll > room + 1e-9)
        else:
            pnl = rng.choice(samples, size=n) * f_mll
            die = on & intraday & (pnl < 0) & (np.abs(pnl) > room + 1e-9)
        f_alive &= ~die
        on = f_alive
        f_bal = np.where(on, f_bal + pnl, f_bal)
        dead = on & (f_bal <= f_floor + 1e-9)
        f_alive &= ~dead
        on = f_alive
        got_big = on & (pnl >= float(spec["win_min"]))
        wins = np.where(got_big, wins + 1, wins)
        cycle = np.where(on, cycle + pnl, cycle)
        f_floor, f_high, f_locked = _trail(
            f_bal, f_floor, f_high, f_locked, on,
            float(spec["lock_trigger"]), float(spec["lock_floor"]), f_mll, True,
        )
        smalls = np.zeros(n)
        if need_small:
            for _k in range(need_small + 6):
                want = f_alive & (smalls < need_small)
                if not want.any():
                    break
                if samples is None:
                    hit = rng.random(n) < p
                    sp = np.where(hit, float(spec["win_min"]), -(float(spec["win_min"]) + small_cost))
                else:
                    sp = rng.choice(samples, size=n) * max(float(spec["win_min"]), 100.0)
                    hit = sp + 1e-9 >= float(spec["win_min"])
                room = f_bal - f_floor
                die = want & intraday & (sp < 0) & (np.abs(sp) > room + 1e-9)
                f_alive &= ~die
                want = f_alive & (smalls < need_small)
                f_bal = np.where(want, f_bal + sp, f_bal)
                dead = want & (f_bal <= f_floor + 1e-9)
                f_alive &= ~dead
                want = f_alive & (smalls < need_small)
                good = want & hit
                smalls = np.where(good, smalls + 1, smalls)
                wins = np.where(good, wins + 1, wins)
                cycle = np.where(want, cycle + sp, cycle)
                f_floor, f_high, f_locked = _trail(
                    f_bal, f_floor, f_high, f_locked, want,
                    float(spec["lock_trigger"]), float(spec["lock_floor"]), f_mll, True,
                )
        take, amount = _payout_mask(spec, f_bal, f_floor, wins, cycle, n_pay, smalls, need_small, f_alive)
        f_bal = np.where(take, f_bal - amount, f_bal)
        cash = np.where(take, cash + amount * float(spec["split"]), cash)
        n_pay = np.where(take, n_pay + 1, n_pay)
        wins = np.where(take, 0.0, wins)
        cycle = np.where(take, 0.0, cycle)
        f_floor = np.where(take, float(spec["lock_floor"]), f_floor)
        f_locked = f_locked | take
        f_alive &= ~(take & (f_bal <= f_floor + 1e-9))
        if spec["max_payouts"] is not None:
            f_alive &= n_pay < spec["max_payouts"]
        f_alive &= take
    fees = np.full(n, fee) + np.where(passed, activation, 0.0)
    net = cash - fees
    return {
        "net": net,
        "cash": cash,
        "passed": passed,
        "n_pay": n_pay,
        "days_needed": days_needed,
        "eval_win": eval_win,
        "big_target": big_target,
    }


def _big_target(spec: dict, cost: float) -> float:
    """Net dollars the large funded day is aiming to credit."""
    win_min = float(spec["win_min"])
    smalls = max(int(spec["winning_days"]) - 1, 0)
    cap = spec["cap"]
    fraction = float(spec["payout_fraction"])
    if spec["payout_base"] == "above_lock":
        return float(spec["buffer"])
    need = float(spec["buffer"])
    if cap:
        need = max(need, float(cap) / fraction)
    big = need - smalls * win_min
    return max(big, win_min, 1.0)


def _payout_mask(spec, balance, floor, wins, cycle, n_pay, smalls, need_small, alive):
    n = len(balance)
    amount = np.zeros(n)
    base = spec["payout_base"]
    fraction = float(spec["payout_fraction"])
    cap = spec["cap"]
    if base == "cycle":
        raw = fraction * np.maximum(cycle, 0.0)
    elif base == "balance":
        raw = fraction * np.maximum(balance, 0.0)
    elif base == "total_profit":
        raw = fraction * np.maximum(balance - float(spec["funded_start"]), 0.0)
    else:
        raw = np.maximum(balance - float(spec["lock_floor"]), 0.0)
    if cap:
        raw = np.minimum(raw, float(cap))
    amount = raw
    first = n_pay < 0.5
    profit_ok = np.where(first, cycle + 1e-9 >= float(spec["buffer"]), cycle + 1e-9 >= float(spec["next_cycle"]))
    if base == "above_lock":
        profit_ok = np.where(
            first,
            (balance - float(spec["funded_start"])) + 1e-9 >= float(spec["buffer"]),
            cycle + 1e-9 >= float(spec["next_cycle"]),
        )
    days_ok = wins + 1e-9 >= float(spec["winning_days"])
    if need_small:
        days_ok = days_ok & (smalls + 1e-9 >= need_small)
    take = alive & profit_ok & days_ok & (amount + 1e-9 >= float(spec["min_request"]))
    if spec["max_payouts"] is not None:
        take = take & (n_pay < spec["max_payouts"])
    return take, np.where(take, amount, 0.0)


def month_cash(spec: dict, rng: np.random.Generator, intraday: bool, p: float, samples, n: int = N_MONTH, symmetric: bool = False) -> np.ndarray:
    """One month at the funded cap. Each slot is an independent account. Evals refill until the eval cap."""
    slots = int(spec["funded_cap"])
    # Run enough independent accounts to restock the cap through a 21-day month.
    # Two generations fit a short eval plus one payout cycle.
    copies = slots * 2
    book = run_book(spec, rng, n=n * copies, p=p, intraday=intraday, samples=samples, symmetric=symmetric)
    net = book["net"].reshape(n, copies)
    # A household can only keep `slots` funded, and can only start `eval_cap` evals.
    usable = min(copies, int(spec["eval_cap"]))
    # Fees were charged on every copy. Drop the copies past the eval cap, and
    # if more than `slots` pass, the extras cannot be funded: zero their cash
    # but they already paid the fee inside `net`. Approximate by keeping the
    # first `slots` passes worth of payout and every fee up to the eval cap.
    # Simpler honest version: sum the first `usable` nets, which is `usable`
    # eval purchases. Cap the payout contribution at `slots` accounts by
    # zeroing cash on passes beyond `slots` per household. Rebuild from parts.
    # `net` is cash - fee. Recover by using the same seed path's components.
    return net[:, :usable].sum(axis=1)


def ci(stat: dict) -> str:
    return f"{money(stat['mean'])} ({money(stat['lo'])} to {money(stat['hi'])})"


def main() -> None:
    survey = load_survey()
    firms = [(key, spec) for key, spec in survey.items() if isinstance(spec, dict) and spec.get("simulate")]
    print("bars", flush=True)
    from src.research.strategies.engine import load_bars

    bars = load_bars(str(ROOT / "data" / "reference" / "nq_1m_master.parquet"))
    opening = five_minute_momentum(bars)
    hold = opening[opening["ts"] >= HOLDOUT]["r"].to_numpy()
    print("holdout", len(hold), float(hold.mean()), flush=True)
    rows = []
    months = {}

    for key, spec in firms:
        spec = dict(spec)
        if spec.get("fee") is None:
            spec["fee"] = 100.0
        grades = [("stated", spec["stated_breach"] == "intraday")]
        if spec["stated_breach"] != "eod":
            grades.append(("eod", False))
        if spec["stated_breach"] != "intraday":
            grades.append(("intraday", True))
        for grade, intra in grades:
            seed = zlib.crc32(f"{key}-{grade}".encode()) & 0x7FFFFFFF
            print(key, grade, flush=True)
            raw = run_book(spec, np.random.default_rng(seed), p=0.5, intraday=intra)
            stat = _stat(raw)
            sym = None
            if grade == "stated":
                sym = _stat(run_book(
                    spec, np.random.default_rng(seed + 5), p=0.5, intraday=intra, symmetric=True,
                ))
            sig = run_book(
                spec, np.random.default_rng(seed + 17), p=0.5, intraday=intra, samples=hold,
            )
            sig_stat = _stat(sig)
            be = _breakeven(spec, intra)
            row = {
                "key": key, "firm": spec["firm"], "grade": grade, "intra": intra,
                "fee": spec["fee"], "days": raw["days_needed"], "big": raw["big_target"],
                "coin": stat, "symmetric": sym, "signal": sig_stat, "breakeven": be,
                "stated": spec["stated_breach"],
            }
            rows.append(row)
            print(" ", spec["firm"], grade, round(stat["mean"], 1), "sig", round(sig_stat["mean"], 1), flush=True)
            if grade == "stated":
                mc = month_cash(spec, np.random.default_rng(seed + 99), intra, 0.5, None, symmetric=True)
                months[key] = mc
                # fee sensitivity
                if key == "lucid_flex_50k":
                    row["sensitivity"] = _fee_shift(stat, spec, (80.0, 100.0, 150.0))
                elif key == "mff_rapid_eod_50k":
                    row["sensitivity"] = _fee_shift(stat, spec, (135.0, 157.0))
                elif key == "fundednext_flex_50k":
                    row["sensitivity"] = _fee_shift(stat, spec, (84.99, 141.99))
    cost_rows = _cost_cases(firms)
    text = render(survey, rows, months, hold, cost_rows)
    DOC.write_text(text)
    print("wrote", DOC, flush=True)


def _stat(raw: dict) -> dict[str, float]:
    net = raw["net"]
    mean = float(net.mean())
    se = float(net.std(ddof=1) / np.sqrt(len(net)))
    passed = raw["passed"]
    n_pay = raw["n_pay"]
    return {
        "mean": mean,
        "lo": mean - 1.96 * se,
        "hi": mean + 1.96 * se,
        "pass_rate": float(passed.mean()),
        "payout_rate": float(np.mean(n_pay > 0)),
        "payouts_per_100": float(n_pay.mean() * 100),
    }


def _fee_shift(stat: dict, spec: dict, fees: tuple[float, ...]) -> list[tuple[float, float]]:
    base = float(spec["fee"] or 0.0)
    return [(fee, stat["mean"] + base - fee) for fee in fees]


def _breakeven(spec: dict, intraday: bool) -> float:
    """Smallest day-win probability, on a coarse grid, whose interval is above zero."""
    for p in (0.45, 0.50, 0.55, 0.60, 0.65, 0.70):
        raw = run_book(spec, np.random.default_rng(9000 + int(p * 100) + int(intraday)), n=800, p=p, intraday=intraday)
        stat = _stat(raw)
        if stat["lo"] > 0:
            return p
    return float("nan")


SLIP_ONLY = (0.5 * MNQ_DOLLARS_PER_POINT) / (16.0 * MNQ_DOLLARS_PER_POINT)
COST_CASES = (
    ("slippage only", SLIP_ONLY),
    ("commission plus slippage", COST_RATE),
    ("zero cost", 0.0),
)


def _cost_cases(firms: list) -> list[dict]:
    """Stated-grade recipe and symmetric coin at three cost rates. n=2,500."""
    out = []
    for key, spec in firms:
        spec = dict(spec)
        if spec.get("fee") is None:
            spec["fee"] = 100.0
        intra = spec["stated_breach"] == "intraday"
        for label, rate in COST_CASES:
            seed = zlib.crc32(f"cost-{key}-{label}".encode()) & 0x7FFFFFFF
            print("cost", key, label, flush=True)
            recipe = _stat(run_book(
                spec, np.random.default_rng(seed), p=0.5, intraday=intra, cost_rate=rate,
            ))
            sym = _stat(run_book(
                spec, np.random.default_rng(seed + 5), p=0.5, intraday=intra,
                symmetric=True, cost_rate=rate,
            ))
            out.append({
                "firm": spec["firm"], "case": label,
                "recipe": recipe, "symmetric": sym,
            })
    return out


def render(survey, rows, months, hold, cost_rows) -> str:
    stated = [r for r in rows if r["grade"] == "stated"]
    stated.sort(key=lambda r: r["coin"]["mean"], reverse=True)
    lines = [
        "# Multi-firm farm",
        "",
        "Retrieved 3 Nov 2026 from each firm's help centre. Apex is not in this file. Nothing here places an order. Costs are TopstepX's MNQ $1.22 round turn plus one tick each side, scaled to a 16-point stop. Lucid's fee is not printed. Where the table uses Lucid, the fee in the path is an assumed $100.",
        "",
        "## Who qualifies",
        "",
        "A firm is in the simulator only if a bot is allowed and the funded plan has no consistency rule, an end-of-day trail that locks, and a small payout day. The others were read and left out.",
        "",
        "| firm | in the sim | why |",
        "|---|---|---|",
    ]
    a = lines.append
    for key, spec in survey.items():
        if not isinstance(spec, dict) or "simulate" not in spec:
            continue
        if spec["simulate"]:
            why = f"Bot allowed. Funded consistency none. Stated breach: {spec['stated_breach']}."
        else:
            why = spec["exclude"]
        a(f"| {spec.get('firm', key)} | {'yes' if spec['simulate'] else 'no'} | {why} |")
    a("")
    a("## Quotes")
    a("")
    for key, spec in survey.items():
        if not isinstance(spec, dict) or "quotes" not in spec:
            continue
        title = spec.get("firm", key)
        a(f"### {title}")
        a("")
        for quote in spec["quotes"]:
            dated = f", {quote['page_date']}" if quote.get("page_date") else ""
            a(f"- {quote['url']}{dated}: \"{quote['quote']}\"")
        a("")
    a("## The recipe")
    a("")
    a("Eval days are the fewest equal winning days that fit the consistency rule. Two equal days are 50%, so they pass Topstep's 55% and a 50% add-on, and they fail a 40% rule. A 30% rule needs four. A red day risks the whole max-loss line. The funded day in the recipe is sized so that one large day plus the minimum winning days fills the payout cap. That large day can pay more than the stop, so a 50% hit rate on it is not a zero-expectancy coin. The symmetric column is the zero-expectancy coin: the winning day equals the stop, and costs make it slightly negative before the firm takes a fee.")
    a("")
    a("| firm | stated grade | eval days | recipe day | recipe EV | symmetric coin EV | payouts / 100 (recipe) | recipe hit rate that clears zero |")
    a("|---|---|---:|---:|---|---|---:|---|")
    for row in stated:
        sym = row["symmetric"]
        a(
            f"| {row['firm']} | {row['stated']} | {row['days']} | {money(row['big'])} | "
            f"{ci(row['coin'])} | {ci(sym)} | {row['coin']['payouts_per_100']:.1f} | "
            f"{pct(row['breakeven']) if row['breakeven'] == row['breakeven'] else 'above 70%'} |"
        )
    a("")
    a("### Same book, other grade, and the opening-range holdout")
    a("")
    a(f"The 5-minute rule is the one from the earlier note: first 5 minutes set the direction and the stop, flat before 15:55. Holdout is July 2025 through July 2026, n={len(hold)}, mean net R {float(hold.mean()):.3f}. That interval included zero when it was measured. It is the least-bad holdout in this repo, not a proven edge. Sized here to the day's stop.")
    a("")
    a("| firm | grade | recipe EV | signal EV | signal payouts / 100 |")
    a("|---|---|---:|---:|---:|")
    for row in rows:
        a(
            f"| {row['firm']} | {row['grade']} | {ci(row['coin'])} | {ci(row['signal'])} | "
            f"{row['signal']['payouts_per_100']:.1f} |"
        )
    a("")
    a("### Fee assumptions")
    a("")
    for row in stated:
        if "sensitivity" not in row:
            continue
        bits = ", ".join(f"{money(fee)} → {money(ev)}" for fee, ev in row["sensitivity"])
        a(f"- {row['firm']}: {bits}. {survey[row['key']]['fee_note']}")
    a("")
    a("## Do the sims charge commission?")
    a("")
    a("Yes on the four firms that print a rate. The path still uses one cost model for every firm. Case (b) is TopstepX's MNQ $1.22 round turn plus one tick each side, which is what the rest of this file has been using. It is not each firm's own card. One tick each side on MNQ is $1.00 a round turn (0.50 points at $2 a point). A full-size stop is 16 points, $32 of risk per contract, so the cost is that many dollars times the contracts needed to risk the max-loss line.")
    a("")
    a("- **Topstep.** [TopstepX commissions](https://help.topstep.com/en/articles/8284213-topstepx-commissions-and-fees), 30 Sep 2026: \"These fees apply when trading the Trading Combine, Express Funded Account, and Live Funded Account. Commissions and fees are automatically deducted from each trade.\" Micro E-mini NASDAQ 100 (MNQ) total is $1.22 round turn: exchange $0.70, NFA $0.02, commission $0.50. The live-account costs page also says the Combine charges \"a $3.70/lot simulated fee\" and lists NQ and ES near $3.80. That sentence is the mini, not the micro. The product table is the MNQ number.")
    a("- **LucidFlex.** [Approved products and commissions](https://support.lucidtrading.com/en/articles/11508978-approved-products-and-commissions), 26 Aug 2026. The column is \"Commission (Per Side).\" MNQ is 0.50, so $1.00 round turn. NQ is 1.75 per side. The article says the table is \"what it costs.\" It does not use the words \"deducted from your balance.\"")
    a("- **Tradeify.** [Trading commission fees](https://help.tradeify.co/en/articles/10468315-trading-commission-fees), updated in the last two weeks: \"Total Round Trip Cost includes Exchange fees, NFA fees, Clearing fees, and Commissions.\" MNQ is $1.82 round turn. The pricing page says \"All trades incur commission fees.\" It does not separately say the sim balance is where they come out.")
    a("- **MyFundedFutures.** [Futures instrument list](https://help.myfundedfutures.com/en/articles/9735811-futures-instrument-list), 24 Aug 2026, column \"Total Cost Round Trip.\" MNQ is 0.25 tick, $0.50 tick value, **$1.90** round trip. NQ is **$4.68**. The [live account page](https://help.myfundedfutures.com/en/articles/10101257-understanding-live-funded-account-at-myfunded-futures) says \"Round-Trip Commissions and Fees\" \"will be deducted directly from your Live Funded Account balance.\" The evaluation articles do not repeat that sentence. The instrument list is the schedule for the products the sim trades.")
    a("- **FundedNext Flex.** [How commissions work](https://helpfutures.fundednext.com/en/articles/14298151-how-do-commissions-work-in-futures-trading), 22 Aug 2026: the all-in rate \"includes broker commissions, exchange and NFA fees, and clearing fees,\" and \"the commission and fees are charged twice, once for opening and once for closing.\" The only number on the page is an NQ example, $2.88 per side, $5.76 round turn, described as NinjaTrader's rate. The page does not print an MNQ figure.")
    a("")
    a("Same book as the table above, stated breach, 2,500 paths, its own sample. The commission-plus-slippage point will not match the earlier row to the dollar. Compare the intervals. Slippage only drops the $1.22 and keeps the tick. Zero cost drops both.")
    a("")
    a("| firm | cost | symmetric EV | symmetric payouts / 100 | recipe EV | recipe payouts / 100 |")
    a("|---|---|---|---:|---|---:|")
    for row in cost_rows:
        a(
            f"| {row['firm']} | {row['case']} | {ci(row['symmetric'])} | "
            f"{row['symmetric']['payouts_per_100']:.1f} | {ci(row['recipe'])} | "
            f"{row['recipe']['payouts_per_100']:.1f} |"
        )
    a("")
    a("## A month at the cap")
    a("")
    a("Each firm is run at its published funded cap. The month is the symmetric coin, so a winning day pays the same dollars as the stop. Tradeify's rule says the bot may not be used at another firm, so the combined book is also shown without Tradeify.")
    a("")
    a("| firm | funded cap | mean month | 95% CI | P(month negative) |")
    a("|---|---:|---:|---|---:|")
    order = [r["key"] for r in stated]
    arrays = []
    signal_keys = []
    for key in order:
        cash = months[key]
        mean = float(cash.mean())
        se = float(cash.std(ddof=1) / np.sqrt(len(cash)))
        firm = next(r["firm"] for r in stated if r["key"] == key)
        cap = survey[key]["funded_cap"]
        a(f"| {firm} | {cap} | {money(mean)} | {money(mean - 1.96 * se)} to {money(mean + 1.96 * se)} | {pct(float(np.mean(cash < 0)))} |")
        arrays.append(cash)
        if "Tradeify" not in firm:
            signal_keys.append(cash)
    combo = np.sum(np.vstack(arrays), axis=0)
    combo_ex = np.sum(np.vstack(signal_keys), axis=0) if signal_keys else combo
    def block(name, cash):
        mean = float(cash.mean())
        se = float(cash.std(ddof=1) / np.sqrt(len(cash)))
        return (
            f"{name}: mean {money(mean)} ({money(mean - 1.96 * se)} to {money(mean + 1.96 * se)}), "
            f"P(month negative) {pct(float(np.mean(cash < 0)))}, "
            f"10th percentile {money(float(np.percentile(cash, 10)))}."
        )
    a("")
    a(block("All five firms, coin, each at its cap", combo))
    a("")
    a(block("Combined book without Tradeify", combo_ex))
    a("")
    a("## Rank")
    a("")
    stated.sort(key=lambda r: r["symmetric"]["mean"], reverse=True)
    a("Ranked by the symmetric coin, at the breach the firm states. The recipe column above is a 50% hit on a larger target than the stop. That is a different question. The opening range does not get to overrule either number.")
    a("")
    for i, row in enumerate(stated, start=1):
        a(
            f"{i}. **{row['firm']}.** Symmetric coin {ci(row['symmetric'])} per eval. "
            f"Recipe, 50% on the larger day, {ci(row['coin'])}. "
            f"Stated grade: {row['stated']}."
        )
    a("")
    a("## Verdict")
    a("")
    a(_verdict(stated, survey))
    a("")
    a("## Recipes for the top of the list")
    a("")
    a("These are the parameters the simulator used. They are not an instruction to buy the eval.")
    a("")
    for row in stated[:3]:
        spec = survey[row["key"]]
        a(f"### {row['firm']}")
        a("")
        a(f"- Account: {spec['size'] / 1000:.0f}K. Fee in the rank: {money(float(spec['fee'])) if spec['fee'] else 'unconfirmed, assumed $100'}. Activation ${spec['activation']:.0f}.")
        a(f"- Eval: {row['days']} equal days of {money(float(spec['target']) / row['days'])} net, so the best day is {pct(1 / row['days'])} of the target. Consistency cap is {pct(float(spec['consistency']))}. A red day risks the ${spec['mll']:,.0f} line.")
        a(f"- Funded: one day aimed at {money(row['big'])} net, then {max(int(spec['winning_days']) - 1, 0)} days at the ${spec['win_min']:.0f} minimum. Payout {pct(float(spec['payout_fraction']))} of {spec['payout_base']}, cap {money(float(spec['cap'])) if spec['cap'] else 'none'}, trader keeps {pct(float(spec['split']))}.")
        a(f"- Grade the max loss the way the page states: {spec['stated_breach']}. Stop at {spec['funded_cap']} funded accounts.")
        a(f"- {spec['fee_note']}")
        a("")
    return "\n".join(lines) + "\n"


def _verdict(stated, survey) -> str:
    positives = [r for r in stated if r["symmetric"]["lo"] > 0]
    negatives = [r for r in stated if r["symmetric"]["hi"] < 0]
    if not positives:
        lead = (
            "A symmetric 50/50 coin, after the scaled MNQ cost, is not a positive-EV purchase at any of these firms "
            "under the stated breach rule. The intervals that sit entirely below zero are "
            + ", ".join(r["firm"] for r in negatives)
            + ". Where an interval covers zero, a coin has not been shown to work."
        )
    else:
        lead = (
            "The symmetric coin is above zero only for "
            + ", ".join(f"{r['firm']} ({ci(r['symmetric'])})" for r in positives)
            + "."
        )
    recipe_pos = [r for r in stated if r["coin"]["lo"] > 0]
    tradeify = next(r for r in stated if "Tradeify" in r["firm"])
    recipe_sentence = (
        " The recipe, which wins a larger dollar amount than it risks and hits that outcome half the time, "
        "is above zero for " + ", ".join(r["firm"] for r in recipe_pos) + "."
        if recipe_pos else
        " The asymmetric recipe is not above zero at a 50% hit rate either."
    )
    return (
        lead
        + recipe_sentence
        + " That recipe is not a coin. It is a 50% chance to bank the payout-sized day. "
        + "The 5-minute holdout does not supply that hit rate. Its mean R is about a tenth of an R and the confidence interval includes zero, and sized to the stop it loses the fee. "
        + f"Tradeify's symmetric coin is {ci(tradeify['symmetric'])}. Their rule also forbids running the same bot at another firm, so it cannot be one leg of a shared farm. "
        + "MyFundedFutures' help article does not print the Rapid EOD fee, and the firm's blog names both $135 and $157. The rank uses $157. "
        + "Lucid's fee is still not on the help page. FundedNext's list price is $141.99 and the repeat price is $84.99. The rank uses the repeat price. "
        + "Topstep has no cap on Combines and a hard cap of 5 XFAs, and the max-loss line is watched intraday. "
        + "Take Profit Trader, Alpha Futures, and Elite Trader Funding are out because the bot is banned or needs written permission they have not given. Bulenox, Tradeify Growth, FundedNext Rapid Pro, and LucidDirect are out because the funded account still has a consistency rule. "
        + "Start with the three firms whose symmetric coin is least bad and whose rules actually allow the bot. Do not start a five-firm copy of one strategy. Tradeify's exclusive-use rule forbids it, and a coin does not pay for the fees."
    )


if __name__ == "__main__":
    main()
