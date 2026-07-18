#!/usr/bin/env python3
"""E2 (Pat's v0.4 addendum): a STABLE shock-bar ruler, precomputed per day.

Pat's briefing metric (src/desk/regime_agent.py) thresholds at
max(40, 6 x trailing-median 1m range), so `threshold_pts` drifts day-to-day
(observed 40.5 -> 78) and `count` is incomparable across days — the agents flagged
it in nearly every May playbook note. This table gives the two stable companions
E2 asks for, per session day, strictly pre-open (bars up to 08:00 ET only):

  shock50_5s     count of 1m bars with range >= 50pts across the trailing 5
                 session blocks (a block = 08:00 -> next 08:00, so today's
                 overnight is included — it is pre-open information)
  shock50_pctl20 percentile of that count vs the prior 20 session days

Standalone artifact — Pat's briefing joins it by day whenever he opts in; nothing
in the live desk pipeline changes until then.

    python -m scripts.build_shock_ruler   -> output/shock_ruler.csv
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

FIXED_PTS = 50.0
BLOCKS = 5
PCTL_WIN = 20


def main():
    data = Path("data/reference/nq_1m_master.parquet")
    if not data.exists():
        data = Path("data/reference/nq_1m_feb_jul2026.parquet")
    df = pd.read_parquet(data)
    rng = (df.high - df.low)
    # block date: bars after 08:00 roll into the NEXT day's pre-open block
    block = (df.ts_event + pd.Timedelta(hours=16)).dt.normalize()
    shocks = pd.Series((rng >= FIXED_PTS).to_numpy(), index=block).groupby(level=0).sum()
    shocks.index = shocks.index.strftime("%Y-%m-%d")

    days = pd.read_csv("output/regime_vector.csv").day.tolist()
    all_blocks = list(shocks.index)
    rows = []
    for d in days:
        recent = [b for b in all_blocks if b <= d][-BLOCKS:]
        rows.append(dict(day=d, shock50_5s=int(shocks.loc[recent].sum())))
    out = pd.DataFrame(rows)
    out["shock50_pctl20"] = (
        out.shock50_5s.rolling(PCTL_WIN + 1, min_periods=6)
        .apply(lambda w: (w.iloc[:-1] < w.iloc[-1]).mean()).round(2))
    out.to_csv("output/shock_ruler.csv", index=False)
    print(f"wrote output/shock_ruler.csv ({len(out)} days)")
    out["m"] = out.day.str[:7]
    q = out.groupby("m").shock50_5s.agg(["mean", "max"]).round(1)
    print(q[q.index >= "2026-01"].to_string())


if __name__ == "__main__":
    main()
