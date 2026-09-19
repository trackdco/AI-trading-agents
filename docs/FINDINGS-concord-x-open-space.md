# FINDINGS — CONCORD≥7 × OPEN-SPACE, the conditional trail, and the open items

2026-08-07. Fit-only, report-only, no holdout contact. New York untouched.

## 1 — HOLDOUT LOOK #1 CLAIM LIST, as it stands

Printed verbatim in the reply. Five registered claims, Bonferroni ×5, two
blocks both of which must pass:

| # | claim | population |
|---|---|---|
| H1 | LONDON base rate | London window book, unselected |
| H2 | NY_PRE base rate | NY_PRE book, unselected |
| H3 | NY_AM base rate | NY_AM book, unselected |
| H4 | sweep_b LONDON base rate | London sweep_b component alone |
| H5 | closeloc cut (queued since D1) | reject-arm first-of-fight book |

**Nothing has touched the sealed data. The list is unchanged.**

> ### A CONFLICT I INTRODUCED AND SHOULD HAVE CAUGHT
>
> I said twice that open-space "joins holdout look #1's claim list".
> **R0 of that declaration forbids it**: *"No selection layer goes to the
> holdout — not S1, not CONCORD, not a depth cut."* H5 is a single
> grandfathered exception, carried because it was queued before the
> per-session work.
>
> Open-space is a **bar-only geometric selection on the trigger
> population**. Adding it to look #1 either requires **amending R0** — a
> decision, not a detail — or requires arguing it is a *population
> definition* rather than a selection layer, which is exactly the kind of
> re-labelling R0 exists to prevent.
>
> **Recorded as an open decision, not resolved here.** Nothing has been
> added to the list.

## 2 — CONCORD≥7 × OPEN-SPACE: the conjunction is not worth taking

### 2a Redundancy, checked first

| TF | P(open) | P(open \| CC≥7) | φ | |
|---|---|---|---|---|
| 3m | 5.8% | 9.3% | **+0.149** | independent enough to stack |
| 5m | 7.0% | 9.9% | **+0.107** | independent enough to stack |

Mildly positively associated — high-concordance bars are somewhat more
likely to be heading into open space — but nowhere near collinear. The two
conditions really are different questions. Checked, not assumed.

### 2b The four cells

| TF | cell | n | /day | EV | day-boot 95% |
|---|---|---|---|---|---|
| 3m | **CC≥7 AND open** | 69 | 0.24 | **+1.507** | [+0.889,+2.189] ✓ |
| 3m | CC≥7 only (level ahead) | 670 | 2.29 | +0.029 | [−0.122,+0.182] |
| 3m | **open only (CC<7)** | 18 | 0.06 | **+1.562** | [+0.182,+3.020] ✓ |
| 3m | neither | 741 | 2.54 | −0.044 | [−0.182,+0.094] |
| 3m | *open-space, all CC* | 87 | 0.30 | **+1.518** | [+0.925,+2.088] ✓ |
| 5m | **CC≥7 AND open** | 68 | 0.23 | **+1.469** | [+0.998,+1.934] ✓ |
| 5m | **open only (CC<7)** | 32 | 0.11 | **+1.179** | [+0.129,+2.122] ✓ |
| 5m | *open-space, all CC* | 100 | 0.34 | **+1.376** | [+0.885,+1.837] ✓ |

**The conjunction does not beat open-space alone.** At 3m it is *worse*
(+1.507 vs +1.518) while discarding 21% of the trades. At 5m it is +0.093
better while discarding 32%.

**And the decisive cell is `open only (CC<7)`:** +1.562 at 3m and +1.179 at
5m, **both clearing zero**. The trades CONCORD would have thrown away are
just as good. That is BR-19's failure mode arriving for the third time —
*the worst flow bin is still profitable, so there is nothing to gate.*

CONCORD≥7 on its own, on this population, is +0.167 (3m) and +0.112 (5m)
and **neither clears zero**. BR-26's London CONCORD result was measured on
the incumbent 15m population; it does not transfer to the LTF reject
stream.

Split-half on the conjunction confirms (3m +1.812/+1.243, 5m
+1.810/+1.085) — but so does open-space alone, on more rows.

### 2c The account lab settles it

| book | /day added | R/day | worst | max size | SIM grad | LIVE $/yr |
|---|---|---|---|---|---|---|
| incumbent alone | — | 0.813 | −5.41 | $350 | 98.5% | $28,501 |
| **+ open-space 3m** | 0.30 | **1.265** | −5.41 | **$350** | 99.9% | **$34,922** |
| + CC≥7 AND open 3m | 0.24 | 1.169 | −5.41 | $350 | 99.9% | $33,249 |
| **+ open-space 5m** | 0.34 | **1.284** | −5.41 | **$350** | **100.0%** | **$37,820** |
| + CC≥7 AND open 5m | 0.23 | 1.155 | −5.41 | $350 | 99.9% | $36,308 |

**Open-space alone beats the conjunction on every axis at both
timeframes.** Blended EV agrees: 3m +0.492 vs +0.466, 5m +0.491 vs +0.461.

**Verdict: do not stack CONCORD onto open-space.** It costs 21–32% of an
already-thin stream and buys nothing that survives.

## 3 — THE CONDITIONAL TRAIL, tested as one rule

15m trail when there is no level ahead; the trigger's own timeframe when
there is. Evaluated on the room-gated population (V2 was only walked there).

| pop | n | all-V1 | all-V2 | **conditional** | 95% | vs best fixed |
|---|---|---|---|---|---|---|
| room 3m | 334 | +0.546 | +0.555 | **+0.607** | [+0.329,+0.876] | **+0.052** |
| room 5m | 308 | +0.411 | +0.462 | **+0.468** | [+0.182,+0.772] | +0.006 |

**The conditional rule beats both fixed policies on both timeframes**, and
its CI clears zero on both. The gain is real but modest at 3m and marginal
at 5m — it is the rule the mechanism implies (BR-58), and the data does not
contradict it.

In the account lab it produces the **highest R/day of any 3m
configuration**: inc + bundled 3m with the conditional trail gives R/day
**1.507** and LIVE **$36,607** — but at **$250** max size against
open-space's $350, because it carries the weak arm's worse days.

## 4 — THE TWO OPEN ITEMS

### 4a The ≥3R-only arm, on its own — it is the part that costs size

| addition | stream EV | R/day | worst | max size | SIM grad | LIVE $/yr |
|---|---|---|---|---|---|---|
| open-space 3m | **+1.518** ✓ | 1.265 | −5.41 | $350 | 99.9% | $34,922 |
| **≥3R-only 3m** | +0.203 (CI spans 0) | 0.985 | −6.88 | **$250** | 98.1% | **$28,196** |
| bundled 3m | +0.546 | 1.437 | −6.88 | $250 | 100.0% | $35,599 |
| open-space 5m | **+1.376** ✓ | 1.284 | −5.41 | $350 | 100.0% | $37,820 |
| **≥3R-only 5m** | **−0.053** | **0.775** | −6.74 | **$250** | 90.1% | **$21,424** |
| bundled 5m | +0.411 | 1.247 | −6.74 | $250 | 99.7% | $32,691 |

**Adding the ≥3R-only arm to the incumbent makes the account worse than the
incumbent alone at 5m** — R/day 0.775 against 0.813, live $21,424 against
$28,501 — and is roughly neutral at 3m ($28,196 vs $28,501).

**It is also exactly what costs the bundled book its size.** Worst day
−5.41 → −6.88 and max size $350 → $250 come entirely from this arm; the
open-space arm changes neither.

So the bundled gate is: one arm that is worth +1.4R and free, bolted to one
arm that is worth ~0 and costs $100 of position size. Splitting them was
the right call and the numbers now say so directly.

### 4b Open-space 3m-vs-5m redundancy, measured fresh

**45.0%** (45 of 100), against the bundled population's 41.9%. **Similar —
this one does carry over.** Worth noting the contrast: concurrency did
*not* carry (37.9% vs 22.2%), redundancy does. Both were checked rather
than assumed; only one needed to be.

A cross-timeframe union of the two open-space streams therefore still needs
a declared dedup rule, exactly as before.

## 5 — TWO DEFECTS FOUND IN THIS RUN, both in my own code

1. **`boot_mean` used `.agg(["sum","size"])`.** `size` counts NaN rows,
   `count` does not, so a column with NaNs got a bootstrap mean deflated to
   sum/size. It surfaced as point estimates falling *outside* their own
   CIs. **Blast radius checked: every prior call passed an all-non-null
   column** (`out_ship` on filtered books, zero NaNs verified), so no
   published number moves. Helper fixed to `count`.
2. **Merge keys were missing `locus`.** `(sess_day, t, side)` carries **up
   to 4 rows** on this population — the same minute triggers at several loci
   — so a three-key merge silently duplicated rows. It inflated the first
   account lab to 1.22 trades/day for a 0.30/day stream and produced worst
   days of −45R. Fixed by adding `locus` to every key, plus **row-count
   assertions on both merges** so a future silent duplication fails loudly.

Both were caught by internal-consistency checks rather than by inspection —
the CI containment check and the sanity that a −1R-capped exit cannot
produce a −45R day. **Every number in this document is post-fix**, and the
corrected open-space and bundled figures reproduce the previously published
values exactly (+1.518 / +1.376 / +0.546 / +0.411), which is the
calibration that the frame is now right.

## WHAT THIS LEAVES

The best-scoring configuration measured so far is **incumbent + open-space
5m**: R/day 1.284, worst day unchanged at −5.41, max size unchanged at
$350, graduation 100.0%, live $37,820 — **+33% on the incumbent alone, for
0.34 extra trades a day and no cost in size.**

Nothing is adopted. The open decision is whether open-space can enter
holdout look #1 at all given R0, and that is a call about the declaration,
not about the data.
