# DECLARATION — HOLDOUT LOOK #1 (bar-only venue)

Written 2026-08-07 AFTER items 1–3 completed and BEFORE any sealed row was
read. Items 1, 2 and 3 are committed (4ffec732, 950c71aa and this branch's
risk-spine commit) and their results are on the record; nothing below was
written to fit a sealed number, because no sealed number exists.

**This is the programme's first holdout look.** It spends the bar-only
venue (23 months, ~±4pp). The flow venue remains unspent and is not
touched here.

---

## R0 — RULING: the UNSELECTED base population is what gets tested

No selection layer goes to the holdout. Not S1, not any cut, not a
"base-plus-best-filter" variant. Reason, recorded: if a fit-selected book
is sent, a pass or fail cannot separate the POPULATION from the CUT, and
there is no second venue afterwards to disentangle them. The population is
the object; a selection layer on top ships on fit + forward validation
(the seven-locus recorder), exactly as S1 does.

## R1 — RULING: the composite is declared, not a component

What is tested is the book that would be TRADED, not one of its parts.
Validating a component and shipping a composite is the failure this
ruling exists to prevent.

**Primary claim = the item-2 composite**, exactly as specified:

```
COMPOSITE = union-break(VAL, VWAP-1) + reject-arm(15m BB MA)
  fit: 3,336 fights | 11.42/day | EV +0.186R [+0.129,+0.244]
       H2-2025 +0.177 [+0.098,+0.261] | H1-2026 +0.196 [+0.111,+0.283]
```

**⚠ OPEN DECISION, must be resolved BEFORE the look runs.** Item 6
(committed 451c8fd3, run after item 2) found a THIRD qualifying
population: sweep_b — the sweep of the trader's own stop after a stopped
attempt — at +0.175R with both eras clear at all four X, 3,723 fights
(12.79/day) structurally clustered. It cleared the same declared bar.

If the intended shipped book includes sweep_b, then the composite above is
a COMPONENT and testing it would violate R1. The three-way union is
~24 fights/day, which raises an operational question (concurrency,
execution capacity) that item 3 has not answered for that scale.

**Therefore:** the primary claim stands as the two-population composite
UNLESS the trader states before the look that sweep_b ships too, in which
case this file is amended to the three-way union and re-committed first.
This is a one-line change and it must happen before contact, never after.

## R2 — Registered claims and the multiplicity correction

Three claims go into this look. **Bonferroni ×3** is applied to every
one — stated now, not after.

| # | claim | population | declared sign & bar (per block) |
|---|---|---|---|
| H1 | COMPOSITE base rate | item-2 composite (or three-way, per R1) | EV > 0, day-boot 97.5% lower bound > 0 after ×3 correction, in **each** block |
| H2 | sweep_b base rate | sweep-reclaim cell (b), X=0.5W fights | same |
| H3 | closeloc cut (queued since D1) | reject-arm first-of-fight book | lift ≥ +0.04R with ×3-corrected CI excluding zero, in **each** block |

H3 is the previously queued bar-only claim and is carried here so its
multiplicity is paid in the same look rather than spent separately later.
Its fit-side credentials are known and spent — the holdout is its only
remaining venue (FINDINGS-D).

## R3 — Two blocks, both must pass

Per the standing D2 rule, unchanged:

- **Block A:** 2023 bar-only months (2023-01..06, 08, 10, 12 — 9 months)
- **Block B:** 2024-01..2025-05 bar-only months (14 months)

A claim passes ONLY if it clears its bar in Block A **and** Block B
independently. A one-block pass is recorded as a miss. The chronological
split is deliberate: it catches internal era-flips a pooled look averages
away.

## R4 — Aggregation rule, fixed in advance

1. **Substrate:** the sealed table is built by the SAME committed builders
   that produced the fit tables (`htf_ma_level_census.py`,
   `htf_ma_sweep_locus.py`), at the same commit, with no variant. The
   commit SHA is recorded in the look's log.
2. **Entry gate:** must PASS on the sealed build before any row is read.
3. **Unit:** the 18:00-anchored session day.
4. **Fights:** structural, X = 0.5W, the declared value — **not** re-tuned
   on the holdout, and the X-sensitivity is NOT re-run there.
5. **Point estimate:** mean out_ship over first-of-fight rows.
6. **Interval:** day-level bootstrap, 2,000 draws, seed 20260807,
   percentile CI, widened to the ×3-corrected level.
7. **Exclusions:** the builder's named exclusions only (no_next_open,
   gap_through_stop), exactly as on fit.
8. **No re-runs.** One look. A failed claim is recorded as a miss and is
   not re-tested on a re-cut population.

## R5 — What a pass and a fail each MEAN (declared before seeing either)

This is stated in advance because item 1 changed the interpretation.

The sealed span is **bull-heavy**, and the composite's short-heavy
components carry a measured negative EV-vs-market slope (−0.0155R per 1%
NQ month, CI [−0.0207,−0.0063]). So:

- **PASS** is strong evidence: the book cleared its bar in the regime
  least favourable to it. No regime caveat survives a pass.
- **FAIL** is ambiguous and will be recorded as such — it cannot
  distinguish "no edge" from "edge, wrong regime". A fail therefore does
  NOT kill the population; it sends it to forward validation with the
  regime caveat attached, and the fail is permanent for this venue.

Declaring this now removes the temptation to discover the regime excuse
after a bad result.

## R6 — Standing constraints, unchanged

Flow venue unspent. Break-arm candidate sets still wait on the base
population. Funded-layer optimisation stays parked. Nothing touches the
sealed rows until this file is committed.
