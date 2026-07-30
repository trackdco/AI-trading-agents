#!/usr/bin/env python3
"""LONDON management tournament — V0 (set-and-forget) vs V1 (BE at +1R) vs V8 (shipped).

THE PEDIGREE: "BE-at-1R vs none = priority tournament (Angus)" — decision log
2026-07-17, config comment §8 ("Priority head-to-head: V1 vs V0"), the February hand
log already trades BE, and docs/LONDON-DOW-MFE.md measured 42% of stack losers touching
+1R before dying (bar-walk what-if +$1,194). This runs the REAL engine arms: V0 and V1
L2 walks over the identical L0 census (same fills, same entry vetoes, same slippage
model; only management differs), then the identical selection stack.

PIPELINE VALIDITY GATE: the V8 arm is rebuilt through the same outcome-join path and
must reproduce the canonical working stack EXACTLY (110 trades, +$17,941, 64% WR) —
mismatch aborts the doc. Entry-time features and the score-0 veto thresholds are
FROZEN from the V8 stack (dep medians as declared numbers) so arms differ ONLY in
management. Selection (the $400 day stop) runs on each arm's own realized dollars —
management legitimately changes which later trades exist.

Working stack throughout: cut@09:30 + score-0 veto + one-position-at-a-time, 1 NQ lot.
FIT ONLY. Sealed untouched. Adoption = ANGUS + prereg rev; this doc measures.

    python -m scripts.london_mgmt_tournament
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
from scripts.london_conviction import CUT_MIN, lonmins
from scripts.london_holdout_report import load_pop, t_test_two_sided
from scripts.london_tf_conviction import serial_walk

KEY = ["ts", "tf", "direction"]
OUTCOLS = ["dollars", "R", "exit_ts", "exit_reason"]
ARMS = {"V8 shipped (partial+trail)": None,
        "V1 BE at +1R": "output/l2_outcomes_london_fit_v1.parquet",
        "V0 set-and-forget": "output/l2_outcomes_london_fit_v0.parquet"}
CANON = dict(n=110, net=17941, wr=64)


def swap_outcomes(P8: pd.DataFrame, arm_path: str | None) -> pd.DataFrame:
    if arm_path is None:
        return P8.copy()
    A = pd.read_parquet(ROOT / arm_path)
    A = A.rename(columns={"dollars_1lot": "dollars"})
    A["exit_ts"] = pd.to_datetime(A.exit_ts, format="mixed", utc=True)
    P = P8.drop(columns=OUTCOLS).merge(
        A[KEY + OUTCOLS].drop_duplicates(KEY), on=KEY, how="left", validate="1:1")
    nan = P.dollars.isna()
    if nan.sum() > 1:
        raise SystemExit(f"JOIN FAILURE: {int(nan.sum())} rows without outcomes "
                         f"joining {arm_path}")
    if nan.any():
        # known single case: 2025-11-27 (Thanksgiving) 5min short — V0 set-and-forget
        # never resolves before the holiday session's bars end. No legitimate outcome
        # exists for that arm; dropped from THIS ARM ONLY and disclosed in the doc.
        print(f"NOTE: dropping {int(nan.sum())} unresolved candidate from {arm_path}: "
              f"{P[nan][['day', 'tf', 'direction']].to_dict('records')}")
        P = P[~nan]
    return P


def stack(P: pd.DataFrame, thr: dict) -> pd.DataFrame:
    Pc = P[P.mins < CUT_MIN]
    b = lon_book(Pc, floor=9.5, lifetime=math.inf, cap=999).reset_index(drop=True)
    b["both_wall"] = ((b.W == 1) & (b.FAR == 1)).astype(int)
    conv = b.both_wall.copy()
    for f, t in thr.items():
        conv = conv + (b[f] > t).astype(int)
    b["conv"] = conv
    return serial_walk(b[b.conv > 0]).reset_index(drop=True)


def main() -> None:
    P8 = load_pop("fit")
    P8["mins"] = lonmins(P8.fill)
    P8["exit_ts"] = pd.to_datetime(P8["exit"], format="mixed", utc=True)

    # frozen veto thresholds from the canonical V8 cut book (declared numbers)
    b8 = lon_book(P8[P8.mins < CUT_MIN], floor=9.5, lifetime=math.inf,
                  cap=999).reset_index(drop=True)
    thr = {f: float(np.nanmedian(b8[f].astype(float)))
           for f in ("dep_thick", "dep_resist", "trigdens_30")}

    books, rows = {}, []
    for name, path in ARMS.items():
        b = stack(swap_outcomes(P8, path), thr)
        books[name] = b
        t = t_test_two_sided(b.R)
        r = {"name": name, "n": len(b), "net": float(b.dollars.sum()),
             "wr": float((b.R > 0).mean()), "r": float(b.R.mean()),
             "dd": maxdd(b.sort_values(["day", "fill_ts"]).dollars.reset_index(drop=True)),
             "p": t["p"]}
        for era in ("2025", "2026"):
            g = b[b.era == era]
            r[era] = f"{len(g)}/{(g.R > 0).mean() * 100:.0f}%/{g.R.mean():+.2f}/${g.dollars.sum():+,.0f}"
        r["exits"] = b.exit_reason.value_counts().to_dict()
        rows.append(r)

    v8 = rows[0]
    ok = (v8["n"] == CANON["n"] and round(v8["net"]) == CANON["net"]
          and round(v8["wr"] * 100) == CANON["wr"])
    if not ok:
        raise SystemExit(f"PIPELINE GATE FAILED: V8 rebuild {v8['n']}/{v8['net']:.0f}/"
                         f"{v8['wr']:.2f} != canonical {CANON} — nothing else is valid")

    L = ["# London management tournament — V0 vs V1 (BE at +1R) vs V8, real engine\n",
         "\n**FIT ONLY. Same census, same fills, same slippage; only management "
         "differs. Selection runs on each arm's own realized dollars. Pipeline gate: "
         "the V8 arm reproduces the canonical stack exactly (verified this run). "
         "Working stack, 1 NQ lot.**\n",
         "\n## The head-to-head\n\n"
         "| arm | n | WR | mean R | net | maxDD | 2025 n/WR/R/$ | 2026 n/WR/R/$ |\n"
         "|---|---|---|---|---|---|---|---|\n"]
    for r in rows:
        L.append(f"| {r['name']} | {r['n']} | {r['wr'] * 100:.0f}% | {r['r']:+.3f} | "
                 f"${r['net']:+,.0f} | ${r['dd']:,.0f} | {r['2025']} | {r['2026']} |\n")
    L.append("\nExit mixes: " + " · ".join(
        f"**{r['name']}**: {r['exits']}" for r in rows) + "\n")

    # per-key deltas: V1 vs V8 on the INTERSECTION of taken trades
    k8 = books["V8 shipped (partial+trail)"].set_index(KEY)
    k1 = books["V1 BE at +1R"].set_index(KEY)
    common = k8.index.intersection(k1.index)
    c8, c1 = k8.loc[common], k1.loc[common]
    saved = ((c8.R <= 0) & (c1.R > -0.15) & (c1.R <= 0.15)).sum()
    killed = ((c8.R > 0.15) & (c1.R > -0.15) & (c1.R <= 0.15)).sum()
    d = (c1.dollars - c8.dollars)
    L.append(f"\n## Where V1's difference comes from ({len(common)} shared trades)\n\n"
             f"- Full V8 losers that V1 scratches near BE (|R| <= 0.15): **{saved}**\n"
             f"- V8 winners that V1 BEs out before the run: **{killed}**\n"
             f"- Net management delta on shared trades: ${d.sum():+,.0f} "
             f"(biggest single save ${d.max():+,.0f}, biggest single cost "
             f"${d.min():+,.0f})\n"
             f"- Trades only in one stack (selection drift via day-stop paths): "
             f"{len(k8) - len(common)} V8-only, {len(k1) - len(common)} V1-only\n")

    L.append("\n## Read it\n\n"
             "- V1-vs-V0 is the DECLARED head-to-head (Angus, 2026-07-17). V8 is the "
             "shipped control; it was chosen in the NY-era tournaments, not against "
             "V1 on London.\n"
             "- Adoption of any arm change = ANGUS ruling + prereg rev + runner "
             "re-rehearsal. If V1 wins here it becomes the declared management "
             "CANDIDATE, judged on the holdout/forward like everything else.\n"
             "- The bar-walk predicted +$1,194 for BE@1R over the shipped book; the "
             "engine number above is the real one (management interacts with "
             "partials, slippage and day-stop paths a bar-walk cannot see).\n"
             "- One disclosed asymmetry: the 2025-11-27 Thanksgiving 5min short has "
             "no V0 outcome (set-and-forget never resolves before the holiday "
             "session ends) and is dropped from the V0 arm only. V8 booked +$70 on "
             "it, V1 -$10 — a one-trade, ~$70 edge to V8 in the table above.\n")
    write("LONDON-MGMT-TOURNAMENT.md", "".join(L))


if __name__ == "__main__":
    main()
