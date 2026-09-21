#!/usr/bin/env python3
"""CENSUS C — the admissibility sweep (prereg: docs/PREREG-htf-ma.md §C).

Adds ceiling_broken_K (K in {1,2,3,5,10,inf}) to every Census B fit event that
carries a ceiling, then reads the declared table: NO-CEILING / BROKEN-K /
UNBROKEN strata on target_before_extreme_20, cluster-collapsed Wilson, era x
side x arm, stratum sizes. ALSO: the branch-asymmetry measurement (ANGUS) —
remaining favorable travel FROM ENTRY per branch, quantiles per era.

    python -m scripts.htf_ma_census_c
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars           # noqa: E402
from scripts.htf_ma_verdict_a import wilson               # noqa: E402
from src.htf_ma.levels import NY, bb_ma_asof              # noqa: E402

K_SWEEP = [1, 2, 3, 5, 10, 10**6]
H = "target_before_extreme_20"


def era_of(day: str) -> str:
    return "H2-2025" if day < "2026-01-01" else "H1-2026"


def cell(d: pd.DataFrame, col: str) -> str:
    if len(d) == 0:
        return "   --"
    cm = d.groupby("cluster_id")[col].mean()
    p, lo, hi = wilson(int(round(cm.sum())), len(cm))
    tag = "*" if len(cm) < 30 else " "
    return f"{cm.mean()*100:5.1f}%[{lo*100:4.1f},{hi*100:4.1f}]n={len(cm)}{tag}"


def main() -> None:
    F = pd.read_parquet(ROOT / "output/htf_ma_census/censusB_fit.parquet")
    F["era"] = F.sess_day.map(era_of)
    E = F[(F.target_defined == True) &                                 # noqa: E712
          ((F.kind == "reject") | ((F.kind == "break") & F.retraced_ma))].copy()
    E["arm"] = np.where(E.kind == "reject", "reject", "break")
    E["dir"] = np.where(E.arm == "reject",
                        np.where(E.side == "below", -1, 1),
                        np.where(E.break_dir == "up", 1, -1))
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close", "volume"]]

    broken_at = {K: np.zeros(len(E), bool) for K in K_SWEEP}
    fav_from_entry = np.full(len(E), np.nan)
    E = E.reset_index(drop=True)
    for day, g in E.groupby("sess_day"):
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        t1 = t0 + pd.Timedelta(hours=23)
        hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30)) & (bars.index < t1)]
        if hist.empty:
            continue
        seg = hist[hist.index >= t0]
        idx = seg.index
        hi_, lo_ = seg.high.to_numpy(), seg.low.to_numpy()
        tf_data = {}
        for tfn, tf in (("5m", 5), ("60m", 60)):
            ftf = hist.resample(f"{tf}min", label="right", closed="left").agg(
                {"close": "last"}).dropna()
            ma = bb_ma_asof(hist, tf)[0].reindex(ftf.index - pd.Timedelta(minutes=1))
            ma.index = ftf.index
            thru = np.sign(ftf.close.to_numpy() - ma.to_numpy())   # +1 above own MA
            tf_data[tfn] = (ftf.index.values, thru)
        for i, r in g.iterrows():
            e_t = pd.Timestamp(r.t) if r.arm == "reject" else \
                pd.Timestamp(r.t) + pd.Timedelta(minutes=float(r.t_retest_min))
            entry = r.event_px if r.arm == "reject" else r.retest_px
            # remaining favorable travel from ENTRY (no stop) — asymmetry q.
            j0 = int(np.searchsorted(idx.values, e_t.to_datetime64()))
            if j0 < len(idx) and np.isfinite(entry):
                ext = (hi_[j0:].max() - entry) if r.dir > 0 else (entry - lo_[j0:].min())
                fav_from_entry[i] = max(ext, 0.0) / r.w15
            if r.ceiling_tf not in tf_data:
                continue
            tix, thru = tf_data[r.ceiling_tf]
            k_end = int(np.searchsorted(tix, e_t.to_datetime64(), side="right"))
            for K in K_SWEEP:
                k_start = max(0, k_end - K)
                broken_at[K][i] = bool((thru[k_start:k_end] == r.dir).any())
    for K in K_SWEEP:
        E[f"broken_{K}"] = broken_at[K]
    E["fav_from_entry_W"] = fav_from_entry
    E.to_parquet(ROOT / "output/htf_ma_census/censusC_fit.parquet", index=False)

    lines = []
    def emit(s=""):
        print(s)
        lines.append(s)

    emit("CENSUS C — admissibility sweep (prereg §C), fit only")
    nc = (E.ceiling_tf == "none")
    emit(f"events: {len(E):,} | NO-CEILING {nc.mean()*100:.1f}% | with ceiling "
         f"{(~nc).mean()*100:.1f}% (5m {(E.ceiling_tf=='5m').mean()*100:.1f}%, "
         f"60m {(E.ceiling_tf=='60m').mean()*100:.1f}%)")

    emit("\n== ANGUS asymmetry: remaining favorable travel FROM ENTRY (W) ==")
    for arm in ("reject", "break"):
        for era in ("H2-2025", "H1-2026"):
            t = E[(E.arm == arm) & (E.era == era)].fav_from_entry_W.dropna()
            emit(f"  {arm:<7} {era}: p50 {t.median():.2f} p75 {t.quantile(.75):.2f} "
                 f"p90 {t.quantile(.9):.2f} p95 {t.quantile(.95):.2f}")

    emit("\n== strata by K (metric: target before 20t past extreme) ==")
    for K in K_SWEEP:
        kn = "inf" if K > 100 else K
        emit(f"[K={kn}]")
        for era in ("H2-2025", "H1-2026"):
            d = E[E.era == era]
            noc = d[d.ceiling_tf == "none"]
            brk = d[(d.ceiling_tf != "none") & d[f"broken_{K}"]]
            unb = d[(d.ceiling_tf != "none") & ~d[f"broken_{K}"]]
            adm = d[(d.ceiling_tf == "none") | d[f"broken_{K}"]]
            emit(f"  {era}: NOCEIL {cell(noc, H)} | BROKEN {cell(brk, H)} | "
                 f"UNBROKEN {cell(unb, H)}")
            emit(f"          ADMISSIBLE(K) {cell(adm, H)}  "
                 f"[sizes: {len(noc)}/{len(brk)}/{len(unb)}]")
    emit("\nPer-arm x side splits + the prereg plateau reading follow in the "
         "verdict append. Sides/arms pooled cells above are for the K surface "
         "shape only; the bar is read on the full split table.")

    emit("\n== full split at each K: ADMISSIBLE vs UNBROKEN, era x arm ==")
    for K in K_SWEEP:
        kn = "inf" if K > 100 else K
        for arm in ("reject", "break"):
            row = []
            for era in ("H2-2025", "H1-2026"):
                d = E[(E.era == era) & (E.arm == arm)]
                adm = d[(d.ceiling_tf == "none") | d[f"broken_{K}"]]
                unb = d[(d.ceiling_tf != "none") & ~d[f"broken_{K}"]]
                am = adm.groupby("cluster_id")[H].mean()
                um = unb.groupby("cluster_id")[H].mean()
                if len(um) < 15:
                    row.append("UNDERPOWERED")
                    continue
                _, alo, _ = wilson(int(round(am.sum())), len(am))
                _, _, uhi = wilson(int(round(um.sum())), len(um))
                sep = am.mean() - um.mean()
                row.append(f"{sep*100:+5.1f}pp{'!' if alo > uhi else ' '}"
                           f"(n{len(um)})")
            emit(f"  K={kn:<4} {arm:<7} " + " | ".join(row) +
                 "   ('!' = CIs non-overlapping)")

    with open(ROOT / "docs/VERDICT-htf-ma-census.md", "a") as fh:
        fh.write("\n## Census C — admissibility sweep (run 2026-08-07)\n\n```\n"
                 + "\n".join(lines) + "\n```\n")
    print("\nappended -> docs/VERDICT-htf-ma-census.md")


if __name__ == "__main__":
    main()
