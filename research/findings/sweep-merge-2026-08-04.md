---
date: 2026-08-04
status: reference
tags: [london, research-process]
sources: []
---

# Sweep merge map — 24 raw concepts → 8 candidates + spec layers

Three parallel research sweeps (order-flow/liquidity, AMT/volume-profile,
session-structure/VWAP; full records in `articles/sweep-2026-08-04-*.md`).
Independent agents converging on the same mechanism is weak evidence the mechanism
is structural (and strong evidence it is well-known — crowding noted per candidate).

| Candidate | Merged from | Convergence |
|---|---|---|
| london-asia-sweep-reversal | OF#1 + AMT#2 + SS#1 | all three sweeps |
| london-asia-sweep-continuation | OF#2 + SS#2 | two sweeps, NQ-native stats |
| london-inventory-fade | OF#8 + AMT#1 + SS#3-fade | all three; NY Fed research |
| london-euro-open-drive | OF#4 + AMT#3 + SS#6 + SS#3-go | all three |
| london-level-trap-fade | OF#3 + AMT#4 | two sweeps |
| london-level-defense-flow | OF#5 + OF#7 + OF#6 | order-flow sweep (flow-native) |
| london-vwap-sigma-rotation | SS#4 + SS#5 + SS#7 | session sweep (σ-location native) |
| london-value-traverse | AMT#5 + AMT#6 + AMT#8 | AMT sweep |

**Spec layers (not standalone candidates — conditioning applied across families):**
- Open-type gate (AMT#7): classify 03:00–03:30 ET as drive / test-drive / auction;
  fade-type candidates stand down on drive opens.
- DoW + DST gates (SS#8): day-of-week regime notes; the DST-mismatch fortnights;
  and the endogenous European-open detector (first 1-min bar in 01:45–03:15 ET with
  volume z-score above threshold) — the robust fix for the session-clock trap
  (`findings/london-session-clock.md`).
- VWAP-σ location (ANGUS standing variable): entry position vs overnight-anchored
  VWAP conditions every candidate; +2σ chases are a different trade than −1σ holds.
- Flow overlays (June 2025+ span only): CVD divergence / absorption confirmation
  as optional gates on candles-only candidates.

**Event-tree pairs (tested as families in the trial ledger, not independent
discoveries):** sweep-reversal ↔ sweep-continuation are ONE trigger split by an
acceptance test + timing; euro-open-drive ↔ vwap-sigma-rotation's fade side are
regime complements; level-trap-fade ↔ level-defense-flow are the candles vs flow
expression of one defense mechanism.

**NY-canon input-family overlap flags (same-account veto context — NY reads: depth
walls, overnight structure, order flow, VWAP, trigger density, structural
events):** level-defense-flow reads depth walls + order flow = HIGH overlap;
level-trap-fade, inventory-fade, euro-open-drive, value-traverse read overnight
structure = MEDIUM; vwap-sigma-rotation reads VWAP = MEDIUM; sweep pair reads
session structure = MEDIUM-LOW. Return correlation is measured at validation; the
structural flag stands regardless (REPORT-correlation-2026-08-04 threshold 5).
