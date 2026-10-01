#!/usr/bin/env python3
"""6E CONTINUOUS — Databento GLBX outrights -> volume-rolled front month.

    python -m scripts.build_6e_continuous <glbx-*.ohlcv-1m.csv.zst>

Mirrors the gc_continuous.py rule: outrights only (calendar spreads carry
a '-' in the mapped symbol and are dropped), front month chosen per
session-day by total volume, roll day-pairs flagged for exclusion.

IMPORTANT — the Databento parent symbol is `6E.FUT`, NOT `EURUSD.FUT`.
`EURUSD.FUT` returns the EFP basis book (symbols `6E:XF:EURUSD:*`,
prices ~0.000-0.011, one negative, ~127 bars/day), which is not the
euro future. See docs/FINDINGS-6e-euro-port.md section 1.

Writes data/reference/6e_1m.parquet and 6e_roll_days.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import zstandard

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "reference"


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    src = Path(sys.argv[1])
    tmp = OUT / "_6e_raw.csv"
    with open(src, "rb") as f, open(tmp, "wb") as o:
        zstandard.ZstdDecompressor().copy_stream(f, o)
    df = pd.read_csv(tmp)
    tmp.unlink()
    df = df[~df.symbol.str.contains("-")]          # drop calendar spreads
    if df.symbol.str.contains(":").any():
        raise SystemExit("EFP/basis symbols present - re-pull with 6E.FUT")
    df["ts"] = pd.to_datetime(df.ts_event, utc=True).dt.tz_convert("America/New_York")
    df["sess"] = (df.ts - pd.Timedelta(hours=18)).dt.normalize()
    vol = df.groupby(["sess", "symbol"]).volume.sum().reset_index()
    front = vol.loc[vol.groupby("sess").volume.idxmax()].set_index("sess").symbol
    cont = df[df.symbol == df.sess.map(front)].sort_values("ts").reset_index(drop=True)
    rolls = [str(d.date()) for d in front[front != front.shift()].index[1:]]
    cont.to_parquet(OUT / "6e_1m.parquet")
    (OUT / "6e_roll_days.json").write_text(json.dumps(rolls))
    act = cont[(cont.ts.dt.hour >= 2) & (cont.ts.dt.hour < 16)]
    med = (act.high - act.low).median()
    print(f"{len(cont):,} bars / {cont.sess.nunique()} session-days / "
          f"{len(rolls)} rolls -> 6e_1m.parquet")
    print(f"median active-session 1m candle: {med:.5f} = {med/0.00005:.1f} ticks")
    print("SCREEN (docs/FINDINGS-6e-euro-port.md S5): the grammar needs >=20 "
          "ticks of median 1m movement. NQ 28, GC 21, 6E 3.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
