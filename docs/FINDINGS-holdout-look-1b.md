# HOLDOUT LOOK #1 — SECOND AND FINAL PASS (H1, H4)

2026-08-07. Corrected sweep builder SHA `6f2f4c8f`. **Permanent for this
venue. No further contact, either direction.**

## THE FIRST PASS'S STRUCTURAL FAILURE, stated alongside the result

`scripts/htf_ma_sweep_locus.py` sourced prior stopped attempts from
`levels_fit_v1.parquet` — **the fit file alone**. sweep_b is defined as a
sweep of a prior stopped attempt's own stop, so on sealed days there were no
prior attempts to reference and **cell (b) could never fire**.
`sweep_sealed.parquet` came back **7,232 rows, 100% sweep_a, zero sweep_b**.

Consequences at the first pass, unchanged in the record:

- **H4 was NOT EVALUABLE** — zero rows read, so no look was spent on it.
- **H1 was VOID** — R1 defines the LONDON book as composite **+ sweep_b**;
  what ran was composite only, and on fit sweep_b is 55% of that book. The
  first pass's +0.183 / +0.116 was a valid test of London composite-only,
  which failed, and was never a test of H1.

The builder also computed a `gray` bucket and never wrote it, so 2025-01..05
— **half of Block B** — had no sweep rows at all. Fixed in the same change.

## CALIBRATION FIRST, before any sealed contact

The corrected lookup was pointed at the **fit span** and checked against the
published artifact:

| check | result |
|---|---|
| rows | 12,607 published vs 12,607 corrected |
| sweep_b rows | 8,243 vs 8,243 |
| identical row set on (day, t, side, n_attempts) | **yes**, 0 either way |
| entry / stop / risk / direction | identical, max diff **0.000e+00** |
| out_ship / out_hold / out_trail / mfe_r / w15 | identical, max diff **0.000e+00** |

**Byte-identical.** The calibration run wrote to a suffixed path so nothing
published was overwritten before the check passed.

*Why the fit-side lookup is unchanged in content:* `levels_fit_v1` and
`levels_fit` hold identical rows and are identical on every field this
builder consumes — `t`, `stop`, `direction`, `out_hold`, `mfe_r`, `risk`,
`out_ship` — and on the derived `stopped` flag (23,444 attempts).
`levels_fit` merely adds three timestamp columns the sweep builder never
reads. Verified before the source was changed, not after.

*(One line in the calibration log reads "+0.146R at 28.33/day" against
BR-15b's "+0.175R at 12.79/day". That is not a discrepancy — it is the raw
unclustered row mean, a statistic never published, versus the first-of-fight
clustered book. Since the artifact is byte-identical, every statistic
derived from it is necessarily identical too.)*

## THE RESULT

Sealed + gray in venue: **20,743 sweep rows, 13,832 of them sweep_b** —
against zero at the first pass.

LONDON book: **1,502 fights — 787 sweep_b, 715 composite.**

| claim | Block A | Block B | verdict |
|---|---|---|---|
| **H1** LONDON base rate (composite + sweep_b) | n=593, EV **+0.221**, ×5 CI **[+0.047,+0.400]** | n=909, EV **+0.177**, ×5 CI **[+0.032,+0.317]** | **PASS** |
| **H4** sweep_b LONDON alone | n=356, EV **+0.251**, ×5 CI **[+0.071,+0.441]** | n=554, EV **+0.223**, ×5 CI **[+0.054,+0.388]** | **PASS** |

Both claims clear a **Bonferroni ×5 two-sided 99% interval in both blocks
independently**, against a declared bar of EV > 0 with the corrected lower
bound above zero. Neither block is underpowered (all four ≥ 356 fights
against a 100 threshold).

## WHAT THIS MEANS, under the pre-committed reading

**R5 was written before any of this and gives PASS the strong reading:**

> *"PASS is strong: the book cleared in the regime least favourable to it,
> and no regime caveat survives."*

The sealed span is bull-heavy and the book carries a measured
−0.0155R-per-1%-NQ slope (BR-17). It cleared anyway, in both blocks.

**R2's contingency does not fire.** It read: *"if H1 passes and H4 fails,
the London book is re-declared without it."* Both passed, so the London book
stands as declared — composite **plus** sweep_b.

**sweep_b is the stronger component, not the weaker one.** H4 alone returns
+0.251 / +0.223 against the composite-only's +0.183 / +0.116 from the first
pass. The component whose inclusion R2 flagged as "the live decision" is the
one carrying the book.

**Shrinkage is normal and the result survives it.** Fit +0.357 → holdout
+0.221 (A) / +0.177 (B), roughly half the fit estimate, still clearing a
×5-corrected interval in both blocks.

## THE VENUE, FINAL STATE

| claim | verdict | source |
|---|---|---|
| **H1** LONDON base rate | **PASS** | this pass |
| H2 NY_PRE base rate | FAIL | first pass, unchanged |
| H3 NY_AM base rate | FAIL (one-block pass is a miss) | first pass, unchanged |
| **H4** sweep_b LONDON alone | **PASS** | this pass |
| H5 closeloc cut | PASS | first pass, unchanged |

**The bar-only venue is now closed.** No further contact in either
direction, regardless of anything found later.

The picture is no longer the inversion reported after the first pass. It is
the ordinary one the programme was built to produce: **the London base
population validated out of sample, NY did not, and one selection layer
validated with it.**

**No real capital moves on any of this.** Nothing here is armed or adopted;
the arming checklist — including the recorder/VPS item — belongs to whenever
there is a rebuilt canon to arm.
