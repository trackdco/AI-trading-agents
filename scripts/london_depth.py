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
}


def load_day(day: str, DIR: Path):
    """day 'YYYY-MM-DD' -> long frame (ts, side, price, size) or None.

    `ts` is the TRUE observation time, not `ts_event`. The condensed extraction FLOORS
    `ts_event` to the minute: `ts_recv - ts_event` runs a median 59.889s (p1 58.193s,
    95.9% inside [59s,60s)) against ~13us of matching-engine-to-capture latency, so the
    row labelled T is the book at ~T+59.9s -- the END of minute T.

    The 2026-08-05 audit in `build_l3_features_london.py` asked exactly the right
    question here and got the right measurements ("depth mid at T vs close of bar T ->
    median |err| 0.25 pt"), but concluded "no lookahead" from a premise about a DIFFERENT
    file: it took the 1m bars to be close-labelled. They are start-labelled
    (`data/reference/parity_slice_feb2026.md`; footprint trades stamped T fall inside bar
    T on 98.1% of 42,230 minutes against 17.5% for the alternative). Under the correct
    premise the same numbers say the snapshot at label T is the book at T+1min.
    `ts_recv` settles it without needing bars at all.
    """
    f = DIR / f"glbx-mdp3-{day.replace('-', '')}.mbp-10_condensed.csv"
    if not f.exists():
        return None
    d = pd.read_csv(f)
    if "ts_recv" not in d.columns:
        raise ValueError(f"{f} has no ts_recv; cannot correct the floored ts_event label")
    lag = (pd.to_datetime(d.ts_recv, utc=True, format="mixed")
           - pd.to_datetime(d.ts_event, utc=True, format="mixed")).dt.total_seconds()
    if lag.median() < 30:
        raise ValueError(
            f"{f}: ts_recv-ts_event median {lag.median():.1f}s, expected ~59.9s. The "
            f"floored-label correction below would become a 60-second ERROR on a genuine "
            f"per-instant sample. Re-verify before use.")
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
    # EXPLICIT TIE-BREAK: largest size, then NEAREST price to the entry.
    #
    # `idxmax` alone resolves a size tie by ROW POSITION, which is input-order dependent
    # -- the same book fed in a different row order yields a different wall. NQ's London
    # book is thin (median 3 contracts a level, 10 levels spanning ~2.25 pts), so exact
    # size ties are common rather than exotic: measured on the 749-fill fit matrix, the
    # two rules disagree on 180 rows, and on every one of those the wall SIZE is
    # identical -- they are pure ties. 45 rows get a different wall DISTANCE and 9 of
    # them flip the `FAR = wall_ahead_d > 4.5` gate condition.
    #
    # Ported from the rev-3 lineage (origin/claude/agent-capture-london), which carried
    # this fix from 2026-08-03 while trunk did not. Found 2026-08-07 while porting
    # trunk's clock correction the other way; a wholesale port would have regressed it.
    # `kind="mergesort"` is required -- it is the only stable sort pandas offers, and an
    # unstable sort re-introduces the same order dependence one layer down.
    if len(above):
        w = above.sort_values(["size", "price"], ascending=[False, True],
                              kind="mergesort").iloc[0]
        f["dep_wall_above_d"] = float(w.price - entry)
        f["dep_wall_above_sz"] = float(w["size"])
    if len(below):
        w = below.sort_values(["size", "price"], ascending=[False, False],
                              kind="mergesort").iloc[0]
        f["dep_wall_below_d"] = float(entry - w.price)
        f["dep_wall_below_sz"] = float(w["size"])
    # BIASED — DO NOT READ AS FLOW (flagged 2026-08-06, Phase 4 inventory).
    # This is the NET depth change across two snapshots five minutes apart, and the
    # London depth extraction retains one row per minute out of a median 23,654 book
    # events. So this differences across ~118,000 unobserved additions, cancellations
    # and executions and keeps only the residual. Cont-Kukanov-Stoikov's identity is
    # that a market sell and a cancelled buy of the same size have the SAME effect on
    # the queue, so a net change cannot separate "book building" from "cancellations
    # happened to net positive" — which is exactly the reading
    # docs/PREREG-london-depth-pass.md §62 declares for the BUILD arm.
    # Kept because a committed artifact (output/london_obk_depth.parquet) already
    # contains it; it must not be used as a flow proxy without that caveat attached.
    # The sound alternative at this resolution is a book LEVEL, not a book DIFFERENCE:
    # see src/engine/book.py.
    b5 = dep[dep.ts <= minute - pd.Timedelta(minutes=5)]
    if not b5.empty:
        f["dep_thick_d5m_BIASED"] = f["dep_thick"] - b5[b5.ts == b5.ts.max()]["size"].sum()
        f["dep_thick_d5m"] = f["dep_thick_d5m_BIASED"]   # legacy name, same value
    return f


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--span", choices=sorted(SPANS), default="fit")
    a = ap.parse_args()
    spec = SPANS[a.span]
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
        rows.append(depth_at(dep, f, t.entry, t.direction))
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
