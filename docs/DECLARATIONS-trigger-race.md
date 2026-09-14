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


---

# AMENDMENT 1 — EPISODE-BASED M1 STATE (declared 2026-08-08, before the run)

Motivated by BR-88 (T3): displacement-at-open demands the displacement
persist into the entry candle, structurally excluding fast reclaims. This
amendment declares the candidate replacement EXPLICITLY and compares —
**nothing replaces anything in the comparison step.**

## THE NEW M1 STATE (candidate)

A per-minute episode machine on 1m bars against the 15m MA (as-of
values, same causality as everything else):

- A **touch minute** — the bar's range contains the current 15m MA —
  ends any episode and disarms M1 at that minute (including a would-be
  trigger minute: price already reached the target, no trade left).
- Otherwise the bar lies entirely on one side of the MA; that side's
  episode continues (or begins fresh on a side flip), tracking the
  **running maximum excursion of the bar extreme beyond the MA**,
  denominated in that minute's W15 at the time of the excursion.
- M1 is **ARMED toward the MA** once the running max reaches **0.5W —
  the floor is UNCHANGED** — and stays armed until the episode ends.

Everything else is untouched: trigger = first close through own BB MA
across the admissible race, affirmation menu/zone, the ≥2 gate for the
1m, priority M1 > M2 > M3, windows, 0.10W tolerance. The trigger
candle's open displacement stays recorded as data.

## COMPARISON PROTOCOL

Full census at the declared 0.10W under BOTH definitions, per window ×
mechanism fights/day side by side, raw-row provenance of the episode-M1
population (was each row M1 / M2 / M3 / absent under the open
definition), flatten probe on the episode variant before anything is
read. Fit-only, counts only.

**"Meaningfully changes," declared now so the rerun decision is not
post-hoc:** M1 fights/day moves ≥25% in any window, OR total fights/day
moves ≥10%, OR ≥10% of raw rows change mechanism. If met → the outcome
pass is re-run against the corrected census (because the population
changed); if not → the existing outcome pass stands.

## DECLARED EXPECTATIONS

The M1 population grows materially (episode arming spans the whole
reclaim, not one candle's open). **T3's 09:03 1m closure is predicted
CAUGHT** (episode max −0.56W ≥ floor, no MA touch before entry,
n_aff=2 → 1m admissible). If it is not caught, that is a miss recorded
as a miss.


---

# AMENDMENT 2 — NO-LOOKAHEAD EARLY-ENTRY CONSTRUCTION (declared 2026-08-08, before the build)

**Motivation, stated on the corrected record**: BR-92's mechanical
decomposition — the cost of waiting for the trigger candle to complete
is positive in all nine cells and monotone in candle length (1m +0.018
/ 2m +0.186 / 3m +0.335) — measured under favorable accounting
(final-candle stop, infeasible-fill drops). This construction prices
the REAL version. It does NOT rest on the withdrawn "his fills are
earlier" claim (BR-95): the trader's documented fills are the closure
trades themselves.

## THE CONSTRUCTION

At each 1m close (decision minute j, entry next 1m open — the standing
entry law), for each TF in the admissible race set {1m, 2m, 3m}:

- **Developing state only**: the TF's developing BB(20) MA as-of minute
  j; the TF bucket containing j, with its open price (known at bucket
  start) and its extreme SO FAR through minute j.
- **Trigger**: the bucket opened on the far side of the current
  developing MA (d·(bucket_open − MA_j) ≤ 0) AND minute j's close is
  through it (d·(close_j − MA_j) > 0) — the first such minute per
  bucket fires. For tf=1 this is identical to the closure construction.
- **Stop**: the bucket's extreme SO FAR ± 1 tick — known at the
  decision minute. **No value from any later minute appears anywhere.**
- Thesis (episode M1 / M2 / M3), affirmation ≥1 for M2/M3, the
  ≥2-affirmation 1m gate, windows, 0.10W tolerance: all unchanged,
  evaluated at minute j.
- Race: earliest firing minute wins; simultaneous → smallest TF.
  First-of-fight clustering X=0.5W, ref = 15m MA, unchanged.
- Outcomes: same targets (M1 → 15m MA; M2/M3 → first/second menu
  structure beyond entry), same walks, costs, day-boot, cells.

## GATE, BEFORE ANYTHING IS READ

T1-flatten on the builder: flatten all bars after a sampled trigger's
decision minute; the trigger set at or before that minute — including
each trigger's ENTRY and STOP — must be unchanged. This is the
prove-it-cannot-see-the-future gate; a single moved stop fails it.

## DECLARED EXPECTATIONS

Fires earlier and MORE often than the closure census (unconfirmed
mid-candle crosses that later reverse now enter and pay for it — that
is the honest cost BR-92's accounting hid). The interesting number is
how much of the +0.161 upper bound survives: report EV per cell vs the
closure census as the null, plus frequency. No declared bar — the
comparison is the deliverable. Report-only, fit-only, nothing adopted.
