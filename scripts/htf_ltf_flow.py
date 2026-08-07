#!/usr/bin/env python3
"""FLOW AT THE LTF DECISION BAR — prediction #5 of the re-census declaration.

The claim that motivated the whole re-census: `flow_features` computes
delta over [bar_start, bar_end). At a 15m trigger that pools the approach,
the failed pokes and the break itself into one number — SNR ~1:15 around
an event that occupies one minute. This script recomputes the SAME twelve
features (imported, not reimplemented) with the window set to the ACTUAL
decision candle at each TF, so the 1m rows see the event minute and
nothing else.

  build   join the twelve features to every ltf_fit row at its own TF
  report  CONCORD (the zero-free-parameter count) and each feature, per
          (session, TF, arm), against the 15m numbers in BR-19

Declared reading, before the run: prediction #5 says flow should be
MARKEDLY STRONGER at 1m. If it is not, that is a real finding — it says
the flow family is genuinely weak rather than mis-measured — and it is
recorded as a result, not as a failed run.

    python -m scripts.htf_ltf_flow [--build]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.htf_ltf_report import (PAIRS, TFS, SESS, assign,       # noqa: E402
                                    book, boot_lift, boot_mean, era)
from scripts.htf_ma_flow_depth_run import CONF_BIN, MAG            # noqa: E402
from scripts.htf_ma_mtable import FLOW_NAMES, flow_features        # noqa: E402
from src.htf_ma.levels import NY                                    # noqa: E402

FIT = ROOT / "output/htf_ma_census/ltf_fit.parquet"
OUT = ROOT / "output/htf_ma_census/ltf_flow.parquet"
XDEC = 0.5


def concord(X: pd.DataFrame) -> pd.Series:
    """Unweighted agreement count, 0-12. Zero free parameters — identical
    construction to BR-19's, so the numbers are comparable."""
    a = pd.DataFrame(index=X.index)
    for c in CONF_BIN:
        a[c] = (X[c] == 1).astype(float)
    a["bp5opp"] = (X["bp5opp"] == 0).astype(float)
    for c in ("cvd_slope30", "delta_z"):
        a[c] = (X[c] > 0).astype(float)
    for c in MAG:
        a[c] = (X[c] >= X[c].median()).astype(float)
    a["closeloc"] = (X["closeloc"] >= 0.5).astype(float)
    return a.sum(axis=1)


def build() -> pd.DataFrame:
    F = pd.read_parquet(FIT)
    F["t"] = pd.to_datetime(F.t)
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close",
                                              "volume"]]
    fp = pd.read_parquet(ROOT / "output/fp_minutes_full.parquet").sort_index()
    out, days = [], sorted(F.sess_day.unique())
    for k, day in enumerate(days):
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        t1 = t0 + pd.Timedelta(hours=23)
        hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30))
                    & (bars.index < t1)]
        fpd = fp[(fp.index >= t0 - pd.Timedelta(hours=30)) & (fp.index < t1)]
        D = F[F.sess_day == day]
        if hist.empty or not len(fpd) or D.empty:
            continue
        for tf, g in D.groupby("tf"):
            tf = int(tf)
            # the TF's own completed candles — the normalisation base for
            # volx / delta_z / rangex must be the SAME timeframe as the bar
            fptf = fpd.resample(f"{tf}min", label="right", closed="left").agg(
                {"vol": "sum", "delta": "sum"}).dropna()
            otf = hist.resample(f"{tf}min", label="right", closed="left").agg(
                {"open": "first", "high": "max", "low": "min",
                 "close": "last"}).dropna()
            for r in g.itertuples():
                ts = pd.Timestamp(r.t)
                b_ = otf.loc[ts] if ts in otf.index else None
                f = flow_features(fpd, ts - pd.Timedelta(minutes=tf), ts,
                                  int(r.direction), fptf[fptf.index < ts],
                                  bar_ohlc=b_, prior_ohlc=otf[otf.index < ts])
                out.append({"sess_day": day, "t": ts, "tf": tf,
                            "locus": r.locus, "arm": r.arm, "side": r.side,
                            **f})
        if k % 40 == 0:
            print(f"  flow {k}/{len(days)}...", flush=True)
    F2 = pd.DataFrame(out)
    F2.to_parquet(OUT, index=False)
    print(f"written: ltf_flow.parquet ({len(F2):,} rows)")
    return F2


def main() -> None:
    G = build() if ("--build" in sys.argv or not OUT.exists()) \
        else pd.read_parquet(OUT)
    F = pd.read_parquet(FIT)
    F["t"] = pd.to_datetime(F.t)
    G["t"] = pd.to_datetime(G.t)
    F = F.merge(G, on=["sess_day", "t", "tf", "locus", "arm", "side"],
                how="left")
    F["era"] = era(F)
    P = pd.read_parquet(PAIRS)
    F["scid"] = assign(F, P, XDEC)
    B = book(F)
    nd = F.sess_day.nunique()

    print(f"\nFLOW AT THE LTF DECISION BAR — {len(B):,} first-of-fight rows, "
          f"{nd} days, X={XDEC}W\n")

    print("=" * 78)
    print("0. COVERAGE AND THE 1m COLLAPSE")
    print("=" * 78)
    print(f"   {'tf':>3s} {'n':>6s} " + " ".join(f"{c[:9]:>9s}"
                                                 for c in FLOW_NAMES))
    for tf in TFS:
        g = B[B.tf == tf]
        print(f"   {tf:3d} {len(g):6d} "
              + " ".join(f"{g[c].notna().mean()*100:8.0f}%" for c in FLOW_NAMES))
    same = B[B.tf == 1]
    agree = (same.flowconf == same.thru_delta_conf).mean() * 100
    print(f"\n   NOTE: at TF=1 the decision bar IS one minute, so flowconf "
          f"(bar delta sign)\n   and thru_delta_conf (last-minute delta sign) "
          f"are the same feature: {agree:.1f}% identical.\n   CONCORD "
          f"therefore double-counts one signal at 1m. Stated, not corrected — "
          f"the\n   count is kept identical to BR-19's so the numbers stay "
          f"comparable.")

    print("\n" + "=" * 78)
    print("1. CONCORD AS A RANKING SIGNAL — Spearman vs out_ship")
    print("   BR-19 at 15m: +0.093 break / +0.129 reject (real ranking, no "
          "gate value)")
    print("=" * 78)
    print(f"   {'sess':7s} {'arm':6s} " + " ".join(f"{f'TF={t}':>14s}"
                                                  for t in TFS))
    for s in SESS:
        for arm in ("reject", "break"):
            cells = []
            for tf in TFS:
                g = B[(B.session == s) & (B.arm == arm) & (B.tf == tf)]
                g = g[g.flowconf.notna()]
                if len(g) < 50:
                    cells.append(f"n={len(g)} thin")
                    continue
                c = concord(g)
                rho = pd.Series(c).corr(g.out_ship.reset_index(drop=True)
                                        if c.index.equals(g.index) is False
                                        else g.out_ship, method="spearman")
                cells.append(f"{rho:+.3f} n={len(g)}")
            print(f"   {s:7s} {arm:6s} " + " ".join(f"{c:>14s}" for c in cells))

    print("\n" + "=" * 78)
    print("2. CONCORD AS A GATE — the Law-7 lift, bar +0.05R, both eras")
    print("   BR-19 at 15m: max whole-book gate lift +0.046R, below the bar, "
          "and every")
    print("   half-1 survivor died on half 2. The worst flow bin was still "
          "profitable.")
    print("=" * 78)
    print(f"   {'sess':7s} {'arm':6s} {'tf':>3s} {'cut':>10s} {'n_keep':>7s} "
          f"{'EV_all':>8s} {'EV_keep':>8s} {'lift':>8s} {'H2 CI':>19s} "
          f"{'H1 CI':>19s}  bar")
    best = []
    for s in SESS:
        for arm in ("reject", "break"):
            for tf in TFS:
                A = B[(B.session == s) & (B.arm == arm) & (B.tf == tf)]
                A = A[A.flowconf.notna()]
                if len(A) < 60:
                    continue
                A = A.assign(cc=concord(A).to_numpy())
                for thr in (5, 6, 7, 8):
                    K = A[A.cc >= thr]
                    if len(K) < 25 or len(K) == len(A):
                        continue
                    lift = K.out_ship.mean() - A.out_ship.mean()
                    ok, cis = [], []
                    for e in ("H2-2025", "H1-2026"):
                        lo, hi = boot_lift(A[A.era == e], K[K.era == e])
                        cis.append(f"[{lo:+.3f},{hi:+.3f}]"
                                   + ("!" if lo > 0 else " "))
                        ok.append(np.isfinite(lo) and lo > 0)
                    p = (lift >= 0.05) and all(ok)
                    if p or lift >= 0.10:
                        print(f"   {s:7s} {arm:6s} {tf:3d} {f'CC>={thr}':>10s} "
                              f"{len(K):7d} {A.out_ship.mean():+8.3f} "
                              f"{K.out_ship.mean():+8.3f} {lift:+8.3f} "
                              f"{cis[0]:>19s} {cis[1]:>19s}  "
                              f"{'PASS' if p else 'miss'}")
                    best.append((lift, p, s, arm, tf, thr))
    if not best:
        print("   (no cell reached the reporting threshold)")
    else:
        npass = sum(1 for b in best if b[1])
        mx = max(best)
        print(f"\n   cells tested: {len(best)} | clearing the declared bar in "
              f"BOTH eras: {npass}")
        print(f"   largest lift anywhere: {mx[0]:+.3f}R "
              f"({mx[2]} {mx[3]} TF={mx[4]} CC>={mx[5]}) "
              f"{'PASS' if mx[1] else '— does not clear both eras'}")
        print(f"   MULTIPLICITY: {len(best)} cells were searched. Bonferroni "
              f"alpha = 0.05/{len(best)} = {0.05/len(best):.5f}. Nothing here "
              f"is a verdict;\n   it is a fit-side ranking of candidates.")

    print("\n" + "=" * 78)
    print("3. PER-FEATURE, THE HEADLINE COMPARISON: does the SAME feature "
          "get stronger at 1m?")
    print("   |Spearman rho| vs out_ship, per TF, pooled over sessions and "
          "arms (the fair")
    print("   like-for-like: same feature, same population grammar, only the "
          "window changes)")
    print("=" * 78)
    print(f"   {'feature':14s} " + " ".join(f"{f'TF={t}':>8s}" for t in TFS)
          + "   direction")
    for c in FLOW_NAMES:
        rr = []
        for tf in TFS:
            g = B[(B.tf == tf) & B[c].notna()]
            rr.append(g[c].corr(g.out_ship, method="spearman")
                      if len(g) >= 100 and g[c].nunique() > 1 else np.nan)
        d = ("STRONGER at 1m" if (np.isfinite(rr[0]) and np.isfinite(rr[-1])
                                  and abs(rr[0]) > abs(rr[-1]) * 1.2)
             else "weaker at 1m" if (np.isfinite(rr[0]) and np.isfinite(rr[-1])
                                     and abs(rr[0]) * 1.2 < abs(rr[-1]))
             else "flat")
        print(f"   {c:14s} " + " ".join(f"{v:+8.3f}" if np.isfinite(v)
                                        else "     n/a" for v in rr)
              + f"   {d}")
    print("\n   PREDICTION #5 said flow would be MARKEDLY STRONGER at 1m. "
          "Read the 1m column\n   against the 5m column above: that is the "
          "test, and it is reported whichever\n   way it falls.")


if __name__ == "__main__":
    main()
