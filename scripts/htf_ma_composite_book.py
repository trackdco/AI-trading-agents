#!/usr/bin/env python3
"""ITEM 2 — the book I'd actually trade, scored on GRADUATION.

Union break (VAL + VWAP-1) PLUS the incumbent reject arm. Adding a
lower-EV population raises the daily total while diluting per-trade
quality, and P(graduate) depends on mean AND variance, so R/day cannot
settle it. Scored on the account lab's P(graduate to LucidLive within the
year) -- the objective the verified 5-payout cap imposes (FINDINGS-B2-redux
section 0b).

Compares: union-break alone | reject alone | COMPOSITE, on identical
account mechanics and the same seeded bootstrap.

    python -m scripts.htf_ma_composite_book
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.htf_ma_account_lab as AL                             # noqa: E402
from scripts.htf_ma_level_report import (PAIRS, assign, book,       # noqa: E402
                                         boot_mean)

SEED, DRAWS, YEAR = 20260807, 1500, 250


def day_r(bk: pd.DataFrame, all_days: pd.Index) -> np.ndarray:
    """Per-day summed R, zero-filled across the full calendar of fit days."""
    s = bk.groupby("sess_day").out_ship.sum()
    return s.reindex(all_days, fill_value=0.0).to_numpy()


def grad_rate(days: np.ndarray, policy: dict, draws=DRAWS) -> tuple:
    rng = np.random.default_rng(SEED)
    seqs = [rng.integers(0, len(days), YEAR) for _ in range(draws)]
    runs = [AL.run_account(days, s, policy, payout_at=6000.) for s in seqs]
    grad = float(np.mean([r["end_state"] == "graduated" for r in runs]))
    net = float(np.mean([sum(w for _, w in r["wd"]) - r["fees"] for r in runs]))
    death = float(np.mean([len(r["funded_deaths"]) > 0 for r in runs]))
    t1 = [r["first_dollar"] for r in runs if r["first_dollar"] is not None]
    return grad, net, death, (float(np.median(t1)) if t1 else np.nan)


def main() -> None:
    F = pd.read_parquet(ROOT / "output/htf_ma_census/levels_fit_v1.parquet")
    F["era"] = np.where(F.sess_day < "2026-01-01", "H2-2025", "H1-2026")
    P = pd.read_parquet(PAIRS)
    F5 = F.join(assign(F, P, 0.5))
    all_days = pd.Index(sorted(F.sess_day.unique()))
    nd = len(all_days)

    val = book(F5[F5.locus == "val"], "break")
    vm1 = book(F5[F5.locus == "vwap_m1"], "break")
    ub = pd.concat([val, vm1]).drop_duplicates(["sess_day", "t", "side"])
    rej = book(F5[F5.locus == "bbma15"], "reject")

    print("== population overlap (do the two populations collide?) ==")
    kb = set(zip(ub.sess_day, ub.t, ub.side))
    kr = set(zip(rej.sess_day, rej.t, rej.side))
    ov = len(kb & kr)
    print(f"  union-break n={len(ub)} | reject n={len(rej)} | "
          f"same (day,minute,side): {ov} "
          f"({ov/min(len(ub),len(rej))*100:.1f}% of the smaller)")
    # same-minute-any-side (a genuine simultaneous-entry collision)
    mb = set(zip(ub.sess_day, ub.t))
    mr = set(zip(rej.sess_day, rej.t))
    print(f"  same (day,minute) any side: {len(mb & mr)} — these fire "
          f"simultaneously and are the concurrency the risk spine must hold")

    comp = pd.concat([ub.assign(pop="union_break"),
                      rej.assign(pop="reject")], ignore_index=True)
    print("\n== books ==")
    print(f"{'book':14s} {'fights':>7s} {'/day':>5s} {'EV':>8s} "
          f"{'pooled 95% CI':>20s} | {'H2-2025':>18s} | {'H1-2026':>18s}")
    for name, b in (("union_break", ub), ("reject", rej), ("COMPOSITE", comp)):
        lo, hi = boot_mean(b)
        cells = {}
        for era, g in b.groupby("era"):
            l2, h2 = boot_mean(g)
            star = "!" if l2 > 0 else " "
            cells[era] = f"{g.out_ship.mean():+.3f}[{l2:+.3f},{h2:+.3f}]{star}"
        print(f"{name:14s} {len(b):7d} {len(b)/nd:5.2f} "
              f"{b.out_ship.mean():+8.3f} [{lo:+.3f},{hi:+.3f}] | "
              f"{cells.get('H2-2025','—'):>18s} | "
              f"{cells.get('H1-2026','—'):>18s}")

    print("\n== day-level shape (what the account actually experiences) ==")
    for name, b in (("union_break", ub), ("reject", rej), ("COMPOSITE", comp)):
        d = day_r(b, all_days)
        n_per = b.groupby("sess_day").size().reindex(all_days, fill_value=0)
        print(f"  {name:12s} dayR mean {d.mean():+.3f} sd {d.std():.2f} | "
              f"trades/day med {n_per.median():.0f} max {n_per.max():.0f} | "
              f"zero-days {(n_per==0).sum():3d} | "
              f"P(day>0) {(d>0).mean()*100:.0f}%")

    print("\n== P(GRADUATE) — the objective the payout cap imposes ==")
    print("  (account lab: eval -> funded -> breach -> re-eval, 250d, "
          "wd@$6k, 1,500 bootstrapped years)")
    print(f"{'book':14s} {'policy':22s} {'GRAD':>7s} {'net':>9s} "
          f"{'P(death)':>9s} {'t1st':>6s}")
    policies = (("flat 150->150", {"s_pre": 150., "s_post": 150.}),
                ("flat 150->300", {"s_pre": 150., "s_post": 300.}),
                ("cushion k=.05[150,300]", {"s_pre": 150., "mode": "cushion",
                                            "k": 0.05, "s_min": 150.,
                                            "s_max": 300.}))
    for name, b in (("union_break", ub), ("reject", rej), ("COMPOSITE", comp)):
        d = day_r(b, all_days)
        for pn, pol in policies:
            g, net, dth, t1 = grad_rate(d, pol)
            print(f"{name:14s} {pn:22s} {g*100:6.1f}% ${net:8,.0f} "
                  f"{dth*100:8.1f}% {t1:6.0f}")

    print("\n== EV-haircut robustness of the ranking (-20%, cushion policy) ==")
    pol = {"s_pre": 150., "mode": "cushion", "k": 0.05, "s_min": 150.,
           "s_max": 300.}
    for name, b in (("union_break", ub), ("reject", rej), ("COMPOSITE", comp)):
        n_per = b.groupby("sess_day").size().reindex(all_days, fill_value=0)
        d = day_r(b, all_days) - 0.2 * b.out_ship.mean() * n_per.to_numpy()
        g, net, dth, t1 = grad_rate(d, pol)
        print(f"  {name:14s} GRAD {g*100:6.1f}% | net ${net:8,.0f} | "
              f"P(death) {dth*100:.1f}%")


if __name__ == "__main__":
    main()
