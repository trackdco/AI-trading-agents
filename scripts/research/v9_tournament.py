#!/usr/bin/env python3
"""RESEARCH ONLY (claude/agent-exit-london-r1). Stage 1, S1.1/S1.3: V0/V1/V8/V9 on the
rev-3 stack, with V9's mechanism decomposition vs V1 and V8.

REUSE, DON'T REBUILD (S5.1): imports load_pop, build_book, CONFIGS, serial_walk from
scripts.london_holdout_report — the frozen rev-3 pipeline — and calls them unmodified.
`swap_arm` below is a GENERIC version of that module's `swap_v1` (same join logic, any
L2 outcome file), written here so the frozen file is never edited.

Format matches docs/LONDON-MGMT-TOURNAMENT.md exactly, extended with a V9 column.

    python -m scripts.research.v9_tournament                    # V0/V1/V8/V9-default
    python -m scripts.research.v9_tournament --grid              # + the 5 grid cells
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.london_combined_job import maxdd  # noqa: E402
from scripts.london_holdout_report import CONFIGS, build_book, load_pop  # noqa: E402
from src.research.holdout_guard import assert_path_fit_only  # noqa: E402

KEY = ["ts", "tf", "direction"]
OUTCOLS = ["dollars", "R", "exit_ts", "exit_reason"]


def swap_arm(P: pd.DataFrame, l2_path: str) -> pd.DataFrame:
    """Generic form of london_holdout_report.swap_v1 — any L2 outcome file, same join
    logic (exact reproduction, not a reimplementation): 1:1 on (ts, tf, direction),
    hard-fail on any unmatched row."""
    assert_path_fit_only(l2_path)
    apath = ROOT / l2_path
    if not apath.exists():
        raise SystemExit(f"MISSING ARTIFACT: {apath}")
    A = pd.read_parquet(apath).rename(columns={"dollars_1lot": "dollars"})
    A["exit_ts"] = pd.to_datetime(A.exit_ts, format="mixed", utc=True)
    P = P.drop(columns=OUTCOLS, errors="ignore").merge(
        A[KEY + OUTCOLS].drop_duplicates(KEY), on=KEY, how="left", validate="1:1")
    nan = P.dollars.isna()
    if nan.sum() > 1:
        raise SystemExit(f"SWAP FAILURE ({l2_path}): {int(nan.sum())} rows without "
                         "outcomes — investigate before trusting anything downstream")
    if nan.any():
        # documented single case (session-3 handoff trap #8 /
        # docs/LONDON-MGMT-TOURNAMENT.md): 2025-11-27 Thanksgiving 5min short never
        # resolves under V0 set-and-forget before the holiday session's bars end.
        # Disclosed, dropped from THIS ARM ONLY — never silent.
        print(f"NOTE: dropping {int(nan.sum())} unresolved candidate from {l2_path}: "
              f"{P[nan][['day', 'tf', 'direction']].to_dict('records')}")
        P = P[~nan]
    return P


def arm_stack(P: pd.DataFrame, l2_path: str | None) -> pd.DataFrame:
    Pa = P if l2_path is None else swap_arm(P, l2_path)
    b, _ = build_book(Pa, "rev3")
    return b


def stats(name: str, b: pd.DataFrame) -> dict:
    b = b.sort_values(["day", "fill_ts"], kind="mergesort")
    r = {"name": name, "n": len(b), "net": float(b.dollars.sum()),
         "wr": float((b.R > 0).mean()), "meanr": float(b.R.mean()),
         "dd": maxdd(b.dollars.reset_index(drop=True))}
    r["netdd"] = r["net"] / max(r["dd"], 1)
    for era in ("2025", "2026"):
        g = b[b.era == era]
        r[era] = (f"{len(g)}/{(g.R > 0).mean() * 100:.0f}%/{g.R.mean():+.2f}/"
                 f"${g.dollars.sum():+,.0f}" if len(g) else "—")
    r["exits"] = b.exit_reason.value_counts().to_dict()
    return r


def decompose(control: pd.DataFrame, test: pd.DataFrame, label: str) -> dict:
    """Defense (delta on control LOSERS) / offense (delta on control WINNERS), on
    the intersection of taken trades — same method as
    docs/LONDON-MGMT-TOURNAMENT.md's V1-vs-V8 breakdown."""
    kc = control.set_index(KEY)
    kt = test.set_index(KEY)
    common = kc.index.intersection(kt.index)
    c, t = kc.loc[common], kt.loc[common]
    losers = c.R <= 0
    d = t.dollars - c.dollars
    return {"label": label, "n_common": len(common),
           "defense_delta": float(d[losers].sum()), "n_losers": int(losers.sum()),
           "offense_delta": float(d[~losers].sum()), "n_winners": int((~losers).sum()),
           "net_delta": float(d.sum()),
           "only_control": len(kc) - len(common), "only_test": len(kt) - len(common)}


def print_table(rows: list[dict]) -> None:
    print(f"\n{'arm':<28} {'n':>4} {'WR':>5} {'meanR':>7} {'net':>12} {'maxDD':>9} "
          f"{'net/DD':>7}")
    for r in rows:
        print(f"{r['name']:<28} {r['n']:>4} {r['wr'] * 100:>4.0f}% {r['meanr']:>+7.3f} "
              f"${r['net']:>+10,.0f} ${r['dd']:>7,.0f} {r['netdd']:>6.1f}x")
        print(f"  {'':<26} 2025 {r['2025']}  |  2026 {r['2026']}")
        print(f"  {'':<26} exits {r['exits']}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", action="store_true", help="also report the 5 V9 grid cells")
    a = ap.parse_args()

    P = load_pop("fit")
    arms = {
        "V8 shipped (partial+trail)": None,
        "V1 BE at +1R": "output/l2_outcomes_london_fit_v1.parquet",
        "V0 set-and-forget": "output/l2_outcomes_london_fit_v0.parquet",
        "V9 default (arm=6.0, lock=0.5)": "output/l2_outcomes_london_fit_v9.parquet",
    }
    books = {name: arm_stack(P, path) for name, path in arms.items()}
    rows = [stats(name, b) for name, b in books.items()]
    print_table(rows)

    print("\n=== V9 mechanism decomposition (S1.3) ===")
    for ctrl_name in ("V1 BE at +1R", "V8 shipped (partial+trail)"):
        dec = decompose(books[ctrl_name], books["V9 default (arm=6.0, lock=0.5)"],
                        f"V9 vs {ctrl_name}")
        print(f"\n{dec['label']} ({dec['n_common']} shared trades):")
        print(f"  defense (control LOSERS, n={dec['n_losers']}): "
              f"${dec['defense_delta']:+,.0f}")
        print(f"  offense (control WINNERS, n={dec['n_winners']}): "
              f"${dec['offense_delta']:+,.0f}")
        print(f"  net delta on shared trades: ${dec['net_delta']:+,.0f}")
        print(f"  only-in-control: {dec['only_control']} | only-in-V9: "
              f"{dec['only_test']}")

    if a.grid:
        gpath = ROOT / "output/research/l2_outcomes_london_fit_v9grid.parquet"
        if not gpath.exists():
            raise SystemExit(f"grid file missing: {gpath} — run "
                             "build_l2_v9_grid.py first")
        G = pd.read_parquet(gpath).rename(columns={"dollars_1lot": "dollars"})
        G["exit_ts"] = pd.to_datetime(G.exit_ts, format="mixed", utc=True)
        cells = sorted(G[["arm_r", "lock_frac"]].drop_duplicates().itertuples(index=False))
        print(f"\n=== S1.2 grid ({len(cells)} cells + default) ===")
        grid_rows = [rows[-1]]  # default cell already computed above
        for arm_r, lock_frac in cells:
            cell = G[(G.arm_r == arm_r) & (G.lock_frac == lock_frac)]
            Pc = P.drop(columns=OUTCOLS, errors="ignore").merge(
                cell[KEY + OUTCOLS].drop_duplicates(KEY), on=KEY, how="left",
                validate="1:1")
            nan = Pc.dollars.isna()
            if nan.sum() > 1:
                raise SystemExit(f"GRID CELL {arm_r}/{lock_frac}: "
                                 f"{int(nan.sum())} unmatched rows")
            if nan.any():
                # same disclosed single case as swap_arm: 2025-11-27 Thanksgiving 5min
                # short never resolves under any set-and-forget-style (V0/V9) management
                # before the holiday session's bars end. Dropped from THIS CELL only.
                print(f"NOTE: dropping {int(nan.sum())} unresolved candidate from grid "
                      f"cell {arm_r}/{lock_frac}: "
                      f"{Pc[nan][['day', 'tf', 'direction']].to_dict('records')}")
                Pc = Pc[~nan]
            b, _ = build_book(Pc, "rev3")
            grid_rows.append(stats(f"V9 arm={arm_r} lock={lock_frac}", b))
        print_table(grid_rows)


if __name__ == "__main__":
    main()
