#!/usr/bin/env python3
"""L3 Stage B — put every London check on trial at its FROZEN threshold.

The old London canon asserts four Layer-1 checks (2025-frozen): W (no wall behind entry), FAR
(wall ahead farther than LON_FAR_MIN), ROOM (room_ahead_R inside a band), ASIA (Asia-session
CVD not deeply opposed). None was ever trialed on an honest population — they were fitted and
shipped. After watching half of NY's checks die under exactly this scrutiny, nothing London
ships untested.

THRESHOLDS ARE IMPORTED, NEVER RE-DERIVED. `london_checks` and its constants come straight
from src/canon/scorer.py. Re-deriving a threshold on the rebuild's population would be fitting
twice and calling it validation.

THE POPULATION IS risk >= LON_RISK_MIN. L2 established that sub-9.5pt loses in every era
(meanR -0.278 fit / -0.291 holdout) whatever else is true, so measuring check lift over the
full census would mostly measure the risk gate again. Every table below is the population the
book would actually trade. The unconditional view is printed once for contrast.

A CHECK SURVIVES ONLY IF IT POINTS THE SAME WAY IN 2025, 2026 AND HOLDOUT (handoff §3).
Discover on 2025, validate on 2026, confirm on the sealed days. One era is an anecdote; two
agreeing eras and a third disagreeing is a coin flip with extra steps.

PERMUTATION NULL (handoff burn list #9). Every lift is compared against the distribution of
lifts produced by shuffling outcomes within era and re-measuring. A check whose real lift sits
inside the noise band is not a check, however plausible its story. Reported as the fraction of
shuffles beating the observed lift — treat >0.05 as failure to clear noise.

NOT DONE HERE, and deliberately: combination probes and adversarial verification. The handoff
routes those through sonnet agents; single-check trial plus the null is the deterministic core
and stands on its own.

    python -m scripts.l3_check_trial_london
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.canon.scorer import (  # noqa: E402
    LON_ASIA_MIN, LON_FAR_MIN, LON_RISK_MIN, LON_ROOM_HI, LON_ROOM_LO, london_checks,
)

CHECKS = ["W", "FAR", "ROOM", "ASIA"]
N_PERM = 2000
RNG = np.random.default_rng(20260729)      # fixed: the null must be reproducible


def load(span: str) -> pd.DataFrame:
    p = ROOT / f"output/l3_features_london_{span}.parquet"
    if not p.exists():
        raise SystemExit(f"{p.relative_to(ROOT)} missing — build L3 features first")
    F = pd.read_parquet(p)
    got = F.apply(lambda r: london_checks(r), axis=1, result_type="expand")
    F = pd.concat([F, got], axis=1)
    F["era"] = "holdout" if span == "holdout" else pd.to_datetime(F.day).dt.year.astype(str)
    F["score"] = F[CHECKS].sum(axis=1)
    return F


def lift(g: pd.DataFrame, check: str) -> tuple:
    a, b = g[g[check] == 1], g[g[check] == 0]
    if not len(a) or not len(b):
        return None
    return (len(a), a.R.mean(), (a.dollars > 0).mean() * 100,
            len(b), b.R.mean(), (b.dollars > 0).mean() * 100,
            a.R.mean() - b.R.mean())


def perm_p(g: pd.DataFrame, check: str, observed: float) -> float:
    """Fraction of outcome-shuffles whose |lift| meets or beats the observed |lift|."""
    mask = (g[check] == 1).to_numpy()
    r = g.R.to_numpy().copy()
    if mask.all() or not mask.any():
        return float("nan")
    hits = 0
    for _ in range(N_PERM):
        RNG.shuffle(r)
        if abs(r[mask].mean() - r[~mask].mean()) >= abs(observed):
            hits += 1
    return hits / N_PERM


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all-risk", action="store_true",
                    help="also print the unconditional (no risk gate) view")
    ap.add_argument("--include-holdout", action="store_true",
                    help="BURNS THE REFERENDUM. The sealed 2023/24 days run ONCE, frozen, at "
                         "the very end (handoff §3). Discovery is 2025, validation is 2026. "
                         "Pass this only for that single final run, never while iterating.")
    a = ap.parse_args()

    spans = ["fit"] + (["holdout"] if a.include_holdout else [])
    if a.include_holdout:
        print("!! --include-holdout: sealed 2023/24 days are in this run. If any rule changes "
              "after seeing it, the holdout is spent and Angus must be told.\n")
    frames = []
    for span in spans:
        try:
            frames.append(load(span))
        except SystemExit as e:
            print(f"note: {e}")
    F = pd.concat(frames, ignore_index=True)
    print(f"L3 features: {len(F)} rows | eras {sorted(F.era.unique())}")
    print(f"frozen thresholds — RISK_MIN {LON_RISK_MIN} | FAR_MIN {LON_FAR_MIN} | "
          f"ROOM ({LON_ROOM_LO}, {LON_ROOM_HI}] | ASIA_MIN {LON_ASIA_MIN}")

    P = F[F.risk >= LON_RISK_MIN].copy()
    print(f"\ntradeable population (risk >= {LON_RISK_MIN}): {len(P)} of {len(F)} "
          f"({len(P) / len(F) * 100:.0f}%)")
    for e in sorted(P.era.unique()):
        d = P[P.era == e]
        print(f"  {e:>8}: n={len(d):>4} WR {(d.dollars > 0).mean() * 100:>3.0f}% "
              f"meanR {d.R.mean():>+7.3f}  1-lot ${d.dollars.sum():>+10,.0f}")

    eras = sorted(P.era.unique())
    print(f"\n{'=' * 92}\nSINGLE-CHECK TRIAL — frozen thresholds, per era\n{'=' * 92}")
    verdicts = {}
    for c in CHECKS:
        print(f"\n{c}")
        print(f"  {'era':>8} {'n pass':>7} {'meanR':>8} {'WR':>5} | {'n fail':>7} "
              f"{'meanR':>8} {'WR':>5} | {'lift':>8} {'perm p':>7}")
        signs = []
        for e in eras:
            g = P[P.era == e]
            L = lift(g, c)
            if L is None:
                print(f"  {e:>8}   (degenerate — all rows on one side)")
                signs.append(0)
                continue
            na, ra, wa, nb, rb, wb, lf = L
            p = perm_p(g, c, lf)
            signs.append(int(np.sign(lf)))
            print(f"  {e:>8} {na:>7} {ra:>+8.3f} {wa:>4.0f}% | {nb:>7} {rb:>+8.3f} "
                  f"{wb:>4.0f}% | {lf:>+8.3f} {p:>7.3f}")
        consistent = len(set(signs)) == 1 and signs[0] != 0
        verdicts[c] = consistent
        print(f"  -> {'CONSISTENT' if consistent else 'INCONSISTENT'} across "
              f"{', '.join(eras)} (signs {signs})")

    print(f"\n{'=' * 92}\nSCORE LADDER — does stacking checks stack edge?\n{'=' * 92}")
    print(f"  {'score':>5} " + " ".join(f"{e:>22}" for e in eras))
    for s in range(5):
        cells = []
        for e in eras:
            d = P[(P.era == e) & (P.score == s)]
            cells.append(f"n={len(d):>4} R{d.R.mean():>+6.3f}" if len(d)
                         else f"{'—':>22}")
        print(f"  {s:>5} " + " ".join(f"{c:>22}" for c in cells))

    print(f"\n{'=' * 92}\nVERDICT\n{'=' * 92}")
    for c in CHECKS:
        print(f"  {c:>5}: {'SURVIVES — same direction in every era' if verdicts[c] else 'FAILS ERA CONSISTENCY — do not ship on this evidence'}")
    print("\nPermutation p > 0.05 means the lift is inside the noise band even where the sign "
          "is consistent; read both columns together, not either alone.")

    if a.all_risk:
        print(f"\n{'=' * 92}\nUNCONDITIONAL (no risk gate) — for contrast only\n{'=' * 92}")
        for c in CHECKS:
            for e in eras:
                L = lift(F[F.era == e], c)
                if L:
                    print(f"  {c:>5} {e:>8}: lift {L[6]:+.3f} "
                          f"(pass n={L[0]} R{L[1]:+.3f} | fail n={L[3]} R{L[4]:+.3f})")


if __name__ == "__main__":
    main()
