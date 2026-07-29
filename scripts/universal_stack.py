#!/usr/bin/env python3
"""Confirmation-count (1/2/3) test on the UNIVERSAL both-books/all-days set (Angus 23-Jul).
Reads output/universal_orderflow.parquet (970 trades, E3+E4, every day, v2-tagged, all signals
already scored). Two views per setup, out-of-fit 2025 vs 2026:

  A) footprint confirmations = absorption + delta_div + stacked_imb, bucketed 0/1/2/3
  B) does adding footprint confirmations ON TOP OF pre-market CVD stack further?

    python -m scripts.universal_stack
"""
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def brk(d, col):
    out = []
    for k in sorted(d[col].unique()):
        s = d[d[col] == k]
        out.append((int(k), len(s), s.win.mean() * 100, s.dollars.mean(), s.dollars.sum()))
    return out


def main():
    S = pd.read_parquet("output/universal_orderflow.parquet")
    S["win"] = S.dollars > 0
    S["fp_n"] = S.absorption + S.delta_div + S.stacked_imb          # footprint confirmations 0-3
    print(f"universe {len(S)} trades  (2025 {int((S.yr==2025).sum())}, 2026 {int((S.yr==2026).sum())})")

    for setup in ["A", "B", "B2"]:
        d = S[S.pattern == setup]
        print(f"\n===== {setup}  n={len(d)}  base win {d.win.mean()*100:.0f}%  ${d.dollars.mean():+.0f}/t =====")
        print("  (A) footprint confirmations 0/1/2/3   [absorption+delta_div+stacked]")
        for yr in (2025, 2026, "ALL"):
            dy = d if yr == "ALL" else d[d.yr == yr]
            cells = "  ".join(f"{k}:n{n:3d} {w:2.0f}% ${m:+5.0f}" for k, n, w, m, _ in brk(dy, "fp_n"))
            print(f"     {str(yr):>4}: {cells}")
        print("  (B) footprint confirmations WITHIN cvd-confirmed trades")
        dc = d[d.cvd_conf == 1]
        for yr in (2025, 2026, "ALL"):
            dy = dc if yr == "ALL" else dc[dc.yr == yr]
            if len(dy) == 0:
                print(f"     {str(yr):>4}: (none)"); continue
            cells = "  ".join(f"{k}:n{n:3d} {w:2.0f}% ${m:+5.0f}" for k, n, w, m, _ in brk(dy, "fp_n"))
            print(f"     {str(yr):>4}: {cells}")

    # combined-signal count including CVD (0-4), ALL setups, out-of-fit
    S["all_n"] = S.cvd_conf + S.absorption + S.delta_div + S.stacked_imb
    print("\n===== ALL setups: total confirmations incl. CVD (0-4) =====")
    for yr in (2025, 2026, "ALL"):
        dy = S if yr == "ALL" else S[S.yr == yr]
        cells = "  ".join(f"{k}:n{n:3d} {w:2.0f}% ${m:+5.0f}" for k, n, w, m, _ in brk(dy, "all_n"))
        print(f"   {str(yr):>4}: {cells}")


if __name__ == "__main__":
    main()
