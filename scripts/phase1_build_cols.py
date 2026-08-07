#!/usr/bin/env python3
"""PHASE 1 prep — close the column gap between the candidate books.

MISMATCH 4 from Phase 0: `next_lvl_R` and the ceiling flags exist only on
the LTF frame. The incumbent has no D7 geometry, so the combined book
cannot be diagnosed on the one variable that is actually live.

This adds next_lvl_R / ceil5 / ceil60 to the incumbent LONDON rows using
the SAME `admissibility` code path the LTF census used (imported, not
reimplemented), so the column means the same thing in both books.

Depth is NOT built for the LTF rows — stated as a standing gap in the
Phase 1 report rather than papered over.

    python -m scripts.phase1_build_cols
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.htf_ma_level_census import LOCI, level_series          # noqa: E402
from src.htf_ma.levels import NY, bb_ma_asof                        # noqa: E402

OUT = ROOT / "output/htf_ma_census"


def main() -> None:
    INC = pd.read_parquet(OUT / "incumbent_london.parquet")
    INC["t"] = pd.to_datetime(INC.t)
    INC["t_entry"] = pd.to_datetime(INC.t_entry)
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close",
                                              "volume"]]
    recs = []
    days = sorted(INC.sess_day.unique())
    for k, day in enumerate(days):
        D = INC[INC.sess_day == day]
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        t1 = t0 + pd.Timedelta(hours=23)
        hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30))
                    & (bars.index < t1)]
        seg = hist[(hist.index >= t0) & (hist.index < t1)]
        if hist.empty or seg.empty:
            continue
        ma15, _ = bb_ma_asof(hist, 15)
        idx = seg.index
        lv = level_series(hist, idx, ma15)
        ceil = {}
        for tfc in (5, 60):
            mac, _ = bb_ma_asof(hist, tfc)
            fc_ = hist.resample(f"{tfc}min", label="right",
                                closed="left").agg({"close": "last"}).dropna()
            fc_ = fc_[(fc_.index > t0) & (fc_.index <= t1)]
            mc_ = mac.reindex(fc_.index - pd.Timedelta(minutes=1)).to_numpy()
            abv = fc_.close.to_numpy() > mc_
            prv = np.concatenate([[False], abv[:-1]])
            ceil[tfc] = {"ma1m": mac.reindex(idx).to_numpy(),
                         "ends": fc_.index.values,
                         "up": abv & ~prv, "dn": (~abv) & prv, "n": len(fc_)}
        for r in D.itertuples():
            te = pd.Timestamp(r.t_entry)
            j0 = int(np.searchsorted(idx.values, te.to_datetime64()))
            p = max(j0 - 1, 0)
            if j0 >= len(idx) or not np.isfinite(r.risk) or r.risk <= 0:
                continue
            d, entry = int(r.direction), float(r.entry)
            best, bname = np.nan, None
            for other in LOCI:
                if other == r.locus:
                    continue
                v = lv[other][p]
                if not np.isfinite(v):
                    continue
                dist = d * (v - entry)
                if dist > 0 and (not np.isfinite(best) or dist < best):
                    best, bname = dist, other
            rec = {"sess_day": day, "t": r.t, "side": r.side, "pop": r.pop,
                   "next_lvl": bname,
                   "next_lvl_R": (best / r.risk) if np.isfinite(best) else np.nan}
            for tfc in (5, 60):
                C = ceil[tfc]
                m = C["ma1m"][p]
                md = d * (m - entry) if np.isfinite(m) else np.nan
                rec[f"ceil{tfc}_between"] = bool(np.isfinite(md)
                                                 and np.isfinite(best)
                                                 and 0 < md < best)
                b = int(np.searchsorted(C["ends"], pd.Timestamp(r.t)
                                        .to_datetime64(), side="right")) - 1
                rec[f"ceil{tfc}_fresh"] = bool(
                    0 <= b < C["n"] and (C["up"][b] if d > 0 else C["dn"][b]))
            recs.append(rec)
        if k % 60 == 0:
            print(f"  {k}/{len(days)}...", flush=True)
    G = pd.DataFrame(recs)
    G.to_parquet(OUT / "incumbent_london_d7.parquet", index=False)
    print(f"written: incumbent_london_d7.parquet ({len(G):,} rows of "
          f"{len(INC):,}); next_lvl_R non-null "
          f"{G.next_lvl_R.notna().mean()*100:.1f}%")


if __name__ == "__main__":
    main()
