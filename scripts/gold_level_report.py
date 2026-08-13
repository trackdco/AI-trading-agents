#!/usr/bin/env python3
"""Which loci, arms and confluences carry an edge on GC — the E1 read for gold.

Every number is dual-currency and day-clustered (Law 3, BR-42), split into halves so a
cell has to clear zero in BOTH — that is the E1.4 bar the NQ census used, and it is the
reason only two of its seven loci survived. Headline claims are calibrated against
outcome shuffles within (session, arm) cells (BR-97).

The book convention is stated rather than assumed, because BR-10 records that the same
population reads -0.04R to +0.20R depending on it: FIRST TRIGGER PER STRUCTURAL FIGHT
(one row per cluster_id), shipped exit, no selection inside the cell.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.research.tomtrades import autopsy as AU

MIN_N = 30


def first_of_fight(df: pd.DataFrame) -> pd.DataFrame:
    """One row per structural fight. Counting every retrigger inflates n and shrinks
    every interval, which is how a book reports significance it has not earned."""
    return (df.sort_values("t").groupby(["locus", "arm", "cluster_id"], as_index=False)
              .first())


def cell(d: pd.DataFrame, label: str, days_all: np.ndarray) -> dict | None:
    if len(d) < MIN_N:
        return None
    lo, hi = AU.dboot_mean(d, "out")
    mid = days_all[len(days_all) // 2]
    h1, h2 = d[d.sess_day < mid], d[d.sess_day >= mid]
    # only the LOWER bound matters: the E1.4 bar is "clears zero in both eras"
    l1 = AU.dboot_mean(h1, "out")[0] if len(h1) >= MIN_N else np.nan
    l2 = AU.dboot_mean(h2, "out")[0] if len(h2) >= MIN_N else np.nan
    return {"cell": label, "n": len(d), "days": d.sess_day.nunique(),
            "per_day": len(d) / max(d.sess_day.nunique(), 1),
            "win_pct": 100 * float((d["out"] > 0).mean()),
            "ev": float(d["out"].mean()), "lo": lo, "hi": hi,
            "h1_ev": float(h1["out"].mean()) if len(h1) else np.nan,
            "h2_ev": float(h2["out"].mean()) if len(h2) else np.nan,
            "both_eras_clear": bool(l1 > 0 and l2 > 0),
            "total_r": float(d["out"].sum())}


def main() -> None:
    src = sys.argv[1] if len(sys.argv) > 1 else "output/gold_level_census_cost0.2.parquet"
    raw = pd.read_parquet(ROOT / src)
    exit_col = sys.argv[2] if len(sys.argv) > 2 else "out_ship"
    df = first_of_fight(raw)
    df = df[df[exit_col].notna()].copy()
    df["out"] = df[exit_col].astype(float)
    days_all = np.array(sorted(df.sess_day.unique()))
    print(f"{len(raw):,} triggers -> {len(df):,} first-of-fight rows, "
          f"{df.sess_day.nunique():,} days, exit={exit_col}", flush=True)

    rows = [cell(df, "ALL", days_all)]
    for (lo_, arm), g in df.groupby(["locus", "arm"]):
        rows.append(cell(g, f"{lo_} · {arm}", days_all))
    for arm, g in df.groupby("arm"):
        rows.append(cell(g, f"ARM {arm}", days_all))
    for s, g in df.groupby("session"):
        rows.append(cell(g, f"SESSION {s}", days_all))
    t = pd.DataFrame([r for r in rows if r]).sort_values("ev", ascending=False)
    pd.set_option("display.width", 250)
    print("\n=== LOCUS x ARM, first-of-fight, shipped exit ===")
    print(t.round(3).to_string(index=False), flush=True)
    t.to_csv(ROOT / "output/gold_level_report.csv", index=False)

    print("\n=== CONFLUENCE SWEEPS (on the whole book) ===")
    df["risk_w"] = df["risk"] / df["w15"]
    for col, q in (("risk", 5), ("risk_w", 5), ("w15", 5), ("n_attempts", 0)):
        tab = AU.bucket_table(df, col, q=q) if q else AU.bucket_table(df, col, q=6)
        tab = tab[tab["n"] >= MIN_N]
        if len(tab):
            print(f"\n-- {col}")
            print(tab.round(3).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
