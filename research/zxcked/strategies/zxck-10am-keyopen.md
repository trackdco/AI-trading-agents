---
id: zxck-10am-keyopen
name: 10:00 ET key-open limit
trader: Powell
prefix: zxck-
sessions: [New York AM — 10:00 ET]
instruments: [NQ, MNQ]
GAP_ENTRY: YES — the PD array at the open is usually a 5m/15m FVG; pools with ash-unicorn-sb
NY_SESSION: YES — and it sits INSIDE ash10hazard's AM1 window (09:45–10:15)
his_rank: "#2 — 'key opens being number two' [Y-oqSZmNo4U @ 15:54]"
sources: [Y-oqSZmNo4U, 38YtF6xFX4o, rsbBubev4PM, 5pL41Pl7GM4, 4COROwkO3DI, WEeXKMzaJjY, tNyT7tHOmGI, 55KRVFLqzwA, C6VSpegON80]
components: zxck-COMPONENTS.md
verdict: PARTIAL
---

# `zxck-10am-keyopen` — the 10:00 ET key-open limit

## Confirmation

### 1 · TEACH-BACK

At 10:00 ET the 4-hour candle opens, and I mark that opening price as a horizontal line — that is
the whole level. The reason I care is a base rate he states outright: roughly 97% of 4-hour
candles carry a wick on **both** sides of their open, so I should expect the market to push one
way off 10:00 and then manipulate back through it before the real move. So I don't chase the
first move; I wait for the manipulation leg to trade **through** the open, and I want that leg to
be a real one — a 2-point poke is not manipulation and 10 points is marginal. Once price has
manipulated, I want to re-enter the open from the other side, and I only take it if the open
**coincides with something** — a 5- or 15-minute FVG, an order block, or the 10:00 candle's own
open acting as an order block — and if the fib on the current unbalanced leg puts that level in
premium (0.79 for a short) or discount (0.5/0.62 for a long). I draw that fib from the most
recent high whose leg has **not** already been 50% rebalanced, which is the rule that stops me
anchoring it wherever I like. Entry is a limit at the open, stop 10–15 points (wider if the
volatility demands it), and I target the first internal opposing high or low — typically 1:4 to
1:6. If instead price rallies off 10:00 with **no** manipulation below it, I flip the level's
role: longs are out and the open itself becomes my target. I check the chart at 08:30 only if
there is CPI/PPI/NFP, otherwise I sit down at 10:00 and take roughly three trades a week.

### 2 · SEVEN-PART COMPLETENESS CHECK

| part | tag | evidence |
|---|---|---|
| **bias source** | **[stated]** | PXH/PXL and open proximity `[f0mYnZ9ISJY @ 17:49]`; and 10:00's own open direction: *"10:00 opens lower… all we want with 10 a.m. is a lower wick, so that we can distribute to the upside"* `[tNyT7tHOmGI @ 15:08]` |
| **setup conditions** | **[stated]** | the level is the 4H candle open `[Y-oqSZmNo4U @ 00:49]`; the both-wicks mechanism `[@ 01:15]`; must coincide with a PD array `[@ 03:15]`; must land on a fib level `[@ 04:49]` |
| **entry trigger** | **[stated]** | *"I want to have a short limit at this 10 a.m. key open"* `[Y-oqSZmNo4U @ 05:12]`; or the first 5-minute trigger after the open `[WEeXKMzaJjY @ 14:21]` |
| **stop / invalidation** | **[stated]** | *"I could get away with a 10 to 15 point stop… or a static 10 to 15 point stop"* `[Y-oqSZmNo4U @ 06:20]`; 27pt conservative `[@ 07:52]`; 15pt covering the PD-array midpoint `[tNyT7tHOmGI @ 17:05]` |
| **targets** | **[stated]** for this card | *"a conservative target of this first internal low… a 6.6 RR, which is typically what I would go for. I go for everything from 1 to 4 to 1 to 6"* `[Y-oqSZmNo4U @ 06:46]` |
| **risk / sizing** | **[stated]** | see `COMPONENTS` §D/§E; *"three trades per week"* `[Y-oqSZmNo4U @ 17:05]` |
| **avoid-filters** | **[stated]** | insufficient manipulation `[5pL41Pl7GM4 @ 01:36]`; no manipulation below ⇒ don't long, target the open `[Y-oqSZmNo4U @ 19:52]`; *"nothing really makes that much sense"* when 10:00 manipulates both sides `[xae9AiV5Ps4 @ 09:16]`; skips FOMC days `[@ 01:31]` |

**No part is [gap]** — this is the best-specified model in his corpus. The open questions are
threshold values, not missing rules.

### 3 · ASK ME

**Q-B1 · How big must the manipulation wick be to count?**
- *Best guess:* **more than 10 points on NQ**, and probably scaled to the day's range rather than
  fixed. Direct evidence: a **2-point** wick — *"Do we see that as sufficient? No"*
  `[5pL41Pl7GM4 @ 01:58]`; a **10-point** wick — *"Is this better? Yes. Is it very good? No"*
  `[@ 02:46]`. He never states a number above that.
- *Why it matters:* **this is the gate that decides whether a day produces a setup at all.** Set
  it at 2 points and nearly every day qualifies; at 20 points, few do. It directly determines
  event count and therefore whether we clear the n≥30 floor.
- *Answerable from method?* **Partly.** If you don't know a number, the fallback I'd propose is
  scale-free: manipulation ≥ some fraction of the prior session's range or of ATR. **That would
  be OUR rule, not his**, and I'd tag it accordingly.

**Q-B2 · Does the entry require price to RE-CROSS the open after manipulating, or just to return to it?**
- *Best guess:* **return to it, from the manipulated side.** In the worked trade 10:00 opens
  lower, wicks down 20 points, distributes up, and he wants *"the retrace to come down and retest
  10:00"* `[tNyT7tHOmGI @ 15:56]` — a return, not a re-cross.
- *Why it matters:* decides whether the entry is a **retest** (fills often, larger stop) or a
  **re-cross-and-return** (rarer, tighter). Changes both trade count and stop geometry.
- *Answerable from method?* **Yes.**

**Q-B3 · Is the fib coincidence mandatory or a bonus?**
- *Best guess:* **mandatory in the 2026 material, optional in 2025.** He calls the fib *"not a
  strategy… a confluence"* `[tNyT7tHOmGI @ 02:23]`, yet in every 2026 worked example the key open
  landing on 0.5/0.62/0.79 is presented as the thing that validates the entry
  `[Y-oqSZmNo4U @ 05:12, 11:11]`.
- *Why it matters:* mandatory turns this into a two-condition setup and cuts event count sharply;
  optional leaves it a one-condition level trade. Also decides whether we must implement the fib
  re-anchoring rule at all.
- *Answerable from method?* **Yes.**

**Q-B4 · Which 10:00 — the 4-hour candle open, or the 10:00 price on a lower timeframe?**
- *Best guess:* **the same number either way**, since the 4H candle opens at 10:00 ET; he says
  *"easiest ways to mark them is just go on the 1 hour time frame"* `[Y-oqSZmNo4U @ 08:40]`.
  I flag it only because DST could break the identity if the 4H boundary is exchange-time.
- *Why it matters:* if the 4H grid is anchored elsewhere (e.g. 18:00 CT), the 10:00 ET candle is
  **not** a 4H open and his stated mechanism doesn't apply. Cheap to get wrong, cheap to confirm.
- *Answerable from method?* **Yes** — you'd know his chart's session/timezone settings.

**Q-B5 · Is the ~97% both-wicks claim about ALL 4-hour candles, or only the 10:00 one?**
- *Best guess:* **all of them.** *"if you look at all these candles on the 4-hour time frame,
  what do they all have in common? They all have wicks on the top and on the bottom. Like 97% of
  them do at least."* `[Y-oqSZmNo4U @ 01:15]`
- *Why it matters:* if it's a universal property of 4H candles, it is **not evidence for 10:00
  specifically** — the mechanism would apply equally to 06:00, 14:00 and 18:00, and the case for
  10:00 rests only on it being the NY AM session. That would change what the strategy is.
- *Answerable from method?* **This one I can just measure** — it's a base rate on data we hold and
  costs no selection budget. I'd run it before anything else, unless you'd rather I didn't.

### 4 · VERDICT — **PARTIAL**

The best-specified model in the corpus and the closest competitor to `ash-unicorn-sb`. All seven
parts are [stated]. It is Partial only because **Q-B1 has no number** and Q-B2/Q-B3 change the
event count by a large factor. Q-B5 is measurable by us.

---

## Edge thesis
10:00 ET is the 4-hour candle open. He claims ~97% of 4H candles wick both sides of their open,
so the open will be traded through in both directions before the session's real move — which
makes it a level the market is very likely to revisit, with a small stop
`[Y-oqSZmNo4U @ 01:15–01:40]`. The same argument is made for midnight at ~95% `[@ 14:17]`.
**Both figures are `[trader-claimed, unverified]` and both are directly measurable by us.**

## Market context / bias
`COMPONENTS` §A, plus the open's own behaviour: opens lower + lower wick ⇒ expect distribution
up `[tNyT7tHOmGI @ 15:08]`; strong close through the level then a return `[38YtF6xFX4o @ 03:45]`;
*"you need context with everything"* `[@ 10:59]`.

## Setup — conditions that must be present
1. Mark the **10:00 ET opening price** `[Y-oqSZmNo4U @ 02:25]`
2. A **manipulation leg through it** — sufficient in size (Q-B1) `[5pL41Pl7GM4 @ 01:36]`
3. The open **coincides with a PD array** — 5m/15m FVG, order block, or the 10:00 candle's own
   open acting as one `[Y-oqSZmNo4U @ 03:15]`, `[5pL41Pl7GM4 @ 19:57]`
4. The open lands on a **fib level** of the unbalanced leg (Q-B3) `[Y-oqSZmNo4U @ 04:49]`

### The fib anchoring rule — `[stated]`, and it removes the main discretion
> *"These little legs are constantly getting rebalanced… this leg has already rebalanced to 50%.
> That's a new leg now, I can't use that fib in the same area anymore… So where I would have to
> actually draw the fib would be this high, because this high we have not rebalanced anywhere."*
> `[Y-oqSZmNo4U @ 09:30–10:43]`
**Anchor to the most recent high/low whose leg is not yet 50% rebalanced.**

## Entry trigger
Limit at the open `[Y-oqSZmNo4U @ 05:12]`, or the **first 5-minute trigger after 10:00**
`[WEeXKMzaJjY @ 14:21]`. Entering before 10:00 is permitted with conviction `[5pL41Pl7GM4 @ 27:29]`.

## Stop / invalidation
**10–15 points** `[Y-oqSZmNo4U @ 06:20]`; 27 for the conservative version `[@ 07:52]`; 15 to cover
the PD-array midpoint `[tNyT7tHOmGI @ 17:05]`. He warns the level is inside the most volatile
session and that 10–15 points is sometimes simply wrong `[Y-oqSZmNo4U @ 07:29]`.

## Targets / management
First internal opposing high/low; 1:4–1:6 `[Y-oqSZmNo4U @ 06:46]`. **The inverted case:** if the
open was never manipulated through, it becomes the **target** instead of the entry `[@ 14:41, 19:52]`.

## Filters / avoid conditions
- ❌ manipulation wick too small (Q-B1)
- ❌ 10:00 manipulates **both** sides ⇒ no read `[xae9AiV5Ps4 @ 09:16]`
- ❌ FOMC / Powell-testimony sessions `[@ 01:31]`
- ❌ Mondays and holiday weeks — `[inferred]` from repeated skipping `[5pL41Pl7GM4 @ 02:23, 29:06]`, never stated as a rule
- ✅ 08:30 instead of 10:00 **only** on CPI/PPI/NFP `[Y-oqSZmNo4U @ 18:12]`

## Performance claims — `[trader-claimed, unverified]`
- *"pretty much all of these days, if you just soup the 10:00 key open into a rejection block or
  one other PD array, you would have gotten a juicy take profit"* `[5pL41Pl7GM4 @ 25:30]`
- the traded example: entry ~485, 15pt stop, target 605 ⇒ **1:8**, $1,200 × 10 Apex accounts
  `[tNyT7tHOmGI @ 17:27, 15:30]`
- *"you can get some pretty gnarly win rates with this"* `[Y-oqSZmNo4U @ 16:43]`

## ⚠️ Overlap with `ash-unicorn-sb`
**Same instrument, same half hour, incompatible entries.** ash10hazard enters the near edge of an
FVG after sweep + MSS with a ~25pt median stop; Powell limits the 10:00 open with a 10–15pt stop.
Neither spec was written with the other in mind, so this is a genuine A/B. Both are blocked on
the same missing **ES** data.

## Revision log
- **2026-08-07 rev a** — built from 9 sources, 4 of them his own channel. PARTIAL pending Q-B1 to Q-B5.
