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
verdict: CONFIRMED
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

### ⬛ SELF-RESOLVED 2026-08-07 — Q6, Q7, Q8, Q9 ALL closed
Full evidence: `SELF-RESOLVED-2026-08-07.md`. **This card has no open questions left.**
- **Q6 → manipulation wick >=10pt acceptable, >=15pt good, <=8pt not.** Four labelled examples:
  2pt *"No"* `[5pL41Pl7GM4 @ 01:58]`; 8pt *"gray area"* `[@ 09:26]`; 10pt *"you can clearly see
  that's a wick"* `[@ 10:10]`; 15pt *"Yes"* `[@ 05:50]` `[inferred]`
  ⚠️ **ASSUMPTION: fixed 10pt floor, NOT ATR-scaled.** He never addresses scaling. An ATR version
  would be OUR rule.
- **Q7 → RETEST**: manipulate through -> move away -> return `[tNyT7tHOmGI @ 15:56]` `[stated]`
- **Q8 → fib is a BONUS**, the 10:00 framework is the only requirement `[tNyT7tHOmGI @ 16:19]` `[stated]`
- **Q9 → 10:00 ET IS a 4H open** on an 18:00-ET (CME session) grid: 18/22/02/06/**10**/14. A
  midnight grid gives 00/04/08/12/16/20 and would not. He names 18:00 as a key open too
  `[38YtF6xFX4o @ 00:00]` `[inferred, arithmetically self-consistent]`

### ⬛ CONFIRMED 2026-08-07
ALL FOUR questions closed by self-resolution (Q6, Q7, Q8, Q9). No question on this card remains open.

Brake also ratified the **fixed 10-point manipulation floor** as his rule:
> *"keep the 10pt floor as a fixed point value like he stated it — that's his rule. The
> ATR-scaled version the agent flagged is a separate hypothesis for later, not a substitute now."*
`[stated-by-user]`

**Exit is now the locked convention** — see `EXIT-CONVENTION-LOCKED.md`: target 2R, break-even at
1R, no trailing, stop-first on a same-bar conflict, capped 16:00 ET, costs reported separately.
Identical to `ash-unicorn-sb`, so the trades pool. **His own 1:4–1:6 band and Apex-driven trailing
stay on this card as `[trader-claimed, unverified]` and are NOT scored.**

### 4 · VERDICT — **CONFIRMED**

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

### 2026-08-07 rev b — self-resolution, Brake's answers, exit lock
Prior rev-a numbers and tags are **retained above, not overwritten**. This revision adds:
the Step-1 self-resolution block, Brake's `[stated-by-user]` answers where given, the locked exit
convention (`EXIT-CONVENTION-LOCKED.md`), and a re-issued verdict.


---

## RAW BASELINE — 2026-08-07 (rev c)

`scripts/zxck_keyopen_baseline.py` · trades `zxck-10am-keyopen-raw-trades.csv` (480 rows, all
sessions logged with skip reasons)

### ⚠️ WINDOW CORRECTION — my error, caught by Brake
rev-a of this card left the window unstated; my first mechanization used **10:00–14:00 ET** (the
4-hour candle) as an assumption. That **violated Brake's standing instruction** — *"from here
onwards we only will stick to 9:45–10:15 macro"* — and broke like-for-like comparison with
`ash-unicorn-sb`, which is scored on a 30-minute window with a hard 10:15 cutoff.
**Corrected to 10:00–10:15 ET**, the honest intersection of his level and that macro.
The 240-minute run is retained below only as a robustness check.

### Spec
NQ 1-min · **10:00–10:15 ET** · 2025-01-01 → 2026-07-15 · 480 sessions (396 real; 84 are 79
Sundays + 5 holidays) · exit = the locked convention, identical to `ash-unicorn-sb`.

### Result

> ### ⚠️ 2026-08-07 — SAME-BAR FILL-AND-STOP FIXED. Every number here moved by −5.0R.
> The exit walk started at the bar *after* the fill, so a minute that filled the limit **and**
> traded through the stop was carried forward as a live trade. **24 of the 146 fill bars were
> already through the stop; 3 trades were scored wrongly** — 2025-05-05 and 2026-01-30 as BE
> when they were losses, and **2026-02-19 as a +2R win when it was −1R**. Total error **−5.0R,
> −0.034R/trade**. R11 always said stop-first on a same-bar conflict; the code now obeys it.
> This makes the card **worse**, and it does not change the verdict — which was already *the
> null*.

| | corrected | ~~before the fix~~ |
|---|---|---|
| n | **146** | 146 |
| win / BE / loss | **37 / 33 / 76** | ~~38 / 35 / 73~~ |
| **win rate** | **25.3%** | ~~26.0%~~ |
| avg R | **−0.014** | ~~+0.021~~ |
| cost | 0.083R/trade (15pt stop) | 0.083R |
| **expectancy** | **−0.097R net** | ~~−0.063R~~ |
| total | **−2.0R gross / −14.2R net** | ~~+3.0R / −9.2R~~ |
| **max drawdown** | **18.0R** | ~~18.0R~~ |
| direction | 75 long / 71 short | 75 / 71 |
| flow-covered | **115 / 146** (computed, **not applied**) | 115 / 146 |

| era | n | WR | avg R | total |
|---|---|---|---|---|
| 2025 | 95 | 22.1% | −0.095 | −9.0R |
| 2026 | 51 | 31.4% | +0.137 | +7.0R |

### ⚠️ THE RESULT IS THE NULL, EXACTLY

A 2R target with break-even at 1R has a known random-walk signature: **25% win / 25% BE / 50%
loss** (reach +1R before −1R with p≈0.5, then +2R before entry with p≈0.5).

| | win | BE | loss |
|---|---|---|---|
| random-walk expectation | 25.0% | 25.0% | 50.0% |
| **observed** | **26.0%** | **24.0%** | **50.0%** |

**There is no detectable edge.** The setup selects *when* to be in the market; it does not appear
to select *which way price goes*.

### Robustness — the conclusion does not depend on the open questions

| variant | n | win | BE | loss | expectancy |
|---|---|---|---|---|---|
| **10:00–10:15, scan includes the 10:00 bar** (locked) | 146 | 26.0% | 24.0% | 50.0% | −0.063R |
| 10:00–10:15, scan starts 10:01 | 159 | 25.2% | 22.6% | 52.2% | −0.102R |
| 10:00–14:00, includes the 10:00 bar | 218 | 24.8% | 24.3% | 50.9% | −0.089R |
| 10:00–14:00, starts 10:01 | — | — | — | — | — |

**The A/B manipulation-bar question I raised as a blocker turns out not to matter** — both
readings land on the null, and so does the wrong window. The blocker is therefore withdrawn: it
was a real ambiguity, but not one that changes the answer.

### Comparison to his claims — directional only
He claims *"pretty much all of these days… you would have gotten a juicy take profit"*
`[5pL41Pl7GM4 @ 25:30]` and a 1:4–1:6 working band `[WEeXKMzaJjY @ 15:56]`, on **trailed** exits.
**Ours is a fixed 2R with break-even at 1R.** These are not measuring the same thing and the
comparison is directional only. What can be said: at a 2R fixed target this setup does not
separate winners from losers at all.

### What this does NOT establish
- It does not test his 1:4–1:6 trailed exit. A `zxck-10am-keyopen-hisexit` arm remains a
  legitimate separate trial with its own prereg.
- It does not test the bonus confluences (PD array, fib, rejection block) — those were correctly
  excluded as bonuses, and adding them would be a filter search, not a baseline.
- **4 arms are now owed to the merged trial ledger** (2 windows × 2 readings), and none has been
  graded against the deflation bar.

### Revision log
- **2026-08-07 rev c** — raw baseline run. Window corrected from my 10:00–14:00 assumption to
  10:00–10:15 per Brake's standing macro rule. Result is the random-walk null under all four
  variants.


---

## BOUNDED BASELINE — 2026-08-07 (rev d) — THE REAL BASELINE

`scripts/zxck_keyopen_bounded.py` · `zxck-10am-keyopen-bounded.csv`
Reading **A** (scan includes the 10:00 bar), per Brake. Span restricted to the tick-covered
window so no convention is mixed. rev-c's numbers stay above as the record of what the OHLC
discard bias was doing.

### ⚠️ The tick resolution Brake asked for COULD NOT BE RUN — we do not hold tick data
See `zxck-COMPONENTS.md` §F00.1. The footprint files are aggregated to (minute × price × side)
and carry **zero** sequence information; depth is one snapshot per minute; there is no Databento
client or key. **The 73 ambiguous sessions in this span remain unresolved, and none was guessed.**

Instead the ambiguity is **bounded**: every ambiguous session is run under *both* orderings.

### Spec
NQ 1-min · 10:00–10:15 ET · **2025-06-01 → 2026-07-15** (the aggressor-tagged span) ·
**352 sessions**, less 61 Sunday/holiday, 25 FOMC/Powell, 1 no-manipulation · exit = the locked
convention. **Flow coverage is 100% by construction** — the span *is* the flow span.

### Sessions
| | n | median daily range |
|---|---|---|
| **decidable** on OHLC | 192 → **115 trades** | 366 pt |
| **ambiguous** (both sides, one bar) | 73 → 44/45 trades | **484 pt** |

### The bounded result

**Re-run 2026-08-07 after the same-bar fix. The bound is unchanged in sign: still entirely at
or below zero.**

| arm | n | win/BE/loss | avg R | expectancy | total | maxDD |
|---|---|---|---|---|---|---|
| **decidable only** | 115 | 22.6 / 24.3 / 53.0 | −0.078 | **−0.162R** | −9.0R | 16.0R |
| ambiguous, *if up first* | 44 | 38.6 / 6.8 / 54.5 | +0.227 | +0.144R | +10.0R | 9.0R |
| ambiguous, *if down first* | 45 | 20.0 / 17.8 / 62.2 | −0.222 | −0.306R | −10.0R | 12.0R |
| **BOUND LOW** | 160 | 21.9 / 22.5 / 55.6 | −0.119 | **−0.202R** | −19.0R | 18.0R |
| **BOUND HIGH** | 159 | 27.0 / 19.5 / 53.5 | +0.006 | **−0.077R** | +1.0R | 16.0R |

~~Pre-fix: decidable −0.127R, bound [−0.140R, −0.027R].~~ The upper bound is now **−0.077R** —
i.e. **even the most favourable resolution of the 73 ambiguous sessions loses money after
costs.** Before the fix that was already true but by a smaller margin.

*Random-walk null for a 2R target with break-even at 1R: **25.0 / 25.0 / 50.0**.*

### Answer to "did recovering the volatile sessions change the picture?"

**No — the whole bound is negative after costs.** Expectancy lies in **[−0.140R, −0.027R]**.
Even the most favourable ordering of the ambiguous sessions does not produce a profitable card.

### The flattering arm, and why it is not a finding
The *"if up first"* ambiguous arm looks strong: 40.9% wins, +0.235R, 18/44 vs the 25% null gives
binomial **p = 0.0148** (**0.0297** after doubling for the arbitrary choice between two orderings).
Two reasons it is not an edge:

1. **Every trade in that arm is a SHORT, by construction.** Under *up first* the manipulation is
   up, so R4 makes every ambiguous trade a short; under *down first* every one is a long. **The
   two arms are the same 44–45 sessions traded in opposite directions** — one directional bet and
   its mirror, not two independent estimates. That arm is partly a bet on NQ's direction over 13
   months.
2. **Choosing it because it looks better is pure selection.** We cannot tell which ordering is
   real; that is the entire reason this is a bound.

**Where the uncertainty is concentrated is itself the useful output:** the ambiguous subset spans
−0.172R to +0.235R on n≈44. That, and only that, is the case for buying the tick data.

### Comparison to his figures — directional only
His *"juicy take profit"* `[5pL41Pl7GM4 @ 25:30]` and 1:4–1:6 band `[WEeXKMzaJjY @ 15:56]` are
**trailed** exits; ours is a fixed 2R with break-even at 1R. Not the same measurement.

### Revision log
- **2026-08-07 rev d** — reading A on the tick-covered span, ambiguity bounded rather than
  guessed. Expectancy bound [−0.140R, −0.027R]: negative under both extremes.

---

### ⬛ 2026-08-07 — H2 and H1-magnitude FAILED out-of-sample
Full result: **`research/_shared/f2-oos-test.md`** (spans both traders, so it lives in `_shared`).

Tested on **115 independent trades** (`zxck-10am-keyopen`, decidable only) — a different trader,
a different setup, identical feature definitions. The hypotheses had only ever been evaluated on
the 29 `ash-unicorn-sb` trades that produced them.

- **H2 FAILED, with the sign reversed.** Pre-registered win < loss < BE; observed **loss 0.226 <
  BE 0.262 < win 0.319**. Cliff's δ **+0.281** against an in-sample **−0.635**. At its original
  1.0 threshold the filter makes the card **worse** (−0.127R → −0.151R expectancy, maxDD 16→19R).
- **H1-magnitude FAILED.** Direction held (win 0.095 > loss 0.072) but Holm-corrected
  **p = 0.1466**, Cliff's δ **+0.196** — a third of the in-sample +0.596.
- **Not an underpowered null:** the sample detects **d ≥ 0.58**; the claimed effects were ~0.6.

**Both hypotheses are retired.** No filter is applied to this card.


---

### ⛔ 2026-08-07 — STAGE 4 POOLED F2/H1 TEST HALTED AT STEP 0 (LOOK-AHEAD)
Full result: **`research/_shared/f2-h1-oos-test.md`**

`retrace_ratio` (F2) is **not a pre-entry feature**. Its retracement window ends at and *includes
the entry minute*, and the entry is an intrabar limit fill, so it contains up to 59 seconds of
post-fill tape. Footprint data is minute-aggregated, so the split is unknowable from held data.
**On 73% of `zxck-10am-keyopen` and 50% of `orb-fvg-nyopen` trades the retracement is a single
minute — the entry minute — so 100% of F2's numerator is exposed.**

**No H2 or H1 statistic was computed.** `disp_delta_magnitude`'s numerator is clean on every trade;
only its normaliser is affected (median 1.0–4.5%).

**R, expectancy, bounds and verdicts on this card are UNAFFECTED** — flow was computed and applied
to nothing.

✅ **The H2 out-of-sample FAILURE on this card STANDS, and stands more firmly.** The
contamination biases toward false positives, so it should have *helped* H2 succeed. H2 failed
anyway, on the most contaminated card in the set (100% median entry-minute share).
