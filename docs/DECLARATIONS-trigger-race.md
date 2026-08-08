# DECLARATION — TRIGGER RACE CENSUS (redeclared confluence grammar)

2026-08-08, written BEFORE the run. Counts only — no outcome is read
anywhere in this census. Fit period 2025-06-01..2026-07-31, unchanged.

## WHY THE REDECLARATION

The first confluence census (BR-73..81) encoded the wrong conjunction: it
demanded the entry candle close through its own LTF MA AND through a VWAP
band at the same candle. The trader's actual grammar, established from his
real executed trades (2026-06-01..03 screenshots) and his own correction:

> "i dont ALWAYS need a vwap break at the same candle as bollinger band
> MA... if it rejected the 15 min, i just need one more thing affirming
> the trade and then bollinger band MA on closure on top to enter."
> "i was gonna take the first closure through whether it be the 1, 2,
> or 3."

Two build defects compounded the wrong conjunction (both published in the
addendum trail before this declaration):

1. **The band-pierce join stage** discarded ~58% of MA-cross-with-
   confluence candles (2m M2 funnel: 582 conf → 245 join).
2. **The 10pt tolerance is flat** and halved in width terms across the
   fit span (0.145W in Q1 → 0.069W in Q4; July 2026 ran 11 triggers vs
   ~50/month in 2025). BR-77's "tighter is better" and BR-81's 1.68/day
   are both confounded by this decay and are flagged as such.

## THE GRAMMAR (five items, each confirmed verbatim by the trader)

1. **Affirmation menu**: POC, VWAP mid, VWAP ±1, VWAP ±2, VAL, VAH
   (8 structures). ±3 excluded (never fired once in 293 days). No 60m MA,
   no prior-day levels. ("yep, on the money")
2. **Zone**: an affirming structure counts if it sits within
   **0.10 · W15 of the 15m BB MA** — anchor is the 15m MA, tolerance is
   width-relative. Declared value 0.10W (what the old 10pt equaled at
   the middle of the span); shape sweep at 0.05 / 0.15 / 0.20W reported
   alongside, nothing picked. ("yep")
3. **The 1m gate**: ≥2 affirming structures at the zone → the 1m joins
   the entry race; exactly 1 → 2m/3m only. ("yep thats good")
4. **Which theses require affirmation**: rejection (M2) and **break
   (M3)** require ≥1 affirming structure; displacement rebalance (M1) is
   self-affirming — no affirmation required to arm, count still recorded.
   ("a break")
5. **Windows unchanged**: LONDON 03:00–04:59, NY_PRE 08:00–09:29, NY_AM
   09:30–10:30 NY. ("10:30 is fine") — noting explicitly that the
   trader's real Jun-3 10:45 short falls outside NY_AM and will be a
   recorded census miss by window, accepted by his choice.

## MECHANICS

- **Theses** (HTF state, 15m frame, as previously built): M1 displacement
  ≥0.5·W15 beyond the 15m MA at the trigger candle's OPEN, firing back
  toward the MA; M2 rejection episode (reject grammar, live until a 15m
  close through the MA), firing away; M3 break episode (15m close through
  its own MA, live until the next cross), firing with the break.
- **Entry**: the FIRST candle to close through its OWN BB(20) MA in the
  trade direction across the admissible TF set {1m, 2m, 3m} — fresh cross
  (open on the far side, close through). The winning TF is RECORDED AS
  DATA on the row; simultaneous multi-TF closes collapse to one trigger
  (winner recorded as the smallest TF, ties flagged). No band-pierce
  requirement anywhere.
- **Affirmation count** is a per-minute state: how many menu structures
  sit within tol·W15 of the 15m MA. Which structures qualified is
  recorded per row.
- **Clustering**: first-of-fight at X=0.5W, fixed-ref, reference = the
  15m MA at the earlier trigger; grouped per (day, thesis, direction) —
  ONE stream across TFs, because the TFs are alternates in one race, not
  separate books.
- **Integrity probe** before anything is read: flatten-future rebuild on
  sampled days; triggers at or before the flatten point must be
  unchanged.

## WHAT GETS REPORTED

Per window × thesis at the declared 0.10W: armed-minutes/day,
affirmed-minutes/day, raw triggers/day, fights/day (the funnel); winning-
TF split; affirmation-count distribution; 1m-admissible share. Tolerance
sweep for shape only. Half-span and monthly counts at the declared
tolerance — the width-relative restatement should flatten the decay the
flat 10pt produced; if it does not, that is reported as a miss.

## EXPECTATIONS (stated for the record, not bars — no outcome claims)

Frequency materially above the old census (join-stage removal alone
roughly doubles the M2/M3 candidate pool; width-relative tolerance
restores the strangled late span); the monthly series roughly flat where
the old one collapsed. The trader's real trades get checked against this
construction when the full screenshot set arrives — misses recorded as
misses.

Standing: fit-only, no holdout (none exists for this family), counts
only, nothing adopted, nothing scored.
