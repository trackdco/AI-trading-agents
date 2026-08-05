---
id: zxck-gap-fill-edge
name: Full gap fill at the far FVG edge
trader: Powell
prefix: zxck-
sessions: [not stated]
instruments: [NQ]
GAP_ENTRY: YES — and it is the DIRECT INVERSE of ash-unicorn-sb's near-edge entry
NY_SESSION: partial
sources: [86DOt135Wts, lRgsHGWzO9E, 4COROwkO3DI]
components: zxck-COMPONENTS.md
verdict: PARTIAL — UNTESTABLE (n=12)
---

# `zxck-gap-fill-edge` — the far edge of the gap

## Confirmation

### 1 · TEACH-BACK

Most people trade the 50% of a fair value gap; this is the other sensitive point — the **far
edge**, where the entire inefficiency has been filled. For a bullish FVG that is its very low
(the most discounted point); for a bearish one, its very high. The logic he gives is simply that
filling the whole imbalance is what causes the reaction, and it works on any timeframe — the
lower the timeframe you read it on, the better the entry, and on a 4-hour chart a fill that looks
like a rip-through often shows a 50-point reaction once you drop down. He is explicit that this
is a **trade-off, not an upgrade**: taking only the far edge gives the best entry but misses a
fair number of trades that turn at the 50% instead, and you have to decide which you want. The
condition that makes it worth taking is the one he repeats everywhere — **engineered liquidity**
at the level, ideally the wick of a higher-timeframe candle with resting liquidity below its CE.
He also gives the live version of this in a different video: don't enter the first tap of a
4-hour gap if equal lows were left behind — wait for those equal lows to be swept **into** the
gap, because that is the better setup. What he never gives is a stop rule or a target rule for
this specific entry, so I would have to borrow both from his general risk framework.

### 2 · SEVEN-PART COMPLETENESS CHECK

| part | tag | evidence |
|---|---|---|
| **bias source** | **[inferred]** | Not stated for this model; inherits `COMPONENTS` §A. The worked example is bearish off a 4H wick CE with sell-side below `[86DOt135Wts @ 01:39]` |
| **setup conditions** | **[stated]** | *"the very low of a bullish fair value gap… the most discount level… is going to be super sensitive. It's going to fill this entire gap"* `[86DOt135Wts @ 00:50]`; any timeframe `[@ 02:26]` |
| **entry trigger** | **[stated]** | limit at the far edge, i.e. the complete fill `[@ 00:50]` |
| **stop / invalidation** | **[gap]** | **Never stated for this entry.** No stop appears anywhere in the gap-fill video |
| **targets** | **[gap]** | Never stated. Reactions of *"50 points"* and *"250 points"* are described after the fact `[@ 02:26, 03:13]`, not set in advance |
| **risk / sizing** | **[inferred]** | `COMPONENTS` §D/§E only |
| **avoid-filters** | **[stated]**, one | *"combine it with liquidity. Engineered liquidity is super powerful"* `[@ 03:35]`; and don't take the first tap if unswept equal lows sit below `[4COROwkO3DI @ 02:05]` |

**Two [gap]s, and one of them (stop) is core.**

### 3 · ASK ME

**Q-D1 · Where does the stop go on a far-edge entry?**
- *Best guess:* **just beyond the gap**, i.e. a few points past the far edge, since the thesis is
  that the full fill is the reaction point and a trade through it invalidates. That is consistent
  with his general rule of sizing the stop to the array `[xae9AiV5Ps4 @ 06:51]`.
- *Why it matters:* it is the **only missing core rule**. Without it there is no trade. And the
  choice is consequential: beyond the gap gives a tiny stop and frequent stop-outs; beyond the
  originating candle gives a large one.
- *Answerable from method?* **Yes.**

**Q-D2 · Does the far edge have to be reached exactly, or is "nearly filled" enough?**
- *Best guess:* **exactly, or within his ~1-point edge tolerance** `[y7KMT9CIVMo @ 03:32]`. He is
  emphatic that the sensitivity is at the extreme itself.
- *Why it matters:* gaps that *nearly* fill are common; gaps that fill to the tick are not.
  This is a several-fold difference in event count.
- *Answerable from method?* **Yes.**

**Q-D3 · Is this a separate model, or just "the other level" inside the wick-CE setup?**
- *Best guess:* **the other level inside the same setup.** Both his worked examples are 4-hour
  **wick** trades with engineered liquidity below the CE `[86DOt135Wts @ 01:39, 02:04]` — the
  same structure as `zxck-wick-ce`, entered at the gap's edge rather than the wick's midpoint.
- *Why it matters:* if it is a variant, it does **not** need its own bias/target rules and does
  not count as a separate trial; if it is standalone, it needs both and it does. This affects
  the trial ledger, not just the card.
- *Answerable from method?* **Yes.**

### ⬛ SELF-RESOLVED 2026-08-07 — Q14, Q15, Q16 ALL closed
Full evidence: `SELF-RESOLVED-2026-08-07.md`. **This card has no open questions left.**
- **Q16 → it is a LEVEL TYPE inside the wick-CE setup**, not an independent model. Both traded
  examples are 4H wick-CE trades with engineered liquidity below the CE `[86DOt135Wts @ 01:39, 02:04]` `[inferred]`
- **Q14 → stop is consequential on Q16: beyond the wick, per `zxck-wick-ce`.** `[inferred]`
  **Assumption stated:** the gap-fill entry inherits the wick-CE stop rather than having its own.
- **Q15 → the far edge must be reached**, within his ~1pt tolerance `[86DOt135Wts @ 02:26]`,
  `[y7KMT9CIVMo @ 03:32]` `[stated]`

**Card retained** despite being a variant, because far-edge-vs-near-edge is the exact A/B against
`ash-unicorn-sb`. **Recorded as a VARIANT, not an independent trial** — it must not be counted
twice in the ledger.

### ⬛ CONFIRMED 2026-08-07
ALL THREE questions closed by self-resolution (Q14, Q15, Q16). No question on this card remains open.

Brake also ratified the **fixed 10-point manipulation floor** as his rule:
> *"keep the 10pt floor as a fixed point value like he stated it — that's his rule. The
> ATR-scaled version the agent flagged is a separate hypothesis for later, not a substitute now."*
`[stated-by-user]`

**Exit is now the locked convention** — see `EXIT-CONVENTION-LOCKED.md`: target 2R, break-even at
1R, no trailing, stop-first on a same-bar conflict, capped 16:00 ET, costs reported separately.
Identical to `ash-unicorn-sb`, so the trades pool. **His own 1:4–1:6 band and Apex-driven trailing
stay on this card as `[trader-claimed, unverified]` and are NOT scored.**

### 4 · VERDICT — **CONFIRMED**

The entry is precisely stated and it is the **cleanest head-to-head against `ash-unicorn-sb`** we
have — same object, opposite edge. But **the stop is a [gap]** and Q-D3 decides whether this is
one card or a variant. Tradeable in principle, not testable until Q-D1 is answered.

---

## Edge thesis
> *"It's called a gap because there's buy side imbalance, sell side inefficiencies. We're just
> filling this whole inefficiency, which often times is going to cause a reaction."*
> `[86DOt135Wts @ 01:15]`

## The stated trade-off — this is the honest part
> *"if you only use the very low of the fair value gaps like I just showed, you're also going to
> miss a fair amount of entries. So that's also personal preference — do you want the best entry
> or do you want to actually be in more trades."* `[86DOt135Wts @ 02:50]`

**Both branches are his.** Which one we test is a choice we make, and it must be recorded as ours.

## ⚠️ Direct opposition to `ash-unicorn-sb`
| | ash10hazard | Powell |
|---|---|---|
| entry point | **near edge** of the FVG, first touch | **far edge**, complete fill |
| implied thesis | the gap is an entry zone, take the earliest touch | the gap is an inefficiency, the reaction comes when it is fully rebalanced |

Same object, opposite side, both on NQ. **This is the single most direct A/B in the two corpora**
and neither was written with the other in mind.

## Performance claims
None quantified. Reactions described post hoc: *"a pretty decent top tick reaction of like 50
points"* `[@ 02:26]`, *"a 250 point selloff"* `[@ 03:13]` — `[trader-claimed, unverified]`.

## Revision log
- **2026-08-07 rev a** — PARTIAL. Stop is a gap (Q-D1); Q-D3 decides card-vs-variant.

### 2026-08-07 rev b — self-resolution, Brake's answers, exit lock
Prior rev-a numbers and tags are **retained above, not overwritten**. This revision adds:
the Step-1 self-resolution block, Brake's `[stated-by-user]` answers where given, the locked exit
convention (`EXIT-CONVENTION-LOCKED.md`), and a re-issued verdict.


---

## ⛔ GATE CHECK 2026-08-07 — **UNTESTABLE at n = 12**

`scripts/zxck_wick_gate.py` — counts only, no outcome measured, no power spent, no trial recorded.

Window 09:45–10:15 ET `[stated-by-user]`, span 2025-06-01 → 2026-07-15, 352 sessions.

| gate | 2025 | 2026 | all |
|---|---|---|---|
| 0. sessions in window (FOMC excluded) | 140 | 126 | 266 |
| 1. + a ≥10pt wick | 128 | 121 | 249 |
| 2. + candle closes against its own wick | 112 | 119 | 231 |
| 3. + that wick swept a prior swing extreme | 41 | 55 | **96** |
| 4. + engineered liquidity >2pt beyond the CE | 22 | 25 | **47** |
| **5. + an FVG at the wick** | 5 | 10 | **15** |
| 6a. + price returns to the CE → `zxck-wick-ce` | 17 | 21 | **38** |
| **6b. + price returns to the FAR EDGE → this card** | **4** | **8** | **12** |

### The far-edge entry dies at gate 5, and it is not a threshold I chose

**Only 15 of 47 qualifying wicks have an FVG at them** — a 68% cut, and it is the single largest
drop in the stack. The 10pt wick floor (which is **ours** by extension, `[A]`) barely filters at
all: 249 of 266 sessions pass it. So the sample is not thin because of any number we picked. It
is thin because **a rejection wick that also leaves a fair value gap is rare.**

**n = 12, split 4/8 across eras. That is under half the n≥30 floor and cannot be baselined.**

**No threshold was relaxed to manufacture sample**, per the standing rule that a thin sample is a
finding rather than a reason to loosen a rule.

### Verdict corrected: **CONFIRMED → PARTIAL / UNTESTABLE**

Two corrections to my own bookkeeping, both mine:
1. This card was marked **Confirmed** while its stop is inherited from `zxck-wick-ce`
   (Q14 → Q16), and **`zxck-wick-ce` is PARTIAL with Q3 unresolved**. A card cannot be Confirmed
   on an inherited open question.
2. It is now also **UNTESTABLE on held data** at n = 12.

**What would make it testable:** more sessions. At ~12 events per 13.5 months, reaching n = 30
needs roughly **2.5 more years** of forward data. It is not a data-purchase problem — the events
simply do not occur often inside a 30-minute window.

### Revision log
- **2026-08-07 rev e** — gate check run before baselining. UNTESTABLE at n=12; verdict corrected
  from Confirmed to Partial. Host detector (`zxck-wick-ce`) reaches **n=38** and is runnable.
