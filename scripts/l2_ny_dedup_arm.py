#!/usr/bin/env python3
"""Re-derive the setup dedup + VWAP ruling on a NEW YORK L2 outcome book.

WHY THIS EXISTS, AND IT IS NOT A NICE-TO-HAVE. **New York has never been deduplicated.**
The dedup was built for London only (`scripts/l1_london_dedup.py`,
`scripts/l2_london_dedup_arm.py`) and NY's outcome books carry no setup identity at all. So
every NY number computed to date counts the SAME TRADE MORE THAN ONCE whenever a level is
broken on several timeframes in sequence. Measured on London, that inflation is **3.0x**
(2,139 displacement outcomes -> 719 setups).

ANGUS 2026-08-05, and he was emphatic:

    "big thing is overlapping entries. for example if it broke the 1 minute bb ma, and then
     3 minute as well after the 1 minute filled, it should not double up on the same trade
     if that makes sense. for me im always looking at multi time frames, and i enter whats
     best. i dont scale my entry just because it broke the MA on multiple time frames
     sequentially."

This is worse than a cosmetic N inflation. The prop objective is scored on GREEN DAYS, and
taking one bad setup three times triples its damage on that day's book -- so the un-deduped
green-day figure is not merely imprecise, it is biased against exactly the metric we are
optimising.

NO RE-IMPLEMENTATION. `assign()` is imported from the London module and used unchanged: same
15-minute window from a setup's first fill, same 5-point proximity, same shared-cluster-level
test, same `first` tie-break on causality, same VWAP eligibility applied BEFORE grouping (an
inadmissible trigger must not claim a setup and block a valid one queued behind it). The rule
is session-agnostic; only the input book differs. The champion-vs-canon lesson stands -- a
faithful-to-spec rewrite once shared 14% of its trades with the thing it rewrote.

ONE NY-SPECIFIC JOIN. `build_l2_outcomes.py` does not carry `vwap_touched` into its rows
(the London builder does), so it is joined back from the L0 census on `ts`.

    python -m scripts.l2_ny_dedup_arm --book output/l2_outcomes_fit_EC_rr0.parquet
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.l1_london_dedup import assign  # noqa: E402

L0 = ROOT / "output/l0_triggers_fit.parquet"


def dedup(O: pd.DataFrame, l0: Path = L0) -> pd.DataFrame:
    O = O.drop(columns=[c for c in O.columns
                        if c.startswith(("setup_", "vs_")) or c in ("arm_none", "arm_struct")],
               errors="ignore").copy()

    if "vwap_touched" not in O.columns:
        T = pd.read_parquet(l0, columns=["ts", "vwap_touched"]).drop_duplicates("ts")
        O = O.merge(T, on="ts", how="left")

    # `assign` speaks the L1 vocabulary: arm_none = this candidate produced a position,
    # fill_px = the price it went on at.
    O["arm_none"] = O["status"] == "outcome"
    O["fill_px"] = O["entry"]
    O = O.sort_values(["day", "fill_ts"]).reset_index(drop=True)

    O = assign(O, "setup")
    O = assign(O, "vs", eligible=O["vwap_touched"].fillna(False).astype(bool))
    return O.drop(columns=["fill_px"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", required=True, help="NY L2 outcomes parquet, edited in place")
    ap.add_argument("--l0", default=str(L0))
    a = ap.parse_args()

    p = Path(a.book)
    O = dedup(pd.read_parquet(p), Path(a.l0))
    O.to_parquet(p, index=False)

    fills = O[O.status == "outcome"]
    disp = fills[fills.kind == "displacement"]
    nd = O.day.nunique()
    ns = int(O.loc[O.vs_id > 0, "vs_id"].nunique())
    print(f"{p.name}")
    print(f"  {len(O):,} candidates / {len(fills):,} fills over {nd} sessions")
    print(f"  displacement fills {len(disp):,} -> deduped setups "
          f"{int(disp.vs_first.sum()):,}  ({len(disp)/max(int(disp.vs_first.sum()),1):.2f}x "
          f"inflation removed)")
    print(f"  VWAP-ruled setups {ns:,}  ({ns/nd:.2f}/session)")
    sz = O.loc[O.vs_id > 0].groupby("vs_id").size()
    if len(sz):
        print(f"  setup sizes: {sz.value_counts().sort_index().to_dict()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
