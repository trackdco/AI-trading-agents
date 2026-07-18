#!/usr/bin/env python3
"""Regime-read scorecard (pass 33, Angus priority: 'the most important thing is making
sure the regime reads are correct'). Grades every agent verdict against the realized day:
oracle action = FLAT if both books red, else the better book. Prints accuracy, the
confusion matrix, each miss, and read-quality capture (full-size follow-the-calls P&L vs
stand-down-oracle P&L). Run per agent version; log both numbers in the ledger.

    python -m scripts.score_regime_reads [--month 2026-03]
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", default="2026-03")
    ap.add_argument("--verdicts", default="output/regime_verdicts.csv")
    ap.add_argument("--daily", default="output/l2_analog_routing.csv",
                    help="per-day pl_e3/pl_e4 source (2026); use allyears_daily_books.csv "
                         "(E3/E4 cols) for 2023-25")
    a = ap.parse_args()
    v = pd.read_csv(a.verdicts)
    r = pd.read_csv(a.daily)
    if "pl_e3" not in r.columns:                       # allyears file naming
        r = r.rename(columns={"E3": "pl_e3", "E4": "pl_e4"})
    r = r[r.day.str.startswith(a.month)].set_index("day")
    rows = []
    for _, x in v.iterrows():
        d = x.date
        if d not in r.index:
            continue
        e3, e4 = r.loc[d, "pl_e3"], r.loc[d, "pl_e4"]
        oracle = "FLAT" if max(e3, e4) < 0 else ("ROTATION" if e3 >= e4 else "MOMENTUM")
        if x.stand_down or x.size_multiplier == 0:
            agent = "FLAT"
        elif x.regime in ("balance", "trap"):
            agent = "ROTATION"
        elif x.regime == "war":
            agent = "MOMENTUM"
        else:
            agent = "FLAT"
        rows.append(dict(day=d, agent_regime=x.regime, agent=agent, oracle=oracle,
                         e3=e3, e4=e4, hit=agent == oracle))
    S = pd.DataFrame(rows)
    print(f"{a.month} regime reads: {S.hit.sum()}/{len(S)} = {S.hit.mean() * 100:.0f}% "
          f"(3-way random ≈ 33%)")
    print(pd.crosstab(S.agent, S.oracle).to_string())
    for _, x in S[~S.hit].iterrows():
        print(f"  MISS {x.day}: agent={x.agent} ({x.agent_regime}) oracle={x.oracle} "
              f"E3 {x.e3:+,.0f} E4 {x.e4:+,.0f}")
    S["agent_pl"] = S.apply(lambda x: 0 if x.agent == "FLAT"
                            else (x.e3 if x.agent == "ROTATION" else x.e4), axis=1)
    S["oracle_pl"] = S.apply(lambda x: max(x.e3, x.e4, 0), axis=1)
    cap = S.agent_pl.sum() / S.oracle_pl.sum() * 100 if S.oracle_pl.sum() else 0
    print(f"read-quality capture: ${S.agent_pl.sum():+,.0f} / ${S.oracle_pl.sum():+,.0f} = {cap:.0f}%")


if __name__ == "__main__":
    main()
