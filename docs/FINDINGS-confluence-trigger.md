# FINDINGS — CONFLUENCE TRIGGER, fresh build at 2m and 3m

2026-08-08. Report-only, fit-only, no holdout contact (the bar-only venue is
closed regardless). Day-clustered bootstrap (seed 20260807) from the start.
2m and 3m reported **separately, never pooled; overlap between them not
computed this pass**, as specified.

**Construction.** Trigger = a TF candle closes through its **own TF BB(20)
MA** in the required direction AND through whichever VWAP band (middle, ±1,
±2, ±3) is in **confluence** with that MA — tolerance **10.0 pts**, taken
from the confluence work's existing `cluster.tolerance_points` in
`config/strategy.yaml` (the value `src/engine/snapshot.py` reads), same at
both TFs, not re-tuned. Qualifying band **recorded as data**, never fixed.
POC **not required**; rows with POC also inside the stack are flagged.
Entry next 1m open; stop trigger-candle extreme ± 1 tick; levels
full-session, triggers inside the three trading windows. Entry gate (T1
flatten): **PASS** (11 probes, 0 bad, 9 moved).

**Multiplicity, stated up front:** 2 TF × 2 mechanisms × 2 directions = 8
cells, and M2 carries 3 targets per cell. ~32 scored numbers, **no declared
bar anywhere** — these are base rates, published nulls included. Nothing
below is a verdict.

## A SPEC DEFECT CAUGHT AT THE POPULATION STAGE, before any M1 outcome was read

The first build measured M1's displacement at the trigger candle's
**close** — which demands the market still be ≥0.5W displaced *after* the
reversal candle. The funnel (74 sampled days) showed that conjunction is
nearly a null set:

| stage | 2m | 3m |
|---|---|---|
| displaced ≥0.5W at candle close | 2,073 | 1,437 |
| …AND closes through own TF MA toward the 15m MA | **11** | **0** |

Same defect class as a D8 pathology — caught on counts, not outcomes (the
only M1 cells in that build printed THIN, no EV was read). Displacement is
now measured at the candle **open** — the state when the trigger candle
began, the faithful reading of "price displaced, trigger fires back." The
close-displacement value stays on every row as data.

## §1 — POPULATION, per timeframe

| | 2m | 3m |
|---|---|---|
| raw triggers | 350 | 242 |
| first-of-fight (X=0.5W) | 284 — **0.97/day** | 206 — **0.70/day** |
| qualifying band | vwap 58 · **p1 106 · m1 91** · p2 15 · m2 14 · **±3: 0** | vwap 69 · p1 75 · m1 54 · p2 5 · m2 3 · ±3: 0 |
| stack ≥2 bands | 10 of 284 | 11 of 206 |
| POC in confluence (flag) | 33.5% | 44.7% |

The trigger is **rare** — under 1/day at 2m across all three windows
combined. The band that qualifies is essentially always the middle or ±1;
**±3 never fires** and ±2 is marginal. The recorded-band column did its
job: had the definition been fixed at any single band in advance, most of
this population would not exist.

## §2 — M1 REBALANCE (first-passage to the 15m MA; same-bar → stop wins)

| TF | dir | n | /day | med dist | hit% | EV | day-boot 95% |
|---|---|---|---|---|---|---|---|
| 2m | long | 48 | 0.16 | 1.84R | 54.2% | +0.276 | [−0.118,+0.729] |
| 2m | short | 48 | 0.16 | 1.31R | 50.0% | +0.030 | [−0.394,+0.604] |
| 3m | long | 26 | 0.09 | **0.39R** | **92.3%** | **+0.419** | **[+0.095,+0.777] !** |
| 3m | short | 22 | 0.08 | 0.52R | 59.1% | **−0.279** | [−0.560,−0.020] ! |

Two cells "clear" — in opposite directions, on 26 and 22 rows,
uncorrected across ~32 numbers. **Read as base rates, not signals.** The
3m-long cell is a high-hit tiny-target scalp: the MA sits a median 0.39R
away, so 92% arrival buys small wins against full −1R stops. Its MFE table
says the same thing — p50 0.21R, P(≥2R) 3.8%: this trade does not run.

**The POC flag hurts M1, in every cell thick enough to split:**
2m-long +0.369 without the flag vs **−0.035 with it**; 3m-long +0.709 vs
+0.080. Direction is consistent, n is thin (11–14 flagged rows). Recorded
as a base rate: POC stacked on the trigger is, if anything, an
*obstacle marker* for the rebalance trade — coherent with the open-space
finding (BR-53) rather than with the confluence assumption.

## §2 — M2 CONTINUATION (no exit assumed; three targets side by side)

| TF | dir | n | target | med dist | hit% | EV | 95% |
|---|---|---|---|---|---|---|---|
| 2m | long | 101 | vwap_p1 | **−0.24R** | 65.3% | −0.172 | [−0.477,+0.245] |
| | | | vah | 0.65R | 49.5% | −0.209 | [−0.454,+0.073] |
| | | | vwap_p2 | 2.62R | 33.7% | −0.222 | [−0.478,+0.075] |
| 2m | short | 87 | vwap_m1 | −0.34R | 67.8% | **−0.300** | **[−0.452,−0.148]** |
| | | | val | 0.22R | 52.9% | **−0.280** | **[−0.459,−0.098]** |
| | | | vwap_m2 | 1.98R | 33.3% | −0.229 | [−0.483,+0.047] |
| 3m | long | 89 | vwap_p1 | −0.24R | 66.3% | −0.141 | [−0.388,+0.125] |
| | | | vah | 0.60R | 56.2% | −0.159 | [−0.398,+0.092] |
| | | | vwap_p2 | 1.89R | 38.2% | −0.131 | [−0.436,+0.229] |
| 3m | short | 69 | vwap_m1 | −0.14R | **79.7%** | +0.073 | [−0.246,+0.493] |
| | | | val | 0.27R | 71.0% | −0.045 | [−0.281,+0.198] |
| | | | vwap_m2 | 1.79R | 39.1% | +0.185 | [−0.281,+0.726] |

**M2 as a fixed-structural-target construction does not price positively
anywhere.** 10 of 12 target-cells are negative; 2m-short clears zero on the
*negative* side at two of its three targets. Which target the data supports:
**none as a full-close exit** — and the table shows why:

- **The first target is behind the entry.** Median distance to VWAP±1 is
  *negative* (−0.14 to −0.34R): the trigger candle just closed through the
  stack, so the nearest band is at or behind the fill. It "hits" 65–80% of
  the time and pays roughly nothing.
- **The far target (±2) sits ~2R away and arrives ~33–39%** — below the
  50%-at-2R breakeven line against a −1R stop, before cost.
- **The tail is where the population earns** — M2's MFE p90 runs 2.3–3.7R —
  and a fixed structural target truncates exactly that. This is BR-46/49's
  fixed-target lesson reproducing on a fresh population.

The dual currency reads the same: high hit rates, negative R. A
hit-rate-led reading of this table would repeat BR-20.

## §3 — BATTERY (remaining items)

**Clustering-X** — both populations and both mechanisms are nearly flat in
X (2m: 1.05 → 0.83/day across 0.25–2.0W; M1 EV +0.147/+0.153/+0.143/+0.128;
M2 t1-hit 67→62%). No convention sensitivity to speak of at this rarity —
the triggers are too far apart for clustering to matter.

**Cost** — M1 survives all three assumptions (2m: +0.153 → +0.128 → +0.103;
3m: +0.099 → +0.081 → +0.062). M2's first-target read is negative at every
cost level and worsens monotonically.

**Per-session (compact, no verdicts):** NY_AM carries the most flow at both
TFs (0.42/day at 2m) and the strongest M2 t1-hit (77.8%/82.4%); M1's
London cell at 3m is 5 trades — noise. No session verdicts drawn.

## WHAT THIS PASS SAYS

1. **The confluence trigger exists but is rare** — ~1/day at 2m, 0.7/day at
   3m, and the stack is nearly always the MA plus exactly one band (middle
   or ±1). ±2/±3 confluence is a near-empty set under the existing 10pt
   tolerance.
2. **M1 is the only faintly positive corner** (+0.10 to +0.15 pooled,
   cost-robust, X-robust) — but it is a sub-0.2/day, small-target
   population whose only "clearing" cells are 22–26 rows in opposite
   directions. Nothing here approaches the standing books.
3. **M2 with fixed structural targets is refuted as priced** — the
   geometry puts the first target behind the entry and the far target
   beyond the hit rate that would pay for it, while the exit style discards
   the tail the population actually has.
4. **The POC flag is, directionally, a negative marker for M1** — the
   opposite of the confluence intuition, on thin n. Recorded, not acted on.

Nothing is adopted. No holdout exists for any of this — the bar-only venue
is closed, so anything carried forward from this family validates on
forward data only.


---

# ADDENDUM 2026-08-08 — M2 target fix, and the tolerance sweep

## THE M2 TARGET FLAW, FIXED

The first pass applied a fixed target set uniformly, which put the "near"
target behind the entry whenever the fired band WAS that target. Targets are
now selected **relative to the band that fired the trigger**: fired =
VWAP-middle → near ∓1, far ∓2; fired = VWAP∓1 → near VAL/VAH, far ∓2; any
other fired band → the next two bands in the trade direction (recorded).
Same first-passage methodology, same-bar → stop wins.

**The geometry artifact is gone** — near-target median distance is now
+0.35R to +0.84R (previously −0.14 to −0.34R) — **and the verdict does not
change: M2 still does not price.**

| TF | dir | n | near: medD / hit / EV | far: medD / hit / EV |
|---|---|---|---|---|
| 2m | long | 101 | 0.84R / 48.5% / −0.234 [−0.473,+0.044] | 2.89R / 29.5% / −0.266 |
| 2m | short | 87 | 0.47R / 52.9% / **−0.263 [−0.442,−0.091]** | 2.14R / 28.0% / **−0.315 [−0.583,−0.049]** |
| 3m | long | 89 | 0.65R / 56.2% / −0.129 | 1.93R / 36.5% / −0.096 |
| 3m | short | 69 | 0.35R / 71.0% / −0.027 | 1.75R / 38.2% / +0.148 [−0.308,+0.702] |

So the first pass's *verdict* survives its own flaw; the *mechanism* stated
in BR-75 ("first target behind the entry") was an artifact of my fixed-set
construction and is corrected: **with honest targets, the population simply
does not continue far enough, often enough, to pay a −1R stop.** 7 of 8
target-cells negative; 2m-short clears zero on the negative side at both.

**The case split is the informative part:**

- **`band1` (fired through ±1 itself) is the bad case everywhere** — the
  majority case (55–74 of each cell), near target ~0.2–0.5R away, EV −0.14
  to −0.36. Price that just crossed the outer band is near exhaustion, not
  ignition.
- **`mid` (fired through the VWAP middle) is the only positive corner**:
  3m long +0.223 near / 3m short +0.168 near and **+0.566 far**, and it is
  the one cell where the far target out-earns the near one. n = 20–26 per
  cell, uncorrected among many — a base-rate observation, nothing more.

## THE TOLERANCE SWEEP — shape, not selection

10pt was imported from the confluence work and never checked against this
population. Swept at 10 / 15 / 20pt, everything else fixed:

| tol | TF | raw | fof/day | M1 EV | M2 near EV |
|---|---|---|---|---|---|
| **10** | 2m | 350 | 0.97 | **+0.153** | −0.247 |
| 15 | 2m | 408 | 1.12 | +0.105 | −0.184 |
| 20 | 2m | 439 | 1.20 | +0.087 | −0.183 |
| **10** | 3m | 242 | 0.70 | **+0.099** | −0.084 |
| 15 | 3m | 286 | 0.82 | +0.088 | −0.090 |
| 20 | 3m | 316 | 0.91 | +0.079 | −0.131 |

**The shape is monotone and answers the construction question:** widening
the tolerance buys ~25% more triggers and pays for them with monotonically
decaying M1 quality at both timeframes, while M2 stays negative throughout.
The thinness is real, not an artifact of a too-tight stack — **the tighter
stack is the better stack**, and the declared 10pt sits on the good side of
its own curve. Nothing is picked; the declared value stays declared.

Standing unchanged: fit-only, no holdout (none exists for this family),
nothing adopted.


---

# ADDENDUM 2 — 2026-08-08: the construction completed

M3 break added as its own third setup, M1 scored against both rebalance
targets, everything split by session, raw funnel counts alongside the
joined counts, and frequency restated at the end — all before anyone
touches the tolerance. Report-only, fit-only, no holdout contact.

**What was added.** (a) **M3 BREAK**: a 15m candle closing through its own
MA opens a break episode in the break direction, live until the next 15m
cross; the entry is the same 2m/3m confluence trigger, firing in the
break's direction; the break candle's oriented closeloc is recorded on
every row and the "high closeloc" threshold is **swept
{none, 0.5, 0.6, 0.7, 0.8} at report time, never fixed**. Scored against
the same band-relative near/far targets as M2. (b) **M1 dual targets**:
the 15m MA and the 1-hour MA, two separate first-passage races, side by
side, never pooled or averaged. (c) M2 unchanged (live episode,
band-relative targets). Mechanism priority M1 > M2 > M3 where HTF states
overlap; overlaps recorded as flags.

**The prior population is untouched by the addition** — M1/M2 counts are
identical to addendum 1 (2m: 96/188 raw; 3m: 48/158), so BR-73..77 stand
as published. M3 is purely additive on previously unclaimed candles.

**Multiplicity, stated up front:** ~120 scored numbers this pass
(6 session×dir cells × targets × mechanisms × 2 TFs, plus a 30-row
sweep), **no declared bar anywhere**. Base rates, published nulls
included. Nothing below is a verdict.

## §0 THE FUNNEL — where the raw population goes (2m shown; 3m same shape)

| mech | state-live candles | +through own MA | +confluence exists | +JOINED |
|---|---|---|---|---|
| M1 | 7,817 | 337 | 156 | **105** |
| M2 | 18,006 | 1,203 | 582 | **245** |
| M3 | 21,829 | 1,329 | 633 | **264** |

The dominant filter is the **own-MA cross** (~2–5% of state-live candles);
confluence then roughly halves it, and requiring the close through the
stacked band halves it again. The construction is thin because three
independent conditions are being intersected, not because any one of them
is rare. Per-session funnels are in the run log; the starkest cell is
**3m M1 London: 1,782 displaced candles → 14 crosses → 5 joins** — a
displaced London market at 3m almost never produces the reversal cross.

## FREQUENCY — restated with the construction complete (the asked-for table)

First-of-fight at X=0.5W, per session, all three mechanisms in:

| tf | session | M1/day | M2/day | M3/day | all/day |
|---|---|---|---|---|---|
| 2m | LONDON | 0.08 | 0.21 | 0.29 | **0.58** |
| 2m | NY_PRE | 0.05 | 0.22 | 0.16 | **0.42** |
| 2m | NY_AM | 0.20 | 0.22 | 0.26 | **0.68** |
| 2m | — total | 0.33 | 0.64 | 0.71 | **1.68** |
| 3m | LONDON | 0.02 | 0.18 | 0.22 | **0.42** |
| 3m | NY_PRE | 0.03 | 0.18 | 0.14 | **0.35** |
| 3m | NY_AM | 0.12 | 0.17 | 0.15 | **0.45** |
| 3m | — total | 0.17 | 0.53 | 0.44 | **1.22** |

The complete construction runs **1.68/day at 2m** (was 0.97 before M3) and
**1.22/day at 3m** — but the *analyzable cell* (session × mechanism ×
direction) runs 0.01–0.29/day, i.e. 2–86 fights over 293 days. That is
the honest denominator for the loosening conversation, which is now
decidable and is **not decided here**: the tolerance stays the declared
10pt, and addendum 1's sweep already showed widening it buys quantity by
selling quality at both TFs. If more frequency is wanted, the sweep says
the tolerance is the wrong lever to pull.

## M1 — both targets, side by side (never pooled, never averaged)

Pooled-cost view first (2m): **15m MA +0.153 vs 60m MA −0.071** — at 2m
the far target simply loses; arrival roughly halves (hit ~28% vs ~55%)
and the extra distance does not pay for it. Per session, the 15m target
is the better of the two in five of six 2m cells.

At 3m the sign flips (60m +0.337 vs 15m +0.099 pooled) — **and that
number should not be trusted, for a reason the row data exposes:** the
60m MA sits **at or behind the entry on 33% of 3m M1 rows** (11% at 2m).
Displacement is defined against the *15m* MA, so price can be displaced
beyond the 15m MA while still on the near side of the 60m MA — the
"target" is then behind the fill and the race is ill-posed. This is the
same geometry class as the M2 flaw fixed in addendum 1, caught here
before anything was concluded from it. On the well-posed subset (60m MA
genuinely ahead) the 3m read is +0.437 on 32 raw rows — NY_AM-long
dominated, thin, uncorrected. Recorded, nothing more.

**Session texture (2m, the thicker TF):** NY_AM carries the M1 flow
(60 of 96 fights) and prices near zero against the 15m MA (+0.055 long /
+0.155 short). London-long is the only cell whose 15m-target EV exceeds
+0.4, on 13 fights. Nothing clears a CI on the positive side anywhere.

## M2 — per session: the verdict does not move

All six 2m session×dir cells are negative at the near target (−0.09 to
−0.38); London-short clears zero on the negative side (near −0.380
[−0.686,−0.056], far −0.632 [−1.056,−0.135]), as do both NY_PRE far
targets. NY_AM remains the least bad (near −0.09/−0.15, far −0.03/+0.14)
— consistent with addendum 1's pooled read. At 3m, London-short and
NY_AM show faintly positive corners (+0.07 to +0.31), CIs all spanning
zero. **Nothing here revises BR-76: M2 does not price.**

## M3 — the new mechanism's base rates

**Frequency: M3 is the biggest of the three arms** (0.71/day at 2m) —
break episodes are common and long-lived, so the confluence trigger finds
more of them than of displacements or rejection cycles.

**Outcome base rates, per session (near/far as M2):**

- **2m London-long is the one CI-clearing cell in the whole table, and it
  clears NEGATIVE at both targets**: near −0.454 [−0.698,−0.188], far
  −0.549 [−0.888,−0.153] on 51 fights. Buying an upside 15m break in
  London via this trigger has been a losing continuation on this fit
  span. Its 3m counterpart *disagrees* (near +0.140), which is the noise
  reading, not the signal reading.
- **NY_PRE is the positive corner at both TFs** — every NY_PRE M3 cell is
  positive at the far target (2m: +0.573 long / +1.045 short; 3m: −0.047
  / +0.622), pooled-dirs far EV +0.820 (2m, n=46). CIs all span zero.
- NY_AM: near negative, far modestly positive, both TFs — the same
  "continuation pays only at distance, if at all" shape M2 shows there.

## THE CLOSELOC SWEEP — flat, and the row data says why

| thr (2m) | LONDON n / near EV | NY_PRE n / near EV | NY_AM n / near EV |
|---|---|---|---|
| none | 86 / −0.144 | 46 / +0.277 | 75 / −0.196 |
| 0.5 | 81 / −0.166 | 45 / +0.302 | 71 / −0.184 |
| 0.8 | 57 / −0.169 | 29 / +0.279 | 49 / −0.285 |

**Raising the threshold to 0.8 discards roughly a third of the population
and improves nothing, in any session, at either TF** (3m is the same
shape). The reason is in the feature itself: break candles close near
their own extreme *by construction* — brk_closeloc has median **0.85**,
96% of rows ≥ 0.5, ~two-thirds ≥ 0.8. There is almost no variance for a
threshold to grade. "High closeloc in the break direction" is a property
the population already has, not a selector within it. The sweep answers
the declared question: **no threshold is adopted because the feature
cannot discriminate here.**

## WHAT THIS PASS ADDS

1. **The construction is now complete as specified** — three mechanisms,
   both M1 targets, per-session everything, funnel alongside joins — and
   the complete book runs **1.68/day (2m) / 1.22/day (3m)**, with the
   analyzable cell at 0.01–0.29/day. The thinness question is now
   answerable on a finished object; the tolerance was not touched.
2. **M3 exists and is the largest arm, but nothing in it prices
   positively with confidence** — the only clearing cell is a negative
   one (2m London-long), and the one attractive corner (NY_PRE far
   targets) is 20–46 rows with CIs spanning zero.
3. **The closeloc threshold is refuted as a selector** — the feature has
   no variance on break candles. Swept as declared, nothing fixed,
   nothing adopted.
4. **The 60m rebalance target is ill-posed on a third of 3m M1 rows**
   (target at/behind entry) — its apparent 3m advantage is not read as
   real. At 2m, where it is well-posed, it loses to the 15m target
   outright.

Standing unchanged: fit-only, no holdout contact (the bar-only venue is
closed; none exists for this family), nothing adopted, 2m/3m never
pooled, tolerance stays 10pt.
