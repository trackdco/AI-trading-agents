"""Footprint bubbles on the Jake fade and the failed-auction rules.

The print count is the `trades` column already stored on each minute, price, and
aggressor side. A bubble is one print (`trades == 1`) at or above a size. 15
contracts is the pre-holdout large-print cutoff: the 95th percentile of the
largest single print in a 09:30-11:30 minute, measured before 1 Jul 2025, was
13. The video's 60 is its own row. Nothing here places an order.
"""

from __future__ import annotations

import math
import sys
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
from scripts.run_jake_method import v4_direction
from scripts.run_limit_research import TRAIN_END, VAL_END, _num, firms, money, pct
from scripts.run_of_vp_videos import attach, bar_stamp, failed_auction, tick_area
from src.research.strategies.costs import COMMISSION_POINTS, TICK
from src.research.strategies.engine import load_bars
from src.research.strategies.hf_limit import Trade, _manage
from src.research.strategies.jake_rules import _week_sunday

OUT = ROOT / "docs" / "OF-VP-FOOTPRINT-TEST.md"
DATA = ROOT / "data" / "reference" / "nq_1m_master.parquet"
CVD = ROOT / "data" / "reference" / "cvd"
NY = "America/New_York"
OPEN = 9 * 60 + 30
END_WIN = 11 * 60 + 30
# Frozen from the pre-holdout morning tape, before any trade result.
LARGE_PRINT = 15
VIDEO_PRINT = 60
POKE_MAX = 25.0
JAKE_RISK = 20.0
FAIZ_RISK = 80.0
LEVEL_PAD = 2.0
# One point. On the train mornings, 25 bars had a 15-lot print within 1 tick of the
# high and 73 had one within 4 ticks. Four ticks is the band used below.
EXTREME_TICKS = 4
HOUSE_STOP = 2.0

GATED = (
    "j15_075", "j15_17", "j15_ref_17", "j60_17",
    "a15_075", "a15_17", "a15_poc", "a60_17",
    "b15_lim_075", "b15_lim_17", "b15_mkt_17", "b60_lim_17",
    "ext15_075", "ext15_17", "ext15_lvl_17", "ext60_17",
)
PLAIN = ("plain_075", "plain_17")
FAMILY = {
    "j15_075": "j15", "j15_17": "j15", "j15_ref_17": "j15_ref", "j60_17": "j60",
    "a15_075": "a15", "a15_17": "a15", "a15_poc": "a15", "a60_17": "a60",
    "b15_lim_075": "b15_lim", "b15_lim_17": "b15_lim", "b15_mkt_17": "b15_mkt", "b60_lim_17": "b60",
    "ext15_075": "ext15", "ext15_17": "ext15", "ext15_lvl_17": "ext15_lvl", "ext60_17": "ext60",
}


def load_footprint():
    """Morning delta, and single prints of at least 15 contracts."""
    bubbles: dict[pd.Timestamp, list[tuple[float, str, float]]] = {}
    delta: dict[pd.Timestamp, tuple[float, float]] = {}
    for path in sorted(CVD.glob("footprint_*.parquet")):
        frame = pd.read_parquet(path, columns=["ts_minute", "price", "side", "volume", "trades"])
        frame["ts"] = pd.to_datetime(frame["ts_minute"], utc=True).dt.tz_convert(NY)
        hm = frame["ts"].dt.hour * 60 + frame["ts"].dt.minute
        morn = frame[(hm >= OPEN) & (hm <= END_WIN)]
        if morn.empty:
            continue
        buy = np.where(morn["side"].to_numpy() == "B", morn["volume"].to_numpy(), 0.0)
        sell = np.where(morn["side"].to_numpy() == "A", morn["volume"].to_numpy(), 0.0)
        grouped = pd.DataFrame({"ts": morn["ts"].to_numpy(), "buy": buy, "sell": sell})
        totals = grouped.groupby("ts", sort=False)[["buy", "sell"]].sum()
        for ts, row in totals.iterrows():
            delta[pd.Timestamp(ts)] = (float(row["buy"]), float(row["sell"]))
        bub = morn[(morn["trades"] == 1) & (morn["volume"] >= LARGE_PRINT)]
        for ts, part in bub.groupby("ts", sort=False):
            stamp = pd.Timestamp(ts)
            rows = bubbles.setdefault(stamp, [])
            rows.extend(
                (float(px), str(side), float(vol))
                for px, side, vol in zip(part["price"], part["side"], part["volume"], strict=True)
            )
        print("tape", path.name, len(bub), flush=True)
    return bubbles, delta


def is_bubble(price: float, side: str, volume: float, trades: int, min_vol: float) -> bool:
    """One aggressor print at or above `min_vol`. Several small prints do not qualify."""
    return bool(int(trades) == 1 and float(volume) >= min_vol and side in ("A", "B") and np.isfinite(price))


def bubbles_at(book: list[tuple[float, str, float]] | None, min_vol: float, side: int, extreme: float):
    if not book:
        return []
    kept = []
    for price, ag, vol in book:
        if vol < min_vol:
            continue
        on_high = side == -1 and ag == "B" and price >= extreme - TICK
        on_low = side == 1 and ag == "A" and price <= extreme + TICK
        if on_high or on_low:
            kept.append((price, vol))
    return kept


def _window_end(day) -> int:
    hit = np.flatnonzero((np.arange(len(day.hm)) >= day.i_open) & (day.hm > END_WIN) & (day.hm < 18 * 60))
    return min(day.end, int(hit[0]) if len(hit) else day.end)


def _no_reward(day, i: int, side: int, delta) -> bool:
    rng = float(day.h[i] - day.l[i])
    if rng <= 0:
        return False
    rec = delta.get(bar_stamp(day, i))
    if rec is None:
        return False
    signed = rec[0] - rec[1]
    pos = (float(day.c[i]) - float(day.l[i])) / rng
    if side == -1:
        return signed > 0 and float(day.c[i]) <= float(day.o[i]) + TICK and pos <= 0.5
    return signed < 0 and float(day.c[i]) >= float(day.o[i]) - TICK and pos >= 0.5


def _refreshed(day, i: int, side: int, extreme: float, delta) -> bool:
    j = i + 1
    if j >= len(day.hm) or int(day.hm[j]) > END_WIN or int(day.hm[j]) >= 18 * 60:
        return False
    rec = delta.get(bar_stamp(day, j))
    if rec is None:
        return False
    signed = rec[0] - rec[1]
    if side == -1:
        return signed < 0 and float(day.c[j]) < extreme
    return signed > 0 and float(day.c[j]) > extreme


def attach_week(days) -> None:
    """Sunday-anchored 70% area from 1-minute closes. Today's cash session is not in it."""
    hist: dict[int, float] = {}
    week = None
    ranges: list[float] = []
    for day in days:
        sunday = _week_sunday(pd.DatetimeIndex([day.ts.normalize()]))[0]
        if week is None or sunday != week:
            hist = {}
            week = sunday
        width = float(day.onh - day.onl) if np.isfinite(day.onh) and np.isfinite(day.onl) else float("nan")
        med = float(np.median(ranges[-20:])) if len(ranges) >= 20 else float("nan")
        pre = np.flatnonzero((day.hm >= 18 * 60) | (day.hm < OPEN))
        close_0929 = float(day.c[int(pre[-1])]) if len(pre) else float("nan")
        day.regime = v4_direction(day.onh, day.onl, close_0929, width, med)
        for i in pre:
            key = int(np.rint(float(day.c[i]) / TICK))
            hist[key] = hist.get(key, 0.0) + float(day.vol[i])
        if len(hist) >= 10:
            keys = np.fromiter(hist.keys(), dtype=np.int64)
            vols = np.fromiter(hist.values(), dtype=float)
            day.week_va = tick_area(keys * TICK, vols)
        else:
            day.week_va = None
        rth = np.flatnonzero((day.hm >= OPEN) & (day.hm < 16 * 60))
        for i in rth:
            key = int(np.rint(float(day.c[i]) / TICK))
            hist[key] = hist.get(key, 0.0) + float(day.vol[i])
        if np.isfinite(width) and width > 0:
            ranges.append(width)


def jake_setup(day, bubbles, delta, min_vol: float, refresh: bool):
    area = day.week_va
    if area is None or day.regime != 0:
        return None
    val, vah, poc = area
    end = _window_end(day)
    i = day.i_open
    while i < end - (2 if refresh else 1):
        hm = int(day.hm[i])
        if hm > END_WIN and hm < 18 * 60:
            break
        if hm < OPEN:
            i += 1
            continue
        short = (
            float(day.h[i]) >= vah - LEVEL_PAD
            and float(day.h[i]) <= vah + POKE_MAX
            and _no_reward(day, i, -1, delta)
            and bool(bubbles_at(bubbles.get(bar_stamp(day, i)), min_vol, -1, float(day.h[i])))
        )
        long = (
            float(day.l[i]) <= val + LEVEL_PAD
            and float(day.l[i]) >= val - POKE_MAX
            and _no_reward(day, i, 1, delta)
            and bool(bubbles_at(bubbles.get(bar_stamp(day, i)), min_vol, 1, float(day.l[i])))
        )
        if short == long:
            i += 1
            continue
        side = -1 if short else 1
        level = vah if short else val
        extreme = float(day.h[i] if short else day.l[i])
        start = i + 1
        if refresh:
            if not _refreshed(day, i, side, extreme, delta):
                i += 1
                continue
            start = i + 2
        if start >= end:
            return None
        stop_px = extreme + 2 * TICK if side == -1 else extreme - 2 * TICK
        return {
            "side": side, "level": level, "stop": stop_px, "start": start,
            "poc": poc, "other": val if short else vah,
        }
    return None


def auction_bubble(day, bubbles, min_vol: float):
    setup = failed_auction(day)
    if setup is None:
        return None
    for j in range(setup["poke"], setup["reclaim"] + 1):
        extreme = float(day.h[j] if setup["side"] == -1 else day.l[j])
        if bubbles_at(bubbles.get(bar_stamp(day, j)), min_vol, setup["side"], extreme):
            return setup
    return None


def wick_cluster(day, setup, bubbles, min_vol: float):
    """Largest single print outside the finished bar's body. The path inside the minute is not known."""
    if setup is None:
        return None
    book = bubbles.get(bar_stamp(day, setup["poke"]))
    if not book:
        return None
    o = float(day.o[setup["poke"]])
    c = float(day.c[setup["poke"]])
    body_lo, body_hi = (o, c) if o <= c else (c, o)
    wick = []
    body = []
    for price, ag, vol in book:
        if vol < min_vol:
            continue
        if setup["side"] == -1 and ag != "B":
            continue
        if setup["side"] == 1 and ag != "A":
            continue
        if price > body_hi + 1e-9 or price < body_lo - 1e-9:
            wick.append((price, vol))
        else:
            body.append((price, vol))
    if not wick or sum(vol for _px, vol in wick) <= sum(vol for _px, vol in body):
        return None
    return max(wick, key=lambda item: item[1])[0]


def _near_level(price: float, levels) -> bool:
    return any(np.isfinite(level) and abs(price - level) <= LEVEL_PAD for level in levels)


def extreme_setup(day, bubbles, min_vol: float, near_level: bool):
    """First no-reward bar whose single print sits within one point of the extreme.

    The stop is two points beyond the print. A two-tick stop is under the two-point
    minimum, because the print is already on the extreme.
    """
    highs = [day.onh, day.pdh]
    lows = [day.onl, day.pdl]
    if day.on_va is not None:
        highs.append(day.on_va[1])
        lows.append(day.on_va[0])
    if day.week_va is not None:
        highs.append(day.week_va[1])
        lows.append(day.week_va[0])
    end = _window_end(day)
    for i in range(day.i_open, end - 1):
        book = bubbles.get(bar_stamp(day, i))
        hi = float(day.h[i])
        lo = float(day.l[i])
        rng = hi - lo
        if rng <= 0 or not book:
            continue
        pos = (float(day.c[i]) - lo) / rng
        buys = [
            price for price, ag, vol in book
            if ag == "B" and vol >= min_vol and hi - price <= EXTREME_TICKS * TICK
        ]
        sells = [
            price for price, ag, vol in book
            if ag == "A" and vol >= min_vol and price - lo <= EXTREME_TICKS * TICK
        ]
        short = bool(buys) and float(day.c[i]) <= float(day.o[i]) + TICK and pos <= 0.5
        long = bool(sells) and float(day.c[i]) >= float(day.o[i]) - TICK and pos >= 0.5
        if short and near_level:
            short = _near_level(hi, highs)
        if long and near_level:
            long = _near_level(lo, lows)
        if short == long:
            continue
        if short:
            price = max(buys)
            return {"side": -1, "level": price, "stop": price + HOUSE_STOP, "start": i + 1}
        price = min(sells)
        return {"side": 1, "level": price, "stop": price - HOUSE_STOP, "start": i + 1}
    return None


def reload_market(day, bubbles, min_vol: float):
    setup = failed_auction(day)
    if setup is None:
        return None
    cluster = wick_cluster(day, setup, bubbles, min_vol)
    if cluster is None:
        return None
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
        if setup["side"] * (stop_px - fill) >= 0 or not (2.0 <= risk <= FAIZ_RISK):
            return None
        return {**setup, "fill": fill, "bar": entry_i, "stop": stop_px, "risk": risk, "level": cluster}
    return None


def rest_limit(day, setup, reward: float | None, target: float | None, max_risk: float):
    if setup is None:
        return []
    end = _window_end(day)
    start = int(setup.get("start", setup.get("reclaim", -1) + 1))
    if start >= end:
        return []
    side = setup["side"]
    level = float(setup["level"])
    stop_px = float(setup["stop"])
    for i in range(start, end):
        if side == 1:
            hit = float(day.o[i]) > level - TICK and float(day.l[i]) <= level - TICK
        else:
            hit = float(day.o[i]) < level + TICK and float(day.h[i]) >= level + TICK
        if not hit:
            continue
        risk = abs(level - stop_px)
        if side * (stop_px - level) >= 0 or not (2.0 <= risk <= max_risk):
            return []
        px = level + side * reward * risk if reward is not None else target
        if px is None or side * (px - level) < 1.0:
            return []
        _k, gross, mae, hit_flag = _manage(
            side, level, stop_px, px, day.o, day.h, day.l, day.c, day.hm, i, day.end,
        )
        trade = Trade(gross, risk, mae, hit_flag)
        trade.planned = abs(px - level)
        return [trade]
    return []


def market_from(day, setup, reward: float):
    if setup is None:
        return []
    target = setup["fill"] + setup["side"] * reward * setup["risk"]
    if setup["side"] * (target - setup["fill"]) < 1.0:
        return []
    _k, gross, mae, hit = _manage(
        setup["side"], setup["fill"], setup["stop"], target, day.o, day.h, day.l, day.c, day.hm, setup["bar"], day.end,
    )
    trade = Trade(gross, setup["risk"], mae, hit)
    trade.planned = abs(target - setup["fill"])
    return [trade]


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


def render(rows, winner, lives, onhl, notes) -> str:
    lines = [
        "# Footprint bubbles on the absorption rules",
        "",
        _lead(winner, onhl, lives),
        "",
        "Disarmed. Nothing here places an order. LucidFlex evals are at 50%, and the fee is the assumed $100. FundedNext is charged Topstep's $1.22 MNQ round turn because that firm does not publish an MNQ rate.",
        "",
        "The order-flow tape is the per-minute footprint already in `data/reference/cvd/`. Each row is one minute, one price, and one aggressor side. `volume` is the contracts. `trades` is how many prints made that volume. A bubble is `trades == 1` and `volume` at or above a cutoff: one print, not a pile of one-lots. The contiguous files run from June 2025 through July 2026. The 2023 and 2024 files cover 18:00 to 11:00 ET, which is enough for the morning entry and not a full session. This run did not buy anything.",
        "",
        "Fifteen contracts is the large-print cutoff. On mornings before 1 July 2025, the 95th percentile of the biggest single print in a 09:30-11:30 minute was 13 contracts, so 15 is that bar rounded up. It was fixed before any of these trades were scored. Sixty is the number in the Faiz video, kept as its own rows. The same video never said whether 60 was NQ or MNQ. On this NQ tape a single 60-lot print is rare.",
        "",
        "Jake's row fades the Sunday-to-09:29 value area, 70% on one-tick bins of the one-minute closes, and stands down on his large-overnight regime. The bar has to tag the edge, close without reward, and print a bubble at the extreme. The refresh row also needs the next minute's delta to flip and the close to take out that extreme. The order is a resting limit at the edge, trade-through, cancelled at 11:30. The stop is the extreme plus two ticks, and a risk wider than 20 points is skipped.",
        "",
        "The failed-auction row is the overnight value area, a poke outside, and a close back inside within three bars. The filter keeps it only when a bubble sits on the breakout side at the extreme of one of those bars. The limit rests at the reclaimed edge. The reload row keeps a failed auction whose largest bubble is outside the body of the finished poke bar, and rests at that price. A second reload row enters only after a later close back through that price. Body versus wick uses the finished high, low, open, and close. The footprint does not say which print came first inside the minute.",
        "",
        "The level-gated rows almost never fire: a 15-lot print on the failed-auction extreme, or within two points of the overnight high, the prior-day high, or the value-area edge, is a handful of days. The extra rows drop the level and keep the absorption itself. The first 09:30-11:30 bar with a single print of at least 15 contracts within one point of the bar's high or low, and a close that does not reward that print, rests a limit at the print on the next bars. The stop is two points past the print. A two-tick stop would be under the two-point minimum this stack already uses, because the print is on the extreme. Sixty contracts is the same row with the video's size.",
        "",
        "What the footprint cannot answer is a refill of the offer inside the minute. That would be a sub-second book, not this tape. Last-of-minute depth snapshots are a different file and are not a refill clock, so they are not used. The order of prints inside the minute is not in the file either. GEX walls are not in the footprint.",
        "",
        "A footprint row needs 80 validation fills to be ranked on the old line. The mornings with a footprint before 1 July 2025 are October 2024 and June 2025, plus five earlier months in the train window, so 80 fills is not available for a one-trade-a-day filter. If none reach 80, the rank falls to rows with at least 20 validation fills, and the doc says so. The sort is validation mean R. Holdout, from 1 July 2025, is scored after that choice. The plain failed auction is the control. It is in the multiple-testing list and it is not eligible. Benjamini-Hochberg at 10% covers every validation test of mean R above zero. Costs match the rest of the stack.",
        "",
        (
            f"Validation mornings with a footprint minute: {notes['val_days']}. "
            f"Failed auctions on those mornings: {notes['val_auction']}. "
            f"Of those, {notes['val_a15']} had a 15-lot bubble at the extreme and {notes['val_a60']} had a 60-lot bubble. "
            f"Reload clusters: {notes['val_b15']} at 15 lots and {notes['val_b60']} at 60."
        ),
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
    by_name = {row["name"]: row for row in rows}
    wide = by_name["ext15_17"]["val"]
    plain = by_name["plain_17"]["val"]
    a(
        f"The widest bubble row, `ext15_17`, filled {wide['n']} validation trades. "
        f"The plain failed auction filled {plain['n']} and its validation mean R is {_num(plain['r'][0])}. "
        "No footprint row reached 20 fills, so none is sent to the holdout or the lifecycle."
    )
    a("")
    a("## Holdout")
    a("")
    if winner is None:
        a("No footprint row had 20 validation fills, so the holdout stays closed.")
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
        thin = "The rank used the 20-fill line because no footprint row reached 80 validation fills." if winner.get("thin") else ""
        if thin:
            a("")
            a(thin)
    a("")
    a("## Lifecycle")
    a("")
    a(
        "The selected entry is replayed at 0.75R in the eval and 1.7R once funded, one resting limit, using that entry's stop. "
        "The overnight row is a 15-point stop on the same shape. Grind days use each book's own holdout hit rate."
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
    return "\n".join(lines) + "\n"


def _lead(winner, onhl, lives) -> str:
    if winner is None:
        return "No footprint filter had enough validation fills to compare with the overnight pull on the holdout."
    h = winner["hold"]
    above = (not math.isnan(h["r"][1])) and h["r"][1] > onhl["r"][0]
    if above:
        bit = (
            f"`{winner['name']}` has a holdout mean-R interval above the overnight pull. "
            f"Mean R {_num(h['r'][0])} ({_num(h['r'][1])} to {_num(h['r'][2])}) against {_num(onhl['r'][0])}."
        )
    else:
        bit = (
            f"The footprint filters do not beat `onhl_pull_s15` on the holdout. "
            f"The validation choice, `{winner['name']}`, has mean R {_num(h['r'][0])} "
            f"({_num(h['r'][1])} to {_num(h['r'][2])}) on {h['n']} fills. "
            f"The overnight pull is {_num(onhl['r'][0])} ({_num(onhl['r'][1])} to {_num(onhl['r'][2])}) on {onhl['n']} fills."
        )
    sel = next((row for row in lives if row["book"] == "selected" and row["firm"] == "Topstep"), None)
    base = next((row for row in lives if row["book"] == "onhl" and row["firm"] == "Topstep"), None)
    if sel and base:
        beat = (not math.isnan(sel["life"]["lo"])) and sel["life"]["lo"] > base["life"]["mean"]
        word = "above" if beat else "against"
        bit += f" Topstep per eval is {money(sel['life']['mean'])} {word} {money(base['life']['mean'])}."
    return bit


def main() -> None:
    print("load", flush=True)
    df = load_bars(str(DATA))
    days = build_days(df)
    attach(df, days)
    attach_week(days)
    print("tape", flush=True)
    bubbles, delta = load_footprint()
    print("signals", len(days), len(bubbles), flush=True)
    names = list(GATED) + list(PLAIN)
    books = {name: [] for name in names}
    life = {fam: {reward: [] for reward in (0.75, 1.7)} for fam in set(FAMILY.values())}
    notes = {"val_days": 0, "val_auction": 0, "val_a15": 0, "val_a60": 0, "val_b15": 0, "val_b60": 0}
    for day in days:
        j15 = jake_setup(day, bubbles, delta, LARGE_PRINT, False)
        j15r = jake_setup(day, bubbles, delta, LARGE_PRINT, True)
        j60 = jake_setup(day, bubbles, delta, VIDEO_PRINT, False)
        auction = failed_auction(day)
        a15 = auction_bubble(day, bubbles, LARGE_PRINT)
        a60 = auction_bubble(day, bubbles, VIDEO_PRINT)
        b15 = None if wick_cluster(day, auction, bubbles, LARGE_PRINT) is None else auction
        b60 = None if auction is None or wick_cluster(day, auction, bubbles, VIDEO_PRINT) is None else auction
        b15_m = reload_market(day, bubbles, LARGE_PRINT)
        books["j15_075"].append(rest_limit(day, j15, 0.75, None, JAKE_RISK))
        books["j15_17"].append(rest_limit(day, j15, 1.7, None, JAKE_RISK))
        books["j15_ref_17"].append(rest_limit(day, j15r, 1.7, None, JAKE_RISK))
        books["j60_17"].append(rest_limit(day, j60, 1.7, None, JAKE_RISK))
        books["a15_075"].append(rest_limit(day, a15, 0.75, None, FAIZ_RISK))
        books["a15_17"].append(rest_limit(day, a15, 1.7, None, FAIZ_RISK))
        books["a15_poc"].append(rest_limit(day, a15, None, None if a15 is None else a15["poc"], FAIZ_RISK))
        books["a60_17"].append(rest_limit(day, a60, 1.7, None, FAIZ_RISK))
        b15_lim = None if b15 is None else {**b15, "level": wick_cluster(day, b15, bubbles, LARGE_PRINT), "start": b15["poke"] + 1}
        b60_lim = None if b60 is None else {**b60, "level": wick_cluster(day, b60, bubbles, VIDEO_PRINT), "start": b60["poke"] + 1}
        books["b15_lim_075"].append(rest_limit(day, b15_lim, 0.75, None, FAIZ_RISK))
        books["b15_lim_17"].append(rest_limit(day, b15_lim, 1.7, None, FAIZ_RISK))
        books["b15_mkt_17"].append(market_from(day, b15_m, 1.7))
        books["b60_lim_17"].append(rest_limit(day, b60_lim, 1.7, None, FAIZ_RISK))
        books["plain_075"].append(rest_limit(day, auction, 0.75, None, FAIZ_RISK))
        books["plain_17"].append(rest_limit(day, auction, 1.7, None, FAIZ_RISK))
        ext15 = extreme_setup(day, bubbles, LARGE_PRINT, False)
        ext_lvl = extreme_setup(day, bubbles, LARGE_PRINT, True)
        ext60 = extreme_setup(day, bubbles, VIDEO_PRINT, False)
        books["ext15_075"].append(rest_limit(day, ext15, 0.75, None, FAIZ_RISK))
        books["ext15_17"].append(rest_limit(day, ext15, 1.7, None, FAIZ_RISK))
        books["ext15_lvl_17"].append(rest_limit(day, ext_lvl, 1.7, None, FAIZ_RISK))
        books["ext60_17"].append(rest_limit(day, ext60, 1.7, None, FAIZ_RISK))
        life["j15"][0.75].append(books["j15_075"][-1])
        life["j15"][1.7].append(books["j15_17"][-1])
        life["j15_ref"][0.75].append(rest_limit(day, j15r, 0.75, None, JAKE_RISK))
        life["j15_ref"][1.7].append(books["j15_ref_17"][-1])
        life["j60"][0.75].append(rest_limit(day, j60, 0.75, None, JAKE_RISK))
        life["j60"][1.7].append(books["j60_17"][-1])
        life["a15"][0.75].append(books["a15_075"][-1])
        life["a15"][1.7].append(books["a15_17"][-1])
        life["a60"][0.75].append(rest_limit(day, a60, 0.75, None, FAIZ_RISK))
        life["a60"][1.7].append(books["a60_17"][-1])
        life["b15_lim"][0.75].append(books["b15_lim_075"][-1])
        life["b15_lim"][1.7].append(books["b15_lim_17"][-1])
        life["b15_mkt"][0.75].append(market_from(day, b15_m, 0.75))
        life["b15_mkt"][1.7].append(books["b15_mkt_17"][-1])
        life["b60"][0.75].append(rest_limit(day, b60_lim, 0.75, None, FAIZ_RISK))
        life["b60"][1.7].append(books["b60_lim_17"][-1])
        life["ext15"][0.75].append(books["ext15_075"][-1])
        life["ext15"][1.7].append(books["ext15_17"][-1])
        life["ext15_lvl"][0.75].append(rest_limit(day, ext_lvl, 0.75, None, FAIZ_RISK))
        life["ext15_lvl"][1.7].append(books["ext15_lvl_17"][-1])
        life["ext60"][0.75].append(rest_limit(day, ext60, 0.75, None, FAIZ_RISK))
        life["ext60"][1.7].append(books["ext60_17"][-1])
        if TRAIN_END <= day.ts < VAL_END and bar_stamp(day, day.i_open) in delta:
            notes["val_days"] += 1
            if auction is not None:
                notes["val_auction"] += 1
            if a15 is not None:
                notes["val_a15"] += 1
            if a60 is not None:
                notes["val_a60"] += 1
            if b15 is not None:
                notes["val_b15"] += 1
            if b60 is not None:
                notes["val_b60"] += 1
    val_i = [i for i, d in enumerate(days) if TRAIN_END <= d.ts < VAL_END]
    hold_i = [i for i, d in enumerate(days) if d.ts >= VAL_END]
    rows = []
    for name, book in books.items():
        trades = _fills(book, val_i)
        p0 = null_of(trades)
        scored = r_test(trades, p0)
        rows.append({
            "name": name, "book": book, "val": scored, "null": p0, "be": be_of(trades),
            "gated": name in GATED, "ranked": False, "bh": False,
        })
        print(name, scored["n"], flush=True)
    flags = bh_mask(np.array([r["val"]["p_r"] for r in rows]))
    for row, ok in zip(rows, flags, strict=True):
        row["bh"] = bool(ok)
    gated_rows = [r for r in rows if r["gated"]]
    pool = [r for r in gated_rows if r["val"]["n"] >= 80 and not math.isnan(r["val"]["r"][0])]
    thin = False
    if not pool:
        pool = [r for r in gated_rows if r["val"]["n"] >= 20 and not math.isnan(r["val"]["r"][0])]
        thin = bool(pool)
    for row in pool:
        row["ranked"] = True
    winner = max(pool, key=lambda r: r["val"]["r"][0]) if pool else None
    onhl17, _src = onhl_book(days, None, 0, 1.7)
    onhl75, _src = onhl_book(days, None, 0, 0.75)
    onhl_tr = _fills(onhl17, hold_i)
    onhl = hit_test(onhl_tr, P0)
    onhl["r"] = mean_r(onhl_tr)
    if winner is not None:
        winner["thin"] = thin
        print("winner", winner["name"], "thin", thin, flush=True)
        hold_tr = _fills(winner["book"], hold_i)
        winner["hold"] = r_test(hold_tr, null_of(hold_tr))
        winner["hold_null"] = null_of(hold_tr)
        winner["hold_be"] = be_of(hold_tr)
    lives = []
    pair = [("onhl", onhl75, onhl17)]
    if winner is not None:
        fam = FAMILY[winner["name"]]
        pair.insert(0, ("selected", life[fam][0.75], life[fam][1.7]))
    for label, eval_book, fund_book in pair:
        eh = [eval_book[i] for i in hold_i]
        fh = [fund_book[i] for i in hold_i]
        trades = [tr for day_book in eh for tr in day_book]
        grind = (sum(tr.hit for tr in trades) / len(trades)) if trades else 0.5
        for spec in firms():
            risk = min(2000.0, float(spec["mll"]))
            life_stat = fullport_life(
                eh, fh, spec, np.random.default_rng(_seed("fp" + label + spec["firm"])), risk, grind, n=400,
            )
            cash, _note, _slots = month_book(eh, fh, spec, risk, grind, n=100)
            mid = float(cash.mean())
            se = float(cash.std(ddof=1) / math.sqrt(len(cash)))
            passes = month_passes(eh, spec, risk, grind, n=60)
            lives.append({
                "firm": spec["firm"], "book": label, "life": life_stat, "passes": passes,
                "month": {"mean": mid, "lo": mid - 1.96 * se, "hi": mid + 1.96 * se, "p_neg": float(np.mean(cash < 0))},
            })
            print("life", label, spec["firm"], round(life_stat["mean"], 1), flush=True)
    OUT.write_text(render(rows, winner, lives, onhl, notes))
    print("wrote", OUT, flush=True)


if __name__ == "__main__":
    main()
