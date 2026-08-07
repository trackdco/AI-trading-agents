#!/usr/bin/env python3
"""Pass 22: back-fill ob_mid/ob_stop (two-candle order block) onto EXISTING trigger caches
so E5/EC2 split arms run on the standard (OTE-off) trigger sets without a full re-detection.
Result-identical to re-detecting: _order_block only needs the trigger's resampled frame + bar
index, both reproducible from the committed dataset.

    python -m scripts._augment_ob

Writes <cache>_ob.csv next to each input; inputs untouched.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.engine.sessions import resample_ohlcv          # noqa: E402
from src.engine.triggers import _order_block            # noqa: E402

DATA = Path("data/reference/nq_1m_feb_jul2026.parquet")
CACHES = [Path("output/triggers_feb.csv"), Path("output/triggers_marjul.csv"),
          Path("output/triggers_junjul.csv")]
# CLI override (pass 31): python -m scripts._augment_ob <data.parquet> <cache.csv> [...]
if len(sys.argv) > 2:
    DATA = Path(sys.argv[1])
    CACHES = [Path(p) for p in sys.argv[2:]]


def main():
    df = pd.read_parquet(DATA)
    frames = {tf: resample_ohlcv(df, tf).reset_index(drop=True)
              for tf in ("1min", "2min", "3min", "5min")}
    idx = {tf: pd.Index(fr["ts_event"]) for tf, fr in frames.items()}

    for cache in CACHES:
        rows = pd.read_csv(cache)
        mids, stops, miss = [], [], 0
        for _, r in rows.iterrows():
            fr, ix = frames[r["tf"]], idx[r["tf"]]
            ts = pd.Timestamp(r["ts"])
            i = ix.get_indexer([ts])[0]
            if i < 0:
                mids.append(None), stops.append(None)
                miss += 1
                continue
            m, s = _order_block(fr, int(i), r["direction"])
            mids.append(m), stops.append(s)
        rows["ob_mid"], rows["ob_stop"] = mids, stops
        out = cache.with_name(cache.stem + "_ob.csv")
        rows.to_csv(out, index=False)
        n_ob = rows["ob_mid"].notna().sum()
        print(f"{out}: {len(rows)} triggers, {n_ob} with OB partner, {miss} bar-misses", flush=True)


if __name__ == "__main__":
    main()
