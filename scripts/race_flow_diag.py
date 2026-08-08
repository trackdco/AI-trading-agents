#!/usr/bin/env python3
"""FLOW + DEPTH into the winner/loser diagnostic — episode census.
REPORT-ONLY, fit-only, no holdout. Day-clustered throughout.

PRIOR-REFUTATION FRAMING, declared before the run: this is NOT a fresh,
unbiased test. The twelve flow features were tested on the 15m census
(CONCORD, BR-19) and refuted as a selection layer twice more (BR-26
transfer failure, BR-62 on open-space); the LTF re-measurement
(htf_ltf_flow) found the family weak rather than mis-measured; the B/C
single-table walk found nothing durable in depth. closeloc is the ONE
survivor (H5 holdout PASS) and it is Law-2 contaminated (BR-43). The
prior is AGAINST this family. Anything that clears here is a base rate
on a refuted family's second look and needs forward confirmation.

LAW-2 CLASSIFICATION (same discipline as race_diagnose):
  MECHANICAL/screened: closeloc, rangex (trigger-candle geometry —
  risk ~= closeloc x range, BR-43); any feature with |rho(risk)| > 0.4
  is auto-flagged. support_wall_dist is price-denominated (vol-coupled).
  Everything else: behavioral candidates.

Features: the 12 FLOW_NAMES (imported flow_features, computed at each
fight's winning-TF decision bar) + the 6 depth/wall features (imported
depth_at, book as-of t-1min, day-median thickness base). Coverage
reported per feature — depth exists only on days with book data; a
sub-90%-coverage finding is a sub-population finding.

    python -m scripts.race_flow_diag [--build]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.htf_ma_flow_depth_run import (depth_at, depth_index,   # noqa: E402
                                           load_book_frames)
from scripts.htf_ma_mtable import FLOW_NAMES, flow_features         # noqa: E402
from scripts.race_diagnose import MECHS, cluster, ddiff             # noqa: E402
from scripts.trigger_race_census import SESSIONS                    # noqa: E402
from src.htf_ma.levels import NY                                    # noqa: E402

OUTP = ROOT / "output/htf_ma_census/race_outcomes_epi.parquet"
# --at-entry (Part 4): evaluate depth AS-OF THE CLOSURE MINUTE t — the
# book you market-order into — instead of t-1min. The old canon's
# hindsight came from LIMIT fills timestamped inside later bars; a
# market order at the close makes the as-of-t snapshot causal. Flow is
# already as-of the closure (windows end at bar_end=t) and is unchanged.
AT_ENTRY = "--at-entry" in sys.argv
FEATP = ROOT / ("output/htf_ma_census/race_flow_feats_entry.parquet"
                if AT_ENTRY
                else "output/htf_ma_census/race_flow_feats.parquet")
DEPTH_FEATS = ["dep_thickness_vs_day", "dep_imbalance",
               "support_minus_resist", "support_wall_dist",
               "support_wall_size", "dep_thickness_delta_5m"]
CONF_SET = {"flowconf", "thru_delta_conf", "d5_conf", "d15_conf",
            "d30_conf", "bp5opp"}
LAW2 = {"closeloc", "rangex"}


def build_feats(B, bars):
    fp = pd.read_parquet(ROOT / "output/fp_minutes_full.parquet").sort_index()
    didx = depth_index()
    rows = []
    days = sorted(B.sess_day.unique())
    ndep = 0
    for k, day in enumerate(days):
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        t1 = t0 + pd.Timedelta(hours=23)
        hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30))
                    & (bars.index < t1)]
        fpd = fp[(fp.index >= t0 - pd.Timedelta(hours=30))
                 & (fp.index < t1)]
        D = B[B.sess_day == day]
        books = load_book_frames(didx[day]) if day in didx else None
        med_all = np.nan
        if books:
            ndep += 1
            med_all = float(np.median([v["size"].sum()
                                       for v in books.values()]))
        cache = {}
        for tf in sorted(D.tf_won.unique()):
            tf = int(tf)
            fptf = fpd.resample(f"{tf}min", label="right",
                                closed="left").agg(
                {"vol": "sum", "delta": "sum"}).dropna() \
                if len(fpd) else None
            otf = hist.resample(f"{tf}min", label="right",
                                closed="left").agg(
                {"open": "first", "high": "max", "low": "min",
                 "close": "last"}).dropna()
            cache[tf] = (fptf, otf)
        for r in D.itertuples():
            ts = pd.Timestamp(r.t)
            tf = int(r.tf_won)
            fptf, otf = cache[tf]
            b_ = otf.loc[ts] if ts in otf.index else None
            f = flow_features(
                fpd if len(fpd) else None, ts - pd.Timedelta(minutes=tf),
                ts, int(r.direction),
                fptf[fptf.index < ts] if fptf is not None else None,
                bar_ohlc=b_, prior_ohlc=otf[otf.index < ts])
            if books:
                dm = ts if AT_ENTRY else ts - pd.Timedelta(minutes=1)
                f.update(depth_at(books, dm, float(r.entry),
                                  int(r.direction), med_all))
            rows.append({"scid": r.scid, **{k2: f.get(k2, np.nan)
                                            for k2 in FLOW_NAMES
                                            + DEPTH_FEATS}})
        if k % 40 == 0:
            print(f"  {k}/{len(days)}... (depth days so far {ndep})",
                  flush=True)
    print(f"depth coverage: {ndep}/{len(days)} days")
    return pd.DataFrame(rows)


def main() -> None:
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low",
                                              "close", "volume"]]
    E = pd.read_parquet(OUTP)
    E["t"] = pd.to_datetime(E.t)
    E["out"] = np.where(E.mech == "M1", E.m1_out, E.near_out)
    E["out_pts"] = E.out * E.risk
    B = cluster(E, bars)
    nd = B.sess_day.nunique()
    print(f"book: {len(B)} fights over {nd} days")

    if "--build" in sys.argv or not FEATP.exists():
        FT = build_feats(B, bars)
        FT.to_parquet(FEATP, index=False)
        print(f"written: {FEATP.name} ({len(FT):,} rows)")
    FT = pd.read_parquet(FEATP)
    B = B.merge(FT, on="scid", how="left", validate="1:1")

    print("\n" + "=" * 100)
    if AT_ENTRY:
        print("AT-ENTRY MODE: depth as-of the closure minute t (the book "
              "a market order enters into — causal, unlike the old")
        print("canon's limit-fill hindsight); flow already ends at the "
              "closure and is unchanged.")
    print("FLOW (12) + DEPTH (6) INTO THE DIAGNOSTIC — SECOND LOOK AT A "
          "REFUTED FAMILY (BR-19/26/62; closeloc BR-43-contaminated).")
    print("The prior is AGAINST. Same screens as race_diagnose: "
          "points-control beside every R split; |rho(risk)|>0.4 "
          "auto-flagged; closeloc/rangex LAW2 by declaration.")
    print("~9 cells x 18 features = ~160 comparisons, no bar: expect "
          "~8 false clears at 95%.")
    print("=" * 100)

    print("\nCOVERAGE (fights with the feature non-null):")
    for v in FLOW_NAMES + DEPTH_FEATS:
        print(f"   {v:24s} {B[v].notna().mean()*100:5.1f}%")

    for w_ in SESSIONS:
        for mech in MECHS:
            g = B[(B.session == w_) & (B.mech == mech)].copy()
            if len(g) < 40:
                print(f"\n## {w_} {mech}  n={len(g)}  THIN — skipped")
                continue
            g["q"] = pd.qcut(g.out.rank(method="first"), 5,
                             labels=False) + 1
            win = g.out > 0
            print(f"\n## {w_} {mech}  n={len(g)}  EV {g.out.mean():+.3f}")
            print(f"   {'feature':24s} {'cov%':>5s} {'W-mean':>8s} "
                  f"{'L-mean':>8s} {'Q1':>8s} {'Q5':>8s} "
                  f"{'split dEV':>10s} {'95% CI(diff)':>18s} "
                  f"{'pts-ctrl':>9s} {'rho':>6s}")
            for v in FLOW_NAMES + DEPTH_FEATS:
                gv = g[g[v].notna()]
                cov = len(gv) / len(g) * 100
                if len(gv) < 40 or gv[v].nunique() < 2:
                    print(f"   {v:24s} {cov:5.0f}%   (thin/constant)")
                    continue
                if v in CONF_SET:
                    mask = gv[v] >= 1.0
                else:
                    mask = gv[v] > gv[v].median()
                if mask.mean() in (0.0, 1.0):
                    print(f"   {v:24s} {cov:5.0f}%   (degenerate split)")
                    continue
                d_, lo_, hi_, na_, nb_ = ddiff(gv, mask, "out")
                dp = (gv[mask].out_pts.mean() - gv[~mask].out_pts.mean()
                      if na_ >= 10 and nb_ >= 10 else np.nan)
                rho = gv[v].astype(float).corr(gv.risk)
                sig = "!" if np.isfinite(lo_) and (lo_ > 0 or hi_ < 0) \
                    else " "
                tag = " [LAW2]" if v in LAW2 or \
                    (np.isfinite(rho) and abs(rho) > 0.4) else ""
                ci = (f"[{lo_:+.3f},{hi_:+.3f}]{sig}"
                      if np.isfinite(lo_) else "thin")
                wv = gv[win.reindex(gv.index).fillna(False)][v]
                lv = gv[~win.reindex(gv.index).fillna(False)][v]
                print(f"   {v:24s} {cov:5.0f}% "
                      f"{wv.astype(float).mean():8.2f} "
                      f"{lv.astype(float).mean():8.2f} "
                      f"{gv[gv.q == 1][v].astype(float).mean():8.2f} "
                      f"{gv[gv.q == 5][v].astype(float).mean():8.2f} "
                      f"{d_:+10.3f} {ci:>18s} {dp:+9.1f} "
                      f"{rho:+6.2f}{tag}")


if __name__ == "__main__":
    main()
