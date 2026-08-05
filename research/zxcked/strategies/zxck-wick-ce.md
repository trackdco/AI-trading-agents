---
id: zxck-wick-ce
name: Rejection block / wick CE
trader: Powell
prefix: zxck-
sessions: [New York AM]
instruments: [NQ, MNQ]
GAP_ENTRY: NO — the entry object is a wick, not an imbalance
NY_SESSION: YES
his_rank: "#1 — 'rejection blocks being number one' [Y-oqSZmNo4U @ 15:54]"
sources: [a3LzCUZU5ko, AGmRZ9Te9NY, D-suu0f3XKI, vWz5HvbuR-8, W_2x8Mv0-9M, 6opmiyFvJBA, wS-dBenAIlY, pMv3USznFdU, xae9AiV5Ps4, DhMaOkJaGYU, 9NDGx9MYuXw]
components: zxck-COMPONENTS.md
verdict: PARTIAL
---

# `zxck-wick-ce` — rejection block / wick CE

## Confirmation

### 1 · TEACH-BACK

I mark my levels before the session: key opens, unfilled opening gaps, HTF FVGs and order
blocks. My bias comes from the PXH/PXL state machine, refined by which extreme the session is
closest to. Then I wait for price to run **into** one of those levels and leave a **fat wick**
that closes back against itself — and critically, the candle has to **close in my direction**;
until that close there is no rejection block, only a wick. What makes it tradeable rather than
noise is that the wick **swept liquidity on its way in** and that there is **more liquidity still
resting beyond my level** — ideally equal highs/lows, more than 2 points away from the CE and
sitting inside the wick's own range — because that resting liquidity is the fuel for the move I
want. I place a limit at the **CE (the 50% of the wick)** and put my stop just beyond the wick's
extreme, sized to the wick itself rather than to a fixed point count: if the wick is 20 points I
accept a 20-point stop and cut size, and if it is 35 points I stop using the wick's origin
entirely and use the CE. If I want confirmation instead of a blind limit — and I do want it near
the open — I drop to the 1- or 5-minute and take a rejection block, CISD or inverse FVG inside my
level, preferring the 5-minute because the 1-minute manipulates me out. Before I commit I check
the wick is **not the beginning of an unfilled imbalance**, **not forming equal highs with a
swing point that hasn't been swept yet**, and that my draw hasn't already been reached. I target
internal structure — the first opposing high/low, an unfilled gap, a key open — for at least 1:3
and usually 1:4–1:6, move to break-even once the prior swing is taken, and trail below 5-minute
structure. Two losses and I am done for the day.

### 2 · SEVEN-PART COMPLETENESS CHECK

| part | tag | evidence |
|---|---|---|
| **bias source** | **[stated]** | PXH/PXL then session extremes then MMXM `[C6VSpegON80 @ 00:24–01:38]`; and *"a third thing is bias — you have to have a bearish target"* `[vWz5HvbuR-8 @ 05:40]` |
| **setup conditions** | **[stated]** | *"It has to tap into something, sweep something. If it does both, then great. And then the most important part of it all… this engineered liquidity"* `[vWz5HvbuR-8 @ 05:16]`; the candle-close requirement `[a3LzCUZU5ko @ 01:34]`; the >2pt distance rule `[xae9AiV5Ps4 @ 02:16]` |
| **entry trigger** | **[stated]**, but as a **menu of three** | CE / start-of-wick / 25%: *"you can either use the CE or the 50%, or you can just enter on the beginning of the wick. That's kind of up to you"* `[6opmiyFvJBA @ 08:13]`; 25% `[WEeXKMzaJjY @ 10:49]`. **Which one is a stated choice, not a rule — see Q-A1** |
| **stop / invalidation** | **[stated]** | *"stop loss at the high or low of the rejection block"* `[a3LzCUZU5ko @ 06:18]`; sized to the array `[xae9AiV5Ps4 @ 06:51]`; alternatives at the PD-array midpoint `[tNyT7tHOmGI @ 17:05]` and fib 0.79 of the wick `[xae9AiV5Ps4 @ 08:03]` |
| **targets** | **[inferred]** — a menu, never a rule | *"aim for some internal structure or a static RR. It's up to you"* `[a3LzCUZU5ko @ 06:18]`; band 1:3 min, 1:4–1:6 `[WEeXKMzaJjY @ 15:56]` |
| **risk / sizing** | **[stated]** | 5pt floor `[BOuJLWIisMI @ 03:28]`; fixed dollar risk with size absorbing stop width `[xae9AiV5Ps4 @ 06:51]`; max 2 losses/day `[tNyT7tHOmGI @ 10:23]` |
| **avoid-filters** | **[stated]** | not the start of an unfilled imbalance `[W_2x8Mv0-9M @ 00:52]`; not equal highs/lows formed by **swing** points `[@ 06:34]`; unswept equal highs = wait `[pMv3USznFdU @ 05:04]`; never against the draw `[W_2x8Mv0-9M @ 04:37]` |

**No part is [gap].** The weakness is that two parts are menus rather than rules.

### 3 · ASK ME

**Q-A1 · Which of the three entry points is the default — CE, start of wick, or 25%?**
- *Best guess from the transcript:* **CE by default**, dropping to start-of-wick only when the
  wick is small enough that the CE stop would be under his 5-point floor, and to 25% when the CE
  would get edged. Evidence for CE: *"The CE is often times going to be the best option"*
  `[pMv3USznFdU @ 01:33]`, and he says to use the CE when *"the risk is too much"*
  `[6opmiyFvJBA @ 08:13]`. Evidence against a clean rule: in his own biggest trade he used the
  **start** `[tNyT7tHOmGI @ 16:41]`, and he says *"I usually just take the closest entry, and I
  take the bigger risk"* `[5pL41Pl7GM4 @ 24:25]`.
- *Why it matters:* it changes **fill rate and stop size on every single trade**. Start-of-wick
  fills more often with a bigger stop; CE fills less often with a smaller stop. It is the largest
  single driver of the backtested result and I cannot pick it for you without inventing his rule.
- *Answerable from method?* **Yes** — you'd know which he actually defaults to.

**Q-A2 · Does the wick have to sweep liquidity, or is tapping a PD array enough?**
- *Best guess:* **either alone is acceptable, both is better.** *"It has to tap into something,
  sweep something. If it does both, then great"* `[vWz5HvbuR-8 @ 05:16]` reads as an OR. But
  `a3LzCUZU5ko @ 02:24` describes sweep-plus-close as the **minimum** tier and adds the PD array
  as the upgrade, which reads as sweep being mandatory.
- *Why it matters:* this is the **event-count gate**. Requiring both could cut candidate setups
  by more than half and decide whether the strategy clears our n≥30 floor at all.
- *Answerable from method?* **Yes.**

**Q-A3 · Does "engineered liquidity beyond the CE" mean beyond the CE, or beyond the wick's extreme?**
- *Best guess:* **beyond the CE but inside the wick's range** — *"if the liquidity is inside of
  the rejection block, from here to here, that's usually the sweet spot"* `[xae9AiV5Ps4 @ 02:40]`,
  combined with the >2pt rule. So: between CE+2pts and the wick's tip.
- *Why it matters:* it is the **primary filter**. Read one way it fires often; read the other way
  it is rare. Everything downstream depends on it.
- *Answerable from method?* **Yes**, or re-watch `xae9AiV5Ps4 @ 02:16–03:03` — that is the only
  place he addresses it.

**Q-A4 · Is the displacement rule (C3) a REQUIREMENT or just a quality tell?**
- *Best guess:* **a quality tell, not a gate.** He introduces it as *"how you can differentiate
  between what's a good one and what's a bad one"* `[pMv3USznFdU @ 06:39]` and never says to skip
  a setup that lacks it.
- *Why it matters:* as a gate it is the sharpest mechanical filter in either trader's corpus
  (one 1-minute candle that is simultaneously a rejection block, an inverse FVG and a CISD). As a
  tell it is descriptive and untestable as written. **This is the highest-value question in the
  whole set** — it decides whether we can implement his own good/bad discriminator.
- *Answerable from method?* **Probably**, otherwise re-watch `pMv3USznFdU @ 06:39–07:24`.

**Q-A5 · Does the third-party "draw already taken" disqualifier apply to his version?**
- *Best guess:* **yes, in spirit.** He says *"don't trade away from the draw"*
  `[W_2x8Mv0-9M @ 04:37]` and *"we hit the draw, so you're now bullish… that's why you don't
  short this"* `[38YtF6xFX4o @ 06:08]`. But the sharp form — *"if we go straight down to where
  your TP would be before filling that rejection block… your main draw was already taken out"*
  — is from a **third party** `[9NDGx9MYuXw @ 02:41]`, not from him.
- *Why it matters:* it is a cheap, mechanical kill-filter. I will not put a third party's rule in
  his card without your say-so.
- *Answerable from method?* **Yes.**

### ⬛ SELF-RESOLVED 2026-08-07 — Q1, Q2, Q4, Q5 closed from the transcripts
Full evidence: `SELF-RESOLVED-2026-08-07.md`.
- **Q1 → entry defaults to the START of the wick**; CE only when that stop would exceed ~20pt
  `[6opmiyFvJBA @ 08:40]`, `[tNyT7tHOmGI @ 06:09, 16:41]` `[inferred]`
- **Q2 → sweep + directional close is MANDATORY**; the PD array is the upgrade `[a3LzCUZU5ko @ 02:24-03:34]` `[stated]`
- **Q4 → displacement is a TELL, not a gate** — it tells you *where* to enter inside the block `[pMv3USznFdU @ 07:24]` `[stated]`
- **Q5 → draw already taken KILLS the setup and flips bias** `[38YtF6xFX4o @ 06:08]` `[stated]` — Powell's own words, so the third-party version is corroborated and usable
- **NEW stop band** `[5pL41Pl7GM4 @ 06:55, 10:59, 14:31, 16:42]`: prefer **5-7pt**, accept **<20pt**, reject **25pt+** `[stated]`

**Still open: Q3 only.**

### ⬛ FOLDED IN 2026-08-07 — Brake's answers

**Q3 · which side the engineered liquidity sits — `[stated-by-user]`: let the best reading ride.**
> *"his own two statements genuinely contradict each other on the liquidity side, and there's no
> point resolving a contradiction for a card you're deprioritizing. Let the best reading ride,
> tagged inferred, and leave the card Partial."*

**Recorded reading `[inferred]`, with the assumption stated:** the engineered liquidity sits
**between the entry and the wick's extreme** — liquidity the wick sweeps on its way into the
level, still resting when the entry fills. Basis: `[xae9AiV5Ps4 @ 02:40]` (*"if the liquidity is
inside of the rejection block"*) plus the >2pt minimum `[@ 02:16]`.
**The contradicting statement is NOT discarded:** `[wS-dBenAIlY @ 01:11]` places it *"right below
this CE"* on a short, which is the opposite side. **Unresolved by design.** Any result on this
card carries the reading as an assumption, not as his rule.

**Card remains PARTIAL — by instruction, not by omission.** It is his #1 model but it is **not a
gap entry**, so it does not serve the pooling goal; its prominence is deliberately not being
allowed to pull priority.

### ⬛ EXIT CONVENTION — LOCKED
Scored on the **identical** convention as `ash-unicorn-sb` so the trade logs pool:
**target = entry ± 2 × risk · break-even at 1R · no trailing · stop fills first on a same-bar
conflict · capped 16:00 ET · R signed by direction · costs reported separately ($25/round-turn).**
Full derivation and verification: `EXIT-CONVENTION-LOCKED.md`.
This card keeps its **own stop rule**, because the stop is what defines R.
**Powell's Apex-driven break-even and trailing, and his stated 1:4–1:6 band, remain
`[trader-claimed, unverified]` colour and are NEVER the scored exit.**

### 4 · VERDICT — **PARTIAL**

Tradeable today. Every one of the seven parts is [stated] or cleanly [inferred] — but **Q-A1 and
Q-A3 change the trade materially**, and Q-A4 decides whether his best filter is implementable.
Not Confirmed until those are answered.

---

## Edge thesis
A wick that runs into a level and closes back against itself marks where a passive participant
defended price. Because the entry is at the wick's midpoint rather than at its origin, the stop
is small relative to the move, which is where the risk-reward comes from — *"the more premium or
discount your entry is, obviously you're going to get a higher risk reward"* `[6opmiyFvJBA @ 05:03]`.
He also gives a behavioural story — traders who swept the level close at break-even and the
rejection block is where that happens `[@ 05:29]` — which is `[inferred by him]` and not testable
from price.

## Market context / bias
See `zxck-COMPONENTS.md` §A. Bias must have a **target on the other side**: *"you have to have a
bearish target, otherwise price wouldn't have gone down"* `[vWz5HvbuR-8 @ 05:40]`.

## Setup — conditions that must be present
1. Price runs **into** a level (key open, FVG, order block, opening gap, fib level) `[a3LzCUZU5ko @ 03:12]`
2. It leaves a **fat wick** rejecting that level `[@ 00:47]`
3. **The candle CLOSES in the trade's direction** — *"it's not a rejection block until this candle
   closes… that's going to give me actual bearish confirmation"* `[AGmRZ9Te9NY @ 02:47]`
4. The wick **swept liquidity** on the way in `[vWz5HvbuR-8 @ 05:16]`
5. **Engineered liquidity rests beyond the CE**, >2 points away, ideally inside the wick's range
   `[xae9AiV5Ps4 @ 02:16]`

> ⚠️ **This is NOT the ICT rejection block.** He rejects that definition explicitly: *"ICT might
> teach it with it being the last up close candle. I don't really care."* `[AGmRZ9Te9NY @ 03:11]`

## Entry trigger
Limit at the **CE**, or the **start of the wick**, or the **25%** — see Q-A1. Two ticks of offset
is his habit `[vWz5HvbuR-8 @ 02:54]`. If not limiting, use a 1m/3m/5m trigger inside the level
(`COMPONENTS` §C), preferring 5-minute.

## Stop / invalidation
Just beyond the wick's extreme; or covering the PD-array midpoint; or below fib 0.79 of the wick.
Sized to the wick, floor 5 points. See `COMPONENTS` §D.

## Targets / management
1:3 minimum, 1:4–1:6 typical. Internal structure, unfilled gaps, key opens. Break-even on the
prior swing being taken; trail below 5-minute structure. See `COMPONENTS` §E, and §F on why a
fixed-target backtest is not measuring his numbers.

## Filters / avoid conditions
- ❌ the wick begins an **unfilled imbalance** on any timeframe `[W_2x8Mv0-9M @ 00:52]`
- ❌ the wick forms **equal highs/lows with a swing point** `[@ 06:34]` — random intraday equal
  highs do not disqualify `[@ 06:08]`
- ❌ **unswept** relative equal highs sit above `[pMv3USznFdU @ 05:04]`
- ❌ trading **away from the draw** `[W_2x8Mv0-9M @ 04:37]`
- ❌ the wick is **35 points or more** for a start-of-wick entry `[pMv3USznFdU @ 01:09]`
- ✅ **SMT at the wick** raises probability `[W_2x8Mv0-9M @ 03:17]` — needs ES, which we lack

## Performance claims — all `[trader-claimed, unverified]`
- *"you can lose nine out of 10 times and still be super profitable"* `[wS-dBenAIlY @ 05:17]`
- a 2-point stop to true day open = *"a 25 RR"* `[@ 04:03]`
- a student *"made $12,000 in his Express account"* using only this `[dlSXQgM1ZpA @ 03:04]`
- *"this is one of the models that I used"* to produce his posted payouts `[a3LzCUZU5ko @ 06:41]`

## Contradictions / open questions
1. **Equal highs — fuel or disqualifier?** Resolved by him: unswept = wait, swept = fuel
   `[pMv3USznFdU @ 05:04]`. The third-party framing `[9NDGx9MYuXw @ 01:32]` describes the
   pre-sweep state. Recorded; no action needed.
2. **Stop sizes 2pt (2025) vs 20pt (2026).** Resolved by him — account-size migration
   `[AGmRZ9Te9NY @ 05:06]` under a scale-to-the-array rule `[xae9AiV5Ps4 @ 06:51]`.
3. **Q-A1 / Q-A3 / Q-A4 remain open.**

## Revision log
- **2026-08-07 rev a** — built from 11 sources across his own channel, the re-hosted course and
  two third parties. Verdict PARTIAL pending Q-A1 to Q-A5.

### 2026-08-07 rev b — self-resolution, Brake's answers, exit lock
Prior rev-a numbers and tags are **retained above, not overwritten**. This revision adds:
the Step-1 self-resolution block, Brake's `[stated-by-user]` answers where given, the locked exit
convention (`EXIT-CONVENTION-LOCKED.md`), and a re-issued verdict.


---

## ⬛ GATE CHECK 2026-08-07 — **n = 38, runnable**

`scripts/zxck_wick_gate.py` — counts only, no power spent. Window 09:45–10:15 ET
`[stated-by-user]`, span 2025-06-01 → 2026-07-15.

The full stack — ≥10pt wick → closes against its own wick → swept a prior swing extreme →
engineered liquidity >2pt beyond the CE → price returns to the CE — yields **38 events
(17 in 2025, 21 in 2026)**.

**Clears the n≥30 floor overall; thin per era.** No threshold was relaxed to get there.

⚠️ The **10pt wick floor is OURS by extension** `[A]` — he gives no size threshold for a
rejection wick, so the only quantified wick guidance in his corpus (the key-open manipulation
floor) was reused. It barely binds: 249 of 266 sessions pass it. The binding gates are the
**sweep** (231→96) and the **engineered liquidity** (96→47).

**This card, not `zxck-gap-fill-edge`, is the runnable one.** The far-edge entry reaches only
n=12 because an FVG is present at just 15 of 47 qualifying wicks.

**Still PARTIAL — Q3 unresolved by instruction**, and any baseline carries the
inside-the-wick liquidity reading as a tagged `[inferred]` assumption.
