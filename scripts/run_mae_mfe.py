"""MAE and MFE of the resting-limit entries, then a modest exit grid.

Distributions use train and validation only. The exit is chosen on validation.
Holdout starts 1 Jul 2025 and is read after that choice. Nothing places an order.
"""

from __future__ import annotations

import math
import sys
import zlib
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_daily_book import (
    at_minute,
    attach_va,
    fallback_orders,
    first_touch,
    month_passes,
    onhl_orders,
)
from scripts.run_daily_book import (
    run_book as daily_run,
)
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
from src.research.strategies.costs import COMMISSION_POINTS, TICK
from src.research.strategies.engine import load_bars
from src.research.strategies.hf_limit import Trade, _manage

OUT = ROOT / "docs" / "MAE-MFE.md"
CHARTS = ROOT / "output" / "mae_mfe"
DATA = ROOT / "data" / "reference" / "nq_1m_master.parquet"
OPEN = 9 * 60 + 30
UNTIL = 11 * 60 + 30
HORIZONS = ("15m", "30m", "60m", "1130", "close")
MAE_CAPS = (4, 6, 8, 10, 12, 15, 20, 30)
ENTRIES = ("ib", "ib_1030", "onhl", "london4", "pdhl", "va")


def horizon_end(day, bar: int, kind: str) -> int:
    """Exclusive end index for a horizon that starts at `bar`."""
    hm0 = int(day.hm[bar])
    if kind == "close":
        return day.end
    if kind == "1130":
        if hm0 > UNTIL:
            return bar
        hit = np.flatnonzero((np.arange(len(day.hm)) > bar) & (day.hm > UNTIL) & (day.hm < 18 * 60))
        return min(day.end, int(hit[0]) if len(hit) else day.end)
    add = {"15m": 15, "30m": 30, "60m": 60}[kind]
    limit = hm0 + add
    hit = np.flatnonzero((np.arange(len(day.hm)) > bar) & (day.hm >= limit) & (day.hm < 18 * 60))
    return min(day.end, int(hit[0]) if len(hit) else day.end)


def path_stats(side: int, entry: float, h, l, hm, start: int, end: int):
    """MAE and MFE from `entry` over [start, end). The first print of each extreme is kept."""
    if end <= start:
        return None
    mae = 0.0
    mfe = 0.0
    i_mae = start
    i_mfe = start
    for k in range(start, end):
        if side == 1:
            fav = float(h[k]) - entry
            adv = entry - float(l[k])
        else:
            fav = entry - float(l[k])
            adv = float(h[k]) - entry
        if fav > mfe + 1e-12:
            mfe = fav
            i_mfe = k
        if adv > mae + 1e-12:
            mae = adv
            i_mae = k
    return {
        "mae": mae,
        "mfe": mfe,
        "t_mae": int(hm[i_mae] - hm[start]),
        "t_mfe": int(hm[i_mfe] - hm[start]),
        "mfe_first": bool(i_mfe < i_mae),
    }


def attach_atr(days) -> None:
    ranges: list[float] = []
    for day in days:
        rth = (day.hm >= OPEN) & (day.hm < 16 * 60)
        day.atr_day = float(np.mean(ranges[-20:])) if len(ranges) >= 20 else float("nan")
        if np.isfinite(day.onh) and np.isfinite(day.onl) and day.onh > day.onl:
            day.on_range = float(day.onh - day.onl)
        else:
            day.on_range = float("nan")
        if int(rth.sum()) >= 30:
            ranges.append(float(day.h[rth].max() - day.l[rth].min()))


def _touch(day, buy, sell, start: int):
    got = first_touch(day.o, day.h, day.l, buy, sell, start, day.end)
    if got is None:
        return None
    side, limit, bar = got
    return {"side": side, "entry": limit, "bar": bar}


def entry_on(day, name: str):
    """The filled resting limit, or None. `ib` is the daily-book fallback, not every IB touch."""
    if name == "ib":
        buy, sell = onhl_orders(day)
        cancel = min(at_from_daily(day), day.end)
        if first_touch(day.o, day.h, day.l, buy, sell, day.i_open, cancel) is not None:
            return None
        fbuy, fsell, fstart = fallback_orders(day, "ib")
        return _touch(day, fbuy, fsell, max(cancel, fstart))
    if name == "ib_1030":
        fbuy, fsell, fstart = fallback_orders(day, "ib")
        return _touch(day, fbuy, fsell, fstart)
    if name == "onhl":
        buy, sell = onhl_orders(day)
        return _touch(day, buy, sell, day.i_open)
    if name in ("london4", "pdhl", "va"):
        buy, sell, start = fallback_orders(day, name)
        return _touch(day, buy, sell, start)
    return None


def at_from_daily(day) -> int:
    return at_minute(day, 11 * 60)


def excursion(day, fill: dict):
    out = {}
    for kind in HORIZONS:
        end = horizon_end(day, fill["bar"], kind)
        stats = path_stats(fill["side"], fill["entry"], day.h, day.l, day.hm, fill["bar"], end)
        out[kind] = stats
    return out


def random_fill(day, fill: dict, name: str):
    seed = zlib.crc32(f"{day.ts.isoformat()}|{name}".encode()) & 0x7FFFFFFF
    side = 1 if np.random.default_rng(seed).random() < 0.5 else -1
    return {"side": side, "entry": float(day.o[fill["bar"]]), "bar": fill["bar"]}


def same_side_fill(day, fill: dict):
    return {"side": fill["side"], "entry": float(day.o[fill["bar"]]), "bar": fill["bar"]}


def _finite(values):
    arr = np.asarray(list(values), dtype=float)
    return arr[np.isfinite(arr)]


def mean_ci(values):
    arr = _finite(values)
    n = len(arr)
    if n < 2:
        return float("nan"), float("nan"), float("nan"), n
    mid = float(arr.mean())
    se = float(arr.std(ddof=1) / math.sqrt(n))
    return mid, mid - 1.96 * se, mid + 1.96 * se, n


def quantiles(values):
    arr = _finite(values)
    if len(arr) < 5:
        return None
    return {
        "n": len(arr),
        "mean": float(arr.mean()),
        "p50": float(np.quantile(arr, 0.50)),
        "p75": float(np.quantile(arr, 0.75)),
        "p90": float(np.quantile(arr, 0.90)),
    }


def unit(points, scale):
    if points is None or not np.isfinite(scale) or scale <= 0:
        return float("nan")
    return points / scale


def cells():
    """Twenty exit rules. Fixed before any holdout number is read."""
    out = []
    for stop in (8.0, 12.0, 15.0, 20.0):
        for reward in (0.75, 1.7):
            out.append({"name": f"s{stop:.0f}_r{reward}", "kind": "fixed", "stop": stop, "reward": reward, "horizon": "close"})
        out.append({"name": f"s{stop:.0f}_opp", "kind": "opposite", "stop": stop, "reward": "opposite", "horizon": "close"})
    for k, label in ((0.10, "atr10_r1.7"), (0.20, "atr20_r1.7")):
        out.append({"name": label, "kind": "atr", "k": k, "reward": 1.7, "horizon": "close"})
    out.append({"name": "lvl2_opp", "kind": "fixed", "stop": 2.0, "reward": "opposite", "horizon": "close"})
    out.append({"name": "lvl2_r1.7", "kind": "fixed", "stop": 2.0, "reward": 1.7, "horizon": "close"})
    out.append({"name": "next_opp", "kind": "next", "reward": "opposite", "horizon": "close"})
    for name, horizon in (("t30", "30m"), ("t60", "60m"), ("t1130", "1130")):
        out.append({"name": name, "kind": "fixed", "stop": 15.0, "reward": 1.7, "horizon": horizon})
    return out


def _opposite(day, side: int):
    if not np.isfinite(day.ib_hi) or not np.isfinite(day.ib_lo):
        return None
    return float(day.ib_hi if side == 1 else day.ib_lo)


def _next_stop(day, side: int, entry: float):
    dists = []
    candidates = [day.onl, day.onh, day.pdl, day.pdh]
    if getattr(day, "va", None) is not None:
        candidates.extend([day.va[0], day.va[1]])
    for px in candidates:
        if not np.isfinite(px):
            continue
        dist = side * (entry - float(px))
        if dist >= 4.0:
            dists.append(dist + 1.0)
    if not dists:
        return None
    return min(dists)


def _stop_and_target(day, fill, spec):
    kind = spec["kind"]
    if kind == "atr":
        if not np.isfinite(day.atr_day):
            return None
        stop = spec["k"] * day.atr_day
        target = fill["entry"] + fill["side"] * spec["reward"] * stop
    elif kind == "next":
        stop = _next_stop(day, fill["side"], fill["entry"])
        if stop is None:
            return None
        target = _opposite(day, fill["side"])
    else:
        stop = spec["stop"]
        if spec["reward"] == "opposite":
            target = _opposite(day, fill["side"])
        else:
            target = fill["entry"] + fill["side"] * float(spec["reward"]) * stop
    if stop is None or target is None or not (2.0 <= stop <= 80.0):
        return None
    if fill["side"] * (target - fill["entry"]) < 1.0:
        return None
    return stop, target


def simulate_cell(days, fills, spec):
    book = []
    for day, fill in zip(days, fills, strict=True):
        if fill is None:
            book.append([])
            continue
        planned = _stop_and_target(day, fill, spec)
        if planned is None:
            book.append([])
            continue
        stop, target = planned
        end = horizon_end(day, fill["bar"], spec["horizon"])
        if end <= fill["bar"]:
            book.append([])
            continue
        stop_px = fill["entry"] - fill["side"] * stop
        _k, gross, mae, hit = _manage(
            fill["side"], fill["entry"], stop_px, target, day.o, day.h, day.l, day.c, day.hm, fill["bar"], end,
        )
        trade = Trade(gross, stop, mae, hit)
        trade.planned = abs(target - fill["entry"])
        book.append([trade])
    return book


def r_test(trades, p0: float):
    n = len(trades)
    rs = np.array([(tr.gross - COMMISSION_POINTS) / tr.risk for tr in trades]) if n else np.array([])
    mid = mean_r(trades)
    if n < 20:
        p_r = 1.0
        hit = {"n": n, "hit": (sum(tr.hit for tr in trades) / n) if n else float("nan"), "lo": float("nan"), "hi": float("nan"), "p": 1.0}
    else:
        se = float(rs.std(ddof=1) / math.sqrt(n)) if n > 1 else float("nan")
        from statistics import NormalDist
        z = mid[0] / se if se and se > 0 else 0.0
        p_r = float(1.0 - NormalDist().cdf(z))
        hit = hit_test(trades, p0)
    return {"n": n, "r": mid, "p_r": p_r, "hit": hit, "p0": p0}


def null_of(trades) -> float:
    vals = []
    for tr in trades:
        reward = getattr(tr, "planned", float("nan"))
        if np.isfinite(reward) and reward > 0 and tr.risk > 0:
            vals.append(tr.risk / (tr.risk + reward))
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


def _rows_for(records, idxs, kind: str):
    mae, mfe, first = [], [], []
    for i in idxs:
        stats = records[i]
        if stats is None or stats.get(kind) is None:
            continue
        mae.append(stats[kind]["mae"])
        mfe.append(stats[kind]["mfe"])
        first.append(stats[kind]["mfe_first"])
    return mae, mfe, first


def paired_edge(real, random_rows, idxs, kind: str):
    diffs = []
    for i in idxs:
        a = real[i]
        b = random_rows[i]
        if a is None or b is None or a.get(kind) is None or b.get(kind) is None:
            continue
        diffs.append((a[kind]["mfe"] - a[kind]["mae"]) - (b[kind]["mfe"] - b[kind]["mae"]))
    return mean_ci(diffs)


def save_charts(ib_mae, ib_mfe, rnd_mae, rnd_mfe, caps, cond_mean):
    CHARTS.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.6))
    axes[0].hist(_finite(ib_mae), bins=30, color="#1f4b99", range=(0, 40))
    axes[0].set_title("IB fallback, adverse excursion")
    axes[0].set_xlabel("MAE to the close, points")
    axes[1].hist(_finite(ib_mfe), bins=30, color="#0f6b4c", range=(0, 80))
    axes[1].set_title("IB fallback, favorable excursion")
    axes[1].set_xlabel("MFE to the close, points")
    fig.tight_layout()
    fig.savefig(CHARTS / "ib_mae_mfe_close.png", dpi=120)
    plt.close(fig)

    labels = ["IB entry", "Random side"]
    means = []
    for mae, mfe in ((ib_mae, ib_mfe), (rnd_mae, rnd_mfe)):
        a = np.asarray(mae, dtype=float)
        b = np.asarray(mfe, dtype=float)
        n = min(len(a), len(b))
        means.append(float(b[:n].mean() - a[:n].mean()) if n else float("nan"))
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    ax.bar(labels, means, color=["#1f4b99", "#9aa0a6"])
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_ylabel("Mean MFE minus mean MAE, points")
    ax.set_title("Train and validation, held to the close")
    fig.tight_layout()
    fig.savefig(CHARTS / "ib_vs_random_balance.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.8, 3.6))
    ax.plot(list(caps), cond_mean, marker="o", color="#1f4b99")
    ax.set_xlabel("Trades whose MAE to the close stayed under this many points")
    ax.set_ylabel("Mean MFE of those trades")
    ax.set_title("Conditional favorable excursion")
    fig.tight_layout()
    fig.savefig(CHARTS / "ib_conditional_mfe.png", dpi=120)
    plt.close(fig)


def _fmt_q(stats) -> str:
    if stats is None:
        return "n/a"
    return f"{stats['mean']:.1f} / {stats['p50']:.1f} / {stats['p90']:.1f} (n={stats['n']})"


def render(summary, edge, cond, grid, winner, lives, coverage) -> str:
    lines = [
        "# MAE and MFE",
        "",
        _lead(edge, winner, lives),
        "",
        "Disarmed. Nothing here places an order. LucidFlex evals are at 50%. Charts are in `output/mae_mfe/`. That folder is gitignored, so the numbers below are the record.",
        "",
        "The entry is the trade-through of a resting limit. The path after that fill is measured with no stop and no target. MAE is the worst point against the trade. MFE is the best point for it. A same-bar print of both extremes counts as the adverse one coming first. Train and validation, through 30 Jun 2025, are the only windows in the distributions and in the exit choice. Holdout, from 1 Jul 2025, is read after the exit is chosen.",
        "",
        "IB in this note is the daily-book fallback. The initial-balance high and low are armed at 11:00, and only on days the overnight pull has not filled. The 10:30 version, with no overnight filter, is in the excursion table and is not an exit candidate. The other entries are the overnight pull, London high and low four points beyond the range, the prior-day high and low, and the prior cash-session value area.",
        "",
        f"Days: train {coverage['train']}, validation {coverage['val']}, holdout {coverage['hold']}.",
        "",
        "## Excursions, train and validation, held to the close",
        "",
        "Mean, median, and 90th percentile, in points. The last column is the share of trades whose favorable extreme printed on an earlier bar than the adverse extreme.",
        "",
        "| entry | n | MAE | MFE | MFE before MAE |",
        "|---|---:|---:|---:|---:|",
    ]
    a = lines.append
    for name, row in summary.items():
        a(f"| {name} | {row['n']} | {_fmt_q(row['mae'])} | {_fmt_q(row['mfe'])} | {pct(row['first'])} |")
    a("")
    early = summary.get("ib_1030")
    late = summary.get("ib")
    under15 = next((row for row in cond if row["cap"] == 15), None)
    if early and late and under15:
        a(
            f"The 10:30 initial-balance entry, with no overnight filter, has a median favorable excursion of {early['mfe']['p50']:.0f} points "
            f"and a median adverse excursion of {early['mae']['p50']:.0f}. Buying the initial-balance low, or selling the high, often sits near the extreme of the rest of the session, so the no-stop path looks generous. "
            f"The daily-book filter keeps the days that have not returned to the overnight level by 11:00. On those days the median favorable excursion is {late['mfe']['p50']:.0f} points and the median heat is {late['mae']['p50']:.0f}. "
            f"A 15 or 20 point stop sits inside that heat. Only {pct(under15['share'])} of those fills stay inside 15 points of adverse excursion all the way to the close."
        )
        a("")
    a("## Does the IB entry beat a random entry at the same minute?")
    a("")
    a(
        "For each IB fill, a control enters at that bar's open, long or short with a fixed seed, and is held to the same horizon. "
        "The score is MFE minus MAE. The difference is the IB score minus the control score. "
        "A same-side entry at that bar's open is not a second test. Both paths see the same highs and lows, so the gap in the score is twice the distance from the open to the limit. That is the trade-through, not a prediction."
    )
    a("")
    a("| sample | horizon | IB MFE−MAE | random MFE−MAE | paired difference |")
    a("|---|---|---:|---:|---:|")
    for row in edge:
        a(
            f"| {row['sample']} | {row['horizon']} | {row['ib']:.1f} | {row['rnd']:.1f} | "
            f"{row['diff']:.1f} ({row['lo']:.1f} to {row['hi']:.1f}) |"
        )
    a("")
    a("## Conditional MFE when MAE stays small")
    a("")
    a("Train and validation, IB fallback, held to the close. This is the usual claim that winners do not go far against you. The share is the fraction of all IB fills, not the fraction of winners.")
    a("")
    a("| MAE under | n | share | mean MFE | median MFE |")
    a("|---:|---:|---:|---:|---:|")
    for row in cond:
        a(f"| {row['cap']:.0f} | {row['n']} | {pct(row['share'])} | {row['mean']:.1f} | {row['p50']:.1f} |")
    a("")
    a("## Exit grid")
    a("")
    a(
        "Twenty rules on the IB fallback only. Fixed stops are 8, 12, 15 and 20 points, with a 0.75R target, a 1.7R target, or the other side of the initial balance. "
        "Two stops are 10% and 20% of the prior 20 cash-session ranges, with a 1.7R target. "
        "Two put the stop two points beyond the entry level. One puts it one point beyond the nearest adverse overnight, prior-day, or value-area price, when that distance is at least four points. "
        "Three keep a 15-point stop and a 1.7R target but flat at 30 minutes, 60 minutes, or 11:30. "
        "The 15-point 0.75R and 1.7R rows are the daily-book exits. A cell needs 80 validation fills to be eligible. The sort is validation mean R. "
        f"Benjamini-Hochberg at 10% covers all {len(grid)} validation tests of mean R above zero."
    )
    a("")
    a("| rule | val n | val hit | null | breakeven | val mean R | p | BH |")
    a("|---|---:|---:|---:|---:|---:|---:|---|")
    ordered = sorted(grid, key=lambda r: -(r["val"]["r"][0] if r["val"]["n"] >= 2 and not math.isnan(r["val"]["r"][0]) else -999))
    for row in ordered:
        v = row["val"]
        a(
            f"| {row['name']} | {v['n']} | {pct(v['hit']['hit'])} | {pct(row['null'])} | {pct(row['be'])} | "
            f"{_num(v['r'][0])} ({_num(v['r'][1])} to {_num(v['r'][2])}) | {v['p_r']:.3f} | {'yes' if row['bh'] else 'no'} |"
        )
    a("")
    a("## Holdout")
    a("")
    if winner is None:
        a("No exit had 80 validation fills.")
    else:
        w = winner
        h = w["hold"]
        a(
            f"The validation choice is `{w['name']}`, validation mean R {_num(w['val']['r'][0])} on {w['val']['n']} fills. "
            f"Holdout hit {pct(h['hit']['hit'])} ({pct(h['hit']['lo'])} to {pct(h['hit']['hi'])}) on {h['n']} fills. "
            f"Holdout mean R {_num(h['r'][0])} ({_num(h['r'][1])} to {_num(h['r'][2])}). "
            f"The no-drift hit rate for these distances is {pct(w['hold_null'])}. The cost breakeven is {pct(w['hold_be'])}."
        )
        ref = next((r for r in grid if r["name"] == "s15_r1.7"), None)
        if ref is not None:
            rh = ref["hold"]
            a("")
            a(
                f"The daily-book exit, 15 points and 1.7R, was not re-chosen. Its holdout hit is {pct(rh['hit']['hit'])} "
                f"({pct(rh['hit']['lo'])} to {pct(rh['hit']['hi'])}) on {rh['n']} fills, mean R {_num(rh['r'][0])} "
                f"({_num(rh['r'][1])} to {_num(rh['r'][2])})."
            )
    a("")
    a("## Lifecycle")
    a("")
    a("The selected exit is used for both the eval and the funded shot. The overnight row is a 0.75R eval and a 1.7R funded shot, 15-point stop. The daily-book row is the initial balance after 11:00 with that same 15-point stop. Later grind days use each book's own holdout hit rate. LucidFlex fee is the assumed $100.")
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


def _lead(edge, winner, lives) -> str:
    train = next((r for r in edge if r["sample"] == "train+validation" and r["horizon"] == "close"), None)
    hold = next((r for r in edge if r["sample"] == "holdout" and r["horizon"] == "close"), None)
    if train is None:
        return "The IB fallback had no excursion sample."
    above = train["lo"] > 0
    edge_bit = (
        f"On train and validation the IB fallback's MFE minus MAE beats a random entry at the same minute by "
        f"{train['diff']:.1f} points ({train['lo']:.1f} to {train['hi']:.1f})."
        if above
        else (
            f"On train and validation the IB fallback does not beat a random entry at the same minute. "
            f"The paired difference in MFE minus MAE is {train['diff']:.1f} points ({train['lo']:.1f} to {train['hi']:.1f})."
        )
    )
    if hold is not None:
        edge_bit += (
            f" The same pre-registered difference on the holdout is {hold['diff']:.1f} ({hold['lo']:.1f} to {hold['hi']:.1f})."
        )
    if winner is None:
        return edge_bit + " No exit had 80 validation fills."
    h = winner["hold"]
    clears = (not math.isnan(h["r"][1])) and h["r"][1] > 0
    exit_bit = (
        f" The validation exit is `{winner['name']}`. Holdout mean R is {_num(h['r'][0])} "
        f"({_num(h['r'][1])} to {_num(h['r'][2])}) on {h['n']} fills."
    )
    exit_bit += " That interval is above zero." if clears else " That interval is not above zero."
    sel = [r for r in lives if r["book"] == "selected"]
    base = [r for r in lives if r["book"] == "onhl"]
    if sel and base:
        exit_bit += (
            f" Topstep per eval is {money(sel[0]['life']['mean'])} against {money(base[0]['life']['mean'])} for the overnight pull."
        )
    return edge_bit + exit_bit


def _collect(days):
    fills = {name: [] for name in ENTRIES}
    real = {name: [] for name in ENTRIES}
    rnd = {name: [] for name in ENTRIES}
    same = {name: [] for name in ENTRIES}
    for day in days:
        for name in ENTRIES:
            fill = entry_on(day, name)
            fills[name].append(fill)
            if fill is None:
                real[name].append(None)
                rnd[name].append(None)
                same[name].append(None)
                continue
            real[name].append(excursion(day, fill))
            rnd[name].append(excursion(day, random_fill(day, fill, name)))
            same[name].append(excursion(day, same_side_fill(day, fill)))
    return fills, real, rnd, same


def _summary(real, idxs):
    out = {}
    for name, rows in real.items():
        mae, mfe, first = _rows_for(rows, idxs, "close")
        if len(mae) < 5:
            continue
        out[name] = {
            "n": len(mae),
            "mae": quantiles(mae),
            "mfe": quantiles(mfe),
            "first": float(np.mean(first)),
        }
    return out


def _edge_row(sample, horizon, real, rnd, same, idxs):
    mae, mfe, _first = _rows_for(real, idxs, horizon)
    rmae, rmfe, _rf = _rows_for(rnd, idxs, horizon)
    diff, lo, hi, _n = paired_edge(real, rnd, idxs, horizon)
    sdiff, slo, shi, _sn = paired_edge(real, same, idxs, horizon)
    ib = float(np.mean(mfe) - np.mean(mae)) if mae else float("nan")
    rand = float(np.mean(rmfe) - np.mean(rmae)) if rmae else float("nan")
    return {
        "sample": sample, "horizon": horizon, "ib": ib, "rnd": rand,
        "diff": diff, "lo": lo, "hi": hi, "same": sdiff, "same_lo": slo, "same_hi": shi,
    }


def _conditional(real, idxs):
    mae, mfe, _first = _rows_for(real, idxs, "close")
    mae_a = np.asarray(mae, dtype=float)
    mfe_a = np.asarray(mfe, dtype=float)
    rows = []
    n_all = len(mae_a) or 1
    for cap in MAE_CAPS:
        keep = mae_a < cap
        taken = mfe_a[keep]
        if len(taken) == 0:
            continue
        rows.append({
            "cap": cap,
            "n": int(keep.sum()),
            "share": float(keep.mean()) if n_all else float("nan"),
            "mean": float(taken.mean()),
            "p50": float(np.quantile(taken, 0.5)),
        })
    return rows, mae, mfe


def main() -> None:
    print("load", flush=True)
    df = load_bars(str(DATA))
    days = build_days(df)
    attach_va(df, days)
    attach_atr(days)
    train_i = [i for i, d in enumerate(days) if d.ts < TRAIN_END]
    val_i = [i for i, d in enumerate(days) if TRAIN_END <= d.ts < VAL_END]
    hold_i = [i for i, d in enumerate(days) if d.ts >= VAL_END]
    fit_i = train_i + val_i
    print("entries", flush=True)
    fills, real, rnd, same = _collect(days)
    summary = _summary(real, fit_i)
    edge = []
    for horizon in ("60m", "close"):
        edge.append(_edge_row("train+validation", horizon, real["ib"], rnd["ib"], same["ib"], fit_i))
    cond, ib_mae, ib_mfe = _conditional(real["ib"], fit_i)
    rmae, rmfe, _rf = _rows_for(rnd["ib"], fit_i, "close")
    save_charts(ib_mae, ib_mfe, rmae, rmfe, [r["cap"] for r in cond], [r["mean"] for r in cond])
    print("exits", flush=True)
    grid = []
    ib = fills["ib"]
    for spec in cells():
        book = simulate_cell(days, ib, spec)
        val_tr = [tr for i in val_i for tr in book[i]]
        scored = r_test(val_tr, null_of(val_tr))
        grid.append({
            "name": spec["name"], "spec": spec, "book": book,
            "val": scored, "null": null_of(val_tr), "be": be_of(val_tr), "bh": False,
        })
        print(spec["name"], scored["n"], flush=True)
    flags = bh_mask(np.array([r["val"]["p_r"] for r in grid]))
    for row, ok in zip(grid, flags, strict=True):
        row["bh"] = bool(ok)
    eligible = [r for r in grid if r["val"]["n"] >= 80 and not math.isnan(r["val"]["r"][0])]
    winner = max(eligible, key=lambda r: r["val"]["r"][0]) if eligible else None
    if winner is not None:
        print("winner", winner["name"], round(winner["val"]["r"][0], 3), flush=True)
        for row in (winner, next(r for r in grid if r["name"] == "s15_r1.7")):
            hold_tr = [tr for i in hold_i for tr in row["book"][i]]
            row["hold"] = r_test(hold_tr, null_of(hold_tr))
            row["hold_null"] = null_of(hold_tr)
            row["hold_be"] = be_of(hold_tr)
        edge.append(_edge_row("holdout", "close", real["ib"], rnd["ib"], same["ib"], hold_i))
        edge.append(_edge_row("holdout", "60m", real["ib"], rnd["ib"], same["ib"], hold_i))
    onhl75, _s = daily_run(days, None, 0, 0.75)
    onhl17, _s = daily_run(days, None, 0, 1.7)
    ib75, _s = daily_run(days, "ib", 11 * 60, 0.75)
    ib17, _s = daily_run(days, "ib", 11 * 60, 1.7)
    books = [("onhl", onhl75, onhl17), ("daily book", ib75, ib17)]
    if winner is not None:
        books.insert(0, ("selected", winner["book"], winner["book"]))
    firm_list = firms()
    lives = []
    for label, eval_book, fund_book in books:
        eh = [eval_book[i] for i in hold_i]
        fh = [fund_book[i] for i in hold_i]
        trades = [tr for day in eh for tr in day]
        grind = (sum(tr.hit for tr in trades) / len(trades)) if trades else 0.5
        for spec in firm_list:
            risk = min(2000.0, float(spec["mll"]))
            life = fullport_life(
                eh, fh, spec, np.random.default_rng(_seed("mae" + label + spec["firm"])), risk, grind, n=400,
            )
            cash, _note, _slots = month_book(eh, fh, spec, risk, grind, n=120)
            mid = float(cash.mean())
            se = float(cash.std(ddof=1) / math.sqrt(len(cash)))
            passes = month_passes(eh, spec, risk, grind, n=80)
            lives.append({
                "firm": spec["firm"], "book": label, "life": life, "passes": passes,
                "month": {"mean": mid, "lo": mid - 1.96 * se, "hi": mid + 1.96 * se, "p_neg": float(np.mean(cash < 0))},
            })
            print("life", label, spec["firm"], round(life["mean"], 1), flush=True)
    text = render(
        summary, edge, cond, grid, winner, lives,
        {"train": len(train_i), "val": len(val_i), "hold": len(hold_i)},
    )
    OUT.write_text(text)
    print("wrote", OUT, flush=True)


if __name__ == "__main__":
    main()
