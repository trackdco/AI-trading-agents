---
date: 2026-08-05
status: VOID NOTICE — stages 1(P&L)/2/3a/3b results withdrawn
tags: [nya-lvl, lookahead, self-correction, void]
sources: ["output/nya_lvl_census.md", "output/nya_lvl_geometry.md", "output/nya_lvl_regime.md", "output/nya_lvl_discriminant.md"]
---

# NYA-LVL-01 — every P&L number is void: the simulation skipped the entry bar

Angus called it — *"almost suspiciously good"* — and he was right. Found on the check
his suspicion prompted.

## The bug, in one sentence

**We fill at the level mid-bar, but the simulation does not start watching until the
15-minute bar closes — a median of 12 minutes later — and in that gap price moves a
median of 21 points against the trade.**

## The measurement

4,681 entries, fit span:

| | |
|---|---:|
| minutes of the entry bar skipped | median **12**, mean 11.1 |
| adverse move inside that skipped window | p50 **21.0**, p75 43.5, p90 75.5 pts |
| **a 10pt stop already hit before the sim starts** | **72.9% of trades** |
| a 15pt stop already hit | 61.8% |
| a 20pt stop already hit | 51.8% |

Roughly three quarters of the trailing arm's trades were already dead in reality before
the simulated trade began. The simulation was scoring the survivors of a filter it never
applied.

## What this voids

- **Stage 2 in full** — the geometry grid, the PF 3.09 trail arm, the PF 1.07 default,
  every one of the 51 arms. All built on paths that start after the entry bar closes.
- **Stage 3a, the regime diagnostic** — same paths. Its conclusions (not trend capture,
  both sides work, positive every month, 2-minute holds) are all computed on the
  survivor-biased set and mean nothing until re-run.
- **Stage 3b, the discriminant** — same paths. All 34 cells per arm, void.
- **Stage 1's P&L tables** — same path construction. Void.

## What survives

- **Stage 1's event counts.** 4,808 touches, 4,759 filled, 16.6/session, the level-type
  distribution, the funnel. Those are counting, not simulation, and the entry-bar gap does
  not touch them.
- **The stage-2 placebo null result — and it survives for an awkward reason.** Both the
  real and the placebo runs used the same broken path construction, so `p = 0.205` is a
  comparison of two equally broken things. That makes it *unaffected as a comparison* but
  it must be re-run before being cited, because a null computed on a void statistic is
  not evidence about the fixed one.
- **The MFE/MAE shape from stage 1** is directionally suspect for the same reason and gets
  recomputed.

## The fix

The entry is a resting limit at a known, pre-computed level. It fills **the minute price
reaches the level**, and the trade is live from that minute. The correct model is:

1. Detect the touch on **1-minute bars**, not on the 15-minute close.
2. Start the path at the **touch minute**, with the stop live immediately.
3. Keep the 15-minute bar only for what it is actually used for in the source — the
   chart he watches — not as the thing that gates when risk begins.

This is also **more faithful to the source**, not less: he places orders at levels and
they fill when price arrives. Nothing in his teaching says risk starts at the next
quarter-hour.

## Honest note on direction of error

Stage 1's raw P&L was **negative** even with this bug helping it. So the raw set is worse
than reported, not better. The bug inflated everything; it did not create the negative
raw result, and §5.9.1's "raw looks ugly" expectation is undisturbed.

## Process note

The bug survived three stages and two prior bug-hunts of my own — I caught an intrabar
lookahead in the trail logic and a wrong-side stop reference, and fixed both, while this
larger one sat underneath. Two lessons worth recording:

1. **Fixing a bug in a suspiciously good result is not the same as validating it.** I
   found two bugs, fixed them, saw the number stay high, and treated that as
   reassurance. It was not.
2. **The check that found it was "what happens between the fill and the first bar I
   look at"** — a question about the seam between event detection and simulation. That
   seam is where this class of bug lives and it should be a standing check on any
   candidate whose trigger timeframe differs from its execution timeframe.
