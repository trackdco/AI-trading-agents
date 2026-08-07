#!/usr/bin/env python3
"""RESTATEMENT — Phase 0 item 4.

Re-derives, from a given M-TABLE fit parquet, the three numbers the
base-rate library leans on, with day-level bootstrap CIs (seed 20260807,
2,000 draws — the D4 aggregation rule):

  1. median stop width in W (reject arm, risk/w15)
  2. the MFE-in-R table (reject arm, by era)
  3. the unselected reject book under the adopted exit (mean out_ship,
     cluster-collapsed), by era and pooled

Run on the pre-fix table and the post-fix table; the diff IS the item-4
deliverable. Optionally pass --clusters <map.parquet> to collapse on
structural clusters instead of the table-native cluster_id.

    python -m scripts.htf_ma_restate --table <fit.parquet> [--clusters <map>]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SEED, DRAWS = 20260807, 2000


def boot_ci(day_vals: pd.Series, stat=np.mean, seed=SEED, draws=DRAWS):
    """Day-level bootstrap: day_vals indexed by sess_day (one value per day,
    already collapsed within day). Returns (lo, hi) 95% percentile CI."""
    rng = np.random.default_rng(seed)
    v = day_vals.to_numpy()
    n = len(v)
    stats = [stat(v[rng.integers(0, n, n)]) for _ in range(draws)]
    return float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))


def era_of(day: str) -> str:
    return "H2-2025" if day < "2026-01-01" else "H1-2026"


def main() -> None:
    table = "output/htf_ma_census/mtable_fit.parquet"
    cl_map = None
    if "--table" in sys.argv:
        table = sys.argv[sys.argv.index("--table") + 1]
    if "--clusters" in sys.argv:
        cl_map = sys.argv[sys.argv.index("--clusters") + 1]
    F = pd.read_parquet(ROOT / table)
    ccol = "cluster_id"
    if cl_map:
        M = pd.read_parquet(ROOT / cl_map)
        F = F.merge(M, on=["sess_day", "t", "arm", "side", "n_attempts"],
                    how="left")
        ccol = "structural_cluster_id"
    F["era"] = F.sess_day.map(era_of)
    R = F[(F.arm == "reject") & F.risk.notna() & (F.risk > 0)
          & F.w15.notna() & (F.w15 > 0)].copy()
    R["stop_w"] = R.risk / R.w15
    print(f"table: {table} | reject rows with geometry: {len(R):,} | "
          f"collapse: {ccol}")

    print("\n== 1. stop width in W (reject) ==")
    for era, g in R.groupby("era"):
        q = g.stop_w.quantile
        dmed = g.groupby("sess_day").stop_w.median()
        lo, hi = boot_ci(dmed, np.median)
        print(f"  {era}: p25 {q(.25):.3f} | p50 {q(.50):.3f} "
              f"[{lo:.3f},{hi:.3f}] | p75 {q(.75):.3f}  (n={len(g):,})")
    q = R.stop_w.quantile
    print(f"  pooled: p25 {q(.25):.3f} | p50 {q(.50):.3f} | p75 {q(.75):.3f}")

    print("\n== 2. MFE in R (reject, rows with valid risk) ==")
    Rm = R[R.mfe_r.notna()]
    for era, g in Rm.groupby("era"):
        q = g.mfe_r.quantile
        print(f"  {era}: p50 {q(.50):.2f} | p75 {q(.75):.2f} | "
              f"p90 {q(.90):.2f} | p95 {q(.95):.2f} | max {g.mfe_r.max():.1f} "
              f"(n={len(g):,})")

    print("\n== 3. unselected reject book, adopted exit (out_ship) ==")
    Rs = R[R.out_ship.notna()]
    for era, g in Rs.groupby("era"):
        cm = g.groupby(ccol).out_ship.mean()
        dm = g.groupby("sess_day").out_ship.mean()
        lo, hi = boot_ci(dm)
        print(f"  {era}: cluster-collapsed mean {cm.mean():+.3f}R | "
              f"day-boot 95% [{lo:+.3f},{hi:+.3f}] | rows {len(g):,} | "
              f"clusters {g[ccol].nunique():,}")
    cm = Rs.groupby(ccol).out_ship.mean()
    dm = Rs.groupby("sess_day").out_ship.mean()
    lo, hi = boot_ci(dm)
    print(f"  pooled: cluster-collapsed mean {cm.mean():+.3f}R | day-boot "
          f"95% [{lo:+.3f},{hi:+.3f}] | rows {len(Rs):,}")
    print("\n(also for reference) hold / trail-only pooled, cluster-collapsed:")
    for col in ("out_hold", "out_trail"):
        s = R[R[col].notna()]
        print(f"  {col}: {s.groupby(ccol)[col].mean().mean():+.3f}R "
              f"(rows {len(s):,})")


if __name__ == "__main__":
    main()
