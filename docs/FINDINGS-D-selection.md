# FINDINGS — PHASE D: next selection work (2026-08-07)

Ran only after Phase A cleared. Book context as in FINDINGS-A. The break
arm stayed parked throughout, per the standing order.

## D1 — closeloc as a bar-only proxy for S1: REAL, PARTIAL, HOLDOUT-WORTHY

closeloc = where the trigger bar closes within its own range, oriented by
trade direction (1 = closed at the trade-favorable extreme). Pure OHLC —
no flow tape needed. On the full-fit reject book (fights with closeloc
defined):

```
rho(closeloc, S1-keep flag)      +0.388
cut-mask overlap (Jaccard)        0.34   (closeloc cuts 457 fights, S1 cuts 998)
closeloc<Q1 cut lift, full book  +0.078   (S1: +0.107)
S1 marginal lift within closeloc-kept  +0.057
closeloc marginal lift within S1-kept  +0.028
EV: unselected +0.149 | closeloc-kept +0.228 | S1-kept +0.257 | both +0.285
```

**Verdict.** closeloc captures roughly 70% of S1's effect from bars alone
and S1 retains real marginal information beyond it (+0.057) — the tape
sees something the candle shape doesn't, but the candle shape sees most
of it. That makes the idea testable where it matters: the 23-month
bar-only holdout at ±4pp resolution.

**Declared holdout claim, queued (LOOK NOT SPENT):** "On the reject-arm
first-of-fight book, removing fights with closeloc < the fit-frozen Q1
raises book EV; sign +, bar: lift ≥ +0.04R in Block A AND Block B under
the D4 aggregation rule." Contamination stated honestly: closeloc's fit
readouts are fully known (cut-study candidate; failed Half-1 at +0.034,
Half-2 read +0.148 after the fact; full-book +0.078) — fit-side
confirmation credentials are spent, which is exactly why its test is the
untouched holdout and nothing else.

## D2 — S1 × exit joint 2×2: NO FIGHT, THE EXIT STANDS

EV per fight, full-fit book:

| population | ship (75%@3R+trail) | pure trail | hold | trail p90 / p95 |
|---|---|---|---|---|
| all | +0.149 | −0.003 | −0.063 | +1.67 / +3.06 |
| S1-kept | **+0.257** | +0.084 | +0.123 | +1.61 / +2.95 |
| S1-cut | +0.060 | −0.075 | −0.219 | +1.75 / +3.17 |

Era detail, S1-kept: ship +0.298/+0.219 (H1/H2); trail +0.212/−0.035.

**Verdict.** The hypothesis (S1-kept fights have fatter tails → favor a
later partial or pure trail) is REFUTED: ship beats trail in every cell,
and the S1-kept tail is not relatively fatter (trail p90/p95 slightly
LOWER in kept than cut). S1's lift is loser-removal, not
runner-selection. The pure-trail arm is era-fragile exactly where the
book is weakest (H2-2025 −0.035). Corroborating B1: raising the partial
target to 4–5R raises EV per fight but not eval survival. **The adopted
exit (75% at 3R, trail remainder) stands unchanged.**

## D3 — two declared increments on S1: BOTH DEAD, AS LAW 7 PRICED

Law 7 arithmetic, stated before compute: (a) a magnitude-rank bottom-
quartile cut inside the S1-kept book (EV +0.257) clears the +0.05R bar
only if its removed bin runs ≤ +0.107R; (b) the 3-bar-delta variant must
beat S1's lift by ≥ +0.02R at comparable removal.

Self-check first: recomputed trigger-bar delta reproduces flowconf on
100.0% of rows — the tape post-pass is consistent with the builder.

```
(a) magnitude<Q1 within S1-kept:  removed bin +0.191R (H1) / +0.608R (H2)
    lift −0.006 / −0.074            — FAIL both halves
(b) 3-bar disagree cut:           lift +0.013 (H1) / +0.078 (H2)
    trigger-bar S1 on same halves: +0.053 / +0.175 — FAIL both halves
```

**Verdict.** (a) Magnitude adds nothing beyond sign — the weakest-flow
agreeing quartile is H2's BEST bin (+0.608R); flow magnitude at the
trigger is not the signal, agreement is. (b) Widening to three bars
dilutes: the trigger bar alone dominates in both halves. Two declared
increments, two recorded misses, zero sweeps. S1 stays exactly as
confirmed: sign-agreement of the trigger bar's delta, nothing fancier.

## D4 — two-axis scoring: ADOPTED

The cut-study runner now reports R/fight, fights/day, AND qualifying-day
rate ($250 floor) on every candidate, permanently. Rationale on the
record: the book is positive, so the job is concentration against the
dollar floor — a cut that raises R while halving frequency can hurt
qualifying days, and B1 showed the eval is won by survival, not
throughput.

## Standing state after Phase D

- S1: confirmed on fit (split-half + three gates + X-robust + permutation
  p 0.017–0.042 under the design's frame), forward validation via the
  Phase C recorder, flow-holdout look correctly unspent.
- closeloc: holdout claim declared and queued for the D2 bar-only look —
  the ONLY validated-on-holdout route currently available to the S1 idea.
- Exit: unchanged. Break arm: parked. Holdout looks: both unspent.
- Next candidate work requires fresh blind declarations; nothing is
  queued beyond the closeloc claim.
