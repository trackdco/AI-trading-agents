#!/usr/bin/env python3
"""Pull the two datasets this project still needs from Databento. RUN THIS LOCALLY.

It cannot run inside the Claude Code remote container: the environment's network policy denies
CONNECT to hist.databento.com (403 at the agent proxy). Run it on Brake's machine, then move the
resulting parquet files into data/reference/ and commit ONLY those (they are a few MB each).

CREDENTIALS. The key is read from the DATABENTO_API_KEY environment variable. It is never written
to disk, never printed, and never committed. Do not paste it into a chat, a file, or a commit.

    export DATABENTO_API_KEY=...        # do NOT put this in .bashrc committed to the repo
    pip install databento pandas pyarrow
    python3 scripts/databento_pull.py

WHAT IT PULLS AND WHY
  1 6E (Euro FX futures), 1-min, 2025-07-01 -> today
      To test the YouTuber's DXY inverse-correlation claim -- his single biggest asserted edge
      (+16-19pp win rate) and the only untested part of his spec. DXY is ICE, not in GLBX, so 6E
      is the CME-listed proxy for the dollar leg.
      SIGN NOTE: gold and the euro are BOTH inverse-dollar, so they move TOGETHER. His "gold
      inverts DXY" becomes "gold agrees with 6E". Getting this sign backwards would invert the
      whole test, so it is stated here rather than left to inference.
  2 GC (Gold), 1-min, 2021-01-01 -> 2022-12-31
      A CROSS-REGIME HOLDOUT. Every gold result in this repo sits on Jul-2025 -> Jul-2026, one
      uninterrupted bull run (3290 -> 5623). 2021-22 covers a range-bound year and a rate-shock
      selloff. The Asia reversal book (n=488, E[R] +0.234, p=0.090) is unvalidated until it is
      read ONCE on this data. Read it once. Re-reading it turns a holdout into a training set.

COST. ohlcv-1m is Databento's cheapest schema; these two pulls are a handful of dollars. Use
timeseries.get_range (streaming) rather than batch.submit_job -- for bar data it is simpler and
there is no job to poll for.
"""
import os
import sys
from datetime import date

import databento as db

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "data", "reference")

PULLS = [
    # (symbol, stype_in, start, end, outfile)
    ("6E.v.0", "continuous", "2025-07-01", str(date.today()), "6e_1m_2025_2026.parquet"),
    ("GC.v.0", "continuous", "2021-01-01", "2022-12-31", "gc_1m_2021_2022.parquet"),
]


def main():
    key = os.environ.get("DATABENTO_API_KEY")
    if not key:
        sys.exit("DATABENTO_API_KEY is not set. export it first; do not hardcode it here.")
    client = db.Historical(key)
    os.makedirs(OUT, exist_ok=True)

    for sym, stype, start, end, fname in PULLS:
        path = os.path.join(OUT, fname)
        if os.path.exists(path):
            print(f"skip {fname} (already exists)")
            continue
        print(f"pull {sym} {start} -> {end} ...", flush=True)
        data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            schema="ohlcv-1m",
            symbols=sym,
            stype_in=stype,
            start=start,
            end=end,
        )
        df = data.to_df()
        if df.empty:
            print(f"  EMPTY for {sym} -- check the symbol/stype before retrying")
            continue
        df = df.reset_index()
        df.to_parquet(path, index=False)
        lo, hi = df.ts_event.min(), df.ts_event.max()
        print(f"  {len(df):,} bars  {lo} -> {hi}  -> {path}")

    print("\nDone. Commit ONLY the parquet files under data/reference/ -- never raw tick or "
          "depth data, and never the API key.")


if __name__ == "__main__":
    main()
