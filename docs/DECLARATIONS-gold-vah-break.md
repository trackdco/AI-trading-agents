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

---

## D7 — Amendment, declared before the XAUUSD compute

Recorded while the 6J and DX controls were running and **before any XAUUSD number
existed**, because it changes how a failure must be read.

**The candidate locus is built from volume, and the replication venue does not have
real volume.** VAH is the developing session value-area high, derived from a volume
profile. On GC that profile is built from exchange-traded contract volume. On Dukascopy
XAUUSD it would be built from that broker's own tick volume — a liquidity proxy, not a
consolidated tape, and spot gold has no central volume at all.

Consequences, fixed now:

- **A PASS is still a pass**, and arguably a strong one: if the effect survives a
  profile built on a different and noisier volume proxy, it is not an artifact of GC's
  particular tape.
- **A FAIL is ambiguous and must be reported as such.** It cannot distinguish "the
  effect is not real" from "the value area cannot be located without real volume." It
  therefore does **not** trigger the D3 refutation on its own.
- To break that ambiguity a fail must be followed by one further check, declared now so
  it is not invented later: re-run the replication on the **non-volume loci only**
  (bbma15, vwap, vwap_m1, vwap_p1), which need no profile. If those reproduce their GC
  ordering and only the profile loci break, the volume proxy is the likely cause. If
  the non-volume loci also scramble, the GC census is the problem.

This weakens the XAUUSD test relative to what D2 implied. The clean replication for a
volume-derived locus would be another **exchange-traded** metal — silver futures — which
D2 excluded and which this repo has no data for. That limitation stands on the record
rather than being worked around.

---

## D8 — RESULTS

Run after the profile bin was corrected to 4×tick (the 1.0-price-unit default produced
zero profile fights on 6J and a 4× shortfall on DX, so the first control pass never
tested the candidate at all). All three instruments pass the D4 gate at the 2-tick floor
and all seven loci are present on all three.

### GC — the candidate holds

`vah · break` **+0.111R** [+0.064, +0.158], H1 +0.092 / H2 +0.131, **the only cell of
fourteen clearing both eras**. At the previous bin and the same floor it was +0.113, so
**the bin was not driving it**. The earlier +0.148 headline was the 0.5-point floor, not
the binning; at the gate-selected 0.2 floor the honest number is **+0.111**.

### The controls — and the reading D3 did not anticipate

Both controls are negative in every cell. Taken at face value that is D3's "negative on
both → metal-specific, strongest outcome for the candidate."

**That reading is wrong, and the check that shows it is the cost decomposition:**

| | median risk | cost charged | EV after cost | **EV before cost** |
|---|---|---|---|---|
| GC | 1.96 pts | 0.149R | +0.000 | **+0.149** |
| DX | 0.040 | 0.308R | −0.164 | **+0.144** |
| 6J | 3.35e-06 | 0.353R | −0.231 | **+0.122** |

**Before cost the three books are the same book.** The controls are negative because a
two-tick assumption eats twice as much of their R — their stops are far smaller relative
to their tick — not because the effect is absent. And `vah · break` is the **top-ranked
cell on all three instruments**: 1st of 14 on GC, 3rd on DX, 1st on 6J.

### Verdict, taken against the declaration rather than around it

**`vah · break` is NOT metal-specific.** It is a generic level-break effect, present on
the yen and the dollar index at the same pre-cost magnitude as on gold. What is
gold-specific is that GC's stops are large enough relative to its tick for the effect to
survive friction.

D3's branches do not cleanly cover this outcome — they assumed the controls would be
positive or negative *on comparable terms*, and they were not. The conservative branch is
taken: this **reclassifies** the finding rather than refuting it, exactly as D3 says a
"positive on both" result should. The interesting object is no longer "gold's value area"
but "a level-break book whose viability is decided by tick geometry."

### What this promotes to the top of the queue

Cost is now the single load-bearing assumption in the entire result. GC at +0.111R is
carrying an **assumed** 0.20-point round turn against a measured book EV of +0.149R
before cost — so the whole edge is the difference between two numbers, one of which was
never measured. If GC's true round turn is 0.10 the candidate roughly doubles; if it is
0.30 the candidate is gone.

**Measuring GC's actual round-turn cost is now worth more than any further census.**
