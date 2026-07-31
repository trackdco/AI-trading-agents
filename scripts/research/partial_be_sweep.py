#!/usr/bin/env python3
"""RESEARCH ONLY (claude/agent-exit-london-r1). Bar-walk sweep: partial take-profit at
+kR, remainder immediately to BE, ridden uncapped to day-end. Answers "what's the best
profit margin for the partial leg" as a directional ranking — NOT an engine-confirmed
result (no mgmt_variant for this combo exists in src/backtest/engine.py, and this
branch may not add one).

METHOD: same bar-walk convention as scripts/london_exit_lab.py (reused, not
reimplemented): fill bar excluded; same-bar stop-vs-partial resolves AGAINST the rule
(stop wins); BE requires the partial-triggering bar to close before it can protect;
unresolved trades flatten at 15:55 ET. Entry stack frozen (rev-3 book, same as the exit
lab and the mgmt tournament).

DECLARED GRID (before running):
  partial_pct = 50% (fixed — matches V8's shipped convention)
  partial_r   in {0.5, 0.75, 1.0, 1.25, 1.5, 2.0}  <- the swept variable
  remainder: BE, no cap, day-end (15:55 ET) flatten if unresolved

FIT ONLY. Sealed untouched.

    python -m scripts.research.partial_be_sweep
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.london_combined_job import maxdd  # noqa: E402
from scripts.london_holdout_report import build_book, load_pop  # noqa: E402
from scripts.research.v9_tournament import swap_arm  # noqa: E402
from src.research.holdout_guard import assert_path_fit_only  # noqa: E402

NQ_PT = 20.0
ET = "America/New_York"
GRID = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
PARTIAL_PCT = 0.50

MASTER = "data/reference/nq_1m_master.parquet"


def load_bars() -> pd.DataFrame:
    assert_path_fit_only(MASTER)  # path-only check; content is the shared 2023-2026
                                   # master file — filtered to fit trade dates below
                                   # via the trade-level walk range, never read whole
    bars = pd.read_parquet(ROOT / MASTER)
    bars["ts_event"] = pd.to_datetime(bars.ts_event, utc=True)
    return bars.set_index("ts_event").sort_index()


def day_end(day: str) -> pd.Timestamp:
    return pd.Timestamp(f"{day} 15:55", tz=ET).tz_convert("UTC")


def walk_partial_be(bars: pd.DataFrame, trade, partial_r: float,
                     partial_pct: float = PARTIAL_PCT) -> float:
    """Realized R (blended across the two legs) under: partial_pct booked at
    +partial_r, remainder to BE same-event, ridden uncapped to day-end. Returns 0.0
    for a trade with no post-fill bars (matches london_exit_lab.walk's convention)."""
    f = pd.to_datetime(trade.fill_ts, utc=True)
    w = bars.loc[f:day_end(trade.day)]
    w = w.iloc[1:]                                 # fill bar excluded
    if not len(w):
        return 0.0
    e, sp = trade.entry, trade.risk / NQ_PT
    sgn = 1.0 if trade.direction == "long" else -1.0
    stop = e - sgn * sp
    partial_lvl = e + sgn * partial_r * sp
    partial_done = False
    hi, lo = w.high.values, w.low.values
    for i in range(len(w)):
        adverse = lo[i] <= stop if sgn > 0 else hi[i] >= stop
        if adverse:
            if not partial_done:
                return -1.0
            # remainder already at BE -> stops out flat; partial leg banked already
            return partial_pct * partial_r
        hits_partial = (hi[i] >= partial_lvl) if sgn > 0 else (lo[i] <= partial_lvl)
        if not partial_done and hits_partial:
            partial_done = True
            stop = e                               # remainder -> BE, same event
    if not partial_done:
        last = w.close.values[-1]
        return sgn * (last - e) / sp               # never reached partial: flat mark
    last = w.close.values[-1]
    remainder_r = sgn * (last - e) / sp
    return partial_pct * partial_r + (1 - partial_pct) * remainder_r


def main() -> None:
    bars = load_bars()
    # rev-3 population, V1's own book (130 trades) -- the primary reference point for
    # this idea (partial+BE is framed as an enhancement on V1's BE@1R), NOT
    # london_veto_scan.build_book() (a stale 09:30-cut/110-trade population that
    # predates the window's revision to 09:45 -- confirmed via git log, corrected here
    # after an initial run wrongly used it).
    P = load_pop("fit")
    P = swap_arm(P, "output/l2_outcomes_london_fit_v1.parquet")
    b, _ = build_book(P, "rev3")
    b = b.reset_index(drop=True)

    print(f"Partial+BE bar-walk sweep ({len(b)} trades, rev-3 V1 population, "
          f"partial_pct={PARTIAL_PCT:.0%})")
    print(f"{'partial_r':>10} {'net':>12} {'WR(+)':>7} {'mean R':>8} {'maxDD':>9}")
    rows = []
    for k in GRID:
        r = np.array([walk_partial_be(bars, t, k) for t in b.itertuples()])
        d = r * b.risk.values
        eq = pd.Series(d[np.lexsort((b.fill_ts.values, b.day.values))])
        dd = maxdd(eq)
        rows.append(dict(partial_r=k, net=float(d.sum()), wr=float((r >= partial_r_wr(k)).mean()),
                          mean_r=float(r.mean()), dd=dd))
        print(f"{k:>9.2f}R ${d.sum():>+10,.0f} {(r > 0).mean() * 100:>6.0f}% "
              f"{r.mean():>+7.3f} ${dd:>7,.0f}")

    print("\nEngine references (rev-3 stack, this branch's rebuild): "
          "V1 BE@1R $+22,665 mean R +0.758 maxDD $1,310 · V8 shipped $+18,941 "
          "mean R +0.613 maxDD $958 · V9 default $+13,040 mean R +0.512 maxDD $2,935")
    print("\nBAR-WALK CAVEAT (carried from london_exit_lab.py): same-bar ambiguity "
          "resolves AGAINST the rule tested; bar-walks understate BE benefits (the "
          "V1 engine run beat its own bar-walk by ~3x in the exit lab). This ranks "
          "the partial_r choice directionally; it does not confirm one — no engine "
          "mgmt_variant for partial+BE exists, and this branch may not add one "
          "(engine.py is out of scope).")


def partial_r_wr(k):
    return 1e-9  # any positive realized R counts as a win for the WR(+) column


if __name__ == "__main__":
    main()
