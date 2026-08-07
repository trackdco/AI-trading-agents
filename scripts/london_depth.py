#!/usr/bin/env python3
"""LONDON depth features from the MBP-10 heatmap data (Angus 27-Jul: 295 days of
per-minute book snapshots, data/reference/depth_london/).

Converts each wide MBP-10 snapshot row (10 levels x bid/ask px+sz) into the same
long-form book NY used, then applies the IDENTICAL depth_at semantics from
scripts/trade_matrix.py: thickness, imbalance, spread, support/resist, wall
above/below (max-size visible level) distance+size, 5-min thickness delta.
Adds dep_* columns to output/london_matrix.parquet in place.

`--span holdout` points the same loader at data/reference/depth_london_2023_24 (identical
Databento condensed layout, identical column names) and the holdout matrix. Nothing about
the depth semantics changes between spans.

    python -m scripts.london_depth
    python -m scripts.london_depth --span holdout
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
NY = "America/New_York"

SPANS = {
    "fit": {"dir": "data/reference/depth_london",
            "matrix": "output/london_matrix.parquet", "years": (2025, 2026)},
    "holdout": {"dir": "data/reference/depth_london_2023_24",
                "matrix": "output/london_matrix_holdout.parquet", "years": (2023, 2024)},
    # Forward shadow log: the SAME live depth directory as `fit` — new condensed MBP-10
    # files land there as sessions complete. Only the day set differs, and that is
    # carried by the matrix handed in via --matrix, never by this dict.
    "forward": {"dir": "data/reference/depth_london",
                "matrix": "output/london_matrix_forward.parquet", "years": (2026, 2027)},
}


def load_day(day: str, DIR: Path):
    """day 'YYYY-MM-DD' -> long frame (ts, side, price, size) or None."""
    f = DIR / f"glbx-mdp3-{day.replace('-', '')}.mbp-10_condensed.csv"
    if not f.exists():
        return None
    d = pd.read_csv(f)
    # CLOCK CORRECTION (ported from trunk, 2026-08-07).
    # `ts_event` is FLOORED to the minute by the condensed extraction: ts_recv runs a
    # median 59.895s later (depth_london) / 59.794s (depth_london_2023_24) against ~13us
    # of matching-engine-to-capture latency. The row labelled T is therefore the book at
    # ~T+59.9s, and indexing on the label puts every as-of read ~60 seconds in the FUTURE.
    # `depth_at` below selects `dep.ts <= minute`, so on the raw label that is a
    # ~60-second lookahead on every dep_* column and on the W/FAR/thick/resist veto ladder.
    # docs/FINDING-london-depth-timestamp-lookahead.md.
    #
    # REFUSES rather than warns, and refuses in BOTH directions: applying this correction
    # to a genuine per-instant sample would itself be a 60-second error.
    if "ts_recv" not in d.columns or "ts_in_delta" not in d.columns:
        raise ValueError(f"{f} lacks ts_recv/ts_in_delta; the floored ts_event label "
                         f"cannot be corrected and must not be used as an as-of read")
    lag = (pd.to_datetime(d.ts_recv, utc=True, format="mixed")
           - pd.to_datetime(d.ts_event, utc=True, format="mixed")).dt.total_seconds()
    if lag.median() < 30:
        raise ValueError(
            f"{f}: ts_recv-ts_event median {lag.median():.1f}s, expected ~59.9s. This "
            f"extraction may not be floored; the correction below would become a "
            f"60-second ERROR. Re-verify before use.")
    ts = (pd.to_datetime(d.ts_recv, utc=True, format="mixed")
          - pd.to_timedelta(d.ts_in_delta, unit="ns")).dt.tz_convert(NY)
    rows = []
    for lvl in range(10):
        for side, px, sz in (("bid", f"bid_px_{lvl:02d}", f"bid_sz_{lvl:02d}"),
                             ("ask", f"ask_px_{lvl:02d}", f"ask_sz_{lvl:02d}")):
            rows.append(pd.DataFrame({"ts": ts, "side": side,
                                      "price": d[px], "size": d[sz]}))
    out = pd.concat(rows, ignore_index=True).dropna(subset=["price"])
    return out[out["size"] > 0]


def depth_at(dep, minute, entry, direction):
    """Identical semantics to scripts.trade_matrix.depth_at."""
    sub = dep[dep.ts <= minute]
    if sub.empty:
        return {}
    b = sub[sub.ts == sub.ts.max()]
    bid, ask = b[b.side == "bid"], b[b.side == "ask"]
    if bid.empty or ask.empty:
        return {}
    tb, ta = bid["size"].sum(), ask["size"].sum()
    f = {"dep_thick": tb + ta, "dep_imb": (tb - ta) / max(tb + ta, 1),
         "dep_spread": ask.price.min() - bid.price.max(),
         "dep_support": tb if direction == "long" else ta,
         "dep_resist": ta if direction == "long" else tb}
    f["dep_sup_m_res"] = f["dep_support"] - f["dep_resist"]
    above, below = b[b.price > entry], b[b.price < entry]
    if len(above):
        # explicit tie-break: largest size, then NEAREST price. idxmax alone resolves
        # ties by row position, which is input-order dependent.
        w = above.sort_values(["size", "price"], ascending=[False, True],
                             kind="mergesort").iloc[0]
        f["dep_wall_above_d"] = float(w.price - entry)
        f["dep_wall_above_sz"] = float(w["size"])
    if len(below):
        w = below.sort_values(["size", "price"], ascending=[False, False],
                             kind="mergesort").iloc[0]
        f["dep_wall_below_d"] = float(entry - w.price)
        f["dep_wall_below_sz"] = float(w["size"])
    b5 = dep[dep.ts <= minute - pd.Timedelta(minutes=5)]
    if not b5.empty:
        f["dep_thick_d5m"] = f["dep_thick"] - b5[b5.ts == b5.ts.max()]["size"].sum()
    return f


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--span", choices=sorted(SPANS), default="fit")
    # L3 override: point the identical depth semantics at the rebuild's matrix.
    ap.add_argument("--matrix", default=None, help="override the matrix parquet to annotate")
    a = ap.parse_args()
    spec = dict(SPANS[a.span])
    if a.matrix:
        spec["matrix"] = a.matrix
    DIR = Path(spec["dir"])

    L = pd.read_parquet(spec["matrix"])
    L = L.drop(columns=[c for c in L.columns if c.startswith("dep_")], errors="ignore")
    cache = {}
    rows = []
    for i, t in enumerate(L.itertuples()):
        if t.day not in cache:
            cache[t.day] = load_day(t.day, DIR)
        dep = cache[t.day]
        if dep is None:
            rows.append({})
            continue
        f = pd.Timestamp(t.fill).tz_convert(NY).floor("min")
        # THREE ANCHORS were adopted on trunk 2026-08-05 (ANGUS): the fill-anchored read
        # is contaminated by construction -- a limit fill requires price to have travelled
        # TO the order -- so the tradeable read is the book at ORDER PLACEMENT (the trigger
        # candle's close). Only two of the three are constructible here: this matrix
        # carries no trigger timestamp, so `t_*` needs `trig_ts` threaded down from L2.
        # `p1_*` is the one-minute-earlier fallback and is the closest available to honest.
        r = depth_at(dep, f, t.entry, t.direction)
        r.update({f"p1_{k}": v for k, v in
                  depth_at(dep, f - pd.Timedelta(minutes=1), t.entry, t.direction).items()})
        rows.append(r)
        if (i + 1) % 200 == 0:
            print(f"  {i+1}/{len(L)}", flush=True)
    X = pd.DataFrame(rows, index=L.index)
    out = pd.concat([L, X], axis=1)
    out.to_parquet(spec["matrix"])
    cov = out.dep_thick.notna().sum()
    print(f"wrote {spec['matrix']}: {len(out)} trades, depth on {cov} "
          f"({cov/len(out)*100:.0f}%), {X.shape[1]} dep_ cols")
    long = out.direction == "long"
    D = pd.Series(np.where(long, out.dep_wall_above_d.notna(), out.dep_wall_below_d.notna()),
                  index=out.index).astype(float).where(out.dep_thick.notna())
    for yr in spec["years"]:
        d = out[(out.yr == yr) & D.notna()]
        dd = D[d.index]
        a, b = d[dd == 1], d[dd == 0]
        print(f"  {yr} quick look — wall-ahead exists: WR {(a.dollars>0).mean():.0%} (n={len(a)}) "
              f"vs absent {(b.dollars>0).mean():.0%} (n={len(b)})")


if __name__ == "__main__":
    main()
