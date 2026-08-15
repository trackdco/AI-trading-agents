# DECLARATION — ROOM-TO-RUN ON GOLD

Written 2026-08-15, **before the gate has been run on GC in any form**. Fit-side by
construction — see §5. Nothing here touches the NQ holdout venues.

---

## §0 — THE QUEUE ITEM IS OUT OF DATE, AND THAT CHANGES THE TEST

`docs/HANDOFF-2026-08-15-gold-research.md` §9 item 2 asks for "room-to-run on gold
(BR-32/35)". **BR-32/35 have been superseded on NQ.** Reading the base-rate ledger
forward from them:

- **BR-53** decomposed the gate. `next_lvl_R >= 3R OR open space` is two claims bundled,
  and only one works: **open space +1.518R (3m) / +1.376R (5m), both eras, both TFs**,
  against **>=3R at +0.203 (H2 does not clear) / −0.053 (neither era)**. The gate's value
  is *whether there is an obstacle at all*, not *how much room*.
- **BR-54** swept the floor on the population where it has range: 1.0R −0.033, 1.5R
  +0.026, 2.0R +0.062, **3.0R +0.203**, 4.0R +0.002, 5.0R −0.088. Non-monotone, peaking
  at exactly the declared threshold and collapsing either side. That is the shape of a
  tuned parameter.
- **BR-57** restated open space against a frozen split-half and **supersedes BR-32/35**.

Porting BR-32/35 to gold would therefore port the version whose stated mechanism has
already been refuted on the instrument it was found on. This declaration ports the
**decomposition** instead. It is the same discipline the level census used: NQ's *answer*
(vwap_m1, val) did not transfer and NQ's *method* found gold's own answer (vah).

## §1 — THE VARIABLE

`next_lvl_R`, computed exactly as `scripts/phase1_build_cols.py` computes it and using
`htf_ma_level_census.level_series` rather than a reimplementation:

> For a row at locus L entering long/short at `entry` with risk `risk`, take every **other**
> locus in `LOCI`, read its as-of value at the close of the bar **before** entry, keep those
> lying ahead of entry in the trade direction, and take the nearest.
> `next_lvl_R = distance / risk`. **No level ahead → undefined → OPEN SPACE.**

The as-of convention is the incumbent's: row *t* is the level at the close of bar *t*,
usable for a decision at *t+1m* and never at *t*. That is what makes this lookahead-free,
and it is the same convention the level census already fights on.

## §2 — POPULATION

GC front month, `data/gc_1m.parquet` (provenance: `docs/DATA-PROVENANCE-gold.md`).

- **First trigger per structural fight** — one row per `(locus, arm, cluster_id)`, via
  `gold_level_report.first_of_fight`, imported not reimplemented. Stated up front because
  BR-10 records the same population reading −0.04R to +0.20R across conventions.
- **Risk floor 0.2 points**, the gate-selected floor from `DECLARATIONS-gold-vah-break`.
  Applied to the baseline *and* every gated cell, so what is measured is room alone and
  not the floor's contribution.
- Shipped exit (`out_ship`), **cost 0.20 points** — the assumed round turn. Queue item 1
  is still unmeasured and `ohlcv-1m` cannot measure it; every EV below inherits that
  assumption.
- `TICK=0.10`, profile `bin_width=0.4` (4 ticks), matching `scripts/gold_level_census.py`.

**What this is not.** BR-35 measured room on NQ's *LTF trigger recensus* at 3m and 5m.
Gold has no LTF trigger stream, so there is no like-for-like port and none is attempted.
This measures room on gold's **level-census population** at 1m decision bars, which is the
natural gold analogue and a different population from BR-35's. Cross-instrument magnitude
comparisons against +1.518R are therefore not available and will not be drawn.

## §3 — THE CELLS, FIXED NOW

**Primary — 3 cells**, the BR-53 decomposition:

| # | cell | rule |
|---|---|---|
| A | **OPEN SPACE** | `next_lvl_R` undefined — no other locus ahead at all |
| B | **ROOM ≥ 3R** | `next_lvl_R >= 3.0` (level ahead, but far) |
| C | **BUNDLED** | A ∪ B — the BR-32/35 form, carried only for comparability |

Baseline for every lift: all first-of-fight rows at the same 0.2 floor.

**Secondary — descriptive, not counted toward the primary bar:** the BR-54 floor sweep
(1.0 / 1.5 / 2.0 / 3.0 / 4.0 / 5.0 R) on the level-ahead subpopulation, and the break /
reject arm split of whichever primary cell survives.

## §4 — THE BAR, AND WHAT COUNTS AS A REFUTATION

- **Day-clustered bootstrap** (BR-42) on every interval. `AU.dboot_mean`.
- **Both-era clearance** (E1.4): the lower bound must clear zero on the full sample **and**
  in both halves independently. On gold this bar has teeth — 8 of 14 level cells cleared
  the full sample and only 1 cleared both halves.
- **Dual currency** (Law 3): win% and EV on every row. **A cell that lifts win rate and not
  EV is a refutation, not an improvement** — BR-20/46/48 are three recorded cases, and the
  tomtrades 89.86%-win-rate cell is the cleanest.
- **Multiplicity stated up front:** 3 primary cells.

## §5 — WHY THIS CANNOT CONFIRM ANYTHING

The whole GC sample has already been through the 14-cell level census that produced
`vah · break`. Every number this run yields is **fit-side**, on data already looked at. It
can refute, it can screen, and it cannot confirm. A real confirmation needs gold data the
analysis has not touched — a later-dated export, not a re-split of this one, because a
holdout carved from a sample already analysed is a split and not a holdout.

## §6 — PREDICTIONS, SCORED AFTER THE RUN

1. **OPEN SPACE (A) clears both eras; ROOM ≥ 3R (B) does not.** The direct port of BR-53.
2. **If B does show an edge, the floor sweep is non-monotone** — the BR-54 signature of a
   tuned threshold rather than a gradient.
3. **BUNDLED (C) lands between A and B**, i.e. bundling dilutes rather than adds.
4. **Open space is rare** — on NQ it was 5.8–7.0% of the ungated population. If gold's
   open-space share is far larger, the loci are not partitioning gold's price space the way
   they partition NQ's, and any magnitude comparison is meaningless.

A refutation of 1 is a result and gets reported as one. **No parameter is to be moved to
make any cell clear.**
