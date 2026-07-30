#!/usr/bin/env python3
"""LONDON ladder at the rev-3 baseline (09:45) — Brake's simplified spec, $200 base.

THE ASK (Brake, 2026-07-30): "1.5x on A+ set ups on monday and friday, and 0.5x on low
conviction set ups" — i.e. A+ & (Mon|Fri) = 1.5, neither-grade = 0.5, all else 1.0.
Re-anchors the ladder lab (docs/LONDON-LADDER-LAB.md) to the 09:45 ruling; same
conventions: $200 base micros, per-era nets, zero-edge shuffle (5,000x within era),
real gain = ladder improvement minus its risk-shuffling component. V8 outcomes are the
strategy of record; V1 rows included as the exit candidate preview. Calendar tiers
remain today-mined and unproven; sizing stays flat live (ANGUS ruling).

    python -m scripts.london_ladder_945
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.london_combined_job import lon_book, maxdd, write
from scripts.london_conviction import lonmins
from scripts.london_holdout_report import load_pop
from scripts.london_mgmt_tournament import swap_outcomes
from scripts.london_tf_conviction import serial_walk

SEED = 20260730
N_PERM = 5000
BASE_D = 200.0
NQ_PT = 20.0
CUT = 585


def stack(P, thr):
    b = lon_book(P[P.mins < CUT], floor=9.5, lifetime=math.inf,
                 cap=999).reset_index(drop=True)
    conv = ((b.W == 1) & (b.FAR == 1)).astype(int)
    for f, t in thr.items():
        conv = conv + (b[f] > t).astype(int)
    return serial_walk(b[conv > 0].assign(conv=conv[conv > 0])).reset_index(drop=True)


def price(b, w, rng):
    stop = (b.risk / NQ_PT).values
    d = b.dollars.values.astype(float)
    eras = b.era.values
    i25, i26 = np.where(eras == "2025")[0], np.where(eras == "2026")[0]
    micros = np.minimum(40, np.round(w * BASE_D / (stop * 2.0)).astype(int))
    pl = micros * d / 10.0
    order = np.lexsort((b.fill_ts.values, b.day.values))
    ze = np.empty(N_PERM)
    dp = d.copy()
    for k in range(N_PERM):
        dp[i25] = d[i25][rng.permutation(len(i25))]
        dp[i26] = d[i26][rng.permutation(len(i26))]
        ze[k] = (micros * dp / 10.0).sum()
    return {"net": pl.sum(), "n25": pl[i25].sum(), "n26": pl[i26].sum(),
            "dd": maxdd(pd.Series(pl[order])), "ze": ze.mean(),
            "risk": (micros * stop * 2).mean()}


def main() -> None:
    rng = np.random.default_rng(SEED + 10)
    P = load_pop("fit")
    P["mins"] = lonmins(P.fill)
    P["exit_ts"] = pd.to_datetime(P["exit"], format="mixed", utc=True)
    b0 = lon_book(P[P.mins < 570], floor=9.5, lifetime=math.inf,
                  cap=999).reset_index(drop=True)
    thr = {f: float(np.nanmedian(b0[f].astype(float)))
           for f in ("dep_thick", "dep_resist", "trigdens_30")}

    L = ["# London ladder at 09:45 — Brake spec (A+ Mon/Fri 1.5x, neither 0.5x), "
         "$200 base\n",
         "\n**FIT ONLY. Calendar tier today-mined/unproven; sizing flat live (ANGUS "
         "ruling). Referee columns: per-era, zero-edge, real gain.**\n",
         "\n| book / ladder | net | 2025 | 2026 | maxDD | net/DD | avg $risk | "
         "zero-edge | real gain |\n|---|---|---|---|---|---|---|---|---|\n"]
    for mgmt, path in (("V8", None),
                       ("V1", "output/l2_outcomes_london_fit_v1.parquet")):
        b = stack(P if path is None else swap_outcomes(P, path), thr)
        aplus = ((b.pattern == "B2") & (b.W == 1) & (b.FAR == 1)).values
        neither = ((b.pattern != "B2") & ~((b.W == 1) & (b.FAR == 1))).values
        goodday = pd.to_datetime(b.day).dt.day_name().str[:3].isin(["Mon", "Fri"]).values
        flat = price(b, np.ones(len(b)), rng)
        spec = price(b, np.where(aplus & goodday, 1.5,
                                 np.where(neither, 0.5, 1.0)), rng)
        for name, r in ((f"{mgmt} flat $200", flat), (f"{mgmt} Brake spec", spec)):
            gain = (r["net"] - flat["net"]) - (r["ze"] - flat["ze"])
            L.append(f"| {name} | ${r['net']:+,.0f} | ${r['n25']:+,.0f} | "
                     f"${r['n26']:+,.0f} | ${r['dd']:,.0f} | "
                     f"{r['net'] / max(r['dd'], 1):.1f} | ${r['risk']:,.0f} | "
                     f"${r['ze']:+,.0f} | ${gain:+,.0f} |\n")
    L.append("\n(A+ = B2 & both-wall; neither = no B2, no both-wall; Mon/Fri tier "
             "applies to A+ only, per the spec as given.)\n")
    write("LONDON-LADDER-945.md", "".join(L))


if __name__ == "__main__":
    main()
