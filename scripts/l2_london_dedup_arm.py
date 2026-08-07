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

The same argument applies to the TARGET arm, which is why `--rr-floor` is here. Cutting the
2R floor changes which candidates the engine will order at all (`vetoed_rr_floor` moves), so
the rr0 arm's *eligible* population differs from the 2R arm's. Inheriting either one's
grouping would let a candidate that arm never traded claim a setup and block the one behind
it — the precise failure this file exists to prevent, one layer up.

    python -m scripts.l2_london_dedup_arm --entry EC
    python -m scripts.l2_london_dedup_arm --entry EC --rr-floor 0
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


def path_for(entry: str, rr_floor: float | None = None, arm: str = "") -> Path:
    """Mirrors the suffix `build_l2_outcomes_london` writes, so the two stay in step."""
    suffix = arm + ("" if entry == "E3" else f"_{entry}") + \
             ("" if rr_floor is None else f"_rr{rr_floor:g}")
    return ROOT / f"output/l2_outcomes_london_fit{suffix}.parquet"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--entry", default="EC", choices=["EC", "E4", "E3"])
    ap.add_argument("--rr-floor", type=float, default=None,
                    help="select the --rr-floor arm's book; omit for the 2.0-floor book")
    ap.add_argument("--arm", default="", help="census arm suffix, e.g. `_pp`")
    a = ap.parse_args()

    p = path_for(a.entry, a.rr_floor, a.arm)
    if not p.exists():
        ap.error(f"{p.relative_to(ROOT)} does not exist — build that arm first")
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
    arm = a.entry + ("" if a.rr_floor is None else f" rr{a.rr_floor:g}")
    print(f"{arm}: {len(O):,} candidates | {fl:,} positions | "
          f"{ns:,} VWAP-ruled setups ({ns/nd:.2f}/session over {nd} sessions)")
    K = O[O.vs_first]
    print("  " + " ".join(f"{k} {(K.kind == k).mean():.0%}"
                          for k in ("displacement", "rejection_block"))
          + f" | median risk {K.risk.median():.2f} pt"
          + f" | below 9.5pt {(K.risk < 9.5).mean():.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
