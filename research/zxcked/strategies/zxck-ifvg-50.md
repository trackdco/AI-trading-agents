---
id: zxck-ifvg-50
name: Inverse-FVG 50% mark
trader: Powell
prefix: zxck-
sessions: [not stated — used as both a standalone model and a trigger]
instruments: [NQ]
GAP_ENTRY: YES — pools directly with ash-unicorn-sb's retrace-participation test
NY_SESSION: partial — examples are NY, but he never restricts it
his_rank: "#3 — stated as a standalone model three separate times, unprompted"
sources: [lRgsHGWzO9E, r5_yNjXsv6k, BOuJLWIisMI, dlSXQgM1ZpA, pMv3USznFdU]
components: zxck-COMPONENTS.md
verdict: INSUFFICIENT
---

# `zxck-ifvg-50` — the inverse-FVG 50% mark

## Confirmation

### 1 · TEACH-BACK

A fair value gap that price has traded **back through and closed beyond** stops being support and
becomes resistance — that inversion is the object. What he claims is that the **50% of that
inverted gap** is where price reacts, and he says it happens often enough on the 5- and
15-minute that you could trade nothing else. So I mark inverse FVGs on the 5m and 15m, wait for
price to return to the midpoint of the gap, and enter there against the gap's original direction
with a **5-point stop**. On the 1- and 3-minute the same object is his fourth entry trigger:
after price taps a level I'm watching, I take the 50% of the 1m/3m inverse FVG that forms inside
it, with the stop above the high made after the tap. He warns that it often *barely* taps the
level and goes, so a strict limit will miss fills. In one worked example the trade is a 5-point
stop targeting the first swing low 37 points away — about 1:7. **What I cannot tell you is when
to take it and when not to**: he gives no bias requirement, no target rule, and no filter beyond
"use good gaps", and the honest position is that I do not have a complete model here.

### 2 · SEVEN-PART COMPLETENESS CHECK

| part | tag | evidence |
|---|---|---|
| **bias source** | **[gap]** | Never stated for this model. In the trigger role it inherits the parent level's bias, but the *standalone* version at `[lRgsHGWzO9E @ 07:44]` has no bias condition at all |
| **setup conditions** | **[stated]**, thinly | *"15 minute or five minute inverse fair value gap"* `[lRgsHGWzO9E @ 07:44]`; as a trigger, 1m/3m `[r5_yNjXsv6k @ 02:20]`. **What makes a gap "good" is never defined** — *"use good gaps. Don't use every random gap that you see"* `[dlSXQgM1ZpA @ 03:51]` |
| **entry trigger** | **[stated]** | *"enter on the 50% mark of that inverse fair value gap"* `[lRgsHGWzO9E @ 07:44]` |
| **stop / invalidation** | **[stated]** | *"with a five-point stop"* `[@ 07:44]`; as a trigger, *"keep your stop above this high… That's five points exactly"* `[r5_yNjXsv6k @ 01:34]` |
| **targets** | **[gap]** for the standalone; **[inferred]** as a trigger | Standalone: none given. Trigger: *"we aim for the first swing low which is 37 points"* `[r5_yNjXsv6k @ 01:34]` |
| **risk / sizing** | **[inferred]** | Inherits `COMPONENTS` §D/§E; nothing model-specific |
| **avoid-filters** | **[gap]** | Only *"use good gaps"* `[dlSXQgM1ZpA @ 03:51]`, which is not a filter |

**Three parts are [gap], and two of them (bias, targets) are core.**

### 3 · ASK ME

**Q-C1 · Is the standalone 5m/15m version real, or was he describing the 1m/3m trigger loosely?**
- *Best guess:* **it is real and separate.** He interrupts his own FVG video to introduce it
  — *"I should make a video on this because it is literally mindboggling how often this happens…
  15 minute or five minute"* `[lRgsHGWzO9E @ 07:20–07:44]` — and repeats the 50%-only advice
  months later `[dlSXQgM1ZpA @ 03:51]`. The trigger version is explicitly 1m/3m
  `[r5_yNjXsv6k @ 02:20]`, so they are different scales.
- *Why it matters:* decides whether we build **one card or two**. A 5m/15m standalone with a
  5-point stop is a very different animal from a 1m/3m trigger inside a level.
- *Answerable from method?* **Yes.**

**Q-C2 · Does the standalone version need a level/bias, or is the inverted gap the whole setup?**
- *Best guess:* **it needs one, and he just didn't say so** — everything else he teaches requires
  a draw, and *"use good gaps"* implies selection. But **he does say you could make a model out
  of this alone** `[lRgsHGWzO9E @ 08:30]`, which reads as no additional condition.
- *Why it matters:* **this is the difference between a testable model and an untestable one.**
  Taken literally, every 5m/15m inverse FVG is a trade — that is thousands of events and almost
  certainly a coin flip. With a bias/level requirement it becomes a real setup. **Without your
  answer I cannot build this card past Insufficient.**
- *Answerable from method?* **Yes** — this is the single most important question in the set.

**Q-C3 · What is the target for the standalone version?**
- *Best guess:* **the first opposing swing point**, by analogy with the trigger version's *"aim
  for the first swing low"* `[r5_yNjXsv6k @ 01:34]` and the general 1:3–1:6 band.
- *Why it matters:* a 5-point stop with no stated target is not a strategy. Every result depends
  on what we choose, and if we choose it, the result is ours.
- *Answerable from method?* **Yes.**

**Q-C4 · What counts as the gap being "inverted" — a close beyond it, or a wick through it?**
- *Best guess:* **a close.** He is consistent elsewhere that closes define state changes — the
  rejection block *"is not a rejection block until this candle closes"* `[AGmRZ9Te9NY @ 02:47]`,
  the CISD needs a close beyond the open, and *"we closed below the fair value gap on the 545
  candle"* is how he narrates an inversion `[BOuJLWIisMI @ 04:39]`.
- *Why it matters:* wick-through inversions are far more common than close-through ones. This
  alone could change event count several-fold.
- *Answerable from method?* **Yes**, or re-watch `BOuJLWIisMI @ 04:16–05:03`.

### 4 · VERDICT — **INSUFFICIENT**

**Bias and targets are both [gap], and Q-C2 decides whether this is a strategy or an
observation.** He rates it highly and states it three times, so it is worth resolving — but I
will not invent a bias rule and a target rule and then call the result his. Not tradeable or
testable as it stands.

---

## Edge thesis
An FVG traded back through and closed beyond has flipped polarity; its midpoint is the sensitive
point. *"There's just something about these 50% marks of these inverse fair value gaps"*
`[lRgsHGWzO9E @ 08:56]`. **No mechanism is offered beyond the observation.**

## Setup / entry / stop
5m or 15m inverse FVG (standalone), or 1m/3m (trigger). Enter the **50%**. **5-point stop.**
`[lRgsHGWzO9E @ 07:44]`, `[r5_yNjXsv6k @ 01:34]`

## Known fill-rate warning — `[stated]`
> *"a lot of the times it's just going to tap slightly into it. Maybe even just barely tap it,
> and then go."* `[r5_yNjXsv6k @ 00:00]`
A strict limit backtest will **understate** fills. Combine with `COMPONENTS` §C4.

## Its role in the trigger menu
Fourth of his four triggers `[r5_yNjXsv6k @ 02:20]`. Relative to a rejection-block trigger:
**higher win rate, worse risk-reward** `[tNyT7tHOmGI @ 05:46]` — a stated ordering we can test.
It is also one of the three conditions in the displacement rule `[pMv3USznFdU @ 02:43]`.

## Performance claims — `[trader-claimed, unverified]`
- *"You could literally make a model out of this alone and be profitable."* `[lRgsHGWzO9E @ 08:30]`
- *"look at how often it does this"* / *"this happens all the time"* `[@ 07:44, 08:30]` — no
  sample, no count.

## Revision log
- **2026-08-07 rev a** — INSUFFICIENT. Bias and target are gaps; Q-C2 is blocking.
