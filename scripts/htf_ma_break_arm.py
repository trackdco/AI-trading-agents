#!/usr/bin/env python3
"""E2 — BREAK ARM, clean first measurement (declarations §E2).

The break arm is a third of the population, has never been measured on its
own terms since the row-existence fix, and its headline was invalidated so
there is nothing to un-learn. This is a FIRST measurement, not a re-run.

Deliverables (declared):
  1. executable break book (first-of-fight, retested) under the shipped
     exit: EV/fight, era split, day-boot CIs, at all four X values --
     the break-arm counterpart of BR-9, which does not exist yet
  2. P(retest|break) and the non-retested travel distribution, restated
     on the fixed table, reported ALONGSIDE the book
  3. cadence and geometry needed to judge "frequency without size"

    python -m scripts.htf_ma_break_arm
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.htf_ma_clustering import assign_structural             # noqa: E402
from scripts.htf_ma_restate import boot_ci                          # noqa: E402

XS = [0.25, 0.5, 1.0, 2.0]


def main() -> None:
    F = pd.read_parquet(ROOT / "output/htf_ma_census/mtable_fit.parquet")
    F["era"] = np.where(F.sess_day < "2026-01-01", "H2-2025", "H1-2026")
    P = pd.read_parquet(ROOT / "output/htf_ma_census/cluster_pairs.parquet")
    uniq = F[["sess_day", "t", "side", "w15", "arm",
              "n_attempts"]].drop_duplicates(["sess_day", "side", "t"])
    ndays = F.sess_day.nunique()

    print(f"E2 — BREAK ARM, fit span, {ndays} days")
    B = F[F.arm == "break"]
    print(f"  raw break triggers: {len(B):,} | reject triggers: "
          f"{(F.arm=='reject').sum():,} "
          f"(break = {len(B)/len(F)*100:.0f}% of the population)")

    print("\n== 2. P(retest | break) and the cost of demanding a retest ==")
    p = B.retested.mean()
    lo, hi = boot_ci(B, "retested", lambda s: s.retested.mean())
    print(f"  pooled P(ever-retest) = {p*100:.1f}% [{lo*100:.1f},{hi*100:.1f}]")
    for era, g in B.groupby("era"):
        lo2, hi2 = boot_ci(g, "retested", lambda s: s.retested.mean())
        print(f"    {era}: {g.retested.mean()*100:.1f}% "
              f"[{lo2*100:.1f},{hi2*100:.1f}] n={len(g):,}")
    nr = B[~B.retested.astype(bool)]
    print(f"  never-retested: n={len(nr)} ({len(nr)/len(B)*100:.1f}%) — the "
          f"branch's opportunity cost (they escape without offering the entry)")

    print("\n== 1. EXECUTABLE BREAK BOOK (first-of-fight, retested), "
          "shipped exit ==")
    print(f"{'X':>6s} {'fights':>7s} {'/day':>5s} {'EV pooled':>10s} | "
          f"{'H2-2025 [day-boot 95]':>27s} | {'H1-2026 [day-boot 95]':>27s}")
    for x in XS:
        ids = assign_structural(uniq, P, x)
        u2 = uniq.join(ids)
        F2 = F.merge(u2[["sess_day", "side", "t", "structural_cluster_id"]],
                     on=["sess_day", "side", "t"], how="left")
        R = F2[(F2.arm == "break") & F2.retested.astype("boolean").fillna(False)
               & F2.out_ship.notna() & (F2.risk > 0)].sort_values("t")
        bk = R.groupby("structural_cluster_id", as_index=False).first()
        cells = {}
        for era, g in bk.groupby("era"):
            lo3, hi3 = boot_ci(g, "out_ship", lambda s: s.out_ship.mean())
            star = "!" if (lo3 > 0 or hi3 < 0) else " "
            cells[era] = f"{g.out_ship.mean():+.3f} [{lo3:+.3f},{hi3:+.3f}]{star}"
        tag = "  <-- DECLARED" if x == 0.5 else ""
        print(f"{x:6.2f} {len(bk):7d} {len(bk)/ndays:5.2f} "
              f"{bk.out_ship.mean():+10.3f} | {cells.get('H2-2025','—'):>27s} | "
              f"{cells.get('H1-2026','—'):>27s}{tag}")

    ids = assign_structural(uniq, P, 0.5)
    u2 = uniq.join(ids)
    F2 = F.merge(u2[["sess_day", "side", "t", "structural_cluster_id"]],
                 on=["sess_day", "side", "t"], how="left")
    R = F2[(F2.arm == "break") & F2.retested.astype("boolean").fillna(False)
           & F2.out_ship.notna() & (F2.risk > 0)].sort_values("t")
    bk = R.groupby("structural_cluster_id", as_index=False).first()
    print("\n== 3. geometry and cadence at the declared X=0.5W ==")
    q = bk.mfe_r.quantile
    print(f"  MFE in R: p50 {q(.50):.2f} | p75 {q(.75):.2f} | p90 {q(.90):.2f}"
          f" | p95 {q(.95):.2f}")
    print(f"  stop width in W: p25 {(bk.risk/bk.w15).quantile(.25):.3f} | "
          f"p50 {(bk.risk/bk.w15).median():.3f} | "
          f"p75 {(bk.risk/bk.w15).quantile(.75):.3f}")
    print(f"  win rate (out_ship>0): {(bk.out_ship>0).mean()*100:.1f}%")
    print(f"  fights/day {len(bk)/ndays:.2f}  vs reject arm 6.3/day "
          f"(BR-9) — 'frequency without size' check")
    print("  other exits, same book: "
          f"trail {bk.out_trail.mean():+.3f}R | hold {bk.out_hold.mean():+.3f}R")
    for era, g in bk.groupby("era"):
        print(f"    {era}: n={len(g)} ship {g.out_ship.mean():+.3f} "
              f"trail {g.out_trail.mean():+.3f}")


if __name__ == "__main__":
    main()
