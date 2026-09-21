#!/usr/bin/env python3
"""VERDICT — Census A (M1 rebalance base rate). Reads FIT rows only.

SPEC §6/§8: Wilson intervals, sides never pooled, era split (2025-H2 discover /
2026-H1 check), cluster-aware power (n_clusters < 30 -> UNDERPOWERED), session
split reported never filtered, both placebos (proximity-matched shifted MA,
>=100 draws; stale MA from 5 sessions earlier) on a sampled day subset.
Writes the Census A section of docs/VERDICT-htf-ma-census.md.

    python -m scripts.htf_ma_verdict_a
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars           # noqa: E402
from src.htf_ma.levels import NY, bb_ma_asof              # noqa: E402

S_SWEEP = [10, 20, 30, 40, 60, 80]
E_SWEEP = [0.5, 1.0, 1.5, 2.0, 3.0]
N_DRAWS, N_PLACEBO_DAYS = 100, 60
Z = 1.96


def wilson(k: int, n: int):
    if n == 0:
        return (np.nan, np.nan, np.nan)
    p = k / n
    den = 1 + Z ** 2 / n
    c = (p + Z ** 2 / (2 * n)) / den
    h = Z * np.sqrt(p * (1 - p) / n + Z ** 2 / (4 * n ** 2)) / den
    return p, c - h, c + h


def cell(d: pd.DataFrame, col: str) -> str:
    ncl = d.cluster_id.nunique()
    # cluster-collapsed: mean of per-cluster means; interval on cluster count
    cm = d.groupby("cluster_id")[col].mean()
    p, lo, hi = wilson(int(round(cm.sum())), len(cm))
    tag = " UNDERPOWERED" if ncl < 30 else ""
    return f"{cm.mean()*100:5.1f}% [{lo*100:4.1f},{hi*100:4.1f}] n={ncl}{tag}"


def era_of(day: str) -> str:
    return "H2-2025" if day < "2026-01-01" else "H1-2026"


def light_touch_rate(seg, ma_line, w_line, rng_stop=40 * 0.25):
    """One-pass D=0.5 event machine vs an arbitrary level line; returns
    (n_events, touched, touched_before_stop40)."""
    hi, lo, cl = seg.high.to_numpy(), seg.low.to_numpy(), seg.close.to_numpy()
    ev = tt = ts = 0
    for side in (1, -1):
        armed = True
        i = 0
        n = len(cl)
        while i < n:
            m, w = ma_line[i], w_line[i]
            if np.isfinite(m) and lo[i] <= m <= hi[i]:
                armed = True
            elif armed and np.isfinite(m) and np.isfinite(w) and w > 0 \
                    and side * (cl[i] - m) / w > 0.5:
                armed = False
                ev += 1
                ref, run = cl[i], 0.0
                for j in range(i + 1, n):
                    adv = (hi[j] - ref) if side > 0 else (ref - lo[j])
                    run = max(run, adv)
                    if np.isfinite(ma_line[j]) and lo[j] <= ma_line[j] <= hi[j]:
                        tt += 1
                        ts += run < rng_stop
                        break
            i += 1
    return ev, tt, ts


def main() -> None:
    F = pd.read_parquet(ROOT / "output/htf_ma_census/censusA_fit.parquet")
    F["era"] = F.sess_day.map(era_of)
    lines = []

    def emit(s=""):
        print(s)
        lines.append(s)

    emit("CENSUS A — M1 REBALANCE, fit only (2025-06..2026-07), 15m reference")
    emit(f"rows={len(F):,} clusters={F.cluster_id.nunique():,} days={F.sess_day.nunique()}")
    emit("\n== touch rate by D x side x era (cluster-collapsed, Wilson 95) ==")
    for D in sorted(F.D.unique()):
        for side in ("above", "below"):
            for era in ("H2-2025", "H1-2026"):
                d = F[(F.D == D) & (F.side == side) & (F.era == era)]
                if len(d) == 0:
                    continue
                emit(f"  D={D:<5} {side:<6} {era:<8} {cell(d, 'touched_ma')}")

    emit("\n== ma_before_stop_S (LOAD-BEARING) — D=0.5, side x era ==")
    for S in S_SWEEP:
        for side in ("above", "below"):
            row = []
            for era in ("H2-2025", "H1-2026"):
                d = F[(F.D == 0.5) & (F.side == side) & (F.era == era)]
                row.append(cell(d, f"ma_before_stop_{S}"))
            emit(f"  S={S:>3}t {side:<6} {row[0]}  |  {row[1]}")

    emit("\n== ma_before_ext_E — D=0.5, pooled sides shown per era ==")
    for E in E_SWEEP:
        for side in ("above", "below"):
            r25 = cell(F[(F.D == 0.5) & (F.side == side) & (F.era == 'H2-2025')], f"ma_before_ext_{E}")
            r26 = cell(F[(F.D == 0.5) & (F.side == side) & (F.era == 'H1-2026')], f"ma_before_ext_{E}")
            emit(f"  E={E:<4}W {side:<6} {r25}  |  {r26}")

    emit("\n== sessions (D=0.5, both eras pooled; reported never filtered) ==")
    for s in ("asia", "london", "ny_pre", "ny_rth_am", "ny_pm"):
        for side in ("above", "below"):
            d = F[(F.D == 0.5) & (F.side == side) & (F.session == s)]
            if len(d):
                emit(f"  {s:<10} {side:<6} touch {cell(d, 'touched_ma')} | "
                     f"stop40 {cell(d, 'ma_before_stop_40')}")

    emit("\n== time-to-touch + adverse (D=0.5, touched rows) ==")
    for era in ("H2-2025", "H1-2026"):
        d = F[(F.D == 0.5) & (F.era == era) & F.touched_ma]
        emit(f"  {era}: t_touch median {d.t_touched_ma.median():.0f}m p75 "
             f"{d.t_touched_ma.quantile(.75):.0f}m | max_adverse median "
             f"{d.max_adverse_pts.median():.1f}pt p75 {d.max_adverse_pts.quantile(.75):.1f}pt "
             f"(in W: {d.max_adverse_bw.median():.2f}/{d.max_adverse_bw.quantile(.75):.2f})")

    emit("\n== htf_agree_1h conditioning (D=0.5, touch rate) ==")
    for era in ("H2-2025", "H1-2026"):
        for side in ("above", "below"):
            d = F[(F.D == 0.5) & (F.era == era) & (F.side == side)]
            a, b = d[d.htf_agree_1h == True], d[d.htf_agree_1h == False]  # noqa: E712
            if len(a) > 5 and len(b) > 5:
                emit(f"  {era} {side}: 1h-agree {cell(a,'touched_ma')} vs disagree {cell(b,'touched_ma')}")

    # ---- placebos on a sampled day subset --------------------------------
    emit("\n== placebos (D=0.5 machine, sampled days, headline = touch-before-stop40 rate) ==")
    rng = np.random.default_rng(11)
    days = sorted(F.sess_day.unique())
    samp = list(rng.choice(days, size=min(N_PLACEBO_DAYS, len(days)), replace=False))
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close", "volume"]]
    prep = {}
    for d in samp:
        t0 = pd.Timestamp(f"{d} 18:00", tz=NY)
        hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30)) &
                    (bars.index < t0 + pd.Timedelta(hours=23))]
        ma, w = bb_ma_asof(hist, 15)
        seg = hist[hist.index >= t0]
        prep[d] = (seg, ma.loc[seg.index].to_numpy(), w.loc[seg.index].to_numpy())
    # real
    ev = tt = ts = 0
    for d in samp:
        seg, ma, w = prep[d]
        e, t, s_ = light_touch_rate(seg, ma, w)
        ev += e; tt += t; ts += s_
    real = ts / ev if ev else np.nan
    emit(f"  real: events={ev} touch={tt/ev*100:.1f}% touch<stop40={real*100:.1f}%")
    # proximity-matched shifted MA
    draws = []
    for k in range(N_DRAWS):
        ev_p = ts_p = 0
        for d in samp:
            seg, ma, w = prep[d]
            dist = np.abs(seg.close.to_numpy() - ma)
            dist = dist[np.isfinite(dist)]
            off = rng.choice(dist) * rng.choice([-1, 1])
            e, t, s_ = light_touch_rate(seg, ma + off, w)
            ev_p += e; ts_p += s_
        draws.append(ts_p / ev_p if ev_p else np.nan)
    draws = np.array([x for x in draws if np.isfinite(x)])
    pct = (draws < real).mean() * 100
    emit(f"  shifted-MA placebo ({len(draws)} draws): mean {draws.mean()*100:.1f}% "
         f"p95 {np.percentile(draws,95)*100:.1f}% -> real at {pct:.0f}th percentile")
    # stale MA (5 sessions earlier, aligned by minute-of-session)
    ev_s = ts_s = 0
    for d in samp:
        i = days.index(d)
        if i < 5:
            continue
        seg, _, w = prep[d]
        d_old = days[i - 5]
        if d_old not in prep:
            t0o = pd.Timestamp(f"{d_old} 18:00", tz=NY)
            ho = bars[(bars.index >= t0o - pd.Timedelta(hours=30)) &
                      (bars.index < t0o + pd.Timedelta(hours=23))]
            mo, wo = bb_ma_asof(ho, 15)
            so = ho[ho.index >= t0o]
            prep[d_old] = (so, mo.loc[so.index].to_numpy(), wo.loc[so.index].to_numpy())
        old_ma = prep[d_old][1]
        L = min(len(old_ma), len(seg))
        e, t, s_ = light_touch_rate(seg.iloc[:L], old_ma[:L], w[:L])
        ev_s += e; ts_s += s_
    stale = ts_s / ev_s if ev_s else np.nan
    emit(f"  stale-MA placebo (5 sessions old): events={ev_s} touch<stop40={stale*100:.1f}%")

    Path(ROOT / "docs").mkdir(exist_ok=True)
    hdr = ("# VERDICT — HTF BB MA mechanism census\n\n## Census A — M1 REBALANCE "
           "(run 2026-08-07, fit only, 15m reference)\n\n```\n")
    (ROOT / "docs/VERDICT-htf-ma-census.md").write_text(hdr + "\n".join(lines) + "\n```\n")
    print("\nwritten -> docs/VERDICT-htf-ma-census.md")


if __name__ == "__main__":
    main()
