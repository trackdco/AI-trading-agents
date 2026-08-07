---
date: 2026-08-05
status: VERDICT — family killed. W was a lookahead.
tags: [nya-lvl, verdict, lookahead, self-correction]
sources: ["output/nya_lvl_null.md", "output/nya_lvl_depth.md", "output/nya_lvl_rebuild.md", "research/findings/NYA-LVL-01-VOID-entry-bar-skipped.md"]
---

# NYA-LVL-01 — VERDICT: killed. Three bugs, all the same shape, all mine.

## Result

**FAIL.** Placebo null, 100 permutations: observed family-wise best **+0.7082 R/trade**,
null median **+0.7509**, **family-wise p = 0.7500** against a declared bar of 0.01. The
null median *exceeds* the observed value — random lines beat the real six.

And the reason is not that the levels are useless. **The reason is that `W` reads the
future.**

## The kill shot

`W` was computed from the order book at the **fill minute**. Our fill happens *inside*
that minute, so the snapshot includes what price did *after* we entered. Recomputed from
a book we would actually have held:

| book used | n | WR at 2R | R/trade | lift |
|---|---:|---:|---:|---:|
| fill minute (as run) | 490 | 56.9% | +0.708 | **+19.5pp** |
| **1 minute before the fill** | 923 | 41.6% | +0.248 | **+4.2pp** |
| 2 minutes before | 1,143 | 39.2% | +0.176 | +2.1pp |

**Nearly 80% of the edge is information from the wrong side of the decision point.**

`W=1` at the fill minute means *"by the time this minute closed, price had run past the
visible book."* We were selecting entries where the push exhausted itself within the
minute we entered, and then fading it. We were reading the answer.

**This also explains the null.** Random lines scored +0.744R — better than the real
levels — which is nonsense as a market fact and exactly right for a lookahead: `W` peeks
regardless of what line it is attached to. One bug explains every result in this family.

## What survives

- **The raw substrate.** 4,548 events over 281 sessions, 16.2/session, six lookahead-clean
  levels. That is a real, high-frequency trigger source and it is unaffected.
- **The honest bar-only ceiling.** ~60% at 1.0R, best single-variable lift +2.7pp,
  roughly +0.20R/trade. Marginal.
- **The `W`-at-one-minute-prior residual: +4.2pp.** Same order as the bar variables. Not
  a strategy.

## What died

The level-interaction thesis, twice over: the geometry search failed its placebo at
p = 0.205, and the depth filter that appeared to rescue it was a lookahead.

## THREE BUGS, ONE SHAPE — the process finding, and it matters more than the verdict

Every bug in this family made the numbers **better**, and every one was **information from
after the decision point**:

1. **The trail** updated its stop from a bar's high and then tested that same bar's low —
   assuming the favourable extreme came first.
2. **The simulation** started 12 minutes after the fill, so a 10pt stop had already been
   hit on 72.9% of trades before the clock started. Produced PF 3.09.
3. **`W`** read the book at the fill minute, including the part after entry. Produced
   56.9% at 2R.

I found #1 and #2 by looking. **I only found #3 because Angus said the result sounded
oversold and pushed back.** That is the wrong ratio.

**The failure was not the bugs — it was what I did after fixing them.** I found two
lookaheads, corrected them, saw the number stay high, and treated survival-of-a-fix as
validation. It is not. A result that has already yielded two lookaheads is *more* likely
to contain a third, not less.

### Standing check adopted from this family

**Any feature whose lift exceeds the bar-only baseline by more than ~5pp is recomputed
one bar earlier BEFORE it is reported at all.** Not after someone is sceptical — before
the number is spoken. The check costs one line of code and would have caught #3 before it
was ever shown.

Corollary, and the one I keep relearning: **the seam between event detection and
simulation is where this class of bug lives.** Bug #2 and bug #3 are the same bug at two
different resolutions — one at 15-minute granularity, one at 1-minute.

## Ledger

All arms recorded, including every void one. A vacated result does not un-charge the
search; the DSR denominator keeps them.

## Not spent

**No 2023/24 look, no sealed-flow look.** The family dies without costing the programme a
holdout look — the one piece of discipline that held throughout.
