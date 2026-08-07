"""Job 1 — sealed holdout census (spec 6.4). WRITE-ONLY.

Computes the canonical-construction census over the six sealed 2023/24
months and writes output/sealed/excursions_holdout.parquet and
output/sealed/profiles_holdout.parquet.

DELIBERATELY PRINTS NO OUTCOME STATISTICS. The only stdout is input-side
completeness (session and profile-status counts), which is inputs-only
information in the sense of the canon's era-measurement precedent. No
excursion counts, no rates, no lifts. Reading the sealed parquets goes
through report.py, which refuses without --unseal + the Job 2 prereg.
"""
from __future__ import annotations

import sys

import pandas as pd

sys.path.insert(0, "scripts/vp_census")
import vp_lib as V

MONTHS = ("2023-07", "2023-09", "2023-11", "2024-03", "2024-04", "2024-10")


def main() -> int:
    bars = V.load_master_bars()
    sess = pd.Series(sorted(set(bars["session"])))
    key = pd.to_datetime(sess).dt.strftime("%Y-%m")
    hold = list(sess[key.isin(MONTHS)])
    print(f"holdout sessions with bars: {len(hold)} across {len(MONTHS)} months")

    prof = V.build_profiles(bars, hold)  # canonical settings only
    status = prof["profile_status"].value_counts().to_dict()
    print(f"profile status counts (inputs-only): {status}")

    ex = V.run_census(bars, prof)
    if len(ex):
        ex["session_id"] = pd.to_datetime(ex["session_date"]).astype(str)
        ex["era"] = pd.to_datetime(ex["session_date"]).dt.year.astype(str)

    prof.to_parquet("output/sealed/profiles_holdout.parquet", index=False)
    ex.to_parquet("output/sealed/excursions_holdout.parquet", index=False)
    print("sealed artifacts written. No statistics computed or printed. "
          "Unsealing requires report.py --unseal plus "
          "docs/PREREG-vp-excursion-census.md (Job 2).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
