# PRE-REGISTRATION — LDN-INV-01, trial 2: continuous asymmetry test

Filed per `docs/VALIDATION-PROCESS.md` §1, **BEFORE the test is run**. The git timestamp
of this commit is the declaration. Same trial family as trial 1: **LDN-INV-01**. Thesis:
`research/candidates/london-inventory-fade.md` (greenlit ANGUS 2026-08-04).

Motivated by `docs/DIAGNOSIS-LDN-INV-01-power.md`: trial 1's quintile design uses 2/5 of
the sample (56 of 139 days in 2026) and is underpowered (44% on the thesis window). This
trial tests the **same thesis on the same data with a specification that uses every day**.

## Why a new trial rather than a re-read of trial 1

The method changes, so it is a new trial and it is ledgered as one. Nothing about trial 1's
result is revised or withdrawn — it stands. This trial does not get to overwrite it.

## Claim (falsifiable, unchanged in substance from trial 1)

NQ point returns in the European-open window are **negatively related** to the prior US RTH
return — bad US days are bought back — and this relationship is **asymmetric**: materially
present on the downside, absent or weaker on the upside. A symmetric relationship is generic
mean reversion, not an inventory effect.

## Specification (this document authorises exactly this computation)

Per day, OLS with HC1 heteroskedasticity-robust standard errors:

```
window_ret  =  b0  +  b_neg * min(prior_rth_ret, 0)  +  b_pos * max(prior_rth_ret, 0)
```

- `window_ret` — NQ point change, close-to-close of boundary minutes, master candle store.
- `prior_rth_ret` — from `output/london_day_features.parquet`, as trial 1.
- Hinge at zero, declared in advance. No knot search, no threshold tuning, no other
  regressors.
- **b_neg < 0** is the inventory fade on the downside. **b_pos ≈ 0** is the asymmetry.

**Primary window: 03:00→04:00 ET** — declared primary *before running*, because it is where
trial 1 and the thesis both locate the residual effect (the classic 02:00–03:00 hour is
publicly dead post-2021). The other three authorised windows (02:00→03:00, 04:00→06:00,
02:00→06:00) are reported for completeness and are **not** eligible to carry the verdict.
This is a single-window test with three descriptive companions — not a four-window search.

## Eras

- Discover 2025 / validate 2026-01..07, **and the inverse pass** (discover 2026 / validate
  2025) per §2.1. Both directions must agree.
- **2023/24 is NOT touched in any form.** `fit_only()` drops the sealed years and asserts
  they are gone. No holdout look.

## Trial accounting

**2 trials** into the LDN-INV-01 ledger (one per era direction), one specification, one
primary window. No arms are abandoned, so nothing further accrues. These count in the DSR
denominator for this family per §2.4.

## Decision rules — three-way, declared in advance

Trial 1's kill criterion 2 is *not* reused: `docs/DIAGNOSIS-LDN-INV-01-power.md` §2 shows it
fires on the discovery era, because "statistically indistinguishable" is satisfied by low
power rather than by absence. This trial replaces it with an explicit three-way rule.

Let `D = b_neg − b_pos` (the asymmetry), and `D₂₅` the 2025 point estimate.

| outcome | condition | meaning |
|---|---|---|
| **PASS** | `b_neg < 0` at p ≤ 0.05 one-sided **and** `D < 0` at p ≤ 0.05 one-sided, **in both era directions** | asymmetric fade confirmed |
| **FAIL** | in the validate era, the 95% CI on `D` **excludes** `D₂₅` **and** contains 0 or is positive | the discovery-era asymmetry is affirmatively absent |
| **INCONCLUSIVE ON POWER** | neither of the above — the CI on `D` contains both 0 and `D₂₅` | the sample cannot separate the hypotheses; report the minimum detectable `D` and the days required at 80% power |

INCONCLUSIVE blocks like FAIL per §5, but its follow-up is data, not redesign.

Additional kill (carried unchanged from trial 1): **fragility** — if the fit is driven by
≤ 3 days (drop-top-3 per §2.5), it is dead regardless of the above.

## Reported alongside, mandatory

- Power and minimum detectable `D` at the realised n, for every era and window.
- Drop-top-3 refit on the primary window.
- Per-era n. No magnitude claim is quotable below the §2.2 pooled floor of 100.

## Known limits

- OLS on daily point returns; heteroskedasticity handled by HC1, serial correlation not
  modelled (day-level, non-overlapping, so §2.2's effective-N correction is not engaged).
- The hinge at zero is a modelling choice, not a measured breakpoint. A different knot
  might fit better; searching for one would be a new trial and is not authorised here.
- L0 structure measurement only — no stops, targets or costs. The §2.5 cost stack applies
  from L1, and nothing here is tradeable evidence.
- Parity: `docs/DIAGNOSIS-LDN-INV-01-power.md` §1 records an unreconciled 1.2–4.6 pt gap
  between this pipeline's census reproduction and trial 1's ledgered figures. `D₂₅` is
  computed **within this run** so the comparison is internally consistent regardless.
