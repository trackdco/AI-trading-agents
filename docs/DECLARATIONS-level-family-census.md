# DECLARATIONS — E1 LEVEL-FAMILY CENSUS, E2 BREAK ARM, E3 SWEEP RE-ENTRY

Declared 2026-08-07, BEFORE any E-series compute. Nothing in this file was
written after seeing a number it constrains. Direction change recorded:
optimisation of the funded layer is STOPPED; the weakness under test is the
TRIGGER POPULATION, not the selection layer.

Rationale on the record (trader's, verbatim in substance): every study to
date has been selection inside a fixed trigger population. Selection can
only remove bad trades from what is already there; the trigger definition
decides what is there at all. One survivor from 18 candidates × 2 arms
says the selection layer is close to exhausted ON THIS POPULATION — not
that the strategy is. And the base book is era-significant only at X=0.5W
(A1), so further cuts polish a marginal foundation. The M-TABLE indexes
fights at ONE level (the 15m BB MA) out of ~14 in the traded level set.

---

## E1 — LEVEL-FAMILY CENSUS

### E1.0 Scope, declared and closed

Four families, six loci, scoped from the trader's own narration and
nothing else. Sweeping all fourteen loci × two mechanisms × two arms would
be 56 censuses — a search wearing a census's clothes. **A fifth locus
requires its own declaration and a reason from the trading, never from a
result.**

| # | family | loci | narration warrant |
|---|---|---|---|
| C | control | 15m BB MA | the incumbent; calibration only |
| 1 | profile POC | POC | Setup 2's entry |
| 2 | value area | VAL, VAH | Setups 1, 3 and the rejected setup keyed off VAL; VAH is its declared symmetric counterpart |
| 3 | VWAP | VWAP | anchor of the ±1 bands |
| 4 | VWAP bands | VWAP−1, VWAP+1 | Setup 1 stacked on VWAP−1; Setup 6's target |

**Run order (declared): C, then 1, 2, 3, 4.** The control runs FIRST and
is a calibration gate, not a finding: the harness must reproduce the
incumbent 15m BB MA reject book within tolerance before any new locus is
read. Tolerance declared now: fight count within ±2% and pooled EV/fight
within ±0.02R of BR-9's +0.149R. If the control misses, no locus is
reported and the harness is fixed first.

### E1.1 Publication rule

**Base rates are published per locus whether positive or null.** Every
null enters BASE-RATES.md on the same footing as every other entry — a
locus that produces no edge is a NULL that future level ideas must beat,
which is the entire point of the base-rate library. No locus is dropped
for being uninteresting.

### E1.2 What is reused, unchanged (no new pipeline)

- **Entry model:** decision at the trigger-bar close; entry at the NEXT 1m
  bar's open (reject arm) or at the as-of level of the previous 1m close
  (break-arm retest limit). The entry-price gate
  (`scripts/htf_ma_entry_gate.py`, T1/T2/T3) MUST PASS on the new builder
  before any row is read.
- **Stop:** the trigger candle's extreme ± 1 tick.
- **Exit:** the shipped exit, unchanged — 75% out at 3R, remainder trailed
  on completed 15m structure. The trail's structure reference stays the
  15m BB MA for EVERY locus, so exits are identical machinery across loci
  and only the fight locus varies.
- **Fight criterion:** structural, X = 0.5W excursion away from THE LOCUS
  (Phase 0 item 3), with the full X ∈ {0.25, 0.5, 1.0, 2.0}W sensitivity
  reported per locus since A1 showed the convention is worth ±0.2R.
- **Scale unit:** W = the 15m BB band width, for ALL loci. W is the
  programme's volatility ruler (BR-4: adverse-before-touch 0.43W,
  era-stable in W and not in points), not a property of the BB MA locus.
  Using one ruler keeps loci comparable. Declared, not swept.
- **Trigger timeframe:** 15m for all loci. The incumbent census is
  15m-referenced, so this is the comparability choice. The LTF is a
  declared constant; sweeping it is forbidden in this study.
- **Level as-of granularity:** per-1m, matching the incumbent exactly.
  (Benchmarked before declaring: full-span per-1m developing-profile
  snapshots cost ~4 minutes, so no coarsening compromise is required and
  none is taken.)
- Same day-level bootstrap (seed 20260807, 2,000 draws), same
  fit/sealed/gray split, same sealed handling — sealed rows written
  unread, neither holdout look spent.

### E1.3 Per-locus report (fixed before running)

Fights; fights/day; base EV/fight under the shipped exit; era split
(H2-2025 / H1-2026); day-boot 95% CIs; MFE-in-R quantiles; and the
clustering sensitivity across X ∈ {0.25, 0.5, 1.0, 2.0}W. Both mechanisms
(M1 rebalance-to-level, M2 rejection-off-level) and both arms
(reject / break) reported separately. No selection, no cuts, no filters —
conditioning columns are recorded and never applied.

### E1.4 Bar for calling a locus WORTH FOLLOWING UP

Declared now so no locus is talked into significance later. A locus earns
a follow-up study only if: EV/fight > 0 with day-boot CI clear of zero in
BOTH eras at the declared X=0.5W, AND the sign holds at a majority of the
four X values. Anything less is published as a base rate and parked. This
is deliberately the same bar BR-9 met and no easier.

---

## E2 — BREAK ARM, UNPARKED

The break arm is a third of the population, has never been honestly
measured since the row-existence fix, and its different-bets thesis (a
rejection bets the level HOLDS; a break-retest bets it FLIPPED) has never
been tested on its own terms. Its headline was invalidated, so there is
nothing to un-learn — this is a clean FIRST measurement, not a re-run.
Its virtue is frequency without size, which is the only lever that fixes
the timeline.

Declared deliverables:
1. Executable break book (first-of-fight, retested fights) under the
   shipped exit: EV/fight, era split, day-boot CIs, at all four X values.
   This is the break-arm counterpart of BR-9 and does not exist yet.
2. P(retest | break) and the non-retested travel distribution, restated on
   the fixed table, reported ALONGSIDE the book (they price the branch's
   fill rate and opportunity cost).
3. Its OWN candidate set with its own declared bar — variables motivated
   by the flipped-level thesis, not inherited from the reject arm's list.
   The candidate set is declared in an appendix to this file BEFORE the
   split-half runs, on the SAME frozen day-split (seed 20260807) used by
   the reject-arm cut study.

Bar for a break-arm cut: identical to the reject arm's — implied lift
≥ +0.05R on Half 1 to be pre-registered, then sign and bar unchanged on
Half 2, then the three gates. No easier bar for a smaller population.

---

## E3 — SWEEP-CONDITIONED RE-ENTRY

Plain re-entry is dead (−0.22R/attempt, A2), so the sweep condition
carries all of the work in the one documented winner. This is the first
variable in the programme that comes from the trader's GRAMMAR rather
than from the table's columns, and it is logged as such.

### E3.1 Sweep definition, declared before any measurement

A SWEEP+RECLAIM occurs on side S between two triggers of the same fight
iff, on completed 15m bars strictly between them:

- **Reference extreme:** the lowest low (for a long-side reclaim) or
  highest high (short side) of the **8 completed 15m bars** preceding the
  stopped attempt — a 2-hour swing window.
- **Penetration:** a subsequent bar's low (high) trades **≥ 4 ticks
  (1.00 pt)** beyond that reference extreme.
- **Reclaim:** a completed 15m bar **closes back inside** the reference
  extreme (above the swept low / below the swept high) within **3 bars**
  of the penetration.

All three conditions must hold. Lookback 8, penetration 4 ticks, reclaim
window 3 bars — declared now, **never swept**. If the definition is wrong
it fails as declared and is recorded as a miss; a redefinition requires a
fresh blind declaration justified from the trading, not from the result.

### E3.2 Law 7 arithmetic FIRST

Before the cut is written, compute what it can be worth through the
mechanism it will be used in: re-entries are ADDED to the book, so
EV moves from E to (n_A·E + n_s·μ_s)/(n_A + n_s) where n_A = 1,830
first-of-fight rows at E = +0.149R, n_s = qualifying sweep re-entries and
μ_s their mean. The arithmetic is published BEFORE the measurement, along
with the μ_s and n_s required to clear +0.02R of book improvement. If the
achievable ceiling is below that, the test is recorded as not worth
running and is not run.

### E3.3 Bar

Fresh blind bar: the sweep-conditioned re-entry subset must show μ_s > 0
with a day-boot CI clear of zero, AND deliver ≥ +0.02R of book
improvement by the arithmetic above, on the SAME frozen split-half
(explore on Half 1, confirm on Half 2), then the three gates.

---

## Standing, unchanged by this direction change

Both holdout looks remain unspent. The closeloc bar-only claim stays
queued as declared. The frozen A-1 spec is untouched and A-3 is not built.
The flow recorder remains ready for the VPS — it is orthogonal to this
direction change and its data keeps accruing value regardless of which
locus wins.
