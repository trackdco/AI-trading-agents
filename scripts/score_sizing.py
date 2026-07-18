#!/usr/bin/env python3
"""SIZING SCOREBOARD (Angus, 18 Jul): grade the gate's sizing in DOLLARS, not wins.

The engine's edge is magnitude-skewed (top 10% of trading days = 35% of all oracle
P&L; median green day $370 vs biggest $4,480), so win/loss counting is the wrong
currency for judging caution. This scoreboard presents the bill Angus asked about:
what the gate's shrinkage cost on eventual winner days vs saved on eventual loser
days, and whether the sizing discriminates at all (avg size on winners vs losers —
if those match, the "insurance" is a flat tax).

Run per agent version alongside score_regime_reads; log both in the ledger.

    python -m scripts.score_sizing [--month 2026-06]   # omit --month for all
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", default=None)
    ap.add_argument("--verdicts", default="output/regime_verdicts.csv")
    ap.add_argument("--daily", default="output/l2_analog_routing.csv")
    a = ap.parse_args()
    v = pd.read_csv(a.verdicts)
    r = pd.read_csv(a.daily)
    if "pl_static" not in r.columns:
        raise SystemExit("daily file needs pl_static (champion day P&L)")
    r = r.set_index("day")
    rows = []
    for _, x in v.iterrows():
        d = x.date
        if d not in r.index or (a.month and not d.startswith(a.month)):
            continue
        p = r.loc[d, "pl_static"]
        s = 0.0 if (x.stand_down or x.size_multiplier == 0) else float(x.size_multiplier)
        rows.append(dict(day=d, m=d[:7], p=p, s=s, effect=(s - 1) * p))
    S = pd.DataFrame(rows)
    if S.empty:
        raise SystemExit("no verdict days matched")
    win, lose = S[S.p > 0], S[S.p < 0]
    print(f"sizing scoreboard over {len(S)} verdict days"
          + (f" ({a.month})" if a.month else " (all months)"))
    print(f"  cost on winner days:  ${win.effect.sum():+,.0f} "
          f"(champion made ${win.p.sum():+,.0f}; avg size {win.s.mean():.2f})")
    print(f"  saved on loser days:  ${lose.effect.sum():+,.0f} "
          f"(champion lost ${lose.p.sum():+,.0f}; avg size {lose.s.mean():.2f})")
    print(f"  NET sizing effect:    ${S.effect.sum():+,.0f}")
    disc = win.s.mean() - lose.s.mean()
    print(f"  discrimination (avg size winners - losers): {disc:+.2f} "
          f"{'— sizing is a flat tax, not insurance' if abs(disc) < 0.10 else ''}")
    print()
    print(S.groupby("m").apply(lambda x: pd.Series({
        "cost_on_winners": x[x.p > 0].effect.sum(),
        "saved_on_losers": x[x.p < 0].effect.sum(),
        "net": x.effect.sum(),
        "size_w": x[x.p > 0].s.mean(), "size_l": x[x.p < 0].s.mean()}),
        include_groups=False).round(2).to_string())


if __name__ == "__main__":
    main()
