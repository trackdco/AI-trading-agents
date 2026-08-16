#!/usr/bin/env python3
"""AB-1 robustness battery — declared in docs/PREREG-displacement-canon.md §7
BEFORE this run. Candidate: VOLX>=1.5 & WALLSZ==1 & risk>=7pt on A/B
displacement entries, hold-to-close, net 1 tick + $5/RT. FIT ONLY.

Legs: (1) clustered views + LODO; (2) 3x3x3 threshold neighborhood — needs
wall-size regridded, so ahead_sz is used directly; (3) session split, 2-tick
column, tail share. Fails any leg => AB-1 dies (prereg).

    python -m scripts.ab1_robustness
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

COST1, COST2 = 0.5, 0.75      # points: (1|2) ticks + commission


def net(d: pd.DataFrame, pts: float) -> pd.Series:
    return d.r_hold - pts / d.risk


def main() -> None:
    D = pd.read_parquet(ROOT / "output/l3_ab_winner_loser.parquet")
    D["T"] = pd.to_datetime(D["T"])
    D = D.sort_values(["day", "direction", "T"], kind="mergesort").reset_index(drop=True)
    new = (D.day.ne(D.day.shift()) | D.direction.ne(D.direction.shift())
           | (D["T"] - D["T"].shift()).gt(pd.Timedelta(minutes=15)))
    D["episode"] = new.cumsum()
    D["wall_ok"] = (D["D"] == 1) & D.ahead_sz.notna()

    S = D[(D.VOLX >= 1.5) & (D.WALLSZ == 1) & (D.risk >= 7)]
    print("=== LEG 1: clustered views (net-1t) ===")
    leg1_pass = True
    for era in ("2025", "2026"):
        d = S[S.era == era]
        tr = net(d, COST1).mean()
        ep = net(d, COST1).groupby(d.episode).mean().mean()
        dsum = net(d, COST1).groupby(d.day).sum()
        lodo = min(net(d[d.day != x], COST1).mean() for x in d.day.unique())
        ok = tr > 0 and ep > 0
        leg1_pass &= ok
        print(f"  {era}: n={len(d):,} eps={d.episode.nunique():,} days={d.day.nunique()} | "
              f"per-trade {tr:+.3f} | episode-mean {ep:+.3f} | day-sum mean {dsum.mean():+.3f} "
              f"({int((dsum>0).sum())}/{len(dsum)} days+) | LODO min {lodo:+.3f} | "
              f"{'OK' if ok else 'FAIL'}")

    print("\n=== LEG 2: threshold neighborhood (net-1t per-trade, 2025 | 2026) ===")
    cells = []
    for v in (1.25, 1.5, 1.75):
        for w in (5, 7, 10):
            for rk in (5, 7, 10):
                m = (D.VOLX >= v) & D.wall_ok & (D.ahead_sz >= w) & (D.risk >= rk)
                r25 = net(D[m & (D.era == "2025")], COST1).mean()
                r26 = net(D[m & (D.era == "2026")], COST1).mean()
                n25 = int((m & (D.era == "2025")).sum())
                cells.append((v, w, rk, n25, r25, r26))
                tag = "*" if (v, w, rk) == (1.5, 7, 7) else " "
                print(f"  {tag}vol>={v:<5} wall>={w:<3} risk>={rk:<3} "
                      f"n25={n25:>5} | {r25:+.3f} | {r26:+.3f}")
    pos = sum(1 for *_, a, b in cells if a > 0 and b > 0)
    print(f"  both-era-positive cells: {pos}/27")
    leg2_pass = pos >= 14

    print("\n=== LEG 3: sessions, 2-tick, tails (candidate cell) ===")
    for era in ("2025", "2026"):
        d = S[S.era == era]
        n2 = net(d, COST2).mean()
        tail = d.r_hold.nlargest(max(1, int(len(d) * .05))).sum() / d.r_hold.sum() \
            if d.r_hold.sum() > 0 else float("nan")
        print(f"  {era}: net-2t {n2:+.3f} | top-5% share of total R {tail*100:.0f}%")
        for s in ("pre", "gold", "other"):
            ds = d[d.sess == s]
            if len(ds) < 15:
                continue
            print(f"    {s:<6} n={len(ds):>4} net-1t {net(ds, COST1).mean():+.3f}")

    print(f"\nVERDICT: leg1 {'PASS' if leg1_pass else 'FAIL'} | "
          f"leg2 {'PASS' if leg2_pass else 'FAIL'} ({pos}/27 need >=14) | "
          f"leg3 reported above. AB-1 "
          f"{'ADVANCES to the full ladder' if leg1_pass and leg2_pass else 'DIES (prereg)'}."
          f" HOLDOUT NOT TOUCHED.")


if __name__ == "__main__":
    main()
