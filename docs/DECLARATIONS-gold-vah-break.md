# DECLARATIONS — replication test for `vah · break` on gold

Declared **before** any replication compute. Nothing in this file was written after
seeing a number it constrains. The GC census that produced the candidate is in
`docs/FINDINGS-gold-level-census.md`.

## D0 — Why this is a replication and not a holdout

A holdout is not available and pretending otherwise would be the failure this file
exists to prevent. **The GC census ran on the whole sample, 2023-01 → 2026-08, and both
era halves were read** (H1 +0.147, H2 +0.149). Any split carved out of GC now is a split
I have already seen. Sealing it would be theatre.

What is genuinely unseen is **other instruments**. Nothing in this repo has run this
census on anything but NQ and GC, and I have computed nothing on the three candidates
below. So the test is replication across instruments rather than across time, and it is
declared as such.

## D1 — The candidate, restated so it cannot drift

`vah · break` — developing session value-area high, break arm — first trigger per
structural fight, shipped exit, 0.5-point risk floor equivalent, cost 0.20 points.
On GC: **+0.148R** [+0.099, +0.197], 4.6 fights/day, n=3,972, both eras clear.

## D2 — Instruments, scoped and closed

| # | instrument | role | status |
|---|---|---|---|
| 1 | **XAUUSD spot** (Dukascopy) | REPLICATION — same underlying, different venue, different tape | downloading |
| 2 | **6J** (CME yen) | GENERALITY CONTROL — not a metal | in repo, uncomputed |
| 3 | **DX** (ICE dollar index) | GENERALITY CONTROL — not a metal | in repo, uncomputed |

A fourth instrument requires its own declaration. Silver was considered and is
**excluded** for now: it would be a second metal and therefore a second replication, and
adding it after seeing result 1 would be a search.

## D3 — Predictions, stated now

**Replication (XAUUSD spot).** `vah · break` EV > 0 with a day-clustered 95% interval
clear of zero, and ranked in the top four of the fourteen locus × arm cells.
- Passes → the GC result survives a change of venue and tape. It becomes a candidate
  worth a size and graduation analysis.
- Fails → the GC result is most likely fit-side. It is reported as refuted and the gold
  track returns to the census rather than to this cell.

**Generality controls (6J, DX).** No directional prediction — this is diagnostic, and the
reading is declared now so it cannot be chosen later:
- Negative or null on both → the effect is metal-specific. Strongest outcome for the
  candidate.
- Positive on both → it is a generic level-break effect, not a gold finding. **This does
  not refute it**, but it reclassifies it: the interesting object becomes the census
  construction itself, and the honest next question is whether `vah · break` is
  measuring anything beyond "price that breaks a developing profile edge keeps going."
- Positive on one → inconclusive, report and stop.

## D4 — Control gate, before any locus is read

On each new instrument the harness must first produce a sane book, or nothing is
reported and the harness is fixed:
- median |R| between 0.5 and 2.0 after the risk floor
- 99.99th percentile |R| below 100 (GC's was 15; the unfloored GC book had three rows at
  10¹¹, which is the failure this gate catches)
- fights/day within 20–200

The risk floor is set **per instrument** as the smallest value that satisfies the gate,
chosen from the same fixed ladder used on GC — 0.2 / 0.3 / 0.5 / 1.0 / 2.0 in tick-scaled
units — and reported. It is not tuned to a result, and the full ladder is published for
every instrument regardless.

## D5 — Publication rule

**All fourteen locus × arm cells are reported for every instrument**, with n, EV,
day-clustered interval and both era halves. No cell is omitted, and the candidate is not
promoted above the others in the tables. If `vah · break` fails, this file is updated
with the failure and the finding is marked refuted rather than quietly dropped.

## D6 — What would still be unproven if everything passes

Cost is assumed, not measured, on every instrument. Room-to-run (BR-32/35) is untested.
No size, no payout cap, no graduation — BR-39 records that frequency beats EV under a
cap, so 4.6 fights/day at +0.148R may still lose to a busier, thinner book. A passing
replication makes this a candidate, not a strategy.
