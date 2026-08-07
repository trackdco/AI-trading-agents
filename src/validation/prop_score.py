#!/usr/bin/env python3
"""THE PROP SCOREBOARD — one harness, one objective, every model scored identically.

ANGUS 2026-08-05. Every number in this repo up to now is per-trade profit factor. That is
the wrong objective and it steered the whole week:

    corr(trades per day, green-day %) = +0.88
    corr(profit factor, green-day %)  = -0.46

Every filter we applied raised PF *by cutting trades*, and cutting trades lowered the
green-day rate. We optimised a number that moves inversely to the one that gets paid.

WHAT ACTUALLY GETS PAID, and why each line is here:

  net points/trade   after a 2.0-point round-trip friction. The bar comes from an external
                     falsification study on OUR instrument -- 14 intraday signal families
                     over 947 days of MNQ, gross returns 0.07 to 1.50 points per trade
                     against 2-point friction, none deployable. Its two positive controls
                     cleared at +15.77 and +5.77 net. So 4 points net is a real bar, set by
                     evidence rather than by preference.
  T-stat, N          the same study's deployment criteria: T >= 2.0, N >= 200.
  green-day %        prop payouts accrue per DAY. This is the number Angus actually trades
                     for: "id rather something that can do 50 points a day consistently
                     year on year as opposed to something that does 200 points once or
                     twice a week".
  max-day %          the consistency rule. Most firms void a payout if one day exceeds
                     ~30% of total profit, which mathematically forbids a tail-driven book.
  worst rolling 10d  streak risk. With copy-traded accounts a bad stretch is eval jail,
                     so the drawdown that matters is consecutive days, not per-trade.

EOD-TRAILING NOTE: the funded shell trails on the CLOSING balance, so intraday heat is
free. Daily aggregates -- not per-trade excursions -- are the correct unit throughout.

    from src.validation.prop_score import score_book, report
    python -m src.validation.prop_score            # score every known book
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

FRICTION_PTS = 2.0        # round-trip, the MNQ study's assumption
BAR_NET_PTS = 4.0
BAR_T = 2.0
BAR_N = 200
BAR_GREEN = 0.55
BAR_MAXDAY = 0.30


def score_book(T: pd.DataFrame, day_col="day", pts_col="pts",
               ts_col="fill_ts", all_days=None) -> dict | None:
    """Score any trade book on the prop objective. `pts_col` must be GROSS points —
    friction is charged here so every model is charged identically regardless of which
    engine or cost model produced it."""
    if T is None or len(T) == 0:
        return None
    T = T.dropna(subset=[pts_col]).copy()
    if len(T) == 0:
        return None
    net = T[pts_col].to_numpy(float) - FRICTION_PTS
    n = len(net)
    sd = net.std(ddof=1) if n > 1 else np.nan
    t = float(net.mean() / (sd / math.sqrt(n))) if sd and sd == sd and sd > 0 else 0.0

    T["_net"] = net
    d = T.groupby(day_col)["_net"].sum()
    if all_days is not None:                       # count flat days as flat, not absent
        d = d.reindex(sorted(set(all_days)), fill_value=0.0)
    d = d.sort_index()
    tot = float(d.sum())
    eq = np.concatenate([[0.0], np.cumsum(d.to_numpy(float))])
    r10 = float(d.rolling(10).sum().min()) if len(d) >= 10 else np.nan

    yr = T.assign(_y=T[day_col].astype(str).str[:4]).groupby("_y")["_net"].sum()

    return {
        "n": n, "net_pts": float(net.mean()), "t": t, "total_pts": tot,
        "days": int(len(d)), "traded_days": int((d != 0).sum()),
        "tpd": n / max(len(d), 1),
        "green": float((d > 0).mean()),
        "green_of_traded": float((d[d != 0] > 0).mean()) if (d != 0).any() else np.nan,
        "med_day": float(d.median()),
        "maxday": float(d.max() / tot) if tot > 0 else np.nan,
        "worst10d": r10,
        "maxdd": float(np.max(np.maximum.accumulate(eq) - eq)),
        "years_green": int((yr > 0).sum()), "years": int(len(yr)),
    }


def verdict(s: dict) -> tuple[bool, list[str]]:
    """The declared bar. Every clause is a separate named failure — a book that misses on
    one thing should not read the same as one that misses on five."""
    fails = []
    if s["net_pts"] < BAR_NET_PTS:
        fails.append(f"net {s['net_pts']:+.2f}pt < {BAR_NET_PTS}")
    if s["t"] < BAR_T:
        fails.append(f"T {s['t']:.2f} < {BAR_T}")
    if s["n"] < BAR_N:
        fails.append(f"N {s['n']} < {BAR_N}")
    if s["green"] < BAR_GREEN:
        fails.append(f"green {s['green']:.0%} < {BAR_GREEN:.0%}")
    if not (s["maxday"] == s["maxday"]) or s["maxday"] > BAR_MAXDAY:
        fails.append(f"maxday {s['maxday']:.0%} > {BAR_MAXDAY:.0%}")
    if s["years_green"] < s["years"]:
        fails.append(f"{s['years']-s['years_green']} of {s['years']} years red")
    return (not fails), fails


HDR = ("| book | N | /day | net pt | T | green | med day | maxday% | worst10d | verdict |\n"
       "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|")


def row(label: str, s: dict | None) -> str:
    if not s:
        return f"| {label} | — | — | — | — | — | — | — | — | no data |"
    ok, fails = verdict(s)
    return (f"| {label} | {s['n']:,} | {s['tpd']:.2f} | **{s['net_pts']:+.2f}** | "
            f"{s['t']:.2f} | {s['green']:.0%} | {s['med_day']:+.1f} | "
            f"{s['maxday']:.0%} | {s['worst10d']:+.0f} | "
            + ("**PASS**" if ok else fails[0] + (f" (+{len(fails)-1})" if len(fails) > 1 else ""))
            + " |")


def main() -> int:
    books = [
        ("NY canon (live)", "output/canon_book.parquet", "pts"),
        ("London old book", "output/london_canon_book.parquet", "pts"),
        # both canon books store dollars/entry/exit rather than points; derived below
        ("LDN-CAN E3 limit", "output/l2_outcomes_london_fit.parquet", "pts"),
        ("LDN-CAN EC market-disp", "output/l2_outcomes_london_fit_EC.parquet", "pts"),
        ("LDN-CAN E4 market-all", "output/l2_outcomes_london_fit_E4.parquet", "pts"),
    ]
    L = ["# THE PROP SCOREBOARD — every book on one objective", "",
         f"Bar: **net ≥ {BAR_NET_PTS:.0f} pt/trade** after {FRICTION_PTS:.0f}pt round-trip "
         f"friction, **T ≥ {BAR_T:.0f}**, **N ≥ {BAR_N}**, "
         f"**green days ≥ {BAR_GREEN:.0%}**, **max day ≤ {BAR_MAXDAY:.0%}** of profit, "
         "every year green.", "",
         "Points are GROSS from each engine and friction is charged here, so all books are",
         "charged identically. Days with no trade count as flat, not absent.", "", HDR]
    for label, path, pcol in books:
        p = ROOT / path
        if not p.exists():
            L.append(row(label, None))
            continue
        T = pd.read_parquet(p)
        if "status" in T.columns:
            T = T[T["status"] == "outcome"]
        # CANON BOOKS CARRY EVERY SIGNAL, INCLUDING SIZE-0 ONES THE LADDER DECLINED.
        # Scoring those as trades reports a live, profitable book as a loser — caught on
        # the first run when the NY canon came back at -3.52pt/trade. Only sized rows trade.
        if "size" in T.columns:
            T = T[T["size"] > 0]
        if pcol not in T.columns and {"entry", "exit_price", "direction"} <= set(T.columns):
            # canon books carry prices, not points. Derive GROSS points signed by side so
            # the friction charge below is applied on the same footing as every other book.
            sgn = (T["direction"].astype(str).str.lower() == "long").map({True: 1.0, False: -1.0})
            T = T.assign(pts=(T["exit_price"] - T["entry"]) * sgn)
        if pcol not in T.columns or "day" not in T.columns:
            L.append(row(label + " (schema)", None))
            continue
        L.append(row(label, score_book(T, pts_col=pcol)))
        if "vs_first" in T.columns:
            L.append(row(label + " · deduped", score_book(T[T.vs_first], pts_col=pcol)))
    text = "\n".join(L)
    print(text)
    (ROOT / "output/prop_scoreboard.md").write_text(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
