# DECLARATION — OUTCOME SCORING ON THE RACE CENSUS

2026-08-08, written and committed BEFORE the outcome run. First outcome
look at this family.

## POPULATION — fixed before any outcome exists

The race census at the **declared 0.10W** tolerance exactly as built
(`race_fit.parquet`, tol=0.10 rows; grammar per
`DECLARATIONS-trigger-race.md`, integrity probe PASS). No re-selection,
no tolerance change, no window change. The two grammar discrepancies
documented in the trade check (the 0.5W displacement floor that missed
T3; the MA-exclusive affirmation count and the 10:30 boundary that
missed T4) are **left exactly as declared** — outcome scoring runs on
the census as it stands, and any grammar change is a separate future
declaration by the trader.

**Calibration assertion before anything is read:** the outcome builder
re-derives the triggers; its emitted (t, mech, dir, tf_won, n_aff) set
must match the census parquet's tol-0.10 rows EXACTLY, else stop.

## SCORING

- **Entry**: next 1m open after the trigger candle's close (standing
  entry law). **Stop**: the winning TF's trigger-candle extreme ± 1
  tick. Gap-through-stop and no-next-open rows excluded and counted.
- **Targets, first-passage** (as-of previous-1m dynamic values; same-bar
  → stop wins; EOD close-out at the session segment's last bar if
  neither side resolves):
  - **M1**: the 15m MA (the honest rebalance target per BR-80).
  - **M2 / M3**: NEAR = the nearest menu structure strictly beyond the
    entry price in the trade direction, evaluated at the trigger row;
    FAR = the second such structure. Structure names recorded per row.
- **MFE-in-R** (stop-bounded) distribution for every cell.
- **Cost**: 0.5pt base; 1.0 / 1.5pt sensitivity.
- **Book**: first-of-fight X=0.5W exactly as the census clusters
  (one stream across TFs, ref = 15m MA); X-sensitivity {0.25, 1.0, 2.0}
  reported on headline cells.
- **Uncertainty**: day-clustered bootstrap, seed 20260807, 2000 draws,
  sum/count resampling; 95% intervals.

## REPORTING DISCIPLINE

Per **window × mechanism × direction**, windows NEVER pooled; dual
currency (hit% AND EV in R) always together. **Multiplicity stated up
front: ~3 windows × 3 mechanisms × 2 directions × up to 2 targets plus
sensitivity tables ≈ 100+ scored numbers, NO DECLARED BAR anywhere** —
this is a base-rate pass on a fresh population; nulls are published;
nothing below a verdict. **Law-2 flag declared in advance**: risk varies
systematically with tf_won (1m stops are structurally tighter), so any
cross-TF EV comparison is R-denominator-coupled and will be flagged, not
interpreted.

Entry-price integrity: T1 flatten probe on the outcome builder (entry
must equal the flattened value and move vs the real run somewhere)
before any outcome is read.

Standing: fit-only, no holdout exists for this family (bar-only venue
closed — forward data is the only out-of-sample), report-only, nothing
adopted.
