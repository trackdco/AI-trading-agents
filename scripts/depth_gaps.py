#!/usr/bin/env python3
"""Regenerate KNOWN_GAPS.csv for a condensed depth folder.

Two kinds of knowledge, deliberately kept separate:

  DERIVED   — counted from the data itself (any session whose minute-count != 180). Cannot
              drift as months are added/replaced.
  CURATED   — facts the data cannot tell you, chiefly days DATABENTO ITSELF flags as degraded
              via its dataset-condition API. A degraded day looks like a merely quiet day in
              the parquet; only the source knows it is bad. Hand-maintained below, merged in
              on every regeneration so it is never lost to a re-run.

    python -m scripts.depth_gaps [folder]        # default: the London 10-13 set
"""
from __future__ import annotations

import glob
import sys
from pathlib import Path

import pandas as pd

DEFAULT = "data/reference/depth_london_10_13"
FULL_SESSION_MINUTES = 180

# --- CURATED: Databento dataset-condition flags. Re-pulling these does NOT help. -----------
# Confirmed by the BentoWarning raised on get_range() for the date in question.
SOURCE_FLAGGED = {
    "2025-11-28": "Databento flags this session DEGRADED (dataset-condition API). Day after US "
                  "Thanksgiving. Re-pull confirmed 2026-07-26 — the gap is upstream, not an "
                  "export bug. DO NOT re-pull again.",
    # precedent, other folder: 2026-04-10 is likewise degraded (see depth_apr2026/README.md)
}


def build(folder: str) -> pd.DataFrame:
    rows: list[dict] = []
    for f in sorted(glob.glob(f"{folder}/*.parquet")):
        d = pd.read_parquet(f, columns=["ts"])
        lon = d.ts.dt.tz_convert("Europe/London")
        for day, n in d.groupby(lon.dt.date).ts.nunique().items():
            key = str(day)
            flagged = key in SOURCE_FLAGGED
            if n == FULL_SESSION_MINUTES and not flagged:
                continue
            status = ("DEGRADED" if flagged else
                      "MISSING" if n < 90 else
                      "EXTRA" if n > FULL_SESSION_MINUTES else "PARTIAL")
            note = SOURCE_FLAGGED.get(key) or (
                "extra boundary minute at 09:59 London; harmless"
                if n > FULL_SESSION_MINUTES else "incomplete session")
            rows.append(dict(date=key, minutes=int(n), expected=FULL_SESSION_MINUTES,
                             status=status, note=note))
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


def main() -> None:
    folder = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    g = build(folder)
    out = Path(folder) / "KNOWN_GAPS.csv"
    g.to_csv(out, index=False)
    print(g.to_string(index=False) if len(g) else "(no gaps)")
    print(f"\nwrote {out}")
    bad = g[g.status.isin(["MISSING", "DEGRADED", "PARTIAL"])]
    print(f"EXCLUDE from per-day stats: {list(bad.date)}")


if __name__ == "__main__":
    main()
