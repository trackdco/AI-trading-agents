# VERDICT — LDN-DEF-01 (level-defense-flow, absorption at a defended level)

**Drafted for Brake's signature.** Per `docs/VALIDATION-PROCESS.md` §5. Routes to Angus.
Reproduce: `python -m scripts.ldn_def01_census`.

Declared `PREREG-london-level-defense-flow.md` at **16:49:59Z**, run unchanged.
**Sealed 2023/24 untouched — holdout footprint files excluded by name and asserted absent
from the loaded file list. No holdout look.**

---

## VERDICT: **FAIL** on all three measures. Price-level absorption does not separate winners from losers at defended London levels.

| measure | 2025 ρ | 2026 ρ | AUC (25/26) | verdict |
|---|---|---|---|---|
| ABSORB | +0.040 | **−0.144** | 0.478 / 0.451 | **FAIL** (fragility) |
| PIN | +0.063 | **−0.012** | 0.515 / 0.510 | **FAIL** (fragility) |
| ICEBERG | +0.037 | **−0.116** | 0.468 / 0.474 | **FAIL** (fragility) |

All three were declared **positive**. All three are weakly positive in the discovery era and
**negative in the validate era**. Every 95% CI contains zero. No measure survives
Holm–Bonferroni. **All three fail the fragility gate** — the sign flips as the level band
moves between 1, 2 and 4 ticks, which is what noise does.

**AUC 0.451–0.515 against 0.5 for a coin flip.** n = 99 / 89, both clear of the floor;
minimum detectable ρ **0.248 / 0.262**. This is a null on evidence, not on power.

---

## 1. Why this result closes the order-flow question, where LDN-FLOW-01 did not

LDN-FLOW-01 tested *minute-aggregate* flow and I was explicit about its limit:

> "Real absorption reads at a price level within the minute — 400 contracts hitting one
> price that does not move. That signature is invisible at this resolution and **is not
> tested here**."

That limit is now retired. This test reads **per-(minute, price, aggressor-side) footprint**
— 24.8M rows — and measures exactly that signature: absorbed-aggressor volume within 2 ticks
of the defended level, and effort divided by result.

**It finds nothing.** The mechanism that "uses our depth/footprint data advantage hardest",
in the candidate's own words, does not identify which level reclaims work.

## 2. The era flip, again

The median split repeats the pattern that killed TRAPPED in LDN-FLOW-01:

| measure | era | high half | low half |
|---|---|---|---|
| ABSORB | 2025 | +3.06 (46.9% win) | +0.51 (48.0%) |
| ABSORB | **2026** | **−11.77** (47.7%) | **+6.28** (53.3%) |
| ICEBERG | 2025 | +5.31 (46.9%) | −1.70 (48.0%) |
| ICEBERG | **2026** | **−10.31** (47.7%) | **+4.86** (53.3%) |

In 2025, high absorption looks mildly helpful. **In 2026 it is actively harmful** — the
high-absorption half loses 11.8 points an event while the low-absorption half makes 6.3.

A single-era study would have concluded that absorption filtering works. Two eras say it is
noise. That is now the third time in this programme the discover/validate split has caught a
result that looked tradeable on one era alone.

## 3. What the fragility gate caught that the primary alone would not

All three measures fail on the **proximity ladder** — ρ changes sign as the band around the
level moves from 1 to 4 ticks. ABSORB 2025: +0.034 → +0.040 → −0.011. ICEBERG 2025:
+0.017 → +0.037 → −0.022.

A real absorption signature would not care whether you look 1 tick or 4 ticks around the
level; defence happens at a price, and widening the window slightly should strengthen the
reading, not invert it. The sign inverting on a band width is the signature of a statistic
built from noise.

## 4. Clean-run confirmation

- **Event set asserted unchanged:** the trap rebuild reproduces the signed-off LDN-TRAP-01
  verdict (161/−2.30, 89/−2.64) before any footprint is read. The run aborts otherwise.
- **Causality asserted in code:** every footprint minute read lies in `[t−3, t]`; the
  outcome is measured over `(t, window close]`. `assert max(mins) <= t` fires on every
  event. Given I re-created a causality-class defect in LDN-VT-01 an hour before this run,
  it is checked mechanically, not by eye.
- **Sealed span:** holdout footprint files (`footprint_holdout_*`) are excluded by name and
  the loader asserts none are present. 2023/24 dropped upstream by `fit_only()`.
- **Absorbed side is fixed by the event**, not chosen: buyers on an upside break, sellers on
  a downside break.

## 5. Trial accounting

**6 trials** into LDN-DEF-01 (3 measures × 2 era directions). London programme running
total: **34**. These count in the DSR denominator per §2.4. Median splits and both ladders
add no trials.

## 6. Recommendation to Angus

**Tombstone the family.** LDN-TRAP-01 (candles expression) was a well-powered null.
LDN-DEF-01 (flow expression, the same events with an absorption requirement) is a null at
the resolution that can actually see absorption. The candidate's own thesis names them one
family, and the family has now failed in both of its expressions.

**And note what this costs to know: nothing was deployed.** Two censuses, 10 trials, no
holdout looks.

The NY-canon veto question is now moot — there is nothing to co-ship. I would still flag
that the veto would very likely have tripped anyway (HIGH input-family overlap: depth and
flow are the canon's core families), so even a PASS would have gone to you as a waiver
decision rather than straight to deployment.

## 7. What this does not establish

- **L0 structure only.** No stops, targets or costs. The candidate stakes much of its claim
  on a tight stop ("defender pulls = thesis dead, out fast"), and holding to the window
  close cannot represent that. A directional signature this absent is unlikely to be
  rescued by exits, but this test does not disprove it.
- **ICEBERG is a proxy, not a measurement** — declared as such in the prereg. The thesis
  defines an iceberg against *displayed depth*; our depth is one book snapshot per minute,
  which cannot support that comparison. What was measured is volume concentration at a
  single price.
- **Out of scope and untested:** the flip rule (reverse on a post-detection close beyond the
  level), and the CVD-divergence variant fading session extremes on delta non-confirmation.
  Both are separate events and would need their own preregs. Given two nulls in this family,
  neither looks like a good investment.
- The substrate is level-reclaim events. Absorption at other event types — session extremes,
  VWAP bands — is not covered.
- Resting-liquidity measures from MBP-10 (book imbalance, size at level) remain untested and
  are a different information family. Our depth is one snapshot per minute, so pulled bids
  and iceberg refill are not measurable from it at all.
