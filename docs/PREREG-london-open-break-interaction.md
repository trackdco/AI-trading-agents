# PRE-REGISTRATION ADDENDUM — LDN-PO3-01 — declared interaction follow-up

**Committed BEFORE the interaction run.** The conditioning prereg
(`docs/PREREG-london-open-break-conditioning.md`) stated: *"If any single variable
survives both eras, its interaction with the others becomes a declared follow-up."*
Three did, all on the fade branch:

| variable | predicted better | result |
|---|---|---|
| V1 break time | open hour (08:00–08:59 LON) | confirmed 4/4 |
| V2 range width | wide vs trailing normal | confirmed 4/4 |
| V3 drift alignment | with-drift | confirmed 4/4 |

The continuation branch confirmed only V1 and is **not** carried into this step — a
one-variable survivor has no interaction to test, and running it anyway would be
searching for a pair that happens to look good.

## What is run

The three **pairwise** interactions on the declared default fade arm F1:
V1×V2, V1×V3, V2×V3. Plus the 3-way, reported for completeness.

## Prediction

Each pair should beat **both** of its own components, in both eras, if the variables
are capturing different parts of the same mechanism rather than three views of one
thing. If the pairs do **not** beat their components, the three variables are largely
redundant — which is itself the answer, and a useful one, because it would mean the
fade branch has one signal and not three.

## Hard rules, declared before the numbers exist

1. **The frozen default spec remains F1 unconditioned.** Nothing in this run promotes
   anything. Per §6.0.1 in-sample rank never promotes.
2. **A conditioned spec may be carried forward to L3 only if ALL hold:** it beats both
   component variables in **both** eras at **both** cost levels, **and** it retains
   **n ≥ 40 per era**. Below that floor the cell is reported and explicitly barred.
3. **The 3-way interaction is barred from being a gate at this sample size**, whatever
   it shows. F1 has 234 (2025) and 125 (2026) trades; a 3-way split of 125 is noise
   with a decimal point. It is printed so the record is complete, and labelled
   unusable.
4. **Every cell is ledgered**, including the barred ones. A search that only records
   the arms it liked is the failure mode the ledger exists to prevent.

## Spans / accounting

Unchanged: 2025 + 2026, 1 pt base and 2 pt strict cost, $160 risk sizing, era split,
never pooled. **Holdout look: NO.** 2023/24 untouched.

## Artifacts

`scripts/london_obk_interact.py`, `output/london_obk_interact.md`, trials to
`output/trial_ledger.parquet`.
