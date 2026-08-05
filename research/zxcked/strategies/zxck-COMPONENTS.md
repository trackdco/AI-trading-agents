---
date: 2026-08-07
kind: shared components — referenced by every zxck- card
trader: Powell
scope: POWELL TRADES MATERIAL ONLY. No PB-course content anywhere in this file.
---

# Powell — shared components

His corpus is one stack, not a set of independent strategies. The bias inputs, the entry-trigger
menu, the engineered-liquidity gate and the management rules are **common to every card**. They
live here so each card can state its own tags without eight copies of the same quote.

Source precedence throughout: **his own channel ("Powell trades") > re-hosted course > third
parties.** Third-party statements are never folded into his rules.

---

## A. BIAS STACK — the order is stated

> *"first thing I do is check daily… number one, daily PXL PXH… then I mark my key opens…
> number three, equal highs/lows without SMT… then higher timeframe market maker models… and
> last I look for 4-hour and 1-hour changes in state of delivery."* `[C6VSpegON80 @ 00:24–01:38]`

### A1 · PXH/PXL daily state machine — `[stated]`
| observation | expectation |
|---|---|
| daily candle closes **above** the previous day's high | the **next high** gets taken |
| closes **back below** a high after taking it | the **low** gets taken |
| closes **below** the previous day's low | the next **low** gets taken |
| bullish candle, ambiguous close | default to the **high** `[jBS22-pX3dU @ 03:31]` |

`[jBS22-pX3dU @ 00:23]`, restated identically 10 months later `[f0mYnZ9ISJY @ 01:36]`.
**Override:** an unfilled NWOG in the path beats the PXH/PXL expectation `[jBS22-pX3dU @ 04:46]`.

### A2 · Session extremes — `[stated] as a question, [gap] as a rule`
> *"If London high or low tapped into something significant or swept something significant, then
> your focus is going to be expanding away from that."* `[BFClqi7fDpk @ 04:51]`
**"Significant" is never defined.** See Q-B1.

### A3 · MMXM (V/A shape) — `[stated]`, bias only
> *"You need a strong pull point, you need a strong target, and then you just need to be able to
> identify this V-shape. If it's the opposite, it's going to be an A-shape."* `[asi9nTJywN4 @ 03:09]`
> *"This is just for my bias"* — entries come from LTF PD arrays `[@ 01:13]`.

### A4 · Unfilled NWOG/NDOG — `[stated]`, and sufficient on its own
> *"this new week opening gap is completely unfilled. So I was really confident we were going
> down. In terms of bias and confluences I don't really need much more if we have that."*
> `[AGmRZ9Te9NY @ 01:12]`

### A5 · Open proximity — `[stated]`
> *"when market opens, which daily high or low are we closest to? Which 4-hour? 1-hour? What are
> we most likely going to manipulate into? And what is the market expanding towards?"*
> `[f0mYnZ9ISJY @ 17:49]` — nearest untested extreme = manipulation target; far side = draw.

---

## B. THE GATE — engineered liquidity

**The one requirement present in nearly every video.**

> *"equal highs and lows is the best form of engineered liquidity… because there's a lot of stops
> above here."* `[rzfgAEYhxCg @ 04:51]`

### B1 · The distance rule — `[stated]`, and it is the only number in either trader's corpus
> *"if it's like two points or less away from the CE, I'll just not take it, because at that
> point I count the CE as already mitigated."* `[xae9AiV5Ps4 @ 02:16]`
> *"can it be too far away? Generally, not really… if the liquidity is inside of the rejection
> block, that's usually the sweet spot."* `[@ 02:40]`

**Band: > 2 points from the CE, ideally within the PD array's own range.**

### B2 · Unswept equal highs are a WAIT, not fuel — `[stated]`
> *"this is an example of a 5-minute rejection block that I would not take because we do have
> relative equal highs… this would actually have needed to sweep that liquidity for me to even
> consider taking this."* `[pMv3USznFdU @ 05:04]`

### B0 · AMD is the SHAPE of this gate, not a separate model — `[stated]`
> *"Watch either engineered liquidity or the AMD. **They are pretty much the same thing.**"*
> `[D-suu0f3XKI @ 02:17]`; *"Those are kind of the same concept."* `[-izOcim8KRQ @ 01:38]`

**Accumulation** (a range) → **manipulation** (a sweep of the range extreme against bias) →
**distribution** (delivery in the bias direction) `[EaxfhUS4eNg @ 00:46, 02:22, 03:57]`. This is
the shape every zxck- setup makes; `zxck-amd-pdarray` was withdrawn as a card on 2026-08-07
because carding it separately would double-count the same trades.

⚠️ **The range itself is never defined** — he draws boxes by eye. That gap blocks
`zxck-mmxm-breaker` (Q22) but no longer blocks anything else.

### B3 · The gate licenses a blind limit — `[stated]`
> *"entering straight at the level pretty much only is valid if you have this engineered
> liquidity."* `[BOuJLWIisMI @ 01:30]`
Consistent with *"the confirmation is to the left of the chart"* `[EaxfhUS4eNg @ 02:45]`.

---

## C. ENTRY-TRIGGER MENU — `[stated]`

> *"it's going to be either straight at the level, rejection block, change in state of delivery,
> or inverse fair value gap. And these are all on the one minute or three minute time frame."*
> `[r5_yNjXsv6k @ 02:20]`; the fib is named as a fifth `[@ 00:45]`.

| # | trigger | notes |
|---|---|---|
| 1 | **straight limit** | requires the B gate `[BOuJLWIisMI @ 01:30]` |
| 2 | **rejection block** | lower win rate, better RR `[tNyT7tHOmGI @ 05:46]` |
| 3 | **CISD** | close beyond a candle's open, retest that open |
| 4 | **inverse FVG 50%** | higher win rate, worse RR `[tNyT7tHOmGI @ 05:46]` |
| 5 | **fib** | 0.62 / 0.705 limits `[y7KMT9CIVMo @ 11:14]` |

### C1 · Trigger timeframe — `[stated]`, with a stated trade-off
> *"if you want even more confirmation, you can get five minute, but then you're going to lose a
> lot of entries or get slightly worse risk-to-reward, which is fine because your win rate is
> going to be higher."* `[r5_yNjXsv6k @ 02:43]`
> *"5-minute entry trigger is better than a 1-minute."* `[tNyT7tHOmGI @ 07:42]`
> *"Stop obsessing over the one minute time frame."* `[WEeXKMzaJjY @ 03:10]`
**Match the trigger timeframe to the level's timeframe** `[xae9AiV5Ps4 @ 05:18]`.

### C2 · When to use a trigger vs a limit — `[stated]`
> *"yesterday I used a one-minute entry trigger because we were so close to market open. So I
> just wanted some confirmation."* `[pMv3USznFdU @ 08:33]`

### C3 · The displacement rule — `[stated]`, his good/bad discriminator
> *"The good rejection blocks on the 5-minute, if you scale down into the 1-minute, you'll have
> this one big candle that gives you three entry triggers on lower time frame, all in one candle.
> And that is just called displacement."* `[pMv3USznFdU @ 06:39]`
Three inner conditions on ONE 1-minute candle: **rejection block + inverse FVG + CISD** `[@ 02:43]`.

### C4 · Edge tolerance — `[stated]`
> *"it hits 41, and the discount is at 40… I'm not really going to care… if you get edged by one
> point, scale down into the 1-minute and be like, am I getting a 1-minute reason to go long?"*
> `[y7KMT9CIVMo @ 03:32, 05:04]`
**A limit-only backtest understates his fill rate.**

### C5 · PD-array hierarchy by discount — `[stated]`
> *"rejection block is the most discounted one… CISDs are the second most discounted… and then
> you got IFVGs and then breakers."* `[asi9nTJywN4 @ 03:53]`
Ordering by **entry price**, not by win rate.

---

## D. STOP / SIZING — `[stated]`

### D1 · The governing rule
> *"when you guys ask how big should my stop loss be, I always say it depends on volatility,
> depends on the points of the range… that 5-minute wick is 20 points big. I can't do anything
> about that except adjust my risk."* `[xae9AiV5Ps4 @ 06:51]`
**Stop follows the PD array's own size. Position size absorbs the difference.**

### D2 · The floor
> *"for me five points is just minimum. I used to do crazy trades like two point stops, three
> point stops… I find five points is more than enough."* `[BOuJLWIisMI @ 03:28]`

### D3 · The migration — not a contradiction
> *"three point stop, not something I really like to do anymore… I used to do two to 10 point
> stops when I was broke because I couldn't handle losses."* `[AGmRZ9Te9NY @ 05:06]`
2025 videos: 2–5pt. 2026 videos: 10–20pt. **Test the later numbers.**

### D4 · Alternatives, both stated
- below the PD array, covering its **midpoint** — *"that is a sensitive point usually within
  every single PD array"* `[tNyT7tHOmGI @ 17:05]`
- below **fib 0.79 of the wick itself** — *"anything beyond that is overextended"* `[xae9AiV5Ps4 @ 08:03]`

---

## E. TARGETS & MANAGEMENT — `[stated]`

### E1 · The RR band
> *"don't take anything lower than one to three. 1 to 3 and up is pretty good for prop firms.
> 1 to 3 to 1 to 6 is the sweet spot for me… My personal lowest is like 1 to 4."* `[WEeXKMzaJjY @ 15:56]`
Corroborated 6 months earlier: *"1 to 3 minimum, preferably one to four"* `[rwPo6UyVOo8 @ 02:51]`.

### E2 · Target selection — `[inferred]`, a menu not a rule
> *"you just aim for some internal structure or a static RR. It's up to you."* `[a3LzCUZU5ko @ 06:18]`
Named in examples: first internal high/low, unfilled gaps, old lows, relative equal highs,
midnight/true day open, data highs/lows.

### E3 · Break-even
> *"I prefer to go break even because with these Apex accounts I have some pretty aggressive
> trailing drawdown."* `[5pL41Pl7GM4 @ 24:46]`
Trigger in examples: once the prior swing high/low is taken `[tNyT7tHOmGI @ 18:14]`.

### E4 · Trailing ladder — `[stated]`
1. after the trigger candle → trail to its low, or break-even `[rQUMdf1gLJk @ 00:50]`
2. on opposing LTF structure → below the last 1m/3m/5m order block `[@ 01:37]`
3. thereafter → to each validated swing low `[@ 02:00]`
> *"five minute structure is probably the best and safest way to trail your stop."* `[@ 06:30]`
**Driven by 14 prop accounts** `[@ 04:02]` — an account artefact, not a market claim.

### E5 · Daily limits — `[stated]`
> *"take max two losses a day, two to three trades per day, and stop."* `[tNyT7tHOmGI @ 10:23]`
Earlier version: *"if the first trade is a win then get off. If the first trade is a loss,
d-risk 50%; if that's a loss get off."* `[rwPo6UyVOo8 @ 02:51]`
**Two different daily rules 6 months apart. See Q-G1.**

### E6 · Session routine — `[stated]`
> *"I like to just go on the chart at 10 a.m. If there's news at 8:30, I'll trade a data high/low
> setup at 8:30 if it appears. If not, I'll look at 10 a.m."* `[Y-oqSZmNo4U @ 18:12]`
> *"I might take like three trades per week."* `[@ 17:05]`
Skips FOMC/Powell-testimony days `[xae9AiV5Ps4 @ 01:31]`.

---

## F. ⚠️ THE FIXED-TARGET PROBLEM — read before any backtest

His break-even (E3) and trailing (E4) are **explicitly Apex-driven**. Every R-multiple he quotes
is a **trailed or break-even'd exit**, not a fixed-target one. **A fixed-2R backtest is not
measuring the same thing as his numbers**, and any comparison to his claimed RRs must say so.

## G. What he never specifies — carried into the question lists

| gap | where it bites |
|---|---|
| *"tap into something significant"* | the precondition for every rejection block |
| *"original consolidation"* / the range | MMXM and AMD both hinge on it |
| manipulation-wick size | 2pt *"not sufficient"*, 10pt *"not very good"* `[5pL41Pl7GM4 @ 01:36, 02:46]`; threshold above 10, never named |
| target selection | a menu, never a rule (E2) |
| which fib leg | partly solved by the rebalance rule, still needs *"a reason"* |
