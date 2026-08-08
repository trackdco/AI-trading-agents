# FINDINGS — TRIGGER RACE CENSUS (redeclared grammar), counts only

2026-08-08. Declaration: `docs/DECLARATIONS-trigger-race.md`, committed
before the run (`ed7c435b`). **Counts only — no outcome was read anywhere
in this pass.** Integrity probe (flatten-future rebuild on sampled days):
**PASS, 10 probes, 0 bad.** Fit 2025-06-01..2026-07-31, 293 session-days;
note the bars end ~2026-07-14, so 2026-07 is a **10-day partial month**.

**The grammar under census** (five items confirmed verbatim by the
trader): thesis = 15m M1 displacement / M2 rejection episode / M3 break
episode; ≥1 affirming structure from {POC, VWAP mid, VWAP ±1, ±2, VAL,
VAH} within **0.10·W15 of the 15m MA** (width-relative — replaces the
flat 10pt) for M2/M3, M1 self-affirming; entry = **first close through
its own BB(20) MA across the {1m, 2m, 3m} race**, 1m admissible only at
≥2 affirmations; no band-pierce requirement; windows unchanged.

## THE HEADLINE COUNTS (declared 0.10W)

| window | M1/d | M2/d | M3/d | all/d |
|---|---|---|---|---|
| LONDON | 0.57 | 0.96 | 1.19 | **2.72** |
| NY_PRE | 0.39 | 0.83 | 0.86 | **2.08** |
| NY_AM | 1.05 | 0.90 | 0.86 | **2.81** |
| **TOTAL** | 2.01 | 2.69 | 2.91 | **7.60** |

First-of-fight at X=0.5W, one stream across TFs. The old (wrong-
conjunction, flat-10pt) census ran 1.68/day at 2m plus 1.22/day at 3m as
two separate books — the corrected grammar finds **~2.6× that combined
volume**, spread evenly across all three windows rather than starved in
London.

**The funnel** (per direction-minute, declared tol): LONDON M3 as the
example — 110.6 armed-min/day → 76.0 affirmed → 2.67 raw triggers → 1.19
fights. The affirmation requirement passes ~two-thirds of armed minutes
(the structures are usually near the zone); the binding filter is now the
own-MA closure itself, which is where the trader's grammar puts it.

## THE RACE'S INTERNAL STRUCTURE (all recorded data, nothing selected)

- **Winning TF**: the 1m wins ~35–40% of fights where the gate lets it
  run, the 2m wins the plurality overall, and the **3m almost never wins**
  (4–65 per cell) — mechanically sensible: in a race, the faster candle
  usually crosses first, so the 3m only wins when the 1m is gated out and
  the 2m didn't cross. The old census's "3m book" was largely an artifact
  of denying the faster TFs.
- **Affirmation count**: overwhelmingly 1 or 2; 3+ is rare (0–14 per
  cell). The **1m-admissible share (≥2 affirmations) runs 38–59%** by
  cell — the double-confirmation gate binds about half the time.
- **Which structures affirm** (fights basis): **POC 959, VWAP mid 916**,
  then p1 444, VAH 345, VAL 261, m1 199. The trader's Jun-3 example
  (15m MA + POC) is the modal case in the census, not an outlier.

## TOLERANCE SWEEP — shape only, nothing picked

| tol (·W15) | LONDON | NY_PRE | NY_AM | TOTAL/d |
|---|---|---|---|---|
| 0.05 | 1.58 | 1.23 | 1.76 | 4.56 |
| **0.10** | **2.72** | **2.08** | **2.81** | **7.60** |
| 0.15 | 3.97 | 3.10 | 4.14 | 11.20 |
| 0.20 | 4.73 | 3.84 | 4.91 | 13.48 |

Monotone and smooth — no cliff at the declared value. Frequency is no
longer the scarce resource it was under the old construction; whether the
wider zones dilute quality is an OUTCOME question and was not looked at.

## THE DECAY IS REPAIRED — the flat-10pt collapse was the tolerance, not the market

- Old census (flat 10pt): raw triggers **2.36/day → 1.86/day** across the
  half-spans; July 2026 at ~1/5 of the 2025 monthly rate.
- Race census (0.10W): fights/day **7.97 → 7.24** across the same halves
  (−9%, vs −21%), and the monthly series *per trading day* is flat-to-
  rising across the whole span: raw 12.0–16.7/day through 2025, and
  **2026-07 — the month the flat tolerance starved hardest — is the
  highest in the series at 18.9 raw/day** over its 10 data days. (The
  unnormalized "84 fights in July" in the run log is the partial month,
  not a collapse.)

This closes the loop on the BR-77/BR-81 confound flags: the late-span
starvation was an artifact of denominating a confluence zone in flat
points across a span where W15 doubled. Width-relative, the trigger
grammar is stationary in frequency.

## WHAT THIS PASS DOES NOT SAY

Nothing here is an edge claim — no EV, hit rate, or excursion was
computed. 7.6 fights/day is the **census population** of the grammar, not
a trade rate; the trader's own selectivity sits on top of it. Next steps
in order: (1) the 8 real NY trades checked against THIS construction and
the old one, each miss recorded at its kill stage — pending the remaining
screenshots; (2) only after that, outcome scoring under a declared plan.

Standing: fit-only, no holdout (none exists for this family), counts
only, nothing adopted.
