#!/usr/bin/env python3
"""Backfill the trial ledger from every signed-off London verdict.

Every row below is TRANSCRIBED from a committed verdict document, cited in the `prereg`
field. Nothing is recomputed from price data, so this introduces no new trial and cannot
change any result — it moves what was already declared in prose onto disk where the
deflation can read it.

Where a verdict published a one-sided p, t is recovered exactly under the z-approximation
those verdicts used. Where a verdict published mean and se, t = mean/se directly. Where a
verdict published only rho and n, t = rho*sqrt(n-2)/sqrt(1-rho^2).

Cells the verdicts did not publish enough to standardise (the asia-sweep group means, which
carry no p or se) are recorded with effect = NaN so the trial COUNT stays honest while the
variance is computed only over cells that can be standardised. Undercounting trials would
flatter every future result.

    python -m scripts.backfill_trial_ledger
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validation.trial_ledger import (
    LEDGER, effect_from_t, record, summary, t_from_one_sided_p,
)


def from_p(fam, trial, era, prereg, est, n, p1, verdict):
    t = t_from_one_sided_p(p1)
    return dict(programme="LONDON", researcher="brake", cluster=fam, family=fam, trial=trial, era=era, prereg=prereg, stat_type="mean",
                estimate=est, n=n, t_stat=t, effect=effect_from_t(t, n), verdict=verdict)


def from_se(fam, trial, era, prereg, est, se, n, verdict):
    t = est / se
    return dict(programme="LONDON", researcher="brake", cluster=fam, family=fam, trial=trial, era=era, prereg=prereg, stat_type="mean",
                estimate=est, n=n, t_stat=t, effect=effect_from_t(t, n), verdict=verdict)


def from_rho(fam, trial, era, prereg, rho, n, verdict):
    t = rho * math.sqrt(max(n - 2, 1)) / math.sqrt(max(1 - rho * rho, 1e-12))
    return dict(programme="LONDON", researcher="brake", cluster=fam, family=fam, trial=trial, era=era, prereg=prereg, stat_type="rho",
                estimate=rho, n=n, t_stat=t, effect=effect_from_t(t, n), verdict=verdict)


def unquantified(fam, trial, era, prereg, est, n, verdict, note):
    return dict(programme="LONDON", researcher="brake", cluster=fam, family=fam, trial=trial, era=era, prereg=prereg, stat_type="mean",
                estimate=est, n=n, t_stat=float("nan"), effect=float("nan"),
                verdict=f"{verdict} ({note})")


ROWS = []

# ---- LDN-TRAP-01 — VERDICT-LDN-TRAP-01.md
P = "PREREG-london-level-trap-fade.md"
ROWS += [from_p("LDN-TRAP-01", "primary", "2025", P, -2.30, 161, 0.721, "FAIL"),
         from_p("LDN-TRAP-01", "primary", "2026", P, -2.64, 89, 0.621, "FAIL"),
         from_p("LDN-TRAP-01", "secondary:first-revisit", "2025", P, -4.72, 102, 0.80, "FAIL"),
         from_p("LDN-TRAP-01", "secondary:first-revisit", "2026", P, -2.36, 61, 0.62, "FAIL")]

# ---- LDN-VWAP-01 — VERDICT-LDN-VWAP-01.md
P = "PREREG-london-vwap-sigma-rotation.md"
ROWS += [from_p("LDN-VWAP-01", "primary", "2025", P, -3.81, 77, 0.694, "INCONCLUSIVE"),
         from_p("LDN-VWAP-01", "primary", "2026", P, -12.15, 38, 0.823, "INCONCLUSIVE"),
         from_p("LDN-VWAP-01", "secondary:gate", "2025", P, -3.09, 110, 0.70, "no effect"),
         from_p("LDN-VWAP-01", "secondary:gate", "2026", P, -11.92, 58, 0.80, "no effect")]

# ---- LDN-VT-01 — VERDICT-LDN-VT-01.md (mean + se published)
P = "PREREG-london-value-traverse.md"
ROWS += [from_se("LDN-VT-01", "primary", "2025", P, +4.74, 4.05, 53, "INCONCLUSIVE"),
         from_se("LDN-VT-01", "primary", "2026", P, -6.62, 14.95, 23, "INCONCLUSIVE"),
         from_se("LDN-VT-01", "secondary:placebo-diff", "2025", P, -0.019, 0.078, 53, "no effect"),
         from_se("LDN-VT-01", "secondary:placebo-diff", "2026", P, +0.087, 0.153, 23, "no effect")]

# ---- LDN-FLOW-01 — VERDICT-LDN-FLOW-01.md (rho published)
P = "PREREG-london-flow-confirmation.md"
for trial, r25, r26, v in (("CONFIRM", -0.006, -0.121, "INCONCLUSIVE"),
                           ("ABSORB", +0.085, -0.028, "INCONCLUSIVE"),
                           ("EFFORT", +0.010, +0.062, "FAIL"),
                           ("TRAPPED", -0.023, +0.068, "FAIL")):
    ROWS += [from_rho("LDN-FLOW-01", trial, "2025", P, r25, 141, v),
             from_rho("LDN-FLOW-01", trial, "2026", P, r26, 106, v)]

# ---- LDN-DEF-01 — VERDICT-LDN-DEF-01.md (rho published)
P = "PREREG-london-level-defense-flow.md"
for trial, r25, r26 in (("ABSORB", +0.040, -0.144), ("PIN", +0.063, -0.012),
                        ("ICEBERG", +0.037, -0.116)):
    ROWS += [from_rho("LDN-DEF-01", trial, "2025", P, r25, 99, "FAIL"),
             from_rho("LDN-DEF-01", trial, "2026", P, r26, 89, "FAIL")]

# ---- LDN-INV-01 — VERDICT-LDN-INV-01.md. D is a regression coefficient in a different
# unit; the verdict publishes a CI for 2026 only. Counted, not standardised.
P = "PREREG-london-inventory-fade-continuous.md"
ROWS += [unquantified("LDN-INV-01", "D:hinged-slope", "2025", P, 1082, 257,
                      "FAIL", "coefficient unit, not standardisable"),
         unquantified("LDN-INV-01", "D:hinged-slope", "2026", P, -402, 139,
                      "FAIL", "coefficient unit, not standardisable"),
         unquantified("LDN-INV-01", "quintile-census", "2025", P, float("nan"), 257,
                      "FAIL", "superseded by trial 2"),
         unquantified("LDN-INV-01", "quintile-census", "2026", P, float("nan"), 139,
                      "FAIL", "superseded by trial 2")]

# ---- LDN-SWP-01 — VERDICT-LDN-SWP-01.md. Corrected London-only group means; the verdict
# publishes no p or se for these cells, so they are counted but not standardised.
P = "PREREG-london-asia-sweep-pair.md"
ROWS += [unquantified("LDN-SWP-01", "D:dead-hour", "2025", P, +3.43, 134, "FAIL", "no p published"),
         unquantified("LDN-SWP-01", "D:dead-hour", "2026", P, +1.16, 66, "FAIL", "no p published"),
         unquantified("LDN-SWP-01", "P:causal", "2025", P, +2.84, 71, "FAIL", "no p published"),
         unquantified("LDN-SWP-01", "P:causal", "2026", P, +1.57, 43, "FAIL", "no p published")]


def main() -> None:
    if LEDGER.exists():
        print(f"REFUSING: {LEDGER} already exists. The ledger is append-only; a backfill "
              "must not run twice or trials would be double-counted. Delete it "
              "deliberately if you intend to rebuild from scratch.")
        return
    d = record(ROWS)
    print(f"backfilled {len(d)} trials from signed-off verdicts -> {LEDGER}\n")
    print(d.groupby("family").agg(trials=("trial", "size"),
                                  standardised=("effect", "count")).to_string())
    print("\n" + summary())
    std = int(d.effect.notna().sum())
    print(f"\nNOTE: the London verdicts declared a running total of 34 trials and the "
          f"ledger holds {len(d)} — the narrative count was right. Trial counting is now "
          "mechanical rather than prose, and this is the number future deflations use.")
    print(f"CAVEAT: only {std} of {len(d)} trials could be standardised onto the common "
          "effect scale. LDN-INV-01 reports a regression coefficient in its own units and "
          "LDN-SWP-01 published group means without p or se, so both are COUNTED but "
          "excluded from the variance. If those 8 are more dispersed than the 26 that "
          "remain, the true bar is higher than the one computed here.")


if __name__ == "__main__":
    main()
