# SPEC — the EC entry matrix: decide at the candle (2026-08-06)

**Status: DRAFT UNDER TEST — fit span only, holdout sealed.**
ANGUS directive, mirroring the London-side matrix. This spec exists so both desks
test the *same* conventions. It follows directly from the depth-lookahead finding
(`docs/FINDING-depth-lookahead.md`) and the displacement pilot
(`scripts/audit_displacement_entry.py`).

---

## 1. The matrix

| kind | E3 — the old way | EC — the new default |
|---|---|---|
| **displacement** (close-through) | limit on the retest | **market on the close** |
| **rejection block** (wick + close back) | limit on the retest | limit on the retest (execution unchanged) |

## 2. The law: one decision point

**Every entry check — depth, flow, geometry, structure — is evaluated at the close
of the TRIGGERING candle (boundary T). Never at the fill.** The fill is execution
only. A rejection-block limit that fills later is not re-scored, live or in test.

Why this is law and not preference:

1. **Causal cleanliness by construction.** The signal bar is complete at T; every
   feature computed from ≤T information — including the signal bar itself — is
   knowable at the decision. Nothing from the entry bar or after T, ever.
2. **Minute-resolution fills cannot be validated honestly at fill time.** A fill
   anywhere inside minute M scored on end-of-M state is the 2026-08-05 lookahead
   bug. There is no honest fill-time depth backtest at our data resolution.
3. **Fill-time conditioning is adversarially selected.** Limits fill preferentially
   when price is trading through the level — the fill mechanism enriches losers.
   A feature measured at fill is a mixture of signal and selection; measured at T
   it is just signal, on a population the entry mechanism didn't filter.
4. **Comparability.** Same features, same moment, different execution: the two
   legs' lift tables live in one coordinate system, so the per-kind matrix choice
   is decided by evidence.

**The live caveat, stated once:** at a later fill, fresher information genuinely
exists and the live path could legally read it. It must not. We only ship policies
the backtest can honestly measure; a fill-time policy is not one of them.

## 3. Depth convention

The depth archive stores, for each minute M, the **last** book state in M. The row
labeled **minute T−1** is therefore the book at the close boundary T — that row,
never the row labeled T, is the decision snapshot for **both** legs.
(`dep[ts <= T]` reads the entry bar's end — the shipped bug, in this convention.)

## 4. Execution conventions per leg

**Displacement leg (market on close):**
- Entry: open of the first 1m bar at/after T (nothing intrabar is used).
- Stop: signal-bar adverse extreme −/+ 1 tick.
- Cost model: report 0 / 1 / 2-tick adverse sensitivity + $5/RT commission at
  $20/pt; small-risk (<4pt) subpopulation broken out — costs bite there.
- Risk guard: risk ≥ 2pt; dedupe one row per (day, T, direction).

**Rejection-block leg (limit on retest):**
- Limit at the retest level (entry_ref), placed at T with features frozen.
- Fill walk: the existing L1 walk, unchanged. Never-filled = no trade — and under
  EC that is acceptable by definition: a rejection block *closed back*, so there is
  no close-through to market into.
- Stop: the existing L2 convention for the kind.

**Sizing note:** the two legs have structurally different risk (candle-extreme
stops median ~14.75pt vs the limit model's tighter stops). The EC book sizes per
trade off each leg's own risk; R units are per-leg and never pooled raw.

## 5. Evidence plan

1. **Run 1 — in flight** (`wf_b89638d4-ea6`): displacement-entry discovery sweep on
   the full fit population, all kinds, six families (signal-bar flow, pre-signal
   flow, geometry, structure, honest depth at T−1, costs), each independently
   verified, synthesized under the era-survival rule (2025 discover / 2026 confirm).
   Its KIND split is the direct evidence for the matrix's rejection-block row:
   if rejection blocks entered at market underperform their limit outcomes, the
   matrix stands.
2. **Run 2 — planned on run 1's landing**: the rejection-block limit leg re-trialed
   with features at T (not at fill); the composite EC book (displacement leg +
   rejection-block leg) vs the E3 baseline, naive exits, era × session.
3. **Holdout:** sealed. One look, later, for a single frozen candidate — a human
   authorization, not an automated step.
