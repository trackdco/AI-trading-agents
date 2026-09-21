# DECLARATION — SWEEP-RECLAIM AS A LOCUS (item 6), declared BLIND

Written 2026-08-07 BEFORE any sweep-reclaim number exists. E3's earlier
attempt is void as a test of this concept: its 8-bar-swing definition
failed to capture the trader's own reference example (the 3 Jun London
pair), so it tested a strawman. That was a SPECIFICATION failure,
established outcome-independently — the reference extreme was simply never
penetrated — and no result from it constrains what follows.

**The definition below comes from the trader's own words in the setup
walkthrough:** *"price took out the low my own stop was sitting under, then
reclaimed."* The reference extreme is therefore **the trader's own stop
level**, not an abstract swing window. That is the correction.

This is censused as its own trigger population — like VAL and VWAP−1 — and
NOT bolted onto an existing book. Cell (a) exists precisely so the concept
has a standalone base rate that avoids the re-entry dilution arithmetic
(Law 7, E3) entirely.

## The two cells

**Cell (a) — STANDALONE sweep-and-reclaim. No prior attempt required.**

The reference extreme is a **swing low/high**: the lowest low (highest
high) of the **8 completed 15m bars** preceding the candidate bar,
excluding the candidate bar itself.

- SWEEP: the candidate 15m bar's low trades **≥ 4 ticks (1.00 pt) below**
  the reference low (mirror for highs).
- RECLAIM: that same bar **closes back above** the reference low.
- Trigger fires at that bar's close. Direction = long for a low sweep,
  short for a high sweep.

Both conditions on ONE bar — a sweep-and-reclaim candle. This is the
cleanest standalone reading and is deliberately stricter than E3's
three-bar reclaim window.

**Cell (b) — the trader's exact case: sweep of the OWN STOP, after a
stopped attempt.**

- A prior attempt at any of the seven censused loci was entered and
  **stopped out**.
- A later 15m bar trades **≥ 4 ticks beyond that attempt's own stop
  price** (the low the stop was sitting under, for a long-side reclaim).
- A completed 15m bar **closes back inside** that stop price within
  **3 bars** of the penetration.
- Trigger fires at that reclaim bar's close, in the SAME direction as the
  stopped attempt.

The pair answers the question the concept poses: **does the prior attempt
matter at all, or is sweep-and-reclaim a standalone edge?**

## Shared machinery (identical to E1 — this is a locus, not a new pipeline)

Entry at the NEXT 1m open. Stop at the trigger candle's extreme ± 1 tick.
Shipped exit (75% at 3R, remainder trailed on 15m structure). W = 15m BB
width. Trigger timeframe 15m. Structural fights at X = 0.5W declared, with
the full X ∈ {0.25, 0.5, 1.0, 2.0}W sensitivity reported. Day-level
bootstrap, seed 20260807. Fit rows only; sealed written unread.

**The entry-price gate must PASS on the sweep builder before any row is
read**, exactly as it did for the seven loci.

## Parameters, pinned and never swept

Lookback 8 bars (cell a) · penetration 4 ticks (both cells) · reclaim
window 1 bar (cell a) / 3 bars (cell b). These are fixed now. If they are
wrong the cells fail as declared and are recorded as misses; a
redefinition requires a fresh blind declaration justified from the
trading, not from a result.

## Bar for follow-up — identical to E1.4, no easier

EV > 0 with day-boot CI clear of zero in BOTH eras at X = 0.5W, AND sign
positive at ≥ 3 of the four X values. Anything less is published as a base
rate and parked.

## Publication rule

Both cells are published whether positive or null, into BASE-RATES.md, on
the same footing as every other locus. A null here is a genuine result: it
would close the sweep concept that has been open since A2.

## Declared in advance: the interpretation of each outcome

- **(a) passes, (b) passes:** sweep-and-reclaim is a real trigger
  population; the prior attempt is incidental. Census (a) is the object.
- **(a) fails, (b) passes:** the prior stopped attempt is load-bearing —
  the edge is in the re-entry context, not the pattern.
- **(a) passes, (b) fails:** the pattern works but the post-stop context
  degrades it (consistent with A2's −0.22R re-entry finding).
- **both fail:** the sweep concept is closed, and A2's re-entry null
  stands as the final word on it.
