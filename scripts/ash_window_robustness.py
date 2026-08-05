#!/usr/bin/env python3
"""ROBUSTNESS ARM — ash-unicorn-sb on 09:45-10:30 instead of 09:45-10:15.

⚠️ THIS IS A SECOND LOOK AT AN ALREADY-BASELINED STRATEGY. Requested by Brake.

The question is NOT "which window is better" — with two windows tried, picking the better one is
selection, and the card's forward test is already pre-registered on the 30-minute window. The
question is: **does the edge survive outside his macro?** The informative answer is "no".

Why 10:15-10:30 is not a widening of his rule: his OWN stated macro schedule is
    AM1  09:45-10:15   |   (nothing)  10:15-10:45   |   AM2  10:45-11:15
so the extra 15 minutes fall in a gap he explicitly does not name as a macro
[qngA8aIfV0M 00:27-01:46].

Everything else is byte-identical to the committed baseline: same A1-A9 assumptions, same
order-block stop, same locked exit (2R target, break-even at 1R, no trailing, stop-first,
16:00 ET cap), same costs. ONLY the window end moves.

    python -m scripts.ash_window_robustness
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.ash_raw_baseline as base  # noqa: E402
from scripts.nya_sb01_feasibility import load_bars  # noqa: E402

COST_USD, PT = 25.0, 20.0


def run_window(bars, m0: int, m1: int, label: str) -> pd.DataFrame:
    keep = base.SESSIONS
    base.SESSIONS = {"NY": [(label, m0, m1)]}
    try:
        return base.run("NY", bars)
    finally:
        base.SESSIONS = keep


def summarise(d: pd.DataFrame, label: str) -> dict:
    if not len(d):
        return {"arm": label, "n": 0}
    eq = d.R.cumsum()
    cost = float((COST_USD / (d.risk_pts * PT)).mean())
    return {"arm": label, "n": len(d),
            "win%": 100 * (d.R >= 2).mean(), "BE%": 100 * (d.R == 0).mean(),
            "loss%": 100 * (d.R <= -1).mean(),
            "avgR": d.R.mean(), "exp": d.R.mean() - cost,
            "totR": d.R.sum(), "maxDD": float((eq.cummax() - eq).max())}


def main() -> None:
    bars = load_bars()
    a = run_window(bars, 585, 615, "AM1")        # committed baseline
    b = run_window(bars, 585, 630, "AM1x30")     # the robustness arm

    # the extension slice: trades that only exist because the window was widened
    b_mins = b.time.str.slice(0, 2).astype(int) * 60 + b.time.str.slice(3, 5).astype(int)
    ext = b[b_mins > 615]
    core = b[b_mins <= 615]

    print("ash-unicorn-sb — WINDOW ROBUSTNESS. Second look, declared as such.\n")
    print(f"instrument NQ 1-min   span {bars.day.min()} -> {bars.day.max()}")
    print("his own macro grid: AM1 09:45-10:15 | GAP 10:15-10:45 | AM2 10:45-11:15\n")

    rows = [summarise(a, "09:45-10:15  (committed baseline)"),
            summarise(b, "09:45-10:30  (robustness arm)"),
            summarise(core, "  of which, entries <=10:15"),
            summarise(ext, "  of which, entries >10:15  <- THE EXTENSION")]
    t = pd.DataFrame(rows)
    print(t.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))

    print("\n" + "=" * 74)
    print("THE EXTENSION SLICE — trades that exist ONLY because the window widened")
    print("=" * 74)
    if len(ext):
        print(ext[["date", "time", "direction", "entry", "stop", "risk_pts",
                   "R", "outcome"]].to_string(index=False))
        print(f"\n  n={len(ext)}   wins {int((ext.R>=2).sum())}  BE {int((ext.R==0).sum())}  "
              f"losses {int((ext.R<=-1).sum())}   total {ext.R.sum():+.1f}R")
    else:
        print("  none")

    # did widening change any trade that ALREADY existed in the baseline?
    m = a[["date", "time", "R"]].merge(core[["date", "time", "R"]], on="date",
                                       how="outer", suffixes=("_15", "_30"), indicator=True)
    changed = m[(m._merge == "both") & (m.R_15 != m.R_30)]
    print(f"\nbaseline trades whose OUTCOME changed under the wider window: {len(changed)}")
    if len(changed):
        print(changed.to_string(index=False))
    only15 = m[m._merge == "left_only"]; only30 = m[m._merge == "right_only"]
    print(f"  present only at 10:15 cutoff: {len(only15)}   "
          f"present only at 10:30 cutoff: {len(only30)}")

    out = ROOT / "research/ash10hazard/strategies/ash-unicorn-sb-window-robustness.csv"
    b.assign(slice=np.where(b_mins > 615, "extension", "core")).to_csv(out, index=False)
    print(f"\ntrades -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
