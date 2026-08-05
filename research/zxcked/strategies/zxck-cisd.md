---
id: zxck-cisd
name: CISD retest (change in state of delivery)
trader: Powell
prefix: zxck-
sessions: [New York — example is the 09:00 ET candle into the open]
instruments: [NQ]
GAP_ENTRY: NO standalone; YES in the CISD+inversion variant
NY_SESSION: YES
sources: [0u1L00q77bw, rzfgAEYhxCg, C6VSpegON80, 55KRVFLqzwA, pMv3USznFdU, asi9nTJywN4]
components: zxck-COMPONENTS.md
verdict: CONFIRMED
---

# `zxck-cisd` — the CISD retest

## Confirmation

### 1 · TEACH-BACK

A change in state of delivery is a specific two-step: a candle **closes beyond the OPENING PRICE
of the opposing candle**, and then price **comes back and tests that opening price** before
expanding. The opening price is the sensitive number — not the body, not the wick — and that is
where my entry goes, two ticks beyond it. It is distinct from an order block: an order block
expands *away* and you come back to it later, whereas a CISD prints an immediate rebalancing wick
straight back into the open. It works on every timeframe he trades, and his own hierarchy is that
**daily, then 4-hour, then 1-hour CISDs are the most powerful and most consistent**. The
underlying claim is universal: down-close candles should support price going up, up-close candles
should support price going down. In the worked example the confluences are that price is below
true day open with almost no trading above it — which he reads as the leg down being manipulation
— and he wants the entry **before** price taps true day open, because tapping it first makes the
setup lower probability. Stop is around 5 points (he says 3 or 5 and isn't sure which he used),
target is true day open. The version he calls "perfect" is when the same candle that creates the
CISD also **inverses a fair value gap**.

### 2 · SEVEN-PART COMPLETENESS CHECK

| part | tag | evidence |
|---|---|---|
| **bias source** | **[stated]** | *"we're below true day open. We barely have any trading above true day open. That's usually a good indicator of this leg down is going to be manipulation"* `[0u1L00q77bw @ 03:27]`; and `COMPONENTS` §A |
| **setup conditions** | **[stated]**, precisely | *"we want the next candle after this one to close above the opening price of this down close candle. And when it does that, we want it to come back down, test the opening price, and then expand"* `[0u1L00q77bw @ 02:16]` |
| **entry trigger** | **[stated]** | *"we can put our entry two ticks above the opening price"* `[@ 06:15]` |
| **stop / invalidation** | **[inferred]** | *"let's say it did a five-point stop. I think that's what I did on this one. It was either a five or a three, I don't remember"* `[@ 06:38]` — a recollection, not a rule |
| **targets** | **[stated]** for the example | *"We can put our TP at true day open"* `[@ 06:15]` |
| **risk / sizing** | **[inferred]** | `COMPONENTS` §D/§E |
| **avoid-filters** | **[stated]**, one | *"if we do tap into this before tapping into today open… if price does this, then it's going to be lower probability. I don't want it anymore"* `[@ 04:39]` |

### 3 · ASK ME

**Q-E1 · Is the CISD a standalone entry, or only an entry trigger inside a level?**
- *Best guess:* **both, and he uses it both ways.** Standalone: *"you can just trade this and with
  good risk and just be done"* `[0u1L00q77bw @ 05:53]`, on daily/4H/1H. As a trigger: third in his
  four-trigger menu, on the 1-minute `[BOuJLWIisMI @ 02:42]`.
- *Why it matters:* the standalone HTF version and the 1-minute trigger version are **different
  strategies with different event counts and different stops**, and merging them would produce a
  meaningless average.
- *Answerable from method?* **Yes.**

**Q-E2 · How far back does the "opening price" reference reach — the immediately prior candle, or any recent opposing candle?**
- *Best guess:* **the immediately prior opposing candle.** All his examples are adjacent, and his
  phrasing is *"the next candle after this one"* `[0u1L00q77bw @ 02:16]`.
- *Why it matters:* allowing a lookback turns this into a much looser and far more frequent
  pattern. It is the difference between a rare HTF signal and a constant intraday one.
- *Answerable from method?* **Yes.**

**Q-E3 · Must the retest come before any other level is tapped, or only before the target?**
- *Best guess:* **before the target specifically** — his stated invalidation is tapping *true day
  open* (which was also his TP) before the entry `[0u1L00q77bw @ 04:39]`. Generalised: if the draw
  is reached before you are filled, the setup is dead.
- *Why it matters:* it is a cheap mechanical kill-filter, and it generalises to every card in
  this corpus if it is the real rule.
- *Answerable from method?* **Yes.**

**Q-E4 · Is the FVG-inversion pairing required, or a bonus?**
- *Best guess:* **a bonus.** *"if you want more confluence, then this is what — this is like
  perfect"* `[0u1L00q77bw @ 09:46]` reads as an upgrade, not a gate.
- *Why it matters:* as a gate it becomes a gap-entry strategy that pools with `ash-unicorn-sb`;
  as a bonus it stays a pure price-structure model and pools with nothing. It changes which Stage-3
  bucket this card belongs in.
- *Answerable from method?* **Yes.**

### ⬛ SELF-RESOLVED 2026-08-07 — Q17, Q18, Q19 ALL closed
Full evidence: `SELF-RESOLVED-2026-08-07.md`. **This card has no open questions left.**
- **Q17 → BOTH**, explicitly: *"it can be a strategy in and of itself. You can just trade this"*
  `[0u1L00q77bw @ 05:53]`. Standalone on D/4H/1H, trigger on 1m. **Carded as two variants, never
  averaged together.** `[stated]`
- **Q18 → the IMMEDIATELY ADJACENT opposing candle** — *"the next candle after this one"*
  `[0u1L00q77bw @ 02:16, 02:41]` `[stated]`
- **Q19 → FVG inversion is a BONUS** — *"if you want more confluence"* `[@ 10:11]` `[stated]`
  ⚠️ **Consequence: `zxck-cisd` does NOT pool with `ash-unicorn-sb` as a gap entry.** Only the
  `zxck-cisd-inversion` sub-case does.

### ⬛ CONFIRMED 2026-08-07
ALL THREE questions closed by self-resolution (Q17, Q18, Q19). No question on this card remains open.

Brake also ratified the **fixed 10-point manipulation floor** as his rule:
> *"keep the 10pt floor as a fixed point value like he stated it — that's his rule. The
> ATR-scaled version the agent flagged is a separate hypothesis for later, not a substitute now."*
`[stated-by-user]`

**Exit is now the locked convention** — see `EXIT-CONVENTION-LOCKED.md`: target 2R, break-even at
1R, no trailing, stop-first on a same-bar conflict, capped 16:00 ET, costs reported separately.
Identical to `ash-unicorn-sb`, so the trades pool. **His own 1:4–1:6 band and Apex-driven trailing
stay on this card as `[trader-claimed, unverified]` and are NOT scored.**

### 4 · VERDICT — **CONFIRMED**

The pattern definition is the **most precise in the corpus** — an exact two-step on a named price.
Partial because the stop is a recollection rather than a rule, and Q-E1 means we may be looking at
two strategies wearing one name.

---

## Edge thesis
> *"down close candles should support price going up. And up close candles should support price
> going down. And that's on every time frame. Monthly, weekly, daily, 4-hour, you name it. Like
> even 15 second."* `[0u1L00q77bw @ 08:13]`

## CISD vs order block — `[stated]`
> *"this immediate rebalancing wick you see here, this is a CISD. When we close above, we come
> back down into the opening price and test it, that's what I call a change in state of delivery.
> This is more like an order block scenario where we expand away from the down closed candle."*
> `[0u1L00q77bw @ 07:26]`

## Timeframe hierarchy — `[stated]`
> *"daily CISD and then 4 hour and one hour CISDs are the most powerful and the most consistent."*
> `[rzfgAEYhxCg @ 00:47]`
Also step 5 of his daily checklist `[C6VSpegON80 @ 01:38]`.

## Variants
| id | what | GAP? |
|---|---|---|
| `zxck-cisd-inversion` | the CISD candle also inverses an FVG — *"perfect"* `[0u1L00q77bw @ 09:46]` | **YES** |
| `zxck-15s-cisd-scalp` | after a PD-array tap or sweep, first 15-second CISD, ~10 points `[@ 08:35]` | **BLOCKED — no sub-minute data** |

## Revision log
- **2026-08-07 rev a** — PARTIAL. Q-E1 may split this into two cards.

### 2026-08-07 rev b — self-resolution, Brake's answers, exit lock
Prior rev-a numbers and tags are **retained above, not overwritten**. This revision adds:
the Step-1 self-resolution block, Brake's `[stated-by-user]` answers where given, the locked exit
convention (`EXIT-CONVENTION-LOCKED.md`), and a re-issued verdict.


---

## RAW BASELINE — 2026-08-07: **n=40, +0.044R — the only zxck card not negative**

`scripts/zxck_remaining_baselines.py` · `zxck-remaining-raw-trades.csv`

### Gate
266 sessions → **84** with a 1-hour CISD → **40** filled (6 skipped: the draw was taken before the
entry, per C5 `[0u1L00q77bw @ 04:39]`).

### Result
| | | | era | n | WR | total |
|---|---|---|---|---|---|---|
| n | **40** | | 2025 | 26 | 23.1% | +1.73R |
| win / BE / loss | **22 / 22 / 45** (+4 timeouts) | | 2026 | 14 | 21.4% | +0.98R |
| avg R | +0.068 |
| cost | 0.024R/trade |
| **expectancy** | **+0.044R net** |
| total | **+2.70R** · maxDD **4.45R** |
| **t / effect** | **+0.351** / **+0.0555** |

### Read this before treating it as a positive

**t = +0.351.** That is indistinguishable from zero. The outcome mix is **22 / 22 / 45** against a
random-walk null of **25 / 25 / 50** — it *is* the null. The +2.70R total comes almost entirely
from 4 timeout trades exiting at fractional R, not from the setup selecting direction.

Against the deflation bar at **+0.6978**, an effect of **+0.0555** is not in the conversation.

**"Not negative" is the honest description. "Works" is not.**

### Assumption carried
**C2 timeframe is OURS by selection** — he names daily, 4H and 1H as *"the most powerful and the
most consistent"* `[rzfgAEYhxCg @ 00:47]`; daily and 4H produce too few levels inside a 30-minute
window, so 1H was taken from among his three. And **C4 stop is `[inferred]`** structural, since his
only statement is *"either a five or a three, I don't remember"* `[0u1L00q77bw @ 06:38]`.

### Revision log
- **2026-08-07 rev d** — raw baseline, n=40, +0.044R expectancy, t=+0.351. Statistically zero.
