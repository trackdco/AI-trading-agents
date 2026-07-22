#!/usr/bin/env python3
"""CVD-conviction gate on the correctly-tagged agent-traded set (Angus 22 Jul). Uses the 327
combined trades (2025 fresh-eyes + 2026 chained) already scored with signals. Shows how the
actual traded P&L reshapes under gates, per setup, per year, OUT-OF-FIT:

  baseline    take every trade the agent took
  cvd         keep only trades where pre-market CVD agrees with direction
  b2_1of3     B2 only: keep the 1/3 bucket (exactly one of absorp/delta_div/stacked)
  combo       cvd on A/B, and on B2 keep (cvd OR 1/3)

    python -m scripts.gate_cvd
"""
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def summ(d):
    if len(d) == 0:
        return "n=0"
    return f"n={len(d):3d}  win {d.win.mean()*100:3.0f}%  ${d.dollars.mean():+6.0f}/t  tot ${d.dollars.sum():+8,.0f}"


def block(name, d):
    print(f"\n===== {name} =====")
    for yr in (2025, 2026, "ALL"):
        dy = d if yr == "ALL" else d[d.yr == yr]
        print(f"  {str(yr):>4}: {summ(dy)}")
    for setup in ["A", "B", "B2"]:
        ds = d[d.pattern == setup]
        print(f"    {setup:2s} ALL: {summ(ds)}")


def main():
    S = pd.read_parquet("output/orderflow_combined.parquet")
    S["win"] = S.dollars > 0
    print(f"loaded {len(S)} trades  (2025 {int((S.yr==2025).sum())}, 2026 {int((S.yr==2026).sum())})")

    block("BASELINE (all agent trades)", S)
    block("GATE: cvd_conf==1 (all setups)", S[S.cvd_conf == 1])

    b2 = S[S.pattern == "B2"]
    block("B2 only, 1-of-3 bucket (nsig==1)", b2[b2.nsig == 1])

    # combo: A/B require cvd; B2 requires (cvd OR exactly-one-of-3)
    ab = S[(S.pattern != "B2") & (S.cvd_conf == 1)]
    b2c = b2[(b2.cvd_conf == 1) | (b2.nsig == 1)]
    combo = pd.concat([ab, b2c])
    block("COMBO: A/B need cvd; B2 needs (cvd OR 1of3)", combo)

    # also: B2 cvd AND 1of3 vs cvd alone, to see if they're additive
    print("\n--- B2 slice interactions (out-of-fit) ---")
    for lbl, m in [("cvd only", b2.cvd_conf == 1), ("1of3 only", b2.nsig == 1),
                   ("cvd AND 1of3", (b2.cvd_conf == 1) & (b2.nsig == 1)),
                   ("cvd OR 1of3", (b2.cvd_conf == 1) | (b2.nsig == 1))]:
        d = b2[m]
        for yr in (2025, 2026, "ALL"):
            dy = d if yr == "ALL" else d[d.yr == yr]
            print(f"  B2 {lbl:14s} {str(yr):>4}: {summ(dy)}")


if __name__ == "__main__":
    main()
