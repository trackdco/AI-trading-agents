#!/usr/bin/env python3
"""E1 — per-locus census report (DECLARATIONS-level-family-census.md §E1.3).

Base rates only. No selection, no cuts, no filters. Every locus is
published whether positive or null.

Structural fights are computed PER LOCUS: two same-session same-side
triggers are one fight unless price left THAT locus by >= X*W between
them. The full X in {0.25, 0.5, 1.0, 2.0}W sensitivity is reported because
A1 showed the convention is worth +-0.2R.

    python -m scripts.htf_ma_level_report [--x 0.5]
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
from scripts.htf_ma_restate import boot_ci                          # noqa: E402
from src.htf_ma.levels import NY, bb_ma_asof                        # noqa: E402

XS = [0.25, 0.5, 1.0, 2.0]
PAIRS = ROOT / "output/htf_ma_census/level_cluster_pairs.parquet"


def build_pairs(F: pd.DataFrame) -> pd.DataFrame:
    """Max excursion away from the LOCUS between consecutive same-side
    triggers, in W units."""
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close",
                                              "volume"]]
    out = []
    days = sorted(F.sess_day.unique())
    for k, day in enumerate(days):
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        t1 = t0 + pd.Timedelta(hours=23)
        hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30))
                    & (bars.index < t1)]
        if hist.empty:
            continue
        ma15, _ = bb_ma_asof(hist, 15)
        seg = hist[(hist.index >= t0) & (hist.index < t1)]
        if seg.empty:
            continue
        idx = seg.index
        hi, lo = seg.high.to_numpy(), seg.low.to_numpy()
        lv = level_series(hist, idx, ma15)
        D = F[F.sess_day == day]
        for locus, g_l in D.groupby("locus"):
            lvl = lv[locus]
            for side, g in g_l.groupby("side"):
                g = g.drop_duplicates("t").sort_values("t")
                ts, ws = g.t.to_list(), g.w15.to_list()
                for a in range(len(ts) - 1):
                    i0 = int(np.searchsorted(idx.values,
                                             pd.Timestamp(ts[a]).to_datetime64()))
                    i1 = int(np.searchsorted(idx.values,
                                             pd.Timestamp(ts[a + 1]).to_datetime64()))
                    if i1 <= i0 or ws[a] <= 0:
                        continue
                    seg_hi = np.abs(hi[i0:i1] - lvl[i0:i1])
                    seg_lo = np.abs(lo[i0:i1] - lvl[i0:i1])
                    m = np.nanmax(np.maximum(seg_hi, seg_lo))
                    out.append({"sess_day": day, "locus": locus, "side": side,
                                "t_b": ts[a + 1], "exc_w": float(m) / ws[a]})
        if k % 60 == 0:
            print(f"  pairs {k}/{len(days)}...", flush=True)
    P = pd.DataFrame(out)
    P.to_parquet(PAIRS, index=False)
    return P


def assign(F: pd.DataFrame, P: pd.DataFrame, x: float) -> pd.Series:
    key = {(r.sess_day, r.locus, r.side, pd.Timestamp(r.t_b)): r.exc_w
           for r in P.itertuples()}
    ids = {}
    for (day, locus, side), g in F.groupby(["sess_day", "locus", "side"],
                                           sort=False):
        g = g.sort_values("t")
        cid, seen = 0, None
        for r in g.itertuples():
            t = pd.Timestamp(r.t)
            if seen is not None and t != seen:
                e = key.get((day, locus, side, t), np.nan)
                if not np.isfinite(e) or e >= x:
                    cid += 1
            seen = t
            ids[r.Index] = f"{day}:{locus}:{side}:S{cid}"
    return pd.Series(ids, name="scid")


def book(F: pd.DataFrame, arm: str) -> pd.DataFrame:
    R = F[(F.arm == arm) & F.out_ship.notna() & (F.risk > 0)]
    if arm == "break":
        R = R[R.retested.astype("boolean").fillna(False)]
    return R.sort_values("t").groupby("scid", as_index=False).first()


def main() -> None:
    F = pd.read_parquet(ROOT / "output/htf_ma_census/levels_fit.parquet")
    F["era"] = np.where(F.sess_day < "2026-01-01", "H2-2025", "H1-2026")
    ndays = F.sess_day.nunique()
    P = pd.read_parquet(PAIRS) if PAIRS.exists() else build_pairs(F)

    print(f"LEVEL-FAMILY CENSUS — fit {F.sess_day.min()}..{F.sess_day.max()}, "
          f"{ndays} days, {len(F):,} triggers\n")
    print("== raw trigger counts (no clustering) ==")
    print(F.groupby(["locus", "arm"]).size().unstack(fill_value=0).to_string())

    for arm in ("reject", "break"):
        print(f"\n{'='*78}\n== {arm.upper()} ARM — executable first-of-fight "
              f"book, shipped exit ==\n{'='*78}")
        for x in XS:
            F2 = F.join(assign(F, P, x))
            tag = "  <-- DECLARED" if x == 0.5 else ""
            print(f"\n-- X = {x:.2f}W{tag}")
            print(f"{'locus':9s} {'fights':>7s} {'/day':>5s} "
                  f"{'EV pooled':>10s} | {'H2-2025 [day-boot 95]':>26s} | "
                  f"{'H1-2026 [day-boot 95]':>26s}")
            for locus in LOCI:
                b = book(F2[F2.locus == locus], arm)
                if len(b) < 30:
                    print(f"{locus:9s} {len(b):7d}   UNDERPOWERED (<30 fights)")
                    continue
                cells = {}
                for era, g in b.groupby("era"):
                    if len(g) < 15:
                        cells[era] = "UNDERPOWERED"
                        continue
                    lo, hi = boot_ci(g, "out_ship",
                                     lambda s: s.out_ship.mean())
                    star = "!" if (lo > 0 or hi < 0) else " "
                    cells[era] = f"{g.out_ship.mean():+.3f} [{lo:+.3f},{hi:+.3f}]{star}"
                print(f"{locus:9s} {len(b):7d} {len(b)/ndays:5.2f} "
                      f"{b.out_ship.mean():+10.3f} | "
                      f"{cells.get('H2-2025','—'):>26s} | "
                      f"{cells.get('H1-2026','—'):>26s}")

        F2 = F.join(assign(F, P, 0.5))
        print(f"\n-- MFE in R at the declared X=0.5W ({arm}) --")
        for locus in LOCI:
            b = book(F2[F2.locus == locus], arm)
            b = b[b.mfe_r.notna()]
            if len(b) < 30:
                continue
            q = b.mfe_r.quantile
            print(f"  {locus:9s} p50 {q(.50):5.2f} | p75 {q(.75):5.2f} | "
                  f"p90 {q(.90):6.2f} | p95 {q(.95):6.2f} | "
                  f"stop_W p50 {(b.risk/b.w15).median():.3f}")

    print("\n== E1.4 BAR: EV>0 with day-boot CI clear of zero in BOTH eras at "
          "X=0.5W, AND sign holding at a majority of the four X values ==")
    for arm in ("reject", "break"):
        for locus in LOCI:
            signs, both = [], False
            for x in XS:
                b = book(F.join(assign(F, P, x))[lambda d: d.locus == locus],
                         arm)
                if len(b) < 30:
                    signs.append(np.nan)
                    continue
                signs.append(np.sign(b.out_ship.mean()))
                if x == 0.5:
                    ok = []
                    for era, g in b.groupby("era"):
                        if len(g) < 15:
                            ok.append(False)
                            continue
                        lo, hi = boot_ci(g, "out_ship",
                                         lambda s: s.out_ship.mean())
                        ok.append(lo > 0)
                    both = len(ok) == 2 and all(ok)
            pos = np.nansum([s > 0 for s in signs])
            verdict = "FOLLOW-UP EARNED" if (both and pos >= 3) else "park (base rate published)"
            print(f"  {arm:7s} {locus:9s} both-era-CI>0 at 0.5W: {both} | "
                  f"positive at {int(pos)}/4 X values -> {verdict}")


if __name__ == "__main__":
    main()
