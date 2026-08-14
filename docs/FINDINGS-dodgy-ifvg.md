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
