#!/usr/bin/env python3
"""Golden deep-dive: fit-stability, two-way OOS, and kind/book splits (ANGUS 2026-07-26:
"you still need to go deeper into the golden window breakdown").

The sub-window subsets were greedily selected on all 13 months — fine for discovery,
inadmissible for adoption. This runs the honest version per sub-window:

  DERIVE on 2025 alone (survival rule within-fold: >=$60/t gap, n>=12/cell; greedy max-3
  conjunction maximizing fold total) -> FREEZE -> test blind on 2026. Then the reverse.
  A subset is real if (a) both derivations pick overlapping rules, (b) both OOS folds are
  positive. Plus: rejection/displacement and E3/E4-book splits per sub-window.

    python -m scripts.golden_deep_oos
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

WINDOWS = {
    "0940-1000": ("output/golden_flow_matrix.parquet", lambda hm: hm < 600),
    "1000-1015": ("output/golden_flow_matrix.parquet", lambda hm: hm >= 600),
    "1015-1030": ("output/late_a_flow_matrix.parquet", None),
}


def build_checks(X: pd.DataFrame) -> dict:
    long = X.direction == "long"
    wall_behind = np.where(long, X.get("dep_wall_below_d"), X.get("dep_wall_above_d"))
    wall_ahead = np.where(long, X.get("dep_wall_above_d"), X.get("dep_wall_below_d"))
    wall_ahead_sz = np.where(long, X.get("dep_wall_above_sz"), X.get("dep_wall_below_sz"))
    has_depth = X.get("dep_thick", pd.Series(np.nan, index=X.index)).notna()
    return {
        "W-nowall-behind": pd.Series(pd.isna(wall_behind), index=X.index).where(has_depth),
        "D-wall-ahead": pd.Series(pd.notna(wall_ahead), index=X.index).where(has_depth),
        "WALLSZ>=7": pd.Series(pd.notna(wall_ahead)
                               & (pd.Series(wall_ahead_sz, index=X.index) >= 7),
                               index=X.index).where(has_depth),
        "F-filldelta": X.get("fill_delta_conf") == 1,
        "d5conf": X.get("d5_conf") == 1,
        "d15conf": X.get("d15_conf") == 1,
        "d30conf": X.get("d30_conf") == 1,
        "C-opsofar": X.get("op_sofar_conf") == 1,
        "pmsofar": X.get("pm_sofar_conf") == 1,
        "G-vwapd": X.get("ent_vs_vwap_sd_dir", pd.Series(np.nan, index=X.index)) >= 0.107,
        "REJ": X.kind == "rejection_block",
    }


def derive(X: pd.DataFrame, checks: dict) -> list:
    """Survivor scan + greedy conjunction on ONE fold. Returns [(name, want_on), ...]."""
    surv = {}
    for name, flag in checks.items():
        m = pd.Series(flag).astype("boolean")
        on, off = X[(m == True).reindex(X.index, fill_value=False)], X[(m == False).reindex(X.index, fill_value=False)]  # noqa: E712
        if len(on) < 12 or len(off) < 12:
            continue
        gap = on.dollars.mean() - off.dollars.mean()
        if abs(gap) >= 60:
            surv[name] = gap > 0
    keep = pd.Series(True, index=X.index)
    cur = X
    rules = []
    for name, want in sorted(surv.items(),
                             key=lambda kv: -(pd.Series(checks[kv[0]]).astype("boolean") == kv[1]).sum()):
        flag = (pd.Series(checks[name]).astype("boolean") == want).reindex(X.index, fill_value=False)
        trial = keep & flag
        t = X[trial]
        if len(t) >= 15 and t.dollars.sum() > cur.dollars.sum():
            keep, cur = trial, t
            rules.append((name, want))
        if len(rules) == 3:
            break
    return rules


def apply_rules(X: pd.DataFrame, checks: dict, rules: list) -> pd.DataFrame:
    keep = pd.Series(True, index=X.index)
    for name, want in rules:
        keep &= (pd.Series(checks[name]).astype("boolean") == want).reindex(X.index, fill_value=False)
    return X[keep]


def stats(s: pd.DataFrame) -> str:
    if not len(s):
        return "(empty)"
    mo = s.groupby("month").dollars.sum()
    return (f"{len(s):>3}t  ${s.dollars.sum():>+8,.0f}  {s.r_multiple.sum():>+6.1f}R  "
            f"win {(s.dollars > 0).mean() * 100:.0f}%  green {int((mo > 0).sum())}/{len(mo)}")


def main() -> None:
    for wname, (path, hmf) in WINDOWS.items():
        X = pd.read_parquet(path)
        if hmf is not None:
            et = pd.to_datetime(X.fill_ts.str.replace("T", " "), utc=True, format="mixed")
            hm = et.dt.tz_convert("America/New_York")
            X = X[hmf(hm.dt.hour * 60 + hm.dt.minute)].copy()
        X["yr"] = X.month.str[:4]
        checks = build_checks(X)
        A, B = X[X.yr == "2025"], X[X.yr == "2026"]
        print(f"\n================== {wname}  (n={len(X)}: {len(A)} in 2025, {len(B)} in 2026) ==================")
        print(f"  baseline: {stats(X)}")
        for da, db, la, lb in ((A, B, "2025", "2026"), (B, A, "2026", "2025")):
            rules = derive(da, checks)
            rl = " & ".join(f"{n}={'ON' if w else 'OFF'}" for n, w in rules) or "(none)"
            ins = apply_rules(da, checks, rules)
            oos = apply_rules(db, checks, rules)
            print(f"  derive {la}: {rl}")
            print(f"    in-sample {la}: {stats(ins)}")
            print(f"    ==> OOS {lb}  : {stats(oos)}")

        # kind and book splits (full sample, descriptive)
        print("  --- kind split ---")
        for k, s in X.groupby("kind"):
            print(f"    {k:<18} {stats(s)}")
        vec = pd.read_csv("output/regime_vector.csv")
        war = {r.day for _, r in vec.iterrows()
               if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
        day = X.fill_ts.str[:10]
        X["book"] = np.where(day.isin(war), "E4-war", "E3-calm")
        print("  --- book split ---")
        for k, s in X.groupby("book"):
            print(f"    {k:<18} {stats(s)}")


if __name__ == "__main__":
    main()
