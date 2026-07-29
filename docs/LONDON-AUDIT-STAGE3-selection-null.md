# London overnight audit — Stage 3: selection-null calibration

**Fit only. Sealed 2023/24 never loaded.**

## What this stage answers

Stages 1 and 2 search thousands of rules and report the best. That process returns a winner even on pure noise, and a per-cell permutation null does not price it — it asks *is this cell real given these rows*, not *how much did searching inflate it*.

So: **500 randomized day-level splits**. In each, the ENTIRE selection procedure runs in-sample (pick the best-performing rule by mean R among all singles and pairs with n>=25), then that rule — chosen blind — is measured out-of-sample. The gap between the two is the shrinkage a rule picked this way should expect.

Splits are **by day**, never by row: same-day trades share regime and tape, so a row-level split would leak and understate shrinkage.

## Result — 500 valid splits

| | median | mean | p10 | p90 |
|---|---|---|---|---|
| best in-sample mean R | +1.378 | +1.401 | +1.127 | +1.704 |
| same rule out-of-sample | +0.260 | +0.288 | -0.200 | +0.799 |
| shrinkage (IS - OOS) | +1.138 | +1.113 | +0.421 | +1.775 |

**Median IS->OOS shrinkage: +1.138 R** (83% of the in-sample figure evaporates out-of-sample for a rule chosen this way).

## Where the wall arm actually sits

The shipped rule (W or FAR) scores **+0.483 mean R** on the full fit population. Against the distribution of *out-of-sample* results from rules selected by search, it sits at the **69th percentile**.

**Read: partly real, materially inflated.** The wall arm beats the typical searched rule but sits inside the range search can reach. Expect the holdout to come in meaningfully below the fit figure — roughly the shrinkage above.

**Practical consequence:** subtract roughly 1.14 R from any fit-span expectation before believing it live. Applied to the wall arm's fit mean R of +0.483, the honest forward expectation is about -0.654 R.
