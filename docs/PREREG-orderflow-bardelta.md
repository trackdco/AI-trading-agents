# PRE-REGISTRATION — order-flow filter on the 20-SMA pin bar (Stage 3)

Written 2026-09-07 after an exploratory pass on 148 trades (3-min SIDE, 2023-26,
footprint-covered days only). That pass is EXPLORATORY and is not evidence. What
follows is the one hypothesis it produced, declared before testing it anywhere else.

## What the exploratory pass showed
- 128 of 148 pin bars (86%) do show negative delta inside the rejected wick.
  Pat's mechanism is REAL as a description: sellers genuinely aggress into the
  hammer's wick and fail.
- But wick delta does NOT separate winners from losers: correlation with R is
  -0.041, and the 20 bars without wick aggression scored no worse.
- The one feature that did separate: delta over the WHOLE BAR.
    bar delta against the trade  +0.165 R  (n=48, win 22.9%)
    bar delta with the trade     -0.064 R  (n=100, win 19.0%)

## The hypothesis, stated once
**H1.** A pin bar whose NET delta over the whole bar still ran against the trade
scores better than one where net delta ran with it. Reading: the trade needs the
aggressive side to have been in control and still failed to close the bar their
way. Flow "with us" on the signal bar means the move already happened and we are
late.

## How it will be tested (declared before running)
- Out-of-sample surfaces: the 1-min SIDE book, the 3-min SLOPE book, the 1-min
  NONE book, and the 2020-22 tape where footprint days exist.
- Split on the SIGN of bar delta only. No threshold tuning, no re-picking the
  feature.
- Bar: H1 holds only if the negative-delta half beats the positive-delta half by
  > 0.10 R on a MAJORITY of those surfaces, with the sign consistent on every one.
- Multiple-comparison note: 6 features x 2 split styles = ~12 comparisons were made
  to find H1. A single confirmation is therefore weak evidence; consistency across
  independent surfaces is the only thing that counts.

## Prediction
- **P1** H1 will NOT replicate cleanly. The exploratory gap came from n=48 against
  n=100 on one surface, which is the size of gap 12 comparisons produce by chance.
- **P2** Wick delta will stay uninformative everywhere - the mechanism is real but
  it is present on nearly every pin, so it cannot discriminate.
