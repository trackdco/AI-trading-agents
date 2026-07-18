#!/usr/bin/env python3
"""AMT day-typing over the MASTER dataset (pass 31) — same method as the pass-23 study,
now a first-class script: for every session day, classify balanced/imbalanced strictly
pre-open (overnight developing value area vs prior day's completed value area).

    python -m scripts.build_daytypes   -> output/amt_daytypes.csv (full-range overwrite)
"""
import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.engine.data import _session_date            # noqa: E402
from src.engine.indicators import volume_profile     # noqa: E402

DATA = Path("data/reference/nq_1m_master.parquet")
OUT = Path("output/amt_daytypes.csv")


def main():
    df = pd.read_parquet(DATA)
    df = df.assign(_sd=_session_date(df["ts_event"], dtime(18, 0)))
    days = sorted(df["_sd"].unique())
    rows, prior = [], None
    for i, d in enumerate(days):
        day_bars = df[df["_sd"] == d]
        on_bars = day_bars[day_bars["ts_event"].dt.time < dtime(8, 0)]
        rec = dict(day=str(d), type="unknown", direction=0, overlap=None)
        if prior is not None and len(on_bars) >= 60:
            pv = prior
            ov = volume_profile(on_bars, 0.25, 70)
            inter = max(0.0, min(ov.vah, pv.vah) - max(ov.val, pv.val))
            width = max(ov.vah - ov.val, 0.25)
            frac = inter / width
            rec["overlap"] = round(frac, 3)
            if frac >= 0.5:
                rec["type"] = "balanced"
            else:
                rec["type"] = "imbalanced"
                rec["direction"] = 1 if ov.poc > pv.poc else -1
            rec["prior_vah"], rec["prior_val"], rec["prior_poc"] = pv.vah, pv.val, pv.poc
        if not day_bars.empty:
            prior = volume_profile(day_bars, 0.25, 70)
        rows.append(rec)
        if i % 200 == 0:
            print(f"  {d} ({i}/{len(days)})", flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    print(f"wrote {OUT} ({len(out)} days)")
    print(out.assign(y=out.day.str[:4]).groupby(["y", "type"]).size().unstack(fill_value=0)
          .to_string())


if __name__ == "__main__":
    main()
