# AUDIT — DodgysDD, the UCLA lecture: the full model, stated in his own words

**Source.** A ~36-hour day-trading class taught at UCLA (his framing: *"shout out to
Peter Tuckman from the New York Stock Exchange for letting me do"* it), uploaded to the
`@DodgysDD` channel as parts 1 and 2. Supplied here as a pasted transcript with **no
video id and no timestamps** — see §0.

**Why this source matters more than the other 472.** `docs/FINDINGS-dodgy-ifvg.md` closes
with an explicit list of six components it could not test because the corpus never
defined them. **This lecture defines all six.** It is the single most complete statement
of the model in the corpus, and it is a classroom lecture rather than a promotional
short, so the rules are stated as rules rather than gestured at over a chart.

| gap named in FINDINGS-dodgy-ifvg.md | status after this lecture |
|---|---|
| the **higher-timeframe FVG** the inversion delivers from | **DEFINED** — X1, a two-stage trade-inside-a-trade |
| the **key-area requirement** (*"not in the middle of nowhere"*) | **DEFINED** — L1–L12, a closed list of twelve level types |
| **trend-line liquidity**, the 2026 model's primary draw | **DEFINED** — L2, with a slope and touch-count rule |
| **momentum entry** (death/birth candle vs a choppy close) | **DEFINED** — E3/E4, body-close + displacement test |
| **SMT**, 1,183 corpus mentions, entirely untested | **DEFINED** — S1, NQ vs ES, and explicitly *not* standalone |
| **order block / CISD confluence** | **DEFINED** — P2/P3/P4 |

Evidence classes follow the house convention in
`.claude/skills/tomtrades-model/references/confluence-table.md`:
**A** = verbatim spoken quote · **B** = asserted, quote in corpus, not re-attached ·
**C** = chart-read only, never spoken · **D** = named but never defined.

Discipline: his definition is quoted, the ambiguity is named, and every formalisation is
a **researcher candidate** carrying a sweep. An `[R]` value is never his parameter.

---

## §0 — PROVENANCE, resolved

The first draft of this document was built from a pasted transcript with no video id and
no timestamps, and said so. **That defect is now closed.** Both parts were re-fetched from
the channel and every rule below is attached to a video id and a timestamp in
`docs/CITATIONS-dodgysdd-lecture.md` — 38 of 38, no unattached rules.

| | |
|---|---|
| **part 1** | `r43i9rRIjoQ` — 11:59:59, 93,167 words |
| **part 2** | `WQycR82IOD4` — 11:57:29, 99,528 words |
| total | **23h 56m, 192,695 words** |

The fetched captions reproduce the supplied transcript verbatim, including its
corruptions, which is the check that matters: the paste was faithful, it just had no
provenance. Identity is confirmed from the primary source — *"DD stands for due
diligence"*, `WQycR82IOD4 @ 09:36:38`.

**Caption corruption is systematic.** IFVG renders as *IPG / IFG*, fair value gap as
*"for value gap" / "fair rally gap" / "reality gap"*, Judas as *Judah*, data wick as
*dataix*, bisi/sibi as *busy / civvy / city*; CISD never appears at all. Words also join
across cue boundaries. Any regex mining of this corpus must allow for both.

---

## §1 — THE ENTRY MODEL

His model is **one trigger with a context stack**, and he is unusually explicit that the
trigger alone is worthless — which matters, because that is exactly what this repo
already measured.

### E1 — The inversion fair value gap (iFVG) — class A, the trigger

**He says:** *"a bullish IPG equals when price closes above a bearish reality gap"* and
*"a bearish IFVG is when price closes below a bullish gap"*. Also: *"fair value gaps and
using fair value gaps are my whole strategy and everything I do revolves around fair
value gaps"*.

**Predicate.** A fair value gap is the standard three-candle imbalance: for a bullish FVG,
`low[i] > high[i-2]`; for a bearish FVG, `high[i] < low[i-2]`. The gap **inverts** when a
subsequent candle's **body** closes through the far side of the zone.

**This is the trigger `scripts/dodgy_ifvg_test.py` already implements** (post-CORRECTION),
and it is **−0.135R after cost / −0.020R before** on NQ. Nothing in this lecture changes
the trigger definition. What the lecture changes is everything wrapped around it.

### E2 — Entry timing: market-on-close-of-the-breaking-candle — class A

**He says:** *"I get in the second this cannon closes, I get in here"* and, contrasting
himself with the ICT 2022 retracement model, *"I don't actually wait for us to go back
into the bullish valley gap... I just take it — market order"*. Asked why not wait:
*"Do you think if we're reversing all these sell orders, do you think we're going to
retrace here a lot? No."*

**This is a material divergence from the ICT lineage and from the beginner model he
teaches earlier in the same lecture.** He teaches liquidity-sweep → MSS → *retrace into*
the FVG as the "2022 model", then says *"I take it before the market structure shift"*
and *"now I do the opposite of this."*

**Testable consequence:** two entry conventions must be run as separate books, not
merged. `entry_mode: {market_on_close, retrace_limit, retrace_ce}`.

### E3 — Body close, never a wick — class A

**He says:** *"the bodies tell the story. The wicks do the damage"*, repeated at least six
times, and on a failed case: *"Did this candle technically close below? No. Close to the
tick"* — he declines the trade.

**Predicate:** `close` of the breaking candle beyond the far edge of the zone. Wick
penetration is explicitly not a trigger. **Already implemented.**

### E4 — Displacement quality: the "Drake candle" — class A

**He says:** *"good displacement equals [draw a giant green candle]... bad displacement
equals [a doji]"*, and *"Some people call this a drake candle"*. Also *"death candle"* for
the bearish case, which he defines by contrast: *"these are obviously weak, choppy candles
that suck... and all of a sudden, poof, we get a giant down move. That's like death."*

**Ambiguity — class D on magnitude.** He never gives a number. Candidates, all `[R]`:
`body/range ≥ q`, `body ≥ k × ATR(n)`, `body ≥ k × median body of prior n bars`.

### E5 — The four hard rules on which iFVG to take — class A, and these are new

He numbers these explicitly as beginner rules:

1. **Singular.** *"the IPG must be singular... it should be only one bearish for value gap
   visible"*. If several stack in one leg: *"we want to wait for both these to inverse"*,
   or combine them into one zone, or *"try to go to the higher time frame, use that one
   instead."*
2. **Big and obvious** — the ten-foot test: *"if I back away from the screen all the way
   back here, what line am I more likely to see?"*
3. **Liquidity swept nearby** — see §2.
4. **The target must still be unswept.** *"we haven't already taken out those highs"*, and
   on a candle that swept everything at once: *"if you ever see like a Trump candle take
   out 50 million highs or lows in the same candle do not enter... there's no more
   liquidity."*

**Rule 4 is the most valuable new predicate in this document.** It is mechanical,
unambiguous, cheap to code, and it was not in the tested specification. It is also the
one rule with a plausible mechanism that the repo's own results do not already contradict.

**Rule 2 is already refuted.** `FINDINGS-dodgy-ifvg.md` swept obviousness at p50/p75/p90
and pre-cost EV moved −0.019 → −0.027 → −0.029, no trend. His central quality claim does
not reproduce.

---

## §2 — THE LIQUIDITY SWEEP: first in his order, and already measured as subtractive

### Q1 — Sweep required before any entry — class A

**He says:** *"before any trade setup, no matter if I'm using order blocks, fair value
gaps, or IPGs, what do I ideally want to see? A nice liquidity sweep"* and *"That is the
one thing you guys should be looking for before any type of entry."* He also names it the
**manipulation leg**: *"manipulation leg equals liquidity sweep"*.

**Status: already tested, and it subtracts.** With the corrected detector, requiring the
sweep took 80,593 → 36,127 signals and moved EV −0.135 → −0.140. *"It is not selecting
better trades; it is selecting fewer."*

**But the lecture adds a qualifier the test did not have** — Q2.

### Q2 — Sweep vs market-structure-shift, and the "same size" test — class A, NEW

He spends real time on distinguishing a sweep from a genuine break, and gives a **magnitude
test** the prior specification lacked:

**He says:** *"is the break of structure... the same size as the range we just put in?"*
— he measures the prior impulse leg with a rectangle and requires the displacement out of
the range to be comparable. *"If it's like 10 points, do you really think that's going to
be a solid confirmation?"* He rates weak breaks *"a two"* out of ten and strong ones
*"a nine or 10"*.

**Predicate `[R]`:** `displacement_out ≥ k × prior_leg_range`, sweep `k ∈ {0.25, 0.5,
0.75, 1.0}`. This is a genuine, codable discriminator that has never been tested.

### Q3 — Spent liquidity is deleted — class A

**He says:** *"After we use the level, does it matter anymore? No"* and *"you delete it
off your chart... there's no more liquidity there."*

**Predicate:** a level is a valid target only until first touch; thereafter it is removed
from the draw set. **Not implemented in the tested version** and it changes the target
selection materially.

---

## §3 — THE DRAW: twelve level types, ranked (L1–L12)

This is the *"key-area requirement"* the prior findings doc listed as untestable. He gives
a closed list. Every one of these is codable against the existing census level machinery.

| id | level | his definition | class |
|---|---|---|---|
| L1 | **equal highs / lows** | double/triple/quadruple tops and bottoms | A |
| L2 | **trend-line liquidity** | 3+ touches on a sloped line | A |
| L3 | **London high / low** | extreme of 02:00–05:00 ET | A |
| L4 | **Asia high / low** | extreme of 20:00–00:00 ET | A |
| L5 | **New York high / low** | extreme of the NY session | A |
| L6 | **previous day high / low** | PDH / PDL | A |
| L7 | **weekly high / low** | *"the low we put in in the last seven days"* | A |
| L8 | **news / data high / low** | abnormal wick on a red-folder release | A |
| L9 | **intermediate-term high / low** | *"a low that bounces off an old fair value gap"* | A |
| L10 | **new week opening gap** | Friday close → Sunday 18:00 open | A |
| L11 | **new day opening gap** | 17:00 close → 18:00 open | A |
| L12 | **session low/high of day** | LOD / HOD | A |

**He ranks obviousness above type:** *"the obvious points... if I back away 10 feet from
the screen and it's obvious to me, those are the ones I was using"*, and *"we are only
focusing on the obvious ones."*

**L1 carries an explicit probability ladder — class A, and it is directly falsifiable:**

| structure | his claimed hit rate |
|---|---|
| 2 wicks adjacent | ~50% |
| 2 wicks several candles apart | 70–80% |
| 3+ wicks stacked | **89%** |
| 4+ wicks, far apart, to the tick | **90–95%** |

**This is the single most testable claim in the lecture.** It is a base rate, it needs no
entry model, and it is measurable on the NQ master file today with the same machinery that
refuted the data-wick claim.

### L2 — trend-line liquidity, defined — class A, NEW and previously called "hardest to code honestly"

**He says:** *"I really prefer trend lines that are kind of like this, not like this"* —
drawing a **45-degree angle** — and the strength rule: *"Do you think a trend line with
eight touches in the same spot is going to be stronger or weaker than a trend line with two
touches?"* Plus the mechanism he calls the **domino effect**: *"if there's stop losses
here, they're just going to trigger these stop losses to be triggered and then these."*

**Ambiguity — class D on construction.** He never states a fitting rule, a tolerance, or
what counts as a touch. `FINDINGS-dodgy-ifvg.md` was right that *"a trend line has free
parameters that a census does not"*. Candidates, all `[R]`: fit to swing points only,
touch tolerance in ticks or in W, min touches ∈ {3,4,5}, max slope, max age.

---

## §4 — THE HIGHER-TIMEFRAME NEST: the "trade inside a trade"

### X1 — Two-stage delivery — class A, NEW, and this is the component the prior doc most wanted

**He says:** *"Ideally what we're looking for is us to tap into a giant 1 hour or 4 hour
fair value gap and then find a one minute entry out of that rally gap. So, it's a trade
off of a trade."* And on timeframe selection: *"I'm only looking at like the one or 4 hour
order block. I don't really care like the daily, the weekly."*

**Predicate.** Stage 1: price must be inside an FVG or order block drawn on `htf ∈ {15m,
1h, 4h}`. Stage 2: take the E1 iFVG trigger on the 1m tape **only while inside that
zone**.

**This is a nesting filter, not a new trigger, and it is cheap to bolt onto the existing
detector.** `FINDINGS-dodgy-ifvg.md` closes by naming exactly this as the untested route
that could change the verdict: *"his model delivers from a monthly fair value gap, not a
5-minute one — and that is a different study."* The lecture says 1h/4h, not monthly, which
narrows it to something codable.

### X2 — Stop placement follows the higher timeframe — class A

**He says:** *"I got stopped out on the one minute time frame, but we still held the
five-minute for gap"* — and concludes the stop belongs below the **more obvious**
higher-timeframe zone, not the 1m one.

**Testable consequence:** stop distance is a function of the HTF zone, which enlarges the
stop and therefore cuts cost-per-R. That is the exact lever the prior findings identified
as the binding constraint (*"this trigger's stops are too small to carry NQ's friction"*).

---

## §5 — TARGETS AND MANAGEMENT

### T1 — Target is a liquidity pool, never a fixed R — class A

**He says:** *"95% of my targets are always highs and lows"*, and on the 2R convention:
*"Do you think the market sees your little riskreward position tool on the screen? No."*
If a pool sits at 1.8R he takes 1.8R.

**This breaks the tested specification.** The current test uses a **fixed 2R target**, and
the addendum already flagged the consequence: *"the target here is a fixed 2R, so room
beyond that is not reward"* — which is why room-to-run reversed sign. **Re-running with a
structural target is not a refinement; it is a different exit and probably the single
largest specification error in the existing test.**

### T2 — Partials and a runner — class A

**He says:** *"you can sell three in one place, one in another place, one in another,
that's five. That's what we call partials"*, and the runner: *"I still have one contract
left... my stop is break even, so I can't lose money."*

### T3 — Break-even trailing — class A, with a stated trigger

**He says:** *"if you're up one R... move your stop to break even"*, and separately he
moves to break-even when a structural signal appears against him (a new opposing FVG or a
trend-line touch). On being up ~1.7–1.8R he treats break-even as mandatory.

**Status: partly tested, and it is inert.** The breakeven rule moved EV by **+0.007R** —
*"a rounding error, not a mechanic"* — but that test used break-even at target 1 on a
fixed-2R book, not at 1R on a structural-target book. It should be re-run under T1.

### T4 — Two-loss rule and the daily lockout — class A

**He says:** *"if you talk to like any professional day trader, they'll usually say
they're done after two losses"*, and he is emphatic about the broker-level lockout:
*"a daily lockout feature will make you a millionaire if you use it."*

**This is a book-level constraint, not a trade filter**, and it is testable as a daily
stop-out rule on the equity curve. It cannot improve per-trade EV by construction; it can
only change the daily-R distribution and therefore max position size — which is the axis
BR-36/39 showed actually matters.

---

## §6 — TIME: kill zones, macros, and the Judas swing

| id | window (ET) | his claim | class |
|---|---|---|---|
| K1 | London 02:00–05:00 | kill zone | A |
| K2 | **NY AM 08:30–11:00** | *"the primary session... the best volume"* | A |
| K3 | NY PM | kill zone | A |
| K4 | Asia 20:00–00:00 | *"Asia equals consolidation normally"* — avoid | A |
| M1 | 08:50–09:10 | macro | A |
| M2 | 09:50–10:10 | macro | A |
| M3 | 10:50–11:10 | macro | A |
| R1 | **10:00** | *"10 a.m. equals great reversal time"* — the 4h candle close | A |

**Status: the session restriction is already refuted, and badly.** `FINDINGS-dodgy-ifvg.md`
restricted to NY 09:30–11:00 and pre-cost EV went **−0.026 → −0.071**. *"'I'm always going
to go to New York session' is, on this trigger, the wrong place to be."*

**But the macro windows M1–M3 and the 10:00 reversal R1 were never tested**, and they are
narrower than the session. R1 has a stated mechanism (the 4-hour candle close) that is
checkable independently of any trade.

### J1 — The Judas swing — class A

**He says:** *"a Judas swing is basically a move to the opposite price of where we're
actually going to go"*, at 09:30, and *"it's a confluence. It's not actually an entry
signal."*

### A1 — AMD / power of three — class A

Accumulation (Asia) → manipulation (London/open) → distribution (NY). He also states the
HTF-wick version: *"every candle forms a wick... we'll drop first to create the weekly
wick and that's where the best entry is below the opening price."*

### F1 — Big overnight move ⇒ choppy NY AM — class A, and it is a rare falsifiable filter

**He says:** *"big overnight move equals choppy or sideways New York AM session"*, and he
quantifies it: *"anything above like 300 points is pretty substantial."*

**This is testable with no entry model at all** — overnight range vs realised NY-AM
trend/efficiency. It is a clean, cheap, falsifiable claim and nothing like it has been
measured in this repo.

---

## §7 — SMT: 1,183 corpus mentions, defined here for the first time

### S1 — Smart money technique / divergence — class A

**He says:** *"a bullish SMT is when NQ takes a low, but ES does not, or vice versa"* and
*"a bearish SMT is when NQ takes out a high, but ES does not."*

**And, critically, he de-prioritises it himself:** *"This is like fifth in my checklist"*,
*"do not trade this religiously"*, *"just because we have an SMT does not mean we're going
to reverse"*, and *"some people get carried away and try to make sure there's an SMT every
trade, but I don't do that."*

**This materially reduces the expected value of testing SMT.** `FINDINGS-dodgy-ifvg.md`
ranked SMT as *"the largest untested component of his model"* on mention-count alone. The
lecture says the mention count overstates its role in the model. It is a fifth-order
confluence by his own account.

**It also requires ES**, which the repo has (`ES` is not in `data/reference/`, but the
level machinery is instrument-parameterised and `scripts/gold_level_census.py` already
takes `--symbol`).

---

## §8 — THE OTHER PD ARRAYS

### P2 — Order block — class A

**He says:** *"a red candle sandwiched between two green candles"* for a bullish OB, and
the confirmation: *"we are closing above the last down-close candle sequence"*. The entry
line is *"the open of the order block"*: *"the open of a candle for the bearish or bullish
order block equals best support resistance."*

Quality: *"do not use wicky candles for order blocks. They suck."*

### P3 — Propulsion block — class A, and he dismisses it

*"It's just an order block off an order block... I never label this on my chart ever."*

### P4 — Breaker block — class A, with two conditions

*"breaker block equals failed order block"*, and it must be **a swing point** and **have a
liquidity sweep**. Without the sweep: *"it's called the mitigation block"*, which he does
not use.

### P5 — Premium / discount — class A

Fib over a *clear impulse leg*; 0.5 = equilibrium; *"as a beginner, try to buy here [below
0.5] and try to short up there"*. Consequent encroachment = the 0.5 of an FVG.

**Status: partially tested.** The addendum measured distance-to-locus, not
premium/discount over an impulse leg. The impulse-leg selection is class D — *"it's got to
be very, very obvious"* is not a rule.

---

## §9 — THE DATA WICK, restated at a lower number

**He says here:** *"there's statistics that tell me 80 about 85% of the time you form a
newswick like that, we will hit it in the same day."*

**In the corpus he said ~99%** (`FINDINGS-dodgy-data-wick.md` quotes *"besides one day in
the last couple five months... there's only one day where they weren't hit"*).

**He has revised his own headline claim down by ~14 points between the corpus and this
lecture, without withdrawing the original.** Log this as a contradiction.

**Measured: 76–84%**, and — the finding that actually matters — **news wicks return 8–11pp
LESS often than ordinary abnormal wicks at every threshold, with non-overlapping
intervals.** The lecture's 85% is close to the measured 83.5% at the 2× rung. **His revised
number is roughly right; his premise is still backwards.** The setup's whole rationale is
that news timing *adds* return probability, and it subtracts.

The lecture adds two conditions the refutation already used: the wick must be **a 1-minute
swing point**, and it must be **"normal size", not tiny**. It adds one that was not used:
the release must be **red-folder on Forex Factory** (08:30 / 10:00 / 14:00 FOMC), which is
narrower than the news set the test used.

---

## §10 — CONTRADICTIONS, logged not resolved

1. **Data wick: 99% (corpus) vs 85% (lecture).** Never withdrawn.
2. **MSS required, or not.** The checklist makes market-structure-shift mandatory; his own
   model *"gets in before the market structure shift"*.
3. **Entry convention.** He teaches retrace-into-FVG for the 2022 model and trades
   market-on-close for his own, in the same lecture, on the same charts.
4. **2R target vs structural target.** He states a 2R discipline and then says 95% of exits
   are at highs and lows.
5. **Random vs algorithmic.** *"we still believe the market's random"* alongside *"an
   algorithm does exist"* — he states this as a deliberate psychological device, not a
   market claim, which is more coherent than it first reads but is untestable either way.
6. **Obviousness.** Presented as the central discriminator; measured to do nothing.

---

## §11 — WHAT IS ACTUALLY NEW, ranked by expected information

Everything below is *new relative to the tested specification*, not new relative to the
corpus.

1. **T1 — structural target instead of fixed 2R.** Not a filter; a different exit. The
   existing test's most consequential specification error, and it is the reason
   room-to-run reversed sign in the addendum.
2. **X1/X2 — the 1h/4h nest and HTF-anchored stops.** Directly attacks the binding
   constraint the prior findings identified (stops too small to carry friction).
3. **E5 rule 4 — target must be unswept.** Mechanical, unambiguous, untested, and it is
   the one filter whose mechanism the repo's own results do not already contradict.
4. **L1 ladder — the equal-highs probability table.** A pure base rate, falsifiable with no
   entry model, directly comparable to the data-wick refutation's method.
5. **Q2 — the displacement-vs-prior-leg magnitude test.** A real discriminator between
   sweep and break that the prior spec lacked entirely.
6. **F1 — big overnight move ⇒ choppy NY AM.** Cheap, falsifiable, no entry model needed.
7. **Q3 — spent levels are deleted from the draw set.** Changes target selection.
8. **L2 — trend-line liquidity with a slope and touch rule.** Still the hardest to code
   honestly; the free parameters are real.
9. **S1 — SMT.** Demoted by his own account from "largest untested component" to
   fifth-order confluence.

**And what is already refuted, so it should not be re-run as if open:** the bare trigger
(E1), the sweep requirement (Q1), obviousness (E5 rule 2), the NY session restriction (K2),
the break-even rule as specified (T3), and the data-wick premise (§9).
