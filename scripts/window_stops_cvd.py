#!/usr/bin/env python3
"""Session-specific stop rules (golden 30-50, pre-market <=15) + optional CVD gate per window.
Does CVD recover the win rate Angus flagged ("losing trades we shouldn't")? Reports P&L,
win, months-green for base and CVD variants. CVD uses the validated NEGATED sign.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.champion_journal_cvd import conviction, load_cvd_delta  # noqa: E402

NY = "America/New_York"
MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]


def main():
    J = pd.read_csv("output/window_expanded.csv")
    delta = load_cvd_delta()
    J["cvd"] = [-conviction(delta, r.fill_ts, r.direction) for r in J.itertuples()]
    V = pd.read_csv("output/regime_vector.csv")[["day", "open_vs_value"]].rename(columns={"day": "date"})
    J = J.merge(V, left_on="day", right_on="date", how="left")
    # session-specific STOP rules
    gold = (J.window == "golden") & (J.risk_pts >= 30) & (J.risk_pts <= 50)
    pre = (J.window == "pre") & (J.risk_pts <= 15)
    base = J[gold | pre].copy()

    def show(s, label):
        mg = s.groupby("month").dollars.sum()
        g = (mg > 0).sum()
        worst = mg.min() if len(mg) else 0
        print(f"{label:38s} {len(s):3d}t  ${s.dollars.sum():+8,.0f}  win {s.win.mean()*100 if len(s) else 0:2.0f}%  "
              f"green {g}/{len(mg)}  worst mo ${worst:+,.0f}")

    print("### SESSION-SPECIFIC STOPS (golden 30-50, pre <=15) + CVD variants ###\n")
    show(base, "base (stops only, no CVD)")
    show(base[base.cvd <= 0], "+ CVD absorption BOTH windows")
    show(base[(base.window == "pre") | (base.cvd <= 0)], "+ CVD on GOLDEN only")
    show(base[(base.window == "golden") | (base.cvd <= 0)], "+ CVD on PRE only")
    show(base[(base.open_vs_value != "below_value") & (base.cvd <= 0)], "+ full gate (below-val + CVD) both")
    print("\n=== per-month: base (stops only) ===")
    for m in MONTHS:
        x = base[base.month == m]
        if len(x):
            print(f"  {m}  {len(x):2d}t  ${x.dollars.sum():+7,.0f}  win {x.win.mean()*100:2.0f}%  {'GRN' if x.dollars.sum()>0 else 'red'}")
    print("\n=== per-month: + CVD on GOLDEN only (keeps pre-market intact) ===")
    best = base[(base.window == "pre") | (base.cvd <= 0)]
    for m in MONTHS:
        x = best[best.month == m]
        if len(x):
            print(f"  {m}  {len(x):2d}t  ${x.dollars.sum():+7,.0f}  win {x.win.mean()*100:2.0f}%  {'GRN' if x.dollars.sum()>0 else 'red'}")


if __name__ == "__main__":
    main()
