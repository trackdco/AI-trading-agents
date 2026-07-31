#!/usr/bin/env python3
"""Sealed-span MARKET-CONDITION measurement — runbook §4.3. INPUTS ONLY, NO OUTCOMES.

Authorized by Angus (verbal, relayed by Brake, 2026-07-31; recorded in
docs/SEALED-RUN-RUNBOOK.md §0.1) to run on the sealed span BEFORE outcomes are opened,
so that the regime characterisation is on record before anyone sees P&L and cannot
become a post-hoc excuse.

THE FOUR PRE-REGISTERED QUANTITIES (declared in the runbook before any sealed data was
read):
  1. median London session range (`on_range`), points
  2. median stop/range fraction
  3. floor-passing candidates per session day
  4. wall-check pass rate, and W / FAR separately

NONE OF THESE IS AN OUTCOME. No P&L, no R, no win rate, no exit reason, no book trade
count, no score. They are properties of the market and of the detector's inputs.

ENFORCED, NOT PROMISED: `FORBIDDEN` below lists every outcome-bearing column in the L3
frame. The script drops them immediately on load and asserts they are gone, so an
outcome figure cannot be computed here even by mistake — a later edit that tried would
raise instead of printing a number.

    python -m scripts.sealed_era_inputs --span fit        # rehearsal
    python -m scripts.sealed_era_inputs --span holdout    # the authorized measurement
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.canon.scorer import london_checks  # noqa: E402

# every outcome-bearing column in the L3 frame — dropped on load, never available
FORBIDDEN = ["R", "dollars", "dollars_1lot", "pts", "exit_reason", "exit_price",
             "exit", "exit_ts", "size_engine", "target", "target_level",
             "working_target", "pnl", "status"]

FEATURES = {"fit": "output/l3_features_london_fit.parquet",
            "holdout": "output/l3_features_london_holdout.parquet"}
YEARS = {"fit": {2025, 2026}, "holdout": {2023, 2024}}

# fit-side baselines, measured 2026-07-31 and committed in the runbook BEFORE the
# sealed measurement — the thresholds below are compared against these, not re-derived
FIT_BASELINE = {"range": 179.0, "stop_frac": 7.38, "density": 3.76, "wall": 24.1}


def load_inputs_only(span: str) -> pd.DataFrame:
    p = ROOT / FEATURES[span]
    if not p.exists():
        raise SystemExit(f"MISSING ARTIFACT: {p} — build L0-L3 for span '{span}' first")
    F = pd.read_parquet(p)
    yrs = set(pd.to_datetime(F.day).dt.year)
    if yrs - YEARS[span]:
        raise SystemExit(f"SPAN VIOLATION: years {sorted(yrs)} in {p.name}, expected "
                         f"subset of {sorted(YEARS[span])}")
    dropped = [c for c in FORBIDDEN if c in F.columns]
    F = F.drop(columns=dropped)
    leaked = [c for c in FORBIDDEN if c in F.columns]
    assert not leaked, f"OUTCOME COLUMN LEAKED: {leaked}"
    print(f"[{span}] loaded {len(F)} candidate rows; dropped {len(dropped)} "
          f"outcome-bearing columns: {dropped}")
    return F


def measure(span: str) -> dict:
    F = load_inputs_only(span)
    F = pd.concat([F, F.apply(london_checks, axis=1, result_type="expand")], axis=1)
    F["wall"] = ((F.W == 1) | (F.FAR == 1)).astype(float)

    n_days = F.day.nunique()
    Q = F[F.risk >= 9.5]                       # floor-passing candidates
    stop_pts = Q.risk.astype(float)            # population `risk` is POINTS
    m = {
        "span": span,
        "candidate_rows": len(F),
        "session_days": n_days,
        "range_median": float(Q.on_range.median()),
        "range_p25": float(Q.on_range.quantile(0.25)),
        "range_p75": float(Q.on_range.quantile(0.75)),
        "stop_median": float(stop_pts.median()),
        "stop_frac_median": float((stop_pts / Q.on_range).median() * 100),
        "density": len(Q) / n_days,
        "wall_pct": float(Q.wall.mean() * 100),
        "W_pct": float(Q.W.mean() * 100),
        "FAR_pct": float(Q.FAR.mean() * 100),
    }
    return m


def verdict(m: dict) -> list[str]:
    """Apply the runbook §4.4 decision rule — thresholds fixed before this ran."""
    b = FIT_BASELINE
    L = []
    rng_dev = (m["range_median"] - b["range"]) / b["range"] * 100
    frac_dev = (m["stop_frac_median"] - b["stop_frac"]) / b["stop_frac"] * 100
    den_dev = (m["density"] - b["density"]) / b["density"] * 100
    wall_dev = m["wall_pct"] - b["wall"]

    L.append(f"session range   {m['range_median']:>7.0f} pt   vs fit {b['range']:.0f}      "
             f"{rng_dev:+.1f}%   {'WITHIN ±25%' if abs(rng_dev) <= 25 else 'OUTSIDE ±25%'}")
    L.append(f"stop/range      {m['stop_frac_median']:>7.2f} %    vs fit {b['stop_frac']:.2f}     "
             f"{frac_dev:+.1f}%   {'WITHIN ±25%' if abs(frac_dev) <= 25 else 'OUTSIDE ±25%'}")
    L.append(f"cand density    {m['density']:>7.2f} /day vs fit {b['density']:.2f}     "
             f"{den_dev:+.1f}%   {'WITHIN ±33%' if abs(den_dev) <= 33 else 'OUTSIDE ±33%'}")
    L.append(f"wall pass rate  {m['wall_pct']:>7.1f} %    vs fit {b['wall']:.1f}     "
             f"{wall_dev:+.1f}pp {'WITHIN ±10pp' if abs(wall_dev) <= 10 else 'OUTSIDE ±10pp'}")

    inputs_comparable = abs(rng_dev) <= 25 and abs(frac_dev) <= 25 and abs(den_dev) <= 33
    L.append("")
    if abs(wall_dev) > 10:
        L.append("BRANCH (C): FEATURE-ASSEMBLY FAULT SUSPECTED — wall pass rate moved "
                 ">10pp. Per the runbook, investigate the pipeline BEFORE interpreting "
                 "any P&L; the report below it is uninterpretable until settled.")
    if inputs_comparable:
        L.append("BRANCH (A): inputs COMPARABLE to fit. A weak result must be read as "
                 "EDGE DECAY. The regime explanation is REJECTED in advance.")
    else:
        L.append("BRANCH (B): inputs MATERIALLY DIFFERENT. A weak result is admissible "
                 "as 'untested in this regime' — never as 'validated'. Promotion stays "
                 "blocked either way.")
    return L


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--span", required=True, choices=["fit", "holdout"])
    a = ap.parse_args()
    m = measure(a.span)

    print(f"\n=== MARKET-CONDITION INPUTS [{a.span}] — NO OUTCOMES ===")
    print(f"  candidate rows           {m['candidate_rows']}")
    print(f"  session days             {m['session_days']}")
    print(f"  session range (median)   {m['range_median']:.0f} pt   "
          f"(p25 {m['range_p25']:.0f} / p75 {m['range_p75']:.0f})")
    print(f"  stop size (median)       {m['stop_median']:.2f} pt")
    print(f"  stop/range (median)      {m['stop_frac_median']:.2f} %")
    print(f"  floor-passing density    {m['density']:.2f} /day")
    print(f"  wall pass rate           {m['wall_pct']:.1f} %  "
          f"(W {m['W_pct']:.1f} / FAR {m['FAR_pct']:.1f})")

    if a.span == "holdout":
        print("\n=== RUNBOOK §4.4 DECISION RULE (thresholds fixed before this ran) ===")
        for line in verdict(m):
            print("  " + line)


if __name__ == "__main__":
    main()
