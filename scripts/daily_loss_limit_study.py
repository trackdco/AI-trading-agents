#!/usr/bin/env python3
"""What would a DAILY LOSS HALT have cost (or saved) on the canon book?

Angus's question, 2026-07-26: the +$56k canon was built with no daily loss limit; the
Tier-1 spine has one (`daily_loss_halt`, default -$800 account-wide). Does adding it
degrade performance?

This answers it two ways:

  1. DETERMINISTIC REPLAY — walk the real 2025-06 -> 2026-07 book in fill order, both
     books combined, and skip every trade taken after the day's realized P&L has already
     breached the limit. Nothing is re-simulated: the same trades, the same fills, just
     truncated days. Reports total, months green, worst day, worst month.
  2. MONTE CARLO — resample whole days (the same day-block bootstrap as
     scripts/mc_dollar_risk.py) to get bust% / median funded year at each limit, because
     the historical path is one draw and survival lives in the tail, not the median.

    python -m scripts.daily_loss_limit_study
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DD = 2000.0
NSIM = 20000
SEED = 20260726
NDAYS = 252

LIMITS = [None, -1600, -1200, -1000, -800, -600, -500, -400, -300]


def load() -> pd.DataFrame:
    """The frozen canon: output/baseline_book.parquet — 400 trades, +$56,065.18, both
    books, sized at the dollar-risk FLOOR schedule (path-independent, reproducible)."""
    d = pd.read_parquet("output/baseline_book.parquet")
    return pd.DataFrame({
        "day": d["day"].astype(str),
        "fill": pd.to_datetime(d["fill"], utc=True),
        "book": d["session"],
        "pl": d["pl"].astype(float),
        "conv": d["conviction"].astype(float),
        "risk": d["risk_pts"].astype(float),
        # R multiple of the realized outcome — sizing-independent
        "Rm": (d["dollars_1lot"] / (d["risk_pts"] * 20.0)).astype(float),
    }).sort_values("fill").reset_index(drop=True)


# ---------------------------------------------------------------- 1. replay

def replay(b: pd.DataFrame, limit, mode="dollar", want_days=False):
    """Walk days in fill order; stop taking trades once the halt condition is met.

    mode 'dollar'  : halt when realized day P&L <= limit
    mode 'R'       : halt when realized day R <= limit  (R measured at the trade's own risk)
    mode 'losers'  : halt after `limit` losing trades in the day
    """
    kept, day_pl, halted_days, skipped = [], {}, 0, 0
    for day, g in b.groupby("day", sort=True):
        acc, accR, losers, stop = 0.0, 0.0, 0, False
        for row in g.itertuples():
            if stop:
                skipped += 1
                continue
            kept.append(row.Index)
            acc += row.pl
            accR += row.Rm * row.conv  # conviction-weighted R, matches dollar sizing
            if row.pl < 0:
                losers += 1
            if limit is not None:
                if mode == "dollar" and acc <= limit:
                    stop = True
                elif mode == "R" and accR <= limit:
                    stop = True
                elif mode == "losers" and losers >= limit:
                    stop = True
        if stop:
            halted_days += 1
        day_pl[day] = acc
    k = b.loc[kept]
    d = pd.Series(day_pl)
    d.index = pd.to_datetime(d.index)
    mo = d.groupby(d.index.to_period("M")).sum()
    return dict(
        days=d if want_days else None,
        total=k.pl.sum(), trades=len(k), skipped=skipped, halted_days=halted_days,
        worst_day=d.min(), worst_mo=mo.min(), months_green=int((mo > 0).sum()),
        months=len(mo), max_dd=float((d.cumsum().cummax() - d.cumsum()).max()),
    )


# ---------------------------------------------------------------- 2. monte carlo

def base_dollar(ad):
    return 200.0 + 75.0 * max(0, int((ad - 3000) // 1000)) if ad > 3000 else 200.0


def micros(conv, risk, ad):
    return min(40, int(round(min(2.0, conv) * base_dollar(ad) / (risk * 2.0))))


def sim_year(rng, days, limit, dd_buffer=250.0):
    bal, line = 0.0, -DD
    for _ in range(NDAYS):
        day = days[rng.integers(len(days))]
        avail = bal - line
        dpl = 0.0
        for conv, risk, Rm in day:
            if (bal - line) + dpl <= dd_buffer:
                break
            if limit is not None and dpl <= limit:
                break
            dpl += micros(conv, risk, avail) * (Rm * risk * 20.0) / 10.0
            if bal + dpl <= line:
                return bal + dpl, True
        bal += dpl
        line = min(0.0, max(line, bal - DD))
    return bal, False


def mc(b: pd.DataFrame, limit):
    days = [g[["conv", "risk", "Rm"]].values for _, g in b.groupby("day")]
    rng = np.random.default_rng(SEED)
    finals = np.empty(NSIM)
    busts = 0
    for i in range(NSIM):
        f, bust = sim_year(rng, days, limit)
        finals[i] = f
        busts += bust
    return dict(bust=busts / NSIM * 100, median=np.median(finals),
                p10=np.percentile(finals, 10), p90=np.percentile(finals, 90))


def day_profile(b: pd.DataFrame) -> None:
    """How often does the canon's realized day P&L even reach the candidate limits?
    A halt that never trips is free; one that trips often is a strategy change."""
    d = b.groupby("day").pl.sum()
    # running intraday minimum — what a halt actually watches
    lo = b.groupby("day").pl.apply(lambda s: s.cumsum().min())
    print(f"  {len(d)} trading days. Final day P&L: median ${d.median():+,.0f}, "
          f"worst ${d.min():+,.0f}, {int((d > 0).sum())} green.")
    print(f"  {'threshold':>10} {'days touching (intraday)':>26} {'days closing below':>20}")
    for t in (-300, -400, -500, -600, -800, -1000, -1200):
        print(f"  ${t:>9} {int((lo <= t).sum()):>16} ({(lo<=t).mean()*100:4.1f}%)"
              f"{int((d <= t).sum()):>13} ({(d<=t).mean()*100:4.1f}%)")


def row(label, r, base):
    print(f"{label:>10} ${r['total']:>10,.0f} {r['total']-base:>+9,.0f} "
          f"{r['trades']:>7} {r['skipped']:>5} {r['halted_days']:>7} "
          f"{r['months_green']:>3}/{r['months']:<4} ${r['worst_mo']:>8,.0f} "
          f"${r['worst_day']:>9,.0f} ${r['max_dd']:>8,.0f}")


def main() -> None:
    b = load()
    print(f"CANON: {len(b)} trades, {b.day.nunique()} days, "
          f"{b.day.min()} -> {b.day.max()}, total ${b.pl.sum():+,.2f}")
    print("(output/baseline_book.parquet — floor sizing, 1.0 conviction = $200 risk,\n"
          " so 1R = $200 and the engine's -2R day halt == a -$400 dollar halt)\n")

    print("0. DAY-LOSS PROFILE — how often each limit would even fire")
    day_profile(b)

    print("\n1. DETERMINISTIC REPLAY — account-wide dollar daily-loss halt, both books")
    hdr = (f"{'limit':>10} {'total':>11} {'vs canon':>9} {'trades':>7} {'skip':>5} "
           f"{'halt-d':>7} {'mo grn':>8} {'worst mo':>9} {'worst day':>10} {'maxDD':>9}")
    print(hdr)
    base = replay(b, None)["total"]
    for lim in LIMITS:
        row("none" if lim is None else f"${lim}", replay(b, lim), base)

    print("\n   loser-count variants (the other shape of the same rule):")
    for v in (2, 3, 4):
        row(f"{v} losers", replay(b, v, mode="losers"), base)

    print("\n   month-by-month, canon vs the two live candidates:")
    mos = {}
    for lab, lim in (("canon", None), ("-$800", -800), ("-$400", -400)):
        d = b.copy()
        kept = replay(b, lim, want_days=True)["days"]
        mos[lab] = kept
    m = pd.DataFrame(mos)
    m.index = pd.to_datetime(m.index)
    m = m.groupby(m.index.to_period("M")).sum()
    m["d800"] = m["-$800"] - m["canon"]
    m["d400"] = m["-$400"] - m["canon"]
    print(m.to_string(float_format=lambda x: f"{x:+,.0f}"))

    print(f"\n2. MONTE CARLO — funded year, {NSIM:,} sims, DD-scaled live sizing, "
          f"dd_halt $250 always on")
    print(f"{'limit':>10} {'bust%':>8} {'median':>12} {'p10':>12} {'p90':>12}")
    for lim in LIMITS:
        mm = mc(b, lim)
        print(f"{('none' if lim is None else f'${lim}'):>10} {mm['bust']:>7.2f}% "
              f"${mm['median']:>11,.0f} ${mm['p10']:>11,.0f} ${mm['p90']:>11,.0f}")


if __name__ == "__main__":
    main()
