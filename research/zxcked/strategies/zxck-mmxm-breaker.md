---
id: zxck-mmxm-breaker
name: MMXM breaker entry
trader: Powell
prefix: zxck-
sessions: [New York]
instruments: [NQ]
GAP_ENTRY: PARTIAL — the breaker is paired with a 5-minute imbalance and entered at its 50%
NY_SESSION: YES — midnight open is the premium/discount pivot
sources: [lPbKWoBShLI, asi9nTJywN4, f0mYnZ9ISJY, C6VSpegON80]
components: zxck-COMPONENTS.md
verdict: INSUFFICIENT
---

# `zxck-mmxm-breaker` — market maker model, breaker entry

## Confirmation

### 1 · TEACH-BACK

A market maker model is a V-shape (buy model) or A-shape (sell model): price taps something
significant, reverses, and runs for the opposing liquidity pool. To call one I need three things
— a **strong reversal point**, a **strong target on the other side**, and the shape itself, which
he identifies by an **original consolidation** followed by a sell-side curve down and a buy-side
curve back up. The model gives me **bias only**; the entry comes from lower-timeframe structure.
The trigger is a **breaker** — a high, a low, a higher high, and then that structure traded
through — and I need a **candle close** through it, not a wick, which he demonstrates with a
counter-example where a sweep without a close is not an entry. I work on the 5-minute because he
says that is the best timeframe for these, I enter at the **50% of the imbalance paired with the
breaker** because it gives a better stop, and my stop is around 5 points. The plus-plus version
has price swinging above or below **midnight open**, which acts as the day's discount/premium
pivot. Targets are the relative equal highs that made the model worth calling in the first place.
**The blocker is the same as AMD**: he identifies the original consolidation by eye and never says
what one is.

### 2 · SEVEN-PART COMPLETENESS CHECK

| part | tag | evidence |
|---|---|---|
| **bias source** | **[stated]** | *"a market maker model is essentially your bias"* `[lPbKWoBShLI @ 06:37]`; *"this is just for my bias"* `[asi9nTJywN4 @ 01:13]` |
| **setup conditions** | **[gap]** on the core | The three requirements are stated `[asi9nTJywN4 @ 03:09]` and the curve description is stated `[lPbKWoBShLI @ 00:23]`, but **"original consolidation" and "something significant" are both undefined** |
| **entry trigger** | **[stated]**, precisely | *"we want a candle closure above this breaker"* `[lPbKWoBShLI @ 03:55]`; counter-example at `@ 04:22`; breaker defined at `@ 01:56` |
| **stop / invalidation** | **[inferred]** | *"my stop loss would be probably five points"* `[@ 05:51]` — hedged |
| **targets** | **[stated]** | *"you just target these equal highs or relative equal highs"* `[@ 06:37]` |
| **risk / sizing** | **[inferred]** | `COMPONENTS` §D/§E |
| **avoid-filters** | **[stated]**, one | a sweep without a close is not an entry `[@ 04:22]` |

### 3 · ASK ME

**Q-G1 · What is the "original consolidation"?**
- *Best guess:* none I'd defend. He points at boxes on a chart in both videos.
- *Why it matters:* it is the identification step for the whole model. **Same blocker as Q-F1**,
  and if one answer covers both, it unblocks two cards at once.
- *Answerable from method?* **Probably not from the videos.** Best from how you'd mark it, or by
  re-watching `lPbKWoBShLI @ 00:23–01:09` and reading the box off the chart.

**Q-G2 · Does the breaker have to be the one formed at the reversal, or any breaker inside the curve?**
- *Best guess:* **any breaker inside the curve, in the model's direction.** He shows *"it gave you
  two entries"* off the same breaker `[lPbKWoBShLI @ 04:22]` and treats the model as offering
  *"a lot of precision entries"* `[@ 01:32]`.
- *Why it matters:* one-shot vs repeatable changes trade count per model several-fold, and it
  changes whether these are independent trades or correlated re-entries — which matters for the
  ledger, not just the P&L.
- *Answerable from method?* **Yes.**

**Q-G3 · Is the midnight-open swing a requirement or the "plus-plus" bonus?**
- *Best guess:* **a bonus.** *"you want a swing above or below your midnight open for it to be
  like a plus plus"* `[lPbKWoBShLI @ 06:37]` — his own phrasing marks it as an upgrade.
- *Why it matters:* as a requirement it is a strong, cheap, mechanical filter that would cut the
  sample hard. Worth knowing before we count events.
- *Answerable from method?* **Yes.**

**Q-G4 · Is MMXM a tradeable model here, or purely a bias input that should not be carded?**
- *Best guess:* **bias input plus a breaker entry** — he supplies a complete entry, so it is more
  than bias. But he says twice that the model itself is bias only.
- *Why it matters:* same double-counting risk as Q-F3. If MMXM is bias and the breaker is the
  trade, the card should be `zxck-breaker-entry` with MMXM as a filter — a different object.
- *Answerable from method?* **Yes.**

### 4 · VERDICT — **INSUFFICIENT**

The breaker trigger is well specified and testable in isolation. The **model that gates it is
not**, and I will not supply a consolidation detector and call the result his.

---

## Definitions — `[stated]`
**Breaker:** *"it's a high and a low and a higher high and then that gets traded through."*
`[lPbKWoBShLI @ 01:56]`
**MMXM:** *"do we tap into something significant where we can reverse and take out the opposing
side… You need a strong pull point, you need a strong target, and then you just need to be able
to identify this V-shape."* `[asi9nTJywN4 @ 00:00, 03:09]`

## Timeframe — `[stated]`
> *"If you're going to use market maker models, I found that five minute time frame is the best
> to use."* `[lPbKWoBShLI @ 03:55]`

## The PD-array hierarchy it sits in — `[stated]`
Rejection block → CISD → inverse FVG → **breaker**, ordered by how discounted the entry is
`[asi9nTJywN4 @ 03:53]`. **Breakers are the least discounted of his entry types**, which is
consistent with the model being a bias frame rather than a precision entry.

## Revision log
- **2026-08-07 rev a** — INSUFFICIENT. Consolidation undefined (Q-G1); Q-G4 may reshape the card.
