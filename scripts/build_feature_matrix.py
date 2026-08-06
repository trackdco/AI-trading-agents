#!/usr/bin/env python3
"""One row per filled trigger, every causally-legal feature, ready for the PBO harness.

ANGUS 2026-08-06: *"become a literal professional trader for new york session in this chat,
and just figure it the fuck out"* and *"when you over fit, you'll know whether it overfits or
not very simply, by seeing if it holds in holdout or not. also PBO and DSR etc etc."*

This file assembles the search space. `scripts/pbo_harness.py` searches it under
Combinatorially Symmetric Cross-Validation and the Deflated Sharpe Ratio.

THE CAUSALITY BAR IS THE WHOLE VALUE OF THIS FILE. A feature qualifies only if it was
knowable when the order was placed. This project has produced two separate false findings by
breaking that rule, both worth remembering because they looked spectacular:

  the depth read one bar late      W +19.0pp -> +8.2pp once read at the decision instead of
                                   the fill (research/findings/LDN-depth-read-one-bar-late.md)
  the retest "confirmation"        +8.90 pt/trade that was really a +10.57 pt head start,
                                   because "the bar closed in our favour" is only known at
                                   the bar's end while the limit filled mid-bar

So: NOTHING read at or after the fill. Depth and footprint are excluded outright for the
limit book -- there is no legal anchor for them on a passive entry.

FOUR FAMILIES:

  geometry   what the setup looks like -- timeframe, pattern, confluence, intended risk,
             level stack. Known at placement by construction.
  clock      hour, minutes into session. Known trivially.
  context    the daily regime layer, built from sessions STRICTLY BEFORE the day
             (scripts/build_daily_context.py shifts once at the end, structurally).
  htf        premium/discount, midnight-open side, and whether the day's move is already
             spent (scripts/build_htf_features.py). The only family that is not a restatement
             of level distance -- see research/findings/the-geometry-frontier.md.

    python -m scripts.build_feature_matrix [--book output/l2_outcomes_fit.parquet]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NY = "America/New_York"
OUT = ROOT / "output/feature_matrix.parquet"

CTX = ["trend_atr", "ret5_atr", "trend_pct", "close_pos", "va_overlap", "va_overlap_3",
       "poc_streak", "poc_dir3", "poc_dir5", "atr20", "atr_pct", "range_atr", "vix", "vix_pct",
       "trend_state", "vol_state", "balance_state", "trend_sign"]
HTF = ["pd_position", "pd_edge", "vs_midnight_open", "vs_mid_norm", "fades_open",
       "already_moved", "opposite_taken", "both_taken"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", default="output/l2_outcomes_fit.parquet")
    ap.add_argument("--dedup", action="store_true",
                    help="keep only the first trigger of each deduped setup (ANGUS: do not "
                         "double up when a level breaks on several timeframes in sequence)")
    a = ap.parse_args()

    O = pd.read_parquet(ROOT / a.book)
    D = O[O.status == "outcome"].copy()
    if a.dedup and "vs_first" in D.columns:
        D = D[D.vs_first]

    D = D.merge(pd.read_parquet(ROOT / "output/daily_context.parquet"), on="day", how="left")
    D = D.merge(pd.read_parquet(ROOT / "output/htf_features.parquet"), on="ts", how="left")
    D["era"] = D.day.str[:4]
    D["dir"] = np.where(D.direction.astype(str).str.lower().str.startswith(("l", "b")), 1, -1)

    ts = pd.to_datetime(D.fill_ts, utc=True, format="mixed").dt.tz_convert(NY)
    D["hour"] = ts.dt.hour
    D["mins_into_session"] = ts.dt.hour * 60 + ts.dt.minute - (9 * 60 + 30)

    def _n(s):
        if isinstance(s, (list, tuple, np.ndarray)):
            return len(s)
        return len(str(s).split(",")) if s not in (None, "", "nan") else 0
    for c in ("cluster_members", "level_stack"):
        if c in D.columns:
            D[f"n_{c}"] = D[c].map(_n)

    # context stated RELATIVE to the trade's direction -- a raw trend number separates nothing
    # until it says "with me" or "against me"
    for c in ("trend_atr", "ret5_atr", "poc_streak", "poc_dir3", "poc_dir5", "trend_sign"):
        if c in D.columns:
            D[f"{c}_dir"] = pd.to_numeric(D[c], errors="coerce") * D["dir"]

    keep = (["day", "era", "ts", "fill_ts", "R", "pts", "risk", "dir", "direction",
             "tf", "pattern", "kind", "htf_flag", "confluence_count", "hour",
             "mins_into_session", "n_cluster_members", "n_level_stack"]
            + [c for c in CTX if c in D.columns]
            + [f"{c}_dir" for c in ("trend_atr", "ret5_atr", "poc_streak", "poc_dir3",
                                    "poc_dir5", "trend_sign") if f"{c}_dir" in D.columns]
            + [c for c in HTF if c in D.columns])
    M = D[[c for c in keep if c in D.columns]].copy()
    M.to_parquet(OUT, index=False)

    print(f"wrote {OUT.relative_to(ROOT)} — {len(M):,} rows x {len(M.columns)} cols, "
          f"{M.day.nunique()} sessions")
    print(f"  span {M.day.min()} -> {M.day.max()}")
    print(f"  base mean R {M.R.mean():+.4f}  net {M.pts.mean():+.3f} pt  "
          f"WR {(M.R > 0).mean():.1%}")
    print(f"  eras: {M.era.value_counts().to_dict()}")
    miss = {c: f"{M[c].isna().mean():.0%}" for c in M.columns if M[c].isna().mean() > 0.02}
    print(f"  columns >2% null: {miss if miss else 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
