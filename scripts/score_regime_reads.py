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
        # ANGUS RULING (18 Jul): a day where the best book made $0 taking no trades
        # counts as FLAT — sitting out a day where trading earned nothing is not a miss.
        oracle = "FLAT" if max(e3, e4) <= 0 else ("ROTATION" if e3 >= e4 else "MOMENTUM")
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
    # E4 (Pat): FLAT as a first-class binary prediction target — the oracle is flat
    # 47-50% of days, so trade/no-trade discrimination is scored on its own.
    ag_t, or_t = S.agent != "FLAT", S.oracle != "FLAT"
    print(f"binary trade/no-trade: {(ag_t == or_t).sum()}/{len(S)} = "
          f"{(ag_t == or_t).mean() * 100:.0f}% (2-way random ≈ 50%)")
    for name, pred, act in [("TRADE", ag_t, or_t), ("FLAT", ~ag_t, ~or_t)]:
        tp = (pred & act).sum()
        prec = tp / pred.sum() * 100 if pred.sum() else float("nan")
        rec = tp / act.sum() * 100 if act.sum() else float("nan")
        print(f"  {name}: precision {prec:.0f}% ({tp}/{pred.sum()})  "
              f"recall {rec:.0f}% ({tp}/{act.sum()})")
    over = ((~ag_t) & or_t)          # sat out a tradeable day
    under = (ag_t & (~or_t))         # traded a day the oracle sat out
    S["agent_pl"] = S.apply(lambda x: 0 if x.agent == "FLAT"
                            else (x.e3 if x.agent == "ROTATION" else x.e4), axis=1)
    S["oracle_pl"] = S.apply(lambda x: max(x.e3, x.e4, 0), axis=1)
    print(f"  over-FLAT cost (sat out tradeable days): "
          f"${S.loc[over, 'oracle_pl'].sum():+,.0f} across {over.sum()} days")
    print(f"  under-FLAT cost (traded no-trade days):  "
          f"${S.loc[under, 'agent_pl'].sum():+,.0f} across {under.sum()} days")
    cap = S.agent_pl.sum() / S.oracle_pl.sum() * 100 if S.oracle_pl.sum() else 0
    print(f"read-quality capture: ${S.agent_pl.sum():+,.0f} / ${S.oracle_pl.sum():+,.0f} = {cap:.0f}%")


if __name__ == "__main__":
    main()
