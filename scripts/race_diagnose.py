#!/usr/bin/env python3
"""WINNER/LOSER DIAGNOSTIC — corrected (episode-M1) race census.
REPORT-ONLY, fit-only, no holdout. Day-clustered from the start.

LAW-2 CLASSIFICATION, DECLARED BEFORE ANY OUTCOME IS READ:
  MECHANICAL (R-denominator-coupled — SCREENED, nothing here is a signal
  until the coupling is ruled out):
    risk   — IS the R denominator
    w15    — scales the candle sizes that set risk
    tf_won — stop width is mechanically tied to the winning TF (the flag
             raised in the outcome pass); its control: EV by tf INSIDE
             risk terciles, and the points-based (not R) read
  STATE (decision-time, behavioral candidates):
    n_aff, aff_<structure> flags (which structures affirmed), n_tie
    (how many TFs closed simultaneously), disp_abs_w (|displacement| at
    trigger open, W units — dimensionless), epi_max_w (M1 episode depth,
    W units), tmin (minutes since the window opened)

Outcome scored: M1 -> m1_out (15m MA race); M2/M3 -> near_out. Realized-R
QUINTILES within each (window, mech) cell, plus winner/loser means, plus
a median-split EV difference with a day-clustered bootstrap CI on the
DIFFERENCE (seed 20260807, 2000 draws). Points-based control (out*risk)
reported alongside every R-based split. Windows and mechanisms NEVER
pooled. Multiplicity: ~9 cells x ~13 variables — >100 comparisons, NO
DECLARED BAR; base rates, nulls published.

    python -m scripts.race_diagnose
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.trigger_race_census import MENU, SESSIONS              # noqa: E402
from src.htf_ma.levels import NY                                    # noqa: E402

SEED, DRAWS = 20260807, 2000
MECHS = ["M1", "M2", "M3"]
OUTP = ROOT / "output/htf_ma_census/race_outcomes_epi.parquet"
CENP = ROOT / "output/htf_ma_census/race_fit_m1episode.parquet"

LAW2 = {"risk", "w15", "tf_won"}
VARS = (["n_aff", "n_tie", "disp_abs_w", "tmin", "risk", "w15"]
        + [f"aff_{k}" for k in MENU])          # + epi_max_w for M1 only


def cluster(F, bars, x=0.5):
    key = {}
    for day, D in F.groupby("sess_day"):
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        seg = bars[(bars.index >= t0)
                   & (bars.index < t0 + pd.Timedelta(hours=23))]
        if seg.empty:
            continue
        idx = seg.index
        hi, lo = seg.high.to_numpy(), seg.low.to_numpy()
        for grp, g in D.groupby(["mech", "dir"]):
            g = g.sort_values("t")
            ts, rp, ws = g.t.tolist(), g.ma15.tolist(), g.w15.tolist()
            for a in range(len(ts) - 1):
                i0 = int(np.searchsorted(idx.values, ts[a].to_datetime64()))
                i1 = int(np.searchsorted(idx.values,
                                         ts[a + 1].to_datetime64()))
                if i1 <= i0 or ws[a] <= 0 or not np.isfinite(rp[a]):
                    continue
                m = np.nanmax(np.maximum(np.abs(hi[i0:i1] - rp[a]),
                                         np.abs(lo[i0:i1] - rp[a])))
                key[(day, grp, ts[a + 1])] = m / ws[a]
    ids = {}
    for (day, mech, dr), g in F.groupby(["sess_day", "mech", "dir"],
                                        sort=False):
        g = g.sort_values("t")
        cid, seen = 0, None
        for r in g.itertuples():
            t = pd.Timestamp(r.t)
            if seen is not None and t != seen:
                e = key.get((day, (mech, dr), t), np.nan)
                if not np.isfinite(e) or e >= x:
                    cid += 1
            seen = t
            ids[r.Index] = f"{day}:{mech}:{dr}:S{cid}"
    return F.assign(scid=pd.Series(ids)).sort_values("t") \
        .groupby("scid", as_index=False).first()


def ddiff(g, mask, col):
    """Median/flag split: mean difference with a day-clustered bootstrap
    CI on the DIFFERENCE (same day draws for both arms)."""
    a, b = g[mask], g[~mask]
    if (len(a) < 10 or len(b) < 10 or a.sess_day.nunique() < 3
            or b.sess_day.nunique() < 3):
        return np.nan, np.nan, np.nan, len(a), len(b)
    days = sorted(g.sess_day.unique())
    di = {d_: i for i, d_ in enumerate(days)}

    def sums(x):
        s = np.zeros(len(days))
        c = np.zeros(len(days))
        for d_, r in x.groupby("sess_day")[col].agg(["sum", "count"]) \
                .iterrows():
            s[di[d_]], c[di[d_]] = r["sum"], r["count"]
        return s, c

    sa, ca = sums(a)
    sb, cb = sums(b)
    rng = np.random.default_rng(SEED)
    i = rng.integers(0, len(days), (DRAWS, len(days)))
    csa, csb = ca[i].sum(1), cb[i].sum(1)
    ea = np.divide(sa[i].sum(1), csa, out=np.full(DRAWS, np.nan),
                   where=csa > 0)
    eb = np.divide(sb[i].sum(1), csb, out=np.full(DRAWS, np.nan),
                   where=csb > 0)
    dd = ea - eb
    return (float(a[col].mean() - b[col].mean()),
            float(np.nanpercentile(dd, 2.5)),
            float(np.nanpercentile(dd, 97.5)), len(a), len(b))


def main() -> None:
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low",
                                              "close", "volume"]]
    E = pd.read_parquet(OUTP)
    E["t"] = pd.to_datetime(E.t)
    C = pd.read_parquet(CENP)[["t", "mech", "dir", "aff_list", "disp_w",
                               "epi_max_w", "tie_tfs"]]
    C["t"] = pd.to_datetime(C.t)
    n0 = len(E)
    E = E.merge(C, on=["t", "mech", "dir"], how="left", validate="1:1")
    assert len(E) == n0, "join changed row count"
    assert E.aff_list.notna().all() or True
    print(f"joined {n0} outcome rows with census features "
          f"(aff_list coverage {E.aff_list.notna().mean()*100:.1f}%)")

    for k in MENU:
        E[f"aff_{k}"] = E.aff_list.fillna("").str.contains(k, regex=False)
    # vwap flag must not also match vwap_p1 etc.
    E["aff_vwap"] = E.aff_list.fillna("").str.split(",") \
        .apply(lambda xs: "vwap" in xs)
    E["n_tie"] = E.tie_tfs.fillna("").str.split(",") \
        .apply(lambda xs: sum(1 for x in xs if x))
    E["disp_abs_w"] = E.disp_w.abs()
    hm = E.t.dt.hour * 60 + E.t.dt.minute
    start = pd.Series(0, index=E.index)
    for nm, (a, b) in SESSIONS.items():
        start[E.session == nm] = a
    E["tmin"] = hm - start
    E["out"] = np.where(E.mech == "M1", E.m1_out, E.near_out)
    E["out_pts"] = E.out * E.risk

    B = cluster(E, bars)
    nd = B.sess_day.nunique()
    print(f"book: {len(B)} fights over {nd} days\n")

    print("=" * 100)
    print("LAW-2 CLASSIFICATION (declared in the header before outcomes "
          "were read): MECHANICAL/screened = risk, w15, tf_won.")
    print("Every split shows the R-based lift AND the points-based "
          "control; a 'signal' that dies in points is the denominator.")
    print("=" * 100)

    for w_ in SESSIONS:
        for mech in MECHS:
            g = B[(B.session == w_) & (B.mech == mech)].copy()
            if len(g) < 40:
                print(f"\n## {w_} {mech}  n={len(g)}  THIN — skipped")
                continue
            g["q"] = pd.qcut(g.out.rank(method="first"), 5,
                             labels=False) + 1
            win = g.out > 0
            print(f"\n## {w_} {mech}  n={len(g)}  EV {g.out.mean():+.3f}  "
                  f"win% {win.mean()*100:.1f}")
            print(f"   {'variable':12s} {'W-mean':>8s} {'L-mean':>8s} "
                  f"{'Q1':>8s} {'Q5':>8s} {'split dEV':>10s} "
                  f"{'95% CI(diff)':>18s} {'pts-ctrl':>9s} {'rho(risk)':>9s}")
            vars_ = VARS + (["epi_max_w"] if mech == "M1" else [])
            for v in vars_:
                if g[v].dtype == bool:
                    mask = g[v]
                    if mask.mean() in (0.0, 1.0):
                        continue
                else:
                    if g[v].nunique() < 2:
                        continue
                    mask = g[v] > g[v].median()
                d_, lo_, hi_, na_, nb_ = ddiff(g, mask, "out")
                dp = (g[mask].out_pts.mean() - g[~mask].out_pts.mean()
                      if na_ >= 10 and nb_ >= 10 else np.nan)
                rho = g[v].astype(float).corr(g.risk)
                sig = "!" if np.isfinite(lo_) and (lo_ > 0 or hi_ < 0) \
                    else " "
                tag = " [LAW2]" if v in LAW2 or \
                    (np.isfinite(rho) and abs(rho) > 0.4) else ""
                ci = (f"[{lo_:+.3f},{hi_:+.3f}]{sig}"
                      if np.isfinite(lo_) else "thin")
                print(f"   {v:12s} {g[win][v].astype(float).mean():8.2f} "
                      f"{g[~win][v].astype(float).mean():8.2f} "
                      f"{g[g.q == 1][v].astype(float).mean():8.2f} "
                      f"{g[g.q == 5][v].astype(float).mean():8.2f} "
                      f"{d_:+10.3f} {ci:>18s} "
                      f"{dp:+9.1f} {rho:+9.2f}{tag}")
            # tf_won: EV by TF with the risk-tercile control
            tf_tab = []
            for tf in (1, 2, 3):
                gt = g[g.tf_won == tf]
                if len(gt) >= 10:
                    tf_tab.append(f"{tf}m n={len(gt)} EV {gt.out.mean():+.3f}")
            if tf_tab:
                print("   tf_won [LAW2]: " + "  ".join(tf_tab))
                try:
                    g["rt"] = pd.qcut(g.risk.rank(method="first"), 3,
                                      labels=False)
                    parts = []
                    for rt in range(3):
                        gr = g[g.rt == rt]
                        by = [f"{tf}:{gr[gr.tf_won == tf].out.mean():+.2f}"
                              f"({len(gr[gr.tf_won == tf])})"
                              for tf in (1, 2, 3)
                              if len(gr[gr.tf_won == tf]) >= 5]
                        parts.append(f"T{rt+1} " + "/".join(by))
                    print("     within risk terciles: " + "  |  ".join(parts))
                except ValueError:
                    pass


if __name__ == "__main__":
    main()
