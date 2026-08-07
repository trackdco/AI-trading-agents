---
date: 2026-08-05
kind: as-taught extraction (intake round 3)
source: youtube.com/@thraxxtrades — Christopher Creamer, "Orderflow Trader"
status: UNTESTED. No prereg written. No data touched.
---

# THRAXX — MACHINE-READY AS-TAUGHT SPECS

Corpus: 15 teaching transcripts in this directory (CATALOG.txt), pulled
2026-08-05 from a 43-video / 126-livestream / 178-short channel.
Credibility: `research/findings/thraxx-credibility.md` — read it, the
affiliate structure matters. Timestamps are the 30-second transcript block
stamps. Quotes verbatim.

**Why this intake is different from the last two.** Orochi and MrZincx
taught *chart geometry* (VWAP bands, opening ranges) that our candle data
already supports. Thraxx teaches **tape and footprint mechanics** — big
prints, diagonal imbalance, absorption — which land directly on the
`data/reference/cvd/footprint_*.parquet` substrate and on the depth
archive. This is the first intake whose primitives sit on the same layer
the canon's own edge was found on (§5.12-10: displacement measured against
visible liquidity).

---

## SHARED INSTRUMENT DEFINITION (applies to all specs)

**Footprint configuration, stated exactly** (UP5dlJThxU8, "My Exact ATAS
Footprint Settings"):

- Cell content: **bid × ask** per price level per candle.
- **Diagonal imbalance ratio: 400%** — "I'm looking for 400% imbalances on
  either side of the bid in the ask". He notes 300/400/500 as the usable
  band and keeps 400.
- **Volume floor: 10 contracts** — "it needs at least 10 contracts to count
  towards a[n] imbalance and then it needs to be four times the amount".
  Stated rationale: a thin candle otherwise prints meaningless imbalances.
- **Stacked imbalance** = the ATAS indicator firing when qualifying
  imbalances sit **on consecutive price levels** and survive to the
  candle's close.
- **Big trade filter, MNQ: minimum 300** — "I'm looking for big trades with
  a minimum value of at least 300. At least." He explicitly names 100 as
  noise.
- Execution timeframe: **5-minute** (15-minute named as an alternative for
  the stacked-imbalance model).

**The load-bearing primitive is ACCEPTANCE, not aggression.** Stated three
ways: "The print itself is not the signal, the reaction to it is"; "the
imbalance itself is not the trade, the reaction to it is"; and the core
question "is aggression being rewarded with price movement?" Every model
below is a two-candle structure — **candle 1 confirms aggression, candle 2
is the execution on the pullback**.

---

## SPEC 1 — BIG-TRADE CONTINUATION (raCTiS4RNno) — the most mechanical sequence in the corpus

1. **THESIS.** A large print is real interest. It earns a trade only if the
   market then *agrees*: price must progress away from it, and when price
   returns, the positioning must be defended. The bet is on the defenders
   of that print, not on the print.

2. **ENTRY — an explicit 4-step sequence.**
   (i) A big trade prints (≥300 MNQ) **inside the body of the candle, not
   at its extreme** — "I don't really want to see the big trade printing
   right at the top of the candle... I want it to be deeper into the body";
   (ii) **follow-through** after the print and a **strong close** in that
   direction (he calls this "75% of the way there");
   (iii) the **next** candle opens and **immediately pulls back** into the
   big-trade area;
   (iv) the counterparty **fails there** — "sellers to stall, stall, stall"
   — the original side re-engages and the candle **flips back**. Entry on
   that flip.

3. **STOP.** Stated, unusually for this repo's intakes: **just beyond the
   big trade / the candle containing it**, "give it a little bit of room so
   you don't get wicked out". This is a TAUGHT stop — the first intake
   where we are not inventing one.

4. **TARGETS.** He uses **2R** in both worked examples, flagged as "let's
   just say for this example". Treat 2R as illustrative, not doctrine —
   declare it as an arm alongside structural targets.

5. **MANAGEMENT (taught).** Move stop to **break-even once the next candle
   takes the prior candle's extreme** in the trade's direction — "I'm going
   to wait until we actually take the lows of the previous 5-minute candle
   cuz it's how I typically manage my trade". Note §5.12-6: **BE is a null
   hypothesis in this shop and has been beaten three times.** His BE rule
   must defeat it, not inherit it.

6. **MANDATORY CONTEXT (his hard gate — see SPEC 3).** He states flatly that
   the model has no standalone edge. Also: in chop, big trades print at both
   ends and must be ignored — "just because these trades print doesn't mean
   you just automatically follow them".

7. **DISCRETION GAPS → census arms.**
   - D1 "big trade" on NQ (not MNQ): his 300 is a *micro* threshold. NQ
     equivalent is 300/10 = 30 contracts if scaling by contract size —
     DECLARE BOTH and a percentile-based variant (§5.12.1-15 warns that
     absolute size thresholds are regime-sensitive; book thickness shifted
     1.45× within our own fit span).
   - D2 "inside the body": quantify as the print's position in the candle
     range — arms at ≤75%, ≤60%, ≤50% from the extreme.
   - D3 "strong close": close in the extreme quartile / body-to-range ratio
     ≥0.6 (the repo already uses this shape).
   - D4 "immediately pulls back": next candle only, vs within N candles
     (he shows both — "sometimes it doesn't come on the next candle").
   - D5 "flips back": close reverses vs delta flips vs both.

8. **FREQUENCY.** He takes these "all the time" on a daily 5-min stream;
   implied several per week, gated hard by context.

---

## SPEC 2 — STACKED-IMBALANCE CONTINUATION (raCTiS4RNno)

1. **THESIS.** Stacked imbalance = sustained one-sided aggression across
   consecutive price levels. If that aggression is real, price should not
   trade back through and *accept* inside the stack.

2. **ENTRY.** (i) Stacked imbalances form and **survive the candle close** —
   he stresses they can vanish intrabar, "you have to wait for the candle
   to actually close"; (ii) next candle pulls back **into** the stack zone
   but **not past it**; (iii) counterparty fails, original side re-engages,
   candle flips; entry on the retest.

3. **STOP.** Taught: **the other side of the candle that created the
   stack**. Invalidation is explicit — "if we push back through it, then
   I'm wrong and then I'm out".

4. **TARGETS.** 2R in the worked example; same caveat as SPEC 1.

5. **MANAGEMENT.** BE when aggression resumes strongly, location-dependent.
   Weaker than SPEC 1's rule; declare as an arm.

6. **MANDATORY CONTEXT — stated as a "non-negotiable" disclaimer.**
   "Stacked imbalances are incredibly common, and that alone makes them
   dangerous. This model only applies when the imbalance is **extreme**."
   A census that fires on every stack is explicitly the strawman he warns
   against.

7. **STRUCTURAL NOTE, testable and interesting.** He observes stacks
   typically sit in **thin / low-volume pockets of that candle's own volume
   profile**. That is a computable secondary filter and a genuine
   hypothesis, not decoration.

8. **DISCRETION GAPS → census arms.** "Extreme" is undefined — arms: stack
   length (≥3 / ≥4 / ≥5 consecutive levels), ratio above his 400% floor
   (400/600/800%), and the low-volume-pocket filter on/off.

---

## SPEC 3 — THE FOUR-LAYER GATE (tm6qCMItaNw) — the mandatory context for Specs 1–2

He is unambiguous that Specs 1–2 are worthless alone: "none of it has an
edge on its own... they only work inside the rest of the framework". The
gate has four ordered layers, and **"if one of those are missing, then I
don't take a trade"**.

1. **ENVIRONMENT** — expanding vs compressing; trending / rotating /
   chopping; higher-timeframe draw; did price just sweep a meaningful
   level, or are we in balance with no edge.
2. **LOCATION** — premium/discount relative to the active range. He names
   **fib 0.705 / 0.788 / 0.886** as his premium-discount model ("the golden
   pocket"), explicitly *not* "some magic universal level".
3. **PATH** — session roles: **Asia builds the initial balance, London
   probes/manipulates/expands away from it, New York resolves**. Questions
   asked: did London take one side of Asia, or both? Did pre-market already
   complete the move? Is an objective still available into NY?
   **Plus gamma/GEX as environment context, explicitly NOT a signal:**
   positive gamma → expect rotation, chop, pinning near strikes, less
   follow-through; negative gamma → larger/faster expansion, cleaner
   directional movement once imbalance appears. He calls these "baseline
   expectations... not predictions".
4. **CONFIRMATION** — order flow last, and only inside a zone already
   chosen: is aggression being rewarded with price progression, is
   absorption present, does delta flip, do aggressive imbalances appear in
   the trade's direction.

**The no-trade day is an explicit part of the framework** — "some of my
best days are the days where I do absolutely nothing."

---

## SPEC 4 — DELTA, AS HE DEFINES IT (MycwtbqQQqc) — a definition, not a setup

Recorded because it constrains how any delta gate must be built. Delta =
aggressive buyers minus aggressive sellers. His claim: **delta measures
participation, not control** — "it's not evidence of structural control,
it's just showing us who is aggressive". The usable question is the
*conjunction*: aggression **and** whether price responded. Heavy aggression
with no price progression is his absorption tell and a reversal candidate,
explicitly not a guarantee.

**This matches our own canon finding** (§5.12-10): flow was near-worthless
AT entry and decisive INSIDE the trade. His framing — aggression only
means something relative to price response — is the same object our
`wall_ratio` / displacement work landed on. That convergence is the single
strongest reason to test this corpus.

---

## CROSS-SPEC FLAGS FOR ANY PREREG

1. **The strawman trap is pre-loaded here.** Both entry models are
   explicitly declared edgeless without the SPEC-3 gate. A naive census of
   raw big-trade or stacked-imbalance triggers will produce a negative and
   it will be **meaningless** — this repo has already made that mistake
   twice (nya-ivb killed twice by strawman censuses and vacated;
   NYO-ROT-01 trial 1 vacated). Per §5.9.1 the taught trade includes its
   mandatory triggers. Either the gate is implemented or the census is not
   a test of his teaching.
2. **The gate is only partly mechanizable today.** Layers 1–2 (environment,
   location) and the session-path half of layer 3 are computable from what
   we hold. **Gamma/GEX is not** — we have no options data. Declare it a
   documented N/A per §5.11-6 rather than silently dropping it.
3. **Stops are TAUGHT here** — a first. Do not default to the house's
   invented stop arms; his structural stop is the primary arm and ours are
   the challengers.
4. **BE is his default management and our null.** §5.12-6: BE has been
   beaten three times on our books. His BE rule must defeat the null.
5. **Contract-size translation is a live risk.** Every number he gives is
   MNQ-scaled. An unscaled port to NQ silently changes the filter by 10×.
6. **Data reach.** Footprint/CVD covers 2025-06-01 → 2026-07-19 — the fit
   span, and the six sealed 2023/24 months carry the same coverage. Depth
   covers 08:00–10:29 ET only. His NY-open trades sit inside depth cover;
   afternoon trades do not.
7. **His own base rate is unknown.** He never states a win rate, expectancy,
   or sample size for either model anywhere in the corpus. There is no
   claimed number to falsify — only mechanics to measure.
