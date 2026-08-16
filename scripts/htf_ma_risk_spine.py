#!/usr/bin/env python3
"""ITEM 3 — RISK SPINE for the new book (in-flight inclusive).

The composite book runs ~11 fights/day (median 11, max 24) and the current
spec says NOTHING about concurrent positions or overlapping exposure inside
an episode. The old canon needed an in-flight-inclusive budget --

    realised losses + in-flight risk + new risk <= budget

-- precisely because its worst days were four to eight OVERLAPPING losers
whose losses were not yet realised when the later entries fired. A
realised-loss-only halt cannot see that and fails exactly when it matters.

This measures the exposure the new book actually creates, then prices the
budget rule against it. Requires t_entry/t_exit (census v2).

    python -m scripts.htf_ma_risk_spine [--budget-r 5.33]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.htf_ma_account_lab as AL                             # noqa: E402
from scripts.htf_ma_level_report import PAIRS, assign, book         # noqa: E402

SEED, DRAWS, YEAR = 20260807, 1500, 250
BUDGET_R = 16.0 / 3.0            # the canon's budget = base x 16/3 (5.33R)


def load_composite() -> tuple[pd.DataFrame, pd.Index]:
    F = pd.read_parquet(ROOT / "output/htf_ma_census/levels_fit.parquet")
    F["era"] = np.where(F.sess_day < "2026-01-01", "H2-2025", "H1-2026")
    P = pd.read_parquet(PAIRS)
    F5 = F.join(assign(F, P, 0.5))
    val = book(F5[F5.locus == "val"], "break")
    vm1 = book(F5[F5.locus == "vwap_m1"], "break")
    ub = pd.concat([val, vm1]).drop_duplicates(["sess_day", "t", "side"])
    rej = book(F5[F5.locus == "bbma15"], "reject")
    comp = pd.concat([ub.assign(pop="union_break"), rej.assign(pop="reject")],
                     ignore_index=True)
    comp = comp[comp.t_entry.notna() & comp.t_exit.notna()].copy()
    comp["t_entry"] = pd.to_datetime(comp.t_entry)
    comp["t_exit"] = pd.to_datetime(comp.t_exit)
    comp["t_3r"] = pd.to_datetime(comp.t_3r)
    return comp.sort_values("t_entry"), pd.Index(sorted(F.sess_day.unique()))


def concurrency(comp: pd.DataFrame) -> pd.DataFrame:
    """How many positions are open when each new one is entered."""
    out = []
    for day, g in comp.groupby("sess_day"):
        g = g.sort_values("t_entry")
        ent = g.t_entry.to_numpy()
        exi = g.t_exit.to_numpy()
        for i in range(len(g)):
            open_now = int(((ent < ent[i]) & (exi > ent[i])).sum())
            out.append({"sess_day": day, "i": i, "open_at_entry": open_now})
    return pd.DataFrame(out)


def risk_at_risk(comp: pd.DataFrame) -> pd.DataFrame:
    """Peak simultaneous DOLLAR-RISK (in R units of `size`) per day.

    In-flight risk of an open position = full 1R until it reaches 3R (at
    which point 75% is booked and the remainder trails on house money);
    0 thereafter. Deliberately conservative — this is the number a budget
    must respect."""
    out = []
    for day, g in comp.groupby("sess_day"):
        g = g.sort_values("t_entry")
        events = []
        for r in g.itertuples():
            risk_end = r.t_3r if (pd.notna(r.t_3r) and r.t_3r < r.t_exit) \
                else r.t_exit
            events.append((r.t_entry, +1.0))
            events.append((risk_end, -1.0))
        events.sort()
        cur = peak = 0.0
        for _, d in events:
            cur += d
            peak = max(peak, cur)
        out.append({"sess_day": day, "peak_R_at_risk": peak, "n": len(g)})
    return pd.DataFrame(out)


def apply_budget(comp: pd.DataFrame, budget_r: float,
                 realised_only: bool = False) -> pd.DataFrame:
    """Sequential in-flight-inclusive budget. Returns the ACCEPTED book.

    At each candidate entry:
        spent = realised_drawdown + (in-flight risk, unless realised_only)
        accept iff spent + 1R <= budget_r
    """
    keep = []
    for day, g in comp.groupby("sess_day"):
        g = g.sort_values("t_entry")
        acc: list = []                    # accepted rows (t_entry,t_exit,r_end,pnl)
        realised = 0.0
        for r in g.itertuples():
            now = r.t_entry
            realised = sum(a["pnl"] for a in acc if a["t_exit"] <= now)
            dd = max(0.0, -realised)
            inflight = 0.0
            if not realised_only:
                inflight = sum(1.0 for a in acc
                               if a["t_entry"] <= now < a["r_end"])
            if dd + inflight + 1.0 <= budget_r:
                risk_end = r.t_3r if (pd.notna(r.t_3r) and r.t_3r < r.t_exit) \
                    else r.t_exit
                acc.append({"t_entry": r.t_entry, "t_exit": r.t_exit,
                            "r_end": risk_end, "pnl": r.out_ship,
                            "idx": r.Index})
        keep.extend(a["idx"] for a in acc)
    return comp.loc[keep]


def grad(days: np.ndarray, draws=DRAWS) -> tuple:
    pol = {"s_pre": 150., "mode": "cushion", "k": 0.05, "s_min": 150.,
           "s_max": 300.}
    rng = np.random.default_rng(SEED)
    seqs = [rng.integers(0, len(days), YEAR) for _ in range(draws)]
    runs = [AL.run_account(days, s, pol, payout_at=6000.) for s in seqs]
    return (float(np.mean([r["end_state"] == "graduated" for r in runs])),
            float(np.mean([len(r["funded_deaths"]) > 0 for r in runs])))


def day_r(bk, all_days):
    return bk.groupby("sess_day").out_ship.sum().reindex(
        all_days, fill_value=0.0).to_numpy()


def main() -> None:
    br = BUDGET_R
    if "--budget-r" in sys.argv:
        br = float(sys.argv[sys.argv.index("--budget-r") + 1])
    comp, all_days = load_composite()
    print(f"composite book: {len(comp):,} fights, {len(all_days)} days, "
          f"{len(comp)/len(all_days):.2f}/day")

    print("\n== 1. CONCURRENCY: positions already open when a new one fires ==")
    C = concurrency(comp)
    vc = C.open_at_entry.value_counts().sort_index()
    for k, v in vc.items():
        if k <= 8:
            print(f"  {k} open: {v:6d} entries ({v/len(C)*100:5.1f}%)")
    print(f"  max simultaneous at an entry: {C.open_at_entry.max()}")
    print(f"  share of entries taken with >=1 already open: "
          f"{(C.open_at_entry>=1).mean()*100:.1f}%")
    print(f"  share with >=4 already open: "
          f"{(C.open_at_entry>=4).mean()*100:.1f}%")

    print("\n== 2. PEAK SIMULTANEOUS RISK (R units of one position's size) ==")
    RR = risk_at_risk(comp)
    q = RR.peak_R_at_risk.quantile
    print(f"  per-day peak R-at-risk: p50 {q(.50):.1f} | p75 {q(.75):.1f} | "
          f"p90 {q(.90):.1f} | p95 {q(.95):.1f} | max {RR.peak_R_at_risk.max():.1f}")
    print(f"  days exceeding the canon budget of {br:.2f}R: "
          f"{(RR.peak_R_at_risk > br).sum()} of {len(RR)} "
          f"({(RR.peak_R_at_risk > br).mean()*100:.1f}%)")

    print("\n== 3. WORST-DAY COMPOSITION (the failure mode the rule exists "
          "for) ==")
    dp = comp.groupby("sess_day").out_ship.sum().sort_values()
    for day in dp.index[:5]:
        g = comp[comp.sess_day == day].sort_values("t_entry")
        losers = g[g.out_ship < 0]
        pk = RR[RR.sess_day == day].peak_R_at_risk.iloc[0]
        print(f"  {day}: dayR {dp[day]:+7.2f} | {len(g):2d} trades, "
              f"{len(losers):2d} losers | peak R-at-risk {pk:.1f} | "
              f"max overlap {concurrency(g).open_at_entry.max()+1}")

    print(f"\n== 4. THE BUDGET RULE, priced (budget = {br:.2f}R) ==")
    base_days = day_r(comp, all_days)
    g0, d0 = grad(base_days)
    print(f"{'rule':34s} {'trades':>7s} {'kept':>6s} {'dayR':>7s} "
          f"{'worst':>7s} {'p05 day':>8s} {'GRAD':>7s} {'P(death)':>9s}")
    print(f"{'no budget (current spec)':34s} {len(comp):7d} {100.0:5.1f}% "
          f"{base_days.mean():+7.3f} {base_days.min():+7.2f} "
          f"{np.percentile(base_days,5):+8.2f} {g0*100:6.1f}% {d0*100:8.1f}%")
    for tag, ro in (("realised-loss only (fails)", True),
                    ("IN-FLIGHT INCLUSIVE", False)):
        for b in ([br] if ro else [3.0, br, 8.0]):
            kb = apply_budget(comp, b, realised_only=ro)
            d = day_r(kb, all_days)
            gg, dd = grad(d)
            print(f"{tag+f' @{b:.2f}R':34s} {len(kb):7d} "
                  f"{len(kb)/len(comp)*100:5.1f}% {d.mean():+7.3f} "
                  f"{d.min():+7.2f} {np.percentile(d,5):+8.2f} "
                  f"{gg*100:6.1f}% {dd*100:8.1f}%")


if __name__ == "__main__":
    main()
