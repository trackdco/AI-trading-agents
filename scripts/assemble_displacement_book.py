#!/usr/bin/env python3
"""ASSEMBLY TEST — do the displacement sweep's verified survivors work JOINTLY?

The sweep (docs/FINDING-displacement-sweep.md) produced one-at-a-time lifts. A
book is a stack. This runs the gold-scoped survivor stack as a waterfall and asks
the only question that matters under the era rule: is the final stack positive
NET OF COSTS in 2025 (discover) as well as 2026 (confirm)?

Stack, in order (each stage on top of the previous):
  G0  gold session (entry minute in [580,630)), depth-evaluable rows
  G1  + candle risk >= 7pt              (structure family, strongest survivor)
  G2  + Mon-Thu                          (structure, borderline survivor)
  G3  + D == 1                           (depth: no visible vacuum ahead)
  G4  + WALLSZ == 1  [masked]            (depth: wall >= 7 ahead, gold-scoped)
  G5  + bp5opp == 1                      (pre-signal absorption, gold-scoped)

Exit arms: 2R-or-stop, EOD-hold, and MENU = hold when RANGEX<1 else 2R (the
RANGEX hold-derate survivor: big signal bars are worse to hold).

Costs: R_net = R - (slip_pts + comm_pts)/risk with slip 1 tick (0.25pt) adverse
and $5/RT at $20/pt (0.25pt) — the sweep's deciding column. 2-tick shown too.

Honesty rails baked in: WALLSZ masked on dep_thick (the verified zero-fill bug);
bp5opp from the VERSIONED builder src/canon/features.py::bp5opp anchored at the
SIGNAL BAR START (pure pre-signal window, the surviving formulation); NaN feature
= row excluded at that stage with the count printed, never zero-filled; episode
key = same-day same-direction chain with gaps <= 15min; every stage reports
per-trade AND per-episode AND per-day views. FIT ONLY. HOLDOUT NOT TOUCHED.

    python -m scripts.assemble_displacement_book
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.audit_displacement_entry import TFMIN, NY  # noqa: E402
from scripts.build_l2_outcomes import load_bars          # noqa: E402
from scripts.honest_disp_depth import build              # noqa: E402
from src.canon.features import bp5opp                    # noqa: E402

SLIP_TICK = 0.25
COMM_PTS = 0.25            # $5 RT at $20/pt


def add_features(A: pd.DataFrame) -> pd.DataFrame:
    A = A.copy()
    A["T"] = pd.to_datetime(A["T"])
    A["dow"] = pd.to_datetime(A.day).dt.dayofweek          # 0=Mon .. 4=Fri
    A["tfm"] = A.tf.map(TFMIN)

    # bp5opp — versioned builder, anchored at the signal bar START (pre-signal).
    fp = pd.read_parquet(ROOT / "output/fp_minutes.parquet")
    fp = fp.sort_index()
    vals = np.full(len(A), np.nan)
    for i, (T, tfm, direction) in enumerate(zip(A["T"], A.tfm, A.direction)):
        start = T - pd.Timedelta(minutes=int(tfm))
        vals[i] = bp5opp(fp, direction, start)
    A["bp5"] = vals

    # RANGEX — signal-bar range vs trailing 20 same-TF-bar mean range, built from
    # 1m bars resampled per (day, tf) with label='right' (the census convention).
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()
    rng = {}
    for (day, tfm), _ in A.groupby(["day", "tfm"]):
        db = bars.loc[day]
        r = (db.high.resample(f"{tfm}min", label="right", closed="left").max()
             - db.low.resample(f"{tfm}min", label="right", closed="left").min())
        rng[(day, tfm)] = (r, r.shift(1).rolling(20).mean())
    rx = np.full(len(A), np.nan)
    for i, (day, tfm, T) in enumerate(zip(A.day, A.tfm, A["T"])):
        r, atr = rng[(day, tfm)]
        if T in r.index and T in atr.index and atr.loc[T] == atr.loc[T] and atr.loc[T] > 0:
            rx[i] = r.loc[T] / atr.loc[T]
    A["rangex"] = rx

    # episode key: same day+direction, chained while successive T gaps <= 15min
    A = A.sort_values(["day", "direction", "T"], kind="mergesort").reset_index(drop=True)
    new = (A.day.ne(A.day.shift()) | A.direction.ne(A.direction.shift())
           | (A["T"] - A["T"].shift()).gt(pd.Timedelta(minutes=15)))
    A["episode"] = new.cumsum()
    return A


def net(A: pd.DataFrame, rcol: str, ticks: int) -> pd.Series:
    return A[rcol] - (SLIP_TICK * ticks + COMM_PTS) / A.risk


def arms(A: pd.DataFrame) -> pd.DataFrame:
    A = A.copy()
    # MENU: hold when the signal bar is NOT extended vs ATR, else take the 2R arm.
    # rangex NaN (first 20 bars of a day) falls back to 2R — the conservative arm.
    A["r_menu"] = np.where(A.rangex < 1.0, A.r_hold, A.r_2r)
    return A


def stage_report(name: str, A: pd.DataFrame) -> None:
    print(f"\n--- {name} ---")
    for era in ("2025", "2026"):
        d = A[A.era == era]
        if len(d) == 0:
            print(f"  {era}: empty")
            continue
        eps, days = d.episode.nunique(), d.day.nunique()
        line = f"  {era}: n={len(d):>5} eps={eps:>4} days={days:>3}"
        for rcol, nm in (("r_2r", "2R"), ("r_hold", "hold"), ("r_menu", "menu")):
            g = d[rcol].mean()
            n1 = net(d, rcol, 1).mean()
            n2 = net(d, rcol, 2).mean()
            tot1 = net(d, rcol, 1).sum()
            # clustered views at 1 tick: mean of per-episode means, mean of per-day sums
            epm = net(d, rcol, 1).groupby(d.episode).mean().mean()
            dsum = net(d, rcol, 1).groupby(d.day).sum()
            line2 = (f"    {nm:<5} gross {g:+.3f} | net1t {n1:+.3f} (ep-mean {epm:+.3f}) "
                     f"| net2t {n2:+.3f} | totR1t {tot1:+8.1f} | "
                     f"day-sum mean {dsum.mean():+.3f}, {int((dsum > 0).sum())}/{len(dsum)} days+")
            if rcol == "r_2r":
                print(line)
            print(line2)


def main() -> None:
    A = arms(add_features(build()))
    P = A[(A.risk >= 2.0)].copy()
    print(f"population risk>=2pt: {len(P):,} | bp5opp NaN: {int(P.bp5.isna().sum())} "
          f"| rangex NaN: {int(P.rangex.isna().sum())}")

    G0 = P[(P.sess == "gold") & P.dep_thick.notna()]
    G1 = G0[G0.risk >= 7.0]
    G2 = G1[G1.dow <= 3]
    G3 = G2[G2.D == 1]
    G4 = G3[G3.WALLSZ.where(G3.dep_thick.notna()) == 1]
    n_bp_nan = int(G4.bp5.isna().sum())
    G5 = G4[G4.bp5 == 1]
    stage_report("G0 gold, depth-evaluable", G0)
    stage_report("G1 + risk>=7pt", G1)
    stage_report("G2 + Mon-Thu", G2)
    stage_report("G3 + D==1", G3)
    stage_report("G4 + WALLSZ==1 (masked)", G4)
    print(f"\n  [G5 drops {n_bp_nan} bp5opp-NaN rows explicitly]")
    stage_report("G5 + bp5opp==1  == THE STACK", G5)

    # the era rule, stated by the machine so nobody argues with the printout:
    for rcol, nm in (("r_2r", "2R"), ("r_hold", "hold"), ("r_menu", "menu")):
        ok25 = net(G5[G5.era == "2025"], rcol, 1).mean() > 0
        ok26 = net(G5[G5.era == "2026"], rcol, 1).mean() > 0
        ep25 = net(G5[G5.era == "2025"], rcol, 1).groupby(G5[G5.era == "2025"].episode).mean().mean() > 0
        ep26 = net(G5[G5.era == "2026"], rcol, 1).groupby(G5[G5.era == "2026"].episode).mean().mean() > 0
        verdict = "PASS" if (ok25 and ok26 and ep25 and ep26) else "FAIL"
        print(f"  ERA RULE [{nm}] net-1t per-trade 2025/2026 {ok25}/{ok26}, "
              f"episode-mean {ep25}/{ep26} -> {verdict}")
    print("\nNOTE: naive exits, no sizing, no V8 menu. Direction-finder for the "
          "L1-L4 rebuild, not a book. HOLDOUT NOT TOUCHED.")


if __name__ == "__main__":
    main()
