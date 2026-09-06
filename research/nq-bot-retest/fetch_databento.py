#!/usr/bin/env python3
"""
Holdout data acquisition via Databento — chosen by the user on 2026-09-06 ("Use the Databento one")
in place of the manual TradingView export named in PREREGISTRATION.md §3.

Dataset GLBX.MDP3 (CME Globex MDP 3.0), schema ohlcv-1m, symbol MNQ.c.0 (continuous front month,
calendar roll = the same roll rule as TradingView's MNQ1!). Writes the CSV that
prepare_holdout_data.py accepts (ts_event ISO-8601 UTC, open, high, low, close, volume, symbol).
Prints only counts, timestamps and the quoted cost — no prices.

The API key is read from the DATABENTO_API_KEY environment variable and never printed.

usage: fetch_databento.py OUT.csv START(YYYY-MM-DD) END(YYYY-MM-DD) [--dry-run]
"""
import os
import sys
import time

import databento as db

out, start, end = sys.argv[1], sys.argv[2], sys.argv[3]
dry = "--dry-run" in sys.argv
key = os.environ.get("DATABENTO_API_KEY")
if not key:
    sys.exit("DATABENTO_API_KEY is not set")

client = db.Historical(key)
params = dict(dataset="GLBX.MDP3", schema="ohlcv-1m", symbols=["MNQ.c.0"], stype_in="continuous",
              start=start, end=end)
avail = client.metadata.get_dataset_range(dataset="GLBX.MDP3")
print(f"GLBX.MDP3 available range: {avail}")
cost = client.metadata.get_cost(**params)
size = client.metadata.get_billable_size(**params)
print(f"quoted cost for {start} -> {end}: ${cost:.4f} USD ({size:,} billable bytes)")
if dry:
    sys.exit(0)

t0 = time.time()
data = client.timeseries.get_range(**params)
df = data.to_df()
print(f"received {len(df):,} rows in {time.time() - t0:.0f}s; columns {list(df.columns)}")
df = df.reset_index()
df = df.sort_values("ts_event")
cols = ["ts_event", "rtype", "publisher_id", "instrument_id", "open", "high", "low", "close", "volume", "symbol"]
cols = [c for c in cols if c in df.columns]
df[cols].to_csv(out, index=False, date_format="%Y-%m-%dT%H:%M:%S.%fZ")
print(f"first {df['ts_event'].iloc[0]}  last {df['ts_event'].iloc[-1]}  symbols {sorted(df['symbol'].unique()) if 'symbol' in df else 'n/a'}")
print("written", out)
