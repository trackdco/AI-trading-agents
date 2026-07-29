# London overnight audit — Stage 3: selection-null calibration

**Fit only. Sealed 2023/24 never loaded.**

## What this stage answers

Stages 1 and 2 search thousands of rules and report the best. That process returns a winner even on pure noise, and a per-cell permutation null does not price it — it asks *is this cell real given these rows*, not *how much did searching inflate it*.

So: **500 randomized day-level splits**. In each, the ENTIRE selection procedure runs in-sample (pick the best-performing rule by mean R among all singles and pairs with n>=25), then that rule — chosen blind — is measured out-of-sample. The gap between the two is the shrinkage a rule picked this way should expect.

Splits are **by day**, never by row: same-day trades share regime and tape, so a row-level split would leak and understate shrinkage.

## Result — shrinkage as a function of how hard you searched

| selection breadth | splits | IS median | OOS median | shrinkage | OOS/IS |
|---|---|---|---|---|---|
| exhaustive (all singles+pairs) | 500 | +1.378 | +0.260 | +1.138 | 0.19 |
| 4-check (the actual L3 breadth) | 500 | +0.587 | +0.600 | -0.014 | 1.02 |
| wall arm fixed (no selection) | 500 | +0.478 | +0.488 | -0.010 | 1.02 |

The exhaustive row is the **upper bound** on selection cost, not the wall arm's. Searching 29k combinations manufactures +1.378 mean R in-sample out of this population and keeps only +0.260 of it — 81% evaporates. That is what unconstrained search does here, and it is the number to remember whenever a mined rule is proposed.

## Where the wall arm actually sits

The wall arm scores **+0.483 mean R** on the full fit population — far BELOW the +1.378 that exhaustive search achieves in-sample. That gap is itself evidence: if the wall arm were a search artifact it would look like one, and it does not. It was chosen from four pre-existing checks at frozen thresholds, and the matching 4-check null shows a median shrinkage of **-0.014 R**, not the exhaustive +1.138.

Held fixed with no selection at all, the wall arm's own split-half behaviour is IS +0.478 -> OOS +0.488 (shrinkage -0.010), which is pure sampling noise rather than selection bias.

**Honest forward expectation: about +0.483 mean R** — the fit figure less the shrinkage measured at the wall arm's OWN selection breadth. Not -0.654, which would wrongly charge it the cost of a 29,161-combination search it never ran.

**What this does NOT establish.** The 4-check null still assumes the four checks were specified independently of this data — they were not; they were fitted on 2025 by the original canon. The sealed 2023/24 holdout remains the only test that owes nothing to any choice made here.
