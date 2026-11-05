"""Test the prop-farm claims and append them to docs/STRATEGY-RESEARCH.md.

Disarmed. No orders. The opening-range rule and the three-bar gap are his
constraints, not a search. Holdout starts 2025-07-01 and is not used to pick
either rule.
"""

from __future__ import annotations

import math
import sys
import zlib
from itertools import pairwise
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.research.prop.farm import (
    household_batch,
    lucid_coin,
    lucid_recipe_run,
    recipe_summary,
    topstep_coin,
)
from src.research.prop.optimise import (
    ANGUS_POLICY,
    PREDECLARED,
    Policy,
    run_lucidflex,
)
from src.research.prop.optimise import summarise as opt_summarise
from src.research.strategies.costs import (
    COMMISSION_POINTS,
    FLAT_MINUTE,
    TICK,
)
from src.research.strategies.engine import load_bars, simulate

DOC = ROOT / "docs" / "STRATEGY-RESEARCH.md"
MARKER = "\n## The prop-farm claim\n"
HOLDOUT = pd.Timestamp("2025-07-01", tz="America/New_York")
N_COIN = 4000
N_RECIPE = 3000
N_BATCH = 600


def money(v: float) -> str:
    if isinstance(v, float) and math.isnan(v):
        return "n/a"
    return f"${v:,.0f}"


def pct(v: float) -> str:
    if isinstance(v, float) and math.isnan(v):
        return "n/a"
    return f"{100 * v:.1f}%"


def ci(stat: dict) -> str:
    return f"{money(stat['mean'])} ({money(stat['lo'])} to {money(stat['hi'])})"


def band(stat: dict) -> str:
    if stat["lo"] > 0:
        return "above zero"
    if stat["hi"] < 0:
        return "below zero"
    return "covering zero"


def five_minute_momentum(df: pd.DataFrame) -> pd.DataFrame:
    """First 5-minute candle sets direction and the stop. Flat before 15:55. No target."""
    o = df["open"].to_numpy()
    h = df["high"].to_numpy()
    low = df["low"].to_numpy()
    c = df["close"].to_numpy()
    hm = df["hm"].to_numpy()
    sess = df["sess"].to_numpy()
    ts = df["ts_event"]
    cuts = np.flatnonzero(np.diff(sess)) + 1
    bounds = np.r_[0, cuts, len(df)]
    rows = []
    opening = (9 * 60 + 30, 9 * 60 + 31, 9 * 60 + 32, 9 * 60 + 33, 9 * 60 + 34)
    for a, b in pairwise(bounds):
        hms = hm[a:b]
        idx = []
        complete = True
        for minute in opening:
            hit = np.flatnonzero(hms == minute)
            if len(hit) == 0:
                complete = False
                break
            idx.append(int(hit[0]))
        if not complete:
            continue
        w0, w1 = idx[0], idx[-1]
        direction = float(c[a + w1] - o[a + w0])
        if direction == 0:
            continue
        side = 1 if direction > 0 else -1
        window_low = float(low[a + w0 : a + w1 + 1].min())
        window_high = float(h[a + w0 : a + w1 + 1].max())
        stop = window_low if side == 1 else window_high
        entry_rel = np.flatnonzero(hms == 9 * 60 + 35)
        if len(entry_rel) == 0:
            continue
        entry_i = a + int(entry_rel[0])
        if hm[entry_i] >= FLAT_MINUTE:
            continue
        entry_raw = float(o[entry_i])
        risk = side * (entry_raw - stop)
        if risk < 2 or risk > 200:
            continue
        entry = entry_raw + side * TICK
        stop_fill = stop - side * TICK
        exit_raw = entry_raw
        exit_px = entry
        mae = 0.0
        for j in range(entry_i, b):
            if sess[j] != sess[entry_i] or hm[j] >= FLAT_MINUTE:
                src = j - 1 if j > entry_i else entry_i
                exit_raw = float(c[src])
                exit_px = exit_raw - side * TICK
                break
            if side == 1:
                mae = max(mae, entry - float(low[j]))
                if o[j] <= stop:
                    exit_raw = float(o[j])
                    exit_px = min(exit_raw, stop_fill)
                    mae = max(mae, entry - exit_px)
                    break
                if low[j] <= stop:
                    exit_raw = stop
                    exit_px = stop_fill
                    mae = max(mae, entry - exit_px)
                    break
            else:
                mae = max(mae, float(h[j]) - entry)
                if o[j] >= stop:
                    exit_raw = float(o[j])
                    exit_px = max(exit_raw, stop_fill)
                    mae = max(mae, exit_px - entry)
                    break
                if h[j] >= stop:
                    exit_raw = stop
                    exit_px = stop_fill
                    mae = max(mae, exit_px - entry)
                    break
        else:
            exit_raw = float(c[b - 1])
            exit_px = exit_raw - side * TICK
        gross = side * (exit_px - entry)
        gross_raw = side * (exit_raw - entry_raw)
        rows.append({
            "ts": ts.iloc[entry_i],
            "r": (gross - COMMISSION_POINTS) / risk,
            "gross_raw": gross_raw,
            "risk": risk,
            "mae_r": mae / risk,
        })
    return pd.DataFrame(rows)


def ifvg_first_in_window(df: pd.DataFrame) -> pd.DataFrame:
    """First 1-point three-bar gap between 09:30 and 11:00. Stop beyond the gap, 2R, one a day.

    His post gives the window, the one-trade cap, the 1-point minimum and the 2R
    target. It does not draw the candle. This is the standard three-bar gap.
    """
    o = df["open"].to_numpy()
    h = df["high"].to_numpy()
    low = df["low"].to_numpy()
    c = df["close"].to_numpy()
    hm = df["hm"].to_numpy()
    sess = df["sess"].to_numpy()
    n = len(df)
    same = np.zeros(n, dtype=bool)
    same[2:] = (sess[2:] == sess[:-2]) & (sess[2:] == sess[1:-1])
    bull = np.zeros(n, dtype=bool)
    bear = np.zeros(n, dtype=bool)
    bull[2:] = (low[2:] >= h[:-2] + 1.0) & same[2:]
    bear[2:] = (h[2:] <= low[:-2] - 1.0) & same[2:]
    in_window = (hm >= 9 * 60 + 30) & (hm < 11 * 60)
    bull &= in_window
    bear &= in_window
    keep_i: list[int] = []
    keep_side: list[int] = []
    keep_stop: list[float] = []
    keep_tgt: list[float] = []
    seen: set[int] = set()
    for i in np.flatnonzero(bull | bear):
        session = int(sess[i])
        if session in seen or i + 1 >= n or sess[i + 1] != sess[i]:
            continue
        side = 1 if bull[i] else -1
        stop = float(h[i - 2] if side == 1 else low[i - 2])
        entry = float(o[i + 1])
        risk = side * (entry - stop)
        if not (2 <= risk <= 200):
            seen.add(session)
            continue
        seen.add(session)
        keep_i.append(int(i))
        keep_side.append(side)
        keep_stop.append(stop)
        keep_tgt.append(entry + side * 2.0 * risk)
    if not keep_i:
        return pd.DataFrame(columns=["ts", "r"])
    trades = simulate(
        "ifvg",
        np.asarray(keep_i),
        np.asarray(keep_side),
        np.asarray(keep_stop, dtype=float),
        np.asarray(keep_tgt, dtype=float),
        o, h, low, c, hm, sess,
        df["ts_event"].to_numpy(),
    )
    return pd.DataFrame({
        "ts": [df["ts_event"].iloc[t.entry_i] for t in trades],
        "r": [t.r_net for t in trades],
    })


def trade_block(frame: pd.DataFrame, with_nq: bool) -> str:
    if len(frame) == 0:
        return "no trades"
    r = frame["r"].to_numpy()
    mean = float(r.mean())
    se = float(r.std(ddof=1) / np.sqrt(len(r)))
    wins = float(r[r > 0].sum())
    losses = float(-r[r <= 0].sum())
    profit_factor = wins / losses if losses else float("nan")
    text = (
        f"n={len(frame)}, win {pct(float((r > 0).mean()))}, "
        f"mean R {mean:.3f} ({mean - 1.96 * se:.3f} to {mean + 1.96 * se:.3f}), "
        f"PF {profit_factor:.2f}"
    )
    if with_nq and "gross_raw" in frame:
        nq = frame["gross_raw"].to_numpy() * 20.0 - 14.52
        mnq = r * frame["risk"].to_numpy() * 2.0
        text += (
            f", mean $ at 1 NQ after his $14.52 {money(float(nq.mean()))}, "
            f"mean $ at 1 MNQ after our costs {money(float(mnq.mean()))}"
        )
        if "mae_r" in frame:
            text += f", median MAE {frame['mae_r'].median():.2f}R"
    return text


def run_recipe(seed: int, **kw) -> dict:
    fee = float(kw.get("fee", 100.0))
    raw = lucid_recipe_run(np.random.default_rng(seed), n=N_RECIPE, **kw)
    return recipe_summary(raw, fee)


def recipe_row(name: str, seed: int, **kw) -> dict:
    mixed = (zlib.crc32(name.encode()) ^ (seed & 0xFFFFFFFF)) & 0x7FFFFFFF
    stat = run_recipe(mixed, **kw)
    print(" ", name, round(stat["mean"], 1), flush=True)
    return stat


def summarise_frame_r(frame: pd.DataFrame) -> np.ndarray:
    if len(frame) == 0:
        return np.array([0.0])
    return frame["r"].to_numpy()


def per_funded(stat: dict) -> float:
    if stat["pass_rate"] <= 0:
        return float("nan")
    return stat["mean_cash_if_passed"] - stat["fees_per_pass"]


def no_edge_lucid_rows() -> list[dict]:
    """The published gross-zero LucidFlex rows, at 40% and at 50%."""
    books = [
        ("50K baseline", 50_000, PREDECLARED),
        ("50K angus 0.25R", 50_000, ANGUS_POLICY),
        ("100K baseline", 100_000, PREDECLARED),
        ("100K angus 0.25R", 100_000, ANGUS_POLICY),
        ("150K baseline", 150_000, PREDECLARED),
        ("150K angus 0.25R", 150_000, ANGUS_POLICY),
        ("50K searched gross-zero", 50_000, Policy(400.0, 2.0, 1, None, 2.0, None, 3)),
        ("100K searched gross-zero", 100_000, Policy(1000.0, 2.0, 1, 2.0, None, None, 3)),
        ("150K searched gross-zero", 150_000, Policy(1000.0, 2.0, 1, 2.0, 2.0, None, 3)),
    ]
    rows = []
    for name, size, policy in books:
        for cons in (0.40, 0.50):
            print(f"no-edge {name} {cons:.0%}", flush=True)
            net = run_lucidflex(
                size, policy, "gross0", 0.0, 1500,
                np.random.default_rng(20261103), 100.0,
                consistency=cons,
            )
            stat = opt_summarise(net)
            rows.append({
                "name": name,
                "size": size,
                "consistency": cons,
                "policy": policy.label(),
                **stat,
            })
    return rows


def slideshow_variants() -> list[tuple[str, dict]]:
    """Assumption changes around the ±$500 Topstep coin. 2,500 paths each."""
    specs: list[tuple[str, dict]] = [
        ("published XFA, max payout, activation, no cost", {"payout": "max"}),
        ("no activation", {"payout": "max", "charge_activation": False}),
        ("trader keeps 100%, not 90%", {"payout": "max", "split": 1.0}),
        ("$125 minimum payout", {"payout": "min"}),
        ("fixed $778 request, trader keeps $700", {"payout": "min", "fixed_payout": 778.0}),
        ("3 winning days, not 5", {"payout": "max", "winning_days": 3}),
        ("no winning-day requirement", {"payout": "max", "winning_days": 0}),
        ("funded starts at $50,000, payout floor $0", {"payout": "max", "xfa": False, "payout_floor": 0.0}),
        ("funded starts at $50,000, payout floor $50,000", {"payout": "max", "xfa": False}),
        ("no trailing floor", {"payout": "max", "trail": False}),
        ("$35 MNQ cost, max payout, intraday", {"payout": "max", "cost": 35.0, "intraday": True}),
    ]
    rows = []
    for i, (name, kw) in enumerate(specs):
        print("variant", name, flush=True)
        stat = topstep_coin(np.random.default_rng(300 + i), n=2500, **kw)
        rows.append((name, stat))
    return rows


def main() -> None:
    coins: list[tuple[str, dict]] = []

    def add_topstep(name: str, seed: int, **kw) -> None:
        print("coin", name, flush=True)
        coins.append((name, topstep_coin(np.random.default_rng(seed), n=N_COIN, **kw)))

    def add_lucid(name: str, seed: int, **kw) -> None:
        print("coin", name, flush=True)
        coins.append((name, lucid_coin(np.random.default_rng(seed), n=N_COIN, **kw)))

    add_topstep("Topstep ±$500, no cost, max payout, activation, end of day", 1, payout="max")
    add_topstep("Topstep ±$500, no cost, $125 payout, activation, end of day", 2, payout="min")
    add_topstep(
        "Topstep ±$500, no cost, $125 payout, no activation, end of day",
        3, payout="min", charge_activation=False,
    )
    add_topstep(
        "Topstep ±$500, no cost, $125 payout, activation, intraday",
        4, payout="min", intraday=True,
    )
    add_topstep(
        "Topstep ±$500, $14.52 cost, $125 payout, activation, intraday",
        5, payout="min", intraday=True, cost=14.52,
    )
    add_topstep(
        "Topstep ±$500, $35 cost, $125 payout, activation, intraday",
        6, payout="min", intraday=True, cost=35.0,
    )
    add_topstep(
        "Topstep ±$500, $35 cost, max payout, activation, intraday",
        7, payout="max", intraday=True, cost=35.0,
    )
    add_topstep(
        "Topstep 54% win, no cost, $125 payout, activation, end of day",
        8, payout="min", p=0.54,
    )
    add_topstep(
        "Topstep 60% win, no cost, $125 payout, activation, end of day",
        9, payout="min", p=0.60,
    )
    for fee in (50.0, 100.0, 150.0, 200.0):
        add_lucid(
            f"LucidFlex ±$500, no cost, max payout, end of day, fee ${fee:.0f}",
            100 + int(fee), fee=fee, payout="max",
        )
    add_lucid(
        "LucidFlex ±$500, no cost, $500 payout, end of day, fee $100",
        11, fee=100, payout="min",
    )
    add_lucid(
        "LucidFlex ±$500, no cost, max payout, intraday, fee $100",
        12, fee=100, payout="max", intraday=True,
    )
    add_lucid(
        "LucidFlex ±$500, $14.52 cost, max payout, end of day, fee $100",
        13, fee=100, payout="max", cost=14.52,
    )
    add_lucid(
        "LucidFlex ±$500, $35 cost, max payout, end of day, fee $100",
        14, fee=100, payout="max", cost=35.0,
    )

    print("recipes", flush=True)
    recipes: list[tuple[str, dict]] = []

    def add_recipe(name: str, seed: int, **kw) -> None:
        recipes.append((name, recipe_row(name, seed, **kw)))

    for size, label in ((25_000, "25K"), (50_000, "50K"), (100_000, "100K")):
        for cons, cname in ((0.40, "40%"), (0.50, "50% add-on")):
            for intra, grade in ((False, "end of day"), (True, "intraday")):
                fees = (50.0, 80.0, 100.0, 150.0, 200.0) if size == 50_000 else (100.0,)
                for fee in fees:
                    if size == 50_000 and intra and fee not in (50.0, 100.0, 150.0):
                        continue
                    add_recipe(
                        f"{label} {cname} {grade} fee ${fee:.0f}",
                        size + int(cons * 1000) + int(intra) * 17 + int(fee),
                        size=size, consistency=cons, intraday=intra, fee=fee,
                    )
    add_recipe(
        "50K 50% add-on end of day fee $100, a missed $150 day fails the account",
        21, consistency=0.50, small_fail="bust", fee=100,
    )
    add_recipe(
        "50K 50% add-on end of day fee $100, same payoffs at 50/50",
        22, consistency=0.50, p_eval=0.5, p_big=0.5, p_small=0.5, fee=100,
    )
    add_recipe(
        "50K 50% add-on intraday fee $100, same payoffs at 50/50",
        23, consistency=0.50, p_eval=0.5, p_big=0.5, p_small=0.5, intraday=True, fee=100,
    )
    add_recipe(
        "50K 40% end of day fee $100, same payoffs at 50/50",
        24, consistency=0.40, p_eval=0.5, p_big=0.5, p_small=0.5, fee=100,
    )

    print("bars", flush=True)
    df = load_bars(str(ROOT / "data" / "reference" / "nq_1m_master.parquet"))
    opening = five_minute_momentum(df)
    gap = ifvg_first_in_window(df)
    opening_hold = opening[opening["ts"] >= HOLDOUT]
    opening_train = opening[opening["ts"] < HOLDOUT]
    gap_hold = gap[gap["ts"] >= HOLDOUT]
    gap_train = gap[gap["ts"] < HOLDOUT]
    print("opening", trade_block(opening_hold, True), flush=True)
    print("ifvg", trade_block(gap_hold, False), flush=True)

    or_r = summarise_frame_r(opening_hold)
    gap_r = summarise_frame_r(gap_hold)
    print("signal farms", flush=True)
    signal_farms = [
        ("50K 50% add-on end of day fee $100, holdout 5-minute R sized to the risk",
         run_recipe(31, consistency=0.50, fee=100, samples=or_r)),
        ("50K 50% add-on intraday fee $100, holdout 5-minute R sized to the risk",
         run_recipe(32, consistency=0.50, fee=100, intraday=True, samples=or_r)),
        ("50K 50% add-on end of day fee $100, holdout three-bar gap R sized to the risk",
         run_recipe(33, consistency=0.50, fee=100, samples=gap_r)),
    ]
    for name, stat in signal_farms:
        print(" ", name, round(stat["mean"], 1), flush=True)
        recipes.append((name, stat))

    print("no-edge lucid", flush=True)
    edge_rows = no_edge_lucid_rows()
    print("slideshow variants", flush=True)
    variants = slideshow_variants()

    print("batches", flush=True)
    batches = []
    for fee in (50.0, 80.0, 100.0, 150.0, 200.0):
        for cons, label in ((0.50, "50% add-on"), (0.40, "40%")):
            for intra, grade in ((False, "end of day"), (True, "intraday")):
                if intra and fee not in (50.0, 100.0):
                    continue
                batch = household_batch(
                    np.random.default_rng(4000 + int(fee) + int(cons * 100) + int(intra)),
                    n=N_BATCH, fee=fee, bankroll=2_000, days=21,
                    consistency=cons, intraday=intra,
                )
                cash = batch.month_cash
                se = float(cash.std(ddof=1) / np.sqrt(len(cash)))
                row = {
                    "fee": fee,
                    "rule": label,
                    "grade": grade,
                    "cash": float(cash.mean()),
                    "lo": float(cash.mean() - 1.96 * se),
                    "hi": float(cash.mean() + 1.96 * se),
                    "p10": float(np.percentile(cash, 10)),
                    "p90": float(np.percentile(cash, 90)),
                    "p_neg": float(batch.ruin),
                    "p_broke": float(batch.p_broke),
                    "p_paid": float(batch.payout_rate),
                    "mean_pays": float(batch.mean_payouts),
                }
                batches.append(row)
                print(" ", row["fee"], row["rule"], row["grade"], round(row["cash"], 1), flush=True)

    text = render(
        coins, recipes, batches, opening_train, opening_hold, gap_train, gap_hold,
        edge_rows, variants,
    )
    current = DOC.read_text()
    if MARKER in current:
        current = current.split(MARKER)[0].rstrip() + "\n"
    DOC.write_text(current.rstrip() + "\n" + text)
    print("wrote", DOC, flush=True)


def wording_and_reproduction(coins, edge_rows, variants) -> list[str]:
    lines: list[str] = []
    a = lines.append
    a("### The live wording, next to Angus")
    a("")
    a("Angus trades these accounts. On 3 Nov 2026 he said LucidFlex evals use a 50% consistency rule, that 40% may be the Pro rule or an older one, and that a funded LucidFlex account has no consistency rule, so a trader can take a large day first and then farm days of +$150. The help pages were fetched again the same day. The funded half of that matches the pages. The eval half does not. Pro is not the 40% rule either. The Pro evaluation page, <https://support.lucidtrading.com/en/articles/12890029-lucidpro-evaluation-account>, has no consistency column and says \"Pass the evaluation in one trading day.\"")
    a("")
    a("| question | Angus | live page |")
    a("|---|---|---|")
    a("| Eval consistency | 50% is the Flex rule. 40% may be Pro or older. | Evaluation account, <https://support.lucidtrading.com/en/articles/12945790-lucidflex-evaluation-account>: the 50K row is \"40% (50% with add-on)\" and the page says \"Pass in as few as 3 days with 40% consistency, or 2 days with the 50% consistency add-on.\" Consistency page, <https://support.lucidtrading.com/en/articles/12945805-lucidflex-consistency-percentage>: \"In LucidFlex evaluation accounts your Consistency Percentage must be 40% or less to be eligible to upgrade to a LucidFlex funded account. If you added the 50% consistency add-on at checkout, it must be 50% or less.\" Customization, <https://support.lucidtrading.com/en/articles/16226050-lucidflex-customization>: \"40% (standard): your largest day must be 40% or less of your evaluation profit. Lowest price. 50% (add-on): your largest day can be up to 50%, so you can pass in as few as 2 days. Added at checkout for a small fee.\" |")
    a("| Funded / payout consistency | No consistency rule. A big day one, then +$150 days, is allowed. | Funded account, <https://support.lucidtrading.com/en/articles/12945795-lucidflex-funded-account>: \"LucidFlex funded accounts have an optional Daily Loss Limit, no consistency rule and no payout buffer.\" And: \"There is no Consistency Percentage on LucidFlex funded accounts.\" Payouts, <https://support.lucidtrading.com/en/articles/12945796-lucidflex-payouts>, page date 28 Jul 2026: \"There are two requirements must be met in LucidFlex to qualify for a payout.\" The two are five days at the minimum daily profit ($150 on a 50K) and positive net profit in the cycle. The page does not add a consistency percentage. The 50K cap is \"50% of Profit up to $2,000.\" |")
    a("")
    a("The formula on the consistency page is \"Largest Single Day Profit / Account Profit = Consistency Percentage.\" The same page says the requirement \"applies only during the evaluation stage.\" The 50% add-on has an example cushion, not a formula: on a 50K the table shows $1,500 at 50% and a cushion of $1,560, and the 25K, 100K and 150K rows are the same 4% step. The page says the table is an example, \"not a fixed dollar amount,\" and that the cushion is a percentage of the actual day. Two days of exactly $1,500 are already 50%, so they pass the add-on without that cushion. The simulator keeps that plain ratio. Both the 40% standard and the 50% add-on are in the recipe tables below. The standard is not changed to 50%.")
    a("")
    a("### The earlier no-edge LucidFlex rows, at both percentages")
    a("")
    a("These are the gross-zero books from the prop-structure search, rerun at 1,500 paths. Each pair uses one seed, so the only change is the eval percentage. The fee is the assumed $100. This is a fresh seed, not a revision of the earlier point estimates. On this seed the two columns match on every row: no path was passed by 50% and failed by 40%. A best day large enough to sit between those two lines did not decide a pass here. The pre-declared $200 stake was never going to. The 2R, $1,000 rows could have, and did not.")
    a("")
    a("| book | rule | EV | 95% CI |")
    a("|---|---|---:|---|")
    for row in edge_rows:
        a(
            f"| {row['name']} | {row['consistency']:.0%} | {money(row['ev'])} | "
            f"{money(row['lo'])} to {money(row['hi'])} |"
        )
    a("")
    base = find(coins, "Topstep ±$500, no cost, max payout, activation, end of day")
    funded_net = per_funded(base)
    a("### Reproducing +$250 to +$300 per attempt")
    a("")
    a("His slideshow, not the farm recipe: one ±$500 trade a day, 50/50, no commission in the payoff, Topstep 50K. He reports a pass rate of about 25–28%, about $220 to get funded at $49 a month, 97% of funded accounts dead within a year, 60% of funded accounts paid before they die because Topstep pays from $125, an average payout of about $700, a median of $225, and a net of about +$300 per attempt. Apex at 80% off is the +$250. Apex is not in the rule file, so that half is not run.")
    a("")
    a(
        f"The no-cost coin that takes the maximum payout, charges the $49 month and the $149 activation, and grades the floor from the close is the row that meets the descriptive statistics. "
        f"Pass {pct(base['pass_rate'])}. Of funded accounts, {pct(base['payout_given_pass'])} are paid and {pct(base['dead_given_pass'])} are dead by day 252. "
        f"Median cash among funded accounts {money(base['median_cash_if_passed'])}. Mean cash among funded accounts {money(base['mean_cash_if_passed'])}. "
        f"Mean payouts among funded accounts {base['mean_payouts_if_passed']:.2f}. "
        f"Fees per passed account {money(base['fees_per_pass'])}, of which the activation is $149, so the subscription piece is {money(base['fees_per_pass'] - 149)}. "
        f"EV per eval purchase {ci(base)}. "
        f"The same paths, stated per funded account, are mean funded cash minus every eval fee spent to produce that account: {money(funded_net)}. "
        f"Those two are the same object. Per-purchase EV equals the pass rate times the per-funded net."
    )
    a("")
    a("The table changes one assumption at a time, 2,500 paths, still a ±$500 coin with no commission unless the row says otherwise. \"Per funded\" is funded cash minus fees per passed account.")
    a("")
    a("| assumption | pass | funded, paid | median cash if funded | mean cash if funded | fees per pass | EV per purchase | per funded |")
    a("|---|---:|---:|---:|---:|---:|---|---|")
    hit_purchase = []
    for name, stat in variants:
        net_f = per_funded(stat)
        a(
            f"| {name} | {pct(stat['pass_rate'])} | {pct(stat['payout_given_pass'])} | "
            f"{money(stat['median_cash_if_passed'])} | {money(stat['mean_cash_if_passed'])} | "
            f"{money(stat['fees_per_pass'])} | {ci(stat)} | {money(net_f)} |"
        )
        if stat["lo"] <= 300 <= stat["hi"] or 250 <= stat["mean"] <= 320:
            hit_purchase.append((name, stat))
    a("")
    if hit_purchase:
        names = "; ".join(
            f"{name} at {ci(stat)}, median {money(stat['median_cash_if_passed'])}, pass {pct(stat['pass_rate'])}"
            for name, stat in hit_purchase
        )
        a(f"Per-purchase EV falls near +$250 to +$320 in: {names}. That row does not also have his $225 median.")
    else:
        a("No single assumption change above puts the per-purchase EV in a band around +$250 to +$320.")
    a("")
    lo_funded = base["lo"] / base["pass_rate"]
    hi_funded = base["hi"] / base["pass_rate"]
    no_act = find(variants, "no activation")
    a(
        f"His descriptive statistics line up with the no-activation row, not with a +$300 purchase. "
        f"That row, 2,500 paths: pass {pct(no_act['pass_rate'])}, {pct(no_act['payout_given_pass'])} of funded accounts paid, "
        f"median {money(no_act['median_cash_if_passed'])}, mean funded cash {money(no_act['mean_cash_if_passed'])}, "
        f"fees per pass {money(no_act['fees_per_pass'])}. "
        f"Those are his 25–28%, about 60%, $225, about $700, and about $220. "
        f"Its per-purchase EV is {ci(no_act)}. Its per-funded net is {money(per_funded(no_act))}."
    )
    a("")
    a(
        f"The 4,000-path row that also charges the $149 activation has per-purchase EV {ci(base)} and a per-funded point of {money(funded_net)}. "
        f"Dividing that purchase interval by the pass rate spreads the per-funded net from {money(lo_funded)} to {money(hi_funded)}. "
        f"His +$300 sits inside that spread and outside the purchase interval. "
        f"A second sample of the same activation-on rule, the first variant row, put the per-funded net at {money(per_funded(find(variants, 'published XFA, max payout, activation, no cost')))}. "
        f"So +$300 is a number the per-funded arithmetic can print. It is not a number the per-purchase interval contains, and it is not stable to a fresh sample. "
        f"The subscription piece of the activation-on row is {money(base['fees_per_pass'] - 149)}, which is the ~$220, and the $375 fees-per-pass is what you get once the $149 is included. "
        f"The $225 median is 90% of a $250 request under the maximum-payout rule. The $125 minimum raises how many funded accounts get paid. It does not produce the median dollar. "
        f"Mean funded cash of {money(base['mean_cash_if_passed'])} is the \"average payout about $700.\""
    )
    a("")
    a("Assumption differences, from his slideshow to the model that produced the earlier −$100:")
    a("")
    a("- His trade is +$500 or −$500, one a day, and the trade itself is worth zero. The earlier baseline risked $200 twice a day, then paid $1.22 and one tick each side, so the trade was already negative. That is why one number was about −$100 and the other is positive before costs are put back.")
    a("- His pass rate, about 25–28%, is the trailing floor. A static $2,000 floor on a fair ±$500 coin passes near 40%. The \"no trailing floor\" row is that object. It does not have his pass rate.")
    a("- The $220 figure is months of the $49 subscription allocated to each pass. The published path also charges $149 after a pass. Dropping the activation raises the per-purchase EV by about that $149 times the pass rate. It does not add $200.")
    a("- Putting the $35 MNQ cost back on, and grading the breach intraday, is the last row of the variant table. That is the slideshow coin under the cost model used everywhere else in this file.")
    a("- A funded account that starts at $50,000 instead of the XFA's $0, a payout that does not keep 10%, and a request sized so the trader keeps $700 are the other rows. Compare each one's pass rate and median with the 25–28% and $225 before calling it his slideshow.")
    a("- 54% and 60% win rates, in the coin table above, are not +$1,400 and +$3,300. The gap between those rows and the 50/50 row is the win rate.")
    a("- LucidFlex funded having no consistency rule was already how the recipe was run. The live page confirms it. The 40% versus 50% rows are the eval rule, and only the eval rule.")
    a("")
    return lines


def find(rows: list[tuple[str, dict]], needle: str) -> dict:
    for name, stat in rows:
        if name == needle:
            return stat
    raise KeyError(needle)


def render(coins, recipes, batches, opening_train, opening_hold, gap_train, gap_hold, edge_rows, variants) -> str:
    lines: list[str] = ["", "## The prop-farm claim", ""]
    a = lines.append
    a("These are the claims from @lndhmtapes (Kairos), tested on the rules in `config/prop_rules.yaml`. Nothing here places an order. Cross-account hedging is not tested. Lucid bans it, and so does the note he wrote himself.")
    a("")
    lines.extend(wording_and_reproduction(coins, edge_rows, variants))
    a("")
    a("### The ±$500 coin, against the earlier −$100")
    a("")
    a("His slideshow coin is one trade a day that closes at **+$500 or −$500**. The trade's own expectancy is zero. There is no commission in that payoff. He reports about **+$300 per Topstep attempt** and about +$250 on an Apex account at 80% off. Apex is not simulated. He also says a pass is about 25–28%, that about 60% of Topstep funded accounts get a payout before they die because the minimum request is $125, that the median Topstep payout is $225 and the average about $700, that 97% of funded accounts are dead within a year, and that the cost of getting funded is about $220 at $49 a month.")
    a("")
    a("The earlier gross-zero result in the prop-structure search is a different bet. The pre-declared baseline risked **$200 twice a day**. Each trade was a random walk aimed at a target, then charged the published MNQ commission of $1.22 and one tick of slippage each side, so the trade was already negative before the firm took a fee. That row was **−$105** on Topstep 50K (−$112 to −$98) and **−$86** on LucidFlex 50K (−$91 to −$81) at an assumed $100 Lucid fee. The Lucid number sat on the fee because a $200 stake rarely reached a $3,000 target inside the horizon. CRT resampled into the same small stake did the same thing and printed the fee.")
    a("")
    a("The table is his coin, one attempt, 4,000 paths, up to 252 trading days. The interval is a 95% interval on the mean. `No activation` drops the $149 Topstep charges after a pass. `$125 payout` requests the minimum whenever half the balance covers it. `Max payout` requests half the balance, capped at $2,000. Intraday mode busts the account when the planned loss is larger than the room under the current floor, which is how Topstep monitors the line. LucidFlex's own check is the close, so its intraday row is a re-grade. The Lucid fee is one-time and the dollar amount is not on the help page.")
    a("")
    a("| setup | pass | ever paid | of funded, paid | of funded, dead in a year | median cash if funded | fees | fees per pass | EV per attempt |")
    a("|---|---:|---:|---:|---:|---:|---:|---:|---|")
    for name, stat in coins:
        a(
            f"| {name} | {pct(stat['pass_rate'])} | {pct(stat['payout_rate'])} | "
            f"{pct(stat['payout_given_pass'])} | {pct(stat['dead_given_pass'])} | "
            f"{money(stat['median_cash_if_passed'])} | {money(stat['mean_fees'])} | "
            f"{money(stat['fees_per_pass'])} | {ci(stat)} |"
        )
    a("")
    no_act = find(coins, "Topstep ±$500, no cost, $125 payout, no activation, end of day")
    real_ts = find(coins, "Topstep ±$500, no cost, $125 payout, activation, intraday")
    cost_ts = find(coins, "Topstep ±$500, $35 cost, $125 payout, activation, intraday")
    nq_ts = find(coins, "Topstep ±$500, $14.52 cost, $125 payout, activation, intraday")
    max_ts = find(coins, "Topstep ±$500, no cost, max payout, activation, end of day")
    wr54 = find(coins, "Topstep 54% win, no cost, $125 payout, activation, end of day")
    wr60 = find(coins, "Topstep 60% win, no cost, $125 payout, activation, end of day")
    lx100 = find(coins, "LucidFlex ±$500, no cost, max payout, end of day, fee $100")
    lx50 = find(coins, "LucidFlex ±$500, no cost, max payout, end of day, fee $50")
    lx200 = find(coins, "LucidFlex ±$500, no cost, max payout, end of day, fee $200")
    lx_cost = find(coins, "LucidFlex ±$500, $35 cost, max payout, end of day, fee $100")
    lx_intra = find(coins, "LucidFlex ±$500, no cost, max payout, intraday, fee $100")
    a(
        f"The row that matches his accounting most closely is the no-activation, $125-payout, no-cost Topstep coin: "
        f"EV {ci(no_act)}, pass {pct(no_act['pass_rate'])}, "
        f"{pct(no_act['payout_given_pass'])} of funded accounts get paid, "
        f"median cash among funded accounts {money(no_act['median_cash_if_passed'])}, "
        f"mean cash among funded accounts {money(no_act['mean_cash_if_passed'])}, "
        f"{pct(no_act['dead_given_pass'])} of funded accounts dead by day 252, "
        f"fees per passed account {money(no_act['fees_per_pass'])}. "
        f"His +$300, 25–28% pass, 60% of funded paid, $225 median, $700 average, 97% dead, and ~$220 to get funded sit next to those six numbers. "
        f"Where a figure matches, it is this row and not the row with the activation."
    )
    a("")
    a(
        f"Charging the $149 activation and grading the breach intraday, still with no commission, is {ci(real_ts)}, {band(real_ts)}. "
        f"Adding $14.52, his one-NQ round turn, is {ci(nq_ts)}. "
        f"Adding $35, which is what $500 of risk costs in MNQ at a 16-point stop under the commission used everywhere else in this file, is {ci(cost_ts)}. "
        f"Taking the maximum payout instead of $125, with no commission and the activation, is {ci(max_ts)}. "
        f"A $500 day is 17% of the $3,000 target, so Topstep's 55% consistency rule does not raise the target. "
        f"Intraday and end-of-day grading agree while the stop fits under the floor. They split once the room is under $500."
    )
    a("")
    a(
        f"His 54% and 60% win-rate claims, on the same $125 Topstep book with the activation and no commission, are {ci(wr54)} and {ci(wr60)}. "
        f"He quotes +$1,400 and +$3,300. The gap between those and the 50/50 row is the win rate, not the fee."
    )
    a("")
    a(
        f"On LucidFlex 50K the same no-cost coin, end of day, maximum payout, is {ci(lx50)} at a $50 fee, {ci(lx100)} at $100, and {ci(lx200)} at $200. "
        f"With the $35 MNQ cost and a $100 fee it is {ci(lx_cost)}. The intraday re-grade at $100 and no cost is {ci(lx_intra)}. "
        f"Lucid's minimum request is $500, not $125, and the payout is half of cycle profit rather than half of a balance that started at zero. "
        f"There is no activation fee. A $500 day does not trip the 40% eval consistency rule. "
        f"The earlier −$100 was not this coin failing. It was a smaller, already-costed bet that never got to a payout."
    )
    a("")
    a("### His LucidFlex recipe")
    a("")
    a("The recipe, as he describes it: an eval day is +$1,500 with probability 60% or a −$2,000 bust. Two of those wins reach the $3,000 target. A funded day is then +$3,400 or −$2,000 with probability 39%, then days of +$150 with probability 95%. The big day counts as one of the five winning days. Profit of $4,000 pays half, capped at $2,000, and the trader keeps 90%, which is $1,800. He stops at 4 payouts. The rule is 5, and this sim allows 5. Those probabilities are his claims about a signal. They are not measurements from this repo. A 60% chance to make $1,500 while risking $2,000 is +$100 on the day before any fee.")
    a("")
    a("Two +$1,500 days make the best day 50% of the profit. The default eval rule is 40%, so those two days do not pass. A third +$1,500 day makes the best day 33% and passes. The 50% add-on passes on day two. Its price is not on the help page, and it is not added on top of the fee. The cushion he mentions, about $1,560, is an example on the page and not a formula. This sim uses a plain ratio and no cushion. A missed +$150 day loses $150 and is retried, which is what the rulebook allows, except the one row where a miss fails the account. That fail rule is what his 81% joint probability assumes.")
    a("")
    a("The household cannot run 100 evals at once. The notes cite Lucid's general FAQ for 10 evals, 5 funded, and 10 combined. The batch section buys a new eval only when the cash covers the fee and a slot is free. 3,000 paths for the per-eval table. The interval is on the mean.")
    a("")
    a("| book | pass | payout rate per eval | payouts per 100 evals | EV per eval |")
    a("|---|---:|---:|---:|---|")
    for name, stat in recipes:
        if "holdout" in name:
            continue
        a(
            f"| {name} | {pct(stat['pass_rate'])} | {pct(stat['payout_rate'])} | "
            f"{stat['payouts_per_100_evals']:.1f} | {ci(stat)} |"
        )
    a("")
    his = find(recipes, "50K 50% add-on end of day fee $100")
    his40 = find(recipes, "50K 40% end of day fee $100")
    his_in = find(recipes, "50K 50% add-on intraday fee $100")
    coin50 = find(recipes, "50K 50% add-on end of day fee $100, same payoffs at 50/50")
    coin_in = find(recipes, "50K 50% add-on intraday fee $100, same payoffs at 50/50")
    bust_small = find(recipes, "50K 50% add-on end of day fee $100, a missed $150 day fails the account")
    k25 = find(recipes, "25K 50% add-on end of day fee $100")
    k100 = find(recipes, "100K 50% add-on end of day fee $100")
    k25_in = find(recipes, "25K 50% add-on intraday fee $100")
    k100_in = find(recipes, "100K 50% add-on intraday fee $100")
    fee_rows = [
        (fee, find(recipes, f"50K 50% add-on end of day fee ${fee:.0f}"))
        for fee in (50.0, 80.0, 100.0, 150.0, 200.0)
    ]
    a(
        f"At his hit rates, the 50K with the 50% add-on, end-of-day grading and a $100 fee is pass {pct(his['pass_rate'])}, "
        f"payout rate {pct(his['payout_rate'])}, {his['payouts_per_100_evals']:.1f} payouts per 100 evals, EV {ci(his)}. "
        f"He quotes a 36% pass, an 11% chance an eval ever pays, about 22 payouts per 100 evals, and about +$290 per eval ($29k on $10k of fees). "
        f"The same book at the default 40% rule is pass {pct(his40['pass_rate'])}, EV {ci(his40)}. "
        f"Replacing his hit rates with a 50/50 coin on the same dollar payoffs is {ci(coin50)}, {band(coin50)}. "
        f"Forcing a missed $150 day to fail the account, which is his 95% assumption rather than the rulebook, is {ci(bust_small)}."
    )
    a("")
    a(
        f"Intraday grading is the open-loss check. On the 50K the first funded trade risks the full $2,000, which still fits. "
        f"A $2,000 withdrawal then locks the floor at $50,100 and leaves about $1,900. The next trade still risks $2,000. "
        f"End of day can close that trade green. Intraday liquidates it on the way down, so the winner is never banked. "
        f"At his hit rates that re-grade is {ci(his_in)} against {ci(his)} at the close. "
        f"The 50/50 version graded intraday is {ci(coin_in)}. "
        f"His martingale post is the same point, with a pass rate of 64–67% at the close and 15–19% on the open loss. "
        f"That book is not re-run. He already measured it as a net loser, and it has no stop to grade except the firm's line."
    )
    a("")
    a("### A household for one month")
    a("")
    a("One household, a $2,000 starting bankroll, 21 trading days, his hit rates, the 50K recipe, 600 households. A passed eval does not trade again the same day. New evals are bought only when a slot is free and the cash covers the fee. The 10th and 90th percentiles are one household's month, not the uncertainty on the mean. P(month negative) is the chance fees exceed payouts. P(can't buy another) is the chance less than one fee is left. A third-party card says Lucid treats a breach-and-rebuy batch as gambling. That sentence was not on the Lucid pages read for the rule file, so it is not in the sim, and it is the rule risk around the table.")
    a("")
    a("| fee | consistency | grading | mean month | 95% CI of the mean | 10th to 90th | P(month negative) | P(can't buy another) | P(a payout) | mean payouts |")
    a("|---:|---|---|---:|---|---|---:|---:|---:|---:|")
    for row in batches:
        a(
            f"| {money(row['fee'])} | {row['rule']} | {row['grade']} | {money(row['cash'])} | "
            f"{money(row['lo'])} to {money(row['hi'])} | {money(row['p10'])} to {money(row['p90'])} | "
            f"{pct(row['p_neg'])} | {pct(row['p_broke'])} | {pct(row['p_paid'])} | {row['mean_pays']:.2f} |"
        )
    a("")
    a("### Account size, at the same fee")
    a("")
    a(
        "The recipe scales with the max-loss line. The eval win is half the profit target, the loss is the full max loss, and the big win is 1.7 times that max loss. The small day is the account's own minimum winning day, $100, $150 or $200. The fee in this comparison is a flat $100, which is his 50K assumption, not a published card. A real fee that scales with size would move the ranking."
    )
    a("")
    a(
        f"End of day, 50% add-on, fee $100: 25K {ci(k25)}, 50K {ci(his)}, 100K {ci(k100)}. "
        f"The same three graded on the open loss: 25K {ci(k25_in)}, 50K {ci(his_in)}, 100K {ci(k100_in)}. "
        f"He says the 50K wins at every farm size. The two rows are the test, at a fee that does not grow with the account. "
        f"A 25K request must be at least $500 and the cap is $1,000 before the split. A 100K cap is $2,500."
    )
    a("")
    a("Across the 50K end-of-day 50% add-on, the fee sensitivity is:")
    a("")
    for fee, stat in fee_rows:
        a(f"- Fee ${fee:.0f}: {ci(stat)}, {band(stat)}.")
    a("")
    a("### Does a signal add anything inside that policy?")
    a("")
    a("The 5-minute rule is his, and it was not fitted here. The 09:30–09:35 ET candle sets the direction and the stop, the entry is the 09:35 open, there is no target, and the trade is flat before 15:55. A session with a missing minute in that candle is skipped. The R column is one MNQ after $1.22 and one tick each side. The NQ dollar column uses the unslipped points and then subtracts his $14.52 once, so the tick is not charged twice. Holdout is July 2025 through July 2026. The earlier window is shown so the holdout is not the only number. It was not used to keep the rule.")
    a("")
    a(f"- 5-minute, before July 2025: {trade_block(opening_train, True)}")
    a(f"- 5-minute, holdout: {trade_block(opening_hold, True)}")
    a("")
    a("The three-bar gap is the reading of his IFVG post that can be coded without inventing a second rule: the first gap of at least one point between 09:30 and 11:00, one trade a day, stop beyond the gap, target 2R. He reported that family as a loser. CRT at 15 minutes and 0.25R is already in the table above: holdout mean R −0.081, win 77.2%, n=2175. His own 4-hour CRT post found profit factor 0.84.")
    a("")
    a(f"- Three-bar gap, before July 2025: {trade_block(gap_train, False)}")
    a(f"- Three-bar gap, holdout: {trade_block(gap_hold, False)}")
    a("")
    a("Inside the 50K farm each step still risks that step's dollars, and the day's result is a draw from the holdout R. That is the signal sized to the farm, not one NQ. The coin next to it is his dollar payoffs at 50%, not at 60/39/95. Both pay a $100 fee and use the 50% add-on.")
    a("")
    or_eod = find(recipes, "50K 50% add-on end of day fee $100, holdout 5-minute R sized to the risk")
    or_in = find(recipes, "50K 50% add-on intraday fee $100, holdout 5-minute R sized to the risk")
    gap_eod = find(recipes, "50K 50% add-on end of day fee $100, holdout three-bar gap R sized to the risk")
    a(f"- His hit rates, from the recipe table: {ci(his)}.")
    a(f"- Same payoffs, 50% coin, end of day: {ci(coin50)}.")
    a(f"- Holdout 5-minute R, sized to the same risks, end of day: pass {pct(or_eod['pass_rate'])}, payout rate {pct(or_eod['payout_rate'])}, EV {ci(or_eod)}.")
    a(f"- The same 5-minute book, graded intraday: {ci(or_in)}.")
    a(f"- Holdout three-bar gap, sized the same way, end of day: pass {pct(gap_eod['pass_rate'])}, payout rate {pct(gap_eod['payout_rate'])}, EV {ci(gap_eod)}.")
    a("")
    or_win = float((opening_hold["r"] > 0).mean()) if len(opening_hold) else float("nan")
    a(
        f"The holdout 5-minute win rate is {pct(or_win)}. "
        f"That is the rate that has to become a 60% eval day and a 95% day of +$150 if this rule is the farm's signal. "
        f"Sizing the holdout R up to the farm's dollar risk is the EV row above, set next to the 50/50 coin and next to his 60/39/95 book. "
        f"The difference from the coin is what the rule adds. The difference from his book is what the rule does not."
    )
    a("")
    a("Not tested, because the post does not give a rule that can be run once: the first-hour session bias, and the Kairos Max overnight entry. Absorption at the day's high or low was not retested. It needs the MBP-10 tape, and the minute book in this repo is the end-of-minute snapshot.")
    a("")
    a("### Verdict")
    a("")
    a(verdict(
        no_act, real_ts, cost_ts, lx100, lx_cost, his, his40, his_in, coin50,
        or_eod, batches, fee_rows,
    ))
    a("")
    return "\n".join(lines) + "\n"


def verdict(no_act, real_ts, cost_ts, lx100, lx_cost, his, his40, his_in, coin50, or_eod, batches, fee_rows) -> str:
    parts = []
    parts.append(
        f"The no-cost Topstep coin, taking $125 and skipping the activation, is {ci(no_act)}, {band(no_act)}. "
        f"That is the version of his claim this simulator can reproduce, and it is the version that leaves out the $149. "
        f"With the activation and an intraday breach it is {ci(real_ts)}, {band(real_ts)}. "
        f"With the $35 MNQ cost as well it is {ci(cost_ts)}, {band(cost_ts)}. "
        f"The earlier −$100 was the $200 costed baseline, not this coin priced with no commission."
    )
    parts.append(
        f"On LucidFlex the ±$500 coin at a $100 fee is {ci(lx100)}, {band(lx100)}, and {ci(lx_cost)}, {band(lx_cost)}, once the $35 cost is on. "
        f"The fee is unconfirmed. The sign follows the fee row above."
    )
    parts.append(
        f"His recipe is not that coin. At the 60/39/95 hit rates, a 50K, the 50% add-on, end-of-day grading and a $100 fee, EV is {ci(his)}, {band(his)}. "
        f"The default 40% rule, same fee, is {ci(his40)}, {band(his40)}. "
        f"The open-loss re-grade of the 50% book is {ci(his_in)}, {band(his_in)}. "
        f"The same payoffs at 50/50 are {ci(coin50)}, {band(coin50)}. "
        f"Set that row next to the hit-rate row before treating the payout cap as the source of the profit."
    )
    by_fee = ", ".join(
        f"${fee:.0f} {band(stat)} ({money(stat['mean'])})" for fee, stat in fee_rows
    )
    eod_100 = next(r for r in batches if r["fee"] == 100 and r["rule"] == "50% add-on" and r["grade"] == "end of day")
    eod_200 = next(r for r in batches if r["fee"] == 200 and r["rule"] == "50% add-on" and r["grade"] == "end of day")
    parts.append(
        f"Per eval, the 50% end-of-day 50K book is {by_fee}. "
        f"A household with his hit rates, a $2,000 bankroll and a $100 fee has a {pct(eod_100['p_neg'])} chance the month's cash is negative "
        f"and a {pct(eod_100['p_broke'])} chance it cannot buy another eval. "
        f"At $200 those figures are {pct(eod_200['p_neg'])} and {pct(eod_200['p_broke'])}. "
        f"The 10th percentile of a single month is {money(eod_100['p10'])} at $100 and {money(eod_200['p10'])} at $200. "
        f"That is the risk of ruin for the month. It is not a lifetime bust probability."
    )
    if cost_ts["hi"] < 0:
        topstep_skill = "With the activation and the MNQ cost, the no-skill Topstep coin sits below zero."
    elif cost_ts["lo"] > 0:
        topstep_skill = "With the activation and the MNQ cost, the no-skill Topstep coin sits above zero."
    else:
        topstep_skill = "With the activation and the MNQ cost, the no-skill Topstep coin has an interval that covers zero."
    parts.append(
        f"The 5-minute holdout, sized to the farm, is {ci(or_eod)}, {band(or_eod)}. "
        f"{topstep_skill} "
        f"On Lucid the recipe is a bet that the 60/39/95 rates are real, that the account is graded at the close, that the 50% add-on is the rule in force, and that the fee is on the side of the table whose interval is above zero. "
        f"Those are claims about a signal and a price, not a property of the payout cap."
    )
    return " ".join(parts)


if __name__ == "__main__":
    main()
