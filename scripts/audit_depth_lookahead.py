#!/usr/bin/env python3
"""LOOKAHEAD AUDIT — does the depth snapshot's end-of-minute convention inflate W/D?

The archive stores, for minute M, the LAST book state in M. `features.depth_at` selects
`ts <= minute`, so a fill in minute M is scored on the book as it looked at ~M:59 —
up to 60s of information the live path cannot have (live stamps the in-memory book
as-of the fill instant).

HONEST COUNTERFACTUAL: score the same fills on the last book state in minute M-1, which
is ~the book at the START of minute M — i.e. what was actually knowable at a fill on the
M boundary. Then re-run the exact l3_check_trial lift table on both versions.

    python -m scripts.audit_depth_lookahead
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.score_canon_span import depth_file          # noqa: E402
from src.canon.features import depth_at                  # noqa: E402

NY = "America/New_York"
DEPTH_DIRS = {"fit": ["data/reference/depth_2025", "data/reference/depth_2026",
                      "data/reference/depth_apr2026"],
              "holdout": ["data/reference/depth_2023_24"]}


def load_depth(span: str, day: str):
    p = depth_file([ROOT / d for d in DEPTH_DIRS[span]], day)
    if p is None:
        return None
    d = pd.read_csv(p)
    d["ts"] = pd.to_datetime(d.ts, utc=True).dt.tz_convert(NY)
    return d


def recompute(span: str, lag_minutes: int) -> pd.DataFrame:
    """Recompute the depth family for every scored candidate, shifting the snapshot
    selection back by `lag_minutes` (0 = the shipped behaviour)."""
    S = pd.read_parquet(ROOT / f"output/l3_scored_{span}.parquet").copy()
    S["fill_ny"] = pd.to_datetime(S.fill_ts, format="mixed", utc=True).dt.tz_convert(NY)
    out = []
    for day, g in S.groupby("day", sort=True):
        dep = load_depth(span, day)
        if dep is None:
            continue
        for r in g.itertuples():
            m = r.fill_ny - pd.Timedelta(minutes=lag_minutes)
            f = depth_at(dep, m, float(r.entry), r.direction)
            out.append({"day": day, "ts": r.ts, "direction": r.direction,
                        "dep_thick": f.get("dep_thick", np.nan),
                        "dep_wall_below_d": f.get("dep_wall_below_d", np.nan),
                        "dep_wall_above_d": f.get("dep_wall_above_d", np.nan),
                        "dep_wall_below_sz": f.get("dep_wall_below_sz", np.nan),
                        "dep_wall_above_sz": f.get("dep_wall_above_sz", np.nan)})
    return pd.DataFrame(out)


def bits(S: pd.DataFrame) -> pd.DataFrame:
    """W / D / WALLSZ from a depth frame, exactly as l3_check_trial builds them."""
    long = S.direction == "long"
    S = S.copy()
    S["W"] = np.where(long, S.dep_wall_below_d.isna(), S.dep_wall_above_d.isna()).astype(float)
    S["W"] = S["W"].where(S.dep_thick.notna())
    S["D"] = pd.Series(np.where(long, S.dep_wall_above_d.notna(), S.dep_wall_below_d.notna()),
                       index=S.index).astype(float).where(S.dep_thick.notna())
    ahead_sz = np.where(long, S.dep_wall_above_sz, S.dep_wall_below_sz)
    S["WALLSZ"] = ((S.D == 1) & (pd.Series(ahead_sz, index=S.index) >= 7)).astype(float)
    return S


def lift(F: pd.DataFrame, check: str, sess: str, era: str) -> dict | None:
    d = F[(F.sess == sess) & (F.era == era) & F[check].notna()]
    on, off = d[d[check] == 1], d[d[check] == 0]
    if len(on) < 15 or len(off) < 15:
        return None
    return {"n_on": len(on), "n_off": len(off),
            "wr_on": (on.dollars_1lot > 0).mean(), "wr_off": (off.dollars_1lot > 0).mean(),
            "r_on": on.R.mean(), "r_off": off.R.mean(),
            "lift": on.R.mean() - off.R.mean()}


def main() -> None:
    for span in ("fit", "holdout"):
        base = pd.read_parquet(ROOT / f"output/l3_scored_{span}.parquet")
        base = base[(base.risk >= 7) & (base.risk <= 60)]
        key = ["day", "ts", "direction"]
        print(f"\n{'='*78}\n{span.upper()} — recomputing depth at lag 0 (shipped) and lag 1 (honest)\n{'='*78}")
        frames = {}
        shipped = base[key + ["W", "D", "WALLSZ"]].rename(
            columns={"W": "W_orig", "D": "D_orig", "WALLSZ": "WALLSZ_orig"})
        for lag in (0, 1):
            R = recompute(span, lag)
            M = base.drop(columns=["W", "D", "WALLSZ"]).merge(R, on=key, how="inner",
                                                              suffixes=("_shipdep", ""))
            M = M.merge(shipped, on=key, how="left")
            frames[lag] = bits(M)
            print(f"  lag {lag}: {len(M):,} rows recomputed")

        # agreement between shipped bits and the lag-0 recompute = sanity check
        f0 = frames[0]
        for chk in ("W", "D", "WALLSZ"):
            both = f0[f0[chk].notna() & f0[f"{chk}_orig"].notna()]
            agree = (both[chk] == both[f"{chk}_orig"]).mean() * 100
            print(f"  sanity lag0 vs shipped {chk}: {agree:.2f}% agree (n={len(both)})")

        print(f"\n  {'check':<8}{'sess':<6}{'era':<9}{'lag':>4}{'n_on':>6}{'WR on':>8}{'WR off':>8}{'lift_R':>9}")
        for chk, sess in (("W", "pre"), ("D", "gold"), ("WALLSZ", "gold")):
            for era in sorted(frames[0].era.unique()):
                for lag in (0, 1):
                    v = lift(frames[lag], chk, sess, era)
                    if v is None:
                        continue
                    tag = "SHIP" if lag == 0 else "HON "
                    print(f"  {chk:<8}{sess:<6}{era:<9}{tag:>4}{v['n_on']:>6}"
                          f"{v['wr_on']:>8.3f}{v['wr_off']:>8.3f}{v['lift']:>+9.3f}")

        # how many rows actually change bit value between lag 0 and lag 1
        f1 = frames[1]
        j = f0[key + ["W", "D", "WALLSZ"]].merge(f1[key + ["W", "D", "WALLSZ"]], on=key,
                                                 suffixes=("_0", "_1"))
        for chk in ("W", "D", "WALLSZ"):
            a, b = j[f"{chk}_0"], j[f"{chk}_1"]
            m = a.notna() & b.notna()
            print(f"  {chk}: {(a[m] != b[m]).sum()} of {m.sum()} rows flip between lag0 and lag1 "
                  f"({(a[m] != b[m]).mean()*100:.2f}%)")


if __name__ == "__main__":
    main()
