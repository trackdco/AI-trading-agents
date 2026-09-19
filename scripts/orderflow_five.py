#!/usr/bin/env python3
"""THE FIVE ORDER-FLOW MEASURES AT ENTRY — pre-declared test.

Declaration: docs/DECLARATIONS-orderflow-five.md (committed before this
build). NOT a search: the trader named these five in advance.

  1 WALL_AHEAD  a depth wall exists AHEAD of entry (in the trade's path)
  2 WALLSZ      that ahead-wall >= 7.0 contracts (canon Q_WALLSZ_MIN)
  3 CVD_CONF    d15_conf == 1
  4 FILL_DELTA  thru_delta_conf == 1
  5 NO_OPP      bp5opp == 0

The ahead/behind wall split is NOT in any existing parquet (earlier work
saved only the support side, i.e. the wall BEHIND). It is rebuilt here
from the depth books at the entry minute — causal, since these are
market orders sent at the trigger candle's close.

    python -m scripts.orderflow_five [--build]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.htf_ma_flow_depth_run import depth_index, load_book_frames  # noqa: E402
from src.htf_ma.levels import NY                                        # noqa: E402

WIDE = ROOT / "output/htf_ma_census/race_wide.parquet"
RUNS = ROOT / "output/htf_ma_census/race_runs.parquet"
REAL = ROOT / "output/htf_ma_census/race_realexit.parquet"
FLOW = ROOT / "output/htf_ma_census/race_flow_feats_entry.parquet"
OUT = ROOT / "output/htf_ma_census/orderflow_five.parquet"
Q_WALLSZ_MIN = 7.0            # canon threshold, taken as-is
SEED, DRAWS = 20260807, 2000
BAR_P3R = 0.283               # what the real exit needs to break even
NAMES = ["WALL_AHEAD", "WALLSZ", "CVD_CONF", "FILL_DELTA", "NO_OPP"]


def build_walls(B):
    """Ahead/behind wall features at the entry minute, per fight."""
    didx = depth_index()
    rows = []
    days = sorted(B.sess_day.unique())
    for k, day in enumerate(days):
        D = B[B.sess_day == day]
        books = load_book_frames(didx[day]) if day in didx else None
        if not books:
            for r in D.itertuples():
                rows.append({"scid": r.scid, "wall_ahead_d": np.nan,
                             "wall_ahead_sz": np.nan,
                             "wall_behind_d": np.nan})
            continue
        keys = sorted(books)
        for r in D.itertuples():
            t = pd.Timestamp(r.t)
            kk = [x for x in keys if x <= t]        # as-of, never after
            if not kk:
                rows.append({"scid": r.scid, "wall_ahead_d": np.nan,
                             "wall_ahead_sz": np.nan,
                             "wall_behind_d": np.nan})
                continue
            b = books[kk[-1]]
            e, d = float(r.entry), int(r.direction)
            below, above = b[b.price < e], b[b.price > e]
            bd = bsz = ad = asz = np.nan
            if len(below):
                w = below.loc[below["size"].idxmax()]
                bd, bsz = float(e - w.price), float(w["size"])
            if len(above):
                w = above.loc[above["size"].idxmax()]
                ad, asz = float(w.price - e), float(w["size"])
            # AHEAD = in the trade's path (above for a long, below for a
            # short) — the canon's `D`. BEHIND is the support side.
            if d > 0:
                a_d, a_sz, b_d = ad, asz, bd
            else:
                a_d, a_sz, b_d = bd, bsz, ad
            rows.append({"scid": r.scid, "wall_ahead_d": a_d,
                         "wall_ahead_sz": a_sz, "wall_behind_d": b_d})
        if k % 50 == 0:
            print(f"  walls {k}/{len(days)}...", flush=True)
    return pd.DataFrame(rows)


def dboot(df, col, draws=DRAWS):
    g = df.groupby("sess_day")[col].agg(["sum", "count"])
    s, n = g["sum"].to_numpy(), g["count"].to_numpy()
    if len(s) < 3:
        return np.nan, np.nan
    rng = np.random.default_rng(SEED)
    i = rng.integers(0, len(s), (draws, len(s)))
    c = n[i].sum(1)
    st = np.divide(s[i].sum(1), c, out=np.full(draws, np.nan), where=c > 0)
    return (float(np.nanpercentile(st, 2.5)),
            float(np.nanpercentile(st, 97.5)))


def main() -> None:
    B = pd.read_parquet(WIDE)
    B["t"] = pd.to_datetime(B.t)
    R = pd.read_parquet(RUNS)
    X = pd.read_parquet(REAL)[["scid", "real_out"]]
    M = B.merge(R, on="scid").merge(X, on="scid")

    if "--build" in sys.argv or not OUT.exists():
        W = build_walls(M[["scid", "sess_day", "t", "entry", "direction"]])
        W.to_parquet(OUT, index=False)
        print(f"written: {OUT.name} ({len(W)} rows)")
    W = pd.read_parquet(OUT)
    M = M.merge(W, on="scid")

    # ---- the five, all oriented to the trade
    M["WALL_AHEAD"] = M.wall_ahead_d.notna().astype(float)
    M.loc[M.wall_ahead_d.isna() & M.wall_behind_d.isna(),
          "WALL_AHEAD"] = np.nan                      # no book at all
    M["WALLSZ"] = np.where(M.wall_ahead_sz.notna(),
                           (M.wall_ahead_sz >= Q_WALLSZ_MIN).astype(float),
                           np.nan)
    M["CVD_CONF"] = (M.d15_conf >= 1).astype(float).where(M.d15_conf.notna())
    M["FILL_DELTA"] = (M.thru_delta_conf >= 1).astype(float) \
        .where(M.thru_delta_conf.notna())
    M["NO_OPP"] = (M.bp5opp <= 0).astype(float).where(M.bp5opp.notna())
    M["reach3"] = (M.run_mfe_r >= 3).astype(float)
    M["win"] = (M.real_out > 0).astype(float)

    print("\n" + "=" * 100)
    print("COVERAGE AND FIRE RATES (pre-declared five; no search)")
    print("=" * 100)
    print(f"   {'measure':12s} {'coverage':>9s} {'fires':>7s}  "
          f"{'fires ALONE (of the 5)':>24s}")
    fired = M[NAMES].fillna(0)
    n_on = fired.sum(axis=1)
    for nm in NAMES:
        cov = M[nm].notna().mean() * 100
        fr = M[nm].mean() * 100
        alone = ((fired[nm] == 1) & (n_on == 1)).sum()
        print(f"   {nm:12s} {cov:8.1f}% {fr:6.1f}% {alone:9d} fights "
              f"({alone/len(M)*100:.1f}%)")
    print(f"\n   how many of the five fire at once: " + "  ".join(
        f"{int(k)}:{int(v)}" for k, v in n_on.value_counts().sort_index().items()))

    base = M.reach3.mean()
    print(f"\n   BASELINE P(3R) = {base*100:.1f}%   "
          f"(bar for the real exit = {BAR_P3R*100:.1f}%)")

    def row(g, label, note=""):
        if len(g) < 25 or g.sess_day.nunique() < 15:
            print(f"   {label:34s} n={len(g):4d} d={g.sess_day.nunique():3d}"
                  f"  THIN {note}")
            return
        lo, hi = dboot(g, "reach3")
        loe, hie = dboot(g, "real_out")
        flag = "  <<<" if lo > BAR_P3R else ""
        print(f"   {label:34s} n={len(g):4d} d={g.sess_day.nunique():3d} "
              f"P3R {g.reach3.mean()*100:5.1f}% [{lo*100:4.1f},{hi*100:5.1f}] "
              f"win {g.win.mean()*100:5.1f}%  EV {g.real_out.mean():+6.3f} "
              f"[{loe:+.2f},{hie:+.2f}]{flag}{note}")

    for mech in ("M1", "M2", "M3"):
        Mm = M[M.mech == mech]
        print("\n" + "=" * 100)
        print(f"SETUP TYPE {mech}  (n={len(Mm)}, never pooled with the "
              f"others)   baseline P3R {Mm.reach3.mean()*100:.1f}%  "
              f"EV {Mm.real_out.mean():+.3f}")
        print("=" * 100)
        print("   -- each measure ALONE (fired vs not) --")
        for nm in NAMES:
            g = Mm[Mm[nm] == 1]
            row(g, f"{nm} fired")
        print("   -- pairs (both fired) --")
        for i in range(len(NAMES)):
            for j in range(i + 1, len(NAMES)):
                a, b = NAMES[i], NAMES[j]
                g = Mm[(Mm[a] == 1) & (Mm[b] == 1)]
                row(g, f"{a} + {b}")
        print("   -- the full stack --")
        g = Mm[(Mm[NAMES] == 1).all(axis=1)]
        row(g, "ALL FIVE")
        for k in (4, 3):
            g = Mm[Mm[NAMES].fillna(0).sum(axis=1) >= k]
            row(g, f">= {k} of five")

    print("\n" + "=" * 100)
    print("SAME, BY SESSION (secondary; the mechanism split above is the "
          "declared primary)")
    print("=" * 100)
    for s in ("LONDON", "NY_PRE", "NY_AM"):
        Ms = M[M.session == s]
        print(f"\n   {s}  baseline P3R {Ms.reach3.mean()*100:.1f}%")
        for nm in NAMES:
            row(Ms[Ms[nm] == 1], f"   {nm} fired")
        row(Ms[(Ms[NAMES] == 1).all(axis=1)], "   ALL FIVE")


if __name__ == "__main__":
    main()
