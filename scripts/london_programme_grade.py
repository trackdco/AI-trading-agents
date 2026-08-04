#!/usr/bin/env python3
"""Grade the whole London programme with our own DSR machine. DIAGNOSTIC, NOT A TRIAL.

Every number below is transcribed from a signed-off verdict — nothing is recomputed from
price data and no new hypothesis is tested, so this adds nothing to the ledger. It answers
one question the desk will inevitably ask:

    "did any of them work better than the others?"

Ranking nine candidates and reading off the best is EXACTLY the search DSR deflates. So
rather than eyeball a league table, the best observed result is put through the machine
with the programme's real trial count.

Per-event Sharpe is recovered from each verdict's published mean, n and one-sided p:
    t = Phi^-1(1 - p1)  ->  SR_per_event = t / sqrt(n)
which is exact for the z-approximation those verdicts used.

    python -m scripts.london_programme_grade
"""
from __future__ import annotations

import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validation.dsr import expected_max_sharpe

PHI = NormalDist()
TRIALS = 34          # London programme ledger at close-out

# (label, era, mean pts, n, one-sided p) — all transcribed from the verdicts.
RESULTS = [
    ("value-traverse (naked-POC)", "2025", +4.74, 53, 0.121),
    ("value-traverse (naked-POC)", "2026", -6.62, 23, 0.671),
    ("level-trap-fade", "2025", -2.30, 161, 0.721),
    ("level-trap-fade", "2026", -2.64, 89, 0.621),
    ("vwap-sigma-rotation", "2025", -3.81, 77, 0.694),
    ("vwap-sigma-rotation", "2026", -12.15, 38, 0.823),
]
# asia-sweep, corrected London-only window (VERDICT-LDN-SWP-01 §"measured causally").
# Reported as means only — the verdict does not publish p for these cells.
SWEEP = [("asia-sweep D (dead-hour)", "2025", +3.43, 134),
         ("asia-sweep D (dead-hour)", "2026", +1.16, 66),
         ("asia-sweep P (causal)", "2025", +2.84, 71),
         ("asia-sweep P (causal)", "2026", +1.57, 43)]


def per_event_sr(p1: float, n: int) -> float:
    return PHI.inv_cdf(1.0 - p1) / np.sqrt(n)


def main() -> None:
    print("LONDON PROGRAMME — graded by our own DSR machine")
    print("DIAGNOSTIC ONLY. Numbers transcribed from signed-off verdicts. No new trial.\n")

    rows = []
    for label, era, mean, n, p1 in RESULTS:
        sr = per_event_sr(p1, n)
        rows.append((label, era, mean, n, sr))

    print(f"{'candidate':<28}{'era':<6}{'mean pts':>10}{'n':>6}{'SR/event':>11}")
    print("-" * 63)
    for label, era, mean, n, sr in sorted(rows, key=lambda r: -r[4]):
        print(f"{label:<28}{era:<6}{mean:>+10.2f}{n:>6}{sr:>+11.4f}")
    print()
    for label, era, mean, n in SWEEP:
        print(f"{label:<28}{era:<6}{mean:>+10.2f}{n:>6}{'(no p published)':>11}")

    srs = np.array([r[4] for r in rows], float)
    best_label, best_era, best_mean, best_n, best_sr = max(rows, key=lambda r: r[4])

    # Prefer the RECORDED ledger over the six-cell estimate this script originally used.
    try:
        from src.validation.trial_ledger import load, trial_effect_variance
        led = load()
        trial_sr_var = trial_effect_variance(led)
        src_note = (f"recorded ledger — {int(led.effect.notna().sum())} standardised "
                    f"of {len(led)} trials")
    except Exception as exc:                     # ledger absent or too thin
        trial_sr_var = float(srs.var(ddof=1))
        src_note = f"FALLBACK six-cell estimate ({exc})"

    print("\n" + "=" * 63)
    print("THE MACHINE ON OUR OWN RESULTS")
    print("=" * 63)
    print(f"best observed            : {best_label} {best_era}  "
          f"SR/event {best_sr:+.4f}  (mean {best_mean:+.2f} pts, n {best_n})")
    print(f"trial-effect variance    : sd {np.sqrt(trial_sr_var):.4f} "
          f"(var {trial_sr_var:.6f})")
    print(f"  source                 : {src_note}")
    print(f"declared trials          : {TRIALS}")

    bar = expected_max_sharpe(TRIALS, trial_sr_var)
    print(f"\nexpected BEST from luck alone, {TRIALS} trials: SR/event {bar:+.4f}")
    print(f"observed best                             : SR/event {best_sr:+.4f}")
    verdict = ("BELOW the luck bar — indistinguishable from noise"
               if best_sr <= bar else "above the luck bar")
    print(f"\n  -> {verdict}")
    print(f"     shortfall: {best_sr - bar:+.4f} SR/event")

    print("\nSanity: even the raw best needed p <= 0.05 to be interesting on its own.")
    print(f"  {best_label} {best_era} came in at p1 = "
          f"{[r for r in RESULTS if r[0] == best_label and r[1] == best_era][0][4]:.3f}, "
          "and inverted in the other era.")


if __name__ == "__main__":
    main()
