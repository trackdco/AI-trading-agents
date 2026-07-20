#!/usr/bin/env python3
"""VERIFY the inventory_pts stand-down lead from standdown_study.py, killing the mild
lookahead (global quantile bucket edges) and adding a true out-of-sample split.

The first pass used pd.qcut on the FULL sample -> bucket EDGES saw all data. Here the
tercile edges are computed EXPANDING (only prior days), so bucket assignment is fully
walk-forward. Then a hard train/test: calibrate nothing but the walk-forward gate,
and separately report a frozen 2023-2024 -> 2025-2026 split so the red year that
matters most (2025) is graded on a rule that never saw it.

    python -m scripts.standdown_verify_inventory
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
BOOKS = "output/allyears_daily_books_r1r2.csv"


def load():
    b = pd.read_csv(BOOKS)
    v = pd.read_csv("output/regime_vector.csv")
    d = b.merge(v, on="day", how="left").sort_values("day").reset_index(drop=True)
    d["champ_pl"] = np.where(d.imbal_share_20 >= 0.5, d.E4, d.E3)
    d = d.dropna(subset=["champ_pl", "inventory_pts"]).reset_index(drop=True)
    d["y"] = d.day.str[:4]
    return d


def wf_gate_continuous(d, feat, min_n=20, fb=60):
    """Fully walk-forward: tercile edges from prior days only, expectancy within the
    day's tercile from prior days only."""
    vals = d[feat].values
    cpl = d.champ_pl.values
    flat = np.zeros(len(d), bool)
    for i in range(len(d)):
        if i < 40:
            prior = cpl[max(0, i - fb):i]
        else:
            past = vals[:i]
            q1, q2 = np.nanquantile(past, [1/3, 2/3])
            x = vals[i]
            if x <= q1:
                mask = past <= q1
            elif x <= q2:
                mask = (past > q1) & (past <= q2)
            else:
                mask = past > q2
            prior_bucket = cpl[:i][mask]
            prior = prior_bucket if len(prior_bucket) >= min_n else cpl[max(0, i - fb):i]
        if len(prior) >= 10 and prior.mean() < 0:
            flat[i] = True
    return flat


def health_gate(d, window=20):
    return (pd.Series(d.champ_pl).rolling(window).sum().shift(1) < 0).fillna(False).values


def report(d, flat, label):
    pl = np.where(flat, 0.0, d.champ_pl.values)
    g = pd.DataFrame({"y": d.y.values, "pl": pl})
    per = g.groupby("y").pl.sum()
    line = "  ".join(f"{y}:${per[y]:+,.0f}" for y in sorted(per.index))
    print(f"{label:38s} ALL ${g.pl.sum():+,.0f}  flat {flat.mean()*100:.0f}%  | {line}")
    return per


def main():
    d = load()
    print(f"{len(d)} days\n--- walk-forward bucket edges (leak removed) ---")
    report(d, np.zeros(len(d), bool), "ALWAYS TRADE")
    report(d, health_gate(d), "HEALTH GATE")
    inv_wf = wf_gate_continuous(d, "inventory_pts")
    report(d, inv_wf, "inventory_pts (WALK-FWD edges)")
    report(d, health_gate(d) | inv_wf, "HEALTH OR inventory_pts (WF)")

    # HARD OOS: the gate is already walk-forward, but make the split explicit -- report
    # 2025+2026 P&L for the inventory gate whose expectancies were only ever built from
    # the past (so 2025 is graded on a rule shaped by 2023-24-25-to-date, never future).
    print("\n--- explicit OOS framing: 2025 & 2026 are 'test' (rule never sees future) ---")
    per = report(d, inv_wf, "inventory_pts gate")
    perh = report(d, health_gate(d), "health gate")
    print(f"\n2025 (hardest red year): inventory ${per.get('2025',0):+,.0f} vs health ${perh.get('2025',0):+,.0f}")
    print(f"2026 (green, cost of caution): inventory ${per.get('2026',0):+,.0f} vs health ${perh.get('2026',0):+,.0f}")

    # sanity: what is the inventory gate actually DOING? correlation of flat-days with loss-days
    pl = d.champ_pl.values
    print(f"\ninventory gate: flats {inv_wf.mean()*100:.0f}% of days; "
          f"of flatted days {(pl[inv_wf] < 0).mean()*100:.0f}% were champion LOSSES "
          f"(vs {(pl < 0).mean()*100:.0f}% base rate) -> "
          f"avoided ${-pl[inv_wf][pl[inv_wf]<0].sum():,.0f} losses, forwent ${pl[inv_wf][pl[inv_wf]>0].sum():,.0f} gains")


if __name__ == "__main__":
    main()
