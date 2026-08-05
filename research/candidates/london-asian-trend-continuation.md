---
date: 2026-08-05
status: PROPOSED — as-taught spec written, awaiting greenlight before any test
tags: [london, asian-session, continuation, lta, pullback]
sources: ["https://www.youtube.com/watch?v=ci24AdpcRaA", "https://www.youtube.com/watch?v=A8KDclHRpGc", "https://www.youtube.com/watch?v=WYq7A8rggmg", "research/findings/london-window-LDN-WIN-01.md"]
---

# london-asian-trend-continuation (LDN-ATC-01) — the pre-London pullback

**Not yet tested. Nothing run. This is the as-taught spec and the case for testing it.**

## How this surfaced, and my own error

My earlier corpus searches returned zero for "london" and I believed them. They were
silently failing on cached filenames that begin with a dash, which broke the shell glob.
Re-run properly: **65 of 103 cached transcripts mention London.** I built the entire
London programme off three videos while sitting on this.

This candidate comes from the densest of them — *"I Use This Entry Strategy Almost Every
London Session (Live Trade)"* (Tradesharpe, 51 London mentions) — a channel I had
dismissed for London on the grounds that his ORB is a New York setup, which he says
himself. He has a separate London body of work. That dismissal was wrong.

## Thesis (for Angus)

**The Asian session sets the direction; the hour before London open gives you the entry;
the London open pays it out.**

Through the Asian session price trends quietly one way. In the hour before London opens
it pulls back — not reversing, just retracing into the space it came from. Then London
opens and the original direction resumes, hard.

His words for the mistake everyone makes: *"you do not want to be buying straight at
highs and you do not want to be selling straight at lows after pushes happen... those
are two common mistakes for trading the London open."*

**That is the sentence that makes this worth testing.** Both candidates I just killed
traded exactly what he says not to trade — the extreme of the pre-open range, at the
open. `LDN-OBK-01` bought the break of the high; `LDN-PO3-01` faded it. This candidate
says the money is in **entering during the pullback, before the open, in the direction
the Asian session was already going.**

**The wrong side** is whoever chased the pre-London pullback thinking it was a reversal.
When London opens they are positioned against the session trend with no room.

## Why it is worth our time specifically

1. **It is a genuinely different object.** Continuation of an *overnight* trend, entered
   on a *pullback*, not a break of a level. Nothing in our book trades the Asian trend.
2. **It agrees with a thing we already measured, unprompted.** My `V3` conditioning test
   found the pre-open drift direction was the single most informative variable on the
   London open: fading a break that ran *with* the drift worked (+326 pts, PF 1.31),
   fading *against* it was a disaster (PF 0.54). Both are the same statement — **the
   pre-London direction carries information into the open.** He arrives at it from the
   other side and trades it directly rather than as a filter.
3. **It is a scalp, and the clock fits our own measurement.** He holds *"maybe 15
   minutes, 30 minutes max, sometimes only 5."* `LDN-WIN-01` found 08:00–09:00 London is
   the volume peak of the session in both eras. Short holds inside the peak hour.
4. **Bars only.** No new data, no purchase, and it reaches the sealed 2023/24 holdout if
   it ever earns a look.

## The spec, as taught — every element quoted

**Timeframe.** 15-minute for entry. *"I'm talking about scalping from point A to point
B... a 15-minute time frame. That is where my entry is going to be."*

**Step 1 — bias, from the Asian session.** Trend of the **last half of Asian** on the
15m, defined mechanically: *"Trend is going to be defined by lower highs, lower lows.
That would mean Asian went in a downtrend. And if we saw 15 minute making higher highs
and higher lows, that means Asian went in an uptrend."*

**Step 2 — the pullback window.** *"In this in-between space time, this is the pre-London
time, right? An hour before London open... this is where we can get the pullback."*

**Step 3 — the pullback must create an LTA.** His own vocabulary, and it is mechanical:
*"When a candle closes bearish and next one closes bullish, that creates a support. When
a candle closes bullish and the next one closes bearish, that creates a resistance."* A
stretch with neither is a **low traffic area** — *"that space had no friction... that's
the part we want to be in the market."*

**Step 4 — the entry trigger.** *"I am looking for a bearish candle close on the 15 and
30 minute together... I'm going to enter with breaking the low with my stop loss above
the high."*
Declared fallback: *"if we have the 30 minute and the 1 hour closing bearish, still
valid"* — even with one weak opposite 15m close.

**Step 5 — stop.** Above the high of the trigger candle (mirror for longs).

**Step 6 — target.** *"At least a one to one. And ultimately you can target to the bottom
of the range. What you're going to target is the next support."*

**Step 7 — the no-trade case.** If London ranges rather than impulses, there is no trade:
*"if it's going to range like this, I'm not interested in a setup."* **This is a
discretionary gap** — he never says how to know in advance. See flags.

## Flags — read before greenlighting

- **INSTRUMENT. He demonstrates on gold and says *"this will work across forex pairs as
  well as gold."* He does not name NQ.** This is the third London candidate from this
  corpus with an instrument-transfer question, and the previous two both died. The
  structure is instrument-agnostic in principle and the clock is the clock — but the
  honest position is that NQ applicability is an assumption, not a claim, and it goes in
  the verdict either way.
- **The no-trade rule is not mechanical.** "Don't trade when London ranges" is knowable
  only afterwards as stated. It must be either dropped (test every signal, accept the
  range days as losses — the honest as-taught reading per §5.9.1) or replaced with a
  declared same-time-computable proxy. **I would drop it** and record that the tested
  spec is stricter than the taught one.
- **The trigger-candle stop is the geometry that just failed.** `LDN-OBK-01` died partly
  because a trigger-candle stop at 2R was hit 65% of the time. Here the stop is the same
  shape but the entry is inside an LTA after a pullback, not at a range extreme — the
  claim is that there is nothing between entry and target. **That difference is the
  experiment**, and it deserves an explicit head-to-head rather than an assumption.
- **"Last half of Asian" needs a clock.** He never gives one. Declared proposal:
  22:00–02:00 London as full Asian, last half = 00:00–02:00 London, frozen before any run.
- **Multi-timeframe alignment is a real cost.** 15m + 30m + 1h closes must be built from
  1m bars with correct boundaries, and DST-correct in London time.

## What I would run, if greenlit

1. **Census first (§5.9.1).** Does the taught behaviour occur? Frequency of: Asian trend
   present → pullback in the pre-London hour → aligned 15m+30m close. Kill line: the
   sequence essentially never completes. **No P&L at census.**
2. Then L1 at the as-taught geometry, with the placebo-style control this programme now
   expects: **the same trigger with a randomised bias direction**, so "continuation" has
   to beat "any direction" rather than just beat zero.
3. Full §5.11/§5.12 ladder from the start this time — time-segment/MFE-MAE schema built
   in at L1 rather than bolted on, depth and flow classes both declared, permutation null
   with selection correction budgeted from the beginning.

## Also found in the same sweep, not yet specced

- `WYq7A8rggmg`, `etovQmnqsmk` — the **LTA construction** videos (35 and 27 London
  mentions), which define the low-traffic-area primitive and discuss Asian-session volume
  directly. These are the source for the inefficiency-primitive question flagged much
  earlier (LTA ≈ zero prints ≈ LVN ≈ FVG — one object, several detectors, only the
  bar-only one reaches the holdout).
- `A8KDclHRpGc` — *"My Strategy To Trade London Session Profitably"* (72 London mentions,
  the densest file in the corpus), forex-framed, not yet read in full.

**Nothing above has been tested. No trials, no ledger entries, no looks.**
