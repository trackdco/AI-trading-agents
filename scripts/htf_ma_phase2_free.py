#!/usr/bin/env python3
"""PHASE 2 — free numbers already sitting in the table (handoff items 9-11).

Fit rows only. No holdout contact. Declarations, made before any number
below existed (standing rule):

ITEM 9   P(retest | break) by era x side, day-boot CI; and the travel
         distribution of NON-retested breaks: reference = ma_px at the cross
         decision bar, direction = break direction, travel = max favorable
         excursion (d*(extreme-ref))/w15 from the first bar after the
         decision to session close. This is the opportunity cost of
         demanding a retest — descriptive, no bar to pass.
ITEM 10  Confluence sign SEPARATELY BY ARM. PREDICTION DECLARED IN ADVANCE
         (handoff): opposite signs — at the level confluence is a wall
         (helps rejections); beyond a broken level it is obstacles (hurts
         break-retests). Currencies, both read (dual-currency law):
         hit = censusB target_before_extreme_20 by confluence_count bin
         {1, 2, 3+}; R = Spearman rho of confluence_count vs out_ship on
         entered rows (mtable join). Read per era.
ITEM 11  Persistence at n>=5 — the range the old cap truncated (144 events).
         continuation_1w = (mfe_r * risk >= w15) on reject rows (did price
         travel >=1W favorable from entry before the stop); out_ship as the
         R currency. Bands declared: 1,2,3,4,5,6+. The BR-5 null predicts
         flat; the declared read is whether the null EXTENDS to n>=5.

    python -m scripts.htf_ma_phase2_free [--table <fit.parquet>]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.htf_ma_restate import boot_ci, era_of                  # noqa: E402
from src.htf_ma.levels import NY                                    # noqa: E402


def rho_rank(a: pd.Series, b: pd.Series) -> float:
    m = a.notna() & b.notna()
    if m.sum() < 10:
        return np.nan
    return float(a[m].rank().corr(b[m].rank()))


def nonretest_travel(bars: pd.DataFrame, brk: pd.DataFrame) -> pd.Series:
    """Max favorable excursion in W from ma_px, first post-decision bar to
    session close, for non-retested break rows."""
    out = {}
    for day, g in brk.groupby("sess_day"):
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        t1 = t0 + pd.Timedelta(hours=23)
        seg = bars[(bars.index >= t0) & (bars.index < t1)]
        if seg.empty:
            continue
        idx = seg.index
        hi, lo = seg.high.to_numpy(), seg.low.to_numpy()
        for r in g.itertuples():
            j0 = int(np.searchsorted(idx.values,
                                     pd.Timestamp(r.t).to_datetime64()))
            if j0 >= len(idx):
                continue
            d = int(r.direction)
            ext = hi[j0:] if d > 0 else lo[j0:]
            trav = float(np.max(d * (ext - r.ma_px)))
            out[r.Index] = max(trav, 0.0) / r.w15 if r.w15 > 0 else np.nan
    return pd.Series(out, name="travel_noretest_W")


def main() -> None:
    table = "output/htf_ma_census/mtable_fit.parquet"
    if "--table" in sys.argv:
        table = sys.argv[sys.argv.index("--table") + 1]
    F = pd.read_parquet(ROOT / table)
    F["era"] = F.sess_day.map(era_of)
    B = pd.read_parquet(ROOT / "output/htf_ma_census/censusB_fit.parquet")
    B["era"] = B.sess_day.map(era_of)

    # ---------------- ITEM 9 ------------------------------------------------
    print("== ITEM 9: P(retest | break), fit ==")
    brk = F[F.arm == "break"].copy()
    for (era, side), g in brk.groupby(["era", "side"]):
        p = g.retested.mean()
        lo, hi = boot_ci(g, "retested", lambda s: s.retested.mean())
        print(f"  {era} {side}: {p*100:5.1f}% [{lo*100:.1f},{hi*100:.1f}] "
              f"n={len(g):,}")
    p = brk.retested.mean()
    lo, hi = boot_ci(brk, "retested", lambda s: s.retested.mean())
    print(f"  pooled: {p*100:5.1f}% [{lo*100:.1f},{hi*100:.1f}] n={len(brk):,}")

    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close",
                                              "volume"]]
    nr = brk[~brk.retested.astype(bool)]
    tv = nonretest_travel(bars, nr)
    nr = nr.join(tv)
    print(f"\n  travel of NON-retested breaks (W from ma_px), n={tv.notna().sum():,}:")
    for era, g in nr.groupby("era"):
        q = g.travel_noretest_W.quantile
        print(f"  {era}: p25 {q(.25):.2f} | p50 {q(.50):.2f} | p75 {q(.75):.2f} "
              f"| p90 {q(.90):.2f} | p95 {q(.95):.2f}")
    print("  (same stat for RETESTED breaks' mfe_r*risk/w15 — comparability):")
    rt = brk[brk.retested.astype(bool) & brk.mfe_r.notna() & (brk.risk > 0)]
    rt = rt.assign(trav_w=rt.mfe_r * rt.risk / rt.w15)
    for era, g in rt.groupby("era"):
        q = g.trav_w.quantile
        print(f"  {era}: p25 {q(.25):.2f} | p50 {q(.50):.2f} | p75 {q(.75):.2f} "
              f"| p90 {q(.90):.2f} | p95 {q(.95):.2f}")

    # ---------------- ITEM 10 -----------------------------------------------
    print("\n== ITEM 10: confluence sign BY ARM "
          "(declared prediction: reject +, break −) ==")
    key = ["sess_day", "t", "side", "n_attempts"]
    Fk = F.merge(B[key + ["kind", "confluence_count",
                          "target_before_extreme_20"]],
                 left_on=key + ["arm"], right_on=key + ["kind"], how="left")
    print("  [hit currency] censusB target_before_extreme_20 by confluence bin:")
    Bv = B[B.target_before_extreme_20.notna()].copy()
    Bv["cbin"] = pd.cut(Bv.confluence_count, [0, 1, 2, 99],
                        labels=["1", "2", "3+"])
    for (kind, era), g in Bv.groupby(["kind", "era"]):
        cells = " | ".join(
            f"{b}: {gg.target_before_extreme_20.mean()*100:4.1f}% n={len(gg)}"
            for b, gg in g.groupby("cbin", observed=True))
        print(f"    {kind:7s} {era}: {cells}")
    print("  [R currency] Spearman confluence_count vs out_ship (entered rows):")
    for (arm, era), g in Fk[Fk.out_ship.notna()
                            & Fk.confluence_count.notna()].groupby(["arm", "era"]):
        r = rho_rank(g.confluence_count, g.out_ship)
        lo, hi = boot_ci(g, "out_ship",
                         lambda s: rho_rank(s.confluence_count, s.out_ship))
        print(f"    {arm:7s} {era}: rho {r:+.3f} [{lo:+.3f},{hi:+.3f}] "
              f"n={len(g):,}")

    # ---------------- ITEM 11 -----------------------------------------------
    print("\n== ITEM 11: persistence, uncapped (declared bands 1..4,5,6+) ==")
    R = F[(F.arm == "reject") & F.risk.notna() & (F.risk > 0)].copy()
    R["cont_1w"] = R.mfe_r * R.risk >= R.w15
    R["nband"] = np.where(R.n_attempts >= 6, "6+",
                          np.where(R.n_attempts == 5, "5",
                                   R.n_attempts.astype(str)))
    print(f"  n_attempts>=5 rows: {len(R[R.n_attempts>=5]):,} "
          f"(the population the old cap discarded)")
    for era, g in R.groupby("era"):
        cells = " | ".join(
            f"{b}: {gg.cont_1w.mean()*100:4.1f}%/{gg.out_ship.mean():+.2f}R "
            f"n={len(gg)}"
            for b, gg in g.groupby("nband")
            if len(gg) >= 5)
        print(f"  {era}: {cells}")
    print("  (cells are continuation_1w% / mean out_ship R)")


if __name__ == "__main__":
    main()
