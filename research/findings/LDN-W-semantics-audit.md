---
date: 2026-08-05
status: reference — feature-semantics audit under §5.12.15
tags: [london, depth, self-correction, feature-semantics]
sources: ["docs/VALIDATION-PROCESS.md#5.12.1", "research/findings/DISCOVERY-raw-triggers-to-canon.md", "output/london_obk_depth.md", "output/london_W_scrutiny.md"]
---

# `W` is displacement geometry, not wall detection — I described it wrong

§5.12.15 (v2, ratified 2026-08-05) requires that what a feature *actually computes* be
verified against what its name and prose claim, by recomputing from raw and cross-tabbing
the edge cases, **before any verdict cites it**. The rule exists because *"the canon's
entire depth story was mis-described in every repo prose for months."*

I reproduced that mis-description. Both London candidate files described `W` as
**"no wall behind"** and attached a liquidity story: *"thin overnight liquidity means a
wall behind you is where price returns to and through."* That is wrong.

## The audit, run on my own data

300 `A/S1` trades with book state, 300 sampled and recomputed from the raw MBP-10
snapshots rather than from the cached column.

| | entry inside the visible ladder | entry **beyond** it |
|---|---:|---:|
| `W = 0` | 138 | 87 |
| `W = 1` | 3 | **72** |

- **`W=1` ⇒ the entry sits outside the entire visible ladder 96.0% of the time.**
  `W=0` ⇒ only 38.7%.
- Median visible ladder span: **5.50 points** — matching the v2 finding that MBP-10
  spans ~5pts total.
- Median distance beyond the ladder when `W=1`: **3.62 points.**

## What it actually means

`W=1` does not mean *"there is no large resting order behind the trade."* It means
**the entry price is roughly 3.6 points beyond where the visible book reaches at all.**
The book has not caught up to price. That is **displacement measured against visible
liquidity** — v2's words — and it is a different mechanism from the one I told.

It also explains, mechanically, the thin/not-thin split I reported earlier from the
other end: `F1`, `F2` and `B/S1` enter *inside* the book (fail-bar or trigger-candle
close), so they are essentially never beyond the ladder and `W` is degenerate there.
`A/S1` enters at a trigger-candle extreme via a resting stop order — the one arm that
routinely gets filled where the ladder no longer reaches.

## Does this change the verdict? No.

**The kill stands.** `W` failed its selection-corrected permutation null at family-wise
p = 0.42, and a permutation null shuffles labels — it is entirely indifferent to what the
label *means*. Correcting the semantics corrects the story, not the statistics.

I am explicitly **not** reopening on this. A better mechanism story for a result that
failed its own null is exactly the kind of rescue §5.12.12 (adversarial refutation) and
§6.0.1 exist to refuse.

## Two further §5.12.15 flags on my own depth pass

1. **I used absolute thresholds.** `WALLSZ >= 7` contracts and `WALLFAR >= 2.75` points
   were inherited from the canon and used unchanged. v2 states absolute thresholds are
   *"regime-sensitive by construction (book thickness shifted 1.45× within fit); prefer
   quantile/relative thresholds, or measure the sensitivity explicitly."* I did neither.
   Recorded as a limitation of that run; it does not change the kill, since those checks
   were not the survivor.
2. **Basis stamp (§5.12.13).** Every London depth conclusion above was computed on:
   1,168 trades carrying book state, `data/reference/depth_london` (295 days, decimal
   scale, verified), entries at the L1 geometry (2R target, uncapped stops), $160-risk
   sizing, 1pt/2pt costs. Any change to that basis reopens the conclusions.

## One forward-looking note, clearly not a rescue

If the real object is *displacement beyond visible liquidity*, then it is worth
separating from the thing I already tested and killed. At L1 I ran **"minimum
displacement ≥ 0.10 × pre-open range"** and it made every arm worse in every era. That
normalises displacement by the **day's range**. `W` normalises it by **how far the book
currently reaches** — a different and much shorter yardstick (~5 points, and it moves
with book thickness).

Those are two different variables that share a word. The second has never been tested on
London in a bar-only form, and a bar-only form is the only version that could reach the
sealed holdout. **That is a candidate for a future prereg, not a claim, and not a reason
to reopen this family.**

## Decoder check — clean

The v2 audit also caught a dual price-scale bug in `scripts/depth_walls.py` (the NY
archive), where a blanket 1e-9 decode corrupted wall distances on 52.5% of rows. Their
note says no verdict was contaminated because their consumers read only size-based
ratios. **Mine reads distances**, so I checked directly: all **295 of 295** files in
`data/reference/depth_london/` are decimal scale, and `scripts/london_depth.load_day`
reads them raw with no decode. **Not contaminated.**
