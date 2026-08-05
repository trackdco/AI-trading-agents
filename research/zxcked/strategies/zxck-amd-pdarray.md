---
id: zxck-amd-pdarray
name: AMD into a PD array
trader: Powell
prefix: zxck-
sessions: [New York — one leg is "power hour"]
instruments: [NQ, MNQ]
GAP_ENTRY: PARTIAL — the PD array entered is often an FVG or order-block 50%
NY_SESSION: YES
sources: [EaxfhUS4eNg, -izOcim8KRQ, D-suu0f3XKI]
components: zxck-COMPONENTS.md
verdict: INSUFFICIENT
---

# `zxck-amd-pdarray` — accumulation / manipulation / distribution

## Confirmation

### 1 · TEACH-BACK

Price builds a range — that is accumulation. I am already directionally biased from higher
timeframes, so what I am waiting for is the **manipulation**: a push out of the range **against**
my bias, which sweeps the stops resting beyond it. I place a limit at a PD array sitting just
beyond the range extreme — in his example a 1-minute order block above the range, in the second a
5-minute order block's 50% — and I do **not** wait for a confirmation candle, because *"the
confirmation is to the left of the chart"*: the range and the sweep are the confirmation. Then
distribution delivers price back through the range in my direction and I target the far side of
it, about 50 points in his example. Stop is roughly 10 points, placed above the 25% mark of the
5-minute array. He treats AMD and engineered liquidity as the same idea seen from two angles. He
also flags his own trade as **not A+** because he was shorting inside a daily discount level.
**The part I cannot do is the first step — he never says what makes a range a range**, and
without that the model has no starting condition I could code.

### 2 · SEVEN-PART COMPLETENESS CHECK

| part | tag | evidence |
|---|---|---|
| **bias source** | **[stated]** | *"we're extremely bearish… I'm going to be short biased on this"* `[EaxfhUS4eNg @ 01:10]`; bias precedes the setup and comes from `COMPONENTS` §A |
| **setup conditions** | **[gap]** on the core | Accumulation/manipulation/distribution are **named and drawn** `[EaxfhUS4eNg @ 00:46, 02:22, 03:57]` but **never defined** — no bar count, no width, no test for what constitutes a range |
| **entry trigger** | **[stated]** | limit at a PD array beyond the range; *"I just placed short limits. I didn't want to see any more confirmation"* `[@ 02:45]` |
| **stop / invalidation** | **[inferred]** | *"my stop was probably like right above the 20 or 75% mark… so yeah, it was 10 points right above that 25% mark"* `[@ 07:07]` — hedged recollection |
| **targets** | **[inferred]** | *"I was probably like 50 points at the bottom of this range, these lows"* `[@ 04:45]` — the far side of the range |
| **risk / sizing** | **[inferred]** | micros used `[@ 06:21]`; `COMPONENTS` §D/§E otherwise |
| **avoid-filters** | **[stated]**, one | shorting into a daily **discount** is *"not A+"* `[@ 05:29]` |

**The core setup condition is a [gap].**

### 3 · ASK ME

**Q-F1 · What makes a range a range?**
- *Best guess:* I genuinely don't have one from the transcripts. Candidates that would be **ours,
  not his**: N consecutive bars inside a band, or a compression measure versus recent ATR.
- *Why it matters:* it is the **first step of the model**. Everything else is well specified and
  none of it can run without it. This same gap blocks `zxck-mmxm-breaker`.
- *Answerable from method?* **Probably not from the videos** — he draws boxes by eye in all three.
  Best answered from how you'd mark it, or by re-watching `EaxfhUS4eNg @ 00:46–01:10` and
  `@ 06:44–07:07` and reading the box edges off the chart.

**Q-F2 · Must the manipulation leg sweep a specific level, or just exit the range?**
- *Best guess:* **sweep something specific.** He wanted *"a manipulation up above these highs"*
  `[EaxfhUS4eNg @ 02:22]`, and his engineered-liquidity work is consistently about equal
  highs/lows rather than a bare range edge.
- *Why it matters:* "exit the range" fires constantly; "sweep equal highs" is rare and selective.
  Combined with Q-F1 it determines whether this model produces 5 or 500 events a year.
- *Answerable from method?* **Yes.**

**Q-F3 · Is AMD a standalone model or a description of what every one of his setups looks like?**
- *Best guess:* **a description.** He says *"AMD and engineered liquidity — they are pretty much
  the same thing"* `[D-suu0f3XKI @ 02:17]`, and the wick-CE, key-open and CISD models all contain
  an accumulate → manipulate → distribute shape.
- *Why it matters:* if it is a description, carding it separately would **double-count the same
  trades in the trial ledger** — the exact failure mode §6.0 exists to prevent.
- *Answerable from method?* **Yes.** This is the one I would most like your read on.

### 4 · VERDICT — **INSUFFICIENT**

The entry, stop and target are all recoverable, but **the setup's first condition is undefined**
and I will not substitute my own range detector and then attribute the result to him. Q-F3 may
also mean this should not be a card at all.

---

## Edge thesis
> *"AMD with into a PD array. Classic model. I love this model."* `[EaxfhUS4eNg @ 04:22]`
> *"this is a model if you want to use one model. This is probably one of the simplest, easiest
> models to use and it's very effective."* `[@ 07:33]` `[trader-claimed, unverified]`

## The entry philosophy — stated here more clearly than anywhere else
> *"for me the confirmation is to the left of the chart. I don't need to see another change in
> state of delivery or a fair value gap after we tap into this."* `[EaxfhUS4eNg @ 02:45]`
Consistent with `COMPONENTS` §B3 — the engineered-liquidity gate is what licenses a blind limit.

## Related
The fib pairs with this: *"this is also great to combine with the AMD video or engineered
liquidity. Those are kind of the same concept."* `[-izOcim8KRQ @ 01:38]`

## Revision log
- **2026-08-07 rev a** — INSUFFICIENT. Range undefined (Q-F1); Q-F3 may fold it into other cards.
