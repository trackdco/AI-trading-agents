# FINDINGS — the iFVG trigger on NQ: no edge, and the filters subtract

NQ, 1,251,240 one-minute bars, 2023-01 → 2026-07. **22,725 inversion signals**, 23 a
day. Cost 0.5 points round turn (the incumbent census's assumption), 2-point risk floor
(BR-29), day-clustered intervals, both era halves.

## The trigger

| variant | n | /day | win % | EV | 95% CI | **EV before cost** |
|---|---|---|---|---|---|---|
| trigger only | 21,219 | 23.1 | 32.5 | **−0.144** | [−0.163, −0.125] | **−0.026** |
| + liquidity sweep required | 10,883 | 11.9 | 32.2 | −0.150 | [−0.177, −0.122] | — |
| + breakeven at target 1 | 21,219 | 23.1 | 27.4 | −0.137 | [−0.156, −0.119] | — |
| sweep + breakeven | 10,883 | 11.9 | 28.3 | −0.144 | [−0.169, −0.118] | — |

**Before cost the trigger is −0.026R** [−0.044, −0.007] — a coin flip, very slightly
negative, with the interval clear of zero. 32.4% of trades reach 2R against 67.5%
stopping out, and 0.324 × 2 − 0.675 = −0.027, so the arithmetic closes on itself.

Cost is 0.118R on a median 4.5-point stop. It is most of the visible loss but not the
whole story: remove it entirely and the trigger still does not pay.

## His two headline rules add nothing

**The liquidity sweep — stated as required** (*"we always want the market to sweep some
sort of higher low"*) — makes EV slightly **worse** and halves the frequency. It is not
selecting better trades; it is selecting fewer.

**The breakeven rule** is the most-repeated mechanic in the entire channel: 1,958
mentions across 472 transcripts, more than "fair value gap" itself. Measured, it moves
EV by **+0.007R** while converting 16% of trades into scratches and dropping the win
rate 5 points. That is a rounding error, not a mechanic.

It is worth naming what it *did not* do, because the repo has been burned here before:
BR-46/48 recorded fixed-target exits buying 15–16pp of hit rate and selling 80–100% of
expectancy — a dual-currency inversion. The breakeven rule does not reproduce that. It
does not help either.

## The quality filters subtract

His two most-emphasised discriminators, the "obviousness" of the gap and the New York
session:

| variant | n | EV | EV before cost |
|---|---|---|---|
| all signals | 21,219 | −0.144 | **−0.026** |
| obvious: gap ≥ p50 of bar range | 10,630 | −0.136 | −0.019 |
| obvious: gap ≥ p75 | 5,388 | −0.139 | −0.027 |
| obvious: gap ≥ p90 | 2,167 | −0.135 | −0.029 |
| **NY 09:30–11:00 only** | 1,743 | −0.141 | **−0.071** |
| NY + obvious p90 | 241 | **−0.194** | **−0.141** |

**Obviousness does nothing.** Across the whole ladder before-cost EV moves −0.019 →
−0.027 → −0.029 with no trend. His central quality claim — *"the most obvious ones work
the best and that's just based off back testing"* — does not reproduce here.

**The session restriction makes it materially worse**, and worse before cost too
(−0.026 → −0.071), so it is not a cost artifact. *"I'm always going to go to New York
session"* is, on this trigger, the wrong place to be.

**The most selective stack is the worst cell in the study.** NY + obvious p90 is −0.194R
on 241 trades. That is the same shape the tomtrades ablation produced — every confluence
subtracting, the full stack worst of all — now on a second author and a second
instrument.

## What this does NOT establish

I tested **my** definition of his trigger, not his. He sells an indicator and teaches
visually, and the following are all absent from this implementation:

- the **higher-timeframe FVG** the inversion is supposed to deliver from
- the **key-area requirement** — *"we don't like just an inversion fair value gap in the
  middle of nowhere"* — London low, Asia low, news low, equal lows
- **trend-line liquidity**, which the 2026 model makes the primary draw
- **momentum entry** — death/birth candle rather than a choppy close
- **SMT**, 1,183 mentions across the corpus and completely untested here
- order block / CISD confluence

So the honest statement is: **the bare inversion trigger has no edge, which is what he
himself says.** His claim is that the context filters supply it. Two of those filters
were testable here and both subtracted; the rest are not yet coded.

The prior is not encouraging — the tomtrades ablation found every confluence subtracted,
and BR-19/21/31 found NQ's selection layers weak — but it is a prior, not a result.

## Next, in order

1. **SMT.** 1,183 mentions, entirely untested, and it needs ES alongside NQ. It is the
   largest untested component of his model.
2. **HTF context.** Restrict inversions to those inside a higher-timeframe FVG. This is
   his stated discriminator and it is codable with the census's existing level machinery.
3. **Trend-line liquidity.** The current model's primary draw, and the hardest to code
   honestly — a trend line has free parameters that a census does not.

Per the repo's non-negotiables: the full ladder is published, no threshold was chosen to
improve a number, and the negative result on the bare trigger is reported without
implying it refutes the full model.

---

# ADDENDUM — does anything the repo already measured rescue it?

He says the bare trigger isn't enough and that context supplies the edge, but never says
which context. This repo has a *measured* list, so rather than guess his confluences,
every inversion was annotated with things already known to matter here.

**Three of them help, and one replicates the repo's own census.**

## 1. Locus ordering reproduces BR-12

Pre-cost EV by the nearest of the seven censused levels:

| locus | EV before cost | | BR-12 rank on NQ (break arm) |
|---|---|---|---|
| **vwap_m1** | **−0.007** | | **+0.248 — 1st** |
| **val** | **−0.012** | | **+0.234 — 2nd** |
| vah | −0.017 | | +0.068 |
| vwap | −0.030 | | +0.096 |
| poc | −0.034 | | +0.094 |
| vwap_p1 | −0.039 | | +0.054 |
| **bbma15** | **−0.059 — worst** | | +0.105 |

vwap_m1 and val are the two best cells here and were the two both-era survivors in BR-12.
Two independent triggers, same instrument, same ordering at the top. That is the closest
thing to a replication in this document.

## 2. Distance to a locus — his own claim, and it holds

| distance to nearest locus | n | EV before cost |
|---|---|---|
| **≤ 0.020 W** | 5,304 | **+0.009** |
| 0.020–0.053 W | 5,304 | −0.034 |
| 0.053–0.124 W | 5,303 | −0.049 |
| ≥ 0.124 W | 5,304 | −0.030 |

The nearest bucket is the only positive cell in the entire study. *"We don't like just an
inversion fair value gap in the middle of nowhere"* is **supported** — measured against
the repo's level set rather than his intuition.

## 3. Direction relative to the 15m BB MA (BR-1)

Trading toward the MA −0.013 before cost, away from it −0.039. The strongest base rate in
the repo (89% NQ, 92.85% GC) shows up as a 0.026R tilt on this trigger too.

## And one that REVERSES against the repo

**Room to run runs the wrong way here.** BR-32/35 found room ≥3R was the largest non-flow
gate on NQ. On this trigger it is monotone *backwards*: ≤0.68R gives +0.003 before cost,
≥3.9R gives −0.041. Plausible reason — the target here is a fixed 2R, so room beyond that
is not reward, it is just a measure of being in open space, which for a mean-reverting
inversion is the wrong place. **A gate does not port between triggers; it has to be
re-measured, and this one flips sign.**

## Stacking them

| stack | n | /day | EV | 95% CI | **before cost** |
|---|---|---|---|---|---|
| all signals | 21,219 | 23.1 | −0.144 | [−0.163, −0.125] | −0.026 |
| at a locus (≤0.02W) | 5,346 | 5.9 | −0.116 | [−0.153, −0.080] | +0.007 |
| + toward the 15m MA | 2,656 | 3.1 | −0.105 | [−0.158, −0.051] | +0.020 |
| **+ locus ∈ {vwap_m1, val}** | 699 | 1.6 | **−0.049** | [−0.155, +0.063] | **+0.073** |
| + risk_w above bottom quartile | 466 | 1.4 | −0.103 | [−0.222, +0.027] | +0.004 |

Monotone improvement for three rungs — **+0.099R of pre-cost EV**, the largest lever found
on this trigger — then the risk filter breaks it, so that one does not stack.

## The higher timeframe, which is his own advice

*"Try to go to the higher time frame, use that one instead."* Same trigger on 5-minute
FVGs, executed on the 1-minute tape:

| | n | /day | median stop | EV | before cost |
|---|---|---|---|---|---|
| 1m trigger | 21,219 | 23.1 | 4.5 pt | −0.144 | −0.026 |
| **5m trigger** | 4,408 | 4.9 | **9.2 pt** | **−0.052** | **+0.020** |

The stop doubles, cost per R halves, and the loss shrinks by two thirds. But H1 is −0.126
against H2's +0.008, so it is unstable across eras, and the context stack stops adding
once n falls this far.

## Verdict

**Yes — three things from the other strategies help, and they are the same things the
repo measured before.** Locus proximity, the vwap_m1/val preference and the BR-1 draw
together move pre-cost EV from −0.026R to +0.073R, and the higher timeframe fixes most of
the cost problem.

**None of it, alone or stacked, gets the book above zero after costs.** The best cell is
−0.049R at 1.6 trades a day with an interval spanning zero and neither era clearing. Two
separate routes to improvement both land just short of the 0.5-point round turn.

Which localises the problem: this trigger's stops are too small to carry NQ's friction,
and the fixes that enlarge them also thin the book faster than they add edge. The
untested route that would change that is a genuinely higher-timeframe structure — his
model delivers from a *monthly* fair value gap, not a 5-minute one — and that is a
different study, not another filter.

---

# CORRECTION — two detector bugs, and the addendum above is partly withdrawn

Everything before this line ran on a **mis-specified detector**. Two bugs, both found by
auditing my own code rather than by anything failing.

## Bug 1 — I tested the wrong pattern entirely

The gap across bars (i−3, i−2, i−1) is complete at bar i−1, and the loop tested bar i
against it and nothing else. **Every "inversion" was therefore exactly one bar old.** An
inversion fair value gap is a gap price *left*, came *back* to, and then closed through —
minutes or hours later. What I actually measured was "three-bar gap immediately reversed
on bar four", a different and much noisier pattern.

Fixed by carrying gaps forward in an active list until they invert, expire (240 bars) or
the session ends, with an optional requirement that price re-enter the zone before the
breaking close.

## Bug 2 — the book double-counted the same move

With gaps carried forward, one momentum candle can close through several stale gaps at
once. Each became its own trade, at nearly the same price, in the same direction. That is
why the corrected trigger first reported **207 signals a day** — an obviously impossible
number for a model whose author takes one to three trades.

Fixed per BR-9/BR-10: one signal per bar per direction (keeping the oldest, most-respected
gap), then a 15-bar cooldown per direction. 199,498 → 85,339 signals, 87.7/day. Still
high, and the convention is now stated rather than implied.

## What the corrected numbers say

| | signals | /day | EV | before cost |
|---|---|---|---|---|
| trigger only | 80,593 | 87.7 | **−0.135** [−0.145, −0.125] | **−0.020** |
| + liquidity sweep | 36,127 | 39.3 | −0.140 | — |
| + breakeven at T1 | 80,593 | 87.7 | −0.128 | — |

**The verdict does not change.** Still negative, still a coin flip before cost, and the
sweep still subtracts. The breakeven rule still moves EV by under 0.01R.

**Gap age turns out not to matter at all** — pre-cost EV is flat from −0.015 to −0.023
across every age quintile from 1 bar to 240. The whole distinction the fix was about makes
no difference to the outcome, which is itself worth knowing.

## But the addendum's headline does NOT survive

| stack | pre-cost, buggy | pre-cost, **corrected** |
|---|---|---|
| all signals | −0.026 | −0.020 |
| at a locus (≤0.02W) | +0.007 | **+0.003** |
| + toward the 15m MA | +0.020 | **−0.008** |
| + locus ∈ {vwap_m1, val} | **+0.073** | **+0.015** |

**The "+0.099R from stacking" claim is withdrawn.** On a correct population the stack is
worth about +0.035R, not +0.099R, and the BR-1 component — *trading toward the 15m MA* —
**flips from helping to hurting**. That part of the addendum was an artifact of counting
one-bar reversals.

What still survives, weakly: **being at a locus beats being between loci** (−0.020 →
+0.003), and **vwap_m1/val remain the best pair** (+0.015). His "not in the middle of
nowhere" claim holds; the magnitude was inflated three-fold by the bug.

The most selective stack is again the worst cell — aged + locus + toward MA is −0.075
before cost on 1.7 trades a day.

## Standing conclusion

The model is negative on NQ at every specification tested, before and after costs, with a
correct detector and a stated clustering convention. The one thing that reliably helps is
locus proximity, and it is worth roughly +0.023R pre-cost — not enough to reach zero, let
alone clear a 0.5-point round turn.
