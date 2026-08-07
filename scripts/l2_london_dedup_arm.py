#!/usr/bin/env python3
"""Re-derive the setup dedup + VWAP ruling directly on an L2 outcome book.

WHY THIS EXISTS. `scripts/l1_london_dedup.py` grouped setups from the E3 limit walk. The
market-entry arms fill at a DIFFERENT moment — the trigger candle's close — so their setup
grouping is not the same object and must not be inherited. Re-deriving it per arm is the
only honest option; carrying E3's grouping across would silently mis-group every arm.

Nothing about the rule changes: same 15-minute window from a setup's FIRST fill, same
5-point proximity, same shared-cluster-level test, same VWAP-touch eligibility applied
BEFORE grouping (ANGUS: it is a trigger requirement, so an inadmissible trigger must not
claim a setup and block a valid one behind it), same `first` tie-break on causality.

    python -m scripts.l2_london_dedup_arm --entry EC
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.l1_london_dedup import assign  # noqa: E402

NY = "America/New_York"


def path_for(entry: str) -> Path:
    return (ROOT / "output/l2_outcomes_london_fit.parquet" if entry == "E3"
            else ROOT / f"output/l2_outcomes_london_fit_{entry}.parquet")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--entry", default="EC", choices=["EC", "E4", "E3"])
    a = ap.parse_args()

    p = path_for(a.entry)
    O = pd.read_parquet(p)
    O = O.drop(columns=[c for c in O.columns
                        if c.startswith(("setup_", "vs_")) or c in ("arm_none", "arm_struct")],
               errors="ignore")
    # `assign` speaks the L1 vocabulary: arm_none = this candidate produced a position,
    # fill_px = the price it went on at.
    O["arm_none"] = O["status"] == "outcome"
    O["fill_px"] = O["entry"]
    O = O.sort_values(["day", "fill_ts"]).reset_index(drop=True)

    O = assign(O, "setup")
    O = assign(O, "vs", eligible=O["vwap_touched"].fillna(False).astype(bool))
    O = O.drop(columns=["fill_px"])
    O.to_parquet(p, index=False)

    nd = O["day"].nunique()
    ns = int(O.loc[O.vs_id > 0, "vs_id"].nunique())
    fl = int(O.arm_none.sum())
    print(f"{a.entry}: {len(O):,} candidates | {fl:,} positions | "
          f"{ns:,} VWAP-ruled setups ({ns/nd:.2f}/session over {nd} sessions)")
    K = O[O.vs_first]
    print("  " + " ".join(f"{k} {(K.kind == k).mean():.0%}"
                          for k in ("displacement", "rejection_block"))
          + f" | median risk {K.risk.median():.2f} pt"
          + f" | below 9.5pt {(K.risk < 9.5).mean():.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
