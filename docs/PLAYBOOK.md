# THE PLAYBOOK

The decision procedure, distilled from a full narrated week (2026-06-22 →
2026-06-26) and reconciled line by line against the tape. **11 takes, 8
passes, 2 unfilled limits, 5 session-days.** Every price he named reproduces
on our bars.

This is what the agent runs. `docs/AGENT-OPERATING-SPEC.md` is how it
operates the chart; this is what it decides. Source of truth for any
individual claim: `data/narrated_days/*.json`.

---

## 0. WHAT THE WEEK LOOKED LIKE

| day | character | takes | result |
|---|---|---|---|
| Mon 22 | topping the weekly range | 3 | +1.0R, +3.8R, and a small London win |
| Tue 23 | 400pt gap fill, one-way down | 3 | +2.94R, +3.69R, +3.13R |
| Wed 24 | chop, range unbroken all day | 3 | −0.46R, −1.0R, +3.58R |
| Thu 25 | London one-way pump, then an 897pt collapse | 2 | break-even, +180pt |
| Fri 26 | bottoming the weekly range | 3 | +2.45R, +2.35R, +2.90R |

He passed **three London candidates in one day** on Wednesday and **the whole
of London** on Thursday. Two limits never filled, one of which would have
made 2R. He does not chase and does not mind.

---

## 1. THE THESIS COMES FIRST, AND IT IS ABOUT LOCATION

Before any candle matters he establishes **where price is in the multi-day
range** and **what he expects it to do from there**. Every trade in the week
is downstream of that sentence.

- Mon: *"we're topping out this range"* → shorts into a top
- Tue: *"I'm expecting us to fill a new week opening gap"* → shorts, with a
  named destination
- Wed: *"it's either gonna break this range… or keep going lower"* → **no
  thesis, so no trades until one appears**
- Thu: *"just straight pumping"* → nothing to do in London
- Fri: *"bottoming out this weekly range"* → longs preferred, shorts allowed

**The thesis names a destination.** Gap fill, weekly VAL, the 17 June lows,
the top of the range. Targets come from the thesis, not from R multiples.

**The thesis can be two-sided.** Friday: *"I'm more long-biased, but I'm not
opposed to shorts. If it's going to continue down, it's going to continue
down here."* He then took a short **and** a long on the same day, both
winners. A two-sided thesis is not indecision — it is a conditional plan.

**The thesis completing is a reason to stop.** Tuesday, once the gap filled
at the open, he passed a mechanically valid short and flipped to expecting a
rebalance. Friday, once he believed the week had bottomed, he excluded shorts
for the rest of the window.

---

## 2. THE TRIGGER — a hard gate, and it is not one thing

**A candidate requires closure through TWO levels.**

> *"My entry always needs to be closure through two levels. That's usually
> what I stick by."*

The levels are: the candle's **own BB(20) MA**, a **VWAP band** (mid, ±1, ±2,
±3), the **developing POC / VAH / VAL**, and the **anchored weekly** profile
edges.

Three qualifications that the week established and that matter:

1. **A rejection counts toward the pair**, not only a closure. Tue N2 closed
   through the 2m MA while *rejecting* the VWAP mid and the POC.
2. **The own BB MA appears to be mandatory.** 11 of 11 takes close through
   the candle's own MA; the second leg varies freely. *Inferred from his
   behaviour, not stated by him — flagged for confirmation.* On Thursday
   London it is the difference between three qualifying candles and one, and
   it is what makes his "no closure through two levels" account exact.
3. **He waits for the second level.** Friday London: the 04:00 2m closed
   through the MA but not VWAP; he waited; the 04:04 2m closed through VWAP;
   *then* he acted. Verified on the tape.

**Timeframes: 2m and 3m.** He checks the other one for confirmation —
*"we look at the 3-minute really quick first as well"* — and simultaneous
closure raises conviction without being required.

---

## 3. THE ENTRY — a limit on the retest, never a market order

> *"The damn agent is gonna be doing limit orders because that's how I
> fucking trade."*

The trigger candle is the **signal** bar, not the entry bar.

**Which level to limit at: the CLOSEST structure to price at the trigger's
close** — *"the last thing it would have broken through."*

This is not a stylistic preference and the week paid for it twice:

- **Mon N1** entered at market on the close: **1.0R**. The retest at 30,851
  would have filled with a 33pt stop instead of 55pt for the same target —
  **2.33R**. His own critique, and the arithmetic confirms it.
- **Fri PRE1** limited the POC (29,369) rather than the 3m MA (29,382.79).
  Price never got back to the MA — highest print after the fill was 29,377.
  Limiting the "obvious" level would have meant **no trade at all**.

**The offset is forward-looking.** A couple of points inside, offset in the
direction the level is *travelling*: *"this candle is closed through, this
Bollinger Band is probably going to move down, I'm going to give it three
points of leeway."*

**LIMIT LIFETIME — two clauses, both hard:**

1. **~10 minutes maximum.**
2. **Cancel if price reaches the next structural level before filling.**
   *"If it runs to a structural level and then fills me, I'm not very
   confident in that anymore."*

**He never chases.** A late fill is a different, worse trade. Two limits went
unfilled in the week; one would have made 2R. *"I could care less."*

---

## 4. THE STOP — where the thesis dies, plus clearance

Never a reflex placement at the candle's extreme. **The test: does the
candle's extreme sit ON a live level?**

- **If yes, go beyond that level.** Price can go touch it and come back.
  Mon L1 (candle high near the weekly high), Tue N1 (candle low sat exactly
  at VWAP−1), Tue N2 (candle high at the POC/VWAP-mid it kept rejecting),
  Wed L1 and Wed PRE1 (candle high at the 3m MA and VWAP+1). Five instances,
  one rule.
- **If no, use it.** Mon N2 (30,913.5 above a 30,911.75 high), Tue L1
  (30,033.5 = the candle high exactly), Thu PRE1 (30,202.5 above 30,201.75),
  Fri PRE1 (29,400 at a 29,401.00 high).

**Stop width drives size, not the decision.** *"This would have been de-risked
with a 68 point stop, maybe two micros."* A wide stop is taken smaller, not
skipped — but an *oversized* one gets scrutiny (Fri N1: *"that's still a
fucking big stop, jeez louise"*, taken anyway because the thesis was strong).

---

## 5. THE EXIT

**Targets are structure named in the thesis.** Weekly VAL, prior-day levels,
the pre-market high, VWAP bands, the 15m MA, a fib level, the top of a range.

**Take profit sits a couple of points SHORT of the band.**

**Partial at intermediate structure, then break-even.** Typically 75% at the
first level. Also move to break-even on touching an intermediate band even
without taking a partial.

**When two levels cluster, take the further one.** *"Price never touches a
value area high and then just runs straight from it. It usually wicks around,
and with VWAP right there, I'm inclined to believe it would touch VWAP."*

**Extend the target when the thesis is confirming.** Fri N1 moved from the
developing VAH to VWAP+1 mid-trade — worth ~90 points. Extend the target,
never the risk.

**Target size scales to direction.** A counter-trend rebalance gets a modest
target by design.

**In chop, trail aggressively** — beyond the wick of any candle that rejects
your level against you. Wed L1 cut a 29pt loss to 13.25pt, and the untrailed
stop would have been hit anyway.

**R is quoted at the FULL target**, not blended across partials.

---

## 6. THE HARD CONSTRAINTS

1. Direction must match the standing thesis.
2. Inside a window: **LONDON 03:00–04:59, NY_PRE 08:00–09:29, NY_AM
   09:30–10:45** NY. **Entries only** — *"you don't flatten trades when the
   window closes."*
3. Not in the first few minutes of the cash open.
4. After a displacement, wait for the rebalance before entering.
5. A thesis alone is never enough — the trigger must exist.
6. **Headroom.** Two levels broken is the minimum, not the criterion. The
   next level beyond the entry must not sit immediately in the way. *"I don't
   like taking trades where it has to break through something in order for my
   trade to work."*
7. **POC alignment.** POC should be *with* the trade, not an obstacle.
8. **In chop, require higher-timeframe alignment** before taking anything.
9. **No entries before high-impact news.**
10. **Move to break-even before the cash open** when carrying a pre-market
    position.

---

## 7. THE TWO ROWS THAT DEFINE THE CHARACTER

**Thursday's break-even.** A pre-market short, planned 2.45R, moved to
break-even before the open *"because open volatility can cook you even if
your thesis is wrong."* Break-even hit at 09:30. The market then fell 897
points and his target printed at 09:31. **29.2R was available had he held.**

> *"That's straight gambling for me."*

**Friday's refusal.** A trigger he believed in with a stop he hated. He
considered limiting a nearer level to get a tighter fill and avoid missing
the move — and refused.

> *"I don't really wanna miss a good entry because I'm being tight with where
> I place my limits. Nah, I'm sticking to my rules. I gotta stick to my
> fucking rules."*

**Any scoring that marks either of these as an error is scoring the wrong
thing.** A rule that pays out over a year is not refuted by the day it costs
the most. This is the single most important instruction for the scorer.

---

## 8. THE THREE-OPTION DECISION

Not take/pass. **Take full / take light / pass.**

> *"I'd probably take this one with light size because it's not like a
> full-conviction trade."*

That trade returned 2.45R. Light size is a real third branch and the log
must carry it.

---

## 9. WHAT IS CALIBRATED

Every level he named across five days reproduces on our bars:

| | status |
|---|---|
| VWAP mid / ±1 / ±2 / ±3 | source `open`, 18:00 anchor — matched to ~0.1pt |
| BB(20) MA, 2m/3m/15m/1h | matched (2m MA he read as 30,008.5 vs our 30,008.58) |
| developing daily POC / VAH / VAL | matched to ~0.5pt |
| anchored weekly profile | 18:00 NY seven days back, developing — VAL confirmed twice |
| fibs | drawn on **manually marked swings**, not a fixed range — confirmed Friday |

**Two ambiguities that must never be resolved by guessing:**

- **"Value area"** means the daily profile some days and the anchored weekly
  one others. On 2026-06-25 they sat **165 points apart**, and taking the
  daily one would have exited a 180pt trade at 30–45pt. Compute both.
- **Fib swings** are a judgment call, not a formula. Using a full-session
  range instead of his marked swing landed ~70pt off on 2026-06-23; using his
  marked swing on 2026-06-26 landed on the level to within 2 points.

---

## 10. WHAT IS STILL OPEN

1. **Is the own BB MA genuinely mandatory?** 11/11, but inferred. A yes makes
   it a hard gate; a no means the agent would be discarding valid setups.
2. **Monday's London stop.** *"Stops at 30"*, sentence cut off. That trade's
   R is provisional.
3. **The 10:45 cut-off vs January's 10:51 entry.** Minor, but unresolved.
