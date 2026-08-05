#!/usr/bin/env python3
"""Balance composites per docs/PREREG-failed-auction.md — frozen definition.

A composite = a maximal run of >= 2 consecutive sessions whose value areas
(amt_days.parquet, 70% TPO) OVERLAP pairwise in sequence: session i joins the
run if [val_i, vah_i] intersects the running composite's [val, vah]. The
composite's edges while it lives = min VAL / max VAH of its members so far
(the union-of-value read a trader would mark). One row per (day, composite
state as of that day's open) so censuses can ask "did a composite of age >= 2
exist this morning, and where were its edges" without lookahead.

    python -m scripts.nya_composites   # writes output/nya_composites.parquet
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    A = pd.read_parquet(ROOT / "output/amt_days.parquet").sort_values("day").reset_index(drop=True)
    rows = []
    run: list[dict] = []   # members of the live composite (strictly prior days)
    for r in A.itertuples():
        if run:
            c_val = min(m["val"] for m in run)
            c_vah = max(m["vah"] for m in run)
            rows.append(dict(day=r.day, comp_age=len(run), comp_val=c_val,
                             comp_vah=c_vah,
                             comp_poc=run[-1]["poc"],
                             comp_start=run[0]["day"]))
        else:
            rows.append(dict(day=r.day, comp_age=0, comp_val=None,
                             comp_vah=None, comp_poc=None, comp_start=None))
        # roll today's session into the run state for tomorrow
        if run:
            c_val = min(m["val"] for m in run)
            c_vah = max(m["vah"] for m in run)
            if r.val <= c_vah and r.vah >= c_val:
                run.append(dict(day=r.day, val=r.val, vah=r.vah, poc=r.poc))
            else:
                run = [dict(day=r.day, val=r.val, vah=r.vah, poc=r.poc)]
        else:
            run = [dict(day=r.day, val=r.val, vah=r.vah, poc=r.poc)]
    out = pd.DataFrame(rows)
    out.to_parquet(ROOT / "output/nya_composites.parquet", index=False)
    live = out[out.comp_age >= 2]
    print(f"{len(out)} sessions; composite(age>=2) exists at open on {len(live)} "
          f"({len(live)/len(out):.0%}); age distribution: "
          f"{out.comp_age.clip(upper=6).value_counts().sort_index().to_dict()}")


if __name__ == "__main__":
    main()
