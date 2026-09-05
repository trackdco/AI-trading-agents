#!/usr/bin/env python3
"""NQ 2017-2019 CONTINUOUS — the SECOND holdout tape (PREREG-holdout-2017-2019.md), rebuilt from the raw Databento pull.

    python -m scripts.build_nq_2017_2019 <glbx-mdp3-20170101-20200102.ohlcv-1m.csv.zst> [out_dir]

Same recipe as build_6e_continuous / gc_continuous: outrights only (calendar
spreads carry a '-' in the mapped symbol and are dropped), front month chosen
per session-day (18:00 ET anchor) by total volume, roll session-days flagged
for exclusion. Parent symbol NQ.FUT, stype_in=parent, GLBX.MDP3, ohlcv-1m.

Integrity gates from docs/PREREG-holdout-2017-2019.md section 1, enforced here
so the file cannot be rebuilt wrong silently:
  - no ':' symbols (EFP/basis contamination - the 6E lesson)
  - price range plausible for NQ 2017-19 (4,500 - 9,300)
  - >= 700 session-days

Source of truth is the raw file committed alongside this output in
data/reference/nq_2017_2019_raw/ (sha256 in its README, matching Databento's
own manifest). Writes nq_2017_2019_1m.parquet and nq_2017_2019_roll_days.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import zstandard

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print(__doc__)
        return 2
    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) == 3 else ROOT / "data" / "reference"
    out.mkdir(parents=True, exist_ok=True)
    tmp = out / "_nq17_raw.csv"
    with open(src, "rb") as f, open(tmp, "wb") as o:
        zstandard.ZstdDecompressor().copy_stream(f, o)
    df = pd.read_csv(tmp)
    tmp.unlink()
    n_raw = len(df)
    df = df[~df.symbol.str.contains("-")]                       # calendar spreads
    if df.symbol.str.contains(":").any():
        raise SystemExit("EFP/basis symbols present - re-pull with NQ.FUT")
    df["ts"] = pd.to_datetime(df.ts_event, utc=True).dt.tz_convert("America/New_York")
    df["sess"] = (df.ts - pd.Timedelta(hours=18)).dt.normalize()
    vol = df.groupby(["sess", "symbol"]).volume.sum().reset_index()
    front = vol.loc[vol.groupby("sess").volume.idxmax()].set_index("sess").symbol
    cont = df[df.symbol == df.sess.map(front)].sort_values("ts").reset_index(drop=True)
    rolls = [str(d.date()) for d in front[front != front.shift()].index[1:]]

    lo, hi = float(cont.low.min()), float(cont.high.max())
    if not (4_500 <= lo <= 5_500 and 8_300 <= hi <= 9_300):
        raise SystemExit(f"price range {lo:.2f}-{hi:.2f} implausible for NQ 2017-19")
    if cont[cont.sess >= "2017-01-01"].sess.nunique() < 700:
        raise SystemExit(f"only {cont.sess.nunique()} session-days")

    cont.to_parquet(out / "nq_2017_2019_1m.parquet")
    (out / "nq_2017_2019_roll_days.json").write_text(json.dumps(rolls))
    print(f"{n_raw:,} raw rows -> {len(cont):,} continuous bars / "
          f"{cont.sess.nunique()} session-days / {len(rolls)} rolls")
    print(f"range {lo:.2f} - {hi:.2f}   {cont.ts.min()} -> {cont.ts.max()}")
    print(f"-> {out / 'nq_2017_2019_1m.parquet'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
