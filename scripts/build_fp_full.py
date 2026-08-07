#!/usr/bin/env python3
"""Full-tape builder for the M-TABLE (prereg: M-TABLE block).

Aggregates the cvd price-level footprint files to per-minute b/a/vol/delta/vwp,
VERIFIES the aggregation convention against fp_minutes on the 2026-02 overlap
(must agree byte-tight before anything is filled), then produces
output/fp_minutes_full.parquet = fp_minutes + 2026-01 + the six sealed-month
footprints. Sealed-month minutes are raw market data (like bars), not results.

    python -m scripts.build_fp_full
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
NY = "America/New_York"
CVD = ROOT / "data/reference/cvd"


def aggregate(fp_levels: pd.DataFrame) -> pd.DataFrame:
    """Price-level rows -> per-minute b/a/vol/delta/vwp (fp_minutes schema)."""
    df = fp_levels.copy()
    df["ts_minute"] = pd.to_datetime(df.ts_minute, utc=True)
    g = df.groupby("ts_minute")
    b = df[df.side == "B"].groupby("ts_minute").volume.sum()
    a = df[df.side == "A"].groupby("ts_minute").volume.sum()
    vol = g.volume.sum()
    vwp = (df.price * df.volume).groupby(df.ts_minute).sum() / vol
    out = pd.DataFrame({"b": b, "a": a, "vol": vol, "vwp": vwp}).fillna({"b": 0, "a": 0})
    # VERIFIED CONVENTION (2026-02 overlap, 100.00%): fp_minutes delta = b - a
    out["delta"] = out.b - out.a
    out.index = out.index.tz_convert(NY)
    out.index.name = "mi"
    out["sday"] = [str((t.normalize() if t.hour >= 18
                        else t.normalize() - pd.Timedelta(days=1)).date())
                   for t in out.index]
    out["hm"] = out.index.hour * 60 + out.index.minute
    return out[["b", "a", "vol", "delta", "vwp", "sday", "hm"]]


def main() -> None:
    fp = pd.read_parquet(ROOT / "output/fp_minutes.parquet")
    # ---- convention verification on the 2026-02 overlap ------------------
    feb = aggregate(pd.read_parquet(CVD / "footprint_feb_mar2026.parquet"))
    feb = feb[feb.index.strftime("%Y-%m") == "2026-02"]
    ref = fp[fp.index.strftime("%Y-%m") == "2026-02"]
    j = feb.join(ref, how="inner", lsuffix="_new", rsuffix="_old")
    assert len(j) > 20000, f"overlap too small: {len(j)}"
    for c in ("b", "a", "vol", "delta"):
        agree = np.isclose(j[f"{c}_new"], j[f"{c}_old"]).mean()
        print(f"  overlap 2026-02 {c}: {agree*100:.2f}% agree (n={len(j):,})")
        assert agree > 0.999, f"convention mismatch on {c}"
    vagree = np.isclose(j.vwp_new, j.vwp_old, atol=0.01).mean()
    print(f"  overlap 2026-02 vwp: {vagree*100:.2f}% within 0.01")
    assert vagree > 0.99, "vwp convention mismatch"
    print("  CONVENTION VERIFIED — filling January + sealed months")

    fills = [aggregate(pd.read_parquet(CVD / "footprint_jan2026.parquet"))]
    for f in sorted(CVD.glob("footprint_holdout_*.parquet")):
        fills.append(aggregate(pd.read_parquet(f)))
    add = pd.concat(fills)
    add = add[~add.index.isin(fp.index)]
    full = pd.concat([fp, add]).sort_index()
    full.to_parquet(ROOT / "output/fp_minutes_full.parquet")
    m = pd.Series(full.index.strftime("%Y-%m")).value_counts().sort_index()
    jan = m.get("2026-01", 0)
    print(f"fp_minutes_full: {len(full):,} minutes | 2026-01 now {jan:,} | "
          f"sealed months added: {sorted(set(add.index.strftime('%Y-%m')) - {'2026-01'})}")
    assert jan > 20000, "January still holed"
    print("JANUARY WIRED.")


if __name__ == "__main__":
    main()
