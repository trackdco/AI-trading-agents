# PRE-REGISTRATION — LDN-SWP-01: the Asia-sweep pair (candidates 2 + 3)

Filed per `docs/VALIDATION-PROCESS.md` §1, **BEFORE any census run**. The git timestamp of
this commit is the declaration. Trial family: **LDN-SWP-01**.

Theses: `research/candidates/london-asia-sweep-reversal.md` and
`london-asia-sweep-continuation.md`, both greenlit ANGUS 2026-08-04. Both flagged
*"event-tree pair — one family, one ledger"*; this document is that one ledger.

**Blocked on:** the §2 bars ratification. This prereg is written and committed now so it is
ready the moment the knobs are signed; **it must not be run until they are** — in
particular the kill-criterion-2 defect in `docs/VERDICT-LDN-INV-01.md` §"Process findings"
must be fixed first, since an equivalence-form absence rule is used below.

---

## 1. The single question

The two candidates are not two strategies. They are two readings of one event, and the
continuation thesis claims **timing decides which reading applies**:

- Asia builds a thin overnight range; stops pool just outside it.
- A sweep **before** deep liquidity (the 00:00–03:00 ET dead hour) is informed early
  positioning → London *extends* it.
- A sweep **after** the European open, into live liquidity, exhausts the stop pool with
  nothing behind it → price *reverts* into the range.

So one test answers both:

> **Does the timing of an Asian-range sweep predict the direction of the subsequent
> London move?**

If the answer is no, **both candidates die on one census.** If yes, the sign of each group
tells us which candidate survives, and L1 builds entries for that one only.

## 2. Claim (falsifiable)

Let `signed_ret` = the 03:00→06:00 ET point return **multiplied by the sweep direction**
(+1 if the Asia *high* was swept, −1 if the *low* was): positive = continued in the sweep
direction, negative = reverted.

**Primary claim:** `mean signed_ret` is materially **higher for dead-hour sweeps than for
post-open sweeps**, in both eras and both era directions.

## 3. Specification — this document authorises exactly this computation

**Groups** (mutually exclusive; days in neither are excluded — there is no event):
- **D — dead-hour sweep:** `sweep_side_dead ∈ {high, low}` (substrate: Asia extreme
  breached 00:00–03:00 ET).
- **P — post-open sweep only:** `sweep_side_dead == ''` **and** the Asia extreme is
  breached during 03:00–06:00 ET.

**Outcome window: 03:00→06:00 ET**, close-to-close of boundary minutes, master candle
store — declared primary before running. It is the tradeable window in both mechanical
skeletons (entry after 03:00, flat by 06:00). No other window carries the verdict.

**Primary statistic:** `Δ = mean signed_ret(D) − mean signed_ret(P)`, Welch two-sample,
two-sided, HC-free (unequal variances assumed).

**Exclusions, all declared here:**
- `dst_mismatch == True` (69 of 912 days): the European open is 04:00 ET on those, so the
  dead-hour definition does not hold. Reported separately, never pooled.
- `sweep_side_dead == 'both'` (4 days): direction undefined.
- Any day missing the Asia levels or the outcome window.

**Asia window:** the substrate default 19:00 (D−1) → 02:00 ET. **Not a parameter here** —
the skeletons list a 20:00→00:00 variant; testing both would be a search and is *not*
authorised by this document.

## 4. Secondary test — one, pre-specified, not a dial sweep

Candidate 3's second condition is narrow Asia. **One** secondary test: repeat the primary
statistic on the subset `asia_rng_pctl20 ≤ 0.2` (bottom quintile of the trailing-20-day
range percentile — the threshold is fixed here, not searched).

No other moderator is authorised. σ-location, retest depth, acceptance counts (N closes),
re-entry windows (M minutes) and the 20:00→00:00 Asia variant are **L1 execution
parameters** and are explicitly out of scope. Introducing any of them requires a new prereg.

## 5. Eras

Discover 2025 / validate 2026-01..07, **and the inverse pass** (discover 2026 / validate
2025) per §2.1. Both directions must agree. **2023/24 is NOT touched in any form** — the
run asserts the sealed years are absent before computing anything. No holdout look.

## 6. Fragility gate — runs FIRST, before any result is read

*Lesson from LDN-INV-01 (`docs/VERDICT-LDN-INV-01.md`): that candidate's entire signature
was three tariff-week days, and the check that revealed it was run last. Here it runs
first.*

Before the primary statistic is reported, `Δ` is recomputed with the 1, 3, 5 and 10
largest-|signed_ret| days removed, and on a 1/99-winsorised outcome. **If the sign of `Δ`
flips at any trim depth ≤ 3 in either era, the family is dead — regardless of every other
result in this document** (§2.5 drop-top-3). The full ladder is reported either way.

## 7. Decision rules — three-way, declared in advance

Kill criterion 2's failure-to-reject form is **not** used (it fires on small samples; see
`docs/DIAGNOSIS-LDN-INV-01-power.md` §2). Absence must be an equivalence claim.

Let `Δ₂₅` be the 2025 point estimate.

| outcome | condition |
|---|---|
| **PASS** | `Δ > 0` at p ≤ 0.05 two-sided in **both** eras, **and** the fragility gate (§6) is clear, **and** n ≥ 30 per group per era |
| **FAIL** | the validate-era 95% CI on `Δ` **excludes** `Δ₂₅` **and** contains 0 or is negative — or the §6 fragility gate fires |
| **INCONCLUSIVE ON POWER** | neither — the CI contains both 0 and `Δ₂₅`; report minimum detectable `Δ` and days required at 80% power |

INCONCLUSIVE blocks like FAIL (§5), but its follow-up is data, not redesign.

**Directional read on a PASS:** `signed_ret(D) > 0` supports the *continuation* candidate;
`signed_ret(P) < 0` supports *reversal*. Both, one, or neither may hold — the verdict states
which, and only the supported half proceeds to L1.

## 8. Mandatory reporting

- n per group per era, before and after exclusions.
- The full fragility ladder from §6, whatever it shows.
- Power and minimum detectable `Δ` at the realised n, per era.
- The `dst_mismatch` subset, separately, never pooled.
- Group means and the raw `signed_ret` distributions, so the reader can see whether `Δ` is
  a location shift or a tail artifact.

## 9. Trial accounting

**4 trials** into LDN-SWP-01: primary × 2 era directions, secondary (narrow-Asia) × 2.
No arms are abandoned; nothing further accrues. These count in the DSR denominator for the
session-structure family per §2.4, alongside the 4 already spent on LDN-INV-01.

## 10. Known limits

- **L0 structure measurement only.** This tests whether the timing→direction signature
  exists at all. It does **not** test either candidate's entry mechanics (failed
  acceptance, retest-and-hold), which are L1. If the signature is absent, no entry logic
  recovers it — which is exactly why this census is cheap and runs first.
- No costs, stops or targets. The §2.5 cost stack applies from L1. Nothing here is
  tradeable evidence in either direction.
- Crowding asymmetry acknowledged: the reversal reading is EXTREME-crowded retail lore
  ("Judas swing"), the continuation reading is niche. A null on the reversal side is the
  more expected outcome and should not be over-read as a surprise.
- Candidate 3's supporting statistics come from one community's study (claims from
  snippets, not verified reads). This census — not that study — is the evidence.
- `sweep_side_dead` uses intrabar high/low against the Asia extremes: a wick through
  counts as a breach. This is deliberate (the stop pool is reached by the wick), but it
  means "sweep" here is not an acceptance test.
