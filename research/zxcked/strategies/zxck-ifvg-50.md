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
verdict: CONFIRMED
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

### ⬛ SELF-RESOLVED 2026-08-07 — Q12, Q13 closed; Q10 and Q11 still block
Full evidence: `SELF-RESOLVED-2026-08-07.md`.
- **Q12 → the standalone 5m/15m version IS real and separate** from the 1m/3m trigger `[lRgsHGWzO9E @ 07:44]` vs `[r5_yNjXsv6k @ 02:20]` `[stated]`
- **Q13 → inversion requires a CLOSE beyond the gap**, not a wick-through `[BOuJLWIisMI @ 04:39]` `[stated]`

**Still INSUFFICIENT: Q10 (bias) and Q11 (target) are both core and both unanswered.**

### ⬛ ANSWERED 2026-08-07 — Q10 closed by Brake, Q11 mooted by the exit lock

**Q10 · does the standalone version need a bias/level? — `[stated-by-user]`: YES, IT REQUIRES ONE.**
> *"the standalone version REQUIRES a directional bias / level. An inverted FVG counts as a setup
> only when it forms in line with a draw on liquidity, same as the rest of his method."*

**LOCKED RULE:** an inverse FVG is a setup **only when it forms in line with a draw on liquidity**
(`zxck-COMPONENTS.md` §A — PXH/PXL, then session extremes, then MMXM). The draw-already-taken kill
`[38YtF6xFX4o @ 06:08]` applies here as it does everywhere else.

**⚠️ THE INTERPRETIVE CHOICE, RECORDED — this gate came from Brake, not from Powell.**
Brake's instruction, verbatim:
> *"the 'you could literally make a model out of this alone' line is treated as him overselling
> the concept, not a literal every-gap rule — the literal version produces thousands of undirected
> events a year and is a coin flip a priori."*

So `[lRgsHGWzO9E @ 08:30]` is read as **rhetoric, not specification**, and *"use good gaps. Don't
use every random gap that you see"* `[dlSXQgM1ZpA @ 03:51]` is read as **the selection criterion he
gestured at but never spelled out** — resolved here as draw-alignment. Both quotes stay on the card.
**Anyone reading a result from this card must know the core gate is a ratified interpretation.**

**Standing instruction from Brake, recorded so it is not quietly ignored later:**
> *"Do NOT build or test the no-bias variant. If the bias requirement makes the event count too
> thin to test later, report that as a finding rather than relaxing the rule."*

**Q11 · target — RESOLVED BY THE EXIT LOCK, not by him.**
The locked convention fixes the target at **2R** for every card
(`EXIT-CONVENTION-LOCKED.md`). His own material never states a target for this model; the
first-opposing-swing reading from `[r5_yNjXsv6k @ 01:34]` is superseded and is no longer load-bearing.

### ⬛ SUPERSEDED — the 2026-08-07 "not answered" note

Brake's reply covered Q3, Q20, Q22 and the 10pt floor. **Q10 (bias) and Q11 (target) were not
addressed**, so the "don't know" protocol applies: record the most literal transcript reading with
the assumption stated, and do not guess silently.

**Q10 `[inferred]` — the literal reading does not resolve, because his two statements conflict:**
> *"You could literally make a model out of this alone and be profitable."* `[lRgsHGWzO9E @ 08:30]`
> — reads as **no additional condition**
> *"use good gaps. Don't use every random gap that you see."* `[dlSXQgM1ZpA @ 03:51]`
> — reads as **a selection criterion he never defines**

Taken at face value together, there **is** a selection rule and he does not state it. That is a
`[gap]`, not a resolution.

**Q11 `[inferred]`, assumption stated:** target the **first opposing swing point**, by analogy
with the trigger version — *"we aim for the first swing low which is 37 points"* `[r5_yNjXsv6k @ 01:34]`.
Under the locked convention this becomes **2R** regardless, so Q11 is no longer blocking on its
own. **Q10 still is.**

**Why this card cannot be greenlit.** Implemented literally — every 5m/15m inverse FVG with a
5-point stop — it produces **thousands of events a year with no directional condition**. That is
not a strategy; it is a coin flip with a tight stop, and testing it would consume a trial and
tell us nothing about him. **He rates this concept third and states it standalone three separate
times, so it is worth resolving — but it needs one answer first.**

**Verdict was INSUFFICIENT at the time of this note; superseded above.**

### ⬛ EXIT CONVENTION — LOCKED
Scored on the **identical** convention as `ash-unicorn-sb` so the trade logs pool:
**target = entry ± 2 × risk · break-even at 1R · no trailing · stop fills first on a same-bar
conflict · capped 16:00 ET · R signed by direction · costs reported separately ($25/round-turn).**
Full derivation and verification: `EXIT-CONVENTION-LOCKED.md`.
This card keeps its **own stop rule**, because the stop is what defines R.
**Powell's Apex-driven break-even and trailing, and his stated 1:4–1:6 band, remain
`[trader-claimed, unverified]` colour and are NEVER the scored exit.**

### 4 · VERDICT — **CONFIRMED** (rev b; was INSUFFICIENT at rev a)

**rev a verdict (retained):** *"Bias and targets are both [gap]… Not tradeable or testable as it
stands."*

**rev b verdict — CONFIRMED.** Both gaps are closed: **bias** by Brake `[stated-by-user]`, **target**
by the locked exit convention. Q12 (the standalone 5m/15m version is real and separate) and Q13
(inversion requires a close) were self-resolved from the transcript. **No open question remains.**

All seven parts now resolve:
| part | tag |
|---|---|
| bias source | **[stated-by-user]** — draw-aligned, via `COMPONENTS` §A |
| setup conditions | **[stated]** — 5m/15m inverse FVG, inverted **by a close** `[BOuJLWIisMI @ 04:39]` |
| entry trigger | **[stated]** — the 50% mark `[lRgsHGWzO9E @ 07:44]` |
| stop / invalidation | **[stated]** — 5 points `[@ 07:44]` |
| targets | **[locked]** — 2R, by the exit convention |
| risk / sizing | **[inferred]** — `COMPONENTS` §D/§E |
| avoid-filters | **[inferred]** — non-draw-aligned gaps excluded; this is the reading of *"use good gaps"* |

**Caveat that travels with the verdict:** Confirmed here rests on a **ratified interpretation of
the bias gate**, not on a rule Powell states. That is a weaker footing than
`zxck-10am-keyopen`, where every part is his.

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

### 2026-08-07 rev b — self-resolution, Brake's answers, exit lock
Prior rev-a numbers and tags are **retained above, not overwritten**. This revision adds:
the Step-1 self-resolution block, Brake's `[stated-by-user]` answers where given, the locked exit
convention (`EXIT-CONVENTION-LOCKED.md`), and a re-issued verdict.

### 2026-08-07 rev c — Brake's close-out answers
Prior revisions retained above, not overwritten.
