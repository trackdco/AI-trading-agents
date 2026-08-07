#!/usr/bin/env python3
"""STRUCTURAL CLUSTERING — Phase 0 item 3.

Replaces the 30-minute same-side window (CLUSTER_GAP_MIN, census A) with a
structural criterion: two same-session same-side triggers are the SAME event
iff price never left the level between them. "Left the level" = an
intervening excursion of at least X*W away from the as-of 15m MA between the
two trigger timestamps (W = earlier trigger's band width).

X is set from the data ONCE, by the declared valley procedure: histogram the
maximum intervening excursion for consecutive same-session same-side trigger
pairs (fit rows only), locate the density valley between the "same fight"
mode near zero and the "separate fights" mass, and read X at the valley.
Time gap is PLOTTED against price gap for the record but the criterion is
excursion-only — time plays no role (that is the point of the replacement).

Outputs: excursion/time-gap table (parquet), the chosen X, and a
structural_cluster_id map keyed (sess_day, t, arm, side, n_attempts) for the
given table.

    python -m scripts.htf_ma_clustering --table output/htf_ma_census/mtable_fit.parquet
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from src.htf_ma.levels import NY, bb_ma_asof                        # noqa: E402


def excursions_for_day(bars: pd.DataFrame, sess_day: str,
                       trigs: pd.DataFrame) -> list[dict]:
    """Max |price - MA|/W between consecutive same-side triggers of one day."""
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t1 = t0 + pd.Timedelta(hours=23)
    hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30)) & (bars.index < t1)]
    if hist.empty:
        return []
    ma15, _ = bb_ma_asof(hist, 15)
    seg = hist[(hist.index >= t0) & (hist.index < t1)]
    idx = seg.index
    hi, lo = seg.high.to_numpy(), seg.low.to_numpy()
    ma = ma15.loc[idx].to_numpy()
    out = []
    for side, g in trigs.groupby("side"):
        g = g.sort_values("t")
        ts = g.t.to_list()
        ws = g.w15.to_list()
        for a in range(len(ts) - 1):
            i0 = int(np.searchsorted(idx.values, ts[a].to_datetime64()))
            i1 = int(np.searchsorted(idx.values, ts[a + 1].to_datetime64()))
            if i1 <= i0:
                continue
            d_hi = np.abs(hi[i0:i1] - ma[i0:i1])
            d_lo = np.abs(lo[i0:i1] - ma[i0:i1])
            exc = float(np.nanmax(np.maximum(d_hi, d_lo))) / ws[a] \
                if ws[a] > 0 else np.nan
            out.append({"sess_day": sess_day, "side": side,
                        "t_a": ts[a], "t_b": ts[a + 1],
                        "gap_min": (ts[a + 1] - ts[a]).total_seconds() / 60.0,
                        "exc_w": exc})
    return out


def assign_structural(trigs: pd.DataFrame, pairs: pd.DataFrame,
                      x: float) -> pd.Series:
    """structural_cluster_id per trigger row: new cluster iff the pair gap
    to the previous same-side trigger had an excursion >= x (in W)."""
    key = {}
    for r in pairs.itertuples():
        key[(r.sess_day, r.side, r.t_b)] = r.exc_w
    ids = []
    for (day, side), g in trigs.groupby(["sess_day", "side"], sort=False):
        g = g.sort_values("t")
        cid = 0
        for i, r in enumerate(g.itertuples()):
            if i > 0:
                exc = key.get((day, side, r.t), np.nan)
                if not np.isfinite(exc) or exc >= x:
                    cid += 1
            ids.append((r.Index, f"{day}:{side}:S{cid}"))
    return pd.Series({i: c for i, c in ids}, name="structural_cluster_id")


def main() -> None:
    table = "output/htf_ma_census/mtable_fit.parquet"
    if "--table" in sys.argv:
        table = sys.argv[sys.argv.index("--table") + 1]
    F = pd.read_parquet(ROOT / table)
    trigs = F[["sess_day", "t", "side", "w15", "arm", "n_attempts"]].copy()
    uniq = trigs.drop_duplicates(["sess_day", "side", "t"])
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close",
                                              "volume"]]
    pairs = []
    days = sorted(uniq.sess_day.unique())
    for k, day in enumerate(days):
        pairs.extend(excursions_for_day(bars, day, uniq[uniq.sess_day == day]))
        if k % 60 == 0:
            print(f"  {k}/{len(days)} days...", flush=True)
    P = pd.DataFrame(pairs)
    P.to_parquet(ROOT / "output/htf_ma_census/cluster_pairs.parquet",
                 index=False)

    e = P.exc_w.dropna()
    print(f"\npairs: {len(P):,} | excursion quantiles (W): "
          + " ".join(f"p{q}={e.quantile(q/100):.2f}"
                     for q in (10, 25, 50, 75, 90)))
    hist_bins = np.arange(0.0, 3.01, 0.1)
    h, edges = np.histogram(e.clip(upper=3.0), bins=hist_bins)
    for i in range(len(h)):
        print(f"  {edges[i]:4.1f}-{edges[i+1]:4.1f}W  {h[i]:5d} "
              + "#" * int(60 * h[i] / max(h.max(), 1)))
    print("\n== time gap x excursion (median gap_min per excursion band) ==")
    P["band"] = pd.cut(P.exc_w, [0, .25, .5, .75, 1, 1.5, 2, 3, 99])
    print(P.groupby("band", observed=True)
           .agg(n=("exc_w", "size"), med_gap=("gap_min", "median"),
                p75_gap=("gap_min", lambda s: s.quantile(.75)))
           .to_string())
    # valley: minimum of the smoothed histogram strictly between the near-zero
    # mode and the separate-fights mass (search 0.2..1.5W)
    smooth = np.convolve(h, np.ones(3) / 3, mode="same")
    lo_i = int(np.argmax(edges[:-1] >= 0.2))
    hi_i = int(np.argmax(edges[:-1] >= 1.5))
    valley_i = lo_i + int(np.argmin(smooth[lo_i:hi_i]))
    x = float(edges[valley_i] + 0.05)
    print(f"\nVALLEY: X = {x:.2f}W (smoothed-min in [0.2, 1.5]W)")

    ids = assign_structural(uniq, P, x)
    uniq2 = uniq.join(ids)
    m = F.merge(uniq2[["sess_day", "side", "t", "structural_cluster_id"]],
                on=["sess_day", "side", "t"], how="left")
    out = Path(table).with_name(Path(table).stem + "_structclust.parquet")
    m[["sess_day", "t", "arm", "side", "n_attempts",
       "structural_cluster_id"]].to_parquet(ROOT / out, index=False)
    n30 = None
    if "cluster_id" in F.columns:
        n30 = F.cluster_id.nunique()
    print(f"clusters: table-native {n30} | structural "
          f"{m.structural_cluster_id.nunique()} | rows {len(F):,}")
    ny = m[m.session.isin(["ny_pre", "ny_rth_am"])] if "session" in m.columns \
        else None
    if ny is not None and len(ny):
        print(f"NY-am rows {len(ny):,}: native clusters "
              f"{ny.cluster_id.nunique() if 'cluster_id' in ny else '?'} | "
              f"structural {ny.structural_cluster_id.nunique()}")
    print(f"map written: {out}")


if __name__ == "__main__":
    main()
