---
date: 2026-08-05
status: census PASSED (27%/28% vs 15% floor) — L1 owed
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

---

## Trial 1 — L0 census (2026-08-05) — **PASSED on premise, advances to L1**

`docs/PREREG-london-atc-census.md` (committed before the run).
`scripts/london_atc_census.py`. 396 London sessions, 2025 discover / 2026 validate.
**2023/24 untouched — no holdout look spent.** No P&L computed; none may kill here.

### The taught sequence happens, and it is era-stable

| era | sessions | completed the chain | rate | floor was 15% |
|---|---:|---:|---:|---|
| 2025 | 257 | 69 | **27%** | PASS |
| 2026 | 139 | 39 | **28%** | PASS |

Half-year: 29% / 25% / 26% / 55%. The last is 2026H2 on 11 sessions — noise, flagged
rather than quoted. The first three are flat, which is what a structural feature should
look like.

### The funnel — every session accounted for (§5.12.1)

| stage | share |
|---|---:|
| no Asian trend at all | 22% |
| trend, but no pullback | 2% |
| pullback, but no LTA | **40%** |
| LTA, but no aligned trigger | 8% |
| fallback arm only (30m+1h) | 1% |
| **triggered** | **27%** |

**The LTA requirement is the binding constraint**, not the trend and not the trigger.
Four sessions in ten have the bias and the pullback and then fail the low-traffic test.
That is where the taught setup does its selecting.

### Two things the census found that the source does not say

**1. The trigger grid is 30-minute, not 15-minute.** He asks for *"a bearish candle close
on the 15 and 30 minute together."* A 15m bar closing at 08:15 has no 30m bar closing at
08:15 — 30m closes fall at 08:00 and 08:30. So "together" can only occur on 30-minute
boundaries, and the observed trigger clock confirms it exactly: **07:30, 08:00, 08:30,
09:00 and nothing between.** The opportunity set is half what a naive reading implies.
This is faithful to what he said; it is just not what it sounds like.

**2. 27% of triggers fire BEFORE the 08:00 open.** Consistent with the taught setup —
he enters on the pullback, not at the open. Worth stating because both dead London
candidates entered *at* the open, and this is mechanically a different trade.

### Semantics check on my own mechanisation (§5.12.15)

The prereg flagged that "≥2 consecutive 15m closes in the pullback direction" is **my**
translation of his LTA rule, not his words. The cross-tab says it is a **loose** test:

| longest run | share |
|---|---:|
| 0–1 (fails) | 53% |
| 2 | 28% |
| 3 | 15% |
| 4 | 4% |

The pullback window holds a median of **4** fifteen-minute bars, so "≥2 consecutive"
is being cleared inside a 4-bar window by 47% of sessions that get that far. **The column
is not measuring anything as selective as the phrase "low traffic area" suggests**, and
the verdict records that rather than letting the name carry weight it has not earned. A
stricter LTA definition is a declared L1 arm, not a census revision.

### Event-universe ceiling, declared before economics (§5.11.2)

All-triggers rather than first-per-day gives **1.55×** (2025) and **1.51×** (2026) more
events — 107 and 59. The fallback arm (30m+1h with a weak opposite 15m) adds only 5
sessions across both eras and is close to irrelevant.

### Lookahead — certified, not assumed (§5.11.7)

Bias fixed at 07:00 from 03:30–07:00 data. Pullback measured against the 07:00 close.
Resampling is right-closed and right-labelled, so a bar labelled `T` contains only data
strictly before `T`. No column reads a bar closing after its decision minute.

**Recorded:** `LDN-ATC-01` × 2 eras in `output/trial_ledger.parquet` (premise frequency,
no effect charged — a trigger count is not an edge claim).

### Next rung — L1

As-taught geometry: entry on the break of the trigger candle's extreme, stop beyond its
opposite side, target 1:1 then next support, hard flat 10:00 London. Built with the
time-segment / MFE-MAE schema in from the start (§5.12.5) rather than bolted on, and with
the randomised-bias control declared in the candidate proposal so "continuation" must beat
"any direction" rather than merely beat zero.
